"""
Story Planner Agent - Develops overarching story arcs and narrative structure.

This CrewAI agent uses:
- Centralized LLM configuration
- Genre-specific story structure templates
- Multi-chapter arc planning
"""

from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional
from config.llm_config import get_llm_config


class StoryPlannerConfig(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for LLM")
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Top-p sampling parameter")
    max_tokens: int = Field(default=12288, description="Maximum tokens for responses")
    streaming: bool = Field(default=True, description="Enable streaming output")

    class Config:
        arbitrary_types_allowed = True


class StoryPlanner(Agent):
    """
    Story Planner agent for developing overarching story arcs.

    Features:
    - CrewAI-based architecture
    - Centralized LLM configuration
    - Genre-aware story structure
    - Multi-chapter arc planning
    - Character arc development
    - Thematic element integration
    """

    def __init__(self, config: StoryPlannerConfig):
        # Get LLM configuration
        llm_config = get_llm_config()
        agent_config = llm_config.get_agent_config("story_planner")

        # Override with provided config
        if config.temperature:
            agent_config['temperature'] = config.temperature
        if config.max_tokens:
            agent_config['max_tokens'] = config.max_tokens

        # Create LLM
        llm = llm_config.create_llm("story_planner")

        # Initialize CrewAI agent
        super().__init__(
            role=agent_config.get('role', 'Story Architect & Narrative Designer'),
            goal=agent_config.get(
                'goal',
                """Create compelling story arcs with well-defined plot points, character arcs, and thematic elements.
                Design a cohesive narrative structure that spans multiple chapters with proper pacing, conflict escalation,
                and satisfying resolution. Ensure each act builds on the previous one and maintains reader engagement."""
            ),
            backstory=agent_config.get(
                'backstory',
                """You are an expert in narrative structure, story theory, and genre conventions with years of experience
                analyzing successful novels. You understand the hero's journey, three-act structure, and various narrative
                frameworks. You excel at creating compelling story arcs that balance character development with plot progression,
                weaving together multiple storylines into a cohesive narrative."""
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=[],  # Story planning doesn't need RAG tools (creates the foundation for RAG)
        )

        self.config = config

    def plan_story_arc(
        self,
        genre: str,
        num_chapters: int,
        story_premise: str,
        additional_instructions: str = ""
    ) -> str:
        """
        Plan the overarching story arc for a novel.

        Args:
            genre: The story genre
            num_chapters: Number of chapters to plan for
            story_premise: The basic premise or concept
            additional_instructions: Any additional planning requirements

        Returns:
            Comprehensive story arc plan
        """
        planning_context = f"""
Story Premise: {story_premise}

Genre: {genre}
Number of Chapters: {num_chapters}

Please create a comprehensive story arc that includes:
1. Three-Act Structure breakdown
2. Major plot points and turning points
3. Character arcs for main characters
4. Conflict escalation pattern
5. Thematic elements
6. Chapter-by-chapter outline with key events

{additional_instructions}
"""

        return f"Planning story arc:\n{planning_context}"
