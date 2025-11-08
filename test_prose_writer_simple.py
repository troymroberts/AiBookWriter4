#!/usr/bin/env python3
"""
Simple test for prose writer agent to verify it can generate output.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agents.writer import Writer, WriterConfig
from crewai import Task, Crew, Process

def test_prose_writer():
    """Test if prose writer can generate a simple scene."""

    print("=" * 80)
    print("TESTING PROSE WRITER")
    print("=" * 80)

    # Create writer with simple config
    writer_config = WriterConfig(
        temperature=0.8,
        max_tokens=4000,
        enable_rag=False  # Disabled for testing
    )

    writer = Writer(config=writer_config)

    # Create a simple test task
    task = Task(
        description="""Write a short scene (500-800 words):

        Scene: A scientist receives an urgent distress signal

        Write narrative prose showing:
        - The scientist (Dr. Elara) at her workstation
        - The moment she receives the signal
        - Her reaction and decision to investigate

        Use third person past tense. Start writing immediately.""",
        agent=writer,
        expected_output="500-800 words of narrative prose"
    )

    # Create crew
    crew = Crew(
        agents=[writer],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\nStarting prose generation...\n")

    # Execute
    result = crew.kickoff()

    print("\n" + "=" * 80)
    print("RESULT:")
    print("=" * 80)
    print(result)
    print("\n" + "=" * 80)
    print(f"Length: {len(str(result))} characters")
    print("=" * 80)

    if result and len(str(result)) > 100:
        print("\n✅ SUCCESS: Writer generated prose!")
        return True
    else:
        print("\n❌ FAILED: Writer returned empty or too short response")
        return False

if __name__ == "__main__":
    try:
        success = test_prose_writer()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
