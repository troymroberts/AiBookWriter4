from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class EditorConfig(BaseModel):
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the editor.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=2000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default=None,
        description="System template for the editor agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the editor agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the editor agent."
    )

    class Config:
        arbitrary_types_allowed = True

class Editor(Agent):
    def __init__(self, config: EditorConfig):
        super().__init__(
            role='Editor',
            goal=f"""
                Review and refine each chapter, providing feedback to the writer if necessary for a {{num_chapters}}-chapter story.
                Ensure each chapter is well-written, consistent with the outline, and free of errors.
                Verify that each chapter meets the minimum length requirement of between {{genre_config.get('MIN_WORDS_PER_CHAPTER', 1600)}} and {{genre_config.get('MAX_WORDS_PER_CHAPTER', 3000)}} words. If a chapter is too short, provide specific feedback to the Writer on what areas need expansion.
                ONLY WORK ON ONE CHAPTER AT A TIME.
                Consider the outline: {{outline_context}}
                Incorporate the genre-specific editing style: {{genre_config.get('PROSE_COMPLEXITY')}}.
                """,
            backstory=f"""
                You are an expert editor ensuring quality, consistency, and adherence to the book outline and style guidelines.
                You check for strict alignment with the chapter outline, verify character and world-building consistency, and critically review and improve prose quality.
                You also ensure that each chapter meets the length requirement of between {{genre_config.get('MIN_WORDS_PER_CHAPTER', 1600)}} and {{genre_config.get('MAX_WORDS_PER_CHAPTER', 3000)}} words.
                You are working on a {{num_chapters}}-chapter story in the {{genre_config.get('GENRE')}} genre, ONE CHAPTER AT A TIME.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            # TODO: Add tools here
            tools=[],
        )

    def create_llm(self, config: EditorConfig):
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