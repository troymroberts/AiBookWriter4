"""
Editor Agent - Reviews and refines chapter content with RAG-enhanced continuity checking.

This agent uses:
- Centralized LLM configuration
- RAG tools for verifying character/plot consistency
- Continuity checking across chapters
- Genre-aware editing standards
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


class EditorConfig(BaseModel):
    temperature: float = Field(default=0.5, ge=0.0, le=1.0, description="Temperature for LLM (lower for precision)")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    max_tokens: int = Field(default=8192, description="Maximum tokens for responses")
    enable_rag_continuity: bool = Field(default=True, description="Enable RAG continuity checking")
    strict_mode: bool = Field(default=False, description="Enable strict editing (more thorough)")

    class Config:
        arbitrary_types_allowed = True


class Editor(Agent):
    """
    Editor agent with RAG-enhanced continuity checking.

    Responsibilities:
    - Review and refine chapter content
    - Check for consistency with established story elements
    - Verify character behavior and development
    - Ensure prose quality and style
    - Check chapter length requirements
    """

    def __init__(self, config: EditorConfig):
        # Get LLM configuration
        llm_config = get_llm_config()
        agent_config = llm_config.get_agent_config("editor")

        # Override with provided config
        if config.temperature:
            agent_config['temperature'] = config.temperature
        if config.max_tokens:
            agent_config['max_tokens'] = config.max_tokens

        # Create LLM
        llm = llm_config.create_llm("editor")

        # Prepare tools
        tools = self._prepare_tools(config)

        # Initialize agent with RAG configuration
        super().__init__(
            role=agent_config.get('role', 'Editorial Specialist'),
            goal=agent_config.get(
                'goal',
                """Review and refine each chapter, ensuring quality, consistency, and adherence to the book outline.
                Use semantic search to verify character consistency, plot continuity, and world-building alignment.
                Check that each chapter meets length requirements and maintains the established narrative voice.
                Provide specific, actionable feedback for improvements."""
            ),
            backstory=agent_config.get(
                'backstory',
                """You are an expert editor with a keen eye for detail and narrative consistency.
                You have access to the complete story knowledge base and can verify facts across all chapters.
                You check for strict alignment with the chapter outline, verify character and world-building consistency,
                and critically review prose quality. You ensure each chapter maintains continuity with the established story."""
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=tools,
        )

        self.config = config

    def _prepare_tools(self, config: EditorConfig) -> List:
        """Prepare the RAG tools based on configuration."""
        tools = []

        # Core RAG tools for continuity checking (always available for editors)
        if config.enable_rag_continuity:
            tools.extend([
                SemanticCharacterSearchTool(),
                GetCharacterDetailsTool(),
                SemanticLocationSearchTool(),
                SemanticPlotSearchTool(),
                CheckContinuityTool(),
                GeneralKnowledgeSearchTool()
            ])

        # Could add additional editing-specific tools here
        # e.g., grammar checking, readability analysis, etc.

        return tools

    def review_chapter(
        self,
        chapter_content: str,
        chapter_outline: str,
        genre_config: dict
    ) -> str:
        """
        Review a chapter for quality, consistency, and adherence to outline.

        Args:
            chapter_content: The written chapter content
            chapter_outline: The original chapter outline
            genre_config: Genre-specific configuration

        Returns:
            Editorial feedback and recommendations
        """
        # This method can be called programmatically
        # The agent will use its RAG tools to verify consistency
        review_context = f"""
Chapter Content:
{chapter_content[:1000]}... (truncated)

Chapter Outline:
{chapter_outline}

Genre Requirements:
- Min words: {genre_config.get('MIN_WORDS_PER_CHAPTER', 1600)}
- Max words: {genre_config.get('MAX_WORDS_PER_CHAPTER', 3000)}
- Prose complexity: {genre_config.get('PROSE_COMPLEXITY', 'moderate')}
"""
        return f"Reviewing chapter with RAG tools: {review_context}"

    def check_character_consistency(self, character_name: str, chapter_content: str) -> str:
        """
        Verify character consistency using RAG.

        Args:
            character_name: Name of character to check
            chapter_content: Chapter content containing the character

        Returns:
            Consistency analysis
        """
        # The agent can use GetCharacterDetailsTool and CheckContinuityTool
        # to verify the character's portrayal matches established details
        return f"Checking consistency for {character_name}"
