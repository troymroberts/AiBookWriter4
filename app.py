import streamlit as st
import yaml
import os
from agents.story_planner import StoryPlanner
from agents.setting_builder import SettingBuilder  # Import SettingBuilder Agent
from agents.outline_creator import OutlineCreator  # Import OutlineCreator Agent
from agents.writer import Writer  # Import Writer Agent
import io  # To capture stdout
import subprocess  # For running ollama command

# Initialize session state for story arc output and trigger - MOVED TO TOP
if "story_arc_output" not in st.session_state:
    st.session_state["story_arc_output"] = ""
if "plan_story_arc_triggered" not in st.session_state:
    st.session_state["plan_story_arc_triggered"] = False
if "setting_builder_output" not in st.session_state:
    st.session_state["setting_builder_output"] = ""
if "build_settings_triggered" not in st.session_state:
    st.session_state["build_settings_triggered"] = False
if "outline_creator_output" not in st.session_state:  # New for Outline Creator
    st.session_state["outline_creator_output"] = ""
if "create_outline_triggered" not in st.session_state:  # New for Outline Creator
    st.session_state["create_outline_triggered"] = False
if "story_planner_model_selection" not in st.session_state:  # Initialize model selections in session state
    st.session_state["story_planner_model_selection"] = "deepseek-r1:1.5b"  # Changed default to deepseek-r1:1.5b
if "writer_model_selection" not in st.session_state:
    st.session_state["writer_model_selection"] = "deepseek-r1:1.5b"  # Changed default to deepseek-r1:1.5b


def get_ollama_models():
    """Fetches the list of available models from the Ollama server."""
    try:
        st.write("DEBUG: Running 'ollama list' command...")  # Debug print before command
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, check=True
        )
        st.write(
            "DEBUG: 'ollama list' command completed successfully."
        )  # Debug print after success
        output_lines = result.stdout.strip().split("\n")
        models = []
        for line in output_lines[1:]:  # Skip header line
            parts = line.split()
            if parts:
                models.append(parts[0])  # Model name is the first part
        st.write("DEBUG: Fetched models:", models)  # Debug print of fetched models
        if (
            "deepseek-r1:1.5b" not in models
        ):  # Changed check to deepseek-r1:1.5b
            st.warning(
                "WARNING: 'deepseek-r1:1.5b' is not in the fetched model list."
            )  # Warning if model is missing
        return models
    except FileNotFoundError as e:
        st.error(
            f"Error: `ollama` command not found. Please ensure Ollama is installed and in your PATH. Details: {e}"
        )
        return []
    except subprocess.CalledProcessError as e:
        st.error(
            f"Error listing Ollama models. Is Ollama server running? Details: {e}"
        )
        st.error(f"Subprocess error output: {e.stderr}")  # Print stderr output for subprocess errors
        st.error(
            f"Subprocess error return code: {e.returncode}"
        )  # Print return code
        return []
    except Exception as e:
        st.error(
            f"An unexpected error occurred while fetching Ollama models: {e}. Details: {e}"
        )
        return []


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

    ollama_model_list = get_ollama_models()  # Fetch models from Ollama

    if ollama_model_list:  # Only show config if models are fetched successfully
        st.write("DEBUG: ollama_model_list:", ollama_model_list)  # DEBUG PRINT - ADD THIS LINE
        with st.expander(
            "Story Planner Agent Configuration"
        ):  # Using expanders for better UI organization
            st.subheader("Story Planner Agent")
            story_planner_model_selection = st.selectbox(
                "Model",
                ollama_model_list,
                index=ollama_model_list.index(
                    st.session_state["story_planner_model_selection"]
                )
                if st.session_state["story_planner_model_selection"] in ollama_model_list
                else 0,
                key="story_planner_model_selection",
            )  # Use dynamic model list
            story_planner_temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.05,
                key="story_planner_temp",
            )
            story_planner_max_tokens = st.number_input(
                "Max Tokens",
                min_value=500,
                max_value=30000,
                value=3500,
                step=100,
                key="story_planner_tokens",
            )
            story_planner_top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=0.95,
                step=0.05,
                key="story_planner_top_p",
            )
            story_planner_context_window = st.number_input(
                "Context Window",
                min_value=2048,
                max_value=131072,
                value=8192,
                step=1024,
                key="story_planner_context",
            )  # INCREASED max_value and adjusted value

        with st.expander(
            "Writer Agent Configuration"
        ):  # Expander for Writer Agent config
            st.subheader("Writer Agent")
            writer_model_selection = st.selectbox(
                "Model",
                ollama_model_list,
                index=ollama_model_list.index(
                    st.session_state["writer_model_selection"]
                )
                if st.session_state["writer_model_selection"] in ollama_model_list
                else 0,
                key="writer_model_selection",
            )  # Use dynamic model list, corrected variable name
            writer_temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.8,
                step=0.05,
                key="writer_temp",
            )
            writer_max_tokens = st.number_input(
                "Max Tokens",
                min_value=500,
                max_value=30000,
                value=3500,
                step=100,
                key="writer_tokens",
            )
            writer_top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=0.95,
                step=0.05,
                key="writer_top_p",
            )
            writer_context_window = st.number_input(
                "Context Window",
                min_value=2048,
                max_value=131072,
                value=8192,
                step=1024,
                key="writer_context",
            )
    else:
        st.warning(
            "Could not fetch model list from Ollama. Ensure Ollama is running and accessible."
        )


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