import streamlit as st
import yaml  # To load genre config
import os  # To list genre files
from agents.story_planner import StoryPlanner  # Import StoryPlanner
import io  # To capture stdout for display

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

    if st.button("Plan Story Arc"):
        st.write(f"Planning story arc for genre: {genre_selection}, chapters: {num_chapters}")
        st.write(f"Initial Prompt: {initial_prompt}")
        st.write(f"Additional Instructions: {additional_instructions}")

        # --- Load Configuration from config.yaml (for base_url, model, prompts_dir) ---
        with open("config.yaml", "r") as config_file:
            config_yaml = yaml.safe_load(config_file)
        prompts_dir_path = config_yaml.get("prompts_dir", "config/prompts")
        base_url_config = config_yaml['model_list'][0]['litellm_params']['base_url'] # Get base_url
        story_planner_model = "deepseek-r1:1.5b" # Model for StoryPlanner - make configurable later

        # --- Initialize Story Planner Agent ---
        story_planner = StoryPlanner(
            base_url=base_url_config,
            model=story_planner_model,
            temperature=0.7,
            context_window=65536,
            max_tokens=3500,
            top_p=0.95,
            prompts_dir=prompts_dir_path,
            genre=genre_selection,
            num_chapters=num_chapters # Use num_chapters from UI
        )

        # --- Plan Story Arc and Display Streamed Output ---
        st.subheader("Story Arc Output:")
        output_placeholder = st.empty()  # Placeholder to update with streamed output
        full_output = "" # To store full output for later use if needed

        story_arc_stream = story_planner.plan_story_arc(
            genre=genre_selection,
            num_chapters=num_chapters, # Use num_chapters from UI
            additional_instructions=additional_instructions
        )

        for chunk in story_arc_stream:
            full_output += chunk
            output_placeholder.text(full_output) # Update placeholder with accumulated output

        st.success("Story arc planning complete!")


with tab2:
    st.header("Agent Configuration")
    # Add widgets for agent model and parameter configuration here

with tab3:
    st.header("Process Monitor")
    # Add area to monitor output and running state here

with tab4:
    st.header("Output Inspection")
    # Add area to inspect final output here

if __name__ == '__main__':
    pass