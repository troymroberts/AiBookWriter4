"""
AiBookWriter4 - Agent Definitions
Pure CrewAI implementation with Ollama support.
"""

from crewai import Agent, LLM
from typing import Optional
import importlib.util
import os


def load_genre_config(genre_name: str, genres_dir: str = "config/genres") -> dict:
    """Load genre-specific configuration from Python files."""
    config_path = os.path.join(genres_dir, f"{genre_name}.py")

    if not os.path.exists(config_path):
        print(f"Warning: Genre config not found: {config_path}")
        return {}

    try:
        spec = importlib.util.spec_from_file_location("genre_config", config_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Extract all uppercase variables as configuration
        return {
            name: getattr(module, name)
            for name in dir(module)
            if name.isupper() and not name.startswith('_')
        }
    except Exception as e:
        print(f"Error loading genre config: {e}")
        return {}


def create_llm(
    base_url: str = "http://localhost:11434",
    model: str = "llama3.2:latest",
    temperature: float = 0.7,
    max_tokens: int = 4000,
    top_p: float = 0.9
) -> LLM:
    """Create a CrewAI LLM instance for Ollama."""
    return LLM(
        model=f"ollama/{model}" if not model.startswith("ollama/") else model,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p
    )


def create_story_planner(
    llm: LLM,
    genre_config: Optional[dict] = None
) -> Agent:
    """Create the Story Planner agent."""
    genre = genre_config.get('GENRE', 'fiction') if genre_config else 'fiction'
    narrative_style = genre_config.get('NARRATIVE_STYLE', 'third_person') if genre_config else 'third_person'

    return Agent(
        role="Story Planner",
        goal=f"""Create a compelling, well-structured story arc for a {genre} novel.
        Develop major plot points, character arcs, and turning points.
        Ensure the narrative has a captivating beginning, rising action, climax,
        and satisfying resolution.""",
        backstory=f"""You are a master storyteller with decades of experience crafting
        {genre} narratives. You understand story structure deeply - the hero's journey,
        three-act structure, and genre conventions. You create story arcs that are
        emotionally resonant and thematically rich. Your preferred narrative style
        is {narrative_style}.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_setting_builder(
    llm: LLM,
    genre_config: Optional[dict] = None
) -> Agent:
    """Create the Setting Builder agent."""
    world_complexity = genre_config.get('WORLD_COMPLEXITY', 0.7) if genre_config else 0.7
    setting_detail = genre_config.get('SETTING_DETAIL_LEVEL', 0.7) if genre_config else 0.7

    detail_desc = "highly detailed" if setting_detail > 0.7 else "moderately detailed" if setting_detail > 0.4 else "focused"

    return Agent(
        role="Setting Builder",
        goal=f"""Create vivid, immersive world settings that enhance the story.
        Develop {detail_desc} descriptions of locations, atmosphere, and environment.
        Ensure settings support the narrative and evoke strong sensory experiences.""",
        backstory=f"""You are a world-building expert who crafts immersive environments.
        You understand how setting influences mood, character, and plot. You create
        locations that feel real and lived-in, with attention to sensory details,
        cultural elements, and atmospheric qualities. World complexity level: {world_complexity:.0%}.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_outline_creator(
    llm: LLM,
    genre_config: Optional[dict] = None
) -> Agent:
    """Create the Outline Creator agent."""
    pacing = genre_config.get('PACING_SPEED', 0.5) if genre_config else 0.5

    pacing_desc = "fast-paced" if pacing > 0.7 else "moderately paced" if pacing > 0.4 else "contemplative"

    return Agent(
        role="Outline Creator",
        goal=f"""Generate detailed chapter-by-chapter outlines based on the story arc.
        Create {pacing_desc} chapter structures with clear scenes, character moments,
        and plot progression. Each chapter should have specific goals and outcomes.""",
        backstory=f"""You are a meticulous planner who transforms story arcs into
        actionable chapter outlines. You understand narrative pacing and how to
        structure chapters for maximum impact. Your outlines include scene breakdowns,
        character beats, and emotional arcs for each chapter.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_writer(
    llm: LLM,
    genre_config: Optional[dict] = None
) -> Agent:
    """Create the Writer agent."""
    prose_style = genre_config.get('DESCRIPTIVE_DEPTH', 0.7) if genre_config else 0.7
    dialogue_freq = genre_config.get('DIALOGUE_FREQUENCY', 0.5) if genre_config else 0.5
    show_dont_tell = genre_config.get('SHOW_DONT_TELL', 0.8) if genre_config else 0.8

    style_desc = "rich, descriptive" if prose_style > 0.7 else "balanced" if prose_style > 0.4 else "spare, minimalist"

    return Agent(
        role="Writer",
        goal=f"""Write compelling chapter prose based on the outline.
        Use {style_desc} prose style with natural dialogue.
        Show character emotions through actions and dialogue rather than exposition.
        Create immersive scenes that bring the story to life.""",
        backstory=f"""You are a skilled novelist who transforms outlines into
        engaging prose. You excel at creating vivid scenes, authentic dialogue,
        and emotional resonance. You understand the 'show don't tell' principle
        (level: {show_dont_tell:.0%}) and balance dialogue with narrative
        (dialogue frequency: {dialogue_freq:.0%}).""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# Agent factory for easy creation
AGENT_CREATORS = {
    "story_planner": create_story_planner,
    "setting_builder": create_setting_builder,
    "outline_creator": create_outline_creator,
    "writer": create_writer,
}


def create_agent(
    agent_type: str,
    llm: LLM,
    genre_config: Optional[dict] = None
) -> Agent:
    """Factory function to create agents by type."""
    if agent_type not in AGENT_CREATORS:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(AGENT_CREATORS.keys())}")

    return AGENT_CREATORS[agent_type](llm, genre_config)
