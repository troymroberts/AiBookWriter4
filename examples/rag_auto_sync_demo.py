"""
RAG Auto-Sync Demo - Demonstrates automatic synchronization between yWriter7 and RAG.

This script shows different ways to use the automatic RAG sync functionality:
1. Using AutoSyncYw7File with context manager (recommended)
2. Using AutoSyncYw7File with manual control
3. Using RAGSyncContext for batch operations
4. Enabling auto-sync on existing Yw7File instances
5. One-shot manual sync operations

Prerequisites:
- A valid .yw7 file with some content
- ChromaDB initialized (automatically created)
- RAG system configured in config.yaml
"""

import logging
from pathlib import Path

from rag.auto_sync import (
    AutoSyncYw7File,
    RAGSyncContext,
    enable_auto_sync,
    sync_file_to_rag
)
from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.chapter import Chapter
from ywriter7.model.scene import Scene
from ywriter7.model.character import Character
from ywriter7.model.id_generator import create_id

# Configure logging to see sync operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_context_manager(file_path: str):
    """
    Demo 1: Using AutoSyncYw7File with context manager (recommended).

    This is the cleanest approach - changes are automatically saved and synced
    when the context exits.
    """
    print("\n" + "="*70)
    print("DEMO 1: AutoSyncYw7File with Context Manager")
    print("="*70)

    with AutoSyncYw7File(file_path) as yw7_file:
        # Make changes to the project
        print(f"\nProject: {yw7_file.novel.title}")
        print(f"Number of chapters: {len(yw7_file.novel.chapters)}")

        # Add a new character
        char_id = create_id(yw7_file.novel.characters)
        character = Character()
        character.title = "Demo Character"
        character.fullName = "Demo Character from Auto-Sync"
        character.desc = "This character was created to demonstrate auto-sync functionality."
        character.notes = "Created by rag_auto_sync_demo.py"

        yw7_file.novel.characters[char_id] = character
        yw7_file.novel.srtCharacters.append(char_id)

        print(f"\nCreated character: {character.title} (ID: {char_id})")
        print("Changes will be saved and synced when context exits...")

    print("\n✓ Context exited - changes saved and synced to RAG automatically!")


def demo_manual_control(file_path: str):
    """
    Demo 2: Using AutoSyncYw7File with manual control.

    Useful when you want to make multiple changes and sync only once.
    """
    print("\n" + "="*70)
    print("DEMO 2: AutoSyncYw7File with Manual Control")
    print("="*70)

    # Create with auto_sync=False for manual control
    yw7_file = AutoSyncYw7File(file_path, auto_sync=False)
    yw7_file.read()

    print(f"\nProject: {yw7_file.novel.title}")

    # Make multiple changes
    if yw7_file.novel.chapters:
        first_chapter_id = yw7_file.novel.srtChapters[0]
        chapter = yw7_file.novel.chapters[first_chapter_id]
        print(f"\nUpdating chapter: {chapter.title}")

        # Update description
        chapter.desc = (chapter.desc or "") + "\n[Updated by auto-sync demo]"

        print("Changes made - now saving and syncing manually...")

        # Manual write and sync
        yw7_file.write()  # Only writes to file (auto_sync=False)
        stats = yw7_file.sync_to_rag()  # Manually trigger sync

        print(f"\n✓ Manual sync completed!")
        print(f"  Characters: {stats.get('characters', 0)}")
        print(f"  Locations: {stats.get('locations', 0)}")
        print(f"  Plot events: {stats.get('plot_events', 0)}")


def demo_batch_operations(file_path: str):
    """
    Demo 3: Using RAGSyncContext for batch operations.

    Ideal for making many changes and syncing once at the end.
    """
    print("\n" + "="*70)
    print("DEMO 3: RAGSyncContext for Batch Operations")
    print("="*70)

    with RAGSyncContext(file_path) as ctx:
        yw7_file = ctx.yw7_file

        print(f"\nProject: {yw7_file.novel.title}")
        print("Making multiple changes in batch...")

        # Update multiple chapters
        for i, chapter_id in enumerate(yw7_file.novel.srtChapters[:3], 1):
            chapter = yw7_file.novel.chapters[chapter_id]
            chapter.desc = (chapter.desc or "") + f"\n[Batch update #{i}]"
            print(f"  Updated: {chapter.title}")

        print("\nAll changes will be synced in a single operation on exit...")

    print("\n✓ Batch operations completed - single sync performed!")


def demo_wrap_existing(file_path: str):
    """
    Demo 4: Enabling auto-sync on existing Yw7File instances.

    Useful when working with existing code that uses Yw7File.
    """
    print("\n" + "="*70)
    print("DEMO 4: Wrap Existing Yw7File Instance")
    print("="*70)

    # Standard Yw7File creation
    yw7_file = Yw7File(file_path)
    yw7_file.read()

    print(f"\nProject: {yw7_file.novel.title}")
    print("This is a standard Yw7File instance...")

    # Enable auto-sync on the existing instance
    enable_auto_sync(yw7_file)
    print("✓ Auto-sync enabled on existing instance!")

    # Now writes will auto-sync
    if yw7_file.novel.characters:
        first_char_id = yw7_file.novel.srtCharacters[0]
        character = yw7_file.novel.characters[first_char_id]
        print(f"\nUpdating character: {character.title}")

        character.notes = (character.notes or "") + "\n[Updated via wrapped instance]"

        print("Saving changes...")
        yw7_file.write()  # Now automatically syncs!

    print("\n✓ Changes saved and synced automatically!")


def demo_manual_sync(file_path: str):
    """
    Demo 5: One-shot manual sync operations.

    Useful for initial population or ad-hoc synchronization.
    """
    print("\n" + "="*70)
    print("DEMO 5: One-Shot Manual Sync")
    print("="*70)

    print(f"\nSyncing {file_path} to RAG system...")

    stats = sync_file_to_rag(file_path)

    print("\n✓ Sync completed!")
    print(f"\nSynchronized items:")
    print(f"  Characters: {stats.get('characters', 0)}")
    print(f"  Locations: {stats.get('locations', 0)}")
    print(f"  Items: {stats.get('items', 0)}")
    print(f"  Plot events: {stats.get('plot_events', 0)}")
    print(f"  Relationships: {stats.get('relationships', 0)}")
    print(f"  Total: {sum(stats.values())} items")


def demo_semantic_search(file_path: str):
    """
    Demo 6: Searching the RAG system after sync.

    Shows how synced data can be queried semantically.
    """
    print("\n" + "="*70)
    print("DEMO 6: Semantic Search After Sync")
    print("="*70)

    from rag.vector_store import VectorStoreManager

    # First, ensure everything is synced
    print("\nEnsuring latest sync...")
    sync_file_to_rag(file_path)

    # Now search the RAG system
    vector_store = VectorStoreManager()

    print("\nSearching for characters...")
    results = vector_store.semantic_search("characters", "protagonist hero main character", n_results=3)

    print(f"\nFound {len(results['ids'])} results:")
    for i, (doc_id, doc, metadata, score) in enumerate(
        zip(results['ids'], results['documents'], results['metadatas'], results['distances']),
        1
    ):
        print(f"\n{i}. {metadata.get('name', 'Unknown')} (ID: {doc_id})")
        print(f"   Similarity: {1 - score:.2%}")
        print(f"   Preview: {doc[:150]}...")


def main():
    """
    Run all demos.

    Make sure you have a valid .yw7 file to work with.
    """
    print("\n" + "="*70)
    print("RAG AUTO-SYNC DEMONSTRATION")
    print("="*70)

    # Use test file from the tests directory
    test_file = "test/test_data/test_story.yw7"

    if not Path(test_file).exists():
        print(f"\nError: Test file not found: {test_file}")
        print("Please create a test .yw7 file or update the path.")
        return

    print(f"\nUsing test file: {test_file}")
    print("\nThis demo will:")
    print("  1. Show context manager usage (recommended)")
    print("  2. Demonstrate manual control")
    print("  3. Show batch operations")
    print("  4. Wrap existing instances")
    print("  5. Perform one-shot sync")
    print("  6. Search synced data")

    try:
        # Run all demos
        demo_context_manager(test_file)
        demo_manual_control(test_file)
        demo_batch_operations(test_file)
        demo_wrap_existing(test_file)
        demo_manual_sync(test_file)
        demo_semantic_search(test_file)

        print("\n" + "="*70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*70)

    except Exception as e:
        logger.error(f"Error running demos: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
