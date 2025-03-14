#--- START OF FILE agents/setting_builder.py ---
# --- agents/setting_builder.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
import yaml
import os  # Import os for path manipulation
from pydantic import BaseModel, Field
from typing import Optional

# Configuration model for the SettingBuilder agent
class SettingBuilderConfig(BaseModel):
    llm_endpoint: str = Field(
        default="http://localhost:11434",
        description="Endpoint for the language model server.",
    )
    llm_model: str = Field(
        default="ollama/llama3:latest",
        description="Model identifier for the setting builder.",
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
    context_window: int = Field(
        default=8192, description="Context window for the language model."
    )
    streaming: bool = Field(
        default=True, description="Enable streaming responses from the LLM."
    )
    system_template: Optional[str] = Field(
        default=None, description="System template for the setting builder agent."
    )
    prompt_template: Optional[str] = Field(
        default=None, description="Prompt template for the setting builder agent."
    )
    response_template: Optional[str] = Field(
        default=None, description="Response template for the setting builder agent."
    )

    class Config:
        arbitrary_types_allowed = True


class SettingBuilder:
    """Agent responsible for establishing and maintaining story settings."""

    def __init__(self, config: SettingBuilderConfig, prompts_dir, streaming=True):
        """Initializes the SettingBuilder agent."""
        self.llm = OllamaLLM(
            base_url=config.llm_endpoint,
            model=config.llm_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            context_window=config.context_window,
            streaming=streaming
        )
        # Load prompts from genre-specific config file
        prompts_dir = prompts_dir  # Ensure prompts_dir is used from init
        prompt_file_path = os.path.join(prompts_dir, "setting_builder.yaml")  # Construct prompt file path
        with open(prompt_file_path, "r") as f:
            agent_prompts = yaml.safe_load(f)  # Load prompts for this agent

        self.system_message = agent_prompts['system_message']  # Load system message
        self.user_prompt_template = agent_prompts['user_prompt']  # Load user prompt template

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("user", self.user_prompt_template)
        ])

    def run_information_gathering_task(self, task_description, outline_context):  # Added outline_context
        """Executes the information gathering task for setting and returns the result."""
        chain = self.prompt | self.llm
        result = chain.invoke({
            "task_description": task_description,
            "outline_context": outline_context  # Pass outline_context to prompt
        })
        return result
#--- END OF FILE agents/setting_builder.py ---