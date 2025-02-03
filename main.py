# --- main.py ---
import os
import json  # For tool arguments
from agents.story_planner import StoryPlanner
from agents.test_agent import TestAgent # Keep for comparison
from tools.ywriter_tools import WriteProjectNoteTool
from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.novel import Novel
import yaml
import importlib.util  # ADDED IMPORT for dynamic module loading
import logging # ADDED IMPORT for logging

logger = logging.getLogger(__name__) # ADDED LOGGER

def load_genre_config(genre_name):
    """Load genre-specific configuration from Python files."""
    genre_config = {}
    config_path = f"config/genres/{genre_name}.py"  # Assuming genres are in config/genres/

    if not os.path.exists(config_path):
        logger.warning(f"Genre configuration file not found: {config_path}")
        return genre_config  # Return empty config if not found

    try:
        spec = importlib.util.spec_from_file_location("genre_config", config_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Extract all uppercase variables as configuration
        genre_config = {
            name: getattr(module, name)
            for name in dir(module)
            if name.isupper() and not name.startswith('_')
        }
        logger.info(f"Loaded genre config from: {config_path}")
    except Exception as e:
        logger.error(f"Error loading genre configuration from {config_path}: {e}")

    return genre_config


if __name__ == "__main__":
    # --- Load Configuration from config.yaml ---
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
    genre_selection = config.get("genre", "literary_fiction")
    prompts_dir_path = config.get("prompts_dir", "config/prompts")

    # --- Story Planner Agent ---
    story_planner = StoryPlanner(
        base_url="http://localhost:11434",
        model="deepseek-r1:32b",  # Using deepseek-r1:1.5b for StoryPlanner
        temperature=0.7,
        context_window=65536,
        max_tokens=10000,
        top_p=0.95,
        prompts_dir=prompts_dir_path,
        genre=genre_selection
    )

    # --- Task for Story Planner Agent ---
    story_planning_task_description = "Plan a story arc for a literary fiction novel."
    print(
        f"\n--- Sending task to Story Planner: ---\n'{story_planning_task_description}'\n--- Story Arc from Story Planner: ---\n"
    )
    story_arc_stream = story_planner.plan_story_arc(  # Get story arc stream
        genre="literary_fiction",
        num_chapters=12,
        additional_instructions="Focus on character development and themes of isolation and redemption.",
    )
    for chunk in story_arc_stream: # Iterate through the stream and print chunks
        print(chunk, end="", flush=True)

    # --- Output Story Arc to Text File (Simplified) ---
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, "story_arc.txt")

    try:
        with open(output_file_path, "w", encoding="utf-8") as outfile:
            outfile.write(f"Genre: {genre_selection}\n\n")
            story_arc_stream = story_planner.plan_story_arc(  # Re-run to get full text for file
                genre="literary_fiction", num_chapters=12, additional_instructions="Focus on character development and themes of isolation and redemption."
            )
            for chunk in story_arc_stream: # Re-iterate through stream and write to file
                outfile.write(chunk)
        print(f"\n--- Story Arc saved to: {output_file_path} ---")
    except Exception as e:
        print(f"--- Error writing Story Arc to file: {e} ---")

    # --- Test load_genre_config ---
    genre_name_test = "literary_fiction" # Or another genre you have
    genre_test_config = load_genre_config(genre_name_test)

    if genre_test_config:
        print(f"\n--- Loaded Genre Config for: {genre_name_test} ---")
        for key, value in genre_test_config.items():
            print(f"{key}: {value}")
    else:
        print(f"\n--- Failed to Load Genre Config for: {genre_name_test} ---")