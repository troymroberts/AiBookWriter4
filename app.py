"""
AiBookWriter4 - Streamlit UI
Clean implementation using CrewAI Flows for book generation.
"""

import streamlit as st
import asyncio
import yaml
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from flows import BookWriterFlow, BookState
from flows.state import WorkflowPhase, ReviewGateStatus

# Page config
st.set_page_config(
    page_title="AI Book Writer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal CSS
st.markdown("""
<style>
    .phase-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 14px;
        font-weight: 500;
    }
    .phase-active { background-color: #28a745; color: white; }
    .phase-complete { background-color: #007bff; color: white; }
    .phase-pending { background-color: #6c757d; color: white; }
    .output-box {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 16px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 13px;
        max-height: 500px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# CONFIG & HELPERS
# =============================================================================

def load_config() -> Dict[str, Any]:
    """Load config.yaml"""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def get_genres() -> List[str]:
    """Get available genre configurations"""
    genres_dir = "config/genres"
    if not os.path.exists(genres_dir):
        return ["literary_fiction", "fantasy_scifi", "thriller_mystery"]
    return sorted([
        f[:-3] for f in os.listdir(genres_dir)
        if f.endswith('.py') and not f.startswith('_')
    ])


def get_ollama_models(base_url: str) -> List[str]:
    """Fetch models from Ollama"""
    try:
        import urllib.request
        import json
        url = f"{base_url}/api/tags"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return [m['name'] for m in data.get('models', [])]
    except Exception:
        return ["llama3.2", "mistral", "mixtral"]


def format_phase(phase: WorkflowPhase) -> str:
    """Format phase name for display"""
    return phase.value.replace('_', ' ').title()


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'flow': None,
        'running': False,
        'output_log': [],
        'results': None,
        'review_pending': False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# FLOW EXECUTION
# =============================================================================

async def run_flow_async(flow: BookWriterFlow, output_placeholder, progress_placeholder):
    """Run the flow with streaming output"""
    try:
        streaming = await flow.kickoff_async()

        async for chunk in streaming:
            # Update output
            if hasattr(chunk, 'content') and chunk.content:
                st.session_state.output_log.append(chunk.content)
                output_placeholder.markdown(
                    f"<div class='output-box'>{''.join(st.session_state.output_log[-100:])}</div>",
                    unsafe_allow_html=True
                )

            # Update progress
            progress = flow.state.get_progress_percentage()
            progress_placeholder.progress(
                int(progress),
                text=f"{format_phase(flow.state.current_phase)} - {progress:.1f}%"
            )

            # Check for review gate
            if flow.state.current_review_status == ReviewGateStatus.PENDING:
                st.session_state.review_pending = True
                return "review_pending"

        return streaming.result

    except Exception as e:
        st.error(f"Flow error: {e}")
        return None


def run_flow_sync(flow: BookWriterFlow, output_placeholder, progress_placeholder):
    """Run flow synchronously (fallback for environments without async)"""
    try:
        # Run kickoff
        result = flow.kickoff()

        # Process streaming output if available
        if hasattr(result, '__iter__'):
            for chunk in result:
                if hasattr(chunk, 'content') and chunk.content:
                    st.session_state.output_log.append(chunk.content)
                    output_placeholder.markdown(
                        f"<div class='output-box'>{''.join(st.session_state.output_log[-100:])}</div>",
                        unsafe_allow_html=True
                    )

                progress = flow.state.get_progress_percentage()
                progress_placeholder.progress(
                    int(progress),
                    text=f"{format_phase(flow.state.current_phase)} - {progress:.1f}%"
                )

        return result.result if hasattr(result, 'result') else result

    except Exception as e:
        st.error(f"Flow error: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_sidebar(config: Dict[str, Any]):
    """Render sidebar with configuration options"""
    with st.sidebar:
        st.header("Configuration")

        # Genre selection
        genres = get_genres()
        genre = st.selectbox(
            "Genre",
            genres,
            index=genres.index("literary_fiction") if "literary_fiction" in genres else 0
        )

        # Project type
        project_type = st.selectbox(
            "Project Type",
            ["STANDARD", "LIGHT_NOVEL", "LITERARY", "FANTASY", "EPIC_FANTASY"],
            index=0
        )

        # Chapter count
        num_chapters = st.slider("Chapters", min_value=1, max_value=100, value=10)

        st.divider()

        # LLM Configuration
        st.subheader("LLM Settings")

        ollama_config = config.get('ollama', {})
        base_url = st.text_input(
            "Ollama URL",
            value=ollama_config.get('base_url', 'http://localhost:11434')
        )

        # Fetch available models
        models = get_ollama_models(base_url)
        default_model = ollama_config.get('model', 'llama3.2')

        model = st.selectbox(
            "Model",
            models if models else [default_model],
            index=0
        )

        st.divider()

        # Review gates
        st.subheader("Review Gates")
        enable_review = st.checkbox("Enable review gates", value=True)
        review_phases = []
        if enable_review:
            review_phases = st.multiselect(
                "Review after",
                ["foundation", "world_building", "structure", "chapter"],
                default=["structure"]
            )

        return {
            'genre': genre,
            'project_type': project_type,
            'num_chapters': num_chapters,
            'base_url': base_url,
            'model': model,
            'enable_review': enable_review,
            'review_phases': review_phases
        }


def render_phase_progress(state: BookState):
    """Render phase progress indicators"""
    phases = [
        WorkflowPhase.FOUNDATION,
        WorkflowPhase.WORLD_BUILDING,
        WorkflowPhase.STRUCTURE,
        WorkflowPhase.WRITING,
        WorkflowPhase.EDITORIAL,
        WorkflowPhase.COMPLETE
    ]

    cols = st.columns(len(phases))

    for i, phase in enumerate(phases):
        with cols[i]:
            if state.current_phase == phase:
                badge_class = "phase-active"
                icon = "🔄"
            elif phases.index(state.current_phase) > i:
                badge_class = "phase-complete"
                icon = "✅"
            else:
                badge_class = "phase-pending"
                icon = "⏳"

            st.markdown(
                f"<span class='phase-badge {badge_class}'>{icon} {format_phase(phase)}</span>",
                unsafe_allow_html=True
            )


def render_review_gate(flow: BookWriterFlow):
    """Render review gate UI when waiting for approval"""
    st.warning("📋 Review Required - Please review the content before proceeding")

    # Show content to review
    with st.expander("Story Arc", expanded=True):
        st.markdown(flow.state.story_arc or "*Not yet generated*")

    with st.expander("Plot Outline", expanded=True):
        st.markdown(flow.state.plot_outline or "*Not yet generated*")

    # Feedback input
    feedback = st.text_area(
        "Feedback (optional)",
        placeholder="Enter any feedback or revision requests..."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Approve & Continue", type="primary", use_container_width=True):
            st.session_state.review_pending = False
            flow.resume_after_review(approved=True, feedback=feedback)
            st.rerun()

    with col2:
        if st.button("🔄 Request Revision", use_container_width=True):
            st.session_state.review_pending = False
            flow.resume_after_review(approved=False, feedback=feedback)
            st.rerun()


def render_results(flow: BookWriterFlow):
    """Render generation results"""
    state = flow.state

    st.success(f"Generation complete! {state.total_words_written:,} words written.")

    # Tabs for different result sections
    tabs = st.tabs(["📖 Manuscript", "👥 Characters", "🏰 Locations", "📊 Stats", "📥 Export"])

    with tabs[0]:  # Manuscript
        st.subheader("Generated Chapters")

        if state.chapters:
            for chapter in state.chapters:
                with st.expander(f"Chapter {chapter.chapter_number}: {chapter.title or 'Untitled'} ({chapter.word_count:,} words)"):
                    st.markdown(chapter.content or "*No content*")
        else:
            st.info("No chapters generated yet")

    with tabs[1]:  # Characters
        st.subheader("Character Profiles")

        if state.characters:
            for char in state.characters:
                with st.expander(f"{char.name} ({char.role})"):
                    st.markdown(f"**Description:** {char.description}")
                    st.markdown(f"**Backstory:** {char.backstory}")
                    st.markdown(f"**Voice:** {char.voice_profile}")
        else:
            st.info("No characters defined")

    with tabs[2]:  # Locations
        st.subheader("Location Profiles")

        if state.locations:
            for loc in state.locations:
                with st.expander(loc.name):
                    st.markdown(f"**Description:** {loc.description}")
                    st.markdown(f"**Significance:** {loc.significance}")
        else:
            st.info("No locations defined")

    with tabs[3]:  # Stats
        st.subheader("Generation Statistics")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Words", f"{state.total_words_written:,}")
        col2.metric("Chapters", f"{state.chapters_completed}/{state.target_chapters}")
        col3.metric("Editorial Iterations", state.total_editorial_iterations)

        st.markdown(f"**Genre:** {state.genre}")
        st.markdown(f"**Project Type:** {state.project_type}")
        st.markdown(f"**Started:** {state.started_at}")
        st.markdown(f"**Completed:** {state.last_updated}")

    with tabs[4]:  # Export
        st.subheader("Export Options")

        # Markdown export
        manuscript = flow.export_manuscript()
        st.download_button(
            "📄 Download Markdown",
            data=manuscript,
            file_name=f"{state.project_name.replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )

        # JSON state export
        import json
        state_json = state.model_dump_json(indent=2)
        st.download_button(
            "💾 Download Project State (JSON)",
            data=state_json,
            file_name=f"{state.project_name.replace(' ', '_')}_state.json",
            mime="application/json",
            use_container_width=True
        )


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    init_session_state()

    st.title("📚 AI Book Writer")
    st.caption("Powered by CrewAI Flows, Ollama, and ChromaDB")

    # Load config
    config = load_config()

    # Sidebar configuration
    settings = render_sidebar(config)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Story Premise")

        project_name = st.text_input(
            "Project Name",
            value="My Novel",
            placeholder="Enter a name for your project"
        )

        premise = st.text_area(
            "Story Premise",
            height=150,
            placeholder="Describe your story idea...\n\nExample: A lighthouse keeper discovers mysterious signals coming from beneath the ocean, leading them to uncover an ancient underwater civilization that has been watching humanity for millennia."
        )

        with st.expander("Additional Instructions (optional)"):
            additional = st.text_area(
                "Extra guidance for the AI",
                placeholder="Any specific requirements, themes to explore, or constraints..."
            )

    with col2:
        st.header("Project Summary")

        st.markdown(f"""
        **Genre:** {settings['genre'].replace('_', ' ').title()}
        **Type:** {settings['project_type']}
        **Chapters:** {settings['num_chapters']}
        **Model:** {settings['model']}
        **Est. Words:** ~{settings['num_chapters'] * 3000:,}
        """)

        if settings['enable_review']:
            st.info(f"Review gates: {', '.join(settings['review_phases'])}")

    st.divider()

    # Generation controls
    if st.session_state.review_pending and st.session_state.flow:
        render_review_gate(st.session_state.flow)

    elif st.session_state.running:
        st.info("🔄 Generation in progress...")

        # Progress indicators
        if st.session_state.flow:
            render_phase_progress(st.session_state.flow.state)

        progress_placeholder = st.empty()
        output_placeholder = st.empty()

        # Show output log
        if st.session_state.output_log:
            output_placeholder.markdown(
                f"<div class='output-box'>{''.join(st.session_state.output_log[-100:])}</div>",
                unsafe_allow_html=True
            )

        if st.button("⏹️ Stop Generation"):
            st.session_state.running = False
            st.rerun()

    elif st.session_state.results:
        # Show results
        render_results(st.session_state.flow)

        if st.button("🔄 Start New Project"):
            st.session_state.flow = None
            st.session_state.results = None
            st.session_state.output_log = []
            st.rerun()

    else:
        # Start button
        if st.button("🚀 Generate Novel", type="primary", use_container_width=True, disabled=not premise):
            if not premise:
                st.error("Please enter a story premise")
                return

            # Create flow with settings
            state = BookState(
                project_name=project_name,
                genre=settings['genre'],
                premise=premise,
                target_chapters=settings['num_chapters'],
                project_type=settings['project_type'],
                llm_base_url=settings['base_url'],
                llm_model=f"ollama/{settings['model']}",
                review_gates_enabled=settings['enable_review'],
                review_gate_phases=settings['review_phases']
            )

            flow = BookWriterFlow(initial_state=state)
            st.session_state.flow = flow
            st.session_state.running = True
            st.session_state.output_log = []

            st.rerun()

    # Run flow if needed (after rerun)
    if st.session_state.running and st.session_state.flow and not st.session_state.review_pending:
        progress_placeholder = st.empty()
        output_placeholder = st.empty()

        progress_placeholder.progress(0, text="Starting...")

        # Try async first, fall back to sync
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                run_flow_async(st.session_state.flow, output_placeholder, progress_placeholder)
            )
        except Exception:
            result = run_flow_sync(st.session_state.flow, output_placeholder, progress_placeholder)

        if result == "review_pending":
            st.session_state.review_pending = True
        elif result:
            st.session_state.results = result
            st.session_state.running = False
        else:
            st.session_state.running = False

        st.rerun()


if __name__ == "__main__":
    main()
