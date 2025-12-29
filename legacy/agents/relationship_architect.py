from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class RelationshipArchitectConfig(BaseModel):
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the relationship architect.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=2000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default=None,
        description="System template for the relationship architect agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the relationship architect agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the relationship architect agent."
    )

    class Config:
        arbitrary_types_allowed = True

class RelationshipArchitect(Agent):
    def __init__(self, config: RelationshipArchitectConfig):
        super().__init__(
            role='Relationship Architect',
            goal=f"""
                Develop and manage the relationships between characters, including family structures, friendships, rivalries, and romantic relationships.
                Ensure relationship dynamics are realistic, engaging, and contribute to the overall narrative.
                Provide detailed relationship backstories and evolution.
                """,
            backstory=f"""
                You are the relationship expert, responsible for creating and maintaining realistic and engaging relationships between characters.
                You define family structures, friendships, rivalries, and romantic relationships, providing detailed backstories and evolution.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            # TODO: Add tools here
            tools=[],
        )

    def create_llm(self, config: RelationshipArchitectConfig):
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