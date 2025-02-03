# --- main.py ---
import os
import json  # For tool arguments
from agents.story_planner import StoryPlanner
from tools.ywriter_tools import WriteProjectNoteTool # Import the yWriter tool
from ywriter7.yw.yw7_file import Yw7File # For creating a dummy yw7 file if needed

if __name__ == "__main__":
    # --- Ensure output directory exists ---
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # --- Define test .yw7 file path ---
    test_yw7_file = os.path.join(output_dir, "test_project_story_arc.yw7")

    # --- Create a dummy .yw7 file if it doesn't exist ---
    if not os.path.exists(test_yw7_file):
        print(f"Creating dummy yWriter project file: {test_yw7_file}")
        yw7_file = Yw7File(test_yw7_file)
        yw7_file.write()  # Create a minimal valid .yw7 file
    else:
        print(f"Using existing yWriter project file: {test_yw7_file}")

    # --- Story Planner Agent ---
    story_planner = StoryPlanner(
        base_url="http://localhost:11434",
        model="deepseek-r1:1.5b",  # Using deepseek-r1:1.5b for StoryPlanner
        temperature=0.7,
        context_window=65536,
        max_tokens=6500,
        top_p=0.95,
    )

    # --- Task for Story Planner Agent ---
    story_planning_task_description = "Plan a story arc for a literary fiction novel."
    print(
        f"\n--- Sending task to Story Planner: ---\n'{story_planning_task_description}'\n--- Story Arc from Story Planner: ---\n"
    )
    story_arc_text = story_planner.plan_story_arc(  # Get story arc text
        genre="literary fiction",
        num_chapters=12,
        additional_instructions="Focus on character development and themes of isolation and redemption.",
    )
    print(story_arc_text)  # Print story arc to console

    # --- Write Story Arc to yWriter Project Note using WriteProjectNoteTool ---
    write_note_tool = WriteProjectNoteTool() # Instantiate the tool

    # --- Prepare arguments for the tool as a JSON string ---
    tool_args = {
        "yw7_path": test_yw7_file,
        "title": "Story Arc (Agent Generated)",
        "content": story_arc_text,
    }
    tool_args_json = json.dumps(tool_args) # Convert arguments to JSON string

    print("\n--- Calling WriteProjectNoteTool... ---")
    tool_output = write_note_tool._run(yw7_path=test_yw7_file, title="Story Arc (Agent Generated)", content=story_arc_text) # Directly run the tool
    print(f"--- WriteProjectNoteTool Output: ---\n{tool_output}") # Print tool output

    print(f"\n--- yWriter project file updated: {test_yw7_file} ---")