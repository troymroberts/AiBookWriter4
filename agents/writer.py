from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class WriterConfig(BaseModel):
    llm_endpoint: str = Field(default="http://10.1.1.47:11434", description="Endpoint for the language model server.")
    llm_model: str = Field(default="ollama/llama3.2:1b", description="Model identifier for the writer.")
    temperature: float = Field(default=0.7, description="Temperature setting for the language model.")
    max_tokens: int = Field(default=3000, description="Maximum number of tokens for the language model.")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter for the language model.")
    system_template: Optional[str] = Field(
        default=None,
        description="System template for the writer agent."
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Prompt template for the writer agent."
    )
    response_template: Optional[str] = Field(
        default=None,
        description="Response template for the writer agent."
    )

    class Config:
        arbitrary_types_allowed = True

class Writer(Agent):
    def __init__(self, config: WriterConfig):
        super().__init__(
            role='Writer',
            goal=f"""
                Write individual chapters based on the provided chapter outline, expanding on the key events, character developments, and setting descriptions with vivid prose and engaging dialogue.
                Pay close attention to the character profiles, including their stats and speech patterns, to create realistic and consistent dialogue and interactions.
                Adhere to the specified tone and style for each chapter, and follow the genre-specific instructions.
                Each chapter MUST be at least {{{{genre_config.get('MIN_WORDS_PER_CHAPTER', 1600)}}}} words in length. Consider this a HARD REQUIREMENT. If your output is shorter, continue writing until you reach this minimum length.
                ONLY WRITE ONE CHAPTER AT A TIME.
                Refer to the provided chapter outline for the content and structure of each chapter, including the list of items relevant to the chapter.
                """,
            backstory=f"""
                You are an expert creative writer who brings scenes to life with vivid prose, compelling characters, and engaging plots.
                You write according to the detailed chapter outline, incorporating all Key Events, Character Developments, Setting, Tone, and Items, while maintaining consistent character voices and personalities.
                You use the character stats and speech patterns defined by the Character Agent to guide your writing.
                You are working on a {{num_chapters}}-chapter story in the {{genre_config.get('GENRE')}} genre, ONE CHAPTER AT A TIME, with each chapter being at least {{{{genre_config.get('MIN_WORDS_PER_CHAPTER', 1600)}}}} words long.
                You are committed to meeting the word count for each chapter and will not stop writing until this requirement is met.
                You will be provided with the specific outline for each chapter and you must adhere to it, paying special attention to the items listed for each chapter.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            # TODO: Add tools here
            tools=[],
        )

    def create_llm(self, config: WriterConfig):
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