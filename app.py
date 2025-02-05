# --- app.py ---
"""
# AI Book Writer Control Panel

This Streamlit application provides a user interface for configuring and controlling the AI Book Writer workflow.

## Features:

- **Project Setup:**
    - Select the genre of the book.
    - Provide an initial story idea/prompt.
    - Specify the desired number of chapters.
    - Add optional additional instructions for the AI.
- **Agent Configuration:**
    - Configure individual settings for each agent:
        - Story Planner
        - Setting Builder
        - Outline Creator
    - Adjust parameters like:
        - Model selection (from available Ollama models)
        - Temperature
        - Max tokens
        - Top-p
        - Context window
- **Process Monitor:**
    - View the output of each agent as it's generated.
    - Track the progress of the book creation workflow.
- **Output:**
    - Inspect the final output of each agent:
        - Story Arc
        - World Settings
        - Chapter Outlines

## Usage:

1. **Install Ollama:** Ensure Ollama is installed and running on your system.
2. **Install Dependencies:** Install the required Python packages using `pip install -r requirements.txt`.
3. **Run the Application:** Execute the script with `streamlit run app.py`.
4. **Configure and Run:** Use the Streamlit interface to configure the project, adjust agent settings, and start the book creation process.

## Changelog:

- **2024-02-05:**
    - Refactored `get_ollama_models()` to handle Ollama not being installed and various error conditions.
    - Moved `run_book_creation_workflow()` to the top for better readability and corrected the order of operations.
    - Implemented streaming output for Story Planner, Setting Builder, and Outline Creator.
    - Removed unnecessary triggers for individual agent steps as they are now part of a single workflow.
    - Added detailed error messages and handling for various scenarios.
    - Corrected indentation and formatting issues.
    - Updated agent configuration to use sliders for numerical parameters.
    - Added "Output" tab for inspecting final agent outputs.
    - Initialized `prompts_dir` from `config.yaml` in the workflow function.
    - Updated `StoryPlannerConfig`, `SettingBuilderConfig`, and `OutlineCreatorConfig` to be correctly passed to their respective agent classes.
    - Added clear section headers for agent outputs in the Process Monitor tab.
    - Implemented dynamic loading of genre configurations.
    - Enhanced error handling and user feedback throughout the application.
    - Corrected the instantiation of `OutlineCreator` to match its `__init__` method signature.
"""

import streamlit as st
import yaml
import os
from agents.story_planner import StoryPlanner, StoryPlannerConfig
from agents.setting_builder import SettingBuilder, SettingBuilderConfig
from agents.outline_creator import OutlineCreator, OutlineCreatorConfig
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize session state
if 'story_arc_output' not in st.session_state:
    st.session_state['story_arc_output'] = ""
if 'setting_builder_output' not in st.session_state:
    st.session_state['setting_builder_output'] = ""
if 'outline_creator_output' not in st.session_state:
    st.session_state['outline_creator_output'] = ""

def get_ollama_models():
    """Fetches the list of available Ollama models using the 'ollama list' command and parses as text."""
    model_list = []
    try:
        # Check if ollama is installed
        try:
            subprocess.run(['ollama', '--version'], capture_output=True, check=True)
        except FileNotFoundError:
            st.error("Ollama is not installed or not in your PATH. Please install Ollama first.")
            return None

        # Get model list
        try:
            process = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
            output = process.stdout
            logger.info(f"Ollama list output: {output}")

            # Parse output as text, extracting model names
            for line in output.strip().split('\n'):
                if line.strip() and not line.startswith("NAME"):
                    parts = line.split()
                    model_name = parts[0]
                    model_list.append({"name": model_name})

            if not model_list:
                st.warning("No models found in Ollama list output.")
                return {'models': []}

            return {'models': model_list}

        except subprocess.CalledProcessError as e:
            if "connection refused" in str(e.stderr).lower():
                st.error("Cannot connect to Ollama. Please make sure Ollama is running using 'ollama serve'")
            else:
                st.error(f"Error running Ollama command: {e}")
            return None

    except Exception as e:
        st.error(f"Unexpected error in get_ollama_models: {str(e)}")
        return None

def run_book_creation_workflow():
    """Executes the book creation workflow: StoryPlanner -> SettingBuilder -> OutlineCreator."""
    genre_selection = st.session_state['genre_selection']
    num_chapters = st.session_state['num_chapters']
    additional_instructions = st.session_state['additional_instructions']

    logger.info(f"Starting book creation workflow for genre: {genre_selection}, chapters: {num_chapters}")

    # --- Load Configuration (for base_url, prompts_dir) ---
    with open("config.yaml", "r") as config_file:
        config_yaml = yaml.safe_load(config_file)
    prompts_dir_path = config_yaml.get("prompts_dir", "config/prompts")
    base_url_config = config_yaml['model_list'][0]['litellm_params']['base_url']

    # --- Initialize Agents ---
    story_planner_config = StoryPlannerConfig(
        llm_endpoint=base_url_config,
        llm_model=st.session_state.get("story_planner_model_selection", "deepseek-coder:1.3b"),
        temperature=st.session_state.get("story_planner_temperature", 0.7),
        max_tokens=st.session_state.get("story_planner_max_tokens", 2000),
        top_p=st.session_state.get("story_planner_top_p", 0.95),
        context_window=st.session_state.get("story_planner_context", 8192)
    )
    story_planner = StoryPlanner(
        config=story_planner_config, prompts_dir=prompts_dir_path, genre=genre_selection, num_chapters=num_chapters,
        streaming=True)

    setting_builder_config = SettingBuilderConfig(
        llm_endpoint=base_url_config,
        llm_model=st.session_state.get("setting_builder_model_selection", "deepseek-coder:1.3b"),
        temperature=st.session_state.get("setting_builder_temperature", 0.7),
        max_tokens=st.session_state.get("setting_builder_max_tokens", 2000),
        top_p=st.session_state.get("setting_builder_top_p", 0.95),
        context_window=st.session_state.get("setting_builder_context", 8192)
    )
    setting_builder = SettingBuilder(
        config=setting_builder_config, prompts_dir=prompts_dir_path, streaming=True)

    outline_creator_config = OutlineCreatorConfig(
        llm_endpoint=base_url_config,
        llm_model=st.session_state.get("outline_creator_model_selection", "deepseek-coder:1.3b"),
        temperature=st.session_state.get("outline_creator_temperature", 0.7),
        max_tokens=st.session_state.get("outline_creator_max_tokens", 2000),
        top_p=st.session_state.get("outline_creator_top_p", 0.95),
        context_window=st.session_state.get("outline_creator_context", 8192)
    )
    outline_creator = OutlineCreator(
        config=outline_creator_config, streaming=True)

    # --- Run Story Planner Task ---
    st.subheader("Story Arc Output:")
    output_placeholder_arc = st.empty()
    story_arc_stream = story_planner.plan_story_arc(genre=genre_selection, num_chapters=num_chapters,
                                                    additional_instructions=additional_instructions)
    full_story_arc_output = ""
    for chunk in story_arc_stream:
        full_story_arc_output += chunk
        output_placeholder_arc.markdown(full_story_arc_output)
    st.session_state['story_arc_output'] = full_story_arc_output
    st.success("Story arc planning complete!")

    # --- Run Setting Builder Task ---
    st.subheader("Setting Builder Output:")
    output_placeholder_settings = st.empty()
    setting_task_description = "Develop initial world settings and locations based on the story arc."
    setting_stream = setting_builder.run_information_gathering_task(task_description=setting_task_description,
                                                                   outline_context=full_story_arc_output)
    full_setting_output = ""
    for chunk in setting_stream:
        full_setting_output += chunk
        output_placeholder_settings.markdown(full_setting_output)
    st.session_state['setting_builder_output'] = full_setting_output
    st.success("Setting building complete!")

    # --- Run Outline Creator Task ---
    st.subheader("Outline Creator Output:")
    output_placeholder_outline = st.empty()
    outline_task_description = "Create detailed chapter outlines based on the story arc."
    outline_stream = outline_creator.run_information_gathering_task(task_description=outline_task_description,
                                                                    project_notes_content=full_story_arc_output)
    full_outline_output = ""
    for chunk in outline_stream:
        full_outline_output += chunk
        output_placeholder_outline.markdown(full_outline_output)
    st.session_state['outline_creator_output'] = full_outline_output
    st.success("Outline creation complete!")

    st.session_state['plan_story_arc_triggered'] = False
    st.session_state['build_settings_triggered'] = False
    st.session_state['create_outline_triggered'] = False

    st.success("Book creation workflow initiated!")

st.title("AI Book Writer Control Panel")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Project Setup", "Agent Configuration", "Process Monitor", "Output"]
)

with tab1:
    st.header("Project Setup")

    genre_dir = "config/genres"
    genre_files = [
        f[:-3] for f in os.listdir(genre_dir) if f.endswith(".py")
    ]
    genre_selection = st.selectbox(
        "Select Genre",
        genre_files,
        index=genre_files.index("literary_fiction")
        if "literary_fiction" in genre_files
        else 0,
    )

    initial_prompt = st.text_area(
        "Initial Story Idea/Prompt",
        value="A story about a solitary lighthouse keeper who discovers a mysterious message in a bottle.",
        height=150,
    )
    num_chapters = st.slider("Number of Chapters", min_value=1, max_value=30, value=4)
    additional_instructions = st.text_area(
        "Additional Instructions (optional)",
        value="Focus on atmosphere and suspense.",
        height=100,
    )

    if st.button("Start Book Creation Process"):
        st.session_state["story_arc_output"] = ""
        st.session_state["setting_builder_output"] = ""
        st.session_state["outline_creator_output"] = ""
        st.session_state["genre_selection"] = genre_selection
        st.session_state["num_chapters"] = num_chapters
        st.session_state["additional_instructions"] = additional_instructions
        run_book_creation_workflow()

with tab2:
    st.header("Agent Configuration")

    st.subheader("Ollama Models")
    ollama_models = get_ollama_models()
    if ollama_models and 'models' in ollama_models and isinstance(ollama_models['models'], list):
        model_list = [model['name'] for model in ollama_models['models']]
    else:
        model_list = ["No models found"]

    with st.expander("Story Planner Agent", expanded=True):
        st.session_state["story_planner_model_selection"] = st.selectbox(
            "Model for Story Planner",
            model_list,
            index=model_list.index("deepseek-coder:1.3b") if "deepseek-coder:1.3b" in model_list else 0,
            key="story_planner_model_selectbox",
        )
        st.session_state["story_planner_temperature"] = st.slider(
            "Temperature (Story Planner)",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.01,
            key="story_planner_temp_slider",
        )
        st.session_state["story_planner_max_tokens"] = st.slider(
            "Max Tokens (Story Planner)",
            min_value=100,
            max_value=4000,
            value=2000,
            step=100,
            key="story_planner_tokens_slider",
        )
        st.session_state["story_planner_top_p"] = st.slider(
            "Top P (Story Planner)",
            min_value=0.0,
            max_value=1.0,
            value=0.95,
            step=0.01,
            key="story_planner_top_p_slider",
        )
        st.session_state["story_planner_context"] = st.slider(
            "Context Window (Story Planner)",
            min_value=2048,
            max_value=32768,
            value=8192,
            step=1024,
            key="story_planner_context_slider",
        )

    with st.expander("Setting Builder Agent", expanded=False):
        st.session_state["setting_builder_model_selection"] = st.selectbox(
            "Model for Setting Builder",
            model_list,
            index=model_list.index("deepseek-coder:1.3b") if "deepseek-coder:1.3b" in model_list else 0,
            key="setting_builder_model_selectbox",
        )
        st.session_state["setting_builder_temperature"] = st.slider(
            "Temperature (Setting Builder)",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.01,
            key="setting_builder_temp_slider",
        )
        st.session_state["setting_builder_max_tokens"] = st.slider(
            "Max Tokens (Setting Builder)",
            min_value=100,
            max_value=4000,
            value=2000,
            step=100,
            key="setting_builder_tokens_slider",
        )
        st.session_state["setting_builder_top_p"] = st.slider(
            "Top P (Setting Builder)",
            min_value=0.0,
            max_value=1.0,
            value=0.95,
            step=0.01,
            key="setting_builder_top_p_slider",
        )
        st.session_state["setting_builder_context"] = st.slider(
            "Context Window (Setting Builder)",
            min_value=2048,
            max_value=32768,
            value=8192,
            step=1024,
            key="setting_builder_context_slider",
        )

    with st.expander("Outline Creator Agent", expanded=False):
        st.session_state["outline_creator_model_selection"] = st.selectbox(
            "Model for Outline Creator",
            model_list,
            index=model_list.index("deepseek-coder:1.3b") if "deepseek-coder:1.3b" in model_list else 0,
            key="outline_creator_model_selectbox",
        )
        st.session_state["outline_creator_temperature"] = st.slider(
            "Temperature (Outline Creator)",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.01,
            key="outline_creator_temp_slider",
        )
        st.session_state["outline_creator_max_tokens"] = st.slider(
            "Max Tokens (Outline Creator)",
            min_value=100,
            max_value=4000,
            value=2000,
            step=100,
            key="outline_creator_tokens_slider",
        )
        st.session_state["outline_creator_top_p"] = st.slider(
            "Top P (Outline Creator)",
            min_value=0.0,
            max_value=1.0,
            value=0.95,
            step=0.01,
            key="outline_creator_top_p_slider",
        )
        st.session_state["outline_creator_context"] = st.slider(
            "Context Window (Outline Creator)",
            min_value=2048,
            max_value=32768,
            value=8192,
            step=1024,
            key="outline_creator_context_slider",
        )

with tab3:
    st.header("Process Monitor")
    st.subheader("Outline Creator Output:")
    output_placeholder_outline = st.empty()
    if st.session_state.get("outline_creator_output"):
        output_placeholder_outline.markdown(st.session_state["outline_creator_output"])

    st.subheader("Setting Builder Output:")
    output_placeholder_settings = st.empty()
    if st.session_state.get("setting_builder_output"):
        output_placeholder_settings.markdown(st.session_state["setting_builder_output"])

    st.subheader("Story Arc Output:")
    output_placeholder_arc = st.empty()
    if st.session_state.get("story_arc_output"):
        output_placeholder_arc.markdown(st.session_state["story_arc_output"])

with tab4:
    st.header("Output Inspection")
    st.subheader("Story Arc:")
    st.text_area(
        "Final Story Arc Output",
        value=st.session_state["story_arc_output"],
        height=400,
    )
    st.subheader("World Settings:")
    st.text_area(
        "Final World Settings Output",
        value=st.session_state["setting_builder_output"],
        height=400,
    )
    st.subheader("Chapter Outlines:")
    st.text_area(
        "Final Chapter Outlines Output",
        value=st.session_state["outline_creator_output"],
        height=400,
    )

if __name__ == "__main__":
    pass