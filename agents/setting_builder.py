"""
Setting Builder Agent - Develops rich, immersive story settings and world-building.

This CrewAI agent uses:
- Centralized LLM configuration
- Genre-specific world-building templates
- Environmental storytelling techniques
"""

from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional
from config.llm_config import get_llm_config


class SettingBuilderConfig(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for LLM")
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Top-p sampling parameter")
    max_tokens: int = Field(default=8192, description="Maximum tokens for responses")
    streaming: bool = Field(default=True, description="Enable streaming output")

    class Config:
        arbitrary_types_allowed = True


class SettingBuilder(Agent):
    """
    Setting Builder agent for developing rich, immersive story settings.

    Features:
    - CrewAI-based architecture
    - Centralized LLM configuration
    - Genre-aware world-building
    - Environmental storytelling
    - Cultural and atmospheric details
    """

    def __init__(self, config: SettingBuilderConfig):
        # Get LLM configuration
        llm_config = get_llm_config()
        agent_config = llm_config.get_agent_config("setting_builder")

        # Override with provided config
        if config.temperature:
            agent_config['temperature'] = config.temperature
        if config.max_tokens:
            agent_config['max_tokens'] = config.max_tokens

        # Create LLM
        llm = llm_config.create_llm("setting_builder")

        # Initialize CrewAI agent
        super().__init__(
            role=agent_config.get('role', 'World Builder & Setting Designer'),
            goal=agent_config.get(
                'goal',
                """Develop rich, immersive settings with detailed locations, atmosphere, and cultural context.
                Create vivid, believable settings that enhance the narrative and provide depth to the story world.
                Design environments that reflect the story's themes and support character development."""
            ),
            backstory=agent_config.get(
                'backstory',
                """You are a master of environmental storytelling and world-building who creates vivid, believable settings
                that enhance the narrative. You understand how physical spaces reflect culture, history, and social dynamics.
                You excel at crafting atmospheric descriptions that immerse readers in the story world, from grand vistas
                to intimate interior spaces. Every detail you add serves the story and enriches the reader's experience."""
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=[],  # Setting building doesn't need RAG tools (creates content for RAG)
        )

        self.config = config

    def build_setting(
        self,
        story_context: str,
        genre: str,
        specific_requirements: str = ""
    ) -> str:
        """
        Build detailed setting information for the story.

        Args:
            story_context: The story arc and plot context
            genre: The story genre
            specific_requirements: Any specific setting requirements

        Returns:
            Detailed setting description
        """
        setting_context = f"""
Story Context: {story_context}

Genre: {genre}

Please develop comprehensive setting details including:
1. Primary locations and their characteristics
2. Cultural and societal elements
3. Historical context (if relevant)
4. Atmospheric details and mood
5. Sensory descriptions (sights, sounds, smells)
6. How settings support the narrative

{specific_requirements}
"""

        return f"Building story settings:\n{setting_context}"

    def describe_location(
        self,
        location_name: str,
        purpose: str,
        atmosphere: str = "neutral"
    ) -> str:
        """
        Create a detailed description of a specific location.

        Args:
            location_name: Name of the location
            purpose: The narrative purpose of this location
            atmosphere: Desired atmosphere (tense, peaceful, mysterious, etc.)

        Returns:
            Detailed location description
        """
        return f"Describing location: {location_name} (Purpose: {purpose}, Atmosphere: {atmosphere})"
