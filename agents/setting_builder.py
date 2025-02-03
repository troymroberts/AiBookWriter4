from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class SettingBuilderConfig(BaseModel):
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the setting builder.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=2000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default=None,
        description="System template for the setting builder agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the setting builder agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the setting builder agent."
    )

    class Config:
        arbitrary_types_allowed = True

class SettingBuilder(Agent):
    def __init__(self, config: SettingBuilderConfig):
        super().__init__(
            role='Setting Builder',
            goal=f"""
                Establish and maintain all settings and world elements needed for the story, ensuring they are rich, consistent, and dynamically integrated as the story progresses.
                Consider the outline for the story and genre specific settings.
                """,
            backstory=f"""
                You are an expert in setting and world-building, responsible for creating rich, consistent, and evolving settings that enhance the story.
                You establish all settings and world elements needed for the entire story and ensure they are dynamically integrated as the story progresses.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            # TODO: Add tools here
            tools=[],
        )

    def create_llm(self, config: SettingBuilderConfig):
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