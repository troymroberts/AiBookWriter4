"""
AiBookWriter4 - Workflow Orchestrator
Coordinates agent execution with parallel/sequential logic and editorial loops.
Includes retry logic and failure monitoring for robust generation.
"""

from crewai import Crew, Process, Task, Agent
from typing import Optional, Dict, Any, List, Callable
import yaml
import os
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from functools import wraps

from agents import create_llm, load_genre_config
from agents_extended import (
    create_story_architect,
    create_character_designer,
    create_location_designer,
    create_item_cataloger,
    create_plot_architect,
    create_timeline_manager,
    create_scene_writer,
    create_dialogue_specialist,
    create_continuity_editor,
    create_style_editor,
    create_chapter_compiler,
    create_manuscript_reviewer,
    create_arc_architect,
    create_character_roster_manager,
    create_power_system_manager,
    create_cliffhanger_specialist,
    create_magic_system_designer,
    create_faction_manager,
    create_lore_keeper,
    create_combat_choreographer,
    create_theme_weaver,
    create_prose_stylist,
    create_psychological_depth_agent,
    ALL_AGENTS,
)
from tasks_extended import (
    # First pass - entity extraction
    create_entity_extraction_task,
    parse_entity_extraction,
    # Second pass - individual entity generation
    create_single_character_task,
    create_single_location_task,
    create_single_item_task,
    # Story architecture
    create_story_architecture_task,
    # Batch tasks (fallback)
    create_character_design_task,
    create_location_design_task,
    create_item_catalog_task,
    # Structure tasks
    create_magic_system_task,
    create_faction_management_task,
    create_lore_document_task,
    create_arc_design_task,
    create_plot_structure_task,
    create_timeline_task,
)
from config.project_types import (
    ProjectTypeConfig,
    get_project_type,
    PROJECT_TYPES,
)


class WorkflowPhase(Enum):
    """Workflow execution phases."""
    FOUNDATION = "foundation"
    WORLD_BUILDING = "world_building"
    STRUCTURE = "structure"
    WRITING = "writing"
    EDITORIAL = "editorial"
    FINAL_REVIEW = "final_review"


@dataclass
class TaskAttempt:
    """Record of a single task attempt."""
    attempt_number: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    output_length: int = 0


@dataclass
class TaskMonitor:
    """Monitor for tracking task execution with retries."""
    task_name: str
    max_retries: int = 3
    retry_delay: float = 2.0
    attempts: List[TaskAttempt] = field(default_factory=list)
    final_output: Optional[str] = None

    def record_attempt(self, success: bool, error: str = None, output: str = None):
        """Record an attempt result."""
        attempt = TaskAttempt(
            attempt_number=len(self.attempts) + 1,
            started_at=self.attempts[-1].started_at if self.attempts else datetime.now(),
            completed_at=datetime.now(),
            success=success,
            error=error,
            output_length=len(output) if output else 0
        )
        if self.attempts:
            self.attempts[-1] = attempt
        else:
            self.attempts.append(attempt)

        if success and output:
            self.final_output = output

    def start_attempt(self):
        """Start a new attempt."""
        self.attempts.append(TaskAttempt(
            attempt_number=len(self.attempts) + 1,
            started_at=datetime.now()
        ))

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)

    @property
    def succeeded(self) -> bool:
        return any(a.success for a in self.attempts)

    @property
    def last_error(self) -> Optional[str]:
        for attempt in reversed(self.attempts):
            if attempt.error:
                return attempt.error
        return None

    def get_summary(self) -> str:
        """Get a summary of all attempts."""
        lines = [f"Task: {self.task_name}"]
        lines.append(f"  Total attempts: {self.total_attempts}")
        lines.append(f"  Success: {self.succeeded}")
        if self.final_output:
            lines.append(f"  Output length: {len(self.final_output)} chars")
        for attempt in self.attempts:
            status = "✓" if attempt.success else "✗"
            lines.append(f"  Attempt {attempt.attempt_number}: {status}")
            if attempt.error:
                lines.append(f"    Error: {attempt.error[:100]}...")
        return "\n".join(lines)


@dataclass
class WorkflowResult:
    """Result from a workflow phase."""
    phase: WorkflowPhase
    success: bool
    outputs: Dict[str, Any]
    errors: List[str]
    task_monitors: Dict[str, TaskMonitor] = field(default_factory=dict)

    def get_failed_tasks(self) -> List[str]:
        """Get list of tasks that failed after all retries."""
        return [name for name, monitor in self.task_monitors.items()
                if not monitor.succeeded]

    def get_retry_summary(self) -> str:
        """Get summary of all task retries."""
        lines = []
        for name, monitor in self.task_monitors.items():
            if monitor.total_attempts > 1 or not monitor.succeeded:
                lines.append(monitor.get_summary())
        return "\n\n".join(lines) if lines else "All tasks succeeded on first attempt."


def with_retry(max_retries: int = 3, delay: float = 2.0, backoff: float = 1.5):
    """
    Decorator for retrying failed operations.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_retries + 1):
                try:
                    result = func(*args, **kwargs)

                    # Validate the result isn't empty or a failure message
                    if result:
                        result_str = str(result)
                        # Check for common failure patterns
                        failure_patterns = [
                            "Your final answer must be",
                            "I cannot",
                            "I'm unable to",
                            "Error:",
                            "Failed to",
                        ]
                        is_failure = any(p.lower() in result_str.lower()[:200]
                                        for p in failure_patterns)

                        # Check minimum length (at least 500 chars for real content)
                        is_too_short = len(result_str.strip()) < 500

                        if is_failure or is_too_short:
                            raise ValueError(
                                f"Output appears invalid (length={len(result_str)}, "
                                f"failure_pattern={is_failure})"
                            )

                    return result

                except Exception as e:
                    last_exception = e
                    error_msg = str(e)

                    # Log the retry
                    print(f"\n⚠️  Attempt {attempt}/{max_retries} failed: {error_msg[:100]}")

                    if attempt < max_retries:
                        print(f"   Retrying in {current_delay:.1f}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        print(f"❌ All {max_retries} attempts failed")

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


def validate_output(output: str, min_length: int = 500, task_type: str = "general") -> bool:
    """
    Validate that agent output is acceptable.

    Args:
        output: The output string to validate
        min_length: Minimum acceptable length
        task_type: Type of task for specialized validation

    Returns:
        True if valid, raises ValueError if invalid
    """
    if not output:
        raise ValueError("Output is empty")

    output_str = str(output).strip()

    # Check minimum length
    if len(output_str) < min_length:
        raise ValueError(
            f"Output too short: {len(output_str)} chars (min: {min_length})"
        )

    # Check for failure patterns
    failure_patterns = [
        "your final answer must be",
        "i cannot complete",
        "i'm unable to",
        "error:",
        "failed to generate",
        "insufficient context",
    ]

    lower_output = output_str.lower()[:500]
    for pattern in failure_patterns:
        if pattern in lower_output:
            raise ValueError(f"Output contains failure pattern: '{pattern}'")

    # Task-specific validation
    if task_type == "character":
        required_sections = ["name", "personality", "background"]
        for section in required_sections:
            if section.lower() not in lower_output:
                print(f"   Warning: Character output may be missing '{section}' section")

    elif task_type == "location":
        required_sections = ["description", "atmosphere"]
        for section in required_sections:
            if section.lower() not in lower_output:
                print(f"   Warning: Location output may be missing '{section}' section")

    return True


class StreamingCallback:
    """Callback handler for streaming CrewAI output."""

    def __init__(self, on_step: Optional[Callable[[str], None]] = None):
        self.on_step = on_step
        self.current_agent = None
        self.buffer = []

    def __call__(self, step_output):
        """Called on each step of agent execution."""
        if self.on_step:
            # Extract meaningful content from step output
            if hasattr(step_output, 'log'):
                self.on_step(step_output.log)
            elif hasattr(step_output, 'output'):
                self.on_step(str(step_output.output))
            elif isinstance(step_output, str):
                self.on_step(step_output)
            else:
                self.on_step(str(step_output))


class NovelWorkflow:
    """
    Orchestrates the complete novel writing workflow.
    Handles parallel/sequential execution, editorial loops, and phase management.
    """

    def __init__(
        self,
        config_path: str = "config.yaml",
        project_type: str = "standard",
        genre: Optional[str] = None,
        num_chapters: Optional[int] = None,
        yw7_file_path: Optional[str] = None,
    ):
        """
        Initialize the novel workflow.

        Args:
            config_path: Path to main configuration file
            project_type: Project type (standard, light_novel, literary, etc.)
            genre: Genre override
            num_chapters: Number of chapters override
            yw7_file_path: Optional path to yWriter7 project file
        """
        # Load configurations
        self.config = self._load_config(config_path)
        self.project_config = get_project_type(project_type)
        self.project_type = project_type

        # Apply overrides
        self.genre = genre or self.config['defaults'].get('genre', 'literary_fiction')
        self.num_chapters = num_chapters or self.project_config.scale.max_chapters

        # Load genre config
        self.genre_config = load_genre_config(
            self.genre,
            self.config['paths']['genres_dir']
        )

        # YWriter7 integration
        self.yw7_file_path = yw7_file_path
        self.knowledge_sources = []

        # Create LLMs
        self.llms = self._create_llms()

        # Create agents based on project type
        self.agents = self._create_agents()

        # Workflow state
        self.phase_results: Dict[WorkflowPhase, WorkflowResult] = {}
        self.task_outputs: Dict[str, Any] = {}

        # Callbacks
        self.on_phase_start: Optional[Callable[[WorkflowPhase], None]] = None
        self.on_phase_complete: Optional[Callable[[WorkflowResult], None]] = None
        self.on_task_complete: Optional[Callable[[str, Any], None]] = None
        self.on_stream: Optional[Callable[[str], None]] = None  # Streaming callback
        self._streaming_callback = None

    def _load_config(self, config_path: str) -> dict:
        """Load main configuration from YAML."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _create_llms(self) -> Dict[str, Any]:
        """Create LLM instances for all enabled agents."""
        ollama_config = self.config['ollama']
        llm_params = self.config['llm']

        base_url = ollama_config['base_url']
        default_model = ollama_config['default_model']
        model_overrides = ollama_config.get('models', {})

        llms = {}
        enabled_agents = self.project_config.get_enabled_agents()

        for agent_name in enabled_agents:
            model = model_overrides.get(agent_name, default_model)
            llms[agent_name] = create_llm(
                base_url=base_url,
                model=model,
                temperature=llm_params.get('temperature', 0.7),
                max_tokens=llm_params.get('max_tokens', 4000),
                top_p=llm_params.get('top_p', 0.9)
            )

        return llms

    def _create_agents(self) -> Dict[str, Agent]:
        """Create all enabled agents."""
        agents = {}
        enabled = self.project_config.get_enabled_agents()

        agent_creators = {
            "story_architect": create_story_architect,
            "character_designer": create_character_designer,
            "location_designer": create_location_designer,
            "item_cataloger": create_item_cataloger,
            "plot_architect": create_plot_architect,
            "timeline_manager": create_timeline_manager,
            "scene_writer": create_scene_writer,
            "dialogue_specialist": create_dialogue_specialist,
            "continuity_editor": create_continuity_editor,
            "style_editor": create_style_editor,
            "chapter_compiler": create_chapter_compiler,
            "manuscript_reviewer": create_manuscript_reviewer,
            "arc_architect": create_arc_architect,
            "character_roster_manager": create_character_roster_manager,
            "power_system_manager": create_power_system_manager,
            "cliffhanger_specialist": create_cliffhanger_specialist,
            "magic_system_designer": create_magic_system_designer,
            "faction_manager": create_faction_manager,
            "lore_keeper": create_lore_keeper,
            "combat_choreographer": create_combat_choreographer,
            "theme_weaver": create_theme_weaver,
            "prose_stylist": create_prose_stylist,
            "psychological_depth": create_psychological_depth_agent,
        }

        for agent_name in enabled:
            if agent_name in self.llms and agent_name in agent_creators:
                agents[agent_name] = agent_creators[agent_name](
                    self.llms[agent_name],
                    self.genre_config
                )

        return agents

    def _setup_knowledge_sources(self):
        """Set up knowledge sources including yWriter7 if available."""
        if self.yw7_file_path and os.path.exists(self.yw7_file_path):
            from knowledge import YWriter7KnowledgeSource

            yw7_knowledge = YWriter7KnowledgeSource(
                file_path=self.yw7_file_path,
                include_scene_content=False,  # Start without full content
                include_characters=True,
                include_locations=True,
                include_items=True,
                include_outlines=True,
            )
            self.knowledge_sources.append(yw7_knowledge)

    def _get_embedder_config(self) -> Dict[str, Any]:
        """Get embedder configuration for knowledge sources."""
        ollama_url = self.config['ollama']['base_url']

        return {
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text",  # Good embedding model for Ollama
                "url": f"{ollama_url}/api/embeddings"
            }
        }

    def _create_crew(
        self,
        agents: List[Agent],
        tasks: List[Task],
        process: Process = Process.sequential,
        memory: bool = False
    ) -> Crew:
        """Create a crew with streaming callback support."""
        # Set up streaming callback if configured
        step_callback = None
        if self.on_stream:
            self._streaming_callback = StreamingCallback(on_step=self.on_stream)
            step_callback = self._streaming_callback

        crew_kwargs = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": self.config['crew'].get('verbose', True),
        }

        # Add step callback for streaming
        if step_callback:
            crew_kwargs["step_callback"] = step_callback

        # Add memory if requested
        if memory:
            crew_kwargs["memory"] = True

        # Add knowledge sources if available
        if self.knowledge_sources:
            crew_kwargs["knowledge_sources"] = self.knowledge_sources
            crew_kwargs["embedder"] = self._get_embedder_config()

        return Crew(**crew_kwargs)

    # =========================================================================
    # PHASE 1: FOUNDATION
    # =========================================================================

    def run_foundation_phase(
        self,
        story_prompt: str,
        additional_instructions: str = ""
    ) -> WorkflowResult:
        """
        Run the foundation phase (story architecture).
        This phase must complete before others can start.
        """
        if self.on_phase_start:
            self.on_phase_start(WorkflowPhase.FOUNDATION)

        errors = []
        outputs = {}

        try:
            # Create story architecture task
            story_task = create_story_architecture_task(
                agent=self.agents['story_architect'],
                genre=self.genre,
                num_chapters=self.num_chapters,
                story_prompt=story_prompt,
                additional_instructions=additional_instructions,
                project_type=self.project_type
            )

            # Run the crew
            crew = self._create_crew(
                agents=[self.agents['story_architect']],
                tasks=[story_task],
                process=Process.sequential,
                memory=True
            )

            result = crew.kickoff()

            outputs['story_architecture'] = result.raw if hasattr(result, 'raw') else str(result)
            self.task_outputs['story_task'] = story_task

            if self.on_task_complete:
                self.on_task_complete('story_architecture', outputs['story_architecture'])

        except Exception as e:
            errors.append(f"Foundation phase error: {str(e)}")

        result = WorkflowResult(
            phase=WorkflowPhase.FOUNDATION,
            success=len(errors) == 0,
            outputs=outputs,
            errors=errors
        )

        self.phase_results[WorkflowPhase.FOUNDATION] = result

        if self.on_phase_complete:
            self.on_phase_complete(result)

        return result

    # =========================================================================
    # PHASE 2: WORLD BUILDING (Two-Pass Generation)
    # =========================================================================

    def run_world_building_phase(self) -> WorkflowResult:
        """
        Run the world building phase using TWO-PASS GENERATION:

        Pass 1: Entity Extraction
            - Analyze story architecture
            - Identify all characters, locations, items needed
            - Create a structured list for individual generation

        Pass 2: Individual Entity Generation
            - Generate each character with FULL context (3500+ words each)
            - Generate each location with FULL context (2500+ words each)
            - Generate each item with FULL context (1500+ words each)

        This approach gives each entity the full 30k+ context window,
        producing much richer, more detailed output that maps directly
        to yWriter7's per-entity database structure.
        """
        if WorkflowPhase.FOUNDATION not in self.phase_results:
            raise RuntimeError("Foundation phase must complete before world building")

        if self.on_phase_start:
            self.on_phase_start(WorkflowPhase.WORLD_BUILDING)

        errors = []
        outputs = {
            'characters': [],
            'locations': [],
            'items': [],
            'entity_list': None
        }

        story_task = self.task_outputs.get('story_task')

        # =====================================================================
        # PASS 1: ENTITY EXTRACTION
        # =====================================================================
        print("\n" + "="*60)
        print("PASS 1: ENTITY EXTRACTION")
        print("Identifying characters, locations, and items to create...")
        print("="*60 + "\n")

        entity_list = None
        try:
            # Run entity extraction task
            extraction_task = create_entity_extraction_task(
                agent=self.agents.get('story_architect', self.agents.get('character_designer')),
                story_task=story_task,
                project_type=self.project_type
            )

            crew = self._create_crew(
                agents=[self.agents.get('story_architect', self.agents.get('character_designer'))],
                tasks=[extraction_task],
                process=Process.sequential
            )

            result = crew.kickoff()
            extraction_output = result.raw if hasattr(result, 'raw') else str(result)

            # Parse the extraction
            entity_list = parse_entity_extraction(extraction_output)
            outputs['entity_list'] = entity_list

            print(f"\nExtracted entities:")
            print(f"  - Main Characters: {len(entity_list['main_characters'])}")
            print(f"  - Supporting Characters: {len(entity_list['supporting_characters'])}")
            print(f"  - Locations: {len(entity_list['locations'])}")
            print(f"  - Items: {len(entity_list['items'])}")

            if self.on_task_complete:
                self.on_task_complete('entity_extraction', extraction_output)

        except Exception as e:
            errors.append(f"Entity extraction error: {str(e)}")
            # Fall back to batch generation if extraction fails
            print(f"Entity extraction failed, falling back to batch mode: {e}")
            return self._run_world_building_batch_fallback(errors, outputs)

        if not entity_list:
            return self._run_world_building_batch_fallback(errors, outputs)

        # =====================================================================
        # PASS 2: INDIVIDUAL ENTITY GENERATION
        # =====================================================================
        print("\n" + "="*60)
        print("PASS 2: INDIVIDUAL ENTITY GENERATION")
        print("Generating each entity with full context window...")
        print("="*60 + "\n")

        # Generate MAIN CHARACTERS individually
        if 'character_designer' in self.agents and entity_list['main_characters']:
            print(f"\n--- Generating {len(entity_list['main_characters'])} Main Characters ---")
            created_chars = []

            for i, char_info in enumerate(entity_list['main_characters']):
                char_name = char_info['name']
                print(f"\n[{i+1}/{len(entity_list['main_characters'])}] Generating: {char_name}")

                try:
                    char_output = self._generate_single_character(
                        name=char_name,
                        role=char_info['role'],
                        description=char_info['description'],
                        is_main=True,
                        previous_characters=created_chars
                    )
                    outputs['characters'].append({
                        'name': char_name,
                        'role': char_info['role'],
                        'type': 'main',
                        'profile': char_output
                    })
                    created_chars.append(char_name)

                    if self.on_task_complete:
                        self.on_task_complete(f'character_{char_name}', char_output[:500] + "...")

                except Exception as e:
                    errors.append(f"Error generating character {char_name}: {str(e)}")
                    print(f"  ERROR: {e}")

        # Generate SUPPORTING CHARACTERS (limit to avoid excessive time)
        if 'character_designer' in self.agents and entity_list['supporting_characters']:
            # Limit supporting characters to reasonable number
            max_supporting = min(len(entity_list['supporting_characters']), 10)
            supporting_to_generate = entity_list['supporting_characters'][:max_supporting]

            print(f"\n--- Generating {len(supporting_to_generate)} Supporting Characters ---")
            created_chars = [c['name'] for c in outputs['characters']]

            for i, char_info in enumerate(supporting_to_generate):
                char_name = char_info['name']
                print(f"\n[{i+1}/{len(supporting_to_generate)}] Generating: {char_name}")

                try:
                    char_output = self._generate_single_character(
                        name=char_name,
                        role=char_info['role'],
                        description=char_info['description'],
                        is_main=False,
                        previous_characters=created_chars
                    )
                    outputs['characters'].append({
                        'name': char_name,
                        'role': char_info['role'],
                        'type': 'supporting',
                        'profile': char_output
                    })
                    created_chars.append(char_name)

                except Exception as e:
                    errors.append(f"Error generating character {char_name}: {str(e)}")

        # Generate LOCATIONS individually
        if 'location_designer' in self.agents and entity_list['locations']:
            print(f"\n--- Generating {len(entity_list['locations'])} Locations ---")
            created_locs = []

            for i, loc_info in enumerate(entity_list['locations']):
                loc_name = loc_info['name']
                print(f"\n[{i+1}/{len(entity_list['locations'])}] Generating: {loc_name}")

                try:
                    loc_output = self._generate_single_location(
                        name=loc_name,
                        loc_type=loc_info['type'],
                        description=loc_info['description'],
                        previous_locations=created_locs
                    )
                    outputs['locations'].append({
                        'name': loc_name,
                        'type': loc_info['type'],
                        'profile': loc_output
                    })
                    created_locs.append(loc_name)

                    if self.on_task_complete:
                        self.on_task_complete(f'location_{loc_name}', loc_output[:500] + "...")

                except Exception as e:
                    errors.append(f"Error generating location {loc_name}: {str(e)}")
                    print(f"  ERROR: {e}")

        # Generate ITEMS individually
        if 'item_cataloger' in self.agents and entity_list['items']:
            # Limit items to reasonable number
            max_items = min(len(entity_list['items']), 15)
            items_to_generate = entity_list['items'][:max_items]

            print(f"\n--- Generating {len(items_to_generate)} Items ---")
            created_items = []

            for i, item_info in enumerate(items_to_generate):
                item_name = item_info['name']
                print(f"\n[{i+1}/{len(items_to_generate)}] Generating: {item_name}")

                try:
                    item_output = self._generate_single_item(
                        name=item_name,
                        category=item_info['category'],
                        description=item_info['description'],
                        owner=item_info.get('owner', 'Unknown'),
                        previous_items=created_items
                    )
                    outputs['items'].append({
                        'name': item_name,
                        'category': item_info['category'],
                        'owner': item_info.get('owner', 'Unknown'),
                        'profile': item_output
                    })
                    created_items.append(item_name)

                    if self.on_task_complete:
                        self.on_task_complete(f'item_{item_name}', item_output[:500] + "...")

                except Exception as e:
                    errors.append(f"Error generating item {item_name}: {str(e)}")
                    print(f"  ERROR: {e}")

        # Run fantasy-specific tasks if enabled
        if self.project_config.fantasy.magic_system and 'magic_system_designer' in self.agents:
            try:
                magic_result = self._run_magic_system_design()
                outputs['magic_system'] = magic_result
            except Exception as e:
                errors.append(f"Magic system design error: {str(e)}")

        if self.project_config.fantasy.factions and 'faction_manager' in self.agents:
            try:
                faction_result = self._run_faction_design()
                outputs['factions'] = faction_result
            except Exception as e:
                errors.append(f"Faction design error: {str(e)}")

        if self.project_config.fantasy.deep_lore and 'lore_keeper' in self.agents:
            try:
                lore_result = self._run_lore_design()
                outputs['lore'] = lore_result
            except Exception as e:
                errors.append(f"Lore design error: {str(e)}")

        # Summary
        print("\n" + "="*60)
        print("WORLD BUILDING COMPLETE")
        print("="*60)

        # Calculate success stats
        total_chars = len(entity_list.get('main_characters', [])) + len(entity_list.get('supporting_characters', [])[:10])
        total_locs = len(entity_list.get('locations', []))
        total_items = len(entity_list.get('items', [])[:15])

        successful_chars = len(outputs['characters'])
        successful_locs = len(outputs['locations'])
        successful_items = len(outputs['items'])

        print(f"\n  Characters: {successful_chars}/{total_chars} generated")
        print(f"  Locations:  {successful_locs}/{total_locs} generated")
        print(f"  Items:      {successful_items}/{total_items} generated")

        # Show any failures
        if errors:
            print(f"\n  ⚠️  {len(errors)} errors occurred:")
            for err in errors[:5]:  # Show first 5 errors
                print(f"    - {err[:80]}")
            if len(errors) > 5:
                print(f"    ... and {len(errors) - 5} more")

        # Overall success rate
        total = total_chars + total_locs + total_items
        successful = successful_chars + successful_locs + successful_items
        if total > 0:
            success_rate = (successful / total) * 100
            print(f"\n  Overall success rate: {success_rate:.1f}%")

        print("="*60 + "\n")

        # Determine overall success (allow partial success if > 50%)
        partial_success = total > 0 and (successful / total) >= 0.5

        result = WorkflowResult(
            phase=WorkflowPhase.WORLD_BUILDING,
            success=len(errors) == 0 or partial_success,
            outputs=outputs,
            errors=errors
        )

        self.phase_results[WorkflowPhase.WORLD_BUILDING] = result

        if self.on_phase_complete:
            self.on_phase_complete(result)

        return result

    def _generate_single_character(
        self,
        name: str,
        role: str,
        description: str,
        is_main: bool = True,
        previous_characters: List[str] = None,
        max_retries: int = 3
    ) -> str:
        """Generate a single character with full context and retry logic."""
        story_task = self.task_outputs.get('story_task')
        min_length = 2000 if is_main else 1000

        for attempt in range(1, max_retries + 1):
            try:
                print(f"   Attempt {attempt}/{max_retries}...")

                char_task = create_single_character_task(
                    agent=self.agents['character_designer'],
                    story_task=story_task,
                    character_name=name,
                    character_role=role,
                    character_brief=description,
                    is_main=is_main,
                    previous_characters=previous_characters
                )

                crew = self._create_crew(
                    agents=[self.agents['character_designer']],
                    tasks=[char_task],
                    process=Process.sequential
                )

                result = crew.kickoff()
                output = result.raw if hasattr(result, 'raw') else str(result)

                # Validate output
                validate_output(output, min_length=min_length, task_type="character")
                print(f"   ✓ Success: {len(output)} chars")
                return output

            except Exception as e:
                error_msg = str(e)
                print(f"   ✗ Failed: {error_msg[:80]}")

                if attempt < max_retries:
                    delay = 2.0 * (1.5 ** (attempt - 1))
                    print(f"   Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    print(f"   ❌ All {max_retries} attempts failed for {name}")
                    raise

        raise RuntimeError(f"Failed to generate character {name} after {max_retries} attempts")

    def _generate_single_location(
        self,
        name: str,
        loc_type: str,
        description: str,
        previous_locations: List[str] = None,
        max_retries: int = 3
    ) -> str:
        """Generate a single location with full context and retry logic."""
        story_task = self.task_outputs.get('story_task')
        min_length = 1500

        for attempt in range(1, max_retries + 1):
            try:
                print(f"   Attempt {attempt}/{max_retries}...")

                loc_task = create_single_location_task(
                    agent=self.agents['location_designer'],
                    story_task=story_task,
                    location_name=name,
                    location_type=loc_type,
                    location_brief=description,
                    previous_locations=previous_locations
                )

                crew = self._create_crew(
                    agents=[self.agents['location_designer']],
                    tasks=[loc_task],
                    process=Process.sequential
                )

                result = crew.kickoff()
                output = result.raw if hasattr(result, 'raw') else str(result)

                # Validate output
                validate_output(output, min_length=min_length, task_type="location")
                print(f"   ✓ Success: {len(output)} chars")
                return output

            except Exception as e:
                error_msg = str(e)
                print(f"   ✗ Failed: {error_msg[:80]}")

                if attempt < max_retries:
                    delay = 2.0 * (1.5 ** (attempt - 1))
                    print(f"   Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    print(f"   ❌ All {max_retries} attempts failed for {name}")
                    raise

        raise RuntimeError(f"Failed to generate location {name} after {max_retries} attempts")

    def _generate_single_item(
        self,
        name: str,
        category: str,
        description: str,
        owner: str = "Unknown",
        previous_items: List[str] = None,
        max_retries: int = 3
    ) -> str:
        """Generate a single item with full context and retry logic."""
        story_task = self.task_outputs.get('story_task')
        min_length = 800

        for attempt in range(1, max_retries + 1):
            try:
                print(f"   Attempt {attempt}/{max_retries}...")

                item_task = create_single_item_task(
                    agent=self.agents['item_cataloger'],
                    story_task=story_task,
                    item_name=name,
                    item_category=category,
                    item_brief=description,
                    owner=owner,
                    previous_items=previous_items
                )

                crew = self._create_crew(
                    agents=[self.agents['item_cataloger']],
                    tasks=[item_task],
                    process=Process.sequential
                )

                result = crew.kickoff()
                output = result.raw if hasattr(result, 'raw') else str(result)

                # Validate output
                validate_output(output, min_length=min_length, task_type="item")
                print(f"   ✓ Success: {len(output)} chars")
                return output

            except Exception as e:
                error_msg = str(e)
                print(f"   ✗ Failed: {error_msg[:80]}")

                if attempt < max_retries:
                    delay = 2.0 * (1.5 ** (attempt - 1))
                    print(f"   Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    print(f"   ❌ All {max_retries} attempts failed for {name}")
                    raise

        raise RuntimeError(f"Failed to generate item {name} after {max_retries} attempts")

    def _run_world_building_batch_fallback(
        self,
        errors: List[str],
        outputs: Dict[str, Any]
    ) -> WorkflowResult:
        """Fallback to batch generation if entity extraction fails."""
        print("\n--- Falling back to batch world building ---")

        story_task = self.task_outputs.get('story_task')

        # Character Designer (batch)
        if 'character_designer' in self.agents:
            try:
                char_task = create_character_design_task(
                    agent=self.agents['character_designer'],
                    story_task=story_task,
                    num_main_characters=self.project_config.scale.max_characters_main,
                    num_supporting=self.project_config.scale.max_characters_supporting,
                    project_type=self.project_type
                )
                crew = self._create_crew(
                    agents=[self.agents['character_designer']],
                    tasks=[char_task],
                    process=Process.sequential
                )
                result = crew.kickoff()
                outputs['characters_batch'] = result.raw if hasattr(result, 'raw') else str(result)
                self.task_outputs['character_task'] = char_task
            except Exception as e:
                errors.append(f"Character batch error: {str(e)}")

        # Location Designer (batch)
        if 'location_designer' in self.agents:
            try:
                loc_task = create_location_design_task(
                    agent=self.agents['location_designer'],
                    story_task=story_task,
                    num_locations=6
                )
                crew = self._create_crew(
                    agents=[self.agents['location_designer']],
                    tasks=[loc_task],
                    process=Process.sequential
                )
                result = crew.kickoff()
                outputs['locations_batch'] = result.raw if hasattr(result, 'raw') else str(result)
                self.task_outputs['location_task'] = loc_task
            except Exception as e:
                errors.append(f"Location batch error: {str(e)}")

        # Item Cataloger (batch)
        if 'item_cataloger' in self.agents and self.task_outputs.get('character_task'):
            try:
                item_task = create_item_catalog_task(
                    agent=self.agents['item_cataloger'],
                    story_task=story_task,
                    character_task=self.task_outputs['character_task']
                )
                crew = self._create_crew(
                    agents=[self.agents['item_cataloger']],
                    tasks=[item_task],
                    process=Process.sequential
                )
                result = crew.kickoff()
                outputs['items_batch'] = result.raw if hasattr(result, 'raw') else str(result)
            except Exception as e:
                errors.append(f"Item batch error: {str(e)}")

        result = WorkflowResult(
            phase=WorkflowPhase.WORLD_BUILDING,
            success=len(errors) == 0,
            outputs=outputs,
            errors=errors
        )

        self.phase_results[WorkflowPhase.WORLD_BUILDING] = result

        if self.on_phase_complete:
            self.on_phase_complete(result)

        return result

    def _run_magic_system_design(self) -> str:
        """Run magic system design subtask."""
        magic_task = create_magic_system_task(
            agent=self.agents['magic_system_designer'],
            story_task=self.task_outputs['story_task'],
            hardness=self.project_config.fantasy.magic_hardness
        )

        crew = self._create_crew(
            agents=[self.agents['magic_system_designer']],
            tasks=[magic_task],
            process=Process.sequential
        )

        result = crew.kickoff()
        self.task_outputs['magic_task'] = magic_task
        return result.raw if hasattr(result, 'raw') else str(result)

    def _run_faction_design(self) -> str:
        """Run faction design subtask."""
        faction_task = create_faction_management_task(
            agent=self.agents['faction_manager'],
            story_task=self.task_outputs['story_task'],
            character_task=self.task_outputs['character_task']
        )

        crew = self._create_crew(
            agents=[self.agents['faction_manager']],
            tasks=[faction_task],
            process=Process.sequential
        )

        result = crew.kickoff()
        self.task_outputs['faction_task'] = faction_task
        return result.raw if hasattr(result, 'raw') else str(result)

    def _run_lore_design(self) -> str:
        """Run lore design subtask."""
        lore_task = create_lore_document_task(
            agent=self.agents['lore_keeper'],
            story_task=self.task_outputs['story_task'],
            location_task=self.task_outputs['location_task']
        )

        crew = self._create_crew(
            agents=[self.agents['lore_keeper']],
            tasks=[lore_task],
            process=Process.sequential
        )

        result = crew.kickoff()
        self.task_outputs['lore_task'] = lore_task
        return result.raw if hasattr(result, 'raw') else str(result)

    # =========================================================================
    # PHASE 3: STRUCTURE
    # =========================================================================

    def run_structure_phase(self) -> WorkflowResult:
        """
        Run the structure phase (plot architecture and timeline).
        """
        if WorkflowPhase.WORLD_BUILDING not in self.phase_results:
            raise RuntimeError("World building phase must complete before structure")

        if self.on_phase_start:
            self.on_phase_start(WorkflowPhase.STRUCTURE)

        errors = []
        outputs = {}

        try:
            # For light novels, run arc design first
            if self.project_config.structure.use_arcs and 'arc_architect' in self.agents:
                arc_outputs = self._run_arc_design()
                outputs['arcs'] = arc_outputs

            # Plot architecture
            plot_task = create_plot_structure_task(
                agent=self.agents['plot_architect'],
                story_task=self.task_outputs['story_task'],
                character_task=self.task_outputs['character_task'],
                location_task=self.task_outputs['location_task'],
                num_chapters=self.num_chapters
            )

            crew = self._create_crew(
                agents=[self.agents['plot_architect']],
                tasks=[plot_task],
                process=Process.sequential,
                memory=True
            )

            result = crew.kickoff()
            outputs['plot_structure'] = result.raw if hasattr(result, 'raw') else str(result)
            self.task_outputs['plot_task'] = plot_task

            if self.on_task_complete:
                self.on_task_complete('plot_structure', outputs['plot_structure'])

            # Timeline management
            if 'timeline_manager' in self.agents:
                timeline_task = create_timeline_task(
                    agent=self.agents['timeline_manager'],
                    plot_task=plot_task
                )

                crew = self._create_crew(
                    agents=[self.agents['timeline_manager']],
                    tasks=[timeline_task],
                    process=Process.sequential
                )

                timeline_result = crew.kickoff()
                outputs['timeline'] = timeline_result.raw if hasattr(timeline_result, 'raw') else str(timeline_result)
                self.task_outputs['timeline_task'] = timeline_task

                if self.on_task_complete:
                    self.on_task_complete('timeline', outputs['timeline'])

        except Exception as e:
            errors.append(f"Structure phase error: {str(e)}")

        result = WorkflowResult(
            phase=WorkflowPhase.STRUCTURE,
            success=len(errors) == 0,
            outputs=outputs,
            errors=errors
        )

        self.phase_results[WorkflowPhase.STRUCTURE] = result

        if self.on_phase_complete:
            self.on_phase_complete(result)

        return result

    def _run_arc_design(self) -> List[str]:
        """Run arc design for light novels."""
        arc_outputs = []
        num_arcs = min(
            self.project_config.structure.max_arcs,
            (self.num_chapters // self.project_config.structure.chapters_per_arc) + 1
        )

        previous_arc_task = None
        for arc_num in range(1, num_arcs + 1):
            arc_task = create_arc_design_task(
                agent=self.agents['arc_architect'],
                story_task=self.task_outputs['story_task'],
                arc_number=arc_num,
                chapters_in_arc=self.project_config.structure.chapters_per_arc,
                previous_arc_task=previous_arc_task
            )

            crew = self._create_crew(
                agents=[self.agents['arc_architect']],
                tasks=[arc_task],
                process=Process.sequential
            )

            result = crew.kickoff()
            arc_output = result.raw if hasattr(result, 'raw') else str(result)
            arc_outputs.append(arc_output)
            previous_arc_task = arc_task

            self.task_outputs[f'arc_{arc_num}_task'] = arc_task

            if self.on_task_complete:
                self.on_task_complete(f'arc_{arc_num}', arc_output)

        return arc_outputs

    # =========================================================================
    # PLANNING WORKFLOW (Combines Foundation, World Building, Structure)
    # =========================================================================

    def run_planning_workflow(
        self,
        story_prompt: str,
        additional_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        Run the complete planning workflow (no writing).
        Returns all planning outputs.
        """
        self._setup_knowledge_sources()

        results = {}

        # Phase 1: Foundation
        foundation = self.run_foundation_phase(story_prompt, additional_instructions)
        results['foundation'] = foundation.outputs
        if not foundation.success:
            results['errors'] = foundation.errors
            return results

        # Phase 2: World Building
        world_building = self.run_world_building_phase()
        results['world_building'] = world_building.outputs
        if not world_building.success:
            results['errors'] = world_building.errors
            return results

        # Phase 3: Structure
        structure = self.run_structure_phase()
        results['structure'] = structure.outputs
        if not structure.success:
            results['errors'] = structure.errors

        return results

    # =========================================================================
    # FULL WORKFLOW
    # =========================================================================

    def run_full_workflow(
        self,
        story_prompt: str,
        additional_instructions: str = "",
        write_chapters: bool = True,
        editorial_loops: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete novel writing workflow.

        Args:
            story_prompt: The story premise
            additional_instructions: Additional guidance
            write_chapters: Whether to write full chapters
            editorial_loops: Whether to run editorial review loops

        Returns:
            Complete workflow results
        """
        # Run planning phases
        results = self.run_planning_workflow(story_prompt, additional_instructions)

        if 'errors' in results and results['errors']:
            return results

        if write_chapters:
            # Phase 4: Writing
            writing = self.run_writing_phase()
            results['writing'] = writing.outputs
            if not writing.success:
                results['errors'] = writing.errors
                return results

            # Phase 5: Editorial (with loops if enabled)
            if editorial_loops and self.project_config.editorial_loops:
                editorial = self.run_editorial_phase()
                results['editorial'] = editorial.outputs

            # Phase 6: Final Review
            final = self.run_final_review_phase()
            results['final_review'] = final.outputs

        return results

    def run_writing_phase(self) -> WorkflowResult:
        """Run the writing phase - writes all chapters."""
        if self.on_phase_start:
            self.on_phase_start(WorkflowPhase.WRITING)

        errors = []
        outputs = {'chapters': []}

        # This would iterate through chapters and scenes
        # Simplified for now - full implementation would parse plot structure
        # and write each scene with proper context

        # Placeholder for chapter writing loop
        outputs['status'] = "Writing phase structure defined - implementation pending"

        result = WorkflowResult(
            phase=WorkflowPhase.WRITING,
            success=len(errors) == 0,
            outputs=outputs,
            errors=errors
        )

        self.phase_results[WorkflowPhase.WRITING] = result

        if self.on_phase_complete:
            self.on_phase_complete(result)

        return result

    def run_editorial_phase(self) -> WorkflowResult:
        """Run editorial review phase."""
        if self.on_phase_start:
            self.on_phase_start(WorkflowPhase.EDITORIAL)

        errors = []
        outputs = {}

        # Editorial loops would go here
        outputs['status'] = "Editorial phase structure defined - implementation pending"

        result = WorkflowResult(
            phase=WorkflowPhase.EDITORIAL,
            success=len(errors) == 0,
            outputs=outputs,
            errors=errors
        )

        self.phase_results[WorkflowPhase.EDITORIAL] = result

        if self.on_phase_complete:
            self.on_phase_complete(result)

        return result

    def run_final_review_phase(self) -> WorkflowResult:
        """Run final manuscript review."""
        if self.on_phase_start:
            self.on_phase_start(WorkflowPhase.FINAL_REVIEW)

        errors = []
        outputs = {}

        outputs['status'] = "Final review structure defined - implementation pending"

        result = WorkflowResult(
            phase=WorkflowPhase.FINAL_REVIEW,
            success=len(errors) == 0,
            outputs=outputs,
            errors=errors
        )

        self.phase_results[WorkflowPhase.FINAL_REVIEW] = result

        if self.on_phase_complete:
            self.on_phase_complete(result)

        return result

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_phase_status(self) -> Dict[str, str]:
        """Get status of all phases."""
        return {
            phase.value: "complete" if phase in self.phase_results else "pending"
            for phase in WorkflowPhase
        }

    def get_enabled_agents_list(self) -> List[str]:
        """Get list of enabled agents for this workflow."""
        return list(self.agents.keys())

    def save_results(self, output_path: str):
        """Save workflow results to file."""
        import json

        results = {
            'project_type': self.project_type,
            'genre': self.genre,
            'num_chapters': self.num_chapters,
            'phases': {}
        }

        for phase, result in self.phase_results.items():
            results['phases'][phase.value] = {
                'success': result.success,
                'outputs': result.outputs,
                'errors': result.errors
            }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point for the workflow."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Book Writer - Novel Workflow")
    parser.add_argument('--project-type', default='standard',
                        choices=list(PROJECT_TYPES.keys()),
                        help='Project type')
    parser.add_argument('--genre', default='literary_fiction', help='Genre')
    parser.add_argument('--chapters', type=int, default=None, help='Number of chapters')
    parser.add_argument('--prompt', required=True, help='Story prompt')
    parser.add_argument('--instructions', default='', help='Additional instructions')
    parser.add_argument('--output', default='output/workflow_result.json', help='Output file')
    parser.add_argument('--planning-only', action='store_true', help='Run planning only')
    parser.add_argument('--yw7-file', default=None, help='yWriter7 project file')

    args = parser.parse_args()

    print(f"Starting AI Book Writer Workflow...")
    print(f"Project Type: {args.project_type}")
    print(f"Genre: {args.genre}")
    print(f"Prompt: {args.prompt[:100]}...")
    print("-" * 50)

    # Create workflow
    workflow = NovelWorkflow(
        project_type=args.project_type,
        genre=args.genre,
        num_chapters=args.chapters,
        yw7_file_path=args.yw7_file
    )

    # Set up progress callbacks
    def on_phase_start(phase):
        print(f"\n{'='*50}")
        print(f"Starting Phase: {phase.value.upper()}")
        print(f"{'='*50}")

    def on_phase_complete(result):
        status = "SUCCESS" if result.success else "FAILED"
        print(f"\nPhase {result.phase.value}: {status}")
        if result.errors:
            for error in result.errors:
                print(f"  ERROR: {error}")

    def on_task_complete(task_name, output):
        print(f"  Completed: {task_name}")

    workflow.on_phase_start = on_phase_start
    workflow.on_phase_complete = on_phase_complete
    workflow.on_task_complete = on_task_complete

    # Run workflow
    if args.planning_only:
        results = workflow.run_planning_workflow(
            story_prompt=args.prompt,
            additional_instructions=args.instructions
        )
    else:
        results = workflow.run_full_workflow(
            story_prompt=args.prompt,
            additional_instructions=args.instructions
        )

    # Save results
    workflow.save_results(args.output)
    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
