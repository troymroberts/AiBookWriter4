"""
RAG (Retrieval-Augmented Generation) module for AiBookWriter4.

This module provides:
- Vector database management with ChromaDB
- Semantic search capabilities
- Bidirectional sync with yWriter7
- Knowledge persistence for story elements
"""

from .vector_store import VectorStoreManager
from .sync_manager import RAGSyncManager

__all__ = ['VectorStoreManager', 'RAGSyncManager']
