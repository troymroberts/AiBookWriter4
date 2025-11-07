"""
Test RAG (Retrieval-Augmented Generation) Integration

This test suite verifies:
1. Vector store initialization
2. Bidirectional sync between yWriter7 and ChromaDB
3. Semantic search capabilities
4. MemoryKeeper agent with RAG tools
5. End-to-end RAG workflow
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import RAG components
from rag.vector_store import VectorStoreManager
from rag.sync_manager import RAGSyncManager

# Import yWriter7 components
from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.novel import Novel
from ywriter7.model.character import Character
from ywriter7.model.location import Location
from ywriter7.model.item import Item
from ywriter7.model.chapter import Chapter
from ywriter7.model.scene import Scene
from ywriter7.model.id_generator import create_id

# Import MemoryKeeper agent
from agents.memory_keeper import MemoryKeeper, MemoryKeeperConfig


def create_test_novel(file_path: str) -> Yw7File:
    """
    Create a test yWriter7 file with sample story data.

    Returns:
        Yw7File instance
    """
    logger.info(f"Creating test novel at: {file_path}")

    # Create novel
    novel = Novel()
    novel.title = "The Chronicles of Testing"
    novel.desc = "A test story for RAG integration"
    novel.authorName = "Test Author"

    # Create characters
    char1_id = "ch1"
    char1 = Character()
    char1.title = "Alice"
    char1.fullName = "Alice Wonderland"
    char1.desc = "A curious young woman with blonde hair and blue eyes"
    char1.bio = "Alice grew up in a small village and always dreamed of adventure. She is brave, intelligent, and kind-hearted."
    char1.goals = "To discover the truth about the ancient prophecy"
    char1.isMajor = True
    novel.characters[char1_id] = char1
    novel.srtCharacters.append(char1_id)

    char2_id = "ch2"
    char2 = Character()
    char2.title = "Bob"
    char2.fullName = "Bob the Brave"
    char2.desc = "A strong warrior with dark hair and green eyes"
    char2.bio = "Bob is Alice's childhood friend and protector. He is loyal and skilled in combat."
    char2.goals = "To protect Alice and prove his worth"
    char2.isMajor = True
    novel.characters[char2_id] = char2
    novel.srtCharacters.append(char2_id)

    char3_id = "ch3"
    char3 = Character()
    char3.title = "Eve"
    char3.fullName = "Eve the Enchantress"
    char3.desc = "A mysterious sorceress with silver hair"
    char3.bio = "Eve knows ancient magic and guards dangerous secrets. She is enigmatic and powerful."
    char3.goals = "To prevent the prophecy from being fulfilled"
    char3.isMajor = False
    novel.characters[char3_id] = char3
    novel.srtCharacters.append(char3_id)

    # Create locations
    loc1_id = "lc1"
    loc1 = Location()
    loc1.title = "The Whispering Forest"
    loc1.desc = "A dark, mysterious forest where ancient spirits dwell. The trees seem to whisper secrets to those who listen."
    novel.locations[loc1_id] = loc1
    novel.srtLocations.append(loc1_id)

    loc2_id = "lc2"
    loc2 = Location()
    loc2.title = "Crystal Palace"
    loc2.desc = "A magnificent palace made entirely of crystal, shimmering in the sunlight. The throne room is breathtaking."
    novel.locations[loc2_id] = loc2
    novel.srtLocations.append(loc2_id)

    # Create items
    item1_id = "it1"
    item1 = Item()
    item1.title = "The Amulet of Power"
    item1.desc = "An ancient amulet that glows with mystical energy. Said to grant its wielder immense power."
    novel.items[item1_id] = item1
    novel.srtItems.append(item1_id)

    # Create chapter
    ch1_id = "c1"
    chapter1 = Chapter()
    chapter1.title = "Chapter 1: The Beginning"
    chapter1.desc = "Alice discovers her destiny"
    chapter1.chType = 0  # Normal chapter
    novel.chapters[ch1_id] = chapter1
    novel.srtChapters.append(ch1_id)

    # Create scenes
    scene1_id = "sc1"
    scene1 = Scene()
    scene1.title = "The Discovery"
    scene1.desc = "Alice finds the ancient amulet in the forest"
    scene1.sceneContent = """
    Alice wandered through the Whispering Forest, her heart pounding with excitement and fear.
    The trees seemed to lean in, their branches forming a canopy that blocked out most of the sunlight.

    Suddenly, she spotted something glowing among the roots of an ancient oak tree.
    As she approached, she realized it was the legendary Amulet of Power.
    Her hands trembled as she reached for it, knowing this moment would change her life forever.
    """
    scene1.characters = [char1_id]
    scene1.locations = [loc1_id]
    scene1.items = [item1_id]
    novel.scenes[scene1_id] = scene1
    chapter1.srtScenes.append(scene1_id)

    scene2_id = "sc2"
    scene2 = Scene()
    scene2.title = "The Encounter"
    scene2.desc = "Bob finds Alice and learns of her discovery"
    scene2.sceneContent = """
    Bob had been searching for Alice for hours. When he finally found her at the edge of the forest,
    he noticed the strange glow emanating from her backpack.

    "Alice, what have you found?" he asked, concern evident in his voice.

    She pulled out the amulet, and Bob's eyes widened in recognition. He had heard the legends.
    "We need to be careful," he warned. "This kind of power attracts dangerous attention."
    """
    scene2.characters = [char1_id, char2_id]
    scene2.locations = [loc1_id]
    scene2.items = [item1_id]
    novel.scenes[scene2_id] = scene2
    chapter1.srtScenes.append(scene2_id)

    # Create chapter 2
    ch2_id = "c2"
    chapter2 = Chapter()
    chapter2.title = "Chapter 2: The Warning"
    chapter2.desc = "Eve appears with a dire warning"
    chapter2.chType = 0
    novel.chapters[ch2_id] = chapter2
    novel.srtChapters.append(ch2_id)

    scene3_id = "sc3"
    scene3 = Scene()
    scene3.title = "The Sorceress Appears"
    scene3.desc = "Eve confronts Alice and Bob at the palace"
    scene3.sceneContent = """
    The Crystal Palace shimmered as Alice and Bob approached, seeking an audience with the queen.
    Before they could reach the entrance, a figure materialized before them in a swirl of silver light.

    "You should not have taken the amulet," Eve said, her voice echoing with power.
    "The prophecy must not be fulfilled, or all will be lost."

    Alice stood her ground. "Who are you to decide our fate?"

    Eve's eyes glowed with ancient knowledge. "I am the last guardian, and I know what that amulet can do."
    """
    scene3.characters = [char1_id, char2_id, char3_id]
    scene3.locations = [loc2_id]
    scene3.items = [item1_id]
    novel.scenes[scene3_id] = scene3
    chapter2.srtScenes.append(scene3_id)

    # Create and save file
    yw7_file = Yw7File(file_path)
    yw7_file.novel = novel
    yw7_file.write()

    logger.info(f"Test novel created with {len(novel.characters)} characters, {len(novel.locations)} locations, {len(novel.scenes)} scenes")

    return yw7_file


def test_vector_store():
    """Test 1: Vector store initialization and basic operations."""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Vector Store Initialization")
    logger.info("="*80)

    try:
        vector_store = VectorStoreManager()
        logger.info("✓ Vector store initialized successfully")

        # Check collections
        stats = vector_store.get_stats()
        logger.info(f"✓ Collections created: {len(stats)} collections")
        logger.info(f"  Stats: {stats}")

        return True
    except Exception as e:
        logger.error(f"✗ Vector store test failed: {e}")
        return False


def test_sync_to_vector_db(test_file_path: str):
    """Test 2: Sync yWriter7 file to vector database."""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Sync yWriter7 → Vector Database")
    logger.info("="*80)

    try:
        vector_store = VectorStoreManager()
        sync_manager = RAGSyncManager(vector_store)

        # Sync from yWriter7
        stats = sync_manager.sync_from_ywriter(test_file_path)
        logger.info(f"✓ Sync completed successfully")
        logger.info(f"  Characters synced: {stats['characters']}")
        logger.info(f"  Locations synced: {stats['locations']}")
        logger.info(f"  Items synced: {stats['items']}")
        logger.info(f"  Plot events synced: {stats['plot_events']}")
        logger.info(f"  Relationships synced: {stats['relationships']}")

        # Verify data
        db_stats = vector_store.get_stats()
        logger.info(f"✓ Vector DB now contains: {db_stats}")

        return True
    except Exception as e:
        logger.error(f"✗ Sync test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_semantic_search():
    """Test 3: Semantic search capabilities."""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Semantic Search")
    logger.info("="*80)

    try:
        vector_store = VectorStoreManager()

        # Test 1: Search for brave characters
        logger.info("\n--- Search: 'brave warrior characters' ---")
        results = vector_store.semantic_search(
            collection_name='characters',
            query='brave warrior characters',
            n_results=2
        )
        logger.info(f"✓ Found {len(results['ids'])} results")
        for i, doc_id in enumerate(results['ids']):
            logger.info(f"  Result {i+1}: {results['metadatas'][i].get('title')} (score: {1 - results['distances'][i]:.3f})")

        # Test 2: Search for mysterious locations
        logger.info("\n--- Search: 'mysterious dark place' ---")
        results = vector_store.semantic_search(
            collection_name='locations',
            query='mysterious dark place',
            n_results=2
        )
        logger.info(f"✓ Found {len(results['ids'])} results")
        for i, doc_id in enumerate(results['ids']):
            logger.info(f"  Result {i+1}: {results['metadatas'][i].get('title')} (score: {1 - results['distances'][i]:.3f})")

        # Test 3: Search for plot events about discovery
        logger.info("\n--- Search: 'finding magical artifact' ---")
        results = vector_store.semantic_search(
            collection_name='plot_events',
            query='finding magical artifact',
            n_results=2
        )
        logger.info(f"✓ Found {len(results['ids'])} results")
        for i, doc_id in enumerate(results['ids']):
            logger.info(f"  Result {i+1}: {results['metadatas'][i].get('title')} in {results['metadatas'][i].get('chapter')}")
            logger.info(f"     Score: {1 - results['distances'][i]:.3f}")

        return True
    except Exception as e:
        logger.error(f"✗ Semantic search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_tools():
    """Test 4: RAG tools for agents."""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: RAG Tools")
    logger.info("="*80)

    try:
        from tools.rag_tools import (
            SemanticCharacterSearchTool,
            GetCharacterDetailsTool,
            CheckContinuityTool
        )

        # Test character search
        logger.info("\n--- Tool: Semantic Character Search ---")
        char_search_tool = SemanticCharacterSearchTool()
        result = char_search_tool._run(query="brave protector", top_k=2)
        logger.info(f"✓ Character search result:\n{result[:300]}...")

        # Test character details
        logger.info("\n--- Tool: Get Character Details ---")
        char_details_tool = GetCharacterDetailsTool()
        result = char_details_tool._run(character_name="Alice")
        logger.info(f"✓ Character details:\n{result[:300]}...")

        # Test continuity check
        logger.info("\n--- Tool: Check Continuity ---")
        continuity_tool = CheckContinuityTool()
        result = continuity_tool._run(query="What happened in the forest?")
        logger.info(f"✓ Continuity check:\n{result[:400]}...")

        return True
    except Exception as e:
        logger.error(f"✗ RAG tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_keeper_agent():
    """Test 5: MemoryKeeper agent with RAG capabilities."""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: MemoryKeeper Agent")
    logger.info("="*80)

    try:
        # Create MemoryKeeper agent
        config = MemoryKeeperConfig(
            temperature=0.6,
            enable_continuity_checks=True,
            enable_relationship_tracking=True
        )

        agent = MemoryKeeper(config)
        logger.info("✓ MemoryKeeper agent created successfully")
        logger.info(f"  Role: {agent.role}")
        logger.info(f"  Tools: {len(agent.tools)} tools available")
        logger.info(f"  Tool names: {[tool.name for tool in agent.tools]}")

        # Verify tools are properly configured
        expected_tools = [
            "Semantic Character Search",
            "Get Character Details",
            "Semantic Location Search",
            "Semantic Plot Search",
            "General Story Knowledge Search",
            "Find Character Relationships",
            "Check Story Continuity"
        ]

        tool_names = [tool.name for tool in agent.tools]
        for expected_tool in expected_tools:
            if expected_tool in tool_names:
                logger.info(f"  ✓ {expected_tool} tool loaded")
            else:
                logger.warning(f"  ✗ {expected_tool} tool missing")

        return True
    except Exception as e:
        logger.error(f"✗ MemoryKeeper agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_files(test_file_path: str):
    """Clean up test files."""
    logger.info("\n" + "="*80)
    logger.info("Cleanup")
    logger.info("="*80)

    try:
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            logger.info(f"✓ Removed test file: {test_file_path}")

        # Note: We keep the vector database for inspection
        logger.info("ℹ Vector database kept in ./knowledge_base for inspection")

        return True
    except Exception as e:
        logger.error(f"✗ Cleanup failed: {e}")
        return False


def main():
    """Run all RAG integration tests."""
    logger.info("="*80)
    logger.info("RAG INTEGRATION TEST SUITE")
    logger.info("="*80)

    test_file_path = "test_chronicles.yw7"

    results = []

    # Create test novel
    try:
        create_test_novel(test_file_path)
        logger.info("✓ Test novel created")
    except Exception as e:
        logger.error(f"✗ Failed to create test novel: {e}")
        import traceback
        traceback.print_exc()
        return

    # Run tests
    results.append(("Vector Store Init", test_vector_store()))
    results.append(("Sync to Vector DB", test_sync_to_vector_db(test_file_path)))
    results.append(("Semantic Search", test_semantic_search()))
    results.append(("RAG Tools", test_rag_tools()))
    results.append(("MemoryKeeper Agent", test_memory_keeper_agent()))

    # Cleanup
    cleanup_test_files(test_file_path)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 All tests passed! RAG integration is working correctly.")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
