"""
Automatic RAG Sync Wrapper for yWriter7 Operations.

Provides automatic synchronization between yWriter7 file operations and the RAG system.
Wraps yWriter7 operations to ensure the knowledge base is always up-to-date.

Usage:
    # Automatic sync with context manager
    with AutoSyncYw7File("story.yw7") as yw7_file:
        yw7_file.novel.chapters[chapter_id].title = "New Title"
        # Sync happens automatically on exit

    # Manual control
    yw7_file = AutoSyncYw7File("story.yw7", auto_sync=False)
    yw7_file.read()
    yw7_file.novel.chapters[chapter_id].title = "New Title"
    yw7_file.write()  # Write to file
    yw7_file.sync_to_rag()  # Manually trigger sync

    # Wrap existing Yw7File instance
    yw7_file = Yw7File("story.yw7")
    yw7_file.read()
    enable_auto_sync(yw7_file, sync_manager)
    yw7_file.write()  # Now automatically syncs to RAG
"""

import logging
from typing import Optional
from pathlib import Path
from functools import wraps

from ywriter7.yw.yw7_file import Yw7File
from .sync_manager import RAGSyncManager
from .vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


class AutoSyncYw7File(Yw7File):
    """
    Extended Yw7File that automatically syncs changes to RAG system.

    Features:
    - Automatic sync after write operations
    - Context manager support for transaction-like operations
    - Manual sync control when needed
    - Seamless drop-in replacement for Yw7File
    """

    def __init__(
        self,
        file_path: str,
        auto_sync: bool = True,
        vector_store: Optional[VectorStoreManager] = None,
        sync_manager: Optional[RAGSyncManager] = None
    ):
        """
        Initialize AutoSyncYw7File.

        Args:
            file_path: Path to the .yw7 file
            auto_sync: Enable automatic RAG sync after write operations (default: True)
            vector_store: VectorStoreManager instance (created if not provided)
            sync_manager: RAGSyncManager instance (created if not provided)
        """
        super().__init__(file_path)
        self.auto_sync = auto_sync

        # Initialize RAG components
        self.vector_store = vector_store or VectorStoreManager()
        self.sync_manager = sync_manager or RAGSyncManager(self.vector_store)

        logger.info(f"AutoSyncYw7File initialized for {file_path} (auto_sync={auto_sync})")

    def write(self) -> None:
        """
        Write changes to .yw7 file and optionally sync to RAG.

        Overrides parent write() to add automatic RAG synchronization.
        """
        # Write to file first
        super().write()
        logger.info(f"Wrote changes to {self.filePath}")

        # Sync to RAG if enabled
        if self.auto_sync:
            self.sync_to_rag()

    def sync_to_rag(self) -> dict:
        """
        Manually trigger sync from yWriter7 to RAG system.

        Returns:
            Dictionary with sync statistics (characters, locations, items, etc.)
        """
        try:
            logger.info(f"Syncing {self.filePath} to RAG system...")
            stats = self.sync_manager.sync_from_ywriter(self.filePath)

            total_synced = sum(stats.values())
            logger.info(f"RAG sync completed: {total_synced} items synced")
            logger.debug(f"Sync details: {stats}")

            return stats
        except Exception as e:
            logger.error(f"Error syncing to RAG: {e}", exc_info=True)
            raise

    def __enter__(self):
        """Context manager entry - read the file."""
        self.read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - write and sync changes."""
        if exc_type is None:
            # Only write if no exception occurred
            self.write()
        else:
            logger.warning(f"Context manager exited with exception: {exc_type.__name__}")
        return False  # Don't suppress exceptions


def enable_auto_sync(
    yw7_file: Yw7File,
    sync_manager: Optional[RAGSyncManager] = None,
    vector_store: Optional[VectorStoreManager] = None
) -> Yw7File:
    """
    Enable automatic RAG sync for an existing Yw7File instance.

    Monkey-patches the write() method to add automatic RAG synchronization
    without modifying the original instance type.

    Args:
        yw7_file: Existing Yw7File instance
        sync_manager: RAGSyncManager instance (created if not provided)
        vector_store: VectorStoreManager instance (created if not provided)

    Returns:
        The same Yw7File instance with auto-sync enabled

    Example:
        yw7_file = Yw7File("story.yw7")
        yw7_file.read()
        enable_auto_sync(yw7_file)  # Now writes will auto-sync
        yw7_file.write()  # Automatically syncs to RAG
    """
    # Initialize RAG components if not provided
    if vector_store is None:
        vector_store = VectorStoreManager()
    if sync_manager is None:
        sync_manager = RAGSyncManager(vector_store)

    # Store original write method
    original_write = yw7_file.write

    # Create wrapped write method
    @wraps(original_write)
    def write_with_sync():
        """Write changes and sync to RAG."""
        # Call original write
        original_write()
        logger.info(f"Wrote changes to {yw7_file.filePath}")

        # Sync to RAG
        try:
            logger.info(f"Auto-syncing {yw7_file.filePath} to RAG system...")
            stats = sync_manager.sync_from_ywriter(yw7_file.filePath)
            total_synced = sum(stats.values())
            logger.info(f"RAG sync completed: {total_synced} items synced")
            logger.debug(f"Sync details: {stats}")
        except Exception as e:
            logger.error(f"Error during auto-sync: {e}", exc_info=True)
            # Don't raise - allow write to succeed even if sync fails

    # Replace write method
    yw7_file.write = write_with_sync

    # Add sync_manager reference for manual access
    yw7_file._sync_manager = sync_manager
    yw7_file._vector_store = vector_store

    logger.info(f"Auto-sync enabled for {yw7_file.filePath}")
    return yw7_file


def disable_auto_sync(yw7_file: Yw7File) -> Yw7File:
    """
    Disable automatic RAG sync for a Yw7File instance.

    Restores the original write() method if it was wrapped by enable_auto_sync().

    Args:
        yw7_file: Yw7File instance with auto-sync enabled

    Returns:
        The same Yw7File instance with auto-sync disabled
    """
    if hasattr(yw7_file.write, '__wrapped__'):
        yw7_file.write = yw7_file.write.__wrapped__
        logger.info(f"Auto-sync disabled for {yw7_file.filePath}")
    else:
        logger.warning(f"No auto-sync detected on {yw7_file.filePath}")

    return yw7_file


class RAGSyncContext:
    """
    Context manager for batch yWriter7 operations with a single RAG sync.

    Useful when making multiple changes and you want to sync only once at the end.

    Example:
        with RAGSyncContext("story.yw7") as ctx:
            yw7_file = ctx.yw7_file
            yw7_file.novel.chapters[ch1].title = "Chapter 1"
            yw7_file.novel.chapters[ch2].title = "Chapter 2"
            # Both chapters synced in one operation on exit
    """

    def __init__(
        self,
        file_path: str,
        vector_store: Optional[VectorStoreManager] = None,
        sync_manager: Optional[RAGSyncManager] = None
    ):
        """
        Initialize RAGSyncContext.

        Args:
            file_path: Path to the .yw7 file
            vector_store: VectorStoreManager instance (created if not provided)
            sync_manager: RAGSyncManager instance (created if not provided)
        """
        self.file_path = file_path
        self.yw7_file = Yw7File(file_path)

        # Initialize RAG components
        self.vector_store = vector_store or VectorStoreManager()
        self.sync_manager = sync_manager or RAGSyncManager(self.vector_store)

        self._changes_made = False

    def __enter__(self):
        """Load the yWriter7 file."""
        self.yw7_file.read()
        logger.info(f"RAGSyncContext opened for {self.file_path}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Write changes and sync to RAG."""
        if exc_type is None:
            # Save changes
            self.yw7_file.write()
            logger.info(f"Changes written to {self.file_path}")

            # Sync to RAG
            try:
                logger.info(f"Syncing {self.file_path} to RAG system...")
                stats = self.sync_manager.sync_from_ywriter(self.file_path)
                total_synced = sum(stats.values())
                logger.info(f"RAG sync completed: {total_synced} items synced")
                logger.debug(f"Sync details: {stats}")
            except Exception as e:
                logger.error(f"Error syncing to RAG: {e}", exc_info=True)
        else:
            logger.warning(f"RAGSyncContext exited with exception: {exc_type.__name__}")

        return False  # Don't suppress exceptions


# Convenience function for one-off operations
def sync_file_to_rag(
    file_path: str,
    vector_store: Optional[VectorStoreManager] = None,
    sync_manager: Optional[RAGSyncManager] = None
) -> dict:
    """
    One-shot sync of a yWriter7 file to RAG system.

    Useful for manual sync operations or initial population of RAG.

    Args:
        file_path: Path to the .yw7 file
        vector_store: VectorStoreManager instance (created if not provided)
        sync_manager: RAGSyncManager instance (created if not provided)

    Returns:
        Dictionary with sync statistics

    Example:
        stats = sync_file_to_rag("story.yw7")
        print(f"Synced {stats['characters']} characters")
    """
    if vector_store is None:
        vector_store = VectorStoreManager()
    if sync_manager is None:
        sync_manager = RAGSyncManager(vector_store)

    logger.info(f"Syncing {file_path} to RAG system...")
    stats = sync_manager.sync_from_ywriter(file_path)
    total_synced = sum(stats.values())
    logger.info(f"RAG sync completed: {total_synced} items synced")

    return stats
