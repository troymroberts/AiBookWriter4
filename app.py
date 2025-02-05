# app.py Changelog
# ------------------
# 2025-02-05 - 16:15 UTC
# Fix: Resolved SyntaxError: expected 'except' or 'finally' block AGAIN on line 72
#      Corrected indentation of the 'except subprocess.CalledProcessError as e:' block
#      to align properly with its corresponding 'try' block when running 'ollama list'.
#
# 2025-02-05 - 16:00 UTC
# Fix: Switched from JSON parsing to text parsing for Ollama model list.
#      Modified get_ollama_models to parse 'ollama list' output as plain text,
#      extracting model names directly from each line, as JSON parsing consistently fails.
#
# 2025-02-05 - 15:45 UTC
# Fix: Improved JSON parsing in get_ollama_models to handle non-JSON output gracefully.
#      Added more robust parsing logic to handle potential non-JSON lines in 'ollama list' output.
#      Displayed raw output using st.code for debugging purposes when JSONDecodeError occurs.
#
# 2025-02-05 - 15:30 UTC
# Fix: Resolved SyntaxError: expected 'except' or 'finally' block on line 46
#      Corrected indentation of except block within get_ollama_models function
#      to properly handle JSONDecodeError and Exception.
#      Added descriptive error messages and return None in except blocks for robustness.
# ------------------
#--- START OF FILE app.py ---#
import streamlit as st
import yaml
import os
from agents.story_planner import StoryPlanner, StoryPlannerConfig  # Import Agent and Config
from agents.setting_builder import SettingBuilder, SettingBuilderConfig  # Import SettingBuilder Agent and Config
from agents.outline_creator import OutlineCreator, OutlineCreatorConfig  # Import OutlineCreator Agent and Config
from agents.writer import Writer  # Import Writer Agent
import io  # To capture stdout
import subprocess  # For running ollama command
import json

# Initialize session state
if 'story_arc_output' not in st.session_state:
    st.session_state['story_arc_output'] = ""
if 'setting_builder_output' not in st.session_state:
    st.session_state['setting_builder_output'] = ""
if 'outline_creator_output' not in st.session_state:
    st.session_state['outline_creator_output'] = ""


def get_ollama_models():
    """Fetches the list of available Ollama models using the 'ollama list' command and parses as text."""
    model_list = []  # Initialize as empty list
    try:
        # First check if ollama is installed
        try:
            subprocess.run(['ollama', '--version'], capture_output=True, check=True)
        except FileNotFoundError:
            st.error("Ollama is not installed or not in your PATH. Please install Ollama first.")
            return None

        # Try to get model list -  REMOVED --format json
        try:
            process = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)  # Removed --format json
            output = process.stdout
            st.code(output)  # Display raw output for debugging

            # Parse output as text, extracting model names - TEXT PARSING IMPLEMENTATION
            model_list = []
            for line in output.strip().split('\n'):
                if line.strip():
                    parts = line.split()  # Split line by spaces
                    model_name = parts[0]  # Model name is the first part of the line
                    model_list.append({"name": model_name})  # Append model dictionary

            if not model_list:
                st.warning("No models found in Ollama list output.")
                return {'models': []}  # Return empty model list

            return {'models': model_list}  # Return list of model dictionaries


        except subprocess.CalledProcessError as e:  # ADDED EXCEPT BLOCK - Handling subprocess error - CORRECTED INDENTATION
            if "connection refused" in str(e.stderr).lower():
                st.error("Cannot connect to Ollama. Please make sure Ollama is running using 'ollama serve'")
            else:
                st.error(f"Error running Ollama command: {e}")  # More generic error for subprocess
            return None


    except Exception as e:  # Expecting except block here - CORRECTED INDENTATION
        st.error(f"Unexpected error in get_ollama_models: {str(e)}")  # More descriptive error message
        return None  # Ensure return None in except block


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
    story_planner_config = StoryPlannerConfig(  # Initialize StoryPlannerConfig
        llm_endpoint=base_url_config,
        llm_model=st.session_state.get("story_planner_model_selection", "deepseek-r1:1.5b"),
        temperature=st.session_state.get("story_planner_temperature", 0.7),
        max_tokens=st.session_state.get("story_planner_max_tokens", 2000),
        top_p=st.session_state.get("story_planner_top_p", 0.95),
        context_window=st.session_state.get("story_planner_context", 8192)
    )
    story_planner = StoryPlanner(  # Initialize StoryPlanner with config
        config=story_planner_config, prompts_dir=prompts_dir_path, genre=genre_selection, num_chapters=num_chapters,
        streaming=True)

    setting_builder_config = SettingBuilderConfig(  # Initialize SettingBuilderConfig
        llm_endpoint=base_url_config,
        llm_model=st.session_state.get("setting_builder_model_selection", "deepseek-r1:1.5b"),  # Use setting builder model selection
        temperature=st.session_state.get("setting_builder_temperature", 0.7),  # Use setting builder temp
        max_tokens=st.session_state.get("setting_builder_max_tokens", 2000),  # Use setting builder tokens
        top_p=st.session_state.get("setting_builder_top_p", 0.95),  # Use setting builder top_p
        context_window=st.session_state.get("setting_builder_context", 8192)  # Use setting builder context
    )
    setting_builder = SettingBuilder(  # Initialize SettingBuilder with config
        config=setting_builder_config, prompts_dir=prompts_dir_path, streaming=True)

    outline_creator_config = OutlineCreatorConfig(  # Initialize OutlineCreatorConfig
        llm_endpoint=base_url_config,
        llm_model=st.session_state.get("outline_creator_model_selection", "deepseek-r1:1.5b"),  # Use outline_creator model selection
        temperature=st.session_state.get("outline_creator_temperature", 0.7),  # Use outline_creator temp
        max_tokens=st.session_state.get("outline_creator_max_tokens", 2000),  # Use outline_creator tokens
        top_p=st.session_state.get("outline_creator_top_p", 0.95),  # Use outline_creator top_p
        context_window=st.session_state.get("outline_creator_context", 8192)  # Use outline_creator context
    )
    outline_creator = OutlineCreator(  # Initialize OutlineCreator with config
        config=outline_creator_config, prompts_dir=prompts_dir_path, streaming=True)

    # --- Run Story Planner Task ---
    st.subheader("Story Arc Output:")  # Section for Story Arc Output
    output_placeholder_arc = st.empty()
    story_arc_stream = story_planner.plan_story_arc(genre=genre_selection, num_chapters=num_chapters,
                                                    additional_instructions=additional_instructions)
    full_story_arc_output = ""
    for chunk in story_arc_stream:
        full_story_arc_output += chunk
        output_placeholder_arc.text(full_story_arc_output)
    st.session_state['story_arc_output'] = full_story_arc_output
    st.success("Story arc planning complete!")

    # --- Run Setting Builder Task ---
    st.subheader("Setting Builder Output:")  # Section for Setting Builder Output
+   output_placeholder_settings = st.empty()
     setting_task_description = "Develop initial world settings and locations based on the story arc."
     setting_stream = setting_builder.run_information_gathering_task(task_description=setting_task_description, outline_context=full_story_arc_output)  # Pass story arc output as context, switched to streaming
     full_setting_output = ""
@@ -108,7 +113,7 @@
         output_placeholder_outline.text(full_outline_output)
     st.session_state['outline_creator_output'] = full_outline_output
     st.success("Outline creation complete!")

-    st.session_state['plan_story_arc_triggered'] = False  # Reset Story Planner trigger - not really needed anymore for this workflow
+   st.session_state['plan_story_arc_triggered'] = False  # Reset Story Planner trigger - not really needed anymore for this workflow
     st.session_state['build_settings_triggered'] = False  # Reset Setting Builder trigger - not really needed anymore for this workflow
     st.session_state['create_outline_triggered'] = False  # Reset Outline Creator trigger - not really needed anymore for this workflow

@@ -190,7 +195,7 @@
         model_list,
         index=model_list.index("deepseek-r1:1.5b") if "deepseek-r1:1.5b" in model_list else 0,
         key="story_planner_model_selectbox",
-    )
+   )
     st.session_state["story_planner_temperature"] = st.slider(
         "Temperature (Story Planner)",
         min_value=0.0,
@@ -215,7 +220,7 @@
         step=0.01,
         key="story_planner_top_p_slider",
     )
-    st.session_state["story_planner_context"] = st.slider(
+   st.session_state["story_planner_context"] = st.slider(
         "Context Window (Story Planner)",
         min_value=2048,
         max_value=32768,
@@ -224,7 +229,7 @@
         key="story_planner_context_slider",
     )

-    st.subheader("Setting Builder Agent")
+   with st.expander("Setting Builder Agent", expanded=False):  # Agent Config Expander
     st.session_state["setting_builder_model_selection"] = st.selectbox(
         "Model for Setting Builder",
         model_list,
@@ -260,8 +265,7 @@
         key="setting_builder_context_slider",
     )

-    st.subheader("Outline Creator Agent")
-    st.session_state["outline_creator_model_selection"] = st.selectbox(
+   with st.expander("Outline Creator Agent", expanded=False):  # Agent Config Expander
+       st.session_state["outline_creator_model_selection"] = st.selectbox(
+           "Model for Outline Creator",
+           model_list,
         index=model_list.index("deepseek-r1:1.5b") if "deepseek-r1:1.5b" in model_list else 0,
         key="outline_creator_model_selectbox",
     )