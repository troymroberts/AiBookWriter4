#!/usr/bin/env python3
"""
Test editor agent with RAG on a realistic scene.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agents.editor import Editor, EditorConfig
from crewai import Task, Crew, Process

def test_editor_with_rag():
    """Test if editor can handle a realistic scene with RAG enabled."""

    print("=" * 80)
    print("TESTING EDITOR WITH RAG")
    print("=" * 80)

    # Create editor with RAG enabled
    editor_config = EditorConfig(
        temperature=0.5,
        max_tokens=32000,
        enable_rag_continuity=True
    )

    editor = Editor(config=editor_config)

    # Use a realistic scene (shorter than actual scenes to test)
    test_scene = """Dr. Elara Myles stood in the Command Center, studying the holographic display of Xylo-7. Commander Marcus Voss briefed her on the mission.

"The situation is critical," Voss said. "We need your expertise to assess the environmental crisis."

Elara nodded. "When do we leave?"

"Within the hour. Lieutenant Sarah Chen and Dr. Raj Patel will assist you."

Elara felt a surge of determination. This mission could save lives."""

    # Create editorial task
    task = Task(
        description=f"""Review and refine this scene:

        Title: Test Scene
        Current Draft:
        {test_scene}

        Improve:
        - Clarity and flow
        - Dialogue naturalness
        - Pacing and tension

        OUTPUT FORMAT:
        Output the complete refined narrative text only. Do NOT include:
        - Editorial comments or meta-commentary
        - Lists of changes made
        - Explanations or feedback

        Output the full polished prose immediately.""",
        agent=editor,
        expected_output="Complete refined narrative prose"
    )

    # Create crew
    crew = Crew(
        agents=[editor],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    print("\nStarting editorial refinement with RAG enabled...\n")
    print(f"Editor has {len(editor.tools)} tools available")
    print(f"Tools: {[tool.__class__.__name__ for tool in editor.tools]}\n")

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
        print("\n✅ SUCCESS: Editor generated refined prose with RAG!")
        return True
    else:
        print("\n❌ FAILED: Editor returned empty or too short response")
        return False

if __name__ == "__main__":
    try:
        success = test_editor_with_rag()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
