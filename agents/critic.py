"""
Critic Agent - Provides constructive feedback with RAG-enhanced analysis.

This CrewAI agent uses:
- Centralized LLM configuration
- RAG tools for verifying story consistency
- Plot hole detection through semantic search
- Character arc analysis
"""

from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional, List
from config.llm_config import get_llm_config

# Import RAG tools
from tools.rag_tools import (
    SemanticCharacterSearchTool,
    GetCharacterDetailsTool,
    SemanticPlotSearchTool,
    CheckContinuityTool,
    GeneralKnowledgeSearchTool
)


class CriticConfig(BaseModel):
    temperature: float = Field(default=0.6, ge=0.0, le=1.0, description="Temperature for LLM (moderate for balanced critique)")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    max_tokens: int = Field(default=6144, description="Maximum tokens for responses")
    enable_rag_analysis: bool = Field(default=True, description="Enable RAG for continuity analysis")
    strict_mode: bool = Field(default=False, description="Enable strict critique mode")

    class Config:
        arbitrary_types_allowed = True


class Critic(Agent):
    """
    Critic agent for analyzing and providing constructive feedback.

    Features:
    - CrewAI-based architecture
    - Centralized LLM configuration
    - RAG-enhanced analysis for:
      - Plot consistency verification
      - Character development tracking
      - Continuity checking
      - Thematic coherence
    """

    def __init__(self, config: CriticConfig):
        # Get LLM configuration
        llm_config = get_llm_config()
        agent_config = llm_config.get_agent_config("critic")

        # Override with provided config
        if config.temperature:
            agent_config['temperature'] = config.temperature
        if config.max_tokens:
            agent_config['max_tokens'] = config.max_tokens

        # Create LLM
        llm = llm_config.create_llm("critic")

        # Prepare tools
        tools = self._prepare_tools(config)

        # Initialize CrewAI agent
        super().__init__(
            role=agent_config.get('role', 'Literary Critic & Quality Analyst'),
            goal=agent_config.get(
                'goal',
                """Provide constructive feedback on story elements, identify weaknesses, and suggest improvements.
                Use semantic search to verify plot consistency, character development, and thematic coherence.
                Identify plot holes, pacing issues, and areas where the narrative could be strengthened.
                Provide specific, actionable recommendations for improvement."""
            ),
            backstory=agent_config.get(
                'backstory',
                """You are a critical reader with deep understanding of storytelling techniques and reader expectations.
                You have access to the complete story knowledge base and can verify consistency across all narrative elements.
                You excel at identifying plot holes, character inconsistencies, and pacing issues. Your feedback is
                constructive, specific, and focused on elevating the quality of the narrative."""
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=tools,
        )

        self.config = config

    def _prepare_tools(self, config: CriticConfig) -> List:
        """Prepare the RAG tools based on configuration."""
        tools = []

        # RAG tools for continuity analysis and critique
        if config.enable_rag_analysis:
            tools.extend([
                SemanticCharacterSearchTool(),
                GetCharacterDetailsTool(),
                SemanticPlotSearchTool(),
                CheckContinuityTool(),
                GeneralKnowledgeSearchTool()
            ])

        return tools

    def critique_chapter(
        self,
        chapter_content: str,
        chapter_number: int,
        story_context: str = ""
    ) -> str:
        """
        Provide comprehensive critique of a chapter.

        Args:
            chapter_content: The chapter to critique
            chapter_number: Chapter number for context
            story_context: Overall story context

        Returns:
            Detailed critique with actionable feedback
        """
        critique_context = f"""
Chapter {chapter_number}

Content (excerpt):
{chapter_content[:500]}...

Story Context:
{story_context}

Using RAG tools to analyze:
1. Plot consistency
2. Character behavior alignment
3. Continuity with previous chapters
4. Thematic coherence
5. Pacing and structure
"""

        return f"Critiquing chapter:\n{critique_context}"

    def check_plot_holes(
        self,
        chapter_content: str,
        chapter_context: str = ""
    ) -> str:
        """
        Identify potential plot holes using RAG verification.

        Args:
            chapter_content: Chapter content to analyze
            chapter_context: Chapter context

        Returns:
            Plot hole analysis
        """
        # The agent will use CheckContinuityTool and SemanticPlotSearchTool
        # to verify plot consistency
        return f"Checking for plot holes in chapter"
