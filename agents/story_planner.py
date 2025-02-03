from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class StoryPlannerConfig(BaseModel):
    """Configuration model for the StoryPlanner agent."""
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the story planner.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=3000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default="""You are an AI Story Planner specializing in creating high-level story arcs.
        Your task is to develop an overarching story arc that includes major plot points,
        character arcs, and turning points. Ensure the narrative has a captivating beginning,
        rising action, climax, and satisfying resolution.
        Your decisions are final, do not delegate or ask further questions.
        Respond with the final answer in the specified format.
        """,
        description="System template for the story planner agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the story planner agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the story planner agent."
    )
    
    class Config:
        arbitrary_types_allowed = True

class StoryPlanner(Agent):
    """
    Agent responsible for developing the overarching story arc, themes, and major plot points.
    """

    def __init__(self, config: StoryPlannerConfig):
        super().__init__(
            role='Chief Story Architect',
            goal='Develop a compelling and cohesive story arc with major plot points for the entire book.',
            backstory='Visionary storyteller with a knack for crafting engaging narratives.',
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
        )

    def create_llm(self, config: StoryPlannerConfig):
        from crewai.llm import LLM
        return LLM(
            base_url=config.llm_endpoint,
            model=config.llm_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            system_template=config.system_template,
            prompt_template=config.prompt_template,
            response_template=config.response_template,
        )