# yWriter7 Sync Integration

## Overview

The AI Book Writer application has **full bidirectional sync** with yWriter7 project files (.yw7 format). This allows AI agents to read from and write to yWriter7 projects, enabling collaboration between human authors and AI agents.

## Test Results ✅

All yWriter7 sync tests passed successfully (5/5):

1. **Project Creation** ✅
2. **Read Operations** ✅
3. **Write Operations** ✅
4. **CrewAI Tools Integration** ✅
5. **Bidirectional Sync** ✅

Run tests: `python test_ywriter7_sync.py`

## Architecture

### Data Models

The yWriter7 integration uses a comprehensive data model hierarchy:

```
Novel (root container)
├── Metadata (title, author, description)
├── Characters (dict, with sorted IDs)
│   ├── title, fullName, description
│   ├── bio, goals, notes
│   └── isMajor flag
├── Locations (dict, with sorted IDs)
│   ├── title, description
│   ├── aka (alternate name)
│   └── tags, image
├── Items (dict, with sorted IDs)
│   ├── title, description
│   ├── aka (alternate name)
│   └── tags, image
├── Project Notes (dict, with sorted IDs)
│   ├── title
│   └── desc (content)
├── Chapters (dict, with sorted IDs)
│   ├── title, description
│   ├── chLevel (0=chapter, 1=part)
│   ├── chType (0=normal, 1=notes, 2=todo, 3=unused)
│   └── srtScenes (sorted scene IDs)
└── Scenes (dict, with sorted IDs)
    ├── title, description
    ├── sceneContent (the actual prose)
    ├── status, tags, notes
    ├── characters[] (list of character IDs)
    ├── locations[] (list of location IDs)
    ├── items[] (list of item IDs)
    └── goal, conflict, outcome
```

### Core Classes

- **`Yw7File`** (`ywriter7/yw/yw7_file.py`) - Main I/O class for reading/writing .yw7 files
- **`Novel`** (`ywriter7/model/novel.py`) - Root container for all project data
- **`Character`** (`ywriter7/model/character.py`) - Character representation
- **`WorldElement`** (`ywriter7/model/world_element.py`) - Base for locations/items
- **`Scene`** (`ywriter7/model/scene.py`) - Scene representation with content
- **`Chapter`** (`ywriter7/model/chapter.py`) - Chapter representation
- **`ProjectNote`** (`ywriter7/model/project_note.py`) - Project notes

## CrewAI Tools

All CrewAI tools are in `tools/ywriter_tools.py` and provide agents with yWriter7 access:

### Read Tools

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `ReadProjectNotesTool` | Read all project notes | yw7_path | Formatted notes text |
| `ReadCharactersTool` | Read all characters | yw7_path | JSON character data |
| `ReadLocationsTool` | Read all locations | yw7_path | JSON location data |
| `ReadOutlineTool` | Read chapter outlines | yw7_path, chapter_id (optional) | Formatted outline |
| `ReadSceneTool` | Read specific scene | yw7_path, scene_id | JSON scene data with content |

### Write Tools

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `WriteProjectNoteTool` | Create new project note | yw7_path, title, content | Success message with note ID |
| `CreateChapterTool` | Create new chapter | yw7_path, title, description | Success message with chapter ID |
| `WriteSceneContentTool` | Write content to scene | yw7_path, scene_id, content | Success message |

## Usage Examples

### Direct API Usage

```python
from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.character import Character
from ywriter7.model.id_generator import create_id

# Read a project
yw7_file = Yw7File("my_novel.yw7")
yw7_file.read()

# Access data
print(f"Title: {yw7_file.novel.title}")
print(f"Characters: {len(yw7_file.novel.characters)}")

# Add a character
char_id = create_id(yw7_file.novel.characters)
new_char = Character()
new_char.title = "Jane Doe"
new_char.fullName = "Jane Elizabeth Doe"
new_char.desc = "A mysterious stranger"
new_char.isMajor = True

yw7_file.novel.characters[char_id] = new_char
yw7_file.novel.srtCharacters.append(char_id)

# Save changes
yw7_file.write()
```

### Using CrewAI Tools

```python
from tools.ywriter_tools import ReadCharactersTool, WriteProjectNoteTool

# Read characters using tool
read_tool = ReadCharactersTool()
characters_json = read_tool._run(yw7_path="my_novel.yw7")
print(characters_json)

# Write a project note using tool
write_tool = WriteProjectNoteTool()
result = write_tool._run(
    yw7_path="my_novel.yw7",
    title="Story Theme",
    content="The central theme is redemption and second chances."
)
print(result)  # "Project note 'Story Theme' written successfully with ID: pn1."
```

### Agent Integration Example

```python
from crewai import Agent, Task, Crew
from config.llm_config import get_llm_config
from tools.ywriter_tools import ReadCharactersTool, WriteProjectNoteTool

# Create agent with yWriter7 tools
config = get_llm_config()
llm = config.create_llm('character_creator')

character_agent = Agent(
    role="Character Creator",
    goal="Create compelling and consistent characters",
    backstory="You are an expert in character development and psychology",
    llm=llm,
    tools=[ReadCharactersTool(), WriteProjectNoteTool()],
    verbose=True
)

# Create task
task = Task(
    description="Read existing characters from my_novel.yw7 and suggest improvements",
    expected_output="A detailed analysis of existing characters with suggestions",
    agent=character_agent
)

# Execute
crew = Crew(agents=[character_agent], tasks=[task])
result = crew.kickoff()
```

## Bidirectional Sync Workflow

The yWriter7 integration supports true bidirectional sync:

### Read → Modify → Write → Read Cycle

```python
# Step 1: Agent reads via tool
read_tool = ReadCharactersTool()
chars = read_tool._run(yw7_path="novel.yw7")

# Step 2: Agent modifies via tool
write_tool = WriteProjectNoteTool()
write_tool._run(
    yw7_path="novel.yw7",
    title="Character Analysis",
    content="Detailed character analysis..."
)

# Step 3: Human opens in yWriter7 and makes changes

# Step 4: Agent reads again - sees human's changes
chars_updated = read_tool._run(yw7_path="novel.yw7")
```

### Knowledge Keeper Pattern

The knowledge keeper agents (CharacterCreator, LoreBuilder, SettingBuilder, etc.) use yWriter7 as their "living story bible":

1. **Writer agents CONSULT** knowledge keepers via ReadTools
2. **Knowledge keepers UPDATE** their domains via WriteTools
3. **MemoryKeeper COORDINATES** updates across keepers
4. **Human authors** can view/edit everything in yWriter7

```
┌─────────────┐
│   Writer    │ ──reads──> CharacterCreator (uses ReadCharactersTool)
│   Agent     │ ──reads──> SettingBuilder (uses ReadLocationsTool)
└─────────────┘ ──reads──> ItemDeveloper (uses ReadItemsTool)
      │
      ▼
  writes scenes
      │
      ▼
┌─────────────┐
│  Memory     │ ──updates──> CharacterCreator (WriteProjectNoteTool)
│  Keeper     │ ──updates──> LoreBuilder (WriteProjectNoteTool)
└─────────────┘ ──updates──> RelationshipArchitect (WriteProjectNoteTool)
```

## File Format Details

### yWriter7 XML Structure

yWriter7 uses XML with CDATA sections for content:

```xml
<?xml version="1.0" encoding="utf-8"?>
<YWRITER7>
  <PROJECT>
    <Title><![CDATA[My Novel]]></Title>
    <AuthorName><![CDATA[AI Book Writer]]></AuthorName>
    <Desc><![CDATA[A test novel]]></Desc>
  </PROJECT>

  <CHARACTERS>
    <CHARACTER>
      <ID>cr1</ID>
      <Title><![CDATA[Alice]]></Title>
      <FullName><![CDATA[Alice Wonderland]]></FullName>
      <Desc><![CDATA[A curious young woman]]></Desc>
      <Bio><![CDATA[Alice grew up in...]]></Bio>
      <Major>-1</Major>
    </CHARACTER>
  </CHARACTERS>

  <LOCATIONS>
    <LOCATION>
      <ID>lc1</ID>
      <Title><![CDATA[Town Square]]></Title>
      <Desc><![CDATA[A bustling plaza...]]></Desc>
    </LOCATION>
  </LOCATIONS>

  <SCENES>
    <SCENE>
      <ID>sc1</ID>
      <Title><![CDATA[Discovery]]></Title>
      <SceneContent><![CDATA[Alice wandered through...]]></SceneContent>
      <Characters>
        <CharID>cr1</CharID>
      </Characters>
      <Locations>
        <LocID>lc1</LocID>
      </Locations>
    </SCENE>
  </SCENES>

  <CHAPTERS>
    <CHAPTER>
      <ID>ch1</ID>
      <Title><![CDATA[Chapter 1]]></Title>
      <Scenes>
        <ScID>sc1</ScID>
      </Scenes>
    </CHAPTER>
  </CHAPTERS>

  <PROJECTNOTES>
    <PROJECTNOTE>
      <ID>pn1</ID>
      <Title><![CDATA[Story Theme]]></Title>
      <Desc><![CDATA[The central theme is...]]></Desc>
    </PROJECTNOTE>
  </PROJECTNOTES>
</YWRITER7>
```

### ID Generation

IDs are generated using `create_id()` from `ywriter7/model/id_generator.py`:

- Characters: `cr1`, `cr2`, `cr3`, ...
- Locations: `lc1`, `lc2`, `lc3`, ...
- Items: `it1`, `it2`, `it3`, ...
- Scenes: `sc1`, `sc2`, `sc3`, ...
- Chapters: `ch1`, `ch2`, `ch3`, ...
- Project Notes: `pn1`, `pn2`, `pn3`, ...

## Fixes Applied

During testing, the following bugs were fixed in the yWriter7 integration:

1. **Missing `indent` import** - Added `from .xml_indent import indent` to `yw7_file.py:24`
2. **Missing `BasicElement` import** - Added `from ..model.basic_element import BasicElement` to `yw7_file.py:23`
3. **Novel not initialized on read** - Added `if self.novel is None: self.novel = Novel()` to `yw7_file.py:137-138`

These fixes are now committed and the yWriter7 integration is fully functional.

## Testing

### Running the Test Suite

```bash
python test_ywriter7_sync.py
```

This creates a sample novel at `output/test_novel.yw7` and runs comprehensive tests:

1. **Project Creation** - Creates a novel with 2 characters, 2 locations, 1 item, 2 chapters, 3 scenes
2. **Read Operations** - Verifies all data can be read correctly
3. **Write Operations** - Tests adding characters, locations, and updating scene content
4. **CrewAI Tools** - Tests all 8 CrewAI tools (5 read, 3 write)
5. **Bidirectional Sync** - Tests read → modify → write → read cycle

### Inspecting Test Results

After running tests, you can open `output/test_novel.yw7` in yWriter7 to see:
- 2 chapters with 3 scenes
- 2 main characters (Alice, Bob) + test characters
- 2 locations (Town Square, Forest Path) + test locations
- 1 item (Magic Compass)
- Multiple project notes including test notes
- Fully written scene content

## Next Steps

Now that yWriter7 sync is working, the next phase is integrating RAG (Retrieval Augmented Generation):

1. **Add ChromaDB** vector database for semantic search
2. **Create MemoryKeeper Agent** to track story progression and update knowledge keepers
3. **Implement query interfaces** so agents can semantically search:
   - Character knowledge base
   - Lore/world knowledge base
   - Relationship graphs
   - Location/setting details
   - Item significance
4. **Bidirectional RAG ↔ yWriter7 sync**:
   - RAG embeddings stay fresh as yWriter7 is updated
   - Knowledge keeper agents update both RAG and yWriter7
   - Human edits in yWriter7 automatically update RAG

## References

- yWriter7 official site: https://www.spacejock.com/yWriter.html
- PyWriter library (basis for this integration): https://github.com/peter88213/PyWriter
- Test script: `test_ywriter7_sync.py`
- Core implementation: `ywriter7/yw/yw7_file.py`
- CrewAI tools: `tools/ywriter_tools.py`
