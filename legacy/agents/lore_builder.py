# --- agents/lore_builder.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
import yaml
import os  # Import os for path manipulation

class LoreBuilder:
    """Agent responsible for developing the story world lore."""

    def __init__(self, base_url, model, prompts_dir, temperature=0.7, max_tokens=3000, top_p=0.95, context_window=8192, streaming=False): 
        """Initializes the LoreBuilder agent with LLM configuration and prompts."""
        self.llm = OllamaLLM(
            base_url=base_url,
            model=model,
            context_window=context_window,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            streaming=streaming # Streaming can be False for initial lore generation
        )
        # Load prompts from genre-specific config file
        prompt_file_path = os.path.join(prompts_dir, "lore_builder.yaml") # Construct prompt file path
        with open(prompt_file_path, "r") as f:
            agent_prompts = yaml.safe_load(f) # Load prompts for this agent

        self.system_message = agent_prompts['system_message'] # Load system message
        self.user_prompt_template = agent_prompts['user_prompt'] # Load user prompt template

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("user", self.user_prompt_template)
        ])

    def build_lore(self, story_arc, genre): # Example task method
        """Builds detailed world lore based on the story arc and genre."""
        chain = self.prompt | self.llm
        result = chain.invoke({
            "story_arc": story_arc,
            "genre": genre,
        })
        return result # Return full lore output as string