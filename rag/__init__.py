"""
RAG (Retrieval-Augmented Generation) module for AiBookWriter4.

This module provides:
- Vector database management with ChromaDB
- Semantic search capabilities
- Bidirectional sync with yWriter7
- Automatic sync wrapper for yWriter7 operations
- Knowledge persistence for story elements
"""

from .vector_store import VectorStoreManager
from .sync_manager import RAGSyncManager
from .auto_sync import (
    AutoSyncYw7File,
    RAGSyncContext,
    enable_auto_sync,
    disable_auto_sync,
    sync_file_to_rag
)

__all__ = [
    'VectorStoreManager',
    'RAGSyncManager',
    'AutoSyncYw7File',
    'RAGSyncContext',
    'enable_auto_sync',
    'disable_auto_sync',
    'sync_file_to_rag'
]
