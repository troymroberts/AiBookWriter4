# --- agents/story_planner.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
import yaml
import os  # Import os for path manipulation
from pydantic import BaseModel, Field
from typing import Optional

# Configuration model for the StoryPlanner agent
class StoryPlannerConfig(BaseModel):
    llm_endpoint: str = Field(
        default="http://localhost:11434",
        description="Endpoint for the language model server.",
    )
    llm_model: str = Field(
        default="ollama/llama3:latest",
        description="Model identifier for the story planner.",
    )
    temperature: float = Field(
        default=0.7, description="Temperature setting for the language model."
    )
    max_tokens: int = Field(
        default=3000, description="Maximum number of tokens for the language model."
    )
    top_p: float = Field(
        default=0.95, description="Top-p sampling parameter for the language model."
    )
    context_window: int = Field(
        default=8192, description="Context window for the language model."
    )
    streaming: bool = Field(
        default=True, description="Enable streaming responses from the LLM."
    )
    system_template: Optional[str] = Field(
        default=None, description="System template for the story planner agent."
    )
    prompt_template: Optional[str] = Field(
        default=None, description="Prompt template for the story planner agent."
    )
    response_template: Optional[str] = Field(
        default=None, description="Response template for the story planner agent."
    )

    class Config:
        arbitrary_types_allowed = True


class StoryPlanner:
    """Agent responsible for developing the overarching story arc."""

    def __init__(self, config: StoryPlannerConfig, prompts_dir, genre, num_chapters, streaming=True):  # Updated to take config and prompts_dir
        """
        Initializes the StoryPlanner agent with LLM configuration and prompts loaded from files.
        """
        self.llm = OllamaLLM(
            base_url=config.llm_endpoint,
            model=config.llm_model,
            context_window=config.context_window,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            streaming=streaming  # Use the streaming parameter here
        )
        # Load prompts from genre-specific config file
        prompts_dir = prompts_dir # Ensure prompts_dir is used from init
        prompt_file_path = os.path.join(prompts_dir, "story_planner.yaml") # Construct prompt file path
        with open(prompt_file_path, "r") as f:
            agent_prompts = yaml.safe_load(f) # Load prompts for this agent

        self.system_message = agent_prompts['system_message'] # Load system message
        self.user_prompt_template = agent_prompts['user_prompt'] # Load user prompt template

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("user", self.user_prompt_template)
        ])
        self.genre = genre
        self.num_chapters = num_chapters  # Store num_chapters as instance variable
        print(f"DEBUG agents/story_planner.py: StoryPlanner __init__ received num_chapters: {num_chapters}") # DEBUG PRINT

    def plan_story_arc(self, genre, num_chapters, additional_instructions=""):  # UPDATED: Removed default num_chapters=10 and using parameter
        """Plans the story arc for a novel, incorporating the configured genre."""
        chain = self.prompt | self.llm
        print(f"DEBUG agents/story_planner.py: plan_story_arc received num_chapters: {num_chapters}") # DEBUG PRINT
        for chunk in chain.stream({  # Use chain.stream() for streaming
            "genre": genre,  # Use the passed-in genre parameter
            "num_chapters": num_chapters,  # UPDATED: Now using the num_chapters parameter passed to this method
            "additional_instructions": additional_instructions
        }):
            yield chunk  # Yield each chunk to the caller for streaming