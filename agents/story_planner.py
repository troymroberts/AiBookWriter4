# --- agents/story_planner.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
import yaml
import os  # Import os for path manipulation

class StoryPlanner:
    """Agent responsible for developing the overarching story arc."""

    def __init__(self, base_url, model, prompts_dir, genre, num_chapters, temperature=0.7, max_tokens=3000, top_p=0.95, context_window=8192, streaming=True): # Updated to take prompts_dir and num_chapters
        """
        Initializes the StoryPlanner agent with LLM configuration and prompts loaded from files.
        """
        self.llm = OllamaLLM(
            base_url=base_url,
            model=model,
            context_window=context_window,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            streaming=streaming # Use the streaming parameter here
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
        self.num_chapters = num_chapters # Store num_chapters as instance variable

    def plan_story_arc(self, genre, num_chapters, additional_instructions=""): # UPDATED: Removed default num_chapters=10 and using parameter
        """Plans the story arc for a novel, incorporating the configured genre."""
        chain = self.prompt | self.llm
        for chunk in chain.stream({ # Use chain.stream() for streaming
            "genre": genre, # Use the passed-in genre parameter
            "num_chapters": num_chapters, # UPDATED: Now using the num_chapters parameter passed to this method
            "additional_instructions": additional_instructions
        }):
            yield chunk # Yield each chunk to the caller for streaming