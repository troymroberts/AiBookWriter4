# --- main.py ---
import os
from agents.test_agent import TestAgent
from ywriter7.model.project_note import ProjectNote # Import pywriter7 ProjectNote

if __name__ == "__main__":
    # --- Test Agent ---
    test_agent = TestAgent(
        base_url="http://localhost:11434",
        model="qwen2.5:1.5b",
        temperature=0.8,
        context_window=65536
    )

    # --- Define Test Task: Generate a Scene Description ---
    test_task_prompt = "Describe a bustling market scene in a fantasy novel, about 5 sentences long."

    print(f"--- Sending prompt to Test Agent: ---\n'{test_task_prompt}'\n--- Response from Test Agent: ---")
    agent_output = test_agent.run_test_task(test_task_prompt) # Get NON-STREAMING output for simplicity

    print(agent_output) # Print to console for verification

    # --- Create pywriter7 ProjectNote ---
    project_note = ProjectNote()
    project_note.title = "Market Scene Description (Agent Generated)" # Set a title
    project_note.desc = agent_output # Set the agent's output as the description

    # --- Output to File in 'output/' directory ---
    output_dir = "output" # Define output directory
    os.makedirs(output_dir, exist_ok=True) # Create output directory if it doesn't exist
    output_file_path = os.path.join(output_dir, "market_scene_description.txt") # Define output file path

    try:
        with open(output_file_path, "w", encoding="utf-8") as outfile:
            outfile.write(f"Project Note Title: {project_note.title}\n\n") # Write title
            outfile.write(project_note.desc) # Write the description (agent output)
        print(f"\n--- Project Note saved to: {output_file_path} ---") # Confirmation message
    except Exception as e:
        print(f"--- Error writing to file: {e} ---")