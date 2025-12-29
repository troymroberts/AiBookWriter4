from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class ItemDeveloperConfig(BaseModel):
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the item developer.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=2000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default=None,
        description="System template for the item developer agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the item developer agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the item developer agent."
    )

    class Config:
        arbitrary_types_allowed = True

class ItemDeveloper(Agent):
    def __init__(self, config: ItemDeveloperConfig):
        super().__init__(
            role='Item Developer',
            goal=f"""
                Develop and maintain a consistent and relevant list of items for the story.
                Define each item with a name, detailed description, purpose in the story, and potential symbolic meaning.
                Track how each item is used across different chapters and scenes.
                Consider the outline: {{outline_context}}
                Incorporate the genre-specific item significance: {{genre_config.get('ITEM_SIGNIFICANCE', 'medium')}}.
                """,
            backstory=f"""
                You are the expert in item creation and management, responsible for enriching the story with meaningful items.
                You define and track all important items, ensuring they are consistent with the world-building and contribute to the plot and themes.
                You are working on a story in the {{genre_config.get('GENRE')}} genre.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            # TODO: Add tools here
            tools=[],
        )

    def create_llm(self, config: ItemDeveloperConfig):
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