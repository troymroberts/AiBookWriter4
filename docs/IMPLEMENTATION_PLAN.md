# AiBookWriter4 Implementation Plan

**Date:** 2026-01-08
**Based on:** SPEC.md v2.0 + Latest CrewAI Features
**Status:** Planning Complete

---

## New CrewAI Features → SPEC.md Mapping

| CrewAI Feature | SPEC.md Requirement | Implementation |
|----------------|---------------------|----------------|
| **Flows** | Supervisor Agent orchestration (§2.2) | `BookWriterFlow` with `@start`, `@listen`, `@router` |
| **HITL** | User-Configurable Checkpoints (§7.1) | Review gates via `humanInputWebhook` |
| **Streaming** | Dashboard Progress Display (§9.2) | Real-time Streamlit updates |
| **A2A** | Agent Delegation in Editorial Loop | Optional for specialized agents |
| **Memory** | RAG System (§3.1) | `memory=True` on Crew (ChromaDB) |
| **Hierarchical Process** | Supervisor Pattern | `Process.hierarchical` with `manager_llm` |

---

## Architecture: BookWriterFlow

Using CrewAI Flows for the supervisor pattern:

```python
from crewai.flow.flow import Flow, start, listen, router
from pydantic import BaseModel

class BookState(BaseModel):
    """Tracks state across the entire book generation process"""
    # Project info
    genre: str = ""
    premise: str = ""
    num_chapters: int = 25

    # Phase tracking
    current_phase: str = "foundation"
    chapters_completed: int = 0

    # Content storage
    story_arc: str = ""
    characters: list = []
    locations: list = []
    lore: dict = {}
    chapter_outlines: list = []
    chapters: list = []

    # Quality metrics
    editorial_iterations: int = 0
    convergence_score: float = 1.0  # < 0.05 = converged

    # Review gates
    awaiting_approval: bool = False
    user_feedback: str = ""

class BookWriterFlow(Flow[BookState]):
    stream = True  # Enable streaming for UI

    @start()
    def foundation_phase(self):
        """Phase 1: Story planning and arc creation"""
        # StoryPlanner crew
        ...

    @listen(foundation_phase)
    def world_building_phase(self, story_arc):
        """Phase 2: Characters, locations, lore (parallel)"""
        # CharacterCreator, LocationDesigner, LoreBuilder crews
        ...

    @listen(world_building_phase)
    def structure_phase(self, world_data):
        """Phase 3: Plot architecture and scene breakdown"""
        # PlotArchitect, TimelineManager crews
        ...

    @router(structure_phase)
    def check_review_gate(self):
        """Router: Check if user review is needed before writing"""
        if self.state.awaiting_approval:
            return "await_approval"
        return "writing"

    @listen("writing")
    def writing_phase(self):
        """Phase 4: Scene-by-scene writing with editorial loop"""
        # Writer → Critic → Reviser → Continuity loop
        ...

    @router(writing_phase)
    def check_convergence(self):
        """Router: Check editorial loop convergence"""
        if self.state.convergence_score < 0.05:
            return "chapter_complete"
        elif self.state.editorial_iterations >= 5:
            return "chapter_complete"  # Max iterations
        return "editorial_loop"

    @listen("editorial_loop")
    def editorial_refinement(self):
        """Editorial loop: Critic → Reviser → Continuity"""
        ...

    @listen("chapter_complete")
    def next_chapter_or_complete(self):
        """Move to next chapter or finish"""
        ...
```

---

## Phase 1: Core Pipeline Implementation

### 1.1 Create BookWriterFlow (flows/book_writer_flow.py)

```
flows/
├── __init__.py
├── book_writer_flow.py      # Main flow orchestrator
├── state.py                  # BookState Pydantic model
└── crews/
    ├── foundation_crew.py    # StoryPlanner crew
    ├── world_building_crew.py # Character, Location, Lore crews
    ├── structure_crew.py     # Plot, Timeline crews
    ├── writing_crew.py       # Writer crew
    └── editorial_crew.py     # Critic, Reviser, Continuity crews
```

### 1.2 Streaming Integration with Streamlit

```python
# app.py integration
async def run_book_generation():
    flow = BookWriterFlow()
    streaming = await flow.kickoff_async(inputs={
        "genre": st.session_state.genre,
        "premise": st.session_state.premise,
        "num_chapters": st.session_state.num_chapters
    })

    progress_bar = st.progress(0)
    output_area = st.empty()

    async for chunk in streaming:
        # Update UI in real-time
        if chunk.chunk_type == StreamChunkType.TEXT:
            output_area.markdown(chunk.content)

        # Update progress
        progress = flow.state.chapters_completed / flow.state.num_chapters
        progress_bar.progress(progress)
```

### 1.3 HITL Review Gates

```python
# Review gate implementation
@listen("await_approval")
def await_user_approval(self):
    """Pause for user review"""
    # In Streamlit, this shows approval UI
    # In API mode, this triggers webhook
    self.state.awaiting_approval = True
    return "Awaiting user approval..."

# Resume after approval
def resume_after_approval(self, feedback: str, approved: bool):
    self.state.user_feedback = feedback
    self.state.awaiting_approval = False
    if approved:
        return self.writing_phase()
    else:
        # Re-run previous phase with feedback
        return self.structure_phase()
```

---

## Phase 2: World Building Crews

### 2.1 Parallel World Building

```python
@listen(foundation_phase)
def world_building_phase(self, story_arc):
    """Run world-building crews in parallel"""
    from crewai import Crew, Process

    # These can run in parallel
    character_crew = Crew(
        agents=[character_designer],
        tasks=[character_tasks],
        process=Process.sequential,
        memory=True  # RAG enabled
    )

    location_crew = Crew(
        agents=[location_designer],
        tasks=[location_tasks],
        process=Process.sequential,
        memory=True
    )

    lore_crew = Crew(
        agents=[lore_keeper],
        tasks=[lore_tasks],
        process=Process.sequential,
        memory=True
    )

    # Execute in parallel using asyncio
    results = await asyncio.gather(
        character_crew.kickoff_async(inputs={"story_arc": story_arc}),
        location_crew.kickoff_async(inputs={"story_arc": story_arc}),
        lore_crew.kickoff_async(inputs={"story_arc": story_arc})
    )

    self.state.characters = results[0].raw
    self.state.locations = results[1].raw
    self.state.lore = results[2].raw
```

---

## Phase 3: Editorial Loop with Convergence

### 3.1 Convergence Detection

```python
def calculate_convergence(self, previous_text: str, current_text: str) -> float:
    """Calculate word-level edit distance as percentage"""
    import difflib

    prev_words = previous_text.split()
    curr_words = current_text.split()

    # Use SequenceMatcher for efficient diff
    matcher = difflib.SequenceMatcher(None, prev_words, curr_words)
    similarity = matcher.ratio()

    # Return change percentage (1 - similarity)
    return 1.0 - similarity

@listen("editorial_loop")
def editorial_refinement(self):
    """Run editorial loop until convergence"""
    previous_chapter = self.state.chapters[-1]

    # Critic review
    critique = critic_crew.kickoff(inputs={"chapter": previous_chapter})

    # Reviser applies feedback
    revised = reviser_crew.kickoff(inputs={
        "chapter": previous_chapter,
        "critique": critique.raw
    })

    # Continuity check
    continuity_result = continuity_crew.kickoff(inputs={
        "chapter": revised.raw,
        "canon": self.state.lore
    })

    # Calculate convergence
    self.state.convergence_score = self.calculate_convergence(
        previous_chapter,
        continuity_result.raw
    )
    self.state.editorial_iterations += 1
    self.state.chapters[-1] = continuity_result.raw

    return continuity_result.raw
```

---

## Canon System Integration

### 4.1 Canon Database with ChromaDB

```python
from crewai.rag.config.utils import set_rag_config, get_rag_client
from crewai.rag.chromadb.config import ChromaDBConfig

# Initialize Canon system
set_rag_config(ChromaDBConfig())
canon_client = get_rag_client()

# Create collections for different canon types
canon_client.create_collection(collection_name="characters")
canon_client.create_collection(collection_name="locations")
canon_client.create_collection(collection_name="lore")
canon_client.create_collection(collection_name="timeline")

# Add canon entry
def add_canon_entry(collection: str, fact: dict):
    """Add a canonical fact to the database"""
    canon_client.add_documents(
        collection_name=collection,
        documents=[{
            "id": fact["fact_id"],
            "content": fact["content"],
            "metadata": {
                "established_in": fact["scene_id"],
                "version": fact.get("version", "main"),
                "supersedes": fact.get("supersedes", None)
            }
        }]
    )

# Check for contradictions
def check_canon_violation(collection: str, proposed_fact: str) -> list:
    """Check if proposed content contradicts established canon"""
    results = canon_client.search(
        collection_name=collection,
        query=proposed_fact,
        limit=5
    )
    # Return potential contradictions for review
    return results
```

---

## File Structure (New)

```
AiBookWriter4/
├── flows/                      # NEW: CrewAI Flows
│   ├── __init__.py
│   ├── book_writer_flow.py     # Main orchestrator
│   ├── state.py                # BookState model
│   └── crews/
│       ├── foundation_crew.py
│       ├── world_building_crew.py
│       ├── structure_crew.py
│       ├── writing_crew.py
│       └── editorial_crew.py
├── canon/                      # NEW: Canon system
│   ├── __init__.py
│   ├── canon_manager.py        # Canon CRUD operations
│   └── contradiction_checker.py
├── agents/                     # EXISTING: Keep agents_extended.py
├── tasks/                      # EXISTING: Keep tasks_extended.py
├── config/                     # EXISTING: Keep genre configs
├── app.py                      # UPDATE: Integrate with Flow
└── ...
```

---

## Implementation Order

### Week 1: Foundation
1. ✅ Update requirements.txt
2. [ ] Create `flows/state.py` with BookState model
3. [ ] Create `flows/book_writer_flow.py` skeleton
4. [ ] Create `flows/crews/foundation_crew.py`
5. [ ] Test basic flow execution

### Week 2: World Building + Structure
1. [ ] Create parallel world-building crews
2. [ ] Implement structure crews
3. [ ] Add memory/RAG to all crews
4. [ ] Test phases 1-3

### Week 3: Writing + Editorial
1. [ ] Implement writing crew with streaming
2. [ ] Implement editorial loop
3. [ ] Add convergence detection
4. [ ] Test full chapter generation

### Week 4: HITL + Polish
1. [ ] Add review gate UI in Streamlit
2. [ ] Implement canon system
3. [ ] Add yWriter export
4. [ ] End-to-end testing

---

## Success Criteria (from SPEC.md §16)

- [ ] Generate coherent 50+ chapter novel from premise
- [ ] Maintain character consistency across all chapters
- [ ] No lore/timeline contradictions in output
- [ ] Support all four priority genres
- [ ] Export valid yWriter7 files
- [ ] Resume from checkpoint after interruption
- [ ] UI remains responsive during generation
- [ ] RAG retrieval completes in < 2 seconds
