"""
Complete 10-Chapter Workflow Test

Tests the enhanced workflow with:
- 10 chapters with proper progression
- Full scene structure (goal/conflict/outcome)
- Character creation with bio/notes/goals/aka
- Location creation with alternate names
- Actual prose generation (not placeholders)
- Editorial refinement
- Complete story arc with beginning/middle/end
"""

import os
import logging
from pathlib import Path
from datetime import datetime

from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.novel import Novel
from ywriter7.model.chapter import Chapter
from ywriter7.model.scene import Scene
from ywriter7.model.character import Character
from ywriter7.model.location import Location
from ywriter7.model.id_generator import create_id

from rag import AutoSyncYw7File, sync_file_to_rag
from config.llm_config import get_llm_config

# Import agents
from agents.story_planner import StoryPlanner, StoryPlannerConfig
from agents.character_creator import CharacterCreator, CharacterCreatorConfig
from agents.setting_builder import SettingBuilder, SettingBuilderConfig
from agents.outline_creator import OutlineCreator, OutlineCreatorConfig
from agents.writer import Writer, WriterConfig
from agents.editor import Editor, EditorConfig

# Import CrewAI
from crewai import Crew, Task, Process

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_step(step_num: int, title: str):
    """Print a formatted step header."""
    print("\n" + "="*80)
    print(f"STEP {step_num}: {title}")
    print("="*80)


def test_complete_workflow():
    """Run the complete 10-chapter workflow test."""

    start_time = datetime.now()
    print("\n" + "🚀 "*20)
    print("COMPLETE 10-CHAPTER WORKFLOW TEST")
    print("🚀 "*20)

    # Configuration
    project_name = "Ten_Chapter_Novel"
    project_path = f"output/{project_name.lower()}.yw7"
    genre = "science fiction"
    num_chapters = 10

    # Load config
    config = get_llm_config()

    print(f"\nProject: {project_name}")
    print(f"Genre: {genre}")
    print(f"Chapters: {num_chapters}")
    print(f"Output: {project_path}")

    # ============================================================
    # STEP 1: Story Planning
    # ============================================================
    print_step(1, "Story Planning")

    # Create initial project
    Path("output").mkdir(exist_ok=True)
    if Path(project_path).exists():
        os.remove(project_path)

    yw7_file = Yw7File(project_path)
    yw7_file.novel = Novel()
    yw7_file.novel.title = project_name.replace('_', ' ')
    yw7_file.novel.authorName = "AI Book Writer"
    yw7_file.novel.desc = f"A {genre} novel created with enhanced workflow"
    yw7_file.write()

    print("✓ Project initialized")

    # Initialize Story Planner
    planner_config = StoryPlannerConfig(
        temperature=0.7,
        max_tokens=12288,
    )
    story_planner = StoryPlanner(config=planner_config)

    story_task = Task(
        description=f"""Create a compelling {genre} story arc for a {num_chapters}-chapter novel.

        Requirements:
        - Complete three-act structure
        - Clear beginning (setup), middle (confrontation), and end (resolution)
        - Protagonist with clear goal and character arc
        - Antagonist with believable motivation
        - Rising tension and stakes throughout
        - Satisfying conclusion

        Include:
        - Overall story premise and themes
        - Character arcs (protagonist, antagonist, 2-3 supporting characters)
        - Key plot points for each act
        - Chapter-by-chapter progression showing how story builds
        - Thematic elements

        Ensure the story has proper progression from chapter 1 through {num_chapters} with a complete narrative arc.""",
        agent=story_planner,
        expected_output="Comprehensive story arc with complete beginning/middle/end structure"
    )

    print("Running Story Planner...")
    story_crew = Crew(
        agents=[story_planner],
        tasks=[story_task],
        process=Process.sequential,
        verbose=True
    )

    story_result = story_crew.kickoff()
    story_arc = str(story_result)

    print(f"✓ Story arc created ({len(story_arc)} characters)")
    print(f"\nStory Preview:\n{story_arc[:500]}...\n")

    # Save to project
    with AutoSyncYw7File(project_path) as yw7:
        yw7.novel.desc = story_arc[:500]

    # ============================================================
    # STEP 2: Character Creation with Full Profiles
    # ============================================================
    print_step(2, "Character Creation with Bio/Notes/Goals/AKA")

    char_config = CharacterCreatorConfig(
        temperature=0.7,
        max_tokens=6144,
    )
    character_creator = CharacterCreator(config=char_config)

    char_task = Task(
        description=f"""Based on the story arc, create 4-5 detailed character profiles:

        Story Context:
        {story_arc[:1500]}

        Create characters with:
        - Full names and physical descriptions
        - Detailed backstories and motivations
        - Character arcs showing development
        - Relationships with other characters
        - Nicknames or alternate names (AKA)
        - Clear story goals
        - Major vs minor character designation

        Format as structured data:
        CHARACTER: [name]
        FULLNAME: [full name]
        AKA: [nicknames, alternate names]
        DESC: [brief description]
        BIO: [detailed biography, background, personality]
        NOTES: [character development notes, arc notes]
        GOALS: [what the character wants to achieve in the story]
        MAJOR: [YES or NO]
        ---""",
        agent=character_creator,
        expected_output="4-5 detailed character profiles with all fields"
    )

    print("Running Character Creator...")
    char_crew = Crew(
        agents=[character_creator],
        tasks=[char_task],
        process=Process.sequential,
        verbose=True
    )

    char_result = char_crew.kickoff()
    char_text = str(char_result)

    # Parse and create characters
    with AutoSyncYw7File(project_path) as yw7:
        current_char_data = {}
        lines = char_text.split('\n')

        for line in lines:
            line = line.strip()

            if line.startswith('CHARACTER:'):
                if current_char_data.get('name'):
                    char_id = create_id(yw7.novel.characters)
                    character = Character()
                    character.title = current_char_data.get('name', 'Unnamed')
                    character.fullName = current_char_data.get('fullname', character.title)
                    character.aka = current_char_data.get('aka', '')
                    character.desc = current_char_data.get('desc', '')
                    character.bio = current_char_data.get('bio', '')
                    character.notes = current_char_data.get('notes', '')
                    character.goals = current_char_data.get('goals', '')
                    character.isMajor = True if current_char_data.get('major', 'YES') == 'YES' else False

                    yw7.novel.characters[char_id] = character
                    yw7.novel.srtCharacters.append(char_id)
                    print(f"  ✓ Created: {character.title} (Major: {character.isMajor})")

                current_char_data = {'name': line.replace('CHARACTER:', '').strip()}

            elif line.startswith('FULLNAME:'):
                current_char_data['fullname'] = line.replace('FULLNAME:', '').strip()
            elif line.startswith('AKA:'):
                current_char_data['aka'] = line.replace('AKA:', '').strip()
            elif line.startswith('DESC:'):
                current_char_data['desc'] = line.replace('DESC:', '').strip()
            elif line.startswith('BIO:'):
                current_char_data['bio'] = line.replace('BIO:', '').strip()
            elif line.startswith('NOTES:'):
                current_char_data['notes'] = line.replace('NOTES:', '').strip()
            elif line.startswith('GOALS:'):
                current_char_data['goals'] = line.replace('GOALS:', '').strip()
            elif line.startswith('MAJOR:'):
                current_char_data['major'] = line.replace('MAJOR:', '').strip()

        # Save last character
        if current_char_data.get('name'):
            char_id = create_id(yw7.novel.characters)
            character = Character()
            character.title = current_char_data.get('name', 'Unnamed')
            character.fullName = current_char_data.get('fullname', character.title)
            character.aka = current_char_data.get('aka', '')
            character.desc = current_char_data.get('desc', '')
            character.bio = current_char_data.get('bio', '')
            character.notes = current_char_data.get('notes', '')
            character.goals = current_char_data.get('goals', '')
            character.isMajor = True if current_char_data.get('major', 'YES') == 'YES' else False

            yw7.novel.characters[char_id] = character
            yw7.novel.srtCharacters.append(char_id)
            print(f"  ✓ Created: {character.title} (Major: {character.isMajor})")

    print(f"✓ Created {len(yw7.novel.characters)} characters")

    # ============================================================
    # STEP 3: Location Creation with Alternate Names
    # ============================================================
    print_step(3, "Location Creation with AKA Fields")

    setting_config = SettingBuilderConfig(
        temperature=0.7,
        max_tokens=8192,
    )
    setting_builder = SettingBuilder(config=setting_config)

    setting_task = Task(
        description=f"""Create detailed settings and locations:

        Story Context:
        {story_arc[:1500]}

        Create 4-5 key locations with:
        - Vivid descriptions
        - Atmosphere and mood
        - Significance to the story
        - Alternate names (historical, colloquial, cultural)

        Format as structured data:
        LOCATION: [name]
        AKA: [alternate names, nicknames]
        DESC: [vivid description with atmosphere]
        ---""",
        agent=setting_builder,
        expected_output="4-5 rich location descriptions with alternate names"
    )

    print("Running Setting Builder...")
    setting_crew = Crew(
        agents=[setting_builder],
        tasks=[setting_task],
        process=Process.sequential,
        verbose=True
    )

    setting_result = setting_crew.kickoff()
    location_text = str(setting_result)

    # Parse and create locations
    with AutoSyncYw7File(project_path) as yw7:
        current_loc_data = {}
        lines = location_text.split('\n')

        for line in lines:
            line = line.strip()

            if line.startswith('LOCATION:'):
                if current_loc_data.get('name'):
                    loc_id = create_id(yw7.novel.locations)
                    location = Location()
                    location.title = current_loc_data.get('name', 'Unnamed Location')
                    location.aka = current_loc_data.get('aka', '')
                    location.desc = current_loc_data.get('desc', '')

                    yw7.novel.locations[loc_id] = location
                    yw7.novel.srtLocations.append(loc_id)
                    print(f"  ✓ Created: {location.title}")

                current_loc_data = {'name': line.replace('LOCATION:', '').strip()}

            elif line.startswith('AKA:'):
                current_loc_data['aka'] = line.replace('AKA:', '').strip()
            elif line.startswith('DESC:'):
                if 'desc' not in current_loc_data:
                    current_loc_data['desc'] = line.replace('DESC:', '').strip()
                else:
                    current_loc_data['desc'] += ' ' + line

        # Save last location
        if current_loc_data.get('name'):
            loc_id = create_id(yw7.novel.locations)
            location = Location()
            location.title = current_loc_data.get('name', 'Unnamed Location')
            location.aka = current_loc_data.get('aka', '')
            location.desc = current_loc_data.get('desc', '')

            yw7.novel.locations[loc_id] = location
            yw7.novel.srtLocations.append(loc_id)
            print(f"  ✓ Created: {location.title}")

    print(f"✓ Created {len(yw7.novel.locations)} locations")

    # ============================================================
    # STEP 4: Chapter Outlining
    # ============================================================
    print_step(4, "Chapter Outlining")

    outline_config = OutlineCreatorConfig(
        temperature=0.7,
        max_tokens=12288,
    )
    outline_creator = OutlineCreator(config=outline_config)

    outline_task = Task(
        description=f"""Create detailed chapter-by-chapter outlines:

        Story Arc:
        {story_arc}

        For each of {num_chapters} chapters:
        - Chapter title reflecting content
        - Brief chapter summary
        - 2-3 scenes per chapter
        - Ensure proper story progression from beginning to end

        The outline should show clear progression:
        - Chapters 1-3: Setup and inciting incident
        - Chapters 4-7: Rising action and complications
        - Chapters 8-9: Climax and confrontation
        - Chapter 10: Resolution and conclusion

        Format for chapter outlines.""",
        agent=outline_creator,
        expected_output=f"Chapter outlines for all {num_chapters} chapters with scene breakdowns"
    )

    print("Running Outline Creator...")
    outline_crew = Crew(
        agents=[outline_creator],
        tasks=[outline_task],
        process=Process.sequential,
        verbose=True
    )

    outline_result = outline_crew.kickoff()
    outline_text = str(outline_result)

    print(f"✓ Outline created ({len(outline_text)} characters)")

    # ============================================================
    # STEP 5: Scene Structure Creation
    # ============================================================
    print_step(5, "Scene Structure with Goal/Conflict/Outcome")

    scene_structure_task = Task(
        description=f"""Parse the chapter outlines and create detailed scene structure.

        Chapter Outlines:
        {outline_text}

        For each chapter, extract:
        1. Chapter title and description
        2. For each scene in the chapter:
           - Scene title
           - Scene goal (what character wants to accomplish)
           - Scene conflict (obstacles, tension, opposition)
           - Scene outcome (how it resolves and connects to next)
           - ACTION or REACTION scene?
           - Scene mode (Dramatic action / Dialogue / Description / Exposition)
           - POV character
           - Key location

        Ensure progression across all {num_chapters} chapters.

        Format as structured data:
        CHAPTER: [number] - [title]
        CHAPTER_DESC: [summary of all scenes]
        SCENE: [title]
        GOAL: [specific goal]
        CONFLICT: [specific conflict]
        OUTCOME: [specific outcome]
        TYPE: [ACTION or REACTION]
        MODE: [narrative mode]
        POV: [character name]
        LOCATION: [location name]
        ---""",
        agent=outline_creator,
        expected_output="Structured scene data with goals/conflicts/outcomes for all scenes"
    )

    print("Creating scene structure...")
    scene_crew = Crew(
        agents=[outline_creator],
        tasks=[scene_structure_task],
        process=Process.sequential,
        verbose=True
    )

    scene_structure_result = scene_crew.kickoff()
    scene_data_text = str(scene_structure_result)

    # Parse and create chapters/scenes
    with AutoSyncYw7File(project_path) as yw7:
        current_chapter = None
        current_chapter_id = None
        current_scene_data = {}
        scene_count = 0

        lines = scene_data_text.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('CHAPTER:'):
                if current_chapter_id and current_chapter:
                    yw7.novel.chapters[current_chapter_id] = current_chapter
                    yw7.novel.srtChapters.append(current_chapter_id)
                    print(f"  ✓ {current_chapter.title} - {len(current_chapter.srtScenes)} scenes")

                current_chapter_id = create_id(yw7.novel.chapters)
                current_chapter = Chapter()
                chapter_title = line.replace('CHAPTER:', '').strip()
                current_chapter.title = chapter_title
                current_chapter.chLevel = 0
                current_chapter.chType = 0
                current_chapter.srtScenes = []

            elif line.startswith('CHAPTER_DESC:'):
                if current_chapter:
                    current_chapter.desc = line.replace('CHAPTER_DESC:', '').strip()

            elif line.startswith('SCENE:'):
                if current_scene_data.get('title') and current_chapter:
                    scene_id = create_id(yw7.novel.scenes)
                    scene = Scene()
                    scene.title = current_scene_data.get('title', 'Untitled Scene')
                    scene.desc = f"{current_scene_data.get('goal', '')} - {current_scene_data.get('conflict', '')}"
                    scene.goal = current_scene_data.get('goal', '')
                    scene.conflict = current_scene_data.get('conflict', '')
                    scene.outcome = current_scene_data.get('outcome', '')
                    scene.isReactionScene = True if current_scene_data.get('type') == 'REACTION' else False
                    scene.scnMode = current_scene_data.get('mode', 'Dramatic action')
                    scene.scnArcs = 'Main Plot'
                    scene.sceneContent = f"[Scene to be written: {scene.title}]"
                    scene.notes = f"POV: {current_scene_data.get('pov', 'Unknown')}\nLocation: {current_scene_data.get('location', 'Unknown')}"
                    scene.tags = current_scene_data.get('type', 'ACTION').lower()

                    yw7.novel.scenes[scene_id] = scene
                    current_chapter.srtScenes.append(scene_id)
                    scene_count += 1

                current_scene_data = {'title': line.replace('SCENE:', '').strip()}

            elif line.startswith('GOAL:'):
                current_scene_data['goal'] = line.replace('GOAL:', '').strip()
            elif line.startswith('CONFLICT:'):
                current_scene_data['conflict'] = line.replace('CONFLICT:', '').strip()
            elif line.startswith('OUTCOME:'):
                current_scene_data['outcome'] = line.replace('OUTCOME:', '').strip()
            elif line.startswith('TYPE:'):
                current_scene_data['type'] = line.replace('TYPE:', '').strip()
            elif line.startswith('MODE:'):
                current_scene_data['mode'] = line.replace('MODE:', '').strip()
            elif line.startswith('POV:'):
                current_scene_data['pov'] = line.replace('POV:', '').strip()
            elif line.startswith('LOCATION:'):
                current_scene_data['location'] = line.replace('LOCATION:', '').strip()

        # Save last scene and chapter
        if current_scene_data.get('title') and current_chapter:
            scene_id = create_id(yw7.novel.scenes)
            scene = Scene()
            scene.title = current_scene_data.get('title', 'Untitled Scene')
            scene.desc = f"{current_scene_data.get('goal', '')} - {current_scene_data.get('conflict', '')}"
            scene.goal = current_scene_data.get('goal', '')
            scene.conflict = current_scene_data.get('conflict', '')
            scene.outcome = current_scene_data.get('outcome', '')
            scene.isReactionScene = True if current_scene_data.get('type') == 'REACTION' else False
            scene.scnMode = current_scene_data.get('mode', 'Dramatic action')
            scene.scnArcs = 'Main Plot'
            scene.sceneContent = f"[Scene to be written: {scene.title}]"
            scene.notes = f"POV: {current_scene_data.get('pov', 'Unknown')}\nLocation: {current_scene_data.get('location', 'Unknown')}"
            scene.tags = current_scene_data.get('type', 'ACTION').lower()

            yw7.novel.scenes[scene_id] = scene
            current_chapter.srtScenes.append(scene_id)
            scene_count += 1

        if current_chapter_id and current_chapter:
            yw7.novel.chapters[current_chapter_id] = current_chapter
            yw7.novel.srtChapters.append(current_chapter_id)
            print(f"  ✓ {current_chapter.title} - {len(current_chapter.srtScenes)} scenes")

    print(f"✓ Created {len(yw7.novel.chapters)} chapters with {scene_count} scenes")

    # ============================================================
    # STEP 6: Prose Writing (ALL scenes)
    # ============================================================
    print_step(6, "Prose Writing (ALL Scenes - Full Novel Generation)")

    writer_config = WriterConfig(
        temperature=0.8,
        max_tokens=32000,  # Increased for longer scenes
    )
    writer = Writer(config=writer_config)

    with AutoSyncYw7File(project_path) as yw7:
        scenes_written = 0
        total_scenes = sum(len(yw7.novel.chapters[ch_id].srtScenes) for ch_id in yw7.novel.srtChapters)

        print(f"Will write {total_scenes} scenes...")

        for ch_id in yw7.novel.srtChapters:
            chapter = yw7.novel.chapters[ch_id]
            print(f"\n📖 Writing Chapter: {chapter.title}")

            for scene_id in chapter.srtScenes:
                scene = yw7.novel.scenes[scene_id]

                print(f"  Writing: {scene.title} ({scenes_written + 1}/{total_scenes})")

                write_task = Task(
                    description=f"""Write compelling, detailed prose for this scene:

                    Title: {scene.title}
                    Goal: {scene.goal}
                    Conflict: {scene.conflict}
                    Outcome: {scene.outcome}
                    Type: {'REACTION' if scene.isReactionScene else 'ACTION'} scene
                    Mode: {scene.scnMode}
                    {scene.notes}

                    Story Context:
                    {story_arc[:1000]}

                    Write 2000-3000 words of rich, engaging prose that:
                    - Shows the character pursuing their goal
                    - Dramatizes the conflict with tension
                    - Reaches the specified outcome
                    - Uses vivid sensory details
                    - Includes compelling dialogue
                    - Maintains consistent character voice

                    Use RAG tools to verify character and location details.""",
                    agent=writer,
                    expected_output="2000-3000 words of polished, detailed prose"
                )

                write_crew = Crew(
                    agents=[writer],
                    tasks=[write_task],
                    process=Process.sequential,
                    verbose=True
                )

                prose_result = write_crew.kickoff()
                scene.sceneContent = str(prose_result)
                scenes_written += 1

                print(f"    ✓ Completed ({len(str(prose_result))} characters)")

    print(f"✓ Wrote prose for {scenes_written} scenes")

    # ============================================================
    # STEP 7: Editorial Refinement
    # ============================================================
    print_step(7, "Editorial Refinement")

    editor_config = EditorConfig(
        temperature=0.5,
        max_tokens=32000,  # Increased to handle longer scenes
    )
    editor = Editor(config=editor_config)

    with AutoSyncYw7File(project_path) as yw7:
        scenes_edited = 0

        for ch_id in yw7.novel.srtChapters:
            chapter = yw7.novel.chapters[ch_id]

            for scene_id in chapter.srtScenes:
                scene = yw7.novel.scenes[scene_id]

                if scene.sceneContent.startswith('[Scene to be written'):
                    continue

                print(f"  Refining: {scene.title}")

                edit_task = Task(
                    description=f"""Review and refine this scene:

                    Title: {scene.title}
                    Current Draft:
                    {scene.sceneContent}

                    Improve:
                    - Clarity and flow
                    - Dialogue naturalness
                    - Pacing and tension
                    - Sensory details
                    - Grammar and style

                    Maintain the core story beats and character voice.""",
                    agent=editor,
                    expected_output="Refined, polished prose"
                )

                edit_crew = Crew(
                    agents=[editor],
                    tasks=[edit_task],
                    process=Process.sequential,
                    verbose=True
                )

                edited_result = edit_crew.kickoff()
                scene.sceneContent = str(edited_result)
                scenes_edited += 1

                print(f"    ✓ Refined")

    print(f"✓ Refined {scenes_edited} scenes")

    # ============================================================
    # STEP 8: Final RAG Sync
    # ============================================================
    print_step(8, "Final RAG Sync")

    sync_stats = sync_file_to_rag(project_path)
    print(f"✓ RAG sync complete:")
    print(f"  Characters synced: {sync_stats.get('characters_synced', 0)}")
    print(f"  Locations synced: {sync_stats.get('locations_synced', 0)}")
    print(f"  Scenes synced: {sync_stats.get('scenes_synced', 0)}")

    # ============================================================
    # Summary
    # ============================================================
    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "="*80)
    print("✅ WORKFLOW COMPLETE!")
    print("="*80)
    print(f"Duration: {duration}")
    print(f"Output file: {project_path}")
    print(f"\nStatistics:")
    print(f"  Chapters: {len(yw7.novel.chapters)}")
    print(f"  Scenes: {scene_count}")
    print(f"  Characters: {len(yw7.novel.characters)}")
    print(f"  Locations: {len(yw7.novel.locations)}")
    print(f"  Scenes with prose: {scenes_written}")
    print(f"  Scenes refined: {scenes_edited}")

    print(f"\n📖 You can now review the complete novel at: {project_path}")


if __name__ == "__main__":
    test_complete_workflow()
