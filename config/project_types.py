"""
AiBookWriter4 - Project Type Configurations
Defines different project types: standard novel, light novel, literary fiction, etc.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class ProjectType(Enum):
    """Available project types."""
    STANDARD = "standard"
    LIGHT_NOVEL = "light_novel"
    LITERARY = "literary"
    FANTASY = "fantasy"
    EPIC_FANTASY = "epic_fantasy"


@dataclass
class ScaleConfig:
    """Configuration for project scale."""
    max_chapters: int = 40
    max_characters_main: int = 5
    max_characters_supporting: int = 15
    max_characters_minor: int = 30
    scenes_per_chapter: int = 3
    target_words_per_chapter: int = 3000
    target_words_per_scene: int = 1000


@dataclass
class StructureConfig:
    """Configuration for story structure."""
    use_arcs: bool = False
    chapters_per_arc: int = 15
    max_arcs: int = 3
    use_volumes: bool = False
    chapters_per_volume: int = 50


@dataclass
class SerializationConfig:
    """Configuration for serialized/web fiction."""
    cliffhanger_frequency: float = 0.5  # 0-1, how often chapters end on cliffhangers
    recap_frequency: int = 0  # Chapters between recap mentions (0 = no recaps)
    reintroduction_threshold: int = 10  # Chapters since last appearance before reintro needed


@dataclass
class QualityConfig:
    """Configuration for prose quality targets."""
    prose_style: str = "balanced"  # sparse, balanced, rich, literary
    dialogue_frequency: float = 0.5  # 0-1
    show_dont_tell: float = 0.7  # 0-1
    thematic_depth: float = 0.5  # 0-1
    character_depth: float = 0.7  # 0-1


@dataclass
class FantasyConfig:
    """Configuration for fantasy-specific elements."""
    magic_system: bool = False
    magic_hardness: float = 0.5  # 0=soft, 1=hard
    power_progression: bool = False
    factions: bool = False
    deep_lore: bool = False


@dataclass
class AgentConfig:
    """Configuration for which agents to use."""
    # Core agents (always used)
    use_story_architect: bool = True
    use_character_designer: bool = True
    use_location_designer: bool = True
    use_plot_architect: bool = True
    use_scene_writer: bool = True
    use_continuity_editor: bool = True

    # Optional core agents
    use_item_cataloger: bool = False
    use_timeline_manager: bool = False
    use_dialogue_specialist: bool = True
    use_style_editor: bool = True
    use_chapter_compiler: bool = True
    use_manuscript_reviewer: bool = True

    # Light novel agents
    use_arc_architect: bool = False
    use_character_roster_manager: bool = False
    use_power_system_manager: bool = False
    use_cliffhanger_specialist: bool = False

    # Fantasy agents
    use_magic_system_designer: bool = False
    use_faction_manager: bool = False
    use_lore_keeper: bool = False
    use_combat_choreographer: bool = False

    # Literary agents
    use_theme_weaver: bool = False
    use_prose_stylist: bool = False
    use_psychological_depth: bool = False


@dataclass
class VectorDBConfig:
    """Configuration for vector database (RAG at scale)."""
    use_vector_db: bool = False
    provider: str = "chromadb"  # chromadb, qdrant
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    collection_prefix: str = ""


@dataclass
class ProjectTypeConfig:
    """Complete configuration for a project type."""
    name: str
    description: str
    scale: ScaleConfig
    structure: StructureConfig
    serialization: SerializationConfig
    quality: QualityConfig
    fantasy: FantasyConfig
    agents: AgentConfig
    vector_db: VectorDBConfig

    # Workflow configuration
    parallel_world_building: bool = True  # Run character/location/item in parallel
    editorial_loops: bool = True  # Enable edit-revise loops

    def get_enabled_agents(self) -> List[str]:
        """Get list of enabled agent types."""
        agents = []
        agent_config = self.agents

        # Core agents
        if agent_config.use_story_architect:
            agents.append("story_architect")
        if agent_config.use_character_designer:
            agents.append("character_designer")
        if agent_config.use_location_designer:
            agents.append("location_designer")
        if agent_config.use_item_cataloger:
            agents.append("item_cataloger")
        if agent_config.use_plot_architect:
            agents.append("plot_architect")
        if agent_config.use_timeline_manager:
            agents.append("timeline_manager")
        if agent_config.use_scene_writer:
            agents.append("scene_writer")
        if agent_config.use_dialogue_specialist:
            agents.append("dialogue_specialist")
        if agent_config.use_continuity_editor:
            agents.append("continuity_editor")
        if agent_config.use_style_editor:
            agents.append("style_editor")
        if agent_config.use_chapter_compiler:
            agents.append("chapter_compiler")
        if agent_config.use_manuscript_reviewer:
            agents.append("manuscript_reviewer")

        # Light novel agents
        if agent_config.use_arc_architect:
            agents.append("arc_architect")
        if agent_config.use_character_roster_manager:
            agents.append("character_roster_manager")
        if agent_config.use_power_system_manager:
            agents.append("power_system_manager")
        if agent_config.use_cliffhanger_specialist:
            agents.append("cliffhanger_specialist")

        # Fantasy agents
        if agent_config.use_magic_system_designer:
            agents.append("magic_system_designer")
        if agent_config.use_faction_manager:
            agents.append("faction_manager")
        if agent_config.use_lore_keeper:
            agents.append("lore_keeper")
        if agent_config.use_combat_choreographer:
            agents.append("combat_choreographer")

        # Literary agents
        if agent_config.use_theme_weaver:
            agents.append("theme_weaver")
        if agent_config.use_prose_stylist:
            agents.append("prose_stylist")
        if agent_config.use_psychological_depth:
            agents.append("psychological_depth")

        return agents


# =============================================================================
# PRESET CONFIGURATIONS
# =============================================================================

STANDARD_NOVEL = ProjectTypeConfig(
    name="Standard Novel",
    description="Traditional 3-act novel structure, 20-40 chapters",
    scale=ScaleConfig(
        max_chapters=40,
        max_characters_main=5,
        max_characters_supporting=15,
        max_characters_minor=30,
        scenes_per_chapter=3,
        target_words_per_chapter=3000,
        target_words_per_scene=1000,
    ),
    structure=StructureConfig(
        use_arcs=False,
        chapters_per_arc=15,
        max_arcs=3,
        use_volumes=False,
        chapters_per_volume=50,
    ),
    serialization=SerializationConfig(
        cliffhanger_frequency=0.3,
        recap_frequency=0,
        reintroduction_threshold=10,
    ),
    quality=QualityConfig(
        prose_style="balanced",
        dialogue_frequency=0.5,
        show_dont_tell=0.7,
        thematic_depth=0.5,
        character_depth=0.7,
    ),
    fantasy=FantasyConfig(
        magic_system=False,
        magic_hardness=0.5,
        power_progression=False,
        factions=False,
        deep_lore=False,
    ),
    agents=AgentConfig(
        use_story_architect=True,
        use_character_designer=True,
        use_location_designer=True,
        use_plot_architect=True,
        use_scene_writer=True,
        use_continuity_editor=True,
        use_item_cataloger=False,
        use_timeline_manager=False,
        use_dialogue_specialist=True,
        use_style_editor=True,
        use_chapter_compiler=True,
        use_manuscript_reviewer=True,
    ),
    vector_db=VectorDBConfig(
        use_vector_db=False,
        provider="chromadb",
    ),
    parallel_world_building=True,
    editorial_loops=True,
)


LIGHT_NOVEL = ProjectTypeConfig(
    name="Light Novel / Web Novel",
    description="Arc-based serialized fiction, 100-500+ chapters, large cast",
    scale=ScaleConfig(
        max_chapters=500,
        max_characters_main=10,
        max_characters_supporting=50,
        max_characters_minor=200,
        scenes_per_chapter=1,  # LN often = 1 scene per chapter
        target_words_per_chapter=3000,
        target_words_per_scene=3000,
    ),
    structure=StructureConfig(
        use_arcs=True,
        chapters_per_arc=30,
        max_arcs=20,
        use_volumes=True,
        chapters_per_volume=50,
    ),
    serialization=SerializationConfig(
        cliffhanger_frequency=1.0,  # Every chapter
        recap_frequency=10,
        reintroduction_threshold=20,
    ),
    quality=QualityConfig(
        prose_style="balanced",
        dialogue_frequency=0.6,
        show_dont_tell=0.6,
        thematic_depth=0.4,
        character_depth=0.6,
    ),
    fantasy=FantasyConfig(
        magic_system=True,
        magic_hardness=0.7,  # LN tends toward hard systems
        power_progression=True,
        factions=True,
        deep_lore=True,
    ),
    agents=AgentConfig(
        use_story_architect=True,
        use_character_designer=True,
        use_location_designer=True,
        use_plot_architect=True,
        use_scene_writer=True,
        use_continuity_editor=True,
        use_item_cataloger=True,
        use_timeline_manager=True,
        use_dialogue_specialist=True,
        use_style_editor=True,
        use_chapter_compiler=True,
        use_manuscript_reviewer=True,
        # Light novel specific
        use_arc_architect=True,
        use_character_roster_manager=True,
        use_power_system_manager=True,
        use_cliffhanger_specialist=True,
        # Fantasy (usually included in LN)
        use_magic_system_designer=True,
        use_faction_manager=True,
        use_lore_keeper=True,
        use_combat_choreographer=True,
    ),
    vector_db=VectorDBConfig(
        use_vector_db=True,  # Recommended at this scale
        provider="qdrant",
        collection_prefix="ln_",
    ),
    parallel_world_building=True,
    editorial_loops=True,
)


LITERARY_FICTION = ProjectTypeConfig(
    name="Literary Fiction",
    description="Character-driven, thematically rich, high prose quality",
    scale=ScaleConfig(
        max_chapters=30,
        max_characters_main=4,
        max_characters_supporting=10,
        max_characters_minor=20,
        scenes_per_chapter=4,
        target_words_per_chapter=4000,
        target_words_per_scene=1000,
    ),
    structure=StructureConfig(
        use_arcs=False,
        chapters_per_arc=10,
        max_arcs=3,
        use_volumes=False,
        chapters_per_volume=30,
    ),
    serialization=SerializationConfig(
        cliffhanger_frequency=0.2,
        recap_frequency=0,
        reintroduction_threshold=5,
    ),
    quality=QualityConfig(
        prose_style="literary",
        dialogue_frequency=0.4,
        show_dont_tell=0.9,
        thematic_depth=0.9,
        character_depth=0.9,
    ),
    fantasy=FantasyConfig(
        magic_system=False,
        magic_hardness=0.0,
        power_progression=False,
        factions=False,
        deep_lore=False,
    ),
    agents=AgentConfig(
        use_story_architect=True,
        use_character_designer=True,
        use_location_designer=True,
        use_plot_architect=True,
        use_scene_writer=True,
        use_continuity_editor=True,
        use_item_cataloger=False,
        use_timeline_manager=True,
        use_dialogue_specialist=True,
        use_style_editor=True,
        use_chapter_compiler=True,
        use_manuscript_reviewer=True,
        # Literary specific
        use_theme_weaver=True,
        use_prose_stylist=True,
        use_psychological_depth=True,
    ),
    vector_db=VectorDBConfig(
        use_vector_db=False,
        provider="chromadb",
    ),
    parallel_world_building=True,
    editorial_loops=True,
)


FANTASY_NOVEL = ProjectTypeConfig(
    name="Fantasy Novel",
    description="World-building focused fantasy with magic systems and factions",
    scale=ScaleConfig(
        max_chapters=50,
        max_characters_main=6,
        max_characters_supporting=20,
        max_characters_minor=40,
        scenes_per_chapter=3,
        target_words_per_chapter=3500,
        target_words_per_scene=1200,
    ),
    structure=StructureConfig(
        use_arcs=True,
        chapters_per_arc=15,
        max_arcs=4,
        use_volumes=False,
        chapters_per_volume=50,
    ),
    serialization=SerializationConfig(
        cliffhanger_frequency=0.5,
        recap_frequency=0,
        reintroduction_threshold=10,
    ),
    quality=QualityConfig(
        prose_style="rich",
        dialogue_frequency=0.5,
        show_dont_tell=0.7,
        thematic_depth=0.6,
        character_depth=0.7,
    ),
    fantasy=FantasyConfig(
        magic_system=True,
        magic_hardness=0.6,
        power_progression=False,
        factions=True,
        deep_lore=True,
    ),
    agents=AgentConfig(
        use_story_architect=True,
        use_character_designer=True,
        use_location_designer=True,
        use_plot_architect=True,
        use_scene_writer=True,
        use_continuity_editor=True,
        use_item_cataloger=True,
        use_timeline_manager=True,
        use_dialogue_specialist=True,
        use_style_editor=True,
        use_chapter_compiler=True,
        use_manuscript_reviewer=True,
        # Fantasy specific
        use_magic_system_designer=True,
        use_faction_manager=True,
        use_lore_keeper=True,
        use_combat_choreographer=True,
    ),
    vector_db=VectorDBConfig(
        use_vector_db=False,
        provider="chromadb",
    ),
    parallel_world_building=True,
    editorial_loops=True,
)


EPIC_FANTASY = ProjectTypeConfig(
    name="Epic Fantasy",
    description="Large-scale fantasy with multiple POVs, extensive world-building",
    scale=ScaleConfig(
        max_chapters=100,
        max_characters_main=8,
        max_characters_supporting=40,
        max_characters_minor=100,
        scenes_per_chapter=4,
        target_words_per_chapter=4000,
        target_words_per_scene=1000,
    ),
    structure=StructureConfig(
        use_arcs=True,
        chapters_per_arc=25,
        max_arcs=5,
        use_volumes=True,
        chapters_per_volume=30,
    ),
    serialization=SerializationConfig(
        cliffhanger_frequency=0.6,
        recap_frequency=15,
        reintroduction_threshold=15,
    ),
    quality=QualityConfig(
        prose_style="rich",
        dialogue_frequency=0.5,
        show_dont_tell=0.8,
        thematic_depth=0.7,
        character_depth=0.8,
    ),
    fantasy=FantasyConfig(
        magic_system=True,
        magic_hardness=0.5,
        power_progression=False,
        factions=True,
        deep_lore=True,
    ),
    agents=AgentConfig(
        use_story_architect=True,
        use_character_designer=True,
        use_location_designer=True,
        use_plot_architect=True,
        use_scene_writer=True,
        use_continuity_editor=True,
        use_item_cataloger=True,
        use_timeline_manager=True,
        use_dialogue_specialist=True,
        use_style_editor=True,
        use_chapter_compiler=True,
        use_manuscript_reviewer=True,
        # Scale management (from LN)
        use_arc_architect=True,
        use_character_roster_manager=True,
        # Fantasy specific
        use_magic_system_designer=True,
        use_faction_manager=True,
        use_lore_keeper=True,
        use_combat_choreographer=True,
        # Literary elements
        use_theme_weaver=True,
    ),
    vector_db=VectorDBConfig(
        use_vector_db=True,
        provider="qdrant",
        collection_prefix="epic_",
    ),
    parallel_world_building=True,
    editorial_loops=True,
)


# =============================================================================
# PROJECT TYPE REGISTRY
# =============================================================================

PROJECT_TYPES: Dict[str, ProjectTypeConfig] = {
    "standard": STANDARD_NOVEL,
    "light_novel": LIGHT_NOVEL,
    "literary": LITERARY_FICTION,
    "fantasy": FANTASY_NOVEL,
    "epic_fantasy": EPIC_FANTASY,
}


def get_project_type(type_name: str) -> ProjectTypeConfig:
    """Get a project type configuration by name."""
    if type_name not in PROJECT_TYPES:
        raise ValueError(f"Unknown project type: {type_name}. Available: {list(PROJECT_TYPES.keys())}")
    return PROJECT_TYPES[type_name]


def list_project_types() -> List[Dict[str, str]]:
    """List all available project types with descriptions."""
    return [
        {"name": name, "description": config.description}
        for name, config in PROJECT_TYPES.items()
    ]


def create_custom_config(
    base_type: str = "standard",
    **overrides
) -> ProjectTypeConfig:
    """
    Create a custom configuration based on a preset with overrides.

    Args:
        base_type: The base project type to start from
        **overrides: Any configuration values to override

    Returns:
        A new ProjectTypeConfig with the overrides applied
    """
    import copy

    base = get_project_type(base_type)
    config = copy.deepcopy(base)

    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
        elif hasattr(config.scale, key):
            setattr(config.scale, key, value)
        elif hasattr(config.structure, key):
            setattr(config.structure, key, value)
        elif hasattr(config.quality, key):
            setattr(config.quality, key, value)
        elif hasattr(config.fantasy, key):
            setattr(config.fantasy, key, value)
        elif hasattr(config.agents, key):
            setattr(config.agents, key, value)

    return config
