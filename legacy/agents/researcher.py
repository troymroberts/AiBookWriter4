from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class ResearcherConfig(BaseModel):
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the researcher.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=2000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default=None,
        description="System template for the researcher agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the researcher agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the researcher agent."
    )

    class Config:
        arbitrary_types_allowed = True

class Researcher(Agent):
    def __init__(self, config: ResearcherConfig):
        super().__init__(
            role='Researcher',
            goal=f"""
                Research specific information, gather relevant data, and provide accurate details to support the story, such as historical context, cultural details, or technical information.
                Consider the outline: {{outline_context}}
                """,
            backstory=f"""
                You are a skilled researcher with access to vast databases and a knack for finding the most relevant information.
                You research specific details needed for the story, such as information about historical context, cultural details, or technical information.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            # TODO: Add tools here
            tools=[],
        )

    def create_llm(self, config: ResearcherConfig):
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