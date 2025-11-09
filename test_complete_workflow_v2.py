"""
Enhanced Complete Workflow with Resilience & Pause/Resume

Features:
- Checkpoint/resume from any workflow step
- Automatic retry with exponential backoff
- Provider fallback on failures
- Empty response detection and handling
- Graceful pause with Ctrl+C
- Per-scene error isolation
- Comprehensive error logging
- Status reporting

Usage:
    # First run
    python test_complete_workflow_v2.py --project MyNovel --genre "science fiction" --chapters 10

    # Resume after failure
    python test_complete_workflow_v2.py --project MyNovel --resume

    # Check status
    python test_complete_workflow_v2.py --project MyNovel --status
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

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

# Import workflow resilience components
from workflow import (
    WorkflowState,
    WorkflowController,
    run_step_with_retry,
    validate_and_retry_crew_kickoff,
    create_llm_with_fallback
)

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


def print_banner(title: str):
    """Print a formatted banner."""
    print("\n" + "🚀 "*20)
    print(title)
    print("🚀 "*20 + "\n")


def execute_story_planning(state: WorkflowState, config) -> str:
    """
    Execute Step 1: Story Planning.

    Returns:
        Story arc text
    """
    logger.info(f"Starting story planning for {state.genre} with {state.num_chapters} chapters")

    planner_config = StoryPlannerConfig(
        temperature=0.7,
        max_tokens=12288,
    )
    story_planner = StoryPlanner(config=planner_config)

    story_task = Task(
        description=f"""Create a compelling {state.genre} story arc for a {state.num_chapters}-chapter novel.

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

        Ensure the story has proper progression from chapter 1 through {state.num_chapters} with a complete narrative arc.""",
        agent=story_planner,
        expected_output="Comprehensive story arc with complete beginning/middle/end structure"
    )

    story_crew = Crew(
        agents=[story_planner],
        tasks=[story_task],
        process=Process.sequential,
        verbose=True
    )

    # Execute with validation and retry
    story_result = validate_and_retry_crew_kickoff(story_crew, "story_planning", max_retries=3)
    story_arc = str(story_result)

    logger.info(f"Story arc created: {len(story_arc)} characters")

    # Save to project
    with AutoSyncYw7File(state.project_path) as yw7:
        yw7.novel.desc = story_arc

    # Store in state
    state.story_arc = story_arc[:500]  # Store preview

    return story_arc


def execute_character_creation(state: WorkflowState, story_arc: str, config) -> int:
    """
    Execute Step 2: Character Creation.

    Returns:
        Number of characters created
    """
    logger.info("Starting character creation")

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

    char_crew = Crew(
        agents=[character_creator],
        tasks=[char_task],
        process=Process.sequential,
        verbose=True
    )

    # Execute with validation and retry
    char_result = validate_and_retry_crew_kickoff(char_crew, "character_creation", max_retries=3)
    char_text = str(char_result)

    # Parse and create characters
    characters_created = 0
    with AutoSyncYw7File(state.project_path) as yw7:
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
                    state.characters_created.append(char_id)
                    characters_created += 1
                    logger.info(f"  Created: {character.title} (Major: {character.isMajor})")

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
            state.characters_created.append(char_id)
            characters_created += 1
            logger.info(f"  Created: {character.title} (Major: {character.isMajor})")

    logger.info(f"Created {characters_created} characters")
    return characters_created


def execute_location_creation(state: WorkflowState, story_arc: str, config) -> int:
    """
    Execute Step 3: Location Creation.

    Returns:
        Number of locations created
    """
    logger.info("Starting location creation")

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

    setting_crew = Crew(
        agents=[setting_builder],
        tasks=[setting_task],
        process=Process.sequential,
        verbose=True
    )

    # Execute with validation and retry
    setting_result = validate_and_retry_crew_kickoff(setting_crew, "location_creation", max_retries=3)
    location_text = str(setting_result)

    # Parse and create locations
    locations_created = 0
    with AutoSyncYw7File(state.project_path) as yw7:
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
                    state.locations_created.append(loc_id)
                    locations_created += 1
                    logger.info(f"  Created: {location.title}")

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
            state.locations_created.append(loc_id)
            locations_created += 1
            logger.info(f"  Created: {location.title}")

    logger.info(f"Created {locations_created} locations")
    return locations_created


def execute_chapter_outlining(state: WorkflowState, story_arc: str, config) -> int:
    """
    Execute Step 4: Chapter Outlining.

    Returns:
        Number of chapters created
    """
    logger.info(f"Starting chapter outlining for {state.num_chapters} chapters")

    outline_config = OutlineCreatorConfig(
        temperature=0.7,
        max_tokens=16384,
    )
    outline_creator = OutlineCreator(config=outline_config)

    outline_task = Task(
        description=f"""Create detailed chapter outlines:

        Story Context:
        {story_arc}

        Create {state.num_chapters} chapters with:
        - Compelling chapter titles
        - 2-4 scenes per chapter
        - Scene descriptions showing progression
        - Clear story beats per chapter

        Format as structured data:
        CHAPTER: [number]
        TITLE: [chapter title]
        DESC: [chapter description]
        SCENE: [scene title]
        SCENEDESC: [what happens in this scene]
        SCENE: [next scene title]
        SCENEDESC: [what happens]
        ---
        [Repeat for all {state.num_chapters} chapters]""",
        agent=outline_creator,
        expected_output=f"{state.num_chapters} detailed chapter outlines with scenes"
    )

    outline_crew = Crew(
        agents=[outline_creator],
        tasks=[outline_task],
        process=Process.sequential,
        verbose=True
    )

    # Execute with validation and retry
    outline_result = validate_and_retry_crew_kickoff(outline_crew, "chapter_outlining", max_retries=3)
    outline_text = str(outline_result)

    # Parse and create chapters/scenes
    chapters_created = 0
    with AutoSyncYw7File(state.project_path) as yw7:
        current_chapter = None
        current_chapter_id = None
        current_scene_data = {}

        lines = outline_text.split('\n')

        for line in lines:
            line = line.strip()

            if line.startswith('CHAPTER:'):
                # Save previous chapter if exists
                if current_chapter:
                    chapters_created += 1

                # Create new chapter
                ch_id = create_id(yw7.novel.chapters)
                chapter = Chapter()
                chapter.title = "Chapter " + line.replace('CHAPTER:', '').strip()
                chapter.desc = ""
                chapter.srtScenes = []

                yw7.novel.chapters[ch_id] = chapter
                yw7.novel.srtChapters.append(ch_id)
                state.chapters_outlined.append(ch_id)

                current_chapter = chapter
                current_chapter_id = ch_id
                logger.info(f"  Created: {chapter.title}")

            elif line.startswith('TITLE:') and current_chapter:
                title_text = line.replace('TITLE:', '').strip()
                if title_text:
                    current_chapter.title = title_text

            elif line.startswith('DESC:') and current_chapter:
                current_chapter.desc = line.replace('DESC:', '').strip()

            elif line.startswith('SCENE:') and current_chapter:
                # Save previous scene if exists
                if current_scene_data.get('title'):
                    scene_id = create_id(yw7.novel.scenes)
                    scene = Scene()
                    scene.title = current_scene_data.get('title', 'Untitled Scene')
                    scene.desc = current_scene_data.get('desc', '')
                    scene.sceneContent = '[Scene to be written]'

                    yw7.novel.scenes[scene_id] = scene
                    current_chapter.srtScenes.append(scene_id)
                    state.scenes_structured.append(scene_id)

                # Start new scene
                current_scene_data = {'title': line.replace('SCENE:', '').strip()}

            elif line.startswith('SCENEDESC:') and current_scene_data:
                current_scene_data['desc'] = line.replace('SCENEDESC:', '').strip()

        # Save last scene and chapter
        if current_scene_data.get('title') and current_chapter:
            scene_id = create_id(yw7.novel.scenes)
            scene = Scene()
            scene.title = current_scene_data.get('title', 'Untitled Scene')
            scene.desc = current_scene_data.get('desc', '')
            scene.sceneContent = '[Scene to be written]'

            yw7.novel.scenes[scene_id] = scene
            current_chapter.srtScenes.append(scene_id)
            state.scenes_structured.append(scene_id)

        if current_chapter:
            chapters_created += 1

    logger.info(f"Created {chapters_created} chapters with {len(state.scenes_structured)} scenes")
    return chapters_created


def execute_scene_structuring(state: WorkflowState, config) -> int:
    """
    Execute Step 5: Scene Structuring (Goal/Conflict/Outcome).

    Returns:
        Number of scenes structured
    """
    logger.info("Starting scene structuring")

    # This step would add detailed structure to each scene
    # For now, we'll keep the scenes as outlined in Step 4
    # In a full implementation, this would add goal/conflict/outcome to each scene

    scenes_structured = len(state.scenes_structured)
    logger.info(f"Structured {scenes_structured} scenes")
    return scenes_structured


def execute_prose_writing(state: WorkflowState, config, controller: WorkflowController) -> int:
    """
    Execute Step 6: Prose Writing.

    Returns:
        Number of scenes written
    """
    logger.info("Starting prose writing")

    writer_config = WriterConfig(
        temperature=0.8,
        max_tokens=32000,
    )
    writer = Writer(config=writer_config)

    scenes_written = 0

    with AutoSyncYw7File(state.project_path) as yw7:
        for ch_id in yw7.novel.srtChapters:
            chapter = yw7.novel.chapters[ch_id]

            for scene_id in chapter.srtScenes:
                scene = yw7.novel.scenes[scene_id]

                # Skip if already written
                if scene_id in state.scenes_written:
                    logger.info(f"  ⏭️  Skipping {scene.title} (already written)")
                    continue

                logger.info(f"  Writing: {scene.title}")

                def write_scene():
                    write_task = Task(
                        description=f"""Write a complete scene in narrative prose format.

                        SCENE DETAILS:
                        Chapter: {chapter.title}
                        Scene: {scene.title}
                        Scene Description: {scene.desc}

                        REQUIREMENTS:
                        - Write 2000-3000 words of narrative prose
                        - Use third person past tense
                        - Include vivid sensory details
                        - Include natural dialogue between characters
                        - Show character emotions and reactions
                        - Maintain smooth pacing

                        OUTPUT FORMAT:
                        Write the complete narrative text only. Do NOT include:
                        - Explanations or meta-commentary
                        - Outlines or summaries
                        - Disclaimers or apologies

                        Start writing the scene immediately.""",
                        agent=writer,
                        expected_output="Complete narrative prose text (2000-3000 words)"
                    )

                    write_crew = Crew(
                        agents=[writer],
                        tasks=[write_task],
                        process=Process.sequential,
                        verbose=True
                    )

                    return validate_and_retry_crew_kickoff(write_crew, f"writing_{scene.title}", max_retries=3)

                try:
                    # Write with retry
                    prose_result = run_step_with_retry(
                        f"write_scene_{scene_id}",
                        write_scene,
                        max_retries=2
                    )

                    scene.sceneContent = str(prose_result)
                    state.scenes_written.append(scene_id)
                    scenes_written += 1

                    # Save checkpoint after each scene
                    state.save()

                    logger.info(f"    ✓ Completed ({len(str(prose_result))} characters)")

                    # Check for pause after each scene
                    if controller.check_should_pause():
                        logger.info("⏸️  Pausing after scene write")
                        return scenes_written

                except Exception as e:
                    logger.error(f"    ❌ Failed to write scene: {e}")
                    scene.sceneContent = f"[Scene writing failed: {e}]"
                    state.mark_step_failed('prose_writing', e)
                    # Continue with next scene instead of failing entire workflow

    logger.info(f"Wrote {scenes_written} scenes")
    return scenes_written


def execute_editorial_refinement(state: WorkflowState, config, controller: WorkflowController) -> int:
    """
    Execute Step 7: Editorial Refinement.

    Note: Using Writer agent for editorial tasks since it handles RAG+editing better than Editor agent.
    This is a workaround for a CrewAI incompatibility with the Editor role and tool usage.

    Returns:
        Number of scenes edited
    """
    logger.info("Starting editorial refinement")

    # Use Writer agent for editorial tasks (works better with RAG than Editor agent)
    from agents.writer import Writer, WriterConfig
    editor_config = WriterConfig(
        temperature=0.5,
        max_tokens=32000,
        enable_rag=True  # Writer handles RAG correctly for editorial tasks
    )
    editor = Writer(config=editor_config)

    scenes_edited = 0

    with AutoSyncYw7File(state.project_path) as yw7:
        for ch_id in yw7.novel.srtChapters:
            chapter = yw7.novel.chapters[ch_id]

            for scene_id in chapter.srtScenes:
                scene = yw7.novel.scenes[scene_id]

                # Skip if not written or already edited
                if scene.sceneContent.startswith('[Scene'):
                    continue

                if scene_id in state.scenes_edited:
                    logger.info(f"  ⏭️  Skipping {scene.title} (already edited)")
                    continue

                logger.info(f"  Refining: {scene.title}")

                def edit_scene():
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

                        Maintain the core story beats and character voice.

                        OUTPUT FORMAT:
                        Output the complete refined narrative text only. Do NOT include:
                        - Editorial comments or meta-commentary
                        - Lists of changes made
                        - Explanations or feedback

                        Output the full polished prose immediately.""",
                        agent=editor,
                        expected_output="Complete refined narrative prose"
                    )

                    edit_crew = Crew(
                        agents=[editor],
                        tasks=[edit_task],
                        process=Process.sequential,
                        verbose=True
                    )

                    return validate_and_retry_crew_kickoff(edit_crew, f"editing_{scene.title}", max_retries=3)

                try:
                    # Edit with retry
                    edited_result = run_step_with_retry(
                        f"edit_scene_{scene_id}",
                        edit_scene,
                        max_retries=2
                    )

                    scene.sceneContent = str(edited_result)
                    state.scenes_edited.append(scene_id)
                    scenes_edited += 1

                    # Save checkpoint after each scene
                    state.save()

                    logger.info(f"    ✓ Refined")

                    # Check for pause after each scene
                    if controller.check_should_pause():
                        logger.info("⏸️  Pausing after scene edit")
                        return scenes_edited

                except Exception as e:
                    logger.error(f"    ❌ Failed to edit scene: {e}")
                    state.mark_step_failed('editorial_refinement', e)
                    # Continue with next scene

    logger.info(f"Refined {scenes_edited} scenes")
    return scenes_edited


def execute_rag_sync(state: WorkflowState) -> dict:
    """
    Execute Step 8: RAG Sync.

    Returns:
        Sync statistics
    """
    logger.info("Starting RAG sync")

    sync_stats = sync_file_to_rag(state.project_path)

    logger.info(f"RAG sync complete:")
    logger.info(f"  Characters synced: {sync_stats.get('characters_synced', 0)}")
    logger.info(f"  Locations synced: {sync_stats.get('locations_synced', 0)}")
    logger.info(f"  Scenes synced: {sync_stats.get('scenes_synced', 0)}")

    return sync_stats


def run_complete_workflow(
    project_name: str,
    genre: str,
    num_chapters: int,
    resume: bool = False
) -> WorkflowState:
    """
    Run the complete enhanced workflow with resilience.

    Args:
        project_name: Name of the project
        genre: Genre of the novel
        num_chapters: Number of chapters
        resume: Whether to resume from checkpoint

    Returns:
        Final workflow state
    """
    start_time = datetime.now()

    print_banner("ENHANCED COMPLETE WORKFLOW WITH RESILIENCE")

    # Initialize or load state
    if resume:
        state = WorkflowState.load(project_name)
        if state:
            logger.info(f"📂 Resuming from checkpoint")
            state.print_status()
        else:
            logger.info(f"⚠️  No checkpoint found, starting fresh")
            resume = False

    if not resume:
        project_path = f"output/{project_name.lower()}.yw7"
        state = WorkflowState(project_name, project_path)
        state.genre = genre
        state.num_chapters = num_chapters
        state.start_time = datetime.now().isoformat()

    # Load LLM config
    config = get_llm_config()

    logger.info(f"\nProject: {state.project_name}")
    logger.info(f"Genre: {state.genre}")
    logger.info(f"Chapters: {state.num_chapters}")
    logger.info(f"Output: {state.project_path}")

    # Initialize workflow controller (handles Ctrl+C gracefully)
    with WorkflowController(state) as controller:

        # ============================================================
        # STEP 1: Story Planning
        # ============================================================
        if not state.can_skip_step('story_planning'):
            print_step(1, "Story Planning")
            state.mark_step_start('story_planning')

            # Create initial project if needed
            if not Path(state.project_path).exists():
                Path("output").mkdir(exist_ok=True)
                yw7_file = Yw7File(state.project_path)
                yw7_file.novel = Novel()
                yw7_file.novel.title = project_name.replace('_', ' ')
                yw7_file.novel.authorName = "AI Book Writer"
                yw7_file.novel.desc = f"A {genre} novel created with enhanced workflow"
                yw7_file.write()
                logger.info("✓ Project initialized")

            try:
                story_arc = run_step_with_retry(
                    'story_planning',
                    lambda: execute_story_planning(state, config),
                    max_retries=3
                )

                state.mark_step_complete('story_planning', f"Story arc: {len(story_arc)} characters")

                # Check for pause
                if not controller.handle_step_checkpoint('story_planning'):
                    return state

            except Exception as e:
                state.mark_step_failed('story_planning', e)
                raise
        else:
            logger.info("⏭️  Skipping story_planning (already completed)")
            # Load story arc from saved state
            with AutoSyncYw7File(state.project_path) as yw7:
                story_arc = yw7.novel.desc

        # ============================================================
        # STEP 2: Character Creation
        # ============================================================
        if not state.can_skip_step('character_creation'):
            print_step(2, "Character Creation")
            state.mark_step_start('character_creation')

            try:
                num_chars = run_step_with_retry(
                    'character_creation',
                    lambda: execute_character_creation(state, story_arc, config),
                    max_retries=3
                )

                state.mark_step_complete('character_creation', f"Created {num_chars} characters")

                if not controller.handle_step_checkpoint('character_creation'):
                    return state

            except Exception as e:
                state.mark_step_failed('character_creation', e)
                raise
        else:
            logger.info("⏭️  Skipping character_creation (already completed)")

        # ============================================================
        # STEP 3: Location Creation
        # ============================================================
        if not state.can_skip_step('location_creation'):
            print_step(3, "Location Creation")
            state.mark_step_start('location_creation')

            try:
                num_locs = run_step_with_retry(
                    'location_creation',
                    lambda: execute_location_creation(state, story_arc, config),
                    max_retries=3
                )

                state.mark_step_complete('location_creation', f"Created {num_locs} locations")

                if not controller.handle_step_checkpoint('location_creation'):
                    return state

            except Exception as e:
                state.mark_step_failed('location_creation', e)
                raise
        else:
            logger.info("⏭️  Skipping location_creation (already completed)")

        # ============================================================
        # STEP 4: Chapter Outlining
        # ============================================================
        if not state.can_skip_step('chapter_outlining'):
            print_step(4, "Chapter Outlining")
            state.mark_step_start('chapter_outlining')

            try:
                num_chapters = run_step_with_retry(
                    'chapter_outlining',
                    lambda: execute_chapter_outlining(state, story_arc, config),
                    max_retries=3
                )

                state.mark_step_complete('chapter_outlining', f"Created {num_chapters} chapters")

                if not controller.handle_step_checkpoint('chapter_outlining'):
                    return state

            except Exception as e:
                state.mark_step_failed('chapter_outlining', e)
                raise
        else:
            logger.info("⏭️  Skipping chapter_outlining (already completed)")

        # ============================================================
        # STEP 5: Scene Structuring
        # ============================================================
        if not state.can_skip_step('scene_structuring'):
            print_step(5, "Scene Structuring")
            state.mark_step_start('scene_structuring')

            try:
                num_scenes = run_step_with_retry(
                    'scene_structuring',
                    lambda: execute_scene_structuring(state, config),
                    max_retries=3
                )

                state.mark_step_complete('scene_structuring', f"Structured {num_scenes} scenes")

                if not controller.handle_step_checkpoint('scene_structuring'):
                    return state

            except Exception as e:
                state.mark_step_failed('scene_structuring', e)
                raise
        else:
            logger.info("⏭️  Skipping scene_structuring (already completed)")

        # ============================================================
        # STEP 6: Prose Writing
        # ============================================================
        if not state.can_skip_step('prose_writing'):
            print_step(6, "Prose Writing")
            state.mark_step_start('prose_writing')

            try:
                scenes_written = execute_prose_writing(state, config, controller)

                # Check if all scenes were written
                total_scenes = len(state.scenes_structured)
                if len(state.scenes_written) >= total_scenes:
                    state.mark_step_complete('prose_writing', f"Wrote {scenes_written} scenes")
                else:
                    logger.warning(f"⚠️  Partially complete: {len(state.scenes_written)}/{total_scenes} scenes written")
                    if controller.check_should_pause():
                        return state

                if not controller.handle_step_checkpoint('prose_writing'):
                    return state

            except Exception as e:
                state.mark_step_failed('prose_writing', e)
                # Don't raise - allow partial completion
                logger.warning(f"⚠️  Prose writing incomplete, you can resume later")
                return state
        else:
            logger.info("⏭️  Skipping prose_writing (already completed)")

        # ============================================================
        # STEP 7: Editorial Refinement
        # ============================================================
        if not state.can_skip_step('editorial_refinement'):
            print_step(7, "Editorial Refinement")
            state.mark_step_start('editorial_refinement')

            try:
                scenes_edited = execute_editorial_refinement(state, config, controller)

                # Check if all scenes were edited
                total_written = len(state.scenes_written)
                if len(state.scenes_edited) >= total_written:
                    state.mark_step_complete('editorial_refinement', f"Refined {scenes_edited} scenes")
                else:
                    logger.warning(f"⚠️  Partially complete: {len(state.scenes_edited)}/{total_written} scenes edited")
                    if controller.check_should_pause():
                        return state

                if not controller.handle_step_checkpoint('editorial_refinement'):
                    return state

            except Exception as e:
                state.mark_step_failed('editorial_refinement', e)
                # Don't raise - allow partial completion
                logger.warning(f"⚠️  Editorial refinement incomplete, you can resume later")
                return state
        else:
            logger.info("⏭️  Skipping editorial_refinement (already completed)")

        # ============================================================
        # STEP 8: RAG Sync
        # ============================================================
        if not state.can_skip_step('rag_sync'):
            print_step(8, "RAG Sync")
            state.mark_step_start('rag_sync')

            try:
                sync_stats = run_step_with_retry(
                    'rag_sync',
                    lambda: execute_rag_sync(state),
                    max_retries=2
                )

                state.mark_step_complete('rag_sync', f"Synced {sync_stats.get('characters_synced', 0)} chars, {sync_stats.get('locations_synced', 0)} locs")

            except Exception as e:
                logger.warning(f"⚠️  RAG sync failed (non-critical): {e}")
                state.mark_step_complete('rag_sync', "Completed with errors")
        else:
            logger.info("⏭️  Skipping rag_sync (already completed)")

    # ============================================================
    # Summary
    # ============================================================
    end_time = datetime.now()
    state.end_time = end_time.isoformat()
    duration = end_time - start_time

    print("\n" + "="*80)
    print("✅ WORKFLOW COMPLETE!")
    print("="*80)
    print(f"Duration: {duration}")
    print(f"Output file: {state.project_path}")

    # Load final stats
    with AutoSyncYw7File(state.project_path) as yw7:
        print(f"\nStatistics:")
        print(f"  Chapters: {len(yw7.novel.chapters)}")
        print(f"  Scenes: {len(yw7.novel.scenes)}")
        print(f"  Characters: {len(yw7.novel.characters)}")
        print(f"  Locations: {len(yw7.novel.locations)}")
        print(f"  Scenes written: {len(state.scenes_written)}")
        print(f"  Scenes edited: {len(state.scenes_edited)}")
        print(f"  Total API calls: {state.total_api_calls}")
        print(f"  Total errors: {len(state.errors)}")

    print(f"\n📖 You can now review the complete novel at: {state.project_path}")

    return state


def show_status(project_name: str):
    """Show status of a project."""
    state = WorkflowState.load(project_name)

    if not state:
        print(f"❌ No checkpoint found for project: {project_name}")
        return

    state.print_status()


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Enhanced AI Book Writer with Resilience & Pause/Resume",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start new project
  python test_complete_workflow_v2.py --project MyNovel --genre "science fiction" --chapters 10

  # Resume from checkpoint
  python test_complete_workflow_v2.py --project MyNovel --resume

  # Check status
  python test_complete_workflow_v2.py --project MyNovel --status

  # Pause running workflow
  # Option 1: Press Ctrl+C (saves checkpoint automatically)
  # Option 2: python -m workflow.controller create MyNovel
        """
    )

    parser.add_argument(
        '--project',
        default='Ten_Chapter_Novel',
        help='Project name (default: Ten_Chapter_Novel)'
    )

    parser.add_argument(
        '--genre',
        default='science fiction',
        help='Genre of the novel (default: science fiction)'
    )

    parser.add_argument(
        '--chapters',
        type=int,
        default=10,
        help='Number of chapters (default: 10)'
    )

    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from checkpoint'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show project status and exit'
    )

    args = parser.parse_args()

    # Handle status command
    if args.status:
        show_status(args.project)
        return

    # Run workflow
    try:
        state = run_complete_workflow(
            project_name=args.project,
            genre=args.genre,
            num_chapters=args.chapters,
            resume=args.resume
        )

        logger.info("\n✅ Workflow completed successfully!")

    except KeyboardInterrupt:
        logger.info("\n⏸️  Workflow interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"\n❌ Workflow failed: {e}")
        logger.error("💾 Checkpoint saved. Resume with --resume flag")
        sys.exit(1)


if __name__ == "__main__":
    main()
