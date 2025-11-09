#!/usr/bin/env python3
"""
Test if WRITER agent can edit text with RAG (to isolate if it's about editing vs writing).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agents.writer import Writer, WriterConfig
from crewai import Task, Crew, Process

def test_writer_editing():
    """Test if writer agent can refine existing text with RAG enabled."""

    print("=" * 80)
    print("TESTING WRITER AGENT DOING EDITORIAL TASK")
    print("=" * 80)

    # Create writer with RAG enabled
    writer_config = WriterConfig(
        temperature=0.7,
        max_tokens=4000,
        enable_rag=True
    )

    writer = Writer(config=writer_config)

    # Same scene as editor test
    test_scene = """Dr. Elara Myles stood in the Command Center, studying the holographic display of Xylo-7. Commander Marcus Voss briefed her on the mission.

"The situation is critical," Voss said. "We need your expertise to assess the environmental crisis."

Elara nodded. "When do we leave?"

"Within the hour. Lieutenant Sarah Chen and Dr. Raj Patel will assist you."

Elara felt a surge of determination. This mission could save lives."""

    # Ask writer to EDIT (not write new)
    task = Task(
        description=f"""Refine and improve this existing scene:

        {test_scene}

        Improve the clarity, dialogue, and sensory details.

        OUTPUT FORMAT:
        Output the complete refined narrative text only.
        Start writing immediately.""",
        agent=writer,
        expected_output="Complete refined narrative prose"
    )

    # Create crew
    crew = Crew(
        agents=[writer],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\nWriter has {len(writer.tools)} tools available")
    print(f"Tools: {[tool.__class__.__name__ for tool in writer.tools]}\n")

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
        print("\n✅ SUCCESS: Writer did editorial task with RAG!")
        return True
    else:
        print("\n❌ FAILED: Writer returned empty response")
        return False

if __name__ == "__main__":
    try:
        success = test_writer_editing()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
