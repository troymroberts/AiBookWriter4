"""
Quick test for RAG auto-sync functionality.

Tests:
1. AutoSyncYw7File basic usage
2. Context manager functionality
3. Manual sync control
4. RAGSyncContext for batch operations
5. Integration with existing tools
"""

import os
import logging
from pathlib import Path

from rag import AutoSyncYw7File, RAGSyncContext, sync_file_to_rag
from tools.ywriter_tools import load_yw7_file
from ywriter7.model.project_note import ProjectNote
from ywriter7.model.id_generator import create_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_auto_sync():
    """Test 1: Basic AutoSyncYw7File usage."""
    print("\n" + "="*70)
    print("TEST 1: Basic AutoSyncYw7File")
    print("="*70)

    test_file = "output/test_novel.yw7"

    if not Path(test_file).exists():
        print(f"⚠ Test file not found: {test_file}")
        return False

    try:
        # Test with auto_sync=False (manual control)
        yw7_file = AutoSyncYw7File(test_file, auto_sync=False)
        yw7_file.read()

        print(f"✓ Loaded file: {yw7_file.novel.title}")
        print(f"  Characters: {len(yw7_file.novel.characters)}")
        print(f"  Locations: {len(yw7_file.novel.locations)}")
        print(f"  Chapters: {len(yw7_file.novel.chapters)}")

        # Test manual sync
        stats = yw7_file.sync_to_rag()
        print(f"\n✓ Manual sync completed:")
        print(f"  Characters: {stats.get('characters', 0)}")
        print(f"  Locations: {stats.get('locations', 0)}")
        print(f"  Plot events: {stats.get('plot_events', 0)}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.error("Test failed", exc_info=True)
        return False


def test_context_manager():
    """Test 2: Context manager functionality."""
    print("\n" + "="*70)
    print("TEST 2: Context Manager")
    print("="*70)

    test_file = "output/test_novel.yw7"

    if not Path(test_file).exists():
        print(f"⚠ Test file not found: {test_file}")
        return False

    try:
        # Use context manager (read-only test)
        with AutoSyncYw7File(test_file, auto_sync=False) as yw7_file:
            print(f"✓ Context manager opened: {yw7_file.novel.title}")
            print(f"  Characters: {len(yw7_file.novel.characters)}")

        print("✓ Context manager closed successfully")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.error("Test failed", exc_info=True)
        return False


def test_rag_sync_context():
    """Test 3: RAGSyncContext for batch operations."""
    print("\n" + "="*70)
    print("TEST 3: RAGSyncContext")
    print("="*70)

    test_file = "output/test_novel.yw7"

    if not Path(test_file).exists():
        print(f"⚠ Test file not found: {test_file}")
        return False

    try:
        # Use RAGSyncContext (read-only test)
        with RAGSyncContext(test_file) as ctx:
            yw7_file = ctx.yw7_file
            print(f"✓ RAGSyncContext opened: {yw7_file.novel.title}")
            print(f"  Chapters: {len(yw7_file.novel.chapters)}")

            # Don't actually modify, just test the context
            print("  (Read-only test - no modifications)")

        print("✓ RAGSyncContext closed successfully")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.error("Test failed", exc_info=True)
        return False


def test_one_shot_sync():
    """Test 4: One-shot sync function."""
    print("\n" + "="*70)
    print("TEST 4: One-Shot Sync")
    print("="*70)

    test_file = "output/test_novel.yw7"

    if not Path(test_file).exists():
        print(f"⚠ Test file not found: {test_file}")
        return False

    try:
        # Test one-shot sync
        stats = sync_file_to_rag(test_file)

        print(f"✓ One-shot sync completed:")
        print(f"  Characters: {stats.get('characters', 0)}")
        print(f"  Locations: {stats.get('locations', 0)}")
        print(f"  Items: {stats.get('items', 0)}")
        print(f"  Plot events: {stats.get('plot_events', 0)}")
        print(f"  Relationships: {stats.get('relationships', 0)}")
        print(f"  Total: {sum(stats.values())} items")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.error("Test failed", exc_info=True)
        return False


def test_tools_integration():
    """Test 5: Integration with existing tools."""
    print("\n" + "="*70)
    print("TEST 5: Tools Integration")
    print("="*70)

    test_file = "output/test_novel.yw7"

    if not Path(test_file).exists():
        print(f"⚠ Test file not found: {test_file}")
        return False

    try:
        # Test load_yw7_file with auto_sync parameter
        yw7_file = load_yw7_file(test_file, auto_sync=False)

        print(f"✓ load_yw7_file works: {yw7_file.novel.title}")
        print(f"  Characters: {len(yw7_file.novel.characters)}")
        print(f"  Locations: {len(yw7_file.novel.locations)}")

        # Check if it's an AutoSyncYw7File instance
        is_auto_sync = isinstance(yw7_file, AutoSyncYw7File)
        print(f"  Auto-sync instance: {is_auto_sync}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.error("Test failed", exc_info=True)
        return False


def test_semantic_search():
    """Test 6: Semantic search after sync."""
    print("\n" + "="*70)
    print("TEST 6: Semantic Search")
    print("="*70)

    test_file = "output/test_novel.yw7"

    if not Path(test_file).exists():
        print(f"⚠ Test file not found: {test_file}")
        return False

    try:
        from rag import VectorStoreManager

        # Ensure data is synced
        stats = sync_file_to_rag(test_file)
        print(f"✓ Synced {sum(stats.values())} items")

        # Test semantic search
        vector_store = VectorStoreManager()

        # Search characters
        if stats.get('characters', 0) > 0:
            results = vector_store.semantic_search(
                "characters",
                "character person protagonist",
                n_results=3
            )
            print(f"\n✓ Character search: {len(results['ids'])} results")
            for i, (doc_id, metadata) in enumerate(zip(results['ids'], results['metadatas']), 1):
                print(f"  {i}. {metadata.get('name', 'Unknown')} (ID: {doc_id})")

        # Search locations
        if stats.get('locations', 0) > 0:
            results = vector_store.semantic_search(
                "locations",
                "place location setting",
                n_results=3
            )
            print(f"\n✓ Location search: {len(results['ids'])} results")
            for i, (doc_id, metadata) in enumerate(zip(results['ids'], results['metadatas']), 1):
                print(f"  {i}. {metadata.get('name', 'Unknown')} (ID: {doc_id})")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.error("Test failed", exc_info=True)
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("RAG AUTO-SYNC TEST SUITE")
    print("="*70)

    tests = [
        ("Basic Auto-Sync", test_basic_auto_sync),
        ("Context Manager", test_context_manager),
        ("RAGSyncContext", test_rag_sync_context),
        ("One-Shot Sync", test_one_shot_sync),
        ("Tools Integration", test_tools_integration),
        ("Semantic Search", test_semantic_search),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test {name} crashed: {e}", exc_info=True)
            results.append((name, False))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
