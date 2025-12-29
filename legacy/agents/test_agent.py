# --- agents/test_agent.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate

class TestAgent:
    """A simple test agent using Langchain and Ollama with streaming."""

    def __init__(self, base_url, model, temperature=0.7, context_window=8192):
        """
        Initializes the TestAgent with a given LLM configuration and streaming enabled.
        """
        self.llm = OllamaLLM(
            base_url=base_url,
            model=model,
            temperature=temperature,
            model_kwargs={'context_window': context_window},
            streaming=True  # <--- ENABLE STREAMING HERE
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful test agent. Please respond concisely."),
            ("user", "{task_prompt}")
        ])

    def run_test_task_stream(self, task_prompt): # Renamed to run_test_task_stream
        """
        Runs a test task and streams the output from the Ollama model.
        """
        chain = self.prompt | self.llm
        for chunk in chain.stream({"task_prompt": task_prompt}): # Use chain.stream()
            print(chunk, end="", flush=True) # Print each chunk immediately
        print() # Add a newline at the end of the stream

    def run_test_task(self, task_prompt): # Keep the non-streaming version too for comparison
        """Runs a test task without streaming (for comparison)."""
        chain = self.prompt | self.llm
        result = chain.invoke({"task_prompt": task_prompt})
        return result