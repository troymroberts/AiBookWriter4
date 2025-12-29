# AiBookWriter4 Architecture

## Overview

AiBookWriter4 is a multi-agent AI system designed for automated novel/book generation. It leverages a pipeline of specialized AI agents, each responsible for a distinct phase of the book creation process.

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Agent Framework | CrewAI 0.100.0 | Multi-agent orchestration |
| LLM Abstraction | LangChain | Prompt chains and streaming |
| LLM Provider | Ollama (local) | Open-source model inference |
| Web UI | Streamlit | Interactive control panel |
| Project Export | yWriter 7 | Professional writing software integration |
| Configuration | PyYAML, Pydantic | Typed config management |

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  Streamlit Web UI (app.py)           CLI (main.py)              ││
│  │  - Project Setup                     - Batch Processing          ││
│  │  - Agent Configuration               - Script Automation         ││
│  │  - Real-time Monitoring                                          ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CONFIGURATION LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ config.yaml  │  │ Genre Configs│  │ Prompt Templates         │  │
│  │ - Model list │  │ - 18 genres  │  │ - story_planner.yaml     │  │
│  │ - Defaults   │  │ - Parameters │  │ - setting_builder.yaml   │  │
│  │ - Paths      │  │ - Styles     │  │ - writer.yaml            │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENT PIPELINE                                │
│                                                                      │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐    │
│  │ Story Planner  │───▶│ Setting Builder│───▶│ Outline Creator│    │
│  │ (LangChain)    │    │ (LangChain)    │    │ (CrewAI)       │    │
│  └────────────────┘    └────────────────┘    └────────────────┘    │
│           │                    │                      │             │
│           ▼                    ▼                      ▼             │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐    │
│  │ Character      │    │ Lore Builder   │    │ Writer         │    │
│  │ Creator        │    │ (LangChain)    │    │ (LangChain)    │    │
│  │ (CrewAI)       │    │                │    │                │    │
│  └────────────────┘    └────────────────┘    └────────────────┘    │
│           │                    │                      │             │
│           ▼                    ▼                      ▼             │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐    │
│  │ Plot Agent     │    │ Critic         │    │ Reviser/Editor │    │
│  │ (CrewAI)       │    │ (CrewAI)       │    │                │    │
│  └────────────────┘    └────────────────┘    └────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          LLM LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Ollama Server                                 ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             ││
│  │  │ deepseek-r1 │  │ llama3      │  │ qwen2.5     │             ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘             ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         OUTPUT LAYER                                 │
│  ┌──────────────────────┐  ┌──────────────────────────────────────┐│
│  │ Text Files (output/) │  │ yWriter 7 Projects (.yw7)            ││
│  │ - story_arc.txt      │  │ - Chapters, Scenes                   ││
│  │ - outlines           │  │ - Characters, Locations              ││
│  │ - chapters           │  │ - Project Notes                      ││
│  └──────────────────────┘  └──────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

## Agent Descriptions

### Primary Workflow Agents

| Agent | Framework | Purpose |
|-------|-----------|---------|
| **Story Planner** | LangChain + Ollama | Creates high-level story arcs with major plot points, character arcs, and turning points |
| **Setting Builder** | LangChain + Ollama | Develops world settings, locations, and environmental details |
| **Outline Creator** | CrewAI | Generates detailed chapter-by-chapter outlines with scene breakdowns |
| **Writer** | LangChain + Ollama | Produces actual prose for chapters based on outlines |

### Supporting Agents

| Agent | Framework | Purpose |
|-------|-----------|---------|
| **Character Creator** | CrewAI | Creates detailed character profiles with stats and speech patterns |
| **Lore Builder** | LangChain | Builds detailed world lore and background mythology |
| **Plot Agent** | CrewAI | Refines chapter outlines for maximum narrative effectiveness |
| **Critic** | CrewAI | Provides constructive criticism and quality assessment |
| **Reviser/Editor** | LangChain | Performs editorial revisions and polish |
| **Relationship Architect** | CrewAI | Manages character dynamics and relationships |

## Data Flow

```
User Input (genre, prompt, chapters)
         │
         ▼
┌─────────────────────────────────┐
│ 1. Story Planner                │
│    - Receives: genre, chapters  │
│    - Outputs: story_arc         │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 2. Setting Builder              │
│    - Receives: story_arc        │
│    - Outputs: world_settings    │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 3. Outline Creator              │
│    - Receives: story_arc,       │
│                world_settings   │
│    - Outputs: chapter_outlines  │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 4. Writer (per chapter)         │
│    - Receives: outline, context │
│    - Outputs: chapter_prose     │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 5. Review Cycle (optional)      │
│    Critic → Reviser → Editor    │
└─────────────────────────────────┘
         │
         ▼
    Final Output
```

## Configuration System

### Hierarchy

1. **Root Config** (`config.yaml`): Global settings, model list, defaults
2. **Genre Configs** (`config/genres/*.py`): Genre-specific parameters (40+ settings each)
3. **Prompt Templates** (`config/prompts/*.yaml`): Agent-specific system/user prompts

### Genre Configuration Parameters

Genre configs control narrative style through these parameter categories:

| Category | Parameters |
|----------|------------|
| Story Elements | `CHARACTER_DEPTH`, `CHARACTER_ARC_TYPE`, `CONFLICT_INTENSITY`, `EMOTIONAL_DEPTH` |
| World Building | `SETTING_DETAIL_LEVEL`, `WORLD_COMPLEXITY`, `HISTORICAL_ACCURACY` |
| Style/Structure | `NARRATIVE_STYLE`, `PACING_SPEED`, `DIALOGUE_FREQUENCY`, `DESCRIPTIVE_DEPTH` |
| Themes | `THEME_COMPLEXITY`, `SYMBOLIC_DENSITY`, `MORAL_AMBIGUITY` |
| Human Characteristics | `SHOW_DONT_TELL`, `SUBTEXT_NUANCE`, `COLLOQUIAL_EXPRESSIONS`, `NATURAL_FLOW` |
| Generation | `MAX_CHAPTERS`, `MIN_CHAPTER_LENGTH`, `MAX_CHAPTER_LENGTH` |

## Key Design Patterns

### 1. Agent Pattern
Each agent has a specialized role with distinct capabilities:
```python
class StoryPlanner:
    def __init__(self, config: StoryPlannerConfig, prompts_dir, genre, num_chapters):
        self.llm = OllamaLLM(...)
        self.prompt = ChatPromptTemplate.from_messages([...])
```

### 2. Configuration Pattern
Pydantic models ensure type-safe configuration:
```python
class StoryPlannerConfig(BaseModel):
    llm_endpoint: str = Field(default="http://localhost:11434")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=3000)
```

### 3. Tool Pattern
CrewAI tools extend `BaseTool` for custom functionality:
```python
class ReadProjectNotesTool(BaseTool):
    name: str = "Read Project Notes"
    description: str = "Read project notes from a yWriter 7 project file."

    def _run(self, yw7_path: str) -> str:
        # Implementation
```

### 4. Streaming Pattern
All agents support streaming responses for real-time output:
```python
for chunk in chain.stream({"genre": genre, "num_chapters": num_chapters}):
    yield chunk
```

## Directory Structure

```
AiBookWriter4/
├── agents/                 # AI agent implementations (16 files)
│   ├── story_planner.py   # Primary story arc agent
│   ├── setting_builder.py # World-building agent
│   ├── outline_creator.py # Chapter outline agent
│   ├── writer.py          # Prose generation agent
│   └── ...                # Additional agents
├── config/
│   ├── genres/            # Genre configurations (18 files)
│   └── prompts/           # YAML prompt templates
├── tools/
│   └── ywriter_tools.py   # yWriter 7 integration tools
├── ywriter7/              # Embedded PyWriter library
│   ├── model/             # Data models
│   ├── file/              # File I/O
│   └── yw/                # yWriter format handlers
├── test/                  # Unit and integration tests
├── output/                # Generated content output
├── app.py                 # Streamlit web interface
├── main.py                # CLI entry point
├── config.yaml            # Main configuration
└── requirements.txt       # Python dependencies
```

## Integration Points

### Ollama Integration
- Local LLM inference server
- Default endpoint: `http://localhost:11434`
- Supports multiple models simultaneously
- Streaming responses for real-time output

### yWriter 7 Integration
- Read/write `.yw7` project files
- Full support for: Chapters, Scenes, Characters, Locations, Items, Project Notes
- Enables export to professional writing software

## Scalability Considerations

- **Parallel Processing**: `BATCH_SIZE` config for simultaneous generation
- **Memory Management**: `MEMORY_LIMIT` config to control resource usage
- **Model Selection**: Different models can be assigned to different agents
- **GPU Acceleration**: `USE_GPU` flag for hardware acceleration
