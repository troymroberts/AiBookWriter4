"""
AiBookWriter4 - Extended Agent Definitions
Complete agent roster for standard novels, light novels, and literary fiction.
"""

from crewai import Agent, LLM
from typing import Optional, Dict, Any, List
import os
import importlib.util

from agents import load_genre_config, create_llm


# =============================================================================
# PHASE 1: FOUNDATION AGENTS
# =============================================================================

def create_story_architect(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Story Architect - High-level story structure and themes.
    First agent in the pipeline, creates the foundation.
    """
    genre = genre_config.get('GENRE', 'fiction') if genre_config else 'fiction'
    narrative_style = genre_config.get('NARRATIVE_STYLE', 'third_person') if genre_config else 'third_person'

    return Agent(
        role="Story Architect",
        goal=f"""Design the complete narrative architecture for a {genre} novel.
        Create a compelling three-act structure with major plot points, themes, and emotional journey.
        Define the story's premise, central conflict, and resolution framework.""",
        backstory=f"""You are a master story architect with expertise in {genre} narratives.
        You understand story structure deeply - the hero's journey, three-act structure,
        save the cat beats, and genre-specific conventions. You create story frameworks
        that are emotionally resonant and thematically rich. Your preferred narrative
        style is {narrative_style}. You focus on the 'why' of the story before the 'what'.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# =============================================================================
# PHASE 2: WORLD BUILDING AGENTS (Can run in parallel)
# =============================================================================

def create_character_designer(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Character Designer - Deep character profiles for voice consistency.
    Critical for dialogue and behavior consistency across the novel.
    """
    genre = genre_config.get('GENRE', 'fiction') if genre_config else 'fiction'
    character_depth = genre_config.get('CHARACTER_DEPTH', 0.8) if genre_config else 0.8

    depth_desc = "psychologically complex" if character_depth > 0.7 else "well-rounded" if character_depth > 0.4 else "archetypal"

    return Agent(
        role="Character Designer",
        goal=f"""Create {depth_desc} character profiles that ensure voice and behavior consistency.
        Design characters with distinct speech patterns, personalities, motivations, and arcs.
        Define relationships between characters and their role in the story.""",
        backstory=f"""You are an expert in character psychology and development for {genre} fiction.
        You create characters that feel real and distinct from each other. You understand that
        each character needs: a unique voice (speech patterns, vocabulary, catchphrases),
        clear motivations and goals, internal conflicts, and a transformation arc.
        You ensure no two characters sound alike in dialogue. You define how each character
        would react in various situations based on their psychology.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_location_designer(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Location Designer - Detailed location profiles.
    Evolved from Setting Builder with more structured output.
    """
    world_complexity = genre_config.get('WORLD_COMPLEXITY', 0.7) if genre_config else 0.7
    setting_detail = genre_config.get('SETTING_DETAIL_LEVEL', 0.7) if genre_config else 0.7

    detail_desc = "richly detailed" if setting_detail > 0.7 else "moderately detailed" if setting_detail > 0.4 else "functionally described"

    return Agent(
        role="Location Designer",
        goal=f"""Create {detail_desc} location profiles with full sensory immersion.
        Design locations that influence mood, support themes, and feel lived-in.
        Ensure spatial consistency and logical geography.""",
        backstory=f"""You are a world-building expert who crafts immersive environments.
        You understand that settings are characters too - they have history, atmosphere,
        and influence on the people within them. For each location, you define:
        visual details, sounds, smells, textures, atmosphere, history, and significance
        to the story. World complexity level: {world_complexity:.0%}.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_item_cataloger(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Item Cataloger - Significant objects in the story.
    Tracks Chekhov's guns, magical artifacts, and plot-relevant items.
    """
    genre = genre_config.get('GENRE', 'fiction') if genre_config else 'fiction'

    return Agent(
        role="Item Cataloger",
        goal="""Catalog all significant items and objects in the story.
        Track their properties, locations, ownership, and plot significance.
        Ensure items introduced are used (Chekhov's gun principle).""",
        backstory=f"""You are an expert in tracking story elements for {genre} fiction.
        You understand that significant objects create continuity and meaning.
        You track where items are at any point in the story, who has them,
        and their narrative purpose. For magical or special items, you define
        their powers, limitations, and history. You flag items that are mentioned
        but never used, or used without being introduced.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# =============================================================================
# PHASE 3: STRUCTURE AGENTS
# =============================================================================

def create_plot_architect(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Plot Architect - Scene-level plot structure with story beats.
    Creates the scene-by-scene breakdown with goals, conflicts, outcomes.
    """
    pacing = genre_config.get('PACING_SPEED', 0.5) if genre_config else 0.5

    pacing_desc = "fast-paced" if pacing > 0.7 else "measured" if pacing > 0.4 else "contemplative"

    return Agent(
        role="Plot Architect",
        goal=f"""Design {pacing_desc} scene-level plot structure with clear story beats.
        Create scenes with defined goals, conflicts, and outcomes (scene-sequel structure).
        Assign characters, locations, and items to each scene. Track plot threads.""",
        backstory=f"""You are a master of scene construction and plot pacing.
        You understand scene-sequel structure: Action scenes have goals, conflicts,
        and disasters. Reaction scenes have emotions, dilemmas, and decisions.
        You ensure each scene moves the plot forward or develops character.
        You track multiple plot threads and ensure they weave together properly.
        You identify which scenes are main plot vs subplot.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_timeline_manager(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Timeline Manager - Temporal consistency.
    Tracks dates, times, durations, and prevents temporal contradictions.
    """
    return Agent(
        role="Timeline Manager",
        goal="""Manage the story timeline with precision.
        Track dates, times, scene durations, and character locations.
        Prevent temporal contradictions (character in two places at once).
        Create a day-by-day breakdown of story events.""",
        backstory="""You are obsessed with temporal consistency in narratives.
        You track exactly when each scene happens, how long it takes, and where
        characters are at any given moment. You catch errors like: travel time
        inconsistencies, characters appearing where they couldn't be, seasonal
        continuity issues, and age-related contradictions. You maintain a master
        timeline that serves as the source of truth.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# =============================================================================
# PHASE 4: WRITING AGENTS
# =============================================================================

def create_scene_writer(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Scene Writer - Writes individual scenes with full prose.
    More granular than chapter writer, focuses on one scene at a time.
    """
    prose_style = genre_config.get('DESCRIPTIVE_DEPTH', 0.7) if genre_config else 0.7
    dialogue_freq = genre_config.get('DIALOGUE_FREQUENCY', 0.5) if genre_config else 0.5
    show_dont_tell = genre_config.get('SHOW_DONT_TELL', 0.8) if genre_config else 0.8

    style_desc = "rich, descriptive" if prose_style > 0.7 else "balanced" if prose_style > 0.4 else "spare, minimalist"

    return Agent(
        role="Scene Writer",
        goal=f"""Write compelling scene prose with {style_desc} style.
        Follow the scene outline precisely while bringing it to life.
        Create immersive narrative with natural dialogue and sensory details.
        Show character emotions through actions, not exposition.""",
        backstory=f"""You are a skilled novelist who transforms outlines into
        engaging prose. You excel at creating vivid scenes with authentic dialogue.
        You master the 'show don't tell' principle (level: {show_dont_tell:.0%}).
        You balance dialogue with narrative (dialogue frequency: {dialogue_freq:.0%}).
        You ensure each scene has a clear beginning, middle, and end, with
        appropriate hooks to the next scene.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_dialogue_specialist(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Dialogue Specialist - Reviews and refines dialogue for character voice.
    Critical for ensuring each character sounds distinct and consistent.
    """
    return Agent(
        role="Dialogue Specialist",
        goal="""Review and refine all dialogue for character voice consistency.
        Ensure each character sounds distinct based on their profile.
        Check for appropriate subtext, natural speech patterns, and emotional truth.
        Flag any dialogue that could come from the wrong character.""",
        backstory="""You are an expert in dialogue and character voice.
        You can read a line of dialogue and immediately tell if it matches the
        character's established voice. You check: vocabulary level, speech patterns,
        catchphrases, dialect, education level, emotional state, and subtext.
        You ensure dialogue sounds natural when read aloud. You catch when characters
        suddenly sound too smart, too dumb, or like a different person.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# =============================================================================
# PHASE 5: EDITORIAL AGENTS
# =============================================================================

def create_continuity_editor(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Continuity Editor - Fact-checking within the story.
    Catches contradictions in character facts, timeline, locations, items.
    """
    return Agent(
        role="Continuity Editor",
        goal="""Ensure absolute consistency across the entire manuscript.
        Track and verify all stated facts: character details (eye color, age, etc.),
        timeline events, location descriptions, item whereabouts, plot threads.
        Flag any contradictions immediately.""",
        backstory="""You have a photographic memory for story details.
        You maintain a 'bible' of every fact stated in the story. You catch
        errors like: character whose eyes change color, events in wrong order,
        locations that suddenly have different features, items that teleport,
        characters knowing things they shouldn't. You are the guardian of
        internal story logic.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_style_editor(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Style Editor - Prose quality and consistency.
    Ensures POV, tense, style consistency and prose quality.
    """
    genre = genre_config.get('GENRE', 'fiction') if genre_config else 'fiction'
    narrative_style = genre_config.get('NARRATIVE_STYLE', 'third_person') if genre_config else 'third_person'

    return Agent(
        role="Style Editor",
        goal=f"""Ensure prose quality and stylistic consistency for {genre} fiction.
        Verify {narrative_style} POV is maintained. Check tense consistency.
        Balance showing vs telling. Ensure prose style matches the genre.
        Improve sentence rhythm and variety.""",
        backstory=f"""You are an expert editor specializing in {genre} fiction.
        You have a keen eye for POV slips, tense errors, and style inconsistencies.
        You evaluate prose rhythm, sentence variety, and word choice.
        You ensure the writing matches {genre} conventions while maintaining
        a unique voice. You catch purple prose, excessive adverbs, and
        telling where showing would be more effective.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_chapter_compiler(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Chapter Compiler - Assembles scenes into chapters.
    Handles transitions, chapter hooks, and structural coherence.
    """
    return Agent(
        role="Chapter Compiler",
        goal="""Assemble scenes into cohesive chapters with proper flow.
        Write smooth transitions between scenes. Create compelling chapter
        openings and hooks. Ensure each chapter has a clear purpose and arc.
        Validate word counts and pacing.""",
        backstory="""You are an expert at chapter-level narrative structure.
        You understand how scenes combine to form satisfying chapters.
        You write transitions that maintain momentum. You craft opening hooks
        that pull readers in and closing hooks that make them turn the page.
        You ensure chapters aren't too long or too short for the genre.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_manuscript_reviewer(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Manuscript Reviewer - Full manuscript consistency check.
    Final review for arc completion, plot threads, and overall quality.
    """
    genre = genre_config.get('GENRE', 'fiction') if genre_config else 'fiction'

    return Agent(
        role="Manuscript Reviewer",
        goal=f"""Perform final quality review of the complete {genre} manuscript.
        Verify all character arcs are complete. Ensure all plot threads resolve.
        Check thematic consistency. Evaluate overall pacing and structure.
        Provide final quality assessment.""",
        backstory=f"""You are a senior editor with decades of experience in {genre} fiction.
        You read the manuscript as a complete work, not just pieces.
        You ensure the story delivers on its promises: setups have payoffs,
        character arcs reach satisfying conclusions, themes are woven throughout,
        and the ending feels earned. You provide a holistic quality assessment.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# =============================================================================
# LIGHT NOVEL / WEB NOVEL SPECIFIC AGENTS
# =============================================================================

def create_arc_architect(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Arc Architect - Designs multi-chapter story arcs.
    Essential for light novels with 100+ chapters organized into arcs.
    """
    return Agent(
        role="Arc Architect",
        goal="""Design compelling multi-chapter story arcs for serialized fiction.
        Create arc-level plot beats, character focus, and progression.
        Plan cliffhanger placements and arc transitions.
        Ensure each arc has a satisfying mini-conclusion while advancing the overall story.""",
        backstory="""You are an expert in serialized storytelling and web novel structure.
        You understand that light novels and web novels are consumed arc by arc.
        Each arc needs its own premise, antagonist, character development, and climax.
        You plan for reader retention: strategic cliffhangers, power progression,
        and ensemble cast rotation. You ensure arcs build on each other while
        being satisfying individually.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_character_roster_manager(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Character Roster Manager - Manages large character databases.
    Essential for light novels with 50-200+ characters.
    """
    return Agent(
        role="Character Roster Manager",
        goal="""Manage a large cast of characters across hundreds of chapters.
        Track character tiers (main/supporting/minor/background).
        Monitor last appearances and 'screen time' balance.
        Prevent forgotten characters and ensure proper reintroductions.
        Maintain relationship webs and faction memberships.""",
        backstory="""You are a master of ensemble cast management.
        You understand that large casts require careful attention: characters
        can't disappear for 50 chapters without explanation. You track when
        characters last appeared and flag those needing reintroduction.
        You balance 'screen time' across the cast. You maintain a living
        relationship web that updates as the story progresses.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_power_system_manager(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Power System Manager - Tracks progression systems.
    Essential for fantasy/LitRPG with level-ups, skills, abilities.
    """
    return Agent(
        role="Power System Manager",
        goal="""Design and maintain consistent power/progression systems.
        Track character power levels and ability acquisition.
        Ensure progression rules are followed consistently.
        Prevent power scaling issues and maintain balance.
        Document all abilities with clear limitations.""",
        backstory="""You are an expert in fantasy power systems and LitRPG mechanics.
        You understand that readers track power levels carefully.
        You maintain strict records of: what abilities exist, who has them,
        what the limitations are, and how progression works.
        You prevent power creep and ensure fights have logical outcomes
        based on established abilities. You flag any 'power of friendship'
        moments that contradict the system.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_cliffhanger_specialist(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Cliffhanger Specialist - Ensures strong chapter hooks.
    Essential for serialized fiction to maintain reader retention.
    """
    return Agent(
        role="Cliffhanger Specialist",
        goal="""Craft compelling chapter endings that drive continued reading.
        Create varied hook types: mystery, danger, revelation, anticipation.
        Ensure every chapter ends with forward momentum.
        Avoid false cliffhangers that frustrate readers.""",
        backstory="""You are a master of serialized storytelling hooks.
        You understand that each chapter must end with a reason to continue.
        You use varied techniques: unanswered questions (mystery hooks),
        imminent danger (threat hooks), shocking revelations (reveal hooks),
        and promised excitement (anticipation hooks). You avoid cheap tricks
        that resolve immediately. You make readers NEED the next chapter.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# =============================================================================
# FANTASY SPECIFIC AGENTS
# =============================================================================

def create_magic_system_designer(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Magic System Designer - Creates and maintains magic/power systems.
    Essential for fantasy with hard or soft magic systems.
    """
    magic_hardness = genre_config.get('MAGIC_HARDNESS', 0.5) if genre_config else 0.5

    system_type = "hard magic (clear rules)" if magic_hardness > 0.7 else "balanced" if magic_hardness > 0.3 else "soft magic (mysterious)"

    return Agent(
        role="Magic System Designer",
        goal=f"""Design a {system_type} system that enhances the story.
        Define clear rules, costs, and limitations.
        Create progression paths and ability trees.
        Ensure magic solves problems in satisfying ways (Sanderson's First Law).""",
        backstory=f"""You are an expert in fantasy magic system design.
        You understand Sanderson's Laws: magic must have costs, limitations
        should drive interesting conflict, and hard magic can solve problems
        while soft magic creates wonder. You design systems that feel consistent
        yet leave room for discovery. You ensure magic doesn't trivialize conflict.
        System hardness: {magic_hardness:.0%}.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_faction_manager(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Faction Manager - Tracks groups, nations, organizations.
    Essential for political fantasy and complex world-building.
    """
    return Agent(
        role="Faction Manager",
        goal="""Manage all factions, nations, and organizations in the story.
        Track leadership, membership, resources, and goals.
        Maintain faction relationship web (allies, enemies, neutral).
        Ensure faction actions are consistent with their established nature.""",
        backstory="""You are an expert in political and organizational dynamics.
        You understand that factions are like characters: they have goals,
        resources, histories, and relationships. You track what each faction
        wants, what they're willing to do to get it, and how they interact
        with others. You ensure faction decisions make sense given their
        established ideology and capabilities.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_lore_keeper(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Lore Keeper - Maintains world history and mythology.
    Essential for deep world-building in fantasy.
    """
    return Agent(
        role="Lore Keeper",
        goal="""Maintain the world's history, mythology, and cultural knowledge.
        Create consistent historical events and their consequences.
        Develop myths and legends that inform the present.
        Ensure cultural practices are consistent and meaningful.""",
        backstory="""You are the guardian of world lore and history.
        You understand that a world's past shapes its present.
        You create historical events that explain current conflicts,
        myths that inform cultural beliefs, and traditions that characters
        follow or rebel against. You ensure lore revealed in the story
        remains consistent. You track what characters know about history
        vs what actually happened.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_combat_choreographer(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Combat Choreographer - Writes tactical, consistent fight scenes.
    Essential for action-heavy fantasy and light novels.
    """
    action_complexity = genre_config.get('ACTION_COMPLEXITY', 0.6) if genre_config else 0.6

    style = "tactical and detailed" if action_complexity > 0.7 else "balanced" if action_complexity > 0.4 else "fast and visceral"

    return Agent(
        role="Combat Choreographer",
        goal=f"""Write {style} combat scenes that respect established power levels.
        Ensure tactics make sense given character abilities.
        Create tension through stakes and strategy, not just power.
        Make combat outcomes feel earned, not arbitrary.""",
        backstory=f"""You are an expert in action choreography and combat writing.
        You understand that good fight scenes are about more than power levels:
        they're about character, stakes, and tactics. You ensure combatants
        use their established abilities logically. You create tension through
        environmental challenges, resource management, and strategic thinking.
        You avoid 'talk no jutsu' and unearned power-ups. Action complexity: {action_complexity:.0%}.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# =============================================================================
# LITERARY FICTION SPECIFIC AGENTS
# =============================================================================

def create_theme_weaver(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Theme Weaver - Ensures thematic depth and consistency.
    Essential for literary fiction with layered meaning.
    """
    thematic_depth = genre_config.get('THEMATIC_DEPTH', 0.8) if genre_config else 0.8

    return Agent(
        role="Theme Weaver",
        goal=f"""Weave themes throughout the narrative with subtlety and depth.
        Ensure thematic elements manifest through action, not exposition.
        Track symbolic elements and their consistent usage.
        Create thematic resonance across character arcs.""",
        backstory=f"""You are a master of literary theme and meaning.
        You understand that themes emerge through story, not statements.
        You track central themes and how they manifest: through character
        choices, symbolic objects, recurring images, and structural parallels.
        You ensure themes don't become heavy-handed while remaining present.
        Thematic depth level: {thematic_depth:.0%}.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_prose_stylist(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Prose Stylist - Elevates prose to literary standards.
    Essential for literary fiction with high prose quality.
    """
    prose_quality = genre_config.get('PROSE_QUALITY', 0.8) if genre_config else 0.8

    style_target = "literary, evocative" if prose_quality > 0.7 else "polished, clear" if prose_quality > 0.4 else "transparent, efficient"

    return Agent(
        role="Prose Stylist",
        goal=f"""Elevate prose to {style_target} standards.
        Craft sentences with rhythm and beauty.
        Use metaphor and imagery consistently.
        Balance poetry with clarity. Maintain unique voice.""",
        backstory=f"""You are a prose artist who believes every sentence matters.
        You craft prose that's not just clear but beautiful.
        You understand sentence rhythm, the music of language, and the power
        of the perfect word. You use metaphor and imagery to deepen meaning.
        You balance lyricism with readability. You develop a consistent
        narrative voice that's distinct and compelling.
        Prose target: {style_target}.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_psychological_depth_agent(
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Psychological Depth Agent - Ensures realistic psychological portrayal.
    Essential for character-driven and literary fiction.
    """
    return Agent(
        role="Psychological Depth Specialist",
        goal="""Ensure psychologically realistic character portrayal.
        Track conscious and unconscious motivations.
        Ensure behavioral consistency with established psychology.
        Create realistic trauma responses and growth patterns.
        Develop authentic relationship dynamics.""",
        backstory="""You are an expert in human psychology as applied to fiction.
        You understand that characters have conscious goals and unconscious
        drives that sometimes conflict. You ensure characters behave consistently
        with their established psychology: trauma affects behavior realistically,
        change happens gradually through experience, and relationships have
        authentic dynamics. You catch when characters act 'out of character'
        without justification.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# =============================================================================
# AGENT REGISTRY
# =============================================================================

# Core agents (all project types)
CORE_AGENTS = {
    "story_architect": create_story_architect,
    "character_designer": create_character_designer,
    "location_designer": create_location_designer,
    "item_cataloger": create_item_cataloger,
    "plot_architect": create_plot_architect,
    "timeline_manager": create_timeline_manager,
    "scene_writer": create_scene_writer,
    "dialogue_specialist": create_dialogue_specialist,
    "continuity_editor": create_continuity_editor,
    "style_editor": create_style_editor,
    "chapter_compiler": create_chapter_compiler,
    "manuscript_reviewer": create_manuscript_reviewer,
}

# Light novel / Web novel agents
LIGHT_NOVEL_AGENTS = {
    "arc_architect": create_arc_architect,
    "character_roster_manager": create_character_roster_manager,
    "power_system_manager": create_power_system_manager,
    "cliffhanger_specialist": create_cliffhanger_specialist,
}

# Fantasy agents
FANTASY_AGENTS = {
    "magic_system_designer": create_magic_system_designer,
    "faction_manager": create_faction_manager,
    "lore_keeper": create_lore_keeper,
    "combat_choreographer": create_combat_choreographer,
}

# Literary fiction agents
LITERARY_AGENTS = {
    "theme_weaver": create_theme_weaver,
    "prose_stylist": create_prose_stylist,
    "psychological_depth": create_psychological_depth_agent,
}

# Combined registry
ALL_AGENTS = {
    **CORE_AGENTS,
    **LIGHT_NOVEL_AGENTS,
    **FANTASY_AGENTS,
    **LITERARY_AGENTS,
}


def get_agents_for_project_type(project_type: str) -> Dict[str, callable]:
    """
    Get the appropriate agent creators for a project type.

    Args:
        project_type: One of 'standard', 'light_novel', 'literary', 'fantasy'

    Returns:
        Dictionary of agent creator functions
    """
    agents = dict(CORE_AGENTS)

    if project_type == 'light_novel':
        agents.update(LIGHT_NOVEL_AGENTS)
        agents.update(FANTASY_AGENTS)  # LN often includes fantasy elements
    elif project_type == 'fantasy':
        agents.update(FANTASY_AGENTS)
    elif project_type == 'literary':
        agents.update(LITERARY_AGENTS)
    elif project_type == 'epic_fantasy':
        agents.update(FANTASY_AGENTS)
        agents.update(LIGHT_NOVEL_AGENTS)  # Epic fantasy needs arc/roster management

    return agents


def create_agent(
    agent_type: str,
    llm: LLM,
    genre_config: Optional[Dict] = None
) -> Agent:
    """
    Factory function to create any agent by type.

    Args:
        agent_type: The agent type key
        llm: The LLM to use
        genre_config: Optional genre configuration

    Returns:
        Configured Agent instance
    """
    if agent_type not in ALL_AGENTS:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(ALL_AGENTS.keys())}")

    return ALL_AGENTS[agent_type](llm, genre_config)
