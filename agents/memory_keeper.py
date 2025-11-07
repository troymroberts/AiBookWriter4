"""
Memory Keeper Agent - Tracks story continuity and maintains knowledge base.

This agent uses RAG (Retrieval-Augmented Generation) to:
- Track story progression through chapters
- Monitor character development and consistency
- Maintain world-building details
- Check continuity across the narrative
- Query story knowledge semantically
"""

from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional
from config.llm_config import get_llm_config

# Import RAG tools
from tools.rag_tools import (
    SemanticCharacterSearchTool,
    GetCharacterDetailsTool,
    SemanticLocationSearchTool,
    SemanticPlotSearchTool,
    FindRelationshipsTool,
    CheckContinuityTool,
    GeneralKnowledgeSearchTool
)


class MemoryKeeperConfig(BaseModel):
    temperature: float = Field(default=0.6, ge=0.0, le=1.0, description="Temperature for LLM (lower for consistency)")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    max_tokens: int = Field(default=8192, description="Maximum tokens for responses")
    enable_continuity_checks: bool = Field(default=True, description="Enable automatic continuity checking")
    enable_relationship_tracking: bool = Field(default=True, description="Enable relationship tracking")

    class Config:
        arbitrary_types_allowed = True


class MemoryKeeper(Agent):
    """
    Memory Keeper agent with RAG capabilities.

    Responsibilities:
    - Track story progression and key events
    - Monitor character development and consistency
    - Maintain world-building knowledge
    - Flag continuity issues
    - Provide semantic search across story knowledge
    """

    def __init__(self, config: MemoryKeeperConfig):
        # Get LLM configuration
        llm_config = get_llm_config()
        agent_config = llm_config.get_agent_config("memory_keeper")

        # Override with provided config
        if config.temperature:
            agent_config['temperature'] = config.temperature
        if config.max_tokens:
            agent_config['max_tokens'] = config.max_tokens

        # Create LLM
        llm = llm_config.create_llm("memory_keeper")

        # Prepare tools
        tools = self._prepare_tools(config)

        # Initialize agent with RAG configuration
        super().__init__(
            role=agent_config.get('role', 'Memory Keeper & Continuity Guardian'),
            goal=agent_config.get(
                'goal',
                """Track and maintain story continuity, character development, and world-building consistency.
                Use semantic search to verify facts, check for contradictions, and ensure narrative coherence.
                Monitor character arcs, relationships, and plot progression across all chapters."""
            ),
            backstory=agent_config.get(
                'backstory',
                """You are the guardian of story continuity with perfect recall of all story elements.
                You have access to a comprehensive knowledge base that tracks characters, locations, plot events,
                and relationships. You use semantic search to quickly find relevant information and identify
                any inconsistencies or contradictions in the narrative. Your mission is to ensure the story
                remains coherent, characters stay true to their established traits, and the world follows its own rules."""
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=tools,
        )

        self.config = config

    def _prepare_tools(self, config: MemoryKeeperConfig):
        """Prepare the RAG tools based on configuration."""
        tools = []

        # Core semantic search tools (always available)
        tools.extend([
            SemanticCharacterSearchTool(),
            GetCharacterDetailsTool(),
            SemanticLocationSearchTool(),
            SemanticPlotSearchTool(),
            GeneralKnowledgeSearchTool(),
        ])

        # Optional tools based on config
        if config.enable_relationship_tracking:
            tools.append(FindRelationshipsTool())

        if config.enable_continuity_checks:
            tools.append(CheckContinuityTool())

        return tools

    def verify_continuity(self, context: str) -> str:
        """
        Verify continuity for a given context.

        Args:
            context: The narrative context to check

        Returns:
            Continuity report
        """
        # This method can be called programmatically
        # The agent will use its tools to check continuity
        return f"Checking continuity for: {context}"

    def track_chapter_completion(self, chapter_number: int, summary: str):
        """
        Track completion of a chapter.

        Args:
            chapter_number: The chapter number
            summary: Summary of the chapter
        """
        # This can be used to trigger RAG updates
        pass