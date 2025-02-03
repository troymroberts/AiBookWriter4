# --- agents/test_agent.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate

class TestAgent:
    """A simple test agent using Langchain and Ollama."""

    def __init__(self, base_url, model, temperature=0.7, context_window=8192):
        """
        Initializes the TestAgent with explicit LLM parameters.

        Args:
            base_url (str): The base URL of the Ollama server.
            model (str): The name of the Ollama model to use.
            temperature (float, optional): The temperature for text generation. Defaults to 0.7.
            context_window (int, optional): The context window size. Defaults to 8192.
        """
        self.llm = OllamaLLM(
            base_url=base_url,
            model=model,
            temperature=temperature,
            model_kwargs={'context_window': context_window} # Set context_window in model_kwargs
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful test agent. Please respond concisely."),
            ("user", "{task_prompt}")
        ])

    def run_test_task(self, task_prompt):
        """
        Runs a test task using the configured Ollama model.

        Args:
            task_prompt (str): The prompt for the task.

        Returns:
            str: The response from the Ollama model.
        """
        chain = self.prompt | self.llm
        result = chain.invoke({"task_prompt": task_prompt})
        return result