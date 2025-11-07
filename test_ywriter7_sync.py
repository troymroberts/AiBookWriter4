#!/usr/bin/env python3
"""
yWriter7 Sync Integration Test Script

Comprehensive test suite for yWriter7 file parsing, export, and bidirectional sync.
Tests the core yWriter7 integration and CrewAI tools for agent interaction.

Usage:
    python test_ywriter7_sync.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.novel import Novel
from ywriter7.model.chapter import Chapter
from ywriter7.model.scene import Scene
from ywriter7.model.character import Character
from ywriter7.model.world_element import WorldElement
from ywriter7.model.project_note import ProjectNote
from ywriter7.model.id_generator import create_id

# Import CrewAI tools
from tools.ywriter_tools import (
    ReadProjectNotesTool,
    ReadCharactersTool,
    ReadLocationsTool,
    ReadOutlineTool,
    ReadSceneTool,
    WriteProjectNoteTool,
    CreateChapterTool,
    WriteSceneContentTool,
)


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text):
    """Print success message."""
    print(f"✅ {text}")


def print_error(text):
    """Print error message."""
    print(f"❌ {text}")


def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")


def create_sample_project(file_path):
    """Create a sample yWriter7 project file for testing.

    Args:
        file_path: Path where the .yw7 file will be created

    Returns:
        Yw7File: The created project
    """
    print_header("Creating Sample yWriter7 Project")

    # Create new project
    yw7_file = Yw7File(file_path)
    yw7_file.novel = Novel()

    # Set project metadata
    yw7_file.novel.title = "AI Book Writer Test Novel"
    yw7_file.novel.desc = "A test novel created by the AI Book Writer application"
    yw7_file.novel.authorName = "AI Book Writer"
    yw7_file.novel.authorBio = "An intelligent book writing system"

    print_info("Creating characters...")
    # Create characters
    char1_id = create_id(yw7_file.novel.characters)
    char1 = Character()
    char1.title = "Alice"
    char1.fullName = "Alice Wonderland"
    char1.desc = "A curious young woman seeking adventure"
    char1.bio = "Alice grew up in a small town and always dreamed of exploring the world."
    char1.goals = "To find her place in the world"
    char1.isMajor = True
    yw7_file.novel.characters[char1_id] = char1
    yw7_file.novel.srtCharacters.append(char1_id)

    char2_id = create_id(yw7_file.novel.characters)
    char2 = Character()
    char2.title = "Bob"
    char2.fullName = "Robert Smith"
    char2.desc = "Alice's mentor and guide"
    char2.bio = "A wise old traveler who has seen much of the world."
    char2.goals = "To help Alice on her journey"
    char2.isMajor = False
    yw7_file.novel.characters[char2_id] = char2
    yw7_file.novel.srtCharacters.append(char2_id)

    print_success(f"Created {len(yw7_file.novel.characters)} characters")

    print_info("Creating locations...")
    # Create locations
    loc1_id = create_id(yw7_file.novel.locations)
    loc1 = WorldElement()
    loc1.title = "The Town Square"
    loc1.desc = "A bustling central plaza where merchants sell their wares"
    loc1.aka = "Central Plaza"
    yw7_file.novel.locations[loc1_id] = loc1
    yw7_file.novel.srtLocations.append(loc1_id)

    loc2_id = create_id(yw7_file.novel.locations)
    loc2 = WorldElement()
    loc2.title = "The Forest Path"
    loc2.desc = "A winding trail through ancient woods"
    yw7_file.novel.locations[loc2_id] = loc2
    yw7_file.novel.srtLocations.append(loc2_id)

    print_success(f"Created {len(yw7_file.novel.locations)} locations")

    print_info("Creating items...")
    # Create items
    item1_id = create_id(yw7_file.novel.items)
    item1 = WorldElement()
    item1.title = "Magic Compass"
    item1.desc = "A mysterious compass that points to one's deepest desire"
    yw7_file.novel.items[item1_id] = item1
    yw7_file.novel.srtItems.append(item1_id)

    print_success(f"Created {len(yw7_file.novel.items)} items")

    print_info("Creating project notes...")
    # Create project notes
    note1_id = create_id(yw7_file.novel.projectNotes)
    note1 = ProjectNote()
    note1.title = "Story Theme"
    note1.desc = "The central theme is self-discovery and finding one's true path in life."
    yw7_file.novel.projectNotes[note1_id] = note1
    yw7_file.novel.srtPrjNotes.append(note1_id)

    note2_id = create_id(yw7_file.novel.projectNotes)
    note2 = ProjectNote()
    note2.title = "Writing Style"
    note2.desc = "Use vivid descriptions and internal monologue to convey Alice's emotional journey."
    yw7_file.novel.projectNotes[note2_id] = note2
    yw7_file.novel.srtPrjNotes.append(note2_id)

    print_success(f"Created {len(yw7_file.novel.projectNotes)} project notes")

    print_info("Creating chapters and scenes...")
    # Create Chapter 1
    ch1_id = create_id(yw7_file.novel.chapters)
    ch1 = Chapter()
    ch1.title = "Chapter 1: The Beginning"
    ch1.desc = "Alice discovers the magic compass in the town square"
    ch1.chLevel = 0
    ch1.chType = 0
    ch1.srtScenes = []

    # Create Scene 1 for Chapter 1
    sc1_id = create_id(yw7_file.novel.scenes)
    sc1 = Scene()
    sc1.title = "Scene 1: Discovery"
    sc1.desc = "Alice finds the compass at a merchant's stall"
    sc1.sceneContent = """Alice wandered through the crowded town square, her eyes scanning the various merchant stalls. The morning sun cast long shadows across the cobblestones.

At a dusty antique stall, something caught her eye—a brass compass with strange engravings. The merchant noticed her interest.

"Ah, that one's special," he said with a knowing smile. "They say it points to your heart's desire."

Alice picked up the compass, and to her amazement, the needle began to spin wildly before settling in a direction that pointed away from town, toward the ancient forest."""
    sc1.characters = [char1_id, char2_id]
    sc1.locations = [loc1_id]
    sc1.items = [item1_id]
    sc1.status = 1  # Draft

    yw7_file.novel.scenes[sc1_id] = sc1
    ch1.srtScenes.append(sc1_id)

    # Create Scene 2 for Chapter 1
    sc2_id = create_id(yw7_file.novel.scenes)
    sc2 = Scene()
    sc2.title = "Scene 2: Meeting Bob"
    sc2.desc = "Alice encounters Bob, who recognizes the compass"
    sc2.sceneContent = """As Alice studied the compass, an old man approached her. His weathered face bore the marks of countless journeys.

"I see you've found the Seeker's Compass," Bob said quietly. "I haven't seen one of those in many years."

Alice looked up, startled. "You know what this is?"

Bob nodded slowly. "Aye, and I know where it's pointing you. That forest path is the beginning of a long journey."

"Will you help me?" Alice asked.

The old traveler smiled. "That's why I'm here, lass. That's why I'm here.\""""
    sc2.characters = [char1_id, char2_id]
    sc2.locations = [loc1_id]
    sc2.items = [item1_id]
    sc2.status = 1

    yw7_file.novel.scenes[sc2_id] = sc2
    ch1.srtScenes.append(sc2_id)

    yw7_file.novel.chapters[ch1_id] = ch1
    yw7_file.novel.srtChapters.append(ch1_id)

    # Create Chapter 2
    ch2_id = create_id(yw7_file.novel.chapters)
    ch2 = Chapter()
    ch2.title = "Chapter 2: Into the Woods"
    ch2.desc = "Alice and Bob venture into the mysterious forest"
    ch2.chLevel = 0
    ch2.chType = 0
    ch2.srtScenes = []

    # Create Scene 1 for Chapter 2
    sc3_id = create_id(yw7_file.novel.scenes)
    sc3 = Scene()
    sc3.title = "Scene 1: The Forest Path"
    sc3.desc = "They enter the ancient forest following the compass"
    sc3.sceneContent = """The forest path was overgrown and dark, sunlight filtering through the canopy in scattered beams. Alice held the compass steady as it guided them deeper into the woods.

"How long have you been traveling, Bob?" Alice asked.

"More years than I care to count," he replied. "But every journey teaches you something new."

The compass needle suddenly shifted, pointing to a barely visible trail branching off to the left."""
    sc3.characters = [char1_id, char2_id]
    sc3.locations = [loc2_id]
    sc3.items = [item1_id]
    sc3.status = 1

    yw7_file.novel.scenes[sc3_id] = sc3
    ch2.srtScenes.append(sc3_id)

    yw7_file.novel.chapters[ch2_id] = ch2
    yw7_file.novel.srtChapters.append(ch2_id)

    print_success(f"Created {len(yw7_file.novel.chapters)} chapters with {len(yw7_file.novel.scenes)} scenes")

    # Write the file
    print_info(f"Writing project to: {file_path}")
    yw7_file.write()
    print_success("Sample project created successfully!")

    return yw7_file


def test_read_operations(file_path):
    """Test reading operations from yWriter7 file.

    Args:
        file_path: Path to the .yw7 file to read

    Returns:
        bool: True if all tests pass
    """
    print_header("Test 1: Read Operations")

    try:
        yw7_file = Yw7File(file_path)
        yw7_file.read()

        # Test project metadata
        print_info("Testing project metadata...")
        assert yw7_file.novel.title == "AI Book Writer Test Novel"
        assert yw7_file.novel.authorName == "AI Book Writer"
        print_success(f"Project title: {yw7_file.novel.title}")
        print_success(f"Author: {yw7_file.novel.authorName}")

        # Test characters
        print_info("Testing characters...")
        assert len(yw7_file.novel.characters) == 2
        char_names = [yw7_file.novel.characters[cid].title for cid in yw7_file.novel.srtCharacters]
        assert "Alice" in char_names
        assert "Bob" in char_names
        print_success(f"Characters: {', '.join(char_names)}")

        # Test locations
        print_info("Testing locations...")
        assert len(yw7_file.novel.locations) == 2
        loc_names = [yw7_file.novel.locations[lid].title for lid in yw7_file.novel.srtLocations]
        print_success(f"Locations: {', '.join(loc_names)}")

        # Test items
        print_info("Testing items...")
        assert len(yw7_file.novel.items) == 1
        item_names = [yw7_file.novel.items[iid].title for iid in yw7_file.novel.srtItems]
        print_success(f"Items: {', '.join(item_names)}")

        # Test project notes
        print_info("Testing project notes...")
        assert len(yw7_file.novel.projectNotes) == 2
        note_titles = [yw7_file.novel.projectNotes[nid].title for nid in yw7_file.novel.srtPrjNotes]
        print_success(f"Project notes: {', '.join(note_titles)}")

        # Test chapters and scenes
        print_info("Testing chapters and scenes...")
        assert len(yw7_file.novel.chapters) == 2
        assert len(yw7_file.novel.scenes) == 3
        print_success(f"Chapters: {len(yw7_file.novel.chapters)}")
        print_success(f"Scenes: {len(yw7_file.novel.scenes)}")

        # Test scene content
        print_info("Testing scene content...")
        first_scene_id = yw7_file.novel.chapters[yw7_file.novel.srtChapters[0]].srtScenes[0]
        first_scene = yw7_file.novel.scenes[first_scene_id]
        assert first_scene.sceneContent is not None
        assert len(first_scene.sceneContent) > 0
        print_success(f"Scene content length: {len(first_scene.sceneContent)} characters")

        # Test character associations
        print_info("Testing character associations in scenes...")
        assert first_scene.characters is not None
        assert len(first_scene.characters) == 2
        print_success(f"Scene has {len(first_scene.characters)} characters")

        return True

    except Exception as e:
        print_error(f"Read operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_write_operations(file_path):
    """Test writing operations to yWriter7 file.

    Args:
        file_path: Path to the .yw7 file to modify

    Returns:
        bool: True if all tests pass
    """
    print_header("Test 2: Write Operations")

    try:
        # Read the existing file
        yw7_file = Yw7File(file_path)
        yw7_file.read()

        # Add a new character
        print_info("Adding new character...")
        char_id = create_id(yw7_file.novel.characters)
        new_char = Character()
        new_char.title = "Charlie"
        new_char.fullName = "Charles Explorer"
        new_char.desc = "A fellow adventurer Alice meets on the path"
        new_char.isMajor = False
        yw7_file.novel.characters[char_id] = new_char
        yw7_file.novel.srtCharacters.append(char_id)
        print_success(f"Added character: {new_char.title}")

        # Add a new location
        print_info("Adding new location...")
        loc_id = create_id(yw7_file.novel.locations)
        new_loc = WorldElement()
        new_loc.title = "The Hidden Glade"
        new_loc.desc = "A secret clearing deep in the forest"
        yw7_file.novel.locations[loc_id] = new_loc
        yw7_file.novel.srtLocations.append(loc_id)
        print_success(f"Added location: {new_loc.title}")

        # Update a scene's content
        print_info("Updating scene content...")
        first_scene_id = yw7_file.novel.chapters[yw7_file.novel.srtChapters[0]].srtScenes[0]
        first_scene = yw7_file.novel.scenes[first_scene_id]
        original_content = first_scene.sceneContent
        first_scene.sceneContent += "\n\n[Updated by test suite]"
        print_success("Updated scene content")

        # Write changes
        print_info("Writing changes to file...")
        yw7_file.write()
        print_success("Changes written successfully")

        # Read back and verify
        print_info("Verifying changes...")
        yw7_file_verify = Yw7File(file_path)
        yw7_file_verify.read()

        assert len(yw7_file_verify.novel.characters) == 3
        assert len(yw7_file_verify.novel.locations) == 3

        verify_scene = yw7_file_verify.novel.scenes[first_scene_id]
        assert "[Updated by test suite]" in verify_scene.sceneContent

        print_success("All write operations verified!")
        return True

    except Exception as e:
        print_error(f"Write operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crewai_tools(file_path):
    """Test CrewAI tools for agent interaction with yWriter7 files.

    Args:
        file_path: Path to the .yw7 file

    Returns:
        bool: True if all tests pass
    """
    print_header("Test 3: CrewAI Tools Integration")

    try:
        # Test ReadProjectNotesTool
        print_info("Testing ReadProjectNotesTool...")
        read_notes_tool = ReadProjectNotesTool()
        notes_result = read_notes_tool._run(yw7_path=file_path)
        assert "Story Theme" in notes_result
        print_success("ReadProjectNotesTool works!")

        # Test ReadCharactersTool
        print_info("Testing ReadCharactersTool...")
        read_chars_tool = ReadCharactersTool()
        chars_result = read_chars_tool._run(yw7_path=file_path)
        assert "Alice" in chars_result
        assert "Bob" in chars_result
        print_success("ReadCharactersTool works!")

        # Test ReadLocationsTool
        print_info("Testing ReadLocationsTool...")
        read_locs_tool = ReadLocationsTool()
        locs_result = read_locs_tool._run(yw7_path=file_path)
        assert "Town Square" in locs_result or "The Town Square" in locs_result
        print_success("ReadLocationsTool works!")

        # Test ReadOutlineTool
        print_info("Testing ReadOutlineTool...")
        read_outline_tool = ReadOutlineTool()
        outline_result = read_outline_tool._run(yw7_path=file_path)
        assert "Chapter 1" in outline_result
        assert "Discovery" in outline_result
        print_success("ReadOutlineTool works!")

        # Test ReadSceneTool
        print_info("Testing ReadSceneTool...")
        # Get first scene ID
        yw7_file = Yw7File(file_path)
        yw7_file.read()
        first_scene_id = yw7_file.novel.chapters[yw7_file.novel.srtChapters[0]].srtScenes[0]

        read_scene_tool = ReadSceneTool()
        scene_result = read_scene_tool._run(yw7_path=file_path, scene_id=first_scene_id)
        assert "Discovery" in scene_result
        print_success("ReadSceneTool works!")

        # Test WriteProjectNoteTool
        print_info("Testing WriteProjectNoteTool...")
        write_note_tool = WriteProjectNoteTool()
        note_result = write_note_tool._run(
            yw7_path=file_path,
            title="Test Note from CrewAI Tool",
            content="This note was created by the automated test suite using CrewAI tools."
        )
        assert "written successfully" in note_result
        print_success("WriteProjectNoteTool works!")

        # Test CreateChapterTool
        print_info("Testing CreateChapterTool...")
        create_chapter_tool = CreateChapterTool()
        chapter_result = create_chapter_tool._run(
            yw7_path=file_path,
            title="Chapter 3: Test Chapter",
            description="A test chapter created by the automated test suite"
        )
        assert "created successfully" in chapter_result
        print_success("CreateChapterTool works!")

        # Test WriteSceneContentTool
        print_info("Testing WriteSceneContentTool...")
        write_scene_tool = WriteSceneContentTool()
        scene_write_result = write_scene_tool._run(
            yw7_path=file_path,
            scene_id=first_scene_id,
            content="This content was written by the CrewAI WriteSceneContentTool during automated testing."
        )
        assert "written" in scene_write_result.lower()
        print_success("WriteSceneContentTool works!")

        print_success("All CrewAI tools work correctly!")
        return True

    except Exception as e:
        print_error(f"CrewAI tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bidirectional_sync(file_path):
    """Test bidirectional sync between agents and yWriter7.

    Args:
        file_path: Path to the .yw7 file

    Returns:
        bool: True if all tests pass
    """
    print_header("Test 4: Bidirectional Sync")

    try:
        print_info("Testing read → modify → write → read cycle...")

        # Step 1: Read original
        yw7_file = Yw7File(file_path)
        yw7_file.read()
        original_char_count = len(yw7_file.novel.characters)
        print_success(f"Initial read: {original_char_count} characters")

        # Step 2: Modify via tools
        write_note_tool = WriteProjectNoteTool()
        write_note_tool._run(
            yw7_path=file_path,
            title="Sync Test Note",
            content="Testing bidirectional sync"
        )
        print_success("Modified via CrewAI tool")

        # Step 3: Read back via different instance
        yw7_file2 = Yw7File(file_path)
        yw7_file2.read()

        # Verify the change persisted
        note_found = False
        for note_id in yw7_file2.novel.srtPrjNotes:
            if yw7_file2.novel.projectNotes[note_id].title == "Sync Test Note":
                note_found = True
                break

        assert note_found, "Note not found after sync"
        print_success("Changes persisted correctly")

        # Step 4: Modify via direct API
        new_char_id = create_id(yw7_file2.novel.characters)
        sync_char = Character()
        sync_char.title = "Sync Test Character"
        sync_char.desc = "Created to test bidirectional sync"
        yw7_file2.novel.characters[new_char_id] = sync_char
        yw7_file2.novel.srtCharacters.append(new_char_id)
        yw7_file2.write()
        print_success("Modified via direct API")

        # Step 5: Verify via tools
        read_chars_tool = ReadCharactersTool()
        chars_result = read_chars_tool._run(yw7_path=file_path)
        assert "Sync Test Character" in chars_result
        print_success("Changes visible to tools")

        print_success("Bidirectional sync works correctly!")
        return True

    except Exception as e:
        print_error(f"Bidirectional sync test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all yWriter7 sync tests."""
    print_header("yWriter7 Sync Integration Tests")
    print("This script tests yWriter7 file parsing, export, and bidirectional sync.\n")

    # Setup
    test_file = "output/test_novel.yw7"
    os.makedirs("output", exist_ok=True)

    # Clean up any existing test file
    if os.path.exists(test_file):
        os.remove(test_file)
        print_info(f"Removed existing test file: {test_file}")

    # Run tests
    results = []

    # Create sample project
    try:
        create_sample_project(test_file)
        results.append(("Project Creation", True))
    except Exception as e:
        print_error(f"Failed to create sample project: {e}")
        results.append(("Project Creation", False))
        return 1

    # Test read operations
    results.append(("Read Operations", test_read_operations(test_file)))

    # Test write operations
    results.append(("Write Operations", test_write_operations(test_file)))

    # Test CrewAI tools
    results.append(("CrewAI Tools", test_crewai_tools(test_file)))

    # Test bidirectional sync
    results.append(("Bidirectional Sync", test_bidirectional_sync(test_file)))

    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print("\n" + "=" * 70)
    if passed == total:
        print_success(f"All tests passed! ({passed}/{total})")
        print_info(f"Test file created at: {test_file}")
        print_info("You can open this file in yWriter7 to inspect it!")
        print_info("\nNext steps:")
        print("  1. Integrate RAG (vector database) for knowledge keeper agents")
        print("  2. Create MemoryKeeper agent to track story progression")
        print("  3. Implement query/update interfaces for knowledge keepers")
        return 0
    else:
        print_error(f"Some tests failed ({passed}/{total} passed)")
        print_info("Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
