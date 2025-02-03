--- START OF FILE app.py ---
import streamlit as st
import yaml
import os
from agents.story_planner import StoryPlanner
from agents.setting_builder import SettingBuilder  # Import SettingBuilder Agent
from agents.outline_creator import OutlineCreator  # Import OutlineCreator Agent
from agents.writer import Writer  # Import Writer Agent
import io  # To capture stdout
import subprocess  # For running ollama command

# Initialize session state
if 'story_arc_output' not in st.session_state:
    st.session_state['story_arc_output'] = ""
if 'setting_builder_output' not in st.session_state:
    st.session_state['setting_builder_output'] = ""
if 'outline_creator_output' not in st.session_state:
    st.session_state['outline_creator_output'] = ""


def get_ollama_models():
    pass # ... (get_ollama_models function - same as before) ...


def run_book_creation_workflow():  # MOVED FUNCTION DEFINITION UP HERE - Corrected order
    """Executes the book creation workflow: StoryPlanner -> SettingBuilder -> OutlineCreator."""
    genre_selection = st.session_state['genre_selection']
    num_chapters = st.session_state['num_chapters']
    additional_instructions = st.session_state['additional_instructions']

    st.write(f"Starting book creation workflow for genre: {genre_selection}, chapters: {num_chapters}")  # Feedback

    # --- Load Configuration (for base_url, prompts_dir) ---
    with open("config.yaml", "r") as config_file:
        config_yaml = yaml.safe_load(config_file)
    prompts_dir_path = config_yaml.get("prompts_dir", "config/prompts")
    base_url_config = config_yaml['model_list'][0]['litellm_params']['base_url']

    # --- Initialize Agents ---
    story_planner_model = st.session_state.get("story_planner_model_selection", "deepseek-r1:1.5b")
    story_planner = StoryPlanner(  # Initialize StoryPlanner
        base_url=base_url_config, model=story_planner_model, prompts_dir=prompts_dir_path, genre=genre_selection, num_chapters=num_chapters, streaming=True)  # ADDED streaming=True

    setting_builder_model = st.session_state.get("story_planner_model_selection", "deepseek-r1:1.5b")  # Using StoryPlanner model for SettingBuilder for now
    setting_builder = SettingBuilder(  # Initialize SettingBuilder
        base_url=base_url_config, model=setting_builder_model, prompts_dir=prompts_dir_path, temperature=st.session_state.get("story_planner_temperature", 0.7), max_tokens=st.session_state.get("story_planner_max_tokens", 2000), top_p=st.session_state.get("story_planner_top_p", 0.95), context_window=st.session_state.get("story_planner_context", 8192), streaming=True)  # ADDED streaming=True and config from Tab 2

    outline_creator_model = st.session_state.get("story_planner_model_selection", "deepseek-r1:1.5b")  # Using StoryPlanner model for OutlineCreator for now
    outline_creator = OutlineCreator(  # Initialize OutlineCreator
        base_url=base_url_config, model=outline_creator_model, prompts_dir=prompts_dir_path, temperature=st.session_state.get("story_planner_temperature", 0.7), max_tokens=st.session_state.get("story_planner_max_tokens", 2000), top_p=st.session_state.get("story_planner_top_p", 0.95), context_window=st.session_state.get("story_planner_context", 8192), streaming=True)  # ADDED streaming=True and config from Tab 2


    # --- Run Story Planner Task ---
    st.subheader("Story Arc Output:")  # Section for Story Arc Output
    output_placeholder_arc = st.empty()
    story_arc_stream = story_planner.plan_story_arc(genre=genre_selection, num_chapters=num_chapters, additional_instructions=additional_instructions)
    full_story_arc_output = ""
    for chunk in story_arc_stream:
        full_story_arc_output += chunk
        output_placeholder_arc.text(full_story_arc_output)
    st.session_state['story_arc_output'] = full_story_arc_output
    st.success("Story arc planning complete!")

    # --- Run Setting Builder Task ---
    st.subheader("Setting Builder Output:")  # Section for Setting Builder Output
    output_placeholder_settings = st.empty()
    setting_task_description = "Develop initial world settings and locations based on the story arc."
    setting_stream = setting_builder.run_information_gathering_task(task_description=setting_task_description, outline_context=full_story_arc_output)  # Pass story arc output as context, switched to streaming
    full_setting_output = ""
    for chunk in setting_stream:  # Stream Setting Builder output
        full_setting_output += chunk
        output_placeholder_settings.text(full_setting_output)
    st.session_state['setting_builder_output'] = full_setting_output
    st.success("Setting building complete!")

    # --- Run Outline Creator Task ---
    st.subheader("Outline Creator Output:")  # Section for Outline Creator Output
    output_placeholder_outline = st.empty()
    outline_task_description = "Create detailed chapter outlines based on the story arc."
    outline_stream = outline_creator.run_information_gathering_task(task_description=outline_task_description, project_notes_content=full_story_arc_output)  # Pass story arc output as project notes, switched to streaming
    full_outline_output = ""
    for chunk in outline_stream:  # Stream Outline Creator output
        full_outline_output += chunk
        output_placeholder_outline.text(full_outline_output)
    st.session_state['outline_creator_output'] = full_outline_output
    st.success("Outline creation complete!")

    st.session_state['plan_story_arc_triggered'] = False  # Reset Story Planner trigger - not really needed anymore for this workflow
    st.session_state['build_settings_triggered'] = False  # Reset Setting Builder trigger - not really needed anymore for this workflow
    st.session_state['create_outline_triggered'] = False  # Reset Outline Creator trigger - not really needed anymore for this workflow

    st.success("Book creation workflow initiated!")  # Overall success message for workflow



st.title("AI Book Writer Control Panel")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Project Setup", "Agent Configuration", "Process Monitor", "Output"]
)


with tab1:
    st.header("Project Setup")

    genre_dir = "config/genres"  # Path to your genres directory
    genre_files = [
        f[:-3] for f in os.listdir(genre_dir) if f.endswith(".py")
    ]  # List genre names
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
    num_chapters = st.slider("Number of Chapters", min_value=1, max_value=30, value=4)  # Default to 4 now
    additional_instructions = st.text_area(
        "Additional Instructions (optional)",
        value="Focus on atmosphere and suspense.",
        height=100,
    )

    if st.button("Start Book Creation Process"):  # CHANGED BUTTON LABEL
        st.session_state["story_arc_output"] = ""  # Clear outputs
        st.session_state["setting_builder_output"] = ""
        st.session_state["outline_creator_output"] = ""
        st.session_state["genre_selection"] = genre_selection
        st.session_state["num_chapters"] = num_chapters
        st.session_state["additional_instructions"] = additional_instructions
        run_book_creation_workflow()  # CALL THE WORKFLOW FUNCTION


with tab2:
    st.header("Agent Configuration")

    st.subheader("Ollama Models")
    ollama_models = get_ollama_models()  # Fetch available Ollama models
    if ollama_models:
        model_list = [model['name'] for model in ollama_models['models']]
    else:
        model_list = ["No models found"]  # Default if no models fetched

    st.subheader("Story Planner Agent")
    st.session_state["story_planner_model_selection"] = st.selectbox(
        "Model for Story Planner",
        model_list,
        index=model_list.index("deepseek-r1:1.5b")
        if "deepseek-r1:1.5b" in model_list
        else 0,
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

    # ... (Agent configurations for other agents would follow a similar pattern) ...


with tab3:
    st.header("Process Monitor")
    # --- Story Arc Output Display (Moved to Workflow Function) ---
    # --- Setting Builder Output Display (Moved to Workflow Function) ---
    # --- Outline Creator Output Display (NEW) ---
    st.subheader("Outline Creator Output:")  # Section for Outline Creator Output
    output_placeholder_outline = st.empty()  # Placeholder for Outline Creator output
    if st.session_state.get("outline_creator_output"):
        output_placeholder_outline.text(st.session_state["outline_creator_output"])

    st.subheader("Setting Builder Output:")  # Section for Setting Builder Output
    output_placeholder_settings = st.empty()
    if st.session_state.get("setting_builder_output"):
        output_placeholder_settings.text(st.session_state["setting_builder_output"])

    st.subheader("Story Arc Output:")  # Section for Story Arc Output
    output_placeholder_arc = st.empty()
    if st.session_state.get("story_arc_output"):
        output_placeholder_arc.text(st.session_state["story_arc_output"])


with tab4:
    st.header("Output Inspection")
    st.subheader("Story Arc:")
    st.text_area(
        "Final Story Arc Output",
        value=st.session_state["story_arc_output"],
        height=400,
    )  # Display stored Story Arc
    st.subheader("World Settings:")  # NEW: World Settings output in Tab 4
    st.text_area(
        "Final World Settings Output",
        value=st.session_state["setting_builder_output"],
        height=400,
    )  # Display World Settings
    st.subheader("Chapter Outlines:")  # NEW: Chapter Outlines output in Tab 4
    st.text_area(
        "Final Chapter Outlines Output",
        value=st.session_state["outline_creator_output"],
        height=400,
    )  # Display Chapter Outlines


if __name__ == "__main__":
    pass