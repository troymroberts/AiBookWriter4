"""
Lore Builder Agent - Develops rich backstory, history, and cultural lore.

This CrewAI agent uses:
- Centralized LLM configuration
- Genre-specific mythology templates
- Historical and cultural framework development
"""

from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional
from config.llm_config import get_llm_config


class LoreBuilderConfig(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for LLM")
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Top-p sampling parameter")
    max_tokens: int = Field(default=8192, description="Maximum tokens for responses")
    streaming: bool = Field(default=False, description="Enable streaming output (default False for lore)")

    class Config:
        arbitrary_types_allowed = True


class LoreBuilder(Agent):
    """
    Lore Builder agent for developing rich backstory, history, and cultural lore.

    Features:
    - CrewAI-based architecture
    - Centralized LLM configuration
    - Mythology and history development
    - Cultural framework creation
    - World-building depth enhancement
    """

    def __init__(self, config: LoreBuilderConfig):
        # Get LLM configuration
        llm_config = get_llm_config()
        agent_config = llm_config.get_agent_config("lore_builder")

        # Override with provided config
        if config.temperature:
            agent_config['temperature'] = config.temperature
        if config.max_tokens:
            agent_config['max_tokens'] = config.max_tokens

        # Create LLM
        llm = llm_config.create_llm("lore_builder")

        # Initialize CrewAI agent
        super().__init__(
            role=agent_config.get('role', 'Lore & Mythology Expert'),
            goal=agent_config.get(
                'goal',
                """Develop rich backstory, history, and cultural lore that adds depth to the world.
                Create intricate mythologies, historical frameworks, and cultural systems that enhance world-building.
                Ensure lore is consistent, meaningful, and supports the narrative themes."""
            ),
            backstory=agent_config.get(
                'backstory',
                """You are a master of creating intricate mythologies, histories, and cultural frameworks that enhance
                worldbuilding. You understand how societies develop over time, how myths reflect cultural values,
                and how history shapes the present. You excel at weaving together legends, historical events,
                and cultural practices into a coherent tapestry that gives depth and authenticity to fictional worlds."""
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=[],  # Lore building doesn't need RAG tools (creates foundational content)
        )

        self.config = config

    def build_lore(
        self,
        story_arc: str,
        genre: str,
        world_context: str = ""
    ) -> str:
        """
        Build detailed world lore based on the story arc and genre.

        Args:
            story_arc: The overarching story arc
            genre: The story genre
            world_context: Existing world-building context

        Returns:
            Comprehensive lore and mythology
        """
        lore_context = f"""
Story Arc: {story_arc}

Genre: {genre}

World Context: {world_context}

Please develop comprehensive world lore including:
1. Historical timeline and major events
2. Cultural traditions and practices
3. Mythologies and legends
4. Religious or philosophical systems (if relevant)
5. Social structures and hierarchies
6. How lore connects to the current story
"""

        return f"Building world lore:\n{lore_context}"

    def create_mythology(
        self,
        theme: str,
        purpose: str = "explain world origins"
    ) -> str:
        """
        Create a mythology or legend for the story world.

        Args:
            theme: The thematic focus of the mythology
            purpose: The narrative purpose (explain origins, moral lessons, etc.)

        Returns:
            Detailed mythology or legend
        """
        return f"Creating mythology - Theme: {theme}, Purpose: {purpose}"

    def develop_history(
        self,
        time_period: str,
        key_events: str = ""
    ) -> str:
        """
        Develop historical background for the story world.

        Args:
            time_period: The historical period to develop
            key_events: Important events that shaped this period

        Returns:
            Detailed historical background
        """
        return f"Developing history - Period: {time_period}, Key Events: {key_events}"
