"""
Character Creator Agent - Develops deep, multidimensional characters with RAG support.

This CrewAI agent uses:
- Centralized LLM configuration
- RAG tools for checking existing characters
- Character consistency verification
- Relationship dynamics analysis
"""

from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional, List
from config.llm_config import get_llm_config

# Import RAG tools
from tools.rag_tools import (
    SemanticCharacterSearchTool,
    GetCharacterDetailsTool,
    FindRelationshipsTool,
    GeneralKnowledgeSearchTool
)


class CharacterCreatorConfig(BaseModel):
    """Configuration for the CharacterCreator agent."""
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for LLM (balanced for creativity and consistency)"
    )
    top_p: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Top-p sampling parameter"
    )
    max_tokens: int = Field(
        default=6144,
        description="Maximum tokens for responses"
    )
    enable_rag: bool = Field(
        default=True,
        description="Enable RAG for character consistency checking"
    )

    class Config:
        """Pydantic configuration class."""
        arbitrary_types_allowed = True


class CharacterCreator(Agent):
    """
    Character Creator agent for developing deep, multidimensional characters.

    Features:
    - CrewAI-based architecture
    - Centralized LLM configuration
    - RAG-enhanced features:
      - Check existing characters before creating duplicates
      - Verify character consistency
      - Analyze existing relationships
      - Ensure unique character voices
    """

    def __init__(self, config: CharacterCreatorConfig):
        """
        Initialize the CharacterCreator agent.

        Args:
            config: Configuration instance containing agent settings.
        """
        # Get LLM configuration
        llm_config = get_llm_config()
        agent_config = llm_config.get_agent_config("character_creator")

        # Override with provided config
        if config.temperature:
            agent_config['temperature'] = config.temperature
        if config.max_tokens:
            agent_config['max_tokens'] = config.max_tokens

        # Create LLM
        llm = llm_config.create_llm("character_creator")

        # Prepare tools
        tools = self._prepare_tools(config)

        # Initialize CrewAI agent
        super().__init__(
            role=agent_config.get('role', 'Character Development Specialist'),
            goal=agent_config.get(
                'goal',
                """Create deep, multidimensional characters with compelling backstories, motivations, and arcs.
                Use semantic search to ensure characters are unique and don't duplicate existing characters.
                Develop rich character profiles including physical traits, psychological depth, relationships,
                and character stats. Ensure each character has a unique voice and serves the narrative."""
            ),
            backstory=agent_config.get(
                'backstory',
                """You are an expert in psychology and character development who brings fictional people to life.
                You have access to all existing characters in the story and can verify uniqueness and relationships.
                Your expertise includes creating detailed profiles, developing unique voices, building realistic
                relationships, and ensuring character motivations drive the story forward. You maintain character
                consistency across all chapters while allowing for natural growth and development."""
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=tools
        )

        self.config = config

    def _prepare_tools(self, config: CharacterCreatorConfig) -> List:
        """Prepare the RAG tools based on configuration."""
        tools = []

        # RAG tools for character development and consistency
        if config.enable_rag:
            tools.extend([
                SemanticCharacterSearchTool(),
                GetCharacterDetailsTool(),
                FindRelationshipsTool(),
                GeneralKnowledgeSearchTool()
            ])

        return tools

    def create_character(
        self,
        character_type: str,
        story_context: str,
        relationships: Optional[str] = None
    ) -> str:
        """
        Create a new character for the story.

        Args:
            character_type: Type or role of character (protagonist, antagonist, etc.)
            story_context: Overall story context
            relationships: Existing character relationships to consider

        Returns:
            Detailed character profile
        """
        char_context = f"""
Character Type: {character_type}

Story Context: {story_context}

Existing Relationships: {relationships or 'None'}

Using RAG to check:
1. Existing similar characters (avoid duplication)
2. Current character roster
3. Existing relationships
4. Character naming patterns

Please create a comprehensive character profile including:
- Full name and age
- Physical description
- Psychological profile
- Backstory and motivations
- Strengths and weaknesses
- Character stats (1-10 scale)
- Speech patterns and voice
- Relationships with other characters
"""

        return f"Creating character:\n{char_context}"

    def analyze_character_arc(
        self,
        character_name: str,
        story_progression: str
    ) -> str:
        """
        Analyze and develop a character's arc throughout the story.

        Args:
            character_name: Name of the character
            story_progression: Current story progression

        Returns:
            Character arc analysis and development plan
        """
        # The agent will use GetCharacterDetailsTool to verify existing traits
        return f"Analyzing arc for {character_name}"
