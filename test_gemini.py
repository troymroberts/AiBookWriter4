#!/usr/bin/env python3
"""
Quick test to verify Gemini API integration works
"""

from config.llm_config import LLMConfig
from crewai import Agent, Task, Crew, Process

def test_gemini():
    print("=" * 80)
    print("TESTING GEMINI API INTEGRATION")
    print("=" * 80)

    # Initialize config
    config = LLMConfig()

    # Get Gemini configuration
    gemini_config = config.get_provider_config()
    print(f"\nProvider: {gemini_config.get('provider')}")
    print(f"Model: {gemini_config.get('model')}")
    print(f"Temperature: {gemini_config.get('temperature')}")

    # Create a simple agent with Gemini
    print("\nCreating test agent with Gemini...")
    llm = config.create_llm()

    test_agent = Agent(
        role="Test Agent",
        goal="Generate a short creative sentence",
        backstory="You are a test agent verifying API connectivity",
        llm=llm,
        verbose=True
    )

    # Create a simple task
    test_task = Task(
        description="Write a single creative sentence about space exploration.",
        agent=test_agent,
        expected_output="A single creative sentence"
    )

    # Run the crew
    print("\nExecuting test task...")
    crew = Crew(
        agents=[test_agent],
        tasks=[test_task],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()

    print("\n" + "=" * 80)
    print("✅ GEMINI TEST SUCCESSFUL")
    print("=" * 80)
    print(f"\nResult: {result}")
    print("\nGemini is working! You can now run the full workflow.")

    return result

if __name__ == "__main__":
    test_gemini()
