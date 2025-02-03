import streamlit as st
import yaml
import os
from agents.story_planner import StoryPlanner
from agents.writer import Writer  # Import Writer Agent (for config example)
import io  # To capture stdout
import subprocess # For running ollama command

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
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching Ollama models: {e}")
        return []


st.title("AI Book Writer Control Panel")

tab1, tab2, tab3, tab4 = st.tabs(["Project Setup", "Agent Configuration", "Process Monitor", "Output"])

# Initialize session state for story arc output and trigger
if 'story_arc_output' not in st.session_state:
    st.session_state['story_arc_output'] = ""
if 'plan_story_arc_triggered' not in st.session_state:
    st.session_state['plan_story_arc_triggered'] = False

with tab1:
    st.header("Project Setup")

    genre_dir = "config/genres"  # Path to your genres directory
    genre_files = [f[:-3] for f in os.listdir(genre_dir) if f.endswith(".py")]  # List genre names
    genre_selection = st.selectbox("Select Genre", genre_files, index=genre_files.index("literary_fiction") if "literary_fiction" in genre_files else 0)

    initial_prompt = st.text_area("Initial Story Idea/Prompt", value="A story about a solitary lighthouse keeper who discovers a mysterious message in a bottle.", height=150)
    num_chapters = st.slider("Number of Chapters", min_value=1, max_value=30, value=4) # Default to 4 now
    additional_instructions = st.text_area("Additional Instructions (optional)", value="Focus on atmosphere and suspense.", height=100)

    if st.button("Plan Story Arc"):
        st.session_state['plan_story_arc_triggered'] = True # Set trigger in session state
        st.session_state['story_arc_output'] = "" # Clear previous output
        st.session_state['genre_selection'] = genre_selection # Store parameters in session state
        st.session_state['num_chapters'] = num_chapters
        st.session_state['additional_instructions'] = additional_instructions


with tab2:
    st.header("Agent Configuration")

    ollama_model_list = get_ollama_models() # Fetch models from Ollama

    if ollama_model_list: # Only show config if models are fetched successfully
        with st.expander("Story Planner Agent Configuration"): # Using expanders for better UI organization
            st.subheader("Story Planner Agent")
            story_planner_model_selection = st.selectbox("Model", ollama_model_list, index=ollama_model_list.index("deepseek-r1:1.5b") if "deepseek-r1:1.5b" in ollama_model_list else 0, key="story_planner_model_selection") # Use dynamic model list - NO direct session_state assignment here anymore
            story_planner_temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.05, key="story_planner_temp")
            story_planner_max_tokens = st.number_input("Max Tokens", min_value=500, max_value=30000, value=3500, step=100, key="story_planner_tokens")
            story_planner_top_p = st.slider("Top P", min_value=0.0, max_value=1.0, value=0.95, step=0.05, key="story_planner_top_p")
            story_planner_context_window = st.number_input("Context Window", min_value=2048, max_value=131072, value=8192, step=1024, key="story_planner_context") # INCREASED max_value and adjusted value

        with st.expander("Writer Agent Configuration"): # Expander for Writer Agent config
            st.subheader("Writer Agent")
            writer_model_selection = st.selectbox("Model", ollama_model_list, index=writer_model_list.index("llama3:8b-instruct") if "llama3:8b-instruct" in ollama_model_list else 0, key="writer_model_selection") # Use dynamic model list - NO direct session_state assignment here anymore
            writer_temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.8, step=0.05, key="writer_temp")
            writer_max_tokens = st.number_input("Max Tokens", min_value=500, max_value=30000, value=3500, step=100, key="writer_tokens")
            writer_top_p = st.slider("Top P", min_value=0.0, max_value=1.0, value=0.95, step=0.05, key="writer_top_p")
            writer_context_window = st.number_input("Context Window", min_value=2048, max_value=131072, value=8192, step=1024, key="writer_context")
    else:
        st.warning("Could not fetch model list from Ollama. Ensure Ollama is running and accessible.")


with tab3:
    st.header("Process Monitor")
    st.subheader("Story Arc Output:")
    output_placeholder = st.empty()  # Placeholder in Tab 3

    if st.session_state['plan_story_arc_triggered']: # Check trigger in session state
        genre_selection = st.session_state['genre_selection'] # Get parameters from session state
        num_chapters = st.session_state['num_chapters']
        additional_instructions = st.session_state['additional_instructions']

        st.write(f"Planning story arc for genre: {genre_selection}, chapters: {num_chapters}") # Moved feedback to Tab 3

        # --- Load Configuration (for base_url, model, prompts_dir) ---
        with open("config.yaml", "r") as config_file:
            config_yaml = yaml.safe_load(config_file)
        prompts_dir_path = config_yaml.get("prompts_dir", "config/prompts")
        base_url_config = config_yaml['model_list'][0]['litellm_params']['base_url'] # Get base_url
        story_planner_model = st.session_state.get("story_planner_model_selection", "deepseek-r1:1.5b") # Get model from Tab 2 or default
        story_planner_temperature = st.session_state.get("story_planner_temp", 0.7)
        story_planner_max_tokens = st.session_state.get("story_planner_tokens", 3500)
        story_planner_top_p = st.session_state.get("story_planner_top_p", 0.95)
        story_planner_context_window = st.session_state.get("story_planner_context", 8192)


        # --- Initialize Story Planner Agent ---
        story_planner = StoryPlanner(
            base_url=base_url_config,
            model=story_planner_model,
            temperature=story_planner_temperature,
            context_window=story_planner_context_window,
            max_tokens=story_planner_max_tokens,
            top_p=story_planner_top_p,
            prompts_dir=prompts_dir_path,
            genre=genre_selection,
            num_chapters=num_chapters # Use num_chapters from UI
        )

        full_output = ""
        story_arc_stream = story_planner.plan_story_arc(
            genre=genre_selection,
            num_chapters=num_chapters, # Use num_chapters from UI
            additional_instructions=additional_instructions
        )

        for chunk in story_arc_stream:
            full_output += chunk
            output_placeholder.text(full_output) # Update placeholder in Tab 3

        st.session_state['story_arc_output'] = full_output # Store full output in session state
        st.session_state['plan_story_arc_triggered'] = False # Reset trigger
        st.success("Story arc planning complete!") # Keep success message in Tab 3


with tab4:
    st.header("Output Inspection")
    st.subheader("Story Arc:")
    st.text_area("Final Story Arc Output", value=st.session_state['story_arc_output'], height=400) # Display stored output


if __name__ == '__main__':
    pass