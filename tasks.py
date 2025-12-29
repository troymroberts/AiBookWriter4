"""
AiBookWriter4 - Task Definitions
CrewAI tasks with context chaining for the book writing workflow.
"""

from crewai import Task, Agent
from typing import Optional, List


def create_story_planning_task(
    agent: Agent,
    genre: str,
    num_chapters: int,
    story_prompt: str,
    additional_instructions: str = ""
) -> Task:
    """Create the story planning task."""
    return Task(
        description=f"""Create a comprehensive story arc for a {genre} novel with {num_chapters} chapters.

**Story Premise:**
{story_prompt}

**Requirements:**
1. Develop the main plot with clear beginning, middle, and end
2. Create compelling character arcs for 2-4 main characters
3. Identify major plot points and turning moments
4. Plan the emotional journey of the story
5. Ensure thematic coherence throughout

{f"**Additional Instructions:** {additional_instructions}" if additional_instructions else ""}

**Output Format:**
Provide a structured story arc including:
- Story Overview (2-3 paragraphs)
- Main Characters (name, role, arc)
- Act Structure (Act 1, 2, 3 breakdown)
- Key Plot Points (inciting incident, midpoint, climax, resolution)
- Themes and Motifs""",
        expected_output=f"""A detailed story arc document for a {num_chapters}-chapter {genre} novel,
including character descriptions, plot structure, and thematic elements.""",
        agent=agent
    )


def create_setting_building_task(
    agent: Agent,
    story_task: Task
) -> Task:
    """Create the setting building task with context from story planning."""
    return Task(
        description="""Based on the story arc, develop detailed world settings and locations.

**Requirements:**
1. Create vivid descriptions for all major locations mentioned in the story
2. Establish the time period and cultural context
3. Develop atmospheric details (weather, seasons, time of day patterns)
4. Include sensory details for each setting (sights, sounds, smells)
5. Note how settings influence or reflect character emotions

**Output Format:**
For each major setting, provide:
- Name and brief description
- Physical details and layout
- Atmosphere and mood
- Sensory elements
- Significance to the story""",
        expected_output="""A comprehensive settings document with detailed descriptions
of all major locations, their atmospheres, and their narrative significance.""",
        agent=agent,
        context=[story_task]  # Receives story arc as context
    )


def create_outline_task(
    agent: Agent,
    story_task: Task,
    setting_task: Task,
    num_chapters: int
) -> Task:
    """Create the outline task with context from story and settings."""
    return Task(
        description=f"""Create detailed outlines for all {num_chapters} chapters of the novel.

**Requirements:**
For each chapter, provide:
1. Chapter title and number
2. Chapter summary (2-3 sentences)
3. Scene breakdown (3-5 scenes per chapter)
4. Character appearances and development points
5. Key plot events and revelations
6. Setting locations used
7. Emotional beats and tone
8. How it connects to the overall arc

**Format:**
Structure each chapter outline clearly with headers and bullet points.
Ensure logical flow from chapter to chapter.""",
        expected_output=f"""Complete outlines for all {num_chapters} chapters, with scene
breakdowns, character beats, and plot progression details.""",
        agent=agent,
        context=[story_task, setting_task]  # Receives both as context
    )


def create_chapter_writing_task(
    agent: Agent,
    chapter_number: int,
    outline_task: Task,
    previous_chapter_task: Optional[Task] = None,
    min_words: int = 2000
) -> Task:
    """Create a chapter writing task."""
    context_tasks = [outline_task]
    if previous_chapter_task:
        context_tasks.append(previous_chapter_task)

    return Task(
        description=f"""Write Chapter {chapter_number} based on the outline.

**Requirements:**
1. Follow the chapter outline closely
2. Write at least {min_words} words
3. Include vivid scene descriptions
4. Write natural, character-appropriate dialogue
5. Show emotions through actions, not exposition
6. Maintain consistent narrative voice
7. End with a hook or transition to the next chapter

**Style Guidelines:**
- Use active voice
- Vary sentence length for rhythm
- Include sensory details
- Balance dialogue and narrative
- Show character interiority appropriately""",
        expected_output=f"""Chapter {chapter_number} prose of at least {min_words} words,
following the outline with compelling narrative and dialogue.""",
        agent=agent,
        context=context_tasks
    )


# Task factory for the core workflow
def create_core_workflow_tasks(
    story_planner: Agent,
    setting_builder: Agent,
    outline_creator: Agent,
    genre: str,
    num_chapters: int,
    story_prompt: str,
    additional_instructions: str = ""
) -> List[Task]:
    """Create the three core tasks for the book planning workflow."""

    story_task = create_story_planning_task(
        agent=story_planner,
        genre=genre,
        num_chapters=num_chapters,
        story_prompt=story_prompt,
        additional_instructions=additional_instructions
    )

    setting_task = create_setting_building_task(
        agent=setting_builder,
        story_task=story_task
    )

    outline_task = create_outline_task(
        agent=outline_creator,
        story_task=story_task,
        setting_task=setting_task,
        num_chapters=num_chapters
    )

    return [story_task, setting_task, outline_task]
