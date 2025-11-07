"""
Writer Agent - Generates chapter prose with RAG-enhanced continuity checking.

This CrewAI agent uses:
- Centralized LLM configuration
- RAG tools for character/plot continuity
- Genre-specific prompts
- yWriter7 integration
"""

from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional, List
from config.llm_config import get_llm_config

# Import RAG tools
from tools.rag_tools import (
    SemanticCharacterSearchTool,
    GetCharacterDetailsTool,
    SemanticLocationSearchTool,
    SemanticPlotSearchTool,
    CheckContinuityTool,
    GeneralKnowledgeSearchTool
)


class WriterConfig(BaseModel):
    temperature: float = Field(default=0.8, ge=0.0, le=1.0, description="Temperature for LLM (higher for creativity)")
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Top-p sampling parameter")
    max_tokens: int = Field(default=16384, description="Maximum tokens for responses")
    enable_rag: bool = Field(default=True, description="Enable RAG continuity checking")
    streaming: bool = Field(default=True, description="Enable streaming output")

    class Config:
        arbitrary_types_allowed = True


class Writer(Agent):
    """
    Writer agent for generating chapter prose with RAG-enhanced continuity.

    Features:
    - CrewAI-based architecture
    - Centralized LLM configuration
    - RAG integration for continuity checking
    - Genre-aware writing
    - Configurable creativity levels
    """

    def __init__(self, config: WriterConfig):
        # Get LLM configuration
        llm_config = get_llm_config()
        agent_config = llm_config.get_agent_config("writer")

        # Override with provided config
        if config.temperature:
            agent_config['temperature'] = config.temperature
        if config.max_tokens:
            agent_config['max_tokens'] = config.max_tokens

        # Create LLM
        llm = llm_config.create_llm("writer")

        # Prepare tools
        tools = self._prepare_tools(config)

        # Initialize CrewAI agent
        super().__init__(
            role=agent_config.get('role', 'Prose Writer & Storyteller'),
            goal=agent_config.get(
                'goal',
                """Write engaging, polished prose that brings the story to life with vivid descriptions and compelling dialogue.
                Use semantic search to verify character consistency and plot continuity.
                Ensure each chapter flows naturally from previous events and maintains established character voices.
                Generate chapters between 2500-5000 words with rich detail and emotional depth."""
            ),
            backstory=agent_config.get(
                'backstory',
                """You are an accomplished author with mastery of language, style, and voice across multiple genres.
                You have access to the complete story knowledge base and can verify character details, previous events,
                and world-building elements before writing. You excel at crafting compelling narratives that maintain
                continuity while advancing the plot. Your prose is vivid, engaging, and emotionally resonant."""
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=tools,
        )

        self.config = config

    def _prepare_tools(self, config: WriterConfig) -> List:
        """Prepare the RAG tools based on configuration."""
        tools = []

        # Core RAG tools for continuity checking during writing
        if config.enable_rag:
            tools.extend([
                SemanticCharacterSearchTool(),
                GetCharacterDetailsTool(),
                SemanticLocationSearchTool(),
                SemanticPlotSearchTool(),
                CheckContinuityTool(),
                GeneralKnowledgeSearchTool()
            ])

        # Could add additional writing-specific tools here
        # e.g., thesaurus, style guides, grammar checking, etc.

        return tools

    def write_chapter(
        self,
        chapter_outline: str,
        genre_config: dict,
        previous_context: Optional[str] = None
    ) -> str:
        """
        Write a chapter based on the provided outline and genre configuration.

        Args:
            chapter_outline: Detailed outline for the chapter
            genre_config: Genre-specific configuration
            previous_context: Optional context from previous chapters

        Returns:
            Complete chapter text
        """
        # This method can be called programmatically
        # The agent will use its RAG tools to check continuity

        context_parts = [f"Chapter Outline:\n{chapter_outline}"]

        if previous_context:
            context_parts.append(f"\nPrevious Context:\n{previous_context}")

        context_parts.append(f"\nGenre: {genre_config.get('GENRE', 'literary_fiction')}")
        context_parts.append(f"Prose Style: {genre_config.get('PROSE_STYLE', 'descriptive')}")
        context_parts.append(f"Target Length: {genre_config.get('MIN_WORDS_PER_CHAPTER', 2500)}-{genre_config.get('MAX_WORDS_PER_CHAPTER', 5000)} words")

        writing_context = "\n".join(context_parts)

        return f"Writing chapter with RAG tools:\n{writing_context}"
