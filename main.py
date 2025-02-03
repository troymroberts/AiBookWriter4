# --- main.py ---
from agents.test_agent import TestAgent
from agents.story_planner import StoryPlanner

if __name__ == "__main__":
    # --- Test Agent (optional, for comparison) ---
    test_agent = TestAgent(
        base_url="http://localhost:11434",
        model="qwen2.5:1.5b",
        temperature=0.8,
        context_window=65536
    )

    # --- Story Planner Agent ---
    story_planner = StoryPlanner(
        base_url="http://localhost:11434",
        model="deepseek-r1:1.5b", # Let's try a different model for the planner
        temperature=0.7,
        context_window=65536,
        max_tokens=3500,
        top_p=0.95
    )

    # --- Test Task for Test Agent (Non-Streaming) ---
    test_task_prompt = "Hello, Test Agent! What is your purpose? (Non-Streaming)"
    print(f"--- Sending prompt to Test Agent (Non-Streaming): ---\n'{test_task_prompt}'\n--- Response from Test Agent (Non-Streaming): ---")
    response_test_agent = test_agent.run_test_task(test_task_prompt)
    print(response_test_agent)

    # --- Test Task for Test Agent (Streaming) ---
    test_task_prompt_stream = "Hello, Test Agent! Tell me a longer story, please. (Streaming)"
    print(f"\n--- Sending prompt to Test Agent (Streaming): ---\n'{test_task_prompt_stream}'\n--- Response from Test Agent (Streaming): ---")
    print("Streaming output:") # Indicate streaming output
    test_agent.run_test_task_stream(test_task_prompt_stream) # Call the streaming method

    # --- Task for Story Planner Agent (Non-Streaming - Keep for now) ---
    story_planning_task_description = "Plan a story arc for a literary fiction novel."
    print(f"\n--- Sending task to Story Planner (Non-Streaming): ---\n'{story_planning_task_description}'\n--- Story Arc from Story Planner (Non-Streaming): ---")
    story_arc = story_planner.plan_story_arc(
        genre="literary fiction",
        num_chapters=12,
        additional_instructions="Focus on character development and themes of isolation and redemption."
    )
    print(story_arc)