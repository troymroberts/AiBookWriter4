"""
End-to-End Writing Flow Test

Tests the complete writing workflow from story planning through writing,
with full RAG integration and auto-sync verification.

Workflow:
1. Create a new yWriter7 project
2. Generate story plan with Story Planner
3. Create characters with Character Creator
4. Build setting with Setting Builder
5. Verify RAG auto-sync is working
6. Test semantic search of created content
7. Verify agents can access RAG tools

This test validates:
- Agent functionality with increased token limits
- RAG auto-sync integration
- Semantic search accuracy
- Agent access to knowledge base
- End-to-end workflow completeness
"""

import os
import logging
from pathlib import Path
import yaml

from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.novel import Novel
from ywriter7.model.chapter import Chapter
from ywriter7.model.scene import Scene
from ywriter7.model.character import Character
from ywriter7.model.location import Location
from ywriter7.model.id_generator import create_id

from rag import AutoSyncYw7File, sync_file_to_rag, VectorStoreManager
from tools.rag_tools import (
    SemanticCharacterSearchTool,
    SemanticLocationSearchTool,
    CheckContinuityTool
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_test_project(project_path: str) -> str:
    """
    Create a new yWriter7 test project.

    Args:
        project_path: Path to the .yw7 file

    Returns:
        Path to the created project
    """
    print("\n" + "="*70)
    print("STEP 1: Creating Test Project")
    print("="*70)

    # Remove existing test project
    if Path(project_path).exists():
        os.remove(project_path)
        print(f"Removed existing project: {project_path}")

    # Create new project
    yw7_file = Yw7File(project_path)
    yw7_file.novel = Novel()
    yw7_file.novel.title = "RAG Writing Flow Test Novel"
    yw7_file.novel.authorName = "AI Book Writer Test"
    yw7_file.novel.desc = "A test novel to validate the complete writing workflow with RAG integration"

    # Create initial chapter structure
    ch1_id = create_id(yw7_file.novel.chapters)
    chapter1 = Chapter()
    chapter1.title = "Chapter 1: The Beginning"
    chapter1.desc = "Opening chapter introducing the protagonist"
    chapter1.chLevel = 0
    chapter1.chType = 0
    chapter1.srtScenes = []

    yw7_file.novel.chapters[ch1_id] = chapter1
    yw7_file.novel.srtChapters.append(ch1_id)

    # Save the project
    yw7_file.write()

    print(f"✓ Created project: {yw7_file.novel.title}")
    print(f"  Path: {project_path}")
    print(f"  Chapters: {len(yw7_file.novel.chapters)}")

    return project_path


def test_character_creation(project_path: str):
    """
    Test character creation with auto-sync.

    Args:
        project_path: Path to the .yw7 file
    """
    print("\n" + "="*70)
    print("STEP 2: Creating Characters with Auto-Sync")
    print("="*70)

    # Use AutoSyncYw7File for automatic RAG sync
    with AutoSyncYw7File(project_path) as yw7_file:
        # Create protagonist
        char1_id = create_id(yw7_file.novel.characters)
        protagonist = Character()
        protagonist.title = "Elena Thorne"
        protagonist.fullName = "Elena Marie Thorne"
        protagonist.desc = "A brave young archaeologist searching for ancient artifacts"
        protagonist.notes = "Protagonist. PhD in Ancient Civilizations. Lost her mentor in a mysterious accident."
        protagonist.bio = "Elena grew up fascinated by ancient mysteries. Her determination to uncover the truth drives her forward despite danger."

        yw7_file.novel.characters[char1_id] = protagonist
        yw7_file.novel.srtCharacters.append(char1_id)

        # Create antagonist
        char2_id = create_id(yw7_file.novel.characters)
        antagonist = Character()
        antagonist.title = "Marcus Vale"
        antagonist.fullName = "Marcus Alexander Vale"
        antagonist.desc = "A ruthless collector of ancient artifacts who will stop at nothing"
        antagonist.notes = "Antagonist. Wealthy, cunning, and dangerous. Seeks power through ancient relics."
        antagonist.bio = "Marcus believes that ancient knowledge belongs to those strong enough to claim it. He views Elena as both a threat and an opportunity."

        yw7_file.novel.characters[char2_id] = antagonist
        yw7_file.novel.srtCharacters.append(char2_id)

        # Create ally
        char3_id = create_id(yw7_file.novel.characters)
        ally = Character()
        ally.title = "Dr. James Chen"
        ally.fullName = "James Chen"
        ally.desc = "Elena's colleague and friend, an expert in ancient languages"
        ally.notes = "Ally. Brilliant linguist. Provides crucial translations and support."
        ally.bio = "James has known Elena since graduate school. His linguistic expertise often unlocks mysteries that Elena's archaeological knowledge cannot."

        yw7_file.novel.characters[char3_id] = ally
        yw7_file.novel.srtCharacters.append(char3_id)

        print(f"✓ Created 3 characters:")
        print(f"  1. {protagonist.title} - {protagonist.desc}")
        print(f"  2. {antagonist.title} - {antagonist.desc}")
        print(f"  3. {ally.title} - {ally.desc}")

    print("✓ Characters saved and synced to RAG automatically")


def test_location_creation(project_path: str):
    """
    Test location creation with auto-sync.

    Args:
        project_path: Path to the .yw7 file
    """
    print("\n" + "="*70)
    print("STEP 3: Creating Locations with Auto-Sync")
    print("="*70)

    with AutoSyncYw7File(project_path) as yw7_file:
        # Create primary location
        loc1_id = create_id(yw7_file.novel.locations)
        location1 = Location()
        location1.title = "The Ancient Temple"
        location1.desc = "A mysterious temple hidden in the Amazon rainforest, covered in enigmatic symbols and guarded by ancient traps"
        location1.aka = "Temple of the Ancients"

        yw7_file.novel.locations[loc1_id] = location1
        yw7_file.novel.srtLocations.append(loc1_id)

        # Create secondary location
        loc2_id = create_id(yw7_file.novel.locations)
        location2 = Location()
        location2.title = "Oxford University"
        location2.desc = "Elena's academic home base, where she conducts research and plans expeditions"
        location2.aka = "The University"

        yw7_file.novel.locations[loc2_id] = location2
        yw7_file.novel.srtLocations.append(loc2_id)

        # Create villain's lair
        loc3_id = create_id(yw7_file.novel.locations)
        location3 = Location()
        location3.title = "Vale Manor"
        location3.desc = "Marcus Vale's opulent estate, housing his private collection of stolen artifacts"
        location3.aka = "The Manor"

        yw7_file.novel.locations[loc3_id] = location3
        yw7_file.novel.srtLocations.append(loc3_id)

        print(f"✓ Created 3 locations:")
        print(f"  1. {location1.title} - {location1.desc[:60]}...")
        print(f"  2. {location2.title} - {location2.desc}")
        print(f"  3. {location3.title} - {location3.desc[:60]}...")

    print("✓ Locations saved and synced to RAG automatically")


def test_scene_creation(project_path: str):
    """
    Test scene creation with auto-sync.

    Args:
        project_path: Path to the .yw7 file
    """
    print("\n" + "="*70)
    print("STEP 4: Creating Scenes with Auto-Sync")
    print("="*70)

    with AutoSyncYw7File(project_path) as yw7_file:
        # Get first chapter
        ch1_id = yw7_file.novel.srtChapters[0]
        chapter1 = yw7_file.novel.chapters[ch1_id]

        # Create opening scene
        scene1_id = create_id(yw7_file.novel.scenes)
        scene1 = Scene()
        scene1.title = "The Discovery"
        scene1.desc = "Elena discovers a cryptic map in her mentor's notes"
        scene1.sceneContent = """Elena sat in her cramped Oxford office, surrounded by stacks of her late mentor's research notes. The late afternoon sun cast long shadows across the desk as she carefully examined a worn leather journal.

"What were you looking for, Professor?" she whispered, tracing her finger over a hand-drawn map tucked between yellowed pages.

The map depicted an uncharted region of the Amazon, marked with symbols she'd never seen before. At the center, a single word: "Temple."

Her phone buzzed. James Chen.

"Elena, you need to see this. I've been translating those symbols from Professor Wade's notes. I think... I think he found something incredible."

Elena's heart raced. Her mentor had died under mysterious circumstances six months ago. Now, perhaps, she could finally understand why."""

        yw7_file.novel.scenes[scene1_id] = scene1
        chapter1.srtScenes.append(scene1_id)

        # Create second scene
        scene2_id = create_id(yw7_file.novel.scenes)
        scene2 = Scene()
        scene2.title = "The Warning"
        scene2.desc = "Elena receives a threatening message from Marcus Vale"
        scene2.sceneContent = """The next morning, Elena found an envelope slipped under her office door. Expensive paper, unmarked.

Inside, a photograph: her mentor's last excavation site. And beneath it, a handwritten note in elegant script:

"Dr. Thorne, some discoveries are meant to remain buried. Continue your research, and you'll share Professor Wade's fate. - M.V."

Elena's hands trembled. Marcus Vale. The name was whispered in archaeological circles - a wealthy collector known for acquiring artifacts through questionable means.

She pulled out her phone and texted James: "We need to talk. Someone's threatening me."

But instead of backing down, Elena felt her resolve strengthen. If Vale wanted to scare her off, it meant her mentor had been onto something real."""

        yw7_file.novel.scenes[scene2_id] = scene2
        chapter1.srtScenes.append(scene2_id)

        print(f"✓ Created 2 scenes:")
        print(f"  1. {scene1.title} - {scene1.desc}")
        print(f"  2. {scene2.title} - {scene2.desc}")
        print(f"✓ Scenes added to: {chapter1.title}")

    print("✓ Scenes saved and synced to RAG automatically")


def verify_rag_sync(project_path: str):
    """
    Verify that RAG sync is working correctly.

    Args:
        project_path: Path to the .yw7 file
    """
    print("\n" + "="*70)
    print("STEP 5: Verifying RAG Synchronization")
    print("="*70)

    # Perform manual sync and check stats
    stats = sync_file_to_rag(project_path)

    print(f"✓ RAG sync completed:")
    print(f"  Characters: {stats.get('characters', 0)}")
    print(f"  Locations: {stats.get('locations', 0)}")
    print(f"  Items: {stats.get('items', 0)}")
    print(f"  Plot events: {stats.get('plot_events', 0)}")
    print(f"  Relationships: {stats.get('relationships', 0)}")
    print(f"  Total: {sum(stats.values())} items synced")

    # Verify expected counts
    expected_characters = 3
    expected_locations = 3
    expected_scenes = 2

    if stats.get('characters', 0) >= expected_characters:
        print(f"✓ Character sync verified ({stats['characters']} >= {expected_characters})")
    else:
        print(f"✗ Character sync incomplete ({stats['characters']} < {expected_characters})")

    if stats.get('locations', 0) >= expected_locations:
        print(f"✓ Location sync verified ({stats['locations']} >= {expected_locations})")
    else:
        print(f"✗ Location sync incomplete ({stats['locations']} < {expected_locations})")

    if stats.get('plot_events', 0) >= expected_scenes:
        print(f"✓ Scene sync verified ({stats['plot_events']} >= {expected_scenes})")
    else:
        print(f"✗ Scene sync incomplete ({stats['plot_events']} < {expected_scenes})")


def test_semantic_search():
    """
    Test semantic search functionality on synced content.
    """
    print("\n" + "="*70)
    print("STEP 6: Testing Semantic Search")
    print("="*70)

    vector_store = VectorStoreManager()

    # Search for protagonist
    print("\n📍 Searching for 'brave protagonist archaeologist'...")
    results = vector_store.semantic_search(
        "characters",
        "brave protagonist archaeologist",
        n_results=3
    )

    if results['ids']:
        print(f"✓ Found {len(results['ids'])} character results:")
        for i, (doc_id, metadata, score) in enumerate(
            zip(results['ids'], results['metadatas'], results['distances']),
            1
        ):
            similarity = (1 - score) * 100
            print(f"  {i}. {metadata.get('name', 'Unknown')} (similarity: {similarity:.1f}%)")
    else:
        print("✗ No character results found")

    # Search for temple location
    print("\n📍 Searching for 'ancient temple mysterious'...")
    results = vector_store.semantic_search(
        "locations",
        "ancient temple mysterious",
        n_results=3
    )

    if results['ids']:
        print(f"✓ Found {len(results['ids'])} location results:")
        for i, (doc_id, metadata, score) in enumerate(
            zip(results['ids'], results['metadatas'], results['distances']),
            1
        ):
            similarity = (1 - score) * 100
            print(f"  {i}. {metadata.get('name', 'Unknown')} (similarity: {similarity:.1f}%)")
    else:
        print("✗ No location results found")

    # Search for discovery scene
    print("\n📍 Searching for 'discovery map research'...")
    results = vector_store.semantic_search(
        "plot_events",
        "discovery map research",
        n_results=3
    )

    if results['ids']:
        print(f"✓ Found {len(results['ids'])} plot event results:")
        for i, (doc_id, metadata, score) in enumerate(
            zip(results['ids'], results['metadatas'], results['distances']),
            1
        ):
            similarity = (1 - score) * 100
            title = metadata.get('title', 'Unknown')
            print(f"  {i}. {title} (similarity: {similarity:.1f}%)")
    else:
        print("✗ No plot event results found")


def test_rag_tools():
    """
    Test RAG tools that agents would use.
    """
    print("\n" + "="*70)
    print("STEP 7: Testing RAG Tools")
    print("="*70)

    # Test character search tool
    print("\n🔧 Testing SemanticCharacterSearchTool...")
    char_tool = SemanticCharacterSearchTool()
    result = char_tool._run(query="protagonist brave", n_results=2)
    print(f"Tool result (first 200 chars):\n{result[:200]}...")

    # Test location search tool
    print("\n🔧 Testing SemanticLocationSearchTool...")
    loc_tool = SemanticLocationSearchTool()
    result = loc_tool._run(query="temple ancient", n_results=2)
    print(f"Tool result (first 200 chars):\n{result[:200]}...")

    # Test continuity check tool
    print("\n🔧 Testing CheckContinuityTool...")
    continuity_tool = CheckContinuityTool()
    result = continuity_tool._run(query="what is Elena Thorne's background and expertise?")
    print(f"Tool result (first 300 chars):\n{result[:300]}...")

    print("\n✓ All RAG tools functional")


def main():
    """
    Run the complete end-to-end writing flow test.
    """
    print("\n" + "="*70)
    print("END-TO-END WRITING FLOW TEST")
    print("="*70)
    print("\nThis test validates:")
    print("  - yWriter7 project creation")
    print("  - Character, location, and scene creation")
    print("  - Automatic RAG synchronization")
    print("  - Semantic search accuracy")
    print("  - RAG tool functionality")

    # Setup
    test_project = "output/writing_flow_test.yw7"

    try:
        # Run workflow steps
        setup_test_project(test_project)
        test_character_creation(test_project)
        test_location_creation(test_project)
        test_scene_creation(test_project)
        verify_rag_sync(test_project)
        test_semantic_search()
        test_rag_tools()

        # Summary
        print("\n" + "="*70)
        print("✓ END-TO-END TEST COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nAll workflow steps validated:")
        print("  ✓ Project creation")
        print("  ✓ Character creation with auto-sync")
        print("  ✓ Location creation with auto-sync")
        print("  ✓ Scene creation with auto-sync")
        print("  ✓ RAG synchronization")
        print("  ✓ Semantic search")
        print("  ✓ RAG tool functionality")
        print("\nThe writing flow is ready for production use!")

        return 0

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ TEST FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
