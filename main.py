# --- main.py ---
from agents.test_agent import TestAgent

if __name__ == "__main__":
    # --- Instantiate Test Agent with direct parameters ---
    test_agent = TestAgent(
        base_url="http://localhost:11434",  # Or "http://10.1.1.47:11434" if that's your server
        model="qwen2.5:1.5b",
        temperature=0.8,
        context_window=8192 # Set context window directly here
    )

    # --- Define Test Task ---
    test_task_prompt = "Hello, Ollama! What is the capital of Spain?"

    # --- Run the Test Task ---
    print(f"--- Sending prompt to Test Agent: ---\n'{test_task_prompt}'\n--- Response from Test Agent: ---")
    response = test_agent.run_test_task(test_task_prompt)
    print(response)

    test_task_prompt_2 = "Could you tell me a short joke?"
    print(f"\n--- Sending prompt to Test Agent: ---\n'{test_task_prompt_2}'\n--- Response from Test Agent: ---")
    response_2 = test_agent.run_test_task(test_task_prompt_2)
    print(response_2)