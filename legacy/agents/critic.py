from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class CriticConfig(BaseModel):
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the critic.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=2000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default=None,
        description="System template for the critic agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the critic agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the critic agent."
    )

    class Config:
        arbitrary_types_allowed = True

class Critic(Agent):
    def __init__(self, config: CriticConfig):
        super().__init__(
            role='Critic',
            goal=f"""
                Provide constructive criticism of each chapter, identifying plot holes, inconsistencies, and areas for improvement in terms of narrative structure, character development, and pacing for a {{num_chapters}}-chapter story.
                Additionally, evaluate the scene order within each chapter and suggest improvements to scene order for better pacing, tension, and flow.
                Consider the outline: {{outline_context}}
                Incorporate the genre-specific critique style: {{genre_config.get('CRITIQUE_STYLE')}}.
                """,
            backstory=f"""
                You are a discerning critic, able to analyze stories and offer insightful feedback for enhancement.
                You provide a critical review of each chapter, identifying any plot holes, inconsistencies, or areas that need improvement.
                You are also skilled at analyzing scene order within chapters and suggesting reorderings to enhance narrative impact.
                You are working on a {{num_chapters}}-chapter story in the {{genre_config.get('GENRE')}} genre.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            # TODO: Add tools here
            tools=[],
        )

    def create_llm(self, config: CriticConfig):
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