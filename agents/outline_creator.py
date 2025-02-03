from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional
from crewai.tools import BaseTool
# from crewai_tools import  # Add this when we have specific tools later
from tools.ywriter_tools import (
    ReadProjectNotesTool,
    WriteProjectNoteTool,
    CreateChapterTool,
    ReadOutlineTool,
    ReadCharactersTool,
    ReadLocationsTool,
)  # Absolute import
# from ..tools.rag_tools import RAGTool  # Add this when we implement RAG

# Configuration model for the OutlineCreator agent
class OutlineCreatorConfig(BaseModel):
    llm_endpoint: str = Field(
        default="http://localhost:11434",
        description="Endpoint for the language model server.",
    )
    llm_model: str = Field(
        default="ollama/llama3:latest",
        description="Model identifier for the outline creator.",
    )
    temperature: float = Field(
        default=0.7, description="Temperature setting for the language model."
    )
    max_tokens: int = Field(
        default=2000, description="Maximum number of tokens for the language model."
    )
    top_p: float = Field(
        default=0.95, description="Top-p sampling parameter for the language model."
    )
    system_template: Optional[str] = Field(
        default=None, description="System template for the outline creator agent."
    )
    prompt_template: Optional[str] = Field(
        default=None, description="Prompt template for the outline creator agent."
    )
    response_template: Optional[str] = Field(
        default=None, description="Response template for the outline creator agent."
    )

    class Config:
        arbitrary_types_allowed = True

# Placeholder for a custom tool to assist with chapter breakdowns
class ChapterBreakdownTool(BaseTool):
    name: str = "Chapter Breakdown Tool"
    description: str = "Assists in dividing the story arc into chapters with appropriate pacing."

    def _run(self, **kwargs) -> str:
        # Implementation for breaking down chapters
        return "Chapter breakdown logic executed."

# Placeholder for a custom tool to format outlines
class OutlineTemplateTool(BaseTool):
    name: str = "Outline Template Tool"
    description: str = (
        "Formats the outline according to genre conventions and project requirements."
    )

    def _run(self, **kwargs) -> str:
        # Implementation for formatting the outline
        return "Outline formatting logic executed."

class OutlineCreator(Agent):
    """
    Agent responsible for generating detailed chapter outlines based on the story arc plan.
    """

    def __init__(self, config: OutlineCreatorConfig, tools: Optional[list[BaseTool]] = None):
        if tools is None:
            tools = []

        tools.extend([
            ChapterBreakdownTool(),
            OutlineTemplateTool(),
        ])

        super().__init__(
            role="Master Outliner",
            goal=f"""
                Generate detailed chapter outlines based on the story arc plan for a {{num_chapters}}-chapter story.
                Include specific chapter titles, key events, character developments, setting, and relevant items for each chapter.
                ONLY CREATE THE OUTLINE FOR ONE CHAPTER AT A TIME
                Consider the overall story arc provided in PROJECTNOTES.
                Incorporate the genre-specific narrative style: {{genre_config.get('NARRATIVE_STYLE')}}.
                Ensure each chapter outline considers and lists relevant characters, locations, and items.
                """,
            backstory=f"""
                You are an expert outline creator who generates detailed chapter outlines based on story premises and story arc plans.
                Your outlines must follow a strict format, including Chapter Title, Key Events, Character Developments, Setting, Tone, and Items for each chapter.
                You are creating an outline for a {{num_chapters}}-chapter story in the {{genre_config.get('GENRE')}} genre.
                You create outlines for ONE CHAPTER AT A TIME.
                Your outlines must explicitly list characters, locations, and items relevant to each chapter.
                """,
            verbose=True,
            allow_delegation=False,
            llm=self.create_llm(config),
            tools=tools,
        )

    def create_llm(self, config: OutlineCreatorConfig):
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