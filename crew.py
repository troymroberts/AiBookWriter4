"""
AiBookWriter4 - Book Writing Crew
Main orchestrator for the AI book writing workflow using CrewAI.
"""

from crewai import Crew, Process
from typing import Optional, Callable
import yaml
import os

from agents import (
    create_llm,
    create_story_planner,
    create_setting_builder,
    create_outline_creator,
    create_writer,
    load_genre_config
)
from tasks import create_core_workflow_tasks


class BookWritingCrew:
    """Orchestrates the AI book writing workflow using CrewAI."""

    def __init__(
        self,
        config_path: str = "config.yaml",
        genre: Optional[str] = None,
        num_chapters: Optional[int] = None
    ):
        """Initialize the BookWritingCrew.

        Args:
            config_path: Path to the configuration file.
            genre: Override genre from config.
            num_chapters: Override number of chapters from config.
        """
        self.config = self._load_config(config_path)

        # Apply overrides
        self.genre = genre or self.config['defaults']['genre']
        self.num_chapters = num_chapters or self.config['defaults']['num_chapters']

        # Load genre-specific configuration
        self.genre_config = load_genre_config(
            self.genre,
            self.config['paths']['genres_dir']
        )

        # Create LLMs for each agent
        self.llms = self._create_llms()

        # Create agents
        self.agents = self._create_agents()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _create_llms(self) -> dict:
        """Create LLM instances for each agent."""
        ollama_config = self.config['ollama']
        llm_params = self.config['llm']

        base_url = ollama_config['base_url']
        default_model = ollama_config['default_model']
        model_overrides = ollama_config.get('models', {})

        llms = {}
        for agent_name in ['story_planner', 'setting_builder', 'outline_creator', 'writer']:
            model = model_overrides.get(agent_name, default_model)
            llms[agent_name] = create_llm(
                base_url=base_url,
                model=model,
                temperature=llm_params['temperature'],
                max_tokens=llm_params['max_tokens'],
                top_p=llm_params['top_p']
            )

        return llms

    def _create_agents(self) -> dict:
        """Create all agents with their configured LLMs."""
        return {
            'story_planner': create_story_planner(
                self.llms['story_planner'],
                self.genre_config
            ),
            'setting_builder': create_setting_builder(
                self.llms['setting_builder'],
                self.genre_config
            ),
            'outline_creator': create_outline_creator(
                self.llms['outline_creator'],
                self.genre_config
            ),
            'writer': create_writer(
                self.llms['writer'],
                self.genre_config
            )
        }

    def run_planning_workflow(
        self,
        story_prompt: str,
        additional_instructions: str = "",
        step_callback: Optional[Callable] = None
    ) -> dict:
        """Run the core planning workflow (story arc, settings, outline).

        Args:
            story_prompt: The initial story idea/premise.
            additional_instructions: Optional additional guidance.
            step_callback: Optional callback for progress updates.

        Returns:
            Dictionary containing outputs from each task.
        """
        # Create tasks
        tasks = create_core_workflow_tasks(
            story_planner=self.agents['story_planner'],
            setting_builder=self.agents['setting_builder'],
            outline_creator=self.agents['outline_creator'],
            genre=self.genre,
            num_chapters=self.num_chapters,
            story_prompt=story_prompt,
            additional_instructions=additional_instructions
        )

        # Create and run crew
        crew = Crew(
            agents=[
                self.agents['story_planner'],
                self.agents['setting_builder'],
                self.agents['outline_creator']
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=self.config['crew'].get('verbose', True)
        )

        # Execute the crew
        result = crew.kickoff()

        # Package results
        return {
            'story_arc': tasks[0].output.raw if hasattr(tasks[0], 'output') else str(result),
            'settings': tasks[1].output.raw if hasattr(tasks[1], 'output') else "",
            'outline': tasks[2].output.raw if hasattr(tasks[2], 'output') else "",
            'full_output': result.raw if hasattr(result, 'raw') else str(result)
        }

    def get_available_genres(self) -> list:
        """Get list of available genre configurations."""
        genres_dir = self.config['paths']['genres_dir']
        if not os.path.exists(genres_dir):
            return []

        return [
            f[:-3] for f in os.listdir(genres_dir)
            if f.endswith('.py') and not f.startswith('_')
        ]


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Book Writer - CrewAI")
    parser.add_argument('--genre', default='literary_fiction', help='Genre for the book')
    parser.add_argument('--chapters', type=int, default=4, help='Number of chapters')
    parser.add_argument('--prompt', required=True, help='Story prompt/premise')
    parser.add_argument('--instructions', default='', help='Additional instructions')
    parser.add_argument('--output', default='output/result.txt', help='Output file path')

    args = parser.parse_args()

    print(f"Starting AI Book Writer...")
    print(f"Genre: {args.genre}")
    print(f"Chapters: {args.chapters}")
    print(f"Prompt: {args.prompt[:100]}...")
    print("-" * 50)

    # Create and run crew
    crew = BookWritingCrew(
        genre=args.genre,
        num_chapters=args.chapters
    )

    results = crew.run_planning_workflow(
        story_prompt=args.prompt,
        additional_instructions=args.instructions
    )

    # Save results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("STORY ARC\n")
        f.write("=" * 60 + "\n\n")
        f.write(results['story_arc'] + "\n\n")

        f.write("=" * 60 + "\n")
        f.write("WORLD SETTINGS\n")
        f.write("=" * 60 + "\n\n")
        f.write(results['settings'] + "\n\n")

        f.write("=" * 60 + "\n")
        f.write("CHAPTER OUTLINES\n")
        f.write("=" * 60 + "\n\n")
        f.write(results['outline'] + "\n")

    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
