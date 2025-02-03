# --- agents/setting_builder.py ---
from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
import yaml
import os # Import os for path manipulation

class SettingBuilder: # Removed Config inheritance and class
    def __init__(self, base_url, model, prompts_dir, temperature=0.7, max_tokens=2000, top_p=0.95, context_window=8192, streaming=True): # Removed config: SettingBuilderConfig
        """Initialize the SettingBuilder agent."""
        self.llm = OllamaLLM( # Direct OllamaLLM initialization
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

        self.system_template = agent_prompts['system_message'] # Load system message
        self.prompt_template = agent_prompts['user_prompt'] # Load user prompt template

        self.prompt = ChatPromptTemplate.from_messages([ # Direct ChatPromptTemplate
            ("system", self.system_template),
            ("user", self.prompt_template)
        ])

    def run_information_gathering_task(self, task_description): # Renamed and simplified, now takes task_description directly
        """Executes the information gathering task and returns the result."""
        chain = self.prompt | self.llm
        result = chain.invoke({"task_description": task_description}) # Simplified invoke
        return result # Return full result as string