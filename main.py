# --- main.py ---
import os
import json  # For tool arguments
from agents.story_planner import StoryPlanner
from agents.test_agent import TestAgent # Keep for comparison
from tools.ywriter_tools import WriteProjectNoteTool
from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.novel import Novel
import yaml # Import PyYAML to load config

if __name__ == "__main__":
    # --- Load Configuration from config.yaml ---
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
    genre_selection = config.get("genre", "literary_fiction") # Get genre, default to literary_fiction
    prompts_file_path = config.get("prompts_file", "config/prompts.yaml") # Get prompts file path

    # --- Load Prompts from prompts.yaml ---
    with open(prompts_file_path, "r") as prompts_file:
        prompts_config = yaml.safe_load(prompts_file)

    # --- Story Planner Agent ---
    story_planner = StoryPlanner(
        base_url="http://localhost:11434",
        model="deepseek-r1:1.5b",  # Using deepseek-r1:1.5b for StoryPlanner
        temperature=0.7,
        context_window=65536,
        max_tokens=3500,
        top_p=0.95,
        prompts=prompts_config, # Pass prompts config
        genre=genre_selection # Pass genre selection
    )

    # --- Task for Story Planner Agent ---
    story_planning_task_description = "Plan a story arc for a literary fiction novel."
    print(
        f"\n--- Sending task to Story Planner: ---\n'{story_planning_task_description}'\n--- Story Arc from Story Planner: ---\n"
    )
    story_arc_text = story_planner.plan_story_arc(  # Get story arc text
        num_chapters=12,
        additional_instructions="Focus on character development and themes of isolation and redemption."
    )
    print(story_arc_text)  # Print story arc to console

    # --- Output Story Arc to Text File (Simplified) ---
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, "story_arc.txt")

    try:
        with open(output_file_path, "w", encoding="utf-8") as outfile:
            outfile.write(f"Genre: {genre_selection}\n\n") # Write genre to file
            outfile.write(story_arc_text)
        print(f"\n--- Story Arc saved to: {output_file_path} ---")
    except Exception as e:
        print(f"--- Error writing Story Arc to file: {e} ---")