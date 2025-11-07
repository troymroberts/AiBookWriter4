"""
Vector Store Manager for ChromaDB integration.

Handles:
- ChromaDB client initialization and management
- Collection creation and management
- Document embedding and storage
- Semantic search queries
- Metadata filtering
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import yaml
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Manages ChromaDB vector store for story knowledge persistence.

    Features:
    - Multiple collections for different story elements
    - Semantic search with metadata filtering
    - Automatic embedding generation
    - Persistent storage
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the vector store manager.

        Args:
            config_path: Path to the application config file
        """
        self.config = self._load_config(config_path)
        self.rag_config = self.config.get("rag", {})

        # Validate RAG is enabled
        if not self.rag_config.get("enabled", False):
            logger.warning("RAG is disabled in config.yaml")

        # Setup ChromaDB
        self.db_path = self.rag_config.get("vector_db_path", "knowledge_base")
        self.collection_prefix = self.rag_config.get("collection_prefix", "aibook")
        self.embedding_model = self.rag_config.get("embedding_model", "all-MiniLM-L6-v2")

        # Initialize ChromaDB client
        self.client = self._init_client()

        # Initialize embedding function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )

        # Collection cache
        self._collections = {}

        # Initialize collections
        self._init_collections()

        logger.info(f"VectorStoreManager initialized with ChromaDB at {self.db_path}")

    def _load_config(self, config_path: str) -> dict:
        """Load application configuration."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return {}

    def _init_client(self) -> chromadb.Client:
        """Initialize ChromaDB client with persistent storage."""
        db_path = Path(self.db_path)
        db_path.mkdir(parents=True, exist_ok=True)

        client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )

        return client

    def _init_collections(self):
        """Initialize all collections defined in config."""
        collections = self.rag_config.get("collections", [
            "characters", "locations", "items",
            "plot_events", "relationships", "lore"
        ])

        for collection_name in collections:
            self.get_or_create_collection(collection_name)

        logger.info(f"Initialized {len(collections)} collections")

    def get_or_create_collection(self, name: str):
        """
        Get or create a ChromaDB collection.

        Args:
            name: Collection name (without prefix)

        Returns:
            ChromaDB collection
        """
        full_name = f"{self.collection_prefix}_{name}"

        if full_name not in self._collections:
            try:
                collection = self.client.get_or_create_collection(
                    name=full_name,
                    embedding_function=self.embedding_fn,
                    metadata={"description": f"Collection for {name}"}
                )
                self._collections[full_name] = collection
                logger.debug(f"Created/retrieved collection: {full_name}")
            except Exception as e:
                logger.error(f"Failed to create collection {full_name}: {e}")
                raise

        return self._collections[full_name]

    def add_document(
        self,
        collection_name: str,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a document to a collection.

        Args:
            collection_name: Name of the collection
            document_id: Unique ID for the document
            content: Document content to embed
            metadata: Optional metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            # Ensure metadata is a dict
            if metadata is None:
                metadata = {}

            # Convert all metadata values to strings (ChromaDB requirement)
            metadata = {k: str(v) for k, v in metadata.items()}

            collection.add(
                ids=[document_id],
                documents=[content],
                metadatas=[metadata]
            )

            logger.debug(f"Added document {document_id} to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add document {document_id} to {collection_name}: {e}")
            return False

    def add_documents(
        self,
        collection_name: str,
        document_ids: List[str],
        contents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Add multiple documents to a collection (batch operation).

        Args:
            collection_name: Name of the collection
            document_ids: List of unique IDs
            contents: List of document contents
            metadatas: Optional list of metadata dictionaries

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            # Prepare metadatas
            if metadatas is None:
                metadatas = [{} for _ in document_ids]

            # Convert all metadata values to strings
            metadatas = [
                {k: str(v) for k, v in meta.items()}
                for meta in metadatas
            ]

            collection.add(
                ids=document_ids,
                documents=contents,
                metadatas=metadatas
            )

            logger.debug(f"Added {len(document_ids)} documents to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add documents to {collection_name}: {e}")
            return False

    def update_document(
        self,
        collection_name: str,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing document.

        Args:
            collection_name: Name of the collection
            document_id: ID of the document to update
            content: New content
            metadata: Optional new metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            # Prepare metadata
            if metadata is None:
                metadata = {}
            metadata = {k: str(v) for k, v in metadata.items()}

            collection.update(
                ids=[document_id],
                documents=[content],
                metadatas=[metadata]
            )

            logger.debug(f"Updated document {document_id} in {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update document {document_id} in {collection_name}: {e}")
            return False

    def delete_document(
        self,
        collection_name: str,
        document_id: str
    ) -> bool:
        """
        Delete a document from a collection.

        Args:
            collection_name: Name of the collection
            document_id: ID of the document to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(ids=[document_id])

            logger.debug(f"Deleted document {document_id} from {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {document_id} from {collection_name}: {e}")
            return False

    def semantic_search(
        self,
        collection_name: str,
        query: str,
        n_results: Optional[int] = None,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic search on a collection.

        Args:
            collection_name: Name of the collection to search
            query: Search query text
            n_results: Number of results to return (default from config)
            where: Metadata filter (e.g., {"type": "major"})
            where_document: Document content filter

        Returns:
            Dictionary with 'ids', 'documents', 'metadatas', 'distances'
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            if n_results is None:
                n_results = self.rag_config.get("top_k", 5)

            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                where_document=where_document
            )

            logger.debug(f"Semantic search in {collection_name}: {len(results['ids'][0])} results")

            return {
                'ids': results['ids'][0],
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0],
                'distances': results['distances'][0]
            }

        except Exception as e:
            logger.error(f"Failed to search {collection_name}: {e}")
            return {'ids': [], 'documents': [], 'metadatas': [], 'distances': []}

    def get_document(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID.

        Args:
            collection_name: Name of the collection
            document_id: ID of the document

        Returns:
            Dictionary with document data or None if not found
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            result = collection.get(ids=[document_id])

            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'document': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to get document {document_id} from {collection_name}: {e}")
            return None

    def get_all_documents(
        self,
        collection_name: str,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all documents from a collection.

        Args:
            collection_name: Name of the collection
            where: Optional metadata filter

        Returns:
            List of document dictionaries
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            result = collection.get(where=where)

            documents = []
            for i in range(len(result['ids'])):
                documents.append({
                    'id': result['ids'][i],
                    'document': result['documents'][i],
                    'metadata': result['metadatas'][i]
                })

            logger.debug(f"Retrieved {len(documents)} documents from {collection_name}")
            return documents

        except Exception as e:
            logger.error(f"Failed to get documents from {collection_name}: {e}")
            return []

    def count_documents(self, collection_name: str) -> int:
        """
        Count documents in a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Number of documents
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            return collection.count()
        except Exception as e:
            logger.error(f"Failed to count documents in {collection_name}: {e}")
            return 0

    def reset_collection(self, collection_name: str) -> bool:
        """
        Delete and recreate a collection (clear all data).

        Args:
            collection_name: Name of the collection to reset

        Returns:
            True if successful, False otherwise
        """
        try:
            full_name = f"{self.collection_prefix}_{collection_name}"

            # Delete the collection
            try:
                self.client.delete_collection(name=full_name)
                logger.info(f"Deleted collection: {full_name}")
            except Exception:
                pass  # Collection might not exist

            # Remove from cache
            if full_name in self._collections:
                del self._collections[full_name]

            # Recreate
            self.get_or_create_collection(collection_name)

            return True

        except Exception as e:
            logger.error(f"Failed to reset collection {collection_name}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all collections.

        Returns:
            Dictionary with collection names and document counts
        """
        stats = {}

        collections = self.rag_config.get("collections", [])
        for collection_name in collections:
            count = self.count_documents(collection_name)
            stats[collection_name] = count

        stats['total'] = sum(stats.values())

        return stats
