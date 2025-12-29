from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class PlotAgentConfig(BaseModel):
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the plot agent.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=2000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default=None,
        description="System template for the plot agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the plot agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the plot agent."
    )

    class Config:
        arbitrary_types_allowed = True

class PlotAgent(Agent):
    def __init__(self, config: PlotAgentConfig):
        super().__init__(
            role='Plot Agent',
            goal=f"""
                Refine chapter outlines to maximize plot effectiveness and pacing at the chapter level, ensuring each chapter's plot is engaging, well-paced, and contributes to the overall story arc.
                Incorporate the genre-specific plot complexity.
                Ensure each chapter outline clearly defines the Goal, Conflict, and Outcome for each scene.
                Ensure each chapter outline links relevant characters, locations, and items to the scenes.
                """,
            backstory=f"""
                You are the plot detail expert, responsible for ensuring each chapter's plot is engaging, well-paced, and contributes to the overall story arc.
                You refine chapter outlines to maximize plot effectiveness and pacing at the chapter level.
                Your refined outlines must include specific Goal, Conflict, and Outcome for each scene and explicitly link characters, locations, and items.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            # TODO: Add tools here
            tools=[],
        )

    def create_llm(self, config: PlotAgentConfig):
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