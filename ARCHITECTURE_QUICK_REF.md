# AiBookWriter4 - Quick Reference Guide

## At a Glance

**Type**: Multi-agent AI novel generation system  
**Framework**: CrewAI (agent orchestration)  
**File Format**: yWriter7 (.yw7 XML)  
**Knowledge Base**: ChromaDB (RAG)  
**LLM Support**: 8 providers (Ollama, Claude, Gemini, Groq, OpenRouter, DeepSeek, Together AI, OpenAI)

---

## The 8-Step Workflow

Run with: `python test_complete_workflow.py`

```
StoryPlanner → CharacterCreator → SettingBuilder → OutlineCreator 
      ↓             ↓                    ↓               ↓
  (Story Arc)  (Characters)        (Locations)      (Chapters)
  
→ Scene Structure Parser → Writer (per scene) → Editor (per scene) → RAG Sync
      ↓                      ↓                       ↓                  ↓
  (Scenes)              (Prose)              (Polished Prose)      (Knowledge Base)
```

---

## Critical Files

### Configuration (All Load from Environment First!)

| File | Purpose | Key Settings |
|------|---------|--------------|
| `config.yaml` | Application defaults | agents, workflows, RAG config |
| `.env` | Provider API keys & model selection | DEFAULT_LLM_PROVIDER, *_API_KEY |
| `config/llm_config.py` | LLM provider factory | get_llm_config(), create_llm() |
| `config/rate_limiter.py` | Rate limit rules & retry logic | RATE_LIMITS dict, @with_rate_limiting |

### Agents (All Extend CrewAI Agent)

| Agent | File | Config Model | Key Method |
|-------|------|--------------|-----------|
| StoryPlanner | `agents/story_planner.py` | StoryPlannerConfig | plan_story_arc() |
| CharacterCreator | `agents/character_creator.py` | CharacterCreatorConfig | create_character() |
| SettingBuilder | `agents/setting_builder.py` | SettingBuilderConfig | build_setting() |
| OutlineCreator | `agents/outline_creator.py` | OutlineCreatorConfig | (via Crew.kickoff()) |
| Writer | `agents/writer.py` | WriterConfig | write_chapter() |
| Editor | `agents/editor.py` | EditorConfig | review_chapter() |

### State & Persistence

| Component | File | Use Case |
|-----------|------|----------|
| Primary State | yWriter7 (.yw7 file) | Source of truth for novel structure |
| Auto-Sync Wrapper | `rag/auto_sync.py` | AutoSyncYw7File - auto write + RAG sync |
| Checkpoints | `tools/writing_state.py` | WritingState - JSON-based save/load |
| Progress Tracking | `tools/writing_progress.py` | WritingProgress - timing & metrics |
| RAG Knowledge | `rag/vector_store.py` | ChromaDB vector database |

### Tools & Integration

| File | Purpose | Tools Provided |
|------|---------|-----------------|
| `tools/rag_tools.py` | RAG-enabled search tools | 6+ semantic search tools for agents |
| `tools/ywriter_tools.py` | yWriter7 operations | Read/write notes, create chapters |

---

## Key Classes & Instantiation

### Getting LLM Config

```python
from config.llm_config import get_llm_config

config = get_llm_config()
llm = config.create_llm("story_planner")  # Uses env vars + config.yaml
```

### Creating an Agent

```python
from agents.story_planner import StoryPlanner, StoryPlannerConfig

agent_config = StoryPlannerConfig(temperature=0.7, max_tokens=12288)
agent = StoryPlanner(config=agent_config)

# Agent is CrewAI Agent - use in Crew + Task
crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
result = crew.kickoff()
```

### Persisting to yWriter7

```python
from rag import AutoSyncYw7File

# Auto-saves on context exit + syncs to RAG
with AutoSyncYw7File("output/novel.yw7") as yw7:
    yw7.novel.characters[char_id] = character
    # Auto-saved and synced!
```

### Saving Checkpoints

```python
from tools.writing_state import WritingState

state = WritingState("my_project")
state.current_chapter_id = "ch_1"
state.save_checkpoint()  # → my_project_checkpoint.json
```

---

## Configuration Hierarchy (Highest to Lowest Priority)

1. **Environment Variables**
   - `DEFAULT_LLM_PROVIDER=anthropic`
   - `ANTHROPIC_API_KEY=sk-ant-...`
   - `AGENT_STORY_PLANNER_PROVIDER=groq`

2. **config.yaml**
   ```yaml
   agents:
     story_planner:
       temperature: 0.7
       max_tokens: 12288
   ```

3. **Defaults in llm_config.py**
   - Provider: ollama
   - Model: llama3.2 (Ollama), claude-3-5-sonnet-20241022 (Anthropic)

---

## Common Operations

### Run Full Workflow
```bash
python test_complete_workflow.py
```

### Check Agent Config
```python
config = get_llm_config()
agent_cfg = config.get_agent_config("story_planner")
print(agent_cfg)
```

### Override Provider
```bash
export DEFAULT_LLM_PROVIDER=groq
export GROQ_API_KEY=your-key
python test_complete_workflow.py
```

### Check Rate Limits
```python
from config.rate_limiter import RATE_LIMITS
print(RATE_LIMITS["groq"]["llama-3.3-70b-versatile"])
```

---

## Workflow Step Details

### Step 1: Story Planning
- **Agent**: StoryPlanner
- **Input**: Genre, # chapters, story premise
- **Output**: story_arc (3-act structure, character arcs, plot points)
- **Saved to**: yWriter7 novel.desc

### Step 2: Character Creation
- **Agent**: CharacterCreator
- **Input**: story_arc
- **Output**: Structured character data (NAME, BIO, GOALS, AKA, MAJOR)
- **Saved to**: yWriter7 novel.characters[]
- **Parsed**: Split output by "CHARACTER:" markers

### Step 3: Location Creation
- **Agent**: SettingBuilder
- **Input**: story_arc
- **Output**: Structured location data (LOCATION, AKA, DESC)
- **Saved to**: yWriter7 novel.locations[]
- **Parsed**: Split output by "LOCATION:" markers

### Step 4: Chapter Outlining
- **Agent**: OutlineCreator
- **Input**: story_arc
- **Output**: Chapter titles, scenes per chapter, descriptions
- **Saved to**: yWriter7 novel.chapters[] + novel.scenes[]
- **Parsed**: Split output by "CHAPTER:" and "SCENE:" markers

### Step 5: Scene Structure
- **Agent**: OutlineCreator (again)
- **Input**: Chapter outlines
- **Output**: Scene goals, conflicts, outcomes, POV, location
- **Parsed**: Extracts GOAL, CONFLICT, OUTCOME, TYPE, MODE, POV, LOCATION per scene

### Step 6: Prose Writing
- **Agent**: Writer
- **Input**: Scene details + story context
- **Output**: 2000-3000 word scene prose
- **Per-Scene**: Iterates through all scenes
- **Saved to**: yWriter7 scene.sceneContent

### Step 7: Editorial Refinement
- **Agent**: Editor
- **Input**: Written prose + scene outline
- **Output**: Polished, refined prose
- **Per-Scene**: Iterates through written scenes only
- **Saved to**: yWriter7 scene.sceneContent

### Step 8: RAG Sync
- **Operation**: Automatic (via AutoSyncYw7File)
- **Target**: ChromaDB collections
- **Collections**: characters, locations, items, plot_events, relationships, lore

---

## Error Handling

### Rate Limiting
- **Pre-request**: Waits if approaching limits
- **On Error**: Retries with exponential backoff (2^n * 2s, max 128s)
- **Decorator**: `@with_rate_limiting("groq", "model", max_retries=5)`

### Workflow Errors
- Minimal explicit handling in workflow
- CrewAI handles agent exceptions
- File I/O has basic try/except
- Config missing = warning (not fatal)

### RAG Sync Errors
- Logged and raised (not silently caught)
- Sync stats returned on success

---

## Data Structures

### Novel Project (yWriter7 Format)
```
Novel
├── title
├── authorName
├── desc
├── chapters[]
│   ├── title
│   ├── desc
│   └── scenes[] (IDs only)
├── scenes[]
│   ├── title
│   ├── goal, conflict, outcome
│   ├── isReactionScene
│   ├── scnMode
│   ├── sceneContent (prose)
│   └── notes
├── characters[]
│   ├── title (name)
│   ├── fullName
│   ├── aka (alternate names)
│   ├── desc, bio, notes, goals
│   ├── isMajor
│   └── (other character fields)
└── locations[]
    ├── title (name)
    ├── aka
    ├── desc
    └── (other location fields)
```

---

## Key Dependencies

**Must-Have**:
- crewai>=0.80.0 (agent orchestration)
- ywriter7 (yWriter file handling)
- chromadb>=0.5.0 (RAG vector DB)
- PyYAML (config)

**LLM Support**:
- anthropic (Claude)
- google-generativeai (Gemini)
- (Ollama built-in via litellm)

**Utilities**:
- python-dotenv (.env loading)
- sentence-transformers (embeddings)
- streamlit, fastapi (UI)

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "ANTHROPIC_API_KEY not found" | Missing .env key | Set ANTHROPIC_API_KEY in .env |
| "Rate limit hit" | Too many requests | Already handled with backoff, just wait |
| "Ollama not responding" | Local server down | Start ollama: `ollama serve` |
| "RAG sync failed" | Vector DB issue | Check knowledge_base/ directory perms |
| "No agent config" | Agent not in config.yaml | Add agent section to config.yaml |

---

## Testing

**Full Workflow**: `python test_complete_workflow.py`  
**RAG Integration**: `python test_rag_integration.py`  
**Writing Flow**: `python test_writing_flow.py`  
**Auto Sync**: `python test_auto_sync.py`  

---

## File Locations Summary

```
/home/user/AiBookWriter4/
├── config.yaml                          # Main app config
├── .env                                 # Secrets (git-ignored)
├── config/
│   ├── llm_config.py                   # LLM provider factory
│   ├── rate_limiter.py                 # Rate limit + retry logic
│   └── genres/                         # Genre configs
├── agents/
│   ├── story_planner.py
│   ├── character_creator.py
│   ├── setting_builder.py
│   ├── outline_creator.py
│   ├── writer.py
│   └── editor.py
├── tools/
│   ├── writing_state.py                # Checkpoints
│   ├── writing_progress.py             # Metrics
│   ├── rag_tools.py                    # Agent tools
│   └── ywriter_tools.py                # yWriter ops
├── rag/
│   ├── auto_sync.py                    # AutoSyncYw7File
│   ├── vector_store.py                 # ChromaDB wrapper
│   ├── sync_manager.py                 # yWriter ↔ RAG sync
│   └── __init__.py
├── ywriter7/                           # yWriter7 library
├── knowledge_base/                     # ChromaDB storage
├── output/                             # Generated novels
└── test_complete_workflow.py           # Main workflow entry point
```

