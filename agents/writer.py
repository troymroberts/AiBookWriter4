"""
Writer Agent - Generates chapter prose with RAG-enhanced continuity checking.

This agent uses:
- Centralized LLM configuration
- RAG tools for character/plot continuity
- Streaming output for real-time chapter generation
- Genre-specific prompts
"""

from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
from config.llm_config import get_llm_config
import yaml
import os
from typing import Generator, Optional


class Writer:
    """
    Agent responsible for writing chapters based on outlines.

    Features:
    - Centralized LLM configuration
    - RAG integration for continuity checking
    - Streaming output
    - Genre-aware writing
    """

    def __init__(
        self,
        prompts_dir: str,
        genre: str,
        num_chapters: int,
        enable_rag: bool = True,
        base_url: Optional[str] = None,  # For backward compatibility
        model: Optional[str] = None,  # For backward compatibility
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        context_window: Optional[int] = None
    ):
        """
        Initialize the Writer agent with LLM configuration and prompts.

        Args:
            prompts_dir: Directory containing prompt YAML files
            genre: Story genre
            num_chapters: Total number of chapters
            enable_rag: Enable RAG tools for continuity (default: True)
            base_url: (Deprecated) Use centralized config instead
            model: (Deprecated) Use centralized config instead
            temperature: Override temperature from config
            max_tokens: Override max_tokens from config
            top_p: Override top_p from config
            context_window: Override context window from config
        """
        # Get centralized LLM configuration
        llm_config = get_llm_config()
        agent_config = llm_config.get_agent_config("writer")

        # Override with provided parameters
        if temperature is not None:
            agent_config['temperature'] = temperature
        if max_tokens is not None:
            agent_config['max_tokens'] = max_tokens
        if top_p is not None:
            agent_config['top_p'] = top_p

        # Backward compatibility: use provided base_url/model if given
        if base_url and model:
            self.llm = OllamaLLM(
                base_url=base_url,
                model=model,
                context_window=context_window or 128000,
                temperature=agent_config.get('temperature', 0.8),
                max_tokens=agent_config.get('max_tokens', 16384),
                top_p=agent_config.get('top_p', 0.95),
                streaming=True
            )
        else:
            # Use centralized config to create LLM
            # Note: For LangChain compatibility, we'll create Ollama LLM directly
            provider_config = llm_config.get_provider_config("writer")

            if provider_config['provider'] == 'ollama':
                self.llm = OllamaLLM(
                    base_url=provider_config.get('base_url', 'http://localhost:11434'),
                    model=provider_config.get('model', 'llama3.2'),
                    context_window=context_window or 128000,
                    temperature=agent_config.get('temperature', 0.8),
                    max_tokens=agent_config.get('max_tokens', 16384),
                    top_p=agent_config.get('top_p', 0.95),
                    streaming=True
                )
            else:
                # For other providers, use CrewAI LLM wrapper
                self.llm = llm_config.create_llm("writer")

        # Load prompts from genre-specific config file
        prompt_file_path = os.path.join(prompts_dir, "writer.yaml")
        with open(prompt_file_path, "r") as f:
            agent_prompts = yaml.safe_load(f)

        self.system_message = agent_prompts['system_message']
        self.user_prompt_template = agent_prompts['user_prompt']

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("user", self.user_prompt_template)
        ])

        self.genre = genre
        self.num_chapters = num_chapters
        self.enable_rag = enable_rag

        # Initialize RAG tools if enabled
        if self.enable_rag:
            self._init_rag_tools()

    def _init_rag_tools(self):
        """Initialize RAG tools for continuity checking during writing."""
        try:
            from rag.vector_store import VectorStoreManager
            self.vector_store = VectorStoreManager()
            self.rag_available = True
        except Exception as e:
            print(f"Warning: RAG tools not available: {e}")
            self.rag_available = False

    def check_continuity(self, context: str, query: str) -> str:
        """
        Check story continuity using RAG before/during writing.

        Args:
            context: Current writing context
            query: What to check (e.g., "character description", "previous events")

        Returns:
            Relevant story information from RAG
        """
        if not self.enable_rag or not self.rag_available:
            return "RAG not available"

        try:
            # Search across all collections for relevant context
            results = []

            # Check characters
            char_results = self.vector_store.semantic_search(
                collection_name='characters',
                query=query,
                n_results=2
            )
            if char_results['ids']:
                results.append(f"Characters: {', '.join(char_results['documents'])}")

            # Check plot events
            plot_results = self.vector_store.semantic_search(
                collection_name='plot_events',
                query=query,
                n_results=3
            )
            if plot_results['ids']:
                results.append(f"Previous events: {', '.join(plot_results['documents'][:2])}")

            return "\n\n".join(results) if results else "No relevant context found"

        except Exception as e:
            return f"Error checking continuity: {e}"

    def write_chapter(
        self,
        chapter_outline: str,
        genre_config: dict,
        check_continuity: bool = True
    ) -> Generator[str, None, None]:
        """
        Write a chapter based on the provided outline and genre configuration.

        Args:
            chapter_outline: Detailed outline for the chapter
            genre_config: Genre-specific configuration
            check_continuity: Whether to check RAG for continuity (default: True)

        Yields:
            Chapter text chunks (streaming)
        """
        # Optionally augment context with RAG continuity check
        enhanced_outline = chapter_outline

        if check_continuity and self.enable_rag and self.rag_available:
            try:
                # Check for relevant context from previous chapters
                continuity_context = self.check_continuity(
                    context=chapter_outline,
                    query="previous events and character details"
                )

                if continuity_context and continuity_context != "No relevant context found":
                    enhanced_outline = f"{chapter_outline}\n\n## Story Context (for continuity):\n{continuity_context}"
            except Exception as e:
                print(f"Warning: Continuity check failed: {e}")

        # Create chain and stream output
        chain = self.prompt | self.llm
        task_input = {
            "outline_context": enhanced_outline,
            "num_chapters": self.num_chapters,
            "genre_config": genre_config,
        }

        # Stream output chunks
        for chunk in chain.stream(task_input):
            yield chunk

    def write_chapter_sync(
        self,
        chapter_outline: str,
        genre_config: dict,
        check_continuity: bool = True
    ) -> str:
        """
        Non-streaming version of write_chapter (returns complete text).

        Args:
            chapter_outline: Detailed outline for the chapter
            genre_config: Genre-specific configuration
            check_continuity: Whether to check RAG for continuity

        Returns:
            Complete chapter text
        """
        chunks = []
        for chunk in self.write_chapter(chapter_outline, genre_config, check_continuity):
            chunks.append(chunk)
        return "".join(chunks)
