"""
AiBookWriter4 - Streamlit UI
Extended web interface for the AI book writing system with streaming output.
"""

import streamlit as st
import yaml
import os
import json
import threading
import queue
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="AI Book Writer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
    }
    .agent-card {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }
    .phase-header {
        background-color: #262730;
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        margin: 8px 0;
    }
    .streaming-output {
        background-color: #0e1117;
        color: #00ff00;
        font-family: monospace;
        padding: 16px;
        border-radius: 8px;
        max-height: 400px;
        overflow-y: auto;
        font-size: 12px;
        white-space: pre-wrap;
    }
    .agent-status {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin: 2px;
    }
    .agent-active {
        background-color: #28a745;
        color: white;
    }
    .agent-pending {
        background-color: #6c757d;
        color: white;
    }
    .agent-complete {
        background-color: #007bff;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def load_config() -> dict:
    """Load configuration from YAML file."""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.error("config.yaml not found!")
        return None


def get_available_genres() -> List[str]:
    """Get list of available genre configurations."""
    genres_dir = "config/genres"
    if not os.path.exists(genres_dir):
        return ["literary_fiction"]

    return sorted([
        f[:-3] for f in os.listdir(genres_dir)
        if f.endswith('.py') and not f.startswith('_')
    ])


def get_ollama_models(base_url: str) -> List[str]:
    """Fetch available models from Ollama server."""
    try:
        import urllib.request
        url = f"{base_url}/api/tags"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return [m['name'] for m in data.get('models', [])]
    except Exception:
        return []


def get_project_types() -> Dict[str, Dict[str, Any]]:
    """Get available project types with descriptions."""
    try:
        from config.project_types import PROJECT_TYPES
        return {
            name: {
                'name': config.name,
                'description': config.description,
                'max_chapters': config.scale.max_chapters,
                'max_main_chars': config.scale.max_characters_main,
                'use_arcs': config.structure.use_arcs,
                'agents': config.get_enabled_agents()
            }
            for name, config in PROJECT_TYPES.items()
        }
    except ImportError:
        return {
            'standard': {
                'name': 'Standard Novel',
                'description': 'Traditional 3-act structure',
                'max_chapters': 40,
                'max_main_chars': 5,
                'use_arcs': False,
                'agents': []
            }
        }


class OutputCapture:
    """Capture stdout/stderr and send to queue."""

    def __init__(self, output_queue: queue.Queue, stream_type: str = 'stdout'):
        self.output_queue = output_queue
        self.stream_type = stream_type
        self.buffer = ""
        self.encoding = 'utf-8'

    def write(self, text):
        if text and text.strip():
            self.output_queue.put({
                'type': 'stream',
                'message': text.rstrip(),
                'stream': self.stream_type
            })

    def flush(self):
        pass

    def isatty(self):
        return False

    def fileno(self):
        return -1

    def readable(self):
        return False

    def writable(self):
        return True

    def seekable(self):
        return False


class StreamingWorkflowRunner:
    """Wrapper to run workflow with streaming output capture."""

    def __init__(self, output_queue: queue.Queue):
        self.output_queue = output_queue
        self.results = None
        self.error = None
        self.current_phase = None
        self.current_agent = None

    def stream_callback(self, message: str):
        """Callback for streaming output."""
        self.output_queue.put({
            'type': 'stream',
            'message': message,
            'phase': self.current_phase,
            'agent': self.current_agent
        })

    def phase_callback(self, phase_name: str):
        """Callback for phase changes."""
        self.current_phase = phase_name
        self.output_queue.put({
            'type': 'phase',
            'phase': phase_name
        })

    def task_callback(self, task_name: str, output: str):
        """Callback for task completion."""
        self.output_queue.put({
            'type': 'task_complete',
            'task': task_name,
            'output': output[:500] + "..." if len(output) > 500 else output
        })

    def run(
        self,
        project_type: str,
        genre: str,
        num_chapters: int,
        story_prompt: str,
        additional_instructions: str,
        write_chapters: bool = False,
        max_chapters_to_write: int = 3
    ):
        """Run the workflow in a thread with stdout capture."""
        import sys

        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = OutputCapture(self.output_queue, 'stdout')
        sys.stderr = OutputCapture(self.output_queue, 'stderr')

        try:
            from workflow import NovelWorkflow

            # Create workflow
            workflow = NovelWorkflow(
                project_type=project_type,
                genre=genre,
                num_chapters=num_chapters
            )

            # Set up callbacks
            workflow.on_phase_start = lambda p: self.phase_callback(p.value)
            workflow.on_task_complete = self.task_callback
            workflow.on_stream = self.stream_callback

            # Run planning workflow
            self.results = workflow.run_planning_workflow(
                story_prompt=story_prompt,
                additional_instructions=additional_instructions
            )

            # Run chapter writing if requested
            if write_chapters and 'errors' not in self.results:
                self.output_queue.put({
                    'type': 'phase',
                    'phase': 'writing'
                })
                writing_result = workflow.run_writing_phase(
                    max_chapters=max_chapters_to_write
                )
                self.results['writing'] = writing_result.outputs
                if writing_result.errors:
                    self.results['writing_errors'] = writing_result.errors

                # Add export methods results
                self.results['chapters_markdown'] = workflow.export_chapters_markdown()
                self.results['full_manuscript'] = workflow.export_full_manuscript()
                self.results['ywriter_xml'] = workflow.export_to_ywriter()

            self.output_queue.put({'type': 'complete', 'results': self.results})

        except Exception as e:
            self.error = str(e)
            self.output_queue.put({'type': 'error', 'error': str(e)})

        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def run_planning_workflow_streaming(
    project_type: str,
    genre: str,
    num_chapters: int,
    story_prompt: str,
    additional_instructions: str,
    output_container,
    status_container,
    write_chapters: bool = False,
    max_chapters_to_write: int = 3
) -> Optional[Dict[str, Any]]:
    """Run the planning workflow with streaming output display."""

    output_queue = queue.Queue()
    runner = StreamingWorkflowRunner(output_queue)

    # Start workflow in background thread
    workflow_thread = threading.Thread(
        target=runner.run,
        args=(project_type, genre, num_chapters, story_prompt, additional_instructions,
              write_chapters, max_chapters_to_write)
    )
    workflow_thread.start()

    # Display streaming output
    output_lines = []
    current_phase = "Initializing..."
    last_update = time.time()

    while workflow_thread.is_alive() or not output_queue.empty():
        try:
            msg = output_queue.get(timeout=0.1)

            if msg['type'] == 'phase':
                current_phase = msg['phase'].replace('_', ' ').title()
                status_container.info(f"🔄 Phase: {current_phase}")
                output_lines.append(f"\n{'='*50}")
                output_lines.append(f"  PHASE: {current_phase.upper()}")
                output_lines.append(f"{'='*50}\n")

            elif msg['type'] == 'stream':
                # Add to output buffer
                line = msg['message']
                if line and line.strip():
                    # Clean up ANSI codes and format
                    clean_line = line.replace('\x1b[', '[ESC[')
                    output_lines.append(clean_line)
                    # Keep last 200 lines
                    if len(output_lines) > 200:
                        output_lines = output_lines[-200:]
                    # Update display (throttle to avoid flickering)
                    if time.time() - last_update > 0.2:
                        display_text = '\n'.join(output_lines[-50:])  # Show last 50 lines
                        output_container.code(display_text, language=None)
                        last_update = time.time()

            elif msg['type'] == 'task_complete':
                output_lines.append(f"\n✅ Completed: {msg['task']}\n")
                display_text = '\n'.join(output_lines[-50:])
                output_container.code(display_text, language=None)

            elif msg['type'] == 'complete':
                status_container.success("✅ Workflow complete!")
                return msg['results']

            elif msg['type'] == 'error':
                status_container.error(f"❌ Error: {msg['error']}")
                return None

        except queue.Empty:
            continue

    workflow_thread.join()
    return runner.results


def run_planning_workflow(
    project_type: str,
    genre: str,
    num_chapters: int,
    story_prompt: str,
    additional_instructions: str,
    progress_callback=None
) -> Dict[str, Any]:
    """Run the planning workflow (non-streaming version)."""
    try:
        from workflow import NovelWorkflow

        workflow = NovelWorkflow(
            project_type=project_type,
            genre=genre,
            num_chapters=num_chapters
        )

        if progress_callback:
            workflow.on_phase_start = lambda p: progress_callback(f"Starting {p.value}...")
            workflow.on_task_complete = lambda t, o: progress_callback(f"Completed: {t}")

        results = workflow.run_planning_workflow(
            story_prompt=story_prompt,
            additional_instructions=additional_instructions
        )

        return results

    except ImportError as e:
        st.error(f"Import error: {e}\n\nMake sure all dependencies are installed.")
        return None
    except Exception as e:
        st.error(f"Error running workflow: {e}")
        return None


def run_legacy_workflow(genre, num_chapters, story_prompt, additional_instructions):
    """Run the original/legacy workflow for compatibility."""
    try:
        from crew import BookWritingCrew

        crew = BookWritingCrew(
            genre=genre,
            num_chapters=num_chapters
        )

        results = crew.run_planning_workflow(
            story_prompt=story_prompt,
            additional_instructions=additional_instructions
        )

        return results

    except Exception as e:
        st.error(f"Error running legacy workflow: {e}")
        return None


def display_agent_list(agents: List[str], columns: int = 3):
    """Display agents in a grid."""
    agent_icons = {
        'story_architect': '📐',
        'character_designer': '👤',
        'location_designer': '🏰',
        'item_cataloger': '🗡️',
        'plot_architect': '📊',
        'timeline_manager': '⏰',
        'scene_writer': '✍️',
        'dialogue_specialist': '💬',
        'continuity_editor': '🔍',
        'style_editor': '🎨',
        'chapter_compiler': '📖',
        'manuscript_reviewer': '📋',
        'arc_architect': '🌀',
        'character_roster_manager': '👥',
        'power_system_manager': '⚡',
        'cliffhanger_specialist': '😱',
        'magic_system_designer': '✨',
        'faction_manager': '⚔️',
        'lore_keeper': '📜',
        'combat_choreographer': '🥊',
        'theme_weaver': '🎭',
        'prose_stylist': '🖋️',
        'psychological_depth': '🧠',
    }

    cols = st.columns(columns)
    for i, agent in enumerate(agents):
        icon = agent_icons.get(agent, '🤖')
        display_name = agent.replace('_', ' ').title()
        cols[i % columns].markdown(f"{icon} {display_name}")


def main():
    st.title("📚 AI Book Writer")
    st.markdown("*Powered by CrewAI, Ollama, and yWriter7*")

    # Load config
    config = load_config()
    if not config:
        return

    # Get project types
    project_types = get_project_types()

    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Ollama status
        ollama_url = config['ollama']['base_url']
        models = get_ollama_models(ollama_url)

        if models:
            st.success(f"✅ Ollama connected ({len(models)} models)")
        else:
            st.error(f"❌ Ollama not reachable at {ollama_url}")

        st.divider()

        # Project Type Selection
        st.subheader("📁 Project Type")

        project_type = st.selectbox(
            "Select Project Type",
            options=list(project_types.keys()),
            format_func=lambda x: project_types[x]['name'],
            help="Choose the type of novel project"
        )

        # Show project type info
        pt_info = project_types[project_type]
        st.caption(pt_info['description'])

        with st.expander("Project Type Details"):
            st.markdown(f"""
            - **Max Chapters:** {pt_info['max_chapters']}
            - **Main Characters:** {pt_info['max_main_chars']}
            - **Arc-Based:** {'Yes' if pt_info['use_arcs'] else 'No'}
            - **Agents:** {len(pt_info['agents'])}
            """)

        st.divider()

        # Workflow mode
        st.subheader("🔄 Workflow")
        use_extended = st.toggle(
            "Use Extended Workflow",
            value=True,
            help="Use the new extended workflow with all agents"
        )

        # Streaming toggle
        enable_streaming = st.toggle(
            "Show Streaming Output",
            value=config.get('ui', {}).get('streaming_output', True),
            help="Display real-time output from agents"
        )

        # Model info
        st.subheader("🤖 Active Model")
        st.caption(f"{config['ollama']['default_model']}")

    # Main content - Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Create", "👥 Agents", "📊 Results", "⚙️ LLM Config", "📖 Help"])

    # =========================================================================
    # TAB 1: CREATE
    # =========================================================================
    with tab1:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.header("Project Setup")

            # Genre selection
            genres = get_available_genres()
            default_idx = genres.index("literary_fiction") if "literary_fiction" in genres else 0

            genre = st.selectbox(
                "Select Genre",
                genres,
                index=default_idx,
                help="Choose the genre style for your book"
            )

            # Number of chapters
            max_chapters = pt_info['max_chapters']
            default_chapters = min(10, max_chapters)

            num_chapters = st.slider(
                "Number of Chapters",
                min_value=1,
                max_value=max_chapters,
                value=default_chapters,
                help=f"How many chapters to plan (max {max_chapters} for {project_type})"
            )

            # For light novels, show arc info
            if pt_info['use_arcs']:
                chapters_per_arc = 30
                num_arcs = (num_chapters // chapters_per_arc) + 1
                st.info(f"📚 This will create approximately {num_arcs} story arc(s)")

            # Story prompt
            story_prompt = st.text_area(
                "Story Premise",
                value=config.get('ui', {}).get('default_prompt',
                    "A lighthouse keeper on a remote island discovers a mysterious signal that seems to be coming from beneath the waves."),
                height=120,
                help="Describe your story idea"
            )

            # Additional instructions
            additional_instructions = st.text_area(
                "Additional Instructions (optional)",
                value="",
                height=80,
                help="Any specific requirements or style preferences"
            )

            st.divider()

            # Chapter Writing Options
            st.subheader("Chapter Writing")
            write_chapters = st.checkbox(
                "Write Chapters (not just plan)",
                value=False,
                help="Generate actual chapter prose, not just outline"
            )

            if write_chapters:
                max_chapters_to_write = st.slider(
                    "Chapters to Write",
                    min_value=1,
                    max_value=min(10, num_chapters),
                    value=min(3, num_chapters),
                    help="Number of chapters to generate (start small, each takes time)"
                )
                st.warning(f"Writing {max_chapters_to_write} chapters will take significant time (~5-15 min each)")
            else:
                max_chapters_to_write = 0

        with col2:
            st.header("Workflow Preview")

            # Show which agents will be used
            st.subheader("Active Agents")

            if pt_info['agents']:
                # Group agents by phase
                phase_agents = {
                    'Foundation': ['story_architect'],
                    'World Building': ['character_designer', 'location_designer', 'item_cataloger',
                                      'magic_system_designer', 'faction_manager', 'lore_keeper'],
                    'Structure': ['plot_architect', 'timeline_manager', 'arc_architect'],
                    'Writing': ['scene_writer', 'dialogue_specialist', 'chapter_compiler',
                               'cliffhanger_specialist', 'combat_choreographer'],
                    'Editorial': ['continuity_editor', 'style_editor', 'character_roster_manager',
                                 'power_system_manager'],
                    'Literary': ['theme_weaver', 'prose_stylist', 'psychological_depth'],
                    'Final': ['manuscript_reviewer']
                }

                for phase, agents in phase_agents.items():
                    active = [a for a in agents if a in pt_info['agents']]
                    if active:
                        with st.expander(f"**{phase}** ({len(active)} agents)", expanded=(phase == 'Foundation')):
                            display_agent_list(active, columns=2)
            else:
                st.caption("Using legacy workflow (3 agents)")

            # Estimated scope
            st.divider()
            st.subheader("Estimated Scope")

            word_target = num_chapters * 3000  # Rough estimate
            st.metric("Target Word Count", f"{word_target:,} words")

            if pt_info['use_arcs']:
                st.metric("Story Arcs", f"{num_arcs}")

        # Run button
        st.divider()

        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("🚀 Generate Book Plan", type="primary", use_container_width=True):
                if not story_prompt.strip():
                    st.error("Please enter a story premise!")
                elif not models:
                    st.error("Ollama server not available. Please check connection.")
                else:
                    # Container for streaming output
                    st.markdown("### Generation Progress")

                    if enable_streaming and use_extended:
                        # Streaming mode
                        status_container = st.empty()
                        output_container = st.empty()

                        status_container.info("Starting workflow...")

                        results = run_planning_workflow_streaming(
                            project_type=project_type,
                            genre=genre,
                            num_chapters=num_chapters,
                            story_prompt=story_prompt,
                            additional_instructions=additional_instructions,
                            output_container=output_container,
                            status_container=status_container,
                            write_chapters=write_chapters,
                            max_chapters_to_write=max_chapters_to_write
                        )
                    else:
                        # Non-streaming mode
                        progress_bar = st.progress(0, text="Initializing...")
                        status_text = st.empty()

                        def update_progress(message):
                            status_text.text(message)

                        with st.spinner("Running AI Book Writer... This may take several minutes."):
                            if use_extended:
                                results = run_planning_workflow(
                                    project_type=project_type,
                                    genre=genre,
                                    num_chapters=num_chapters,
                                    story_prompt=story_prompt,
                                    additional_instructions=additional_instructions,
                                    progress_callback=update_progress
                                )
                            else:
                                results = run_legacy_workflow(
                                    genre=genre,
                                    num_chapters=num_chapters,
                                    story_prompt=story_prompt,
                                    additional_instructions=additional_instructions
                                )

                        progress_bar.progress(100, text="Complete!")

                    if results:
                        st.session_state['results'] = results
                        st.session_state['project_type'] = project_type
                        st.session_state['genre'] = genre
                        st.session_state['num_chapters'] = num_chapters
                        st.session_state['use_extended'] = use_extended
                        st.session_state['wrote_chapters'] = write_chapters
                        if write_chapters:
                            st.success("✅ Book plan AND chapters generated! Check the Results tab.")
                        else:
                            st.success("✅ Book plan generated! Check the Results tab.")
                        st.rerun()

    # =========================================================================
    # TAB 2: AGENTS
    # =========================================================================
    with tab2:
        st.header("Agent Reference")

        agent_info = {
            'story_architect': {
                'name': 'Story Architect',
                'icon': '📐',
                'phase': 'Foundation',
                'description': 'Designs the complete narrative architecture including three-act structure, themes, and emotional journey.',
                'outputs': ['Logline', 'Story Overview', 'Act Structure', 'Theme List']
            },
            'character_designer': {
                'name': 'Character Designer',
                'icon': '👤',
                'phase': 'World Building',
                'description': 'Creates deep character profiles with psychology, voice patterns, and arcs for consistency.',
                'outputs': ['Character Profiles', 'Voice Guides', 'Relationship Map']
            },
            'location_designer': {
                'name': 'Location Designer',
                'icon': '🏰',
                'phase': 'World Building',
                'description': 'Designs detailed locations with sensory details, atmosphere, and significance.',
                'outputs': ['Location Profiles', 'Sensory Details', 'Connections']
            },
            'arc_architect': {
                'name': 'Arc Architect',
                'icon': '🌀',
                'phase': 'Structure',
                'description': 'Designs multi-chapter story arcs for serialized fiction (Light Novels).',
                'outputs': ['Arc Premises', 'Chapter Breakdowns', 'Cliffhanger Placements']
            },
            'magic_system_designer': {
                'name': 'Magic System Designer',
                'icon': '✨',
                'phase': 'World Building',
                'description': 'Creates consistent magic/power systems following Sanderson\'s Laws.',
                'outputs': ['System Rules', 'Abilities List', 'Progression Path']
            },
            'continuity_editor': {
                'name': 'Continuity Editor',
                'icon': '🔍',
                'phase': 'Editorial',
                'description': 'Catches contradictions in character facts, timeline, locations, and items.',
                'outputs': ['Continuity Report', 'Flagged Issues', 'Fix Suggestions']
            },
            'theme_weaver': {
                'name': 'Theme Weaver',
                'icon': '🎭',
                'phase': 'Literary',
                'description': 'Ensures thematic depth and consistency for literary fiction.',
                'outputs': ['Theme Analysis', 'Symbol Tracking', 'Enhancement Suggestions']
            },
        }

        # Display agent cards
        cols = st.columns(3)
        for i, (key, info) in enumerate(agent_info.items()):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"### {info['icon']} {info['name']}")
                    st.caption(f"Phase: {info['phase']}")
                    st.markdown(info['description'])
                    st.markdown("**Outputs:**")
                    for output in info['outputs']:
                        st.markdown(f"- {output}")
                    st.divider()

        # Full agent list by project type
        st.subheader("Agents by Project Type")

        for pt_name, pt_data in project_types.items():
            with st.expander(f"**{pt_data['name']}** - {len(pt_data['agents'])} agents"):
                display_agent_list(pt_data['agents'], columns=4)

    # =========================================================================
    # TAB 3: RESULTS
    # =========================================================================
    with tab3:
        st.header("Generated Content")

        if 'results' in st.session_state and st.session_state['results']:
            results = st.session_state['results']
            use_extended = st.session_state.get('use_extended', False)

            # Show metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Project Type", st.session_state.get('project_type', 'standard'))
            with col2:
                st.metric("Genre", st.session_state.get('genre', 'unknown'))
            with col3:
                st.metric("Chapters", st.session_state.get('num_chapters', 0))

            st.divider()

            if use_extended:
                # Extended workflow results
                wrote_chapters = st.session_state.get('wrote_chapters', False)
                if wrote_chapters and 'writing' in results:
                    result_tabs = st.tabs(["🏗️ Foundation", "🌍 World Building", "📊 Structure", "📖 Chapters", "📥 Download"])
                else:
                    result_tabs = st.tabs(["🏗️ Foundation", "🌍 World Building", "📊 Structure", "📥 Download"])

                with result_tabs[0]:
                    st.subheader("Story Architecture")
                    foundation = results.get('foundation', {})
                    if 'story_architecture' in foundation:
                        st.markdown(foundation['story_architecture'])
                    else:
                        st.info("No foundation data available")

                with result_tabs[1]:
                    st.subheader("World Building")
                    world = results.get('world_building', {})

                    # Check for errors
                    if 'errors' in results and results['errors']:
                        with st.expander("⚠️ Errors Encountered", expanded=True):
                            for err in results['errors']:
                                st.error(err)

                    if world:
                        sub_tabs = st.tabs(["Characters", "Locations", "Items", "Magic", "Factions", "Lore", "Summary"])

                        with sub_tabs[0]:
                            # New format: list of individual character profiles
                            characters = world.get('characters', [])
                            if isinstance(characters, list) and characters:
                                st.success(f"Generated {len(characters)} characters")
                                for char in characters:
                                    char_type = char.get('type', 'unknown')
                                    icon = "⭐" if char_type == 'main' else "👤"
                                    with st.expander(f"{icon} {char.get('name', 'Unknown')} ({char.get('role', 'Unknown')})"):
                                        st.markdown(char.get('profile', 'No profile data'))
                            elif isinstance(characters, str):
                                st.markdown(characters)
                            else:
                                st.info("No character data")

                        with sub_tabs[1]:
                            locations = world.get('locations', [])
                            if isinstance(locations, list) and locations:
                                st.success(f"Generated {len(locations)} locations")
                                for loc in locations:
                                    with st.expander(f"🏰 {loc.get('name', 'Unknown')} ({loc.get('type', 'Unknown')})"):
                                        st.markdown(loc.get('profile', 'No profile data'))
                            elif isinstance(locations, str):
                                st.markdown(locations)
                            else:
                                st.info("No location data")

                        with sub_tabs[2]:
                            items = world.get('items', [])
                            if isinstance(items, list) and items:
                                st.success(f"Generated {len(items)} items")
                                for item in items:
                                    with st.expander(f"🗡️ {item.get('name', 'Unknown')} ({item.get('category', 'Unknown')})"):
                                        st.caption(f"Owner: {item.get('owner', 'Unknown')}")
                                        st.markdown(item.get('profile', 'No profile data'))
                            elif isinstance(items, str):
                                st.markdown(items)
                            else:
                                st.info("No item data")

                        with sub_tabs[3]:
                            st.markdown(world.get('magic_system', 'No magic system data'))

                        with sub_tabs[4]:
                            st.markdown(world.get('factions', 'No faction data'))

                        with sub_tabs[5]:
                            st.markdown(world.get('lore', 'No lore data'))

                        with sub_tabs[6]:
                            # Show entity extraction summary
                            entity_list = world.get('entity_list', {})
                            if entity_list:
                                st.subheader("Entity Extraction Summary")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Main Characters", len(entity_list.get('main_characters', [])))
                                    st.metric("Locations", len(entity_list.get('locations', [])))
                                with col2:
                                    st.metric("Supporting Characters", len(entity_list.get('supporting_characters', [])))
                                    st.metric("Items", len(entity_list.get('items', [])))

                                # Generation success rates
                                st.subheader("Generation Results")
                                chars_generated = len(world.get('characters', []))
                                locs_generated = len(world.get('locations', []))
                                items_generated = len(world.get('items', []))

                                total_expected = (len(entity_list.get('main_characters', [])) +
                                                min(len(entity_list.get('supporting_characters', [])), 10) +
                                                len(entity_list.get('locations', [])) +
                                                min(len(entity_list.get('items', [])), 15))
                                total_generated = chars_generated + locs_generated + items_generated

                                if total_expected > 0:
                                    success_rate = (total_generated / total_expected) * 100
                                    st.progress(success_rate / 100)
                                    st.caption(f"Success rate: {success_rate:.1f}% ({total_generated}/{total_expected} entities)")
                    else:
                        st.info("No world building data available")

                with result_tabs[2]:
                    st.subheader("Plot Structure")
                    structure = results.get('structure', {})

                    if structure:
                        if 'arcs' in structure:
                            st.markdown("### Story Arcs")
                            for i, arc in enumerate(structure['arcs'], 1):
                                with st.expander(f"Arc {i}"):
                                    st.markdown(arc)

                        if 'plot_structure' in structure:
                            st.markdown("### Plot Structure")
                            st.markdown(structure['plot_structure'])

                        if 'timeline' in structure:
                            st.markdown("### Timeline")
                            st.markdown(structure['timeline'])
                    else:
                        st.info("No structure data available")

                # Chapters tab (only if chapters were written)
                if wrote_chapters and 'writing' in results:
                    with result_tabs[3]:
                        st.subheader("Written Chapters")
                        writing = results.get('writing', {})

                        if writing:
                            chapters = writing.get('chapters', [])
                            total_words = writing.get('total_word_count', 0)

                            # Summary metrics
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Chapters Written", len(chapters))
                            with col2:
                                st.metric("Total Words", f"{total_words:,}")

                            # Show any errors
                            writing_errors = results.get('writing_errors', [])
                            if writing_errors:
                                with st.expander("⚠️ Writing Errors", expanded=False):
                                    for err in writing_errors:
                                        st.error(err)

                            # Display each chapter
                            st.divider()
                            for chapter in chapters:
                                chapter_num = chapter.get('number', '?')
                                word_count = chapter.get('word_count', 0)
                                content = chapter.get('content', '')

                                with st.expander(f"📖 Chapter {chapter_num} ({word_count:,} words)", expanded=False):
                                    st.markdown(content)
                        else:
                            st.info("No chapters written yet")

                    download_tab_idx = 4
                else:
                    download_tab_idx = 3

                with result_tabs[download_tab_idx]:
                    st.subheader("Download Results")

                    # Compile plan output
                    plan_output = f"""# AI Book Writer - Story Plan
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Project Type: {st.session_state.get('project_type', 'standard')}
Genre: {st.session_state.get('genre', 'unknown')}
Chapters Planned: {st.session_state.get('num_chapters', 0)}

## Foundation
{results.get('foundation', {}).get('story_architecture', 'N/A')}

## World Building

### Characters
"""
                    # Handle character data (could be list or string)
                    chars = results.get('world_building', {}).get('characters', [])
                    if isinstance(chars, list):
                        for char in chars:
                            plan_output += f"\n#### {char.get('name', 'Unknown')} ({char.get('role', '')})\n"
                            plan_output += f"{char.get('profile', 'No profile')[:2000]}...\n"
                    else:
                        plan_output += str(chars)

                    plan_output += f"""
### Locations
"""
                    locs = results.get('world_building', {}).get('locations', [])
                    if isinstance(locs, list):
                        for loc in locs:
                            plan_output += f"\n#### {loc.get('name', 'Unknown')} ({loc.get('type', '')})\n"
                            plan_output += f"{loc.get('profile', 'No profile')[:1500]}...\n"
                    else:
                        plan_output += str(locs)

                    plan_output += f"""
### Items
{results.get('world_building', {}).get('items', 'N/A')}

### Magic System
{results.get('world_building', {}).get('magic_system', 'N/A')}

### Factions
{results.get('world_building', {}).get('factions', 'N/A')}

### Lore
{results.get('world_building', {}).get('lore', 'N/A')}

## Structure

### Plot Structure
{results.get('structure', {}).get('plot_structure', 'N/A')}

### Timeline
{results.get('structure', {}).get('timeline', 'N/A')}
"""

                    st.markdown("### Plan Downloads")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Download Plan (Markdown)",
                            data=plan_output,
                            file_name=f"book_plan_{st.session_state.get('project_type', 'standard')}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    with col2:
                        st.download_button(
                            label="📥 Download Plan (JSON)",
                            data=json.dumps(results, indent=2, default=str),
                            file_name=f"book_plan_{st.session_state.get('project_type', 'standard')}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                            mime="application/json",
                            use_container_width=True
                        )

                    # Chapter downloads (if chapters were written)
                    if wrote_chapters and 'writing' in results:
                        st.divider()
                        st.markdown("### Chapter Downloads")

                        # Get pre-compiled markdown from workflow
                        chapters_md = results.get('chapters_markdown', '')
                        full_manuscript = results.get('full_manuscript', '')

                        if not chapters_md:
                            # Compile chapters manually if not available
                            writing = results.get('writing', {})
                            chapters = writing.get('chapters', [])
                            total_words = writing.get('total_word_count', 0)

                            chapters_md = f"""# Novel Chapters
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Total Words: {total_words:,}
Chapters: {len(chapters)}

---

"""
                            for chapter in chapters:
                                chapters_md += f"{chapter.get('content', '')}\n\n"
                                chapters_md += f"*({chapter.get('word_count', 0):,} words)*\n\n---\n\n"

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.download_button(
                                label="📖 Chapters (Markdown)",
                                data=chapters_md,
                                file_name=f"chapters_{st.session_state.get('project_type', 'standard')}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                                mime="text/markdown",
                                use_container_width=True
                            )
                        with col2:
                            if full_manuscript:
                                st.download_button(
                                    label="📚 Full Manuscript",
                                    data=full_manuscript,
                                    file_name=f"manuscript_{st.session_state.get('project_type', 'standard')}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                                    mime="text/markdown",
                                    use_container_width=True
                                )
                        with col3:
                            ywriter_xml = results.get('ywriter_xml', '')
                            if ywriter_xml:
                                st.download_button(
                                    label="📝 yWriter7 Project",
                                    data=ywriter_xml,
                                    file_name=f"novel_{st.session_state.get('project_type', 'standard')}_{datetime.now().strftime('%Y%m%d_%H%M')}.yw7",
                                    mime="application/xml",
                                    use_container_width=True
                                )

            else:
                # Legacy workflow results
                result_tabs = st.tabs(["Story Arc", "Settings", "Outline", "Download"])

                with result_tabs[0]:
                    st.markdown("### Story Arc")
                    st.markdown(results.get('story_arc', 'No story arc generated'))

                with result_tabs[1]:
                    st.markdown("### World Settings")
                    st.markdown(results.get('settings', 'No settings generated'))

                with result_tabs[2]:
                    st.markdown("### Chapter Outlines")
                    st.markdown(results.get('outline', 'No outline generated'))

                with result_tabs[3]:
                    full_output = f"""# AI Book Writer Output
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Genre: {st.session_state.get('genre', 'unknown')}
Chapters: {st.session_state.get('num_chapters', 0)}

## Story Arc
{results.get('story_arc', '')}

## World Settings
{results.get('settings', '')}

## Chapter Outlines
{results.get('outline', '')}
"""
                    st.download_button(
                        label="📥 Download Full Output",
                        data=full_output,
                        file_name=f"book_plan_{st.session_state.get('genre', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
        else:
            st.info("No results yet. Generate a book plan in the Create tab.")

            # Show sample output structure
            with st.expander("Expected Output Structure"):
                st.markdown("""
                **Extended Workflow generates:**

                1. **Foundation**
                   - Story Architecture (logline, themes, acts)

                2. **World Building**
                   - Character Profiles (with voice guides)
                   - Location Profiles (with sensory details)
                   - Item Catalog
                   - Magic System (for fantasy)
                   - Factions (for fantasy)
                   - Lore (for fantasy)

                3. **Structure**
                   - Story Arcs (for light novels)
                   - Plot Structure (scene-by-scene)
                   - Timeline
                """)

    # =========================================================================
    # TAB 4: LLM CONFIGURATION
    # =========================================================================
    with tab4:
        st.header("LLM Provider Configuration")
        st.markdown("Configure multiple LLM backends and assign them to specific agents.")

        try:
            from llm_providers import (
                get_registry, get_agent_manager, ProviderConfig, ProviderType,
                AgentLLMAssignment
            )

            registry = get_registry()
            agent_manager = get_agent_manager()

            # Provider Management Section
            st.subheader("🔌 LLM Providers")

            # Add new provider form
            with st.expander("➕ Add New Provider", expanded=False):
                # Pre-configured URLs for providers
                url_info = {
                    'ollama': {
                        'url': 'http://localhost:11434',
                        'help': 'For network: http://IP_ADDRESS:11434'
                    },
                    'lmstudio': {
                        'url': 'http://localhost:1234',
                        'help': 'For network: http://IP_ADDRESS:1234'
                    },
                    'openrouter': {
                        'url': 'https://openrouter.ai/api/v1',
                        'help': 'Get API key from openrouter.ai'
                    },
                    'openai': {
                        'url': 'https://api.openai.com/v1',
                        'help': 'Get API key from platform.openai.com'
                    },
                    'gemini': {
                        'url': 'https://generativelanguage.googleapis.com',
                        'help': 'Get API key from Google AI Studio'
                    },
                    'anthropic': {
                        'url': 'https://api.anthropic.com',
                        'help': 'Get API key from console.anthropic.com'
                    }
                }

                col1, col2 = st.columns(2)
                with col1:
                    new_provider_name = st.text_input("Provider Name", key="new_prov_name",
                                                      placeholder="e.g., My OpenRouter")
                    new_provider_type = st.selectbox(
                        "Provider Type",
                        options=[pt.value for pt in ProviderType],
                        format_func=lambda x: x.title(),
                        key="new_prov_type"
                    )

                # Track provider type changes to update URL
                if 'last_provider_type' not in st.session_state:
                    st.session_state.last_provider_type = new_provider_type
                if st.session_state.last_provider_type != new_provider_type:
                    st.session_state.last_provider_type = new_provider_type
                    # Clear the cached URL to show new default
                    if 'new_prov_url' in st.session_state:
                        del st.session_state['new_prov_url']
                    st.rerun()

                with col2:
                    info = url_info.get(new_provider_type, {'url': '', 'help': ''})
                    new_base_url = st.text_input(
                        "Base URL",
                        value=info['url'],
                        key="new_prov_url",
                        help=info['help']
                    )
                    new_api_key = st.text_input("API Key (if required)", type="password",
                                                key="new_prov_key")

                if st.button("Add Provider", key="add_provider_btn"):
                    if new_provider_name and new_base_url:
                        try:
                            new_config = ProviderConfig(
                                name=new_provider_name,
                                provider_type=ProviderType(new_provider_type),
                                base_url=new_base_url,
                                api_key=new_api_key
                            )
                            provider = registry.add_provider(new_config)
                            success, msg = provider.test_connection()
                            if success:
                                registry.save_config()
                                st.success(f"✅ Added provider: {new_provider_name} - {msg}")
                                st.rerun()
                            else:
                                st.warning(f"⚠️ Provider added but connection test failed: {msg}")
                                registry.save_config()
                        except Exception as e:
                            st.error(f"Error adding provider: {e}")
                    else:
                        st.error("Please provide a name and base URL")

            # List existing providers
            providers = registry.list_providers()
            if providers:
                for prov_name in providers:
                    provider = registry.get_provider(prov_name)
                    if not provider:
                        continue

                    with st.expander(f"**{prov_name}** ({provider.provider_type.value})", expanded=False):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.text(f"URL: {provider.config.base_url}")
                            st.text(f"Type: {provider.provider_type.value}")
                        with col2:
                            # Test connection
                            if st.button(f"Test Connection", key=f"test_{prov_name}"):
                                success, msg = provider.test_connection()
                                if success:
                                    st.success(msg)
                                else:
                                    st.error(msg)
                        with col3:
                            if st.button("🗑️ Remove", key=f"remove_{prov_name}"):
                                registry.remove_provider(prov_name)
                                registry.save_config()
                                st.rerun()

                        # Show available models
                        st.markdown("**Available Models:**")
                        try:
                            models = provider.get_models(refresh=False)
                            if models:
                                model_data = []
                                for m in models[:20]:  # Limit to 20 for display
                                    model_data.append({
                                        'Model': m.name,
                                        'Context': f"{m.context_window:,}",
                                        'Max Output': f"{m.max_output:,}"
                                    })
                                st.dataframe(model_data, use_container_width=True, hide_index=True)
                                if len(models) > 20:
                                    st.caption(f"...and {len(models) - 20} more models")
                            else:
                                st.info("No models found. Click 'Test Connection' to refresh.")
                        except Exception as e:
                            st.error(f"Error fetching models: {e}")
            else:
                st.info("No providers configured. Add one above.")

            st.divider()

            # Agent LLM Assignment Section
            st.subheader("🤖 Agent LLM Assignments")
            st.markdown("Assign specific LLMs to different agents. Unassigned agents use the default.")

            # Default assignment
            col1, col2 = st.columns(2)
            with col1:
                default_prov = st.selectbox(
                    "Default Provider",
                    options=providers if providers else ["No providers"],
                    index=providers.index(agent_manager.default_provider) if agent_manager.default_provider in providers else 0,
                    key="default_provider_select"
                )
            with col2:
                # Get models for selected provider
                if default_prov and default_prov != "No providers":
                    prov = registry.get_provider(default_prov)
                    if prov:
                        models = prov.get_models()
                        model_ids = [m.id for m in models]
                        default_model_idx = model_ids.index(agent_manager.default_model) if agent_manager.default_model in model_ids else 0
                        default_model = st.selectbox(
                            "Default Model",
                            options=model_ids if model_ids else ["No models"],
                            index=default_model_idx if model_ids else 0,
                            key="default_model_select"
                        )
                    else:
                        default_model = st.selectbox("Default Model", options=["No models"])
                else:
                    default_model = st.selectbox("Default Model", options=["Configure provider first"])

            if st.button("Save Default", key="save_default_btn"):
                if default_prov and default_model and default_prov != "No providers":
                    agent_manager.set_default(default_prov, default_model)
                    agent_manager.save_config()
                    st.success(f"✅ Default set to {default_prov}/{default_model}")

            # Per-agent assignments
            st.markdown("### Per-Agent Assignments")

            # Get list of available agents
            try:
                from agents_extended import ALL_AGENTS
                agent_names = list(ALL_AGENTS.keys())
            except:
                agent_names = ['story_architect', 'character_designer', 'location_designer',
                              'plot_architect', 'scene_writer', 'continuity_editor']

            # Show existing assignments and allow new ones
            for agent_name in agent_names:
                assignment = agent_manager.assignments.get(agent_name)
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

                with col1:
                    st.markdown(f"**{agent_name.replace('_', ' ').title()}**")

                with col2:
                    assigned_prov = st.selectbox(
                        "Provider",
                        options=["(Use Default)"] + providers,
                        index=(providers.index(assignment.provider_name) + 1) if assignment and assignment.provider_name in providers else 0,
                        key=f"prov_{agent_name}",
                        label_visibility="collapsed"
                    )

                with col3:
                    if assigned_prov and assigned_prov != "(Use Default)":
                        prov = registry.get_provider(assigned_prov)
                        if prov:
                            models = prov.get_models()
                            model_ids = [m.id for m in models]
                            current_model = assignment.model_id if assignment else ""
                            model_idx = model_ids.index(current_model) if current_model in model_ids else 0
                            assigned_model = st.selectbox(
                                "Model",
                                options=model_ids if model_ids else ["No models"],
                                index=model_idx,
                                key=f"model_{agent_name}",
                                label_visibility="collapsed"
                            )
                        else:
                            assigned_model = None
                    else:
                        assigned_model = st.selectbox(
                            "Model",
                            options=["(Default)"],
                            key=f"model_{agent_name}",
                            label_visibility="collapsed"
                        )

                with col4:
                    if assigned_prov != "(Use Default)" and assigned_model:
                        if st.button("Set", key=f"set_{agent_name}"):
                            agent_manager.assign(agent_name, assigned_prov, assigned_model)
                            agent_manager.save_config()
                            st.success(f"✅ Set")
                    elif assignment:
                        if st.button("Clear", key=f"clear_{agent_name}"):
                            if agent_name in agent_manager.assignments:
                                del agent_manager.assignments[agent_name]
                                agent_manager.save_config()
                                st.rerun()

            # Context window info
            st.divider()
            st.subheader("📊 Context Window Summary")
            st.markdown("Context windows affect how much information each agent can process.")

            context_data = []
            for agent_name in agent_names[:10]:
                ctx = agent_manager.get_context_window_for_agent(agent_name)
                assignment = agent_manager.get_assignment(agent_name)
                context_data.append({
                    'Agent': agent_name.replace('_', ' ').title(),
                    'Provider': assignment.provider_name or "(Default)",
                    'Model': assignment.model_id or "(Default)",
                    'Context Window': f"{ctx:,} tokens"
                })
            st.dataframe(context_data, use_container_width=True, hide_index=True)

        except ImportError as e:
            st.error(f"LLM Provider module not available: {e}")
        except Exception as e:
            st.error(f"Error loading LLM configuration: {e}")
            import traceback
            st.code(traceback.format_exc())

    # =========================================================================
    # TAB 5: HELP
    # =========================================================================
    with tab5:
        st.header("Help & Documentation")

        with st.expander("🚀 Quick Start", expanded=True):
            st.markdown("""
            1. **Select Project Type** in the sidebar (Standard, Light Novel, Literary, etc.)
            2. **Choose a Genre** that matches your story
            3. **Set Chapter Count** based on your project scope
            4. **Enter your Story Premise** - be descriptive!
            5. **Click Generate** and wait for the AI to work

            The system will run multiple specialized AI agents to create a comprehensive book plan.
            """)

        with st.expander("📁 Project Types"):
            st.markdown("""
            | Type | Best For | Chapters | Key Features |
            |------|----------|----------|--------------|
            | **Standard** | Traditional novels | 20-40 | 3-act structure, core agents |
            | **Light Novel** | Web novels, serialized | 100-500 | Arc-based, power progression |
            | **Literary** | Character-driven | 20-30 | Theme weaving, prose styling |
            | **Fantasy** | World-building heavy | 30-50 | Magic systems, factions, lore |
            | **Epic Fantasy** | Multi-POV epics | 50-100 | Combined features |
            """)

        with st.expander("🤖 Agent Workflow"):
            st.markdown("""
            The extended workflow runs in phases:

            ```
            Phase 1: FOUNDATION
                └── Story Architect (creates narrative structure)

            Phase 2: WORLD BUILDING (can run in parallel)
                ├── Character Designer
                ├── Location Designer
                ├── Item Cataloger
                └── Fantasy agents (if enabled)

            Phase 3: STRUCTURE
                ├── Arc Architect (light novels)
                ├── Plot Architect
                └── Timeline Manager

            Phase 4+: WRITING & EDITORIAL (future)
            ```
            """)

        with st.expander("💾 yWriter7 Integration"):
            st.markdown("""
            The system can integrate with yWriter7 projects:

            - **Read existing projects** for RAG context
            - **Export to yWriter7 format** (.yw7 files)
            - **Track characters, locations, items** in yWriter7 format

            To use: Place .yw7 files in the `projects/` directory.
            """)

        with st.expander("⚙️ Configuration"):
            st.markdown("""
            Edit `config.yaml` to customize:

            - **Model assignments** per agent
            - **LLM parameters** (temperature, max tokens)
            - **Embedder settings** for RAG
            - **Vector database** configuration (for large projects)
            - **Workflow settings** (parallel execution, editorial loops)
            - **UI settings** (port, streaming output)
            """)

        with st.expander("🔧 Running the App"):
            port = config.get('ui', {}).get('port', 8501)
            st.markdown(f"""
            The app is configured to run on port **{port}**.

            To start the app:
            ```bash
            cd /root/AiBookWriter4
            source venv/bin/activate
            streamlit run app.py --server.port {port}
            ```

            Or use the run script:
            ```bash
            ./run.sh
            ```
            """)


if __name__ == "__main__":
    main()
