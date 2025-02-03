# --- agents/writer.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
import yaml
import os # Import os for path manipulation

class Writer:
    """Agent responsible for writing chapters based on outlines."""

    def __init__(self, base_url, model, prompts_dir, genre, num_chapters, temperature=0.7, max_tokens=3000, top_p=0.95, context_window=8192): # ADDED num_chapters parameter
        """
        Initializes the Writer agent with LLM configuration and prompts loaded from files.
        """
        self.llm = OllamaLLM(
            base_url=base_url,
            model=model,
            context_window=context_window,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            streaming=True # Enable streaming for Writer
        )
        # Load prompts from genre-specific config file
        prompt_file_path = os.path.join(prompts_dir, "writer.yaml") # Construct prompt file path
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


    def write_chapter(self, chapter_outline, genre_config):
        """Writes a chapter based on the provided outline and genre configuration."""
        chain = self.prompt | self.llm
        task_input = {
            "outline_context": chapter_outline, # Pass the chapter outline as context
            "num_chapters": self.num_chapters, # Use self.num_chapters here
            "genre_config": genre_config,
        }
        # For streaming, use chain.stream instead of chain.invoke
        for chunk in chain.stream(task_input):
            yield chunk # Yield each chunk for streaming