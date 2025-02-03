# --- agents/story_planner.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
import yaml # Import PyYAML to load config

class StoryPlanner:
    """Agent responsible for developing the overarching story arc."""

    def __init__(self, base_url, model, prompts, genre, temperature=0.7, max_tokens=3000, top_p=0.95, context_window=8192):
        """
        Initializes the StoryPlanner agent with LLM configuration and prompts.

        Args:
            base_url (str): Base URL of the Ollama server.
            model (str): Model identifier.
            prompts (dict): Dictionary of prompts loaded from config.
            genre (str): The selected literary genre. # ADDED genre parameter
            temperature (float, optional): Temperature for generation. Defaults to 0.7.
            max_tokens (int, optional): Maximum tokens in response. Defaults to 3000.
            top_p (float, optional): Top-p sampling parameter. Defaults to 0.95.
            context_window (int, optional): Context window size. Defaults to 8192.
        """
        self.llm = OllamaLLM(
            base_url=base_url,
            model=model,
            context_window=context_window,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        # Load prompts from config
        self.system_message = prompts['story_planner']['system_message']
        self.user_prompt_template = prompts['story_planner']['user_prompt']

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message), # Use system message from config
            ("user", self.user_prompt_template) # Use user prompt template from config
        ])
        self.genre = genre # Store the genre

    def plan_story_arc(self, num_chapters=10, additional_instructions=""):
        """
        Plans the story arc for a novel, incorporating the configured genre.

        Args:
            num_chapters (int, optional): Number of chapters. Defaults to 10.
            additional_instructions (str, optional): Any specific instructions. Defaults to "".

        Returns:
            str: The generated story arc.
        """
        chain = self.prompt | self.llm
        result = chain.invoke({
            "genre": self.genre, # Use the stored genre
            "num_chapters": num_chapters,
            "additional_instructions": additional_instructions
        })
        return result