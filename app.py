import streamlit as st
import yaml
import os
from agents.story_planner import StoryPlanner
from agents.setting_builder import SettingBuilder # Import SettingBuilder Agent
from agents.writer import Writer  # Import Writer Agent (for config example)
import io  # To capture stdout
import subprocess # For running ollama command

# Initialize session state for story arc output and trigger - MOVED TO TOP
if 'story_arc_output' not in st.session_state:
    st.session_state['story_arc_output'] = ""
if 'plan_story_arc_triggered' not in st.session_state:
    st.session_state['plan_story_arc_triggered'] = False
if 'setting_builder_output' not in st.session_state:
    st.session_state['setting_builder_output'] = ""
if 'build_settings_triggered' not in st.session_state:
    st.session_state['build_settings_triggered'] = False
if 'story_planner_model_selection' not in st.session_state: # Initialize model selections in session state
    st.session_state['story_planner_model_selection'] = "deepseek-r1:1.5b" # Changed default to deepseek-r1:1.5b
if 'writer_model_selection' not in st.session_state:
    st.session_state['writer_model_selection'] = "deepseek-r1:1.5b" # Changed default to deepseek-r1:1.5b


def get_ollama_models():
    """Fetches the list of available models from the Ollama server."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
        output_lines = result.stdout.strip().split('\n')
        models = []
        for line in output_lines[1:]: # Skip header line
            parts = line.split()
            if parts:
                models.append(parts[0]) # Model name is the first part
        return models
    except FileNotFoundError:
        st.error("Error: `ollama` command not found. Please ensure Ollama is installed and in your PATH.")
        return []
    except subprocess.CalledProcessError as e:
        st.error(f"Error listing Ollama models. Is Ollama server running? Details: {e}")
        st.error(f"Subprocess error output: {e.stderr}") # Print stderr output for subprocess errors
        st.error(f"Subprocess error return code: {e.returncode}") # Print return code
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching Ollama models: {e}. Details: {e}")
        return []


st.title("AI Book Writer Control Panel")

tab1, tab2, tab3, tab4 = st.tabs(["Project Setup", "Agent Configuration", "Process Monitor", "Output"])


with tab1:
    st.header("Project Setup")

    genre_dir = "config/genres"  # Path to your genres directory
    genre_files = [f[:-3] for f in os.listdir(genre_dir) if f.endswith(".py")]  # List genre names
    genre_selection = st.selectbox("Select Genre", genre_files, index=genre_files.index("literary_fiction") if "literary_fiction" in genre_files else 0)

    initial_prompt = st.text_area("Initial Story Idea/Prompt", value="A story about a solitary lighthouse keeper who discovers a mysterious message in a bottle.", height=150)
    num_chapters = st.slider("Number of Chapters", min_value=1, max_value=30, value=4) # Default to 4 now
    additional_instructions = st.text_area("Additional Instructions (optional)", value="Focus on atmosphere and suspense.", height=100)

    if st.button("Plan Story Arc"): # Story Planner Button (same as before)
        st.session_state['plan_story_arc_triggered'] = True 
        st.session_state['story_arc_output'] = "" 
        st.session_state['genre_selection'] = genre_selection 
        st.session_state['num_chapters'] = num_chapters
        st.session_state['additional_instructions'] = additional_instructions

    if st.button("Build Settings"): # NEW: Setting Builder Button
        st.session_state['build_settings_triggered'] = True # Add trigger for Setting Builder
        st.session_state['setting_builder_output'] = "" # Initialize output for Setting Builder


with tab2:
    st.header("Agent Configuration")

    ollama_model_list = get_ollama_models() # Fetch models from Ollama

    if ollama_model_list: # Only show config if models are fetched successfully
        st.write("DEBUG: ollama_model_list:", ollama_model_list) # DEBUG PRINT - ADD THIS LINE
        with st.expander("Story Planner Agent Configuration"): # Using expanders for better UI organization
            st.subheader("Story Planner Agent")
            story_planner_model_selection = st.selectbox("Model", ollama_model_list, index=ollama_model_list.index(st.session_state['story_planner_model_selection']) if st.session_state['story_planner_model_selection'] in ollama_model_list else 0, key="story_planner_model_selection") # Use dynamic model list
            story_planner_temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.05, key="story_planner_temp")
            story_planner_max_tokens = st.number_input("Max Tokens", min_value=500, max_value=30000, value=3500, step=100, key="story_planner_tokens")
            story_planner_top_p = st.slider("Top P", min_value=0.0, max_value=1.0, value=0.95, step=0.05, key="story_planner_top_p")
            story_planner_context_window = st.number_input("Context Window", min_value=2048, max_value=131072, value=8192, step=1024, key="story_planner_context") # INCREASED max_value and adjusted value

        with st.expander("Writer Agent Configuration"): # Expander for Writer Agent config
            st.subheader("Writer Agent")
            writer_model_selection = st.selectbox("Model", ollama_model_list, index=writer_model_list.index(st.session_state['writer_model_selection']) if st.session_state['writer_model_selection'] in ollama_model_list else 0, key="writer_model_selection") # Use dynamic model list
            writer_temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.8, step=0.05, key="writer_temp")
            writer_max_tokens = st.number_input("Max Tokens", min_value=500, max_value=30000, value=3500, step=100, key="writer_tokens")
            writer_top_p = st.slider("Top P", min_value=0.0, max_value=1.0, value=0.95, step=0.05, key="writer_top_p")
            writer_context_window = st.number_input("Context Window", min_value=2048, max_value=131072, value=8192, step=1024, key="writer_context")
    else:
        st.warning("Could not fetch model list from Ollama. Ensure Ollama is running and accessible.")


with tab3:
    st.header("Process Monitor")
    st.subheader("Story Arc Output:")
    output_placeholder_arc = st.empty()  # Placeholder for Story Arc
    
    if st.session_state['plan_story_arc_triggered']: # Story Planner Logic (same as before, but using output_placeholder_arc)
        # ... (Story Planner agent initialization and stream - using output_placeholder_arc.text(full_output)) ...
        st.session_state['story_arc_output'] = full_output
        st.session_state['plan_story_arc_triggered'] = False
        st.success("Story arc planning complete!")

    st.subheader("Setting Builder Output:") # NEW: Setting Builder Output section
    output_placeholder_settings = st.empty() # Placeholder for Setting Builder output

    if st.session_state.get('build_settings_triggered'): # NEW: Setting Builder Logic
        st.write("Building world settings...") # Feedback message
        # --- Load Configuration and Initialize SettingBuilder Agent ---
        with open("config.yaml", "r") as config_file:
            config_yaml = yaml.safe_load(config_file)
        prompts_dir_path = config_yaml.get("prompts_dir", "config/prompts")
        base_url_config = config_yaml['model_list'][0]['litellm_params']['base_url']
        setting_builder_model = st.session_state.get("story_planner_model_selection", "deepseek-r1:1.5b") # Using StoryPlanner model for now - make configurable later

        setting_builder = SettingBuilder( # Initialize SettingBuilder Agent
            base_url=base_url_config,
            model=setting_builder_model,
            temperature=0.7, # Default values for now - make configurable later
            max_tokens=2000,
            top_p=0.95,
            prompts_dir=prompts_dir_path,
        )

        setting_output = ""
        # --- Run Setting Builder Task (Placeholder Task for now) ---
        setting_task_description = "Develop initial world settings and locations based on the story arc." # Simple task
        setting_result = setting_builder.run_information_gathering_task(task_description=setting_task_description) # Assuming a method like this exists in SettingBuilder
        setting_output = setting_result # Capture the output

        output_placeholder_settings.text(setting_output) # Display Setting Builder output in Tab 3
        st.session_state['setting_builder_output'] = setting_output # Store output in session state
        st.session_state['build_settings_triggered'] = False # Reset trigger
        st.success("Setting building complete!") # Success message


with tab4:
    st.header("Output Inspection")
    st.subheader("Story Arc:")
    st.text_area("Final Story Arc Output", value=st.session_state['story_arc_output'], height=400) # Display stored Story Arc

    st.subheader("World Settings:") # NEW: World Settings output in Tab 4
    st.text_area("Final World Settings Output", value=st.session_state['setting_builder_output'], height=400) # Display World Settings


if __name__ == '__main__':
    pass