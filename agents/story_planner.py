# --- agents/story_planner.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
import yaml
import os  # Import os for path manipulation

class StoryPlanner:
    """Agent responsible for developing the overarching story arc."""

    def __init__(self, base_url, model, prompts_dir, genre, temperature=0.7, max_tokens=3000, top_p=0.95, context_window=8192): # Updated to take prompts_dir
        """
        Initializes the StoryPlanner agent with LLM configuration and prompts loaded from files.
        """
        self.llm = OllamaLLM(
            base_url=base_url,
            model=model,
            context_window=context_window,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        # Load prompts from genre-specific config file
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

    def plan_story_arc(self, num_chapters=10, additional_instructions=""):
        """Plans the story arc for a novel, incorporating the configured genre."""
        chain = self.prompt | self.llm
        result = chain.invoke({
            "genre": self.genre,
            "num_chapters": num_chapters,
            "additional_instructions": additional_instructions
        })
        return result