# --- agents/setting_builder.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
import yaml
import os  # Import os for path manipulation

class SettingBuilder:
    """Agent responsible for establishing and maintaining story settings."""

    def __init__(self, base_url, model, prompts_dir, temperature=0.7, max_tokens=2000, top_p=0.95, context_window=8192, streaming=True):
        """Initializes the SettingBuilder agent."""
        self.llm = OllamaLLM(
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            context_window=context_window,
            streaming=streaming
        )
        # Load prompts from genre-specific config file
        prompt_file_path = os.path.join(prompts_dir, "setting_builder.yaml") # Construct prompt file path
        with open(prompt_file_path, "r") as f:
            agent_prompts = yaml.safe_load(f) # Load prompts for this agent

        self.system_message = agent_prompts['system_message'] # Load system message
        self.user_prompt_template = agent_prompts['user_prompt'] # Load user prompt template

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("user", self.user_prompt_template)
        ])

    def run_information_gathering_task(self, task_description, outline_context): # Added outline_context
        """Executes the information gathering task for setting and returns the result."""
        chain = self.prompt | self.llm
        result = chain.invoke({
            "task_description": task_description,
            "outline_context": outline_context # Pass outline_context to prompt
        })
        return result