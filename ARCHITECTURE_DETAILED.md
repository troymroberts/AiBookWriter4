# AiBookWriter4 Architecture Analysis

## Overview

AiBookWriter4 is a multi-agent AI-powered novel generation system built on **CrewAI**, using **yWriter7** for project file management and **ChromaDB** for RAG (Retrieval-Augmented Generation). The system orchestrates multiple specialized agents through a workflow pipeline to generate complete novels with characters, settings, plots, and prose.

---

## 1. WORKFLOW SYSTEM

### Main Workflow: `test_complete_workflow.py`

The workflow is organized into **8 sequential steps**:

```
Step 1: Story Planning        → Create 3-act story arc with character/plot arcs
Step 2: Character Creation    → Create 4-5 detailed character profiles
Step 3: Location Creation     → Build 4-5 immersive locations with descriptions
Step 4: Chapter Outlining     → Outline all chapters with scene structure
Step 5: Scene Structure       → Extract goal/conflict/outcome for each scene
Step 6: Prose Writing         → Generate 2000-3000 words per scene
Step 7: Editorial Refinement  → Review and polish all scenes
Step 8: RAG Sync              → Sync final novel to knowledge base
```

### Key Workflow Features

- **Sequential Execution**: Each step depends on outputs from previous steps
- **Crew-based Orchestration**: Uses CrewAI's `Crew` and `Task` for agent coordination
- **CrewAI Process**: `Process.sequential` ensures ordered execution
- **Output Streaming**: Agents use verbose=True for real-time feedback
- **State Persistence**: 
  - yWriter7 file (`.yw7`) serves as primary persistence mechanism
  - `AutoSyncYw7File` context manager ensures changes are saved
  - Manual checkpoint support via `WritingState` class

### Workflow Data Flow

```python
# Each step creates structured output → next step consumes it
story_arc_output 
  → character_creation (requires story context)
  → location_creation (requires story context)
  → outline_creation (uses story_arc_output)
  → scene_structure (parses outline_text into chapters/scenes)
  → prose_writing (iterates through all scenes)
  → editorial_refinement (refines written prose)
  → rag_sync (syncs completed novel to knowledge base)
```

---

## 2. AGENT STRUCTURE

### Core Agents (6 Primary)

#### 1. **StoryPlanner**
- **File**: `/home/user/AiBookWriter4/agents/story_planner.py`
- **Role**: Story Architect & Narrative Designer
- **Responsibilities**:
  - Three-act structure breakdown
  - Major plot points and turning points
  - Character arcs for main characters
  - Conflict escalation patterns
  - Thematic elements
- **Configuration**:
  - Temperature: 0.7 (balanced creativity)
  - Max Tokens: 12,288 (comprehensive output)
  - No RAG tools (creates foundation)
- **Instantiation Pattern**:
  ```python
  planner_config = StoryPlannerConfig(temperature=0.7, max_tokens=12288)
  story_planner = StoryPlanner(config=planner_config)
  ```

#### 2. **CharacterCreator**
- **File**: `/home/user/AiBookWriter4/agents/character_creator.py`
- **Role**: Character Development Specialist
- **Responsibilities**:
  - Create 4-5 multidimensional characters
  - Develop backstories, motivations, arcs
  - Check for character duplication (RAG)
  - Establish relationships
  - Parse structured character data (NAME, FULLNAME, AKA, DESC, BIO, NOTES, GOALS, MAJOR)
- **Tools**: 
  - SemanticCharacterSearchTool
  - GetCharacterDetailsTool
  - FindRelationshipsTool
  - GeneralKnowledgeSearchTool
- **Configuration**:
  - Temperature: 0.7
  - Max Tokens: 6,144

#### 3. **SettingBuilder**
- **File**: `/home/user/AiBookWriter4/agents/setting_builder.py`
- **Role**: World Builder & Setting Designer
- **Responsibilities**:
  - Create 4-5 immersive locations
  - Develop cultural/atmospheric details
  - Generate alternate names (AKA fields)
  - Environmental storytelling
- **Configuration**:
  - Temperature: 0.7
  - Max Tokens: 8,192
  - No RAG tools (creates content for RAG)

#### 4. **OutlineCreator**
- **File**: `/home/user/AiBookWriter4/agents/outline_creator.py`
- **Role**: Chapter & Scene Architect
- **Responsibilities**:
  - Generate chapter-by-chapter outlines
  - Scene-level breakdown (goal/conflict/outcome)
  - Narrative flow and pacing
  - Chapter progression (setup → climax → resolution)
- **Configuration**:
  - Temperature: 0.7
  - Max Tokens: 12,288

#### 5. **Writer**
- **File**: `/home/user/AiBookWriter4/agents/writer.py`
- **Role**: Prose Writer & Storyteller
- **Responsibilities**:
  - Generate 2000-3000 words per scene
  - Maintain character voice and consistency
  - Use RAG for continuity verification
  - Integrate dialogue and sensory details
- **Tools**: All 6 RAG tools for continuity checking
- **Configuration**:
  - Temperature: 0.8 (higher creativity)
  - Max Tokens: 32,000 (handles full scenes)

#### 6. **Editor**
- **File**: `/home/user/AiBookWriter4/agents/editor.py`
- **Role**: Editorial Specialist
- **Responsibilities**:
  - Review and refine chapter content
  - Verify character consistency (RAG)
  - Check prose quality and style
  - Ensure outline adherence
- **Tools**: All 6 RAG tools for continuity checking
- **Configuration**:
  - Temperature: 0.5 (lower for precision)
  - Max Tokens: 32,000

### Additional Agents (Defined in config.yaml but not heavily used)

- **Critic**: Literary analysis and quality feedback
- **Relationship Architect**: Character dynamics mapping
- **Lore Builder**: World-building and mythology
- **Memory Keeper**: Continuity tracking with RAG

### Agent Instantiation Pattern

All agents follow this pattern:

```python
class MyAgent(Agent):
    def __init__(self, config: MyAgentConfig):
        # 1. Get global LLM config
        llm_config = get_llm_config()
        agent_config = llm_config.get_agent_config("agent_name")
        
        # 2. Override with runtime config
        if config.temperature:
            agent_config['temperature'] = config.temperature
        if config.max_tokens:
            agent_config['max_tokens'] = config.max_tokens
        
        # 3. Create LLM instance
        llm = llm_config.create_llm("agent_name")
        
        # 4. Prepare tools (if RAG-enabled)
        tools = self._prepare_tools(config)
        
        # 5. Initialize CrewAI Agent
        super().__init__(
            role=agent_config.get('role', 'Default Role'),
            goal=agent_config.get('goal', 'Default Goal'),
            backstory=agent_config.get('backstory', 'Default Backstory'),
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=tools
        )
```

---

## 3. LLM INTEGRATION

### Configuration System: `config/llm_config.py`

#### LLMConfig Class

Central configuration manager supporting **8 LLM providers**:

1. **Ollama** - Local models
2. **Anthropic** - Claude models
3. **Gemini** - Google Gemini
4. **Groq** - Fast inference
5. **OpenRouter** - Multi-model aggregator
6. **DeepSeek** - Open source models
7. **Together AI** - Distributed inference
8. **OpenAI** - GPT models

#### Configuration Sources (Priority Order)

1. **Environment Variables** (highest priority)
   - `DEFAULT_LLM_PROVIDER` - which provider to use
   - `AGENT_[AGENT_NAME]_PROVIDER` - agent-specific provider override
   - Provider-specific keys: `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, etc.
   - Agent-specific models: `OLLAMA_MODEL_STORY_PLANNER`

2. **config.yaml** (second priority)
   ```yaml
   agents:
     story_planner:
       provider: "anthropic"  # Optional override
       model: "claude-3-5-sonnet-20241022"
       temperature: 0.7
       max_tokens: 12288
   ```

3. **Defaults** (lowest priority)
   - Provider: ollama
   - Model: varies by provider (e.g., "llama3.2" for Ollama, "claude-3-5-sonnet-20241022" for Anthropic)

#### Provider Configuration Examples

```python
# Get config for specific agent
config = get_llm_config()

# Returns dict with provider-specific settings:
{
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "api_key": "sk-ant-...",
    "temperature": 0.7,
    "max_tokens": 4096,
    "streaming": True
}
```

#### LLM Creation

```python
llm = config.create_llm("story_planner")
# Returns CrewAI LLM instance ready for use
```

#### Rate Limiting per Provider

Each provider has configured rate limits in `/home/user/AiBookWriter4/config/rate_limiter.py`:

```python
RATE_LIMITS = {
    "groq": {
        "llama-3.3-70b-versatile": {
            "tpm": 12000,    # Tokens per minute
            "rpm": 30,       # Requests per minute
            "tpd": 100000,   # Tokens per day
            "rpd": 1000,     # Requests per day
        }
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {
            "tpm": 40000,
            "rpm": 50,
        }
    }
    # ... etc
}
```

---

## 4. STATE MANAGEMENT & PERSISTENCE

### Primary State Container: yWriter7 File (`.yw7`)

The **yWriter7 XML format** serves as the source of truth:

```python
yw7_file = Yw7File(project_path)
yw7_file.novel = Novel()
yw7_file.novel.chapters[chapter_id] = chapter
yw7_file.novel.characters[char_id] = character
yw7_file.novel.locations[loc_id] = location
yw7_file.novel.scenes[scene_id] = scene
yw7_file.write()  # Persist to disk
```

### AutoSyncYw7File: Automatic Persistence

**File**: `/home/user/AiBookWriter4/rag/auto_sync.py`

Extends Yw7File with automatic RAG synchronization:

```python
# Use as context manager - auto-saves on exit
with AutoSyncYw7File(project_path) as yw7:
    yw7.novel.chapters[chapter_id] = chapter
    # Automatically calls yw7.write() and sync_to_rag() on context exit
```

**Features**:
- Transparent drop-in replacement for Yw7File
- Automatic write + RAG sync after modifications
- Manual sync control available
- Sync statistics returned

### WritingState Class: Checkpoint System

**File**: `/home/user/AiBookWriter4/tools/writing_state.py`

Simple JSON-based checkpoint persistence:

```python
state = WritingState("my_project")
state.current_chapter_id = "chapter_1"
state.completed_scenes = ["scene_1", "scene_2"]
state.save_checkpoint()  # Saves to "my_project_checkpoint.json"

# Later, recover state
state = WritingState("my_project")
state.load_checkpoint()  # Restores from JSON
```

**Tracked State**:
- `current_chapter_id` - which chapter being written
- `current_scene_id` - which scene being written
- `completed_chapters` - array of finished chapter IDs
- `completed_scenes` - array of finished scene IDs

### WritingProgress: Progress Tracking

**File**: `/home/user/AiBookWriter4/tools/writing_progress.py`

Tracks writing metrics and progress:

```python
progress = WritingProgress(total_chapters=10)

progress.start_chapter(chapter_1)
# ... write chapter ...
progress.complete_chapter(chapter_1)

# Get metrics
average_time = progress.get_average_chapter_time()
estimated_remaining = progress.estimate_completion_time()
summary = progress.get_progress_summary()
```

### RAG Vector Store: Semantic Memory

**File**: `/home/user/AiBookWriter4/rag/vector_store.py`

ChromaDB-based semantic search storage:

```python
vector_store = VectorStoreManager()

# Add story elements
vector_store.add_character("Alice", "Protagonist, young woman seeking redemption...")

# Search semantically
results = vector_store.search_characters("young female protagonist")
```

**Collections**:
- `characters` - Character profiles
- `locations` - Location descriptions
- `items` - Item details
- `plot_events` - Key plot points
- `relationships` - Character relationships
- `lore` - World-building

---

## 5. ERROR HANDLING

### Rate Limiting and Retry Logic

**File**: `/home/user/AiBookWriter4/config/rate_limiter.py`

Sophisticated retry mechanism with exponential backoff:

```python
@with_rate_limiting("groq", "llama-3.3-70b-versatile", max_retries=5)
def call_llm():
    return llm.complete(prompt)
```

**Features**:
- Pre-request throttling (waits if approaching limits)
- Post-request usage tracking
- Automatic retry on rate limits (429)
- Exponential backoff (2^n * base with jitter)
- Network error handling (timeout, connection, 503, 502)
- Backoff multiplier capping (64x max = 128 seconds)
- Per-provider header-based limit updates

**Retry Logic**:
```python
for attempt in range(max_retries):
    try:
        _rate_limiter.wait_if_needed(provider, model, estimated_tokens)
        result = func(*args, **kwargs)
        _rate_limiter.record_request(provider, model, estimated_tokens)
        return result
    except Exception as e:
        if "rate limit" in str(e).lower() or "429" in str(e):
            if attempt < max_retries - 1:
                wait_time = _rate_limiter.handle_rate_limit_error(provider)
                time.sleep(wait_time)
                continue
        elif "timeout" in str(e).lower() or "connection" in str(e).lower():
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
        raise
```

### Workflow Error Handling

**Current Approach**: Minimal explicit error handling

```python
# In test_complete_workflow.py:
try:
    with open(output_file_path, "w", encoding="utf-8") as outfile:
        outfile.write(story_arc)
except Exception as e:
    print(f"Error: {e}")
```

**Implicit Error Handling**:
- CrewAI handles agent/task errors internally
- LLM provider errors surfaced through exceptions
- File I/O wrapped in basic try/except
- Missing config files logged as warnings (not fatal)

### RAG Sync Error Handling

**File**: `/home/user/AiBookWriter4/rag/auto_sync.py`

```python
def sync_to_rag(self) -> dict:
    try:
        logger.info(f"Syncing {self.filePath} to RAG system...")
        stats = self.sync_manager.sync_from_ywriter(self.filePath)
        total_synced = sum(stats.values())
        logger.info(f"Synced {total_synced} story elements to RAG")
        return stats
    except Exception as e:
        logger.error(f"RAG sync failed: {e}")
        raise
```

### Logging Infrastructure

- **Writing Progress Logger**: `/home/user/AiBookWriter4/tools/writing_progress.py`
  - Files logs to `writing_log.txt`
  - Tracks agent actions and chapter completion
  - Session-level timing

- **Module Loggers**:
  - Rate limiter logs rate limit hits and backoffs
  - RAG system logs sync operations
  - LLM config logs provider selection
  - Agents log verbose output (if enabled)

---

## 6. KEY FILES & PURPOSES

### Configuration Files

| File | Purpose |
|------|---------|
| `config.yaml` | Application-level settings (agents, workflows, RAG, yWriter config) |
| `.env` | Provider credentials and API keys (git-ignored) |
| `config/llm_config.py` | LLM provider configuration and instantiation |
| `config/rate_limiter.py` | Rate limiting rules and retry logic |
| `config/genres/*.py` | Genre-specific templates (prose style, chapter length, etc.) |

### Agent Files

| File | Agent | Purpose |
|------|-------|---------|
| `agents/story_planner.py` | StoryPlanner | Story arc and plot structure |
| `agents/character_creator.py` | CharacterCreator | Character development |
| `agents/setting_builder.py` | SettingBuilder | Location and world-building |
| `agents/outline_creator.py` | OutlineCreator | Chapter and scene outlines |
| `agents/writer.py` | Writer | Prose generation |
| `agents/editor.py` | Editor | Content refinement |
| `agents/critic.py` | Critic | Quality analysis |
| `agents/lore_builder.py` | LoreBuilder | Mythology and background |
| `agents/memory_keeper.py` | MemoryKeeper | Continuity tracking |
| `agents/relationship_architect.py` | RelationshipArchitect | Character dynamics |

### Workflow & State Files

| File | Purpose |
|------|---------|
| `test_complete_workflow.py` | Main 8-step novel generation workflow |
| `tools/writing_state.py` | JSON-based checkpoint system |
| `tools/writing_progress.py` | Progress tracking and metrics |

### RAG System Files

| File | Purpose |
|------|---------|
| `rag/__init__.py` | RAG module exports |
| `rag/vector_store.py` | ChromaDB semantic search |
| `rag/sync_manager.py` | yWriter7 ↔ RAG synchronization |
| `rag/auto_sync.py` | Automatic sync wrapper |
| `tools/rag_tools.py` | CrewAI tools for semantic search |

### Integration Files

| File | Purpose |
|------|---------|
| `ywriter7/yw/yw7_file.py` | yWriter7 XML file I/O |
| `tools/ywriter_tools.py` | CrewAI tools for yWriter operations |

### UI Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit control panel |
| `web_server.py` | FastAPI web UI |
| `main.py` | CLI entry point |

---

## 7. WORKFLOW EXECUTION EXAMPLE

### Running the Complete Workflow

```bash
python test_complete_workflow.py
```

### Step-by-Step Execution

```python
# Step 1: Initialize project file
yw7_file = Yw7File("output/ten_chapter_novel.yw7")
yw7_file.novel = Novel()
yw7_file.write()

# Step 2: Run Story Planner
story_planner = StoryPlanner(config=StoryPlannerConfig(...))
story_result = story_crew.kickoff()  # CrewAI processes task
story_arc = str(story_result)

# Step 3: Character Creation (saves to yWriter file)
with AutoSyncYw7File(project_path) as yw7:
    # Parse character output and create Character objects
    character = Character()
    character.title = "Alice"
    character.bio = "..."
    yw7.novel.characters[char_id] = character
    # Auto-syncs to RAG on context exit

# Step 4-7: Similar pattern for locations, outlines, scenes, prose, editing

# Step 8: Manual RAG sync
sync_stats = sync_file_to_rag(project_path)
```

---

## 8. DEPENDENCIES

**Key Dependencies**:
- `crewai>=0.80.0` - Multi-agent orchestration
- `anthropic>=0.40.0` - Claude API
- `google-generativeai>=0.8.0` - Gemini API
- `chromadb>=0.5.0` - Vector database
- `sentence-transformers>=2.7.0` - Embeddings
- `PyYAML>=6.0.1` - Configuration
- `streamlit>=1.40.0` - UI
- `fastapi>=0.115.0` - Web API

---

## 9. ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│                    8-Step Workflow Pipeline                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. StoryPlanner → 2. CharacterCreator → 3. SettingBuilder  │
│                                                               │
│  4. OutlineCreator → 5. Scene Structure Parser              │
│                                                               │
│  6. Writer (per scene) → 7. Editor (per scene)              │
│                                                               │
│  8. RAG Sync                                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
                ┌─────────────────────────────┐
                │   LLM Configuration System  │
                ├─────────────────────────────┤
                │  ┌──────────────────────┐   │
                │  │ config/llm_config.py │   │
                │  ├──────────────────────┤   │
                │  │ Supports:            │   │
                │  │ - Ollama             │   │
                │  │ - Anthropic          │   │
                │  │ - Gemini             │   │
                │  │ - Groq               │   │
                │  │ - OpenRouter         │   │
                │  │ - DeepSeek           │   │
                │  │ - Together AI        │   │
                │  │ - OpenAI             │   │
                │  └──────────────────────┘   │
                │         ↓                     │
                │   Rate Limiter               │
                │   (exponential backoff)      │
                └─────────────────────────────┘
                              ↓
                ┌─────────────────────────────┐
                │   State Management Layer    │
                ├─────────────────────────────┤
                │  yWriter7 File (.yw7)       │
                │  + AutoSyncYw7File wrapper  │
                │  + WritingState checkpoints │
                │  + WritingProgress metrics  │
                └─────────────────────────────┘
                              ↓
                ┌─────────────────────────────┐
                │   RAG System (ChromaDB)     │
                ├─────────────────────────────┤
                │  Vector Store:              │
                │  - Characters               │
                │  - Locations                │
                │  - Items                    │
                │  - Plot Events              │
                │  - Relationships            │
                │  - Lore                     │
                └─────────────────────────────┘
```

---

## 10. CURRENT LIMITATIONS & GAPS

### Error Handling
- **Limited retry logic** in workflow (only basic try/except)
- **No graceful recovery** from mid-workflow failures
- **No checkpointing** for step recovery within workflow
- Rate limiting only applied via decorator (not always used)

### State Management
- **No distributed state** (only file-based)
- **No atomic transactions** (if write fails, state is inconsistent)
- **WritingState minimalist** (only tracks IDs, not full state)
- **No rollback capability** if errors occur mid-step

### Agent Coordination
- **No agent-to-agent communication** (only via workflow sequencing)
- **No feedback loops** (agents don't iterate on own outputs)
- **No consensus mechanism** (all agents work independently)
- **No conflict resolution** (conflicting outputs not reconciled)

### RAG System
- **No RAG tool error handling** (search failures not gracefully handled)
- **No chunking strategy** for large content
- **No similarity threshold tuning** per use case
- **No content update strategy** (full re-sync vs incremental)

---

## Summary

AiBookWriter4 is a sophisticated multi-agent novel generation system with:
- **8-step sequential workflow** for complete novel creation
- **6 primary agents** with specialized roles
- **Flexible LLM provider support** (8+ providers)
- **Centralized configuration system** (config.yaml + .env)
- **Automatic state persistence** (yWriter7 + RAG)
- **Intelligent rate limiting** with exponential backoff
- **Semantic knowledge base** for consistency checking

The architecture is well-structured for creative writing but lacks advanced error recovery and distributed state management for large-scale production use.
