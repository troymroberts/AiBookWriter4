# Agents API Reference

## Overview

AiBookWriter4 uses two agent frameworks:
- **LangChain**: For streaming LLM interactions with prompt templates
- **CrewAI**: For complex multi-tool agents with role-based behaviors

## Agent Base Patterns

### LangChain-Based Agents

LangChain agents use `OllamaLLM` with `ChatPromptTemplate`:

```python
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate

class ExampleAgent:
    def __init__(self, config: AgentConfig, prompts_dir: str):
        self.llm = OllamaLLM(
            base_url=config.llm_endpoint,
            model=config.llm_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            streaming=True
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", user_prompt)
        ])
```

### CrewAI-Based Agents

CrewAI agents extend `Agent` with roles, goals, and tools:

```python
from crewai import Agent
from crewai.llm import LLM

class ExampleCrewAgent(Agent):
    def __init__(self, config: AgentConfig, tools: list = None):
        super().__init__(
            role="Agent Role",
            goal="Agent Goal",
            backstory="Agent Backstory",
            llm=self.create_llm(config),
            tools=tools or [],
            verbose=True
        )
```

---

## StoryPlanner

**Location:** `agents/story_planner.py`
**Framework:** LangChain + Ollama

Creates high-level story arcs with major plot points, character arcs, and turning points.

### Configuration

```python
class StoryPlannerConfig(BaseModel):
    llm_endpoint: str = "http://localhost:11434"
    llm_model: str = "ollama/llama3:latest"
    temperature: float = 0.7
    max_tokens: int = 3000
    top_p: float = 0.95
    context_window: int = 8192
    streaming: bool = True
    system_template: Optional[str] = None
    prompt_template: Optional[str] = None
    response_template: Optional[str] = None
```

### Class: StoryPlanner

#### Constructor

```python
StoryPlanner(
    config: StoryPlannerConfig,
    prompts_dir: str,
    genre: str,
    num_chapters: int,
    streaming: bool = True
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `StoryPlannerConfig` | Agent configuration |
| `prompts_dir` | `str` | Path to prompts directory |
| `genre` | `str` | Genre name (e.g., "literary_fiction") |
| `num_chapters` | `int` | Number of chapters to plan |
| `streaming` | `bool` | Enable streaming responses |

#### Methods

##### `plan_story_arc(genre, num_chapters, additional_instructions="")`

Generates a story arc for the specified parameters.

**Parameters:**
- `genre` (str): Genre for the story
- `num_chapters` (int): Number of chapters
- `additional_instructions` (str): Optional extra instructions

**Returns:** Generator yielding string chunks (streaming)

**Example:**
```python
config = StoryPlannerConfig(
    llm_endpoint="http://localhost:11434",
    llm_model="deepseek-r1:1.5b"
)
planner = StoryPlanner(
    config=config,
    prompts_dir="config/prompts",
    genre="literary_fiction",
    num_chapters=10
)

for chunk in planner.plan_story_arc(
    genre="literary_fiction",
    num_chapters=10,
    additional_instructions="Focus on themes of isolation"
):
    print(chunk, end="", flush=True)
```

---

## SettingBuilder

**Location:** `agents/setting_builder.py`
**Framework:** LangChain + Ollama

Develops world settings, locations, and environmental details based on the story arc.

### Configuration

```python
class SettingBuilderConfig(BaseModel):
    llm_endpoint: str = "http://localhost:11434"
    llm_model: str = "ollama/llama3:latest"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.95
    context_window: int = 8192
```

### Class: SettingBuilder

#### Constructor

```python
SettingBuilder(
    config: SettingBuilderConfig,
    prompts_dir: str,
    streaming: bool = True
)
```

#### Methods

##### `run_information_gathering_task(task_description, outline_context)`

Generates world settings based on the provided story context.

**Parameters:**
- `task_description` (str): Description of the setting task
- `outline_context` (str): Story arc/outline to base settings on

**Returns:** Generator yielding string chunks

**Example:**
```python
config = SettingBuilderConfig(llm_model="llama3:8b")
builder = SettingBuilder(config=config, prompts_dir="config/prompts")

for chunk in builder.run_information_gathering_task(
    task_description="Develop world settings",
    outline_context=story_arc_text
):
    print(chunk, end="")
```

---

## OutlineCreator

**Location:** `agents/outline_creator.py`
**Framework:** CrewAI

Generates detailed chapter-by-chapter outlines with scene breakdowns.

### Configuration

```python
class OutlineCreatorConfig(BaseModel):
    llm_endpoint: str = "http://localhost:11444"
    llm_model: str = "ollama/llama3:latest"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.95
    system_template: Optional[str] = None
    prompt_template: Optional[str] = None
    response_template: Optional[str] = None
```

### Class: OutlineCreator

Extends `crewai.Agent`

#### Constructor

```python
OutlineCreator(
    config: OutlineCreatorConfig,
    tools: Optional[List[BaseTool]] = None,
    streaming: bool = True
)
```

#### Built-in Tools

- `ChapterBreakdownTool`: Assists with chapter divisions and pacing
- `OutlineTemplateTool`: Formats outlines according to genre conventions

#### Agent Properties

| Property | Value |
|----------|-------|
| `role` | "Master Outliner" |
| `goal` | Generate detailed chapter outlines based on story arc |
| `verbose` | True |
| `allow_delegation` | False |

#### Methods

##### `run_information_gathering_task(task_description, project_notes_content)`

Creates chapter outlines based on the story arc.

**Parameters:**
- `task_description` (str): Description of outline task
- `project_notes_content` (str): Story arc content

**Returns:** Generator yielding string chunks

**Example:**
```python
config = OutlineCreatorConfig(llm_model="qwen2.5:7b")
creator = OutlineCreator(config=config)

for chunk in creator.run_information_gathering_task(
    task_description="Create detailed chapter outlines",
    project_notes_content=story_arc_text
):
    print(chunk, end="")
```

---

## Writer

**Location:** `agents/writer.py`
**Framework:** LangChain + Ollama

Produces actual prose for chapters based on outlines and genre configuration.

### Class: Writer

#### Constructor

```python
Writer(
    base_url: str = "http://localhost:11434",
    model: str = "llama3:8b-instruct",
    temperature: float = 0.8,
    context_window: int = 8192,
    max_tokens: int = 3500,
    top_p: float = 0.95,
    prompts_dir: str = "config/prompts",
    genre: str = "literary_fiction",
    num_chapters: int = 10
)
```

#### Methods

Writes chapter prose based on outline and context.

**Example:**
```python
writer = Writer(
    model="llama3:8b-instruct",
    temperature=0.8,
    genre="literary_fiction"
)
```

---

## CharacterCreator

**Location:** `agents/character_creator.py`
**Framework:** CrewAI

Creates detailed character profiles with stats, backgrounds, and speech patterns.

### Configuration

```python
class CharacterCreatorConfig(BaseModel):
    llm_endpoint: str = "http://localhost:11434"
    llm_model: str = "ollama/llama3:latest"
    temperature: float = 0.7
    max_tokens: int = 2000
```

### Agent Properties

| Property | Value |
|----------|-------|
| `role` | "Character Designer" |
| `goal` | Create compelling, multi-dimensional characters |

---

## PlotAgent

**Location:** `agents/plot_agent.py`
**Framework:** CrewAI

Refines chapter outlines for maximum narrative effectiveness.

### Configuration

```python
class PlotAgentConfig(BaseModel):
    llm_endpoint: str = "http://localhost:11434"
    llm_model: str = "ollama/llama3:latest"
    temperature: float = 0.7
    max_tokens: int = 2000
```

---

## Critic

**Location:** `agents/critic.py`
**Framework:** CrewAI

Provides constructive criticism and quality assessment of chapters.

### Configuration

```python
class CriticConfig(BaseModel):
    llm_endpoint: str = "http://localhost:11434"
    llm_model: str = "ollama/llama3:latest"
    temperature: float = 0.5  # Lower for consistent analysis
    max_tokens: int = 2000
```

---

## LoreBuilder

**Location:** `agents/lore_builder.py`
**Framework:** LangChain + Ollama

Builds detailed world lore, mythology, and background history.

---

## Common Patterns

### Streaming Output

All agents support streaming for real-time output:

```python
# Pattern for consuming streaming output
full_output = ""
for chunk in agent.method(params):
    full_output += chunk
    print(chunk, end="", flush=True)
```

### Configuration with Pydantic

All configs use Pydantic for validation:

```python
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    llm_endpoint: str = Field(
        default="http://localhost:11434",
        description="LLM server endpoint"
    )

    class Config:
        arbitrary_types_allowed = True
```

### Prompt Loading

Agents load prompts from YAML files:

```python
# config/prompts/agent_name.yaml
system_message: >
  You are an AI assistant...

user_prompt: "Task: {task} for {genre} with {num_chapters} chapters"
```

```python
# In agent __init__
with open(f"{prompts_dir}/agent_name.yaml", "r") as f:
    prompts = yaml.safe_load(f)
self.system_message = prompts['system_message']
self.user_prompt = prompts['user_prompt']
```

---

## Creating Custom Agents

### LangChain-Based Custom Agent

```python
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

class CustomAgentConfig(BaseModel):
    llm_endpoint: str = "http://localhost:11434"
    llm_model: str = "llama3:8b"
    temperature: float = 0.7

class CustomAgent:
    def __init__(self, config: CustomAgentConfig):
        self.llm = OllamaLLM(
            base_url=config.llm_endpoint,
            model=config.llm_model,
            temperature=config.temperature,
            streaming=True
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("user", "{task}")
        ])

    def execute(self, task: str):
        chain = self.prompt | self.llm
        for chunk in chain.stream({"task": task}):
            yield chunk
```

### CrewAI-Based Custom Agent

```python
from crewai import Agent
from crewai.llm import LLM
from crewai.tools import BaseTool

class CustomTool(BaseTool):
    name: str = "Custom Tool"
    description: str = "Does something custom"

    def _run(self, **kwargs) -> str:
        return "Tool result"

class CustomCrewAgent(Agent):
    def __init__(self, config):
        llm = LLM(
            base_url=config.llm_endpoint,
            model=config.llm_model,
            temperature=config.temperature
        )
        super().__init__(
            role="Custom Role",
            goal="Custom Goal",
            backstory="Custom Backstory",
            llm=llm,
            tools=[CustomTool()],
            verbose=True
        )
```
