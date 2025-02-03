from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class ReviserConfig(BaseModel):
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the reviser.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=2000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default=None,
        description="System template for the reviser agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the reviser agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the reviser agent."
    )

    class Config:
        arbitrary_types_allowed = True

class Reviser(Agent):
    def __init__(self, config: ReviserConfig):
        super().__init__(
            role='Reviser',
            goal=f"""
                Revise each chapter based on feedback from the Critic and Editor, ensuring the chapter is coherent, consistent, and polished for a {{num_chapters}}-chapter story.
                Incorporate revisions to improve the story's quality and readability.
                Incorporate any suggested scene reordering from the Critic. If scenes are reordered, rewrite scene transitions to ensure smooth flow and coherence.
                Consider the outline: {{outline_context}}
                """,
            backstory=f"""
                You are a skilled reviser, capable of incorporating feedback and polishing each chapter to perfection.
                You revise the story based on feedback, ensuring the story is coherent, consistent, and polished.
                You are working on a {{num_chapters}}-chapter story in the {{genre_config.get('GENRE')}} genre.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            # TODO: Add tools here
            tools=[],
        )

    def create_llm(self, config: ReviserConfig):
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