from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class MemoryKeeperConfig(BaseModel):
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the memory keeper.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=2000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default=None,
        description="System template for the memory keeper agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the memory keeper agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the memory keeper agent."
    )

    class Config:
        arbitrary_types_allowed = True

class MemoryKeeper(Agent):
    def __init__(self, config: MemoryKeeperConfig):
        super().__init__(
            role='Memory Keeper',
            goal=f"""
                Track and summarize each chapter's key events, character developments, and world details for a {{num_chapters}}-chapter story.
                Monitor character development and relationships for consistency, maintain world-building consistency, and flag any continuity issues.
                Consider the outline: {{outline_context}}
                """,
            backstory=f"""
                You are the keeper of the story's continuity and context.
                You track and summarize each chapter's key events, character developments, and world details, monitor character development and relationships for consistency, maintain world-building consistency, and flag any continuity issues.
                You are working on a {{num_chapters}}-chapter story.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            # TODO: Add tools here
            tools=[],
        )

    def create_llm(self, config: MemoryKeeperConfig):
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