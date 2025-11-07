# AiBookWriter4 - Quick Reference Guide

## File Locations Summary

### Critical Core Files
```
LLM Configuration:
  /home/user/AiBookWriter4/config/llm_config.py          (341 lines - Main config manager)

yWriter7 Integration:
  /home/user/AiBookWriter4/ywriter7/yw/yw7_file.py       (Core file I/O)
  /home/user/AiBookWriter4/ywriter7/model/novel.py       (Data structure)
  /home/user/AiBookWriter4/ywriter7/model/scene.py       (Scene with auto word count)
  /home/user/AiBookWriter4/ywriter7/model/character.py   (Character model)
  /home/user/AiBookWriter4/ywriter7/model/id_generator.py (ID creation)

CrewAI Tools:
  /home/user/AiBookWriter4/tools/ywriter_tools.py        (8 tools - read/write)

Agents (CrewAI):
  /home/user/AiBookWriter4/agents/character_creator.py   (Simple CrewAI pattern)
  /home/user/AiBookWriter4/agents/outline_creator.py     (Advanced with tools)
  /home/user/AiBookWriter4/agents/memory_keeper.py       (STUB - needs implementation)
  /home/user/AiBookWriter4/agents/critic.py
  /home/user/AiBookWriter4/agents/editor.py

Agents (LangChain - Legacy):
  /home/user/AiBookWriter4/agents/story_planner.py       (Active, streaming)
  /home/user/AiBookWriter4/agents/writer.py              (Active, streaming)
  /home/user/AiBookWriter4/agents/setting_builder.py
  /home/user/AiBookWriter4/agents/lore_builder.py

Configuration:
  /home/user/AiBookWriter4/config.yaml                   (Main config)
  /home/user/AiBookWriter4/.env.example                  (LLM credentials)
  /home/user/AiBookWriter4/config/genres/literary_fiction.py (Genre template)

Application Entry Points:
  /home/user/AiBookWriter4/main.py                       (CLI)
  /home/user/AiBookWriter4/app.py                        (Streamlit UI)

Testing:
  /home/user/AiBookWriter4/test_ywriter7_sync.py         (639 lines - comprehensive tests)
  /home/user/AiBookWriter4/YWRITER7_SYNC.md              (Integration docs)
  /home/user/AiBookWriter4/AGENT_ANALYSIS.md             (Agent analysis)
```

---

## Code Pattern Examples

### 1. Using LLM Configuration

```python
from config.llm_config import get_llm_config, create_agent_llm

# Get global config instance
config = get_llm_config()

# Get provider config for specific agent
provider_config = config.get_provider_config("story_planner")
# Returns: {provider, model, temperature, max_tokens, ...}

# Get agent's role/goal/backstory
agent_config = config.get_agent_config("story_planner")
# Returns: {role, goal, backstory, temperature, max_tokens, ...}

# Create LLM instance for agent
llm = config.create_llm("story_planner")
# Returns: CrewAI LLM instance configured for provider

# Or use convenience function
llm = create_agent_llm("writer", temperature=0.8)  # Override temperature
```

### 2. Creating a CrewAI Agent

```python
from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional
from config.llm_config import get_llm_config

# Step 1: Define configuration model
class MyAgentConfig(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    
    class Config:
        arbitrary_types_allowed = True

# Step 2: Create agent class
class MyAgent(Agent):
    def __init__(self, config: MyAgentConfig):
        llm = self.create_llm(config)
        
        super().__init__(
            role='My Agent Role',
            goal='What this agent wants to achieve',
            backstory='Background and expertise',
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=[]  # Add tools here
        )
    
    def create_llm(self, config: MyAgentConfig):
        from crewai import LLM
        llm_config = get_llm_config()
        base_config = llm_config.get_provider_config("my_agent")
        base_config.update({
            'temperature': config.temperature,
            'top_p': config.top_p
        })
        # Create LLM based on provider
        return llm_config.create_llm("my_agent")

# Step 3: Use agent
config = MyAgentConfig(temperature=0.5)
agent = MyAgent(config)
```

### 3. Working with yWriter7 Files

```python
from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.character import Character
from ywriter7.model.scene import Scene
from ywriter7.model.id_generator import create_id

# Read existing project
yw7_file = Yw7File("my_novel.yw7")
yw7_file.read()

# Access data
novel = yw7_file.novel
print(f"Title: {novel.title}")
print(f"Characters: {len(novel.characters)}")
print(f"Chapters: {len(novel.chapters)}")

# Iterate through chapters
for ch_id in novel.srtChapters:
    chapter = novel.chapters[ch_id]
    print(f"Chapter: {chapter.title}")
    for sc_id in chapter.srtScenes:
        scene = novel.scenes[sc_id]
        print(f"  Scene: {scene.title} ({scene.wordCount} words)")

# Add new character
char_id = create_id(novel.characters)
new_char = Character()
new_char.title = "Jane Doe"
new_char.fullName = "Jane Elizabeth Doe"
new_char.desc = "A mysterious stranger"
new_char.bio = "Jane's background..."
new_char.isMajor = True

novel.characters[char_id] = new_char
novel.srtCharacters.append(char_id)

# Update scene content
scene = novel.scenes["sc1"]
scene.sceneContent = "Alice wandered through the forest..."
# wordCount and letterCount auto-updated by setter

# Save changes
yw7_file.write()
```

### 4. Using yWriter7 CrewAI Tools

```python
from tools.ywriter_tools import (
    ReadProjectNotesTool,
    ReadCharactersTool,
    WriteProjectNoteTool,
    CreateChapterTool,
    WriteSceneContentTool
)

# Read operations
read_notes = ReadProjectNotesTool()
notes = read_notes._run(yw7_path="my_novel.yw7")

read_chars = ReadCharactersTool()
characters_json = read_chars._run(yw7_path="my_novel.yw7")

# Write operations
write_note = WriteProjectNoteTool()
result = write_note._run(
    yw7_path="my_novel.yw7",
    title="Story Arc",
    content="The story follows..."
)

create_chapter = CreateChapterTool()
result = create_chapter._run(
    yw7_path="my_novel.yw7",
    title="Chapter 1: The Beginning",
    description="Introducing the protagonist"
)

write_scene = WriteSceneContentTool()
result = write_scene._run(
    yw7_path="my_novel.yw7",
    scene_id="sc1",
    content="Alice wandered through..."
)
```

### 5. Using Tools in an Agent

```python
from crewai import Agent, Task, Crew
from tools.ywriter_tools import ReadCharactersTool, WriteProjectNoteTool

# Create agent with tools
agent = Agent(
    role="Story Analyst",
    goal="Analyze and improve story",
    backstory="Expert story analyst",
    llm=llm,
    tools=[ReadCharactersTool(), WriteProjectNoteTool()],
    verbose=True
)

# Create task
task = Task(
    description="Read characters and write analysis",
    expected_output="Character analysis notes",
    agent=agent
)

# Run task
crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
```

### 6. Configuration Loading

```python
import yaml
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Load YAML config
with open("config.yaml", "r") as f:
    app_config = yaml.safe_load(f)

# Access configurations
genre = app_config.get("genre", "literary_fiction")
num_chapters = app_config.get("num_chapters", 12)

# Access agent config
agents_config = app_config.get("agents", {})
story_planner_config = agents_config.get("story_planner", {})

# Access environment variables
api_key = os.getenv("GROQ_API_KEY")
provider = os.getenv("DEFAULT_LLM_PROVIDER", "ollama")

# Load genre-specific config
from config.genres.literary_fiction import CHARACTER_DEPTH, THEME_COMPLEXITY
```

### 7. MemoryKeeper Implementation Pattern (TO DO)

```python
from crewai import Agent
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import chromadb  # To be added to requirements

class MemoryKeeperConfig(BaseModel):
    vector_db_path: str = "knowledge_base"
    embedding_model: str = "all-minilm-l6-v2"

class MemoryKeeper(Agent):
    def __init__(self, config: MemoryKeeperConfig):
        self.vector_store = chromadb.Client()
        self.collection = self.vector_store.get_or_create_collection("story_context")
        
        super().__init__(
            role="Memory Keeper",
            goal="Track story continuity and context",
            backstory="Guardian of story consistency",
            llm=self.create_llm(config),
            tools=[SemanticSearchTool(), ContinuityCheckTool()],
            verbose=True
        )
    
    def store_chapter_summary(self, chapter_id: str, summary: str):
        """Store chapter summary with embeddings"""
        self.collection.add(
            ids=[chapter_id],
            documents=[summary],
            metadatas=[{"type": "chapter", "chapter_id": chapter_id}]
        )
    
    def query_similar_context(self, query: str, n_results: int = 5):
        """Semantic search for similar contexts"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
    
    def check_character_consistency(self, character_id: str, new_info: str):
        """Verify consistency with existing character info"""
        existing = self.query_similar_context(f"Character {character_id}", n_results=1)
        # Compare and flag inconsistencies
        pass
```

---

## Key Development Patterns

### Agent Initialization Pattern
```
Config Model (BaseModel) 
  ↓
Agent.__init__(config)
  ↓
LLM Creation (provider-specific)
  ↓
super().__init__() with role/goal/backstory/tools/llm
```

### Data Flow Pattern
```
Input (Story Idea)
  ↓
StoryPlanner (LangChain) → Story Arc
  ↓
OutlineCreator (CrewAI) → Chapter Outlines
  ↓
Writer (LangChain) → Chapter Prose
  ↓
Editor (CrewAI) → Reviewed Chapters
  ↓
yWriter7 File (via Tools)
  ↓
Output (Published .yw7)
```

### Configuration Priority
```
Runtime args (highest)
  ↓
Environment variables (.env)
  ↓
config.yaml settings
  ↓
Agent defaults (lowest)
```

---

## Common Tasks

### Task 1: Add a New Tool to an Agent

1. Create tool in `tools/ywriter_tools.py`:
```python
class MyCustomInput(BaseModel):
    param1: str = Field(..., description="Description")

class MyCustomTool(BaseTool):
    name: str = "My Custom Tool"
    description: str = "Does something useful"
    args_schema: type[BaseModel] = MyCustomInput
    
    def _run(self, param1: str, **kwargs) -> str:
        # Implementation
        return result
```

2. Add to agent:
```python
agent = Agent(
    role="...",
    goal="...",
    backstory="...",
    tools=[MyCustomTool()],
    llm=llm
)
```

### Task 2: Add a New Genre

1. Create file `config/genres/my_genre.py`:
```python
CHARACTER_DEPTH = 0.8
CONFLICT_INTENSITY = 0.7
PACING_SPEED = 0.6
THEME_COMPLEXITY = 0.8
NARRATIVE_STYLE = "descriptive"
PROSE_STYLE = "elegant"
```

2. Update `config.yaml`:
```yaml
genre: my_genre
```

### Task 3: Add a New Agent

1. Create file `agents/my_agent.py` with:
   - Config model (Pydantic)
   - Agent class extending crewai.Agent
   - LLM creation method

2. Register in `config.yaml`:
```yaml
agents:
  my_agent:
    role: "My Role"
    goal: "My Goal"
    backstory: "My backstory"
    temperature: 0.7
    max_tokens: 4096
```

---

## Testing Your Code

### Run yWriter7 Integration Tests
```bash
python test_ywriter7_sync.py
```

### Test LLM Configuration
```bash
python config/llm_config.py
```

### Run Main CLI
```bash
python main.py
```

### Run Streamlit UI
```bash
streamlit run app.py
```

---

## Key Statistics

- **Total Lines of Code**: ~10,000+
- **Python Files**: 80+
- **Agent Implementations**: 14
- **CrewAI Tools**: 8
- **Supported LLM Providers**: 4
- **Available Genres**: 18+
- **Test Coverage**: Comprehensive yWriter7 tests (639 lines)

---

## Next Steps for Your Implementation

1. **Read these files first:**
   - `/home/user/AiBookWriter4/config/llm_config.py` - Understand config system
   - `/home/user/AiBookWriter4/tools/ywriter_tools.py` - Understand tool patterns
   - `/home/user/AiBookWriter4/agents/memory_keeper.py` - Understand stub

2. **Implement:**
   - ChromaDB vector database
   - MemoryKeeper storage backend
   - Semantic query tools
   - Bidirectional sync logic

3. **Test extensively:**
   - Use test_ywriter7_sync.py as pattern
   - Create test_rag_integration.py
   - Verify consistency checks

4. **Integrate:**
   - Add tools to existing agents
   - Update agent workflows
   - Test end-to-end story generation
