# --- agents/story_planner.py ---
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate

class StoryPlanner:
    """Agent responsible for developing the overarching story arc."""

    def __init__(self, base_url, model, temperature=0.7, max_tokens=3000, top_p=0.95):
        """
        Initializes the StoryPlanner agent with LLM configuration.

        Args:
            base_url (str): Base URL of the Ollama server.
            model (str): Model identifier.
            temperature (float, optional): Temperature for generation. Defaults to 0.7.
            max_tokens (int, optional): Maximum tokens in response. Defaults to 3000.
            top_p (float, optional): Top-p sampling parameter. Defaults to 0.95.
        """
        self.llm = OllamaLLM(
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI Story Planner specializing in creating high-level story arcs.
            Your task is to develop an overarching story arc that includes major plot points,
            character arcs, and turning points. Ensure the narrative has a captivating beginning,
            rising action, climax, and satisfying resolution.
            Your decisions are final, do not delegate or ask further questions.
            Respond with the final answer in the specified format."""),
            ("user", "{genre} story of {num_chapters} chapters. {additional_instructions}")
        ])

    def plan_story_arc(self, genre="mystery", num_chapters=10, additional_instructions=""):
        """
        Plans the story arc for a novel.

        Args:
            genre (str, optional): Genre of the story. Defaults to "mystery".
            num_chapters (int, optional): Number of chapters. Defaults to 10.
            additional_instructions (str, optional): Any specific instructions. Defaults to "".

        Returns:
            str: The generated story arc.
        """
        chain = self.prompt | self.llm
        result = chain.invoke({
            "genre": genre,
            "num_chapters": num_chapters,
            "additional_instructions": additional_instructions
        })
        return result