# Tools API Reference

## Overview

AiBookWriter4 provides custom CrewAI tools for integration with yWriter 7 project files. All tools extend `crewai.tools.BaseTool` and use Pydantic models for input validation.

**Location:** `tools/ywriter_tools.py`

---

## Helper Functions

### `load_yw7_file(file_path: str) -> Yw7File`

Loads a yWriter 7 project file for reading or writing.

**Parameters:**
- `file_path` (str): Path to the `.yw7` file

**Returns:** `Yw7File` object

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file is not a `.yw7` file

**Example:**
```python
from tools.ywriter_tools import load_yw7_file

yw7 = load_yw7_file("project.yw7")
print(yw7.novel.title)
```

---

## Read Tools

### ReadProjectNotesTool

Reads project notes from a yWriter 7 project file.

#### Input Schema

```python
class ReadProjectNotesInput(BaseModel):
    yw7_path: str = Field(..., description="The path to the .yw7 file.")
```

#### Tool Properties

| Property | Value |
|----------|-------|
| `name` | "Read Project Notes" |
| `description` | "Read project notes from a yWriter 7 project file." |

#### Returns

String containing all project notes formatted as:
```
Title: Note Title
Content: Note content
---
Title: Second Note
Content: Second note content
```

#### Example

```python
from tools.ywriter_tools import ReadProjectNotesTool

tool = ReadProjectNotesTool()
result = tool._run(yw7_path="my_novel.yw7")
print(result)
```

---

### ReadCharactersTool

Reads character data from a yWriter 7 project file.

#### Input Schema

```python
class ReadCharactersInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
```

#### Tool Properties

| Property | Value |
|----------|-------|
| `name` | "Read Characters" |
| `description` | "Read character data from a yWriter 7 project file." |

#### Returns

JSON-formatted character data:
```json
{"ID": "cr1", "Name": "John", "Description": "...", "Full Name": "John Doe", "Notes": "..."}
```

#### Example

```python
from tools.ywriter_tools import ReadCharactersTool

tool = ReadCharactersTool()
characters = tool._run(yw7_path="my_novel.yw7")
```

---

### ReadLocationsTool

Reads location data from a yWriter 7 project file.

#### Input Schema

```python
class ReadLocationsInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
```

#### Tool Properties

| Property | Value |
|----------|-------|
| `name` | "Read Locations" |
| `description` | "Read location data from a yWriter 7 project file." |

#### Returns

JSON-formatted location data:
```json
{"ID": "lc1", "Name": "Castle", "Description": "...", "AKA": "The Fortress"}
```

---

### ReadOutlineTool

Reads chapter outlines from a yWriter 7 project file.

#### Input Schema

```python
class ReadOutlineInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
    chapter_id: Optional[str] = Field(
        None, description="Optional ID of a specific chapter to read"
    )
```

#### Tool Properties

| Property | Value |
|----------|-------|
| `name` | "Read Outline" |
| `description` | "Read chapter outlines from a yWriter 7 project file." |

#### Returns

Formatted outline with chapters and scenes:
```
Chapter ID: ch1, Title: The Beginning
Description: Opening chapter...
  Scenes:
  Scene ID: sc1, Title: Morning, Summary: Character wakes up
  Scene ID: sc2, Title: Discovery, Summary: Finding the letter

Chapter ID: ch2, Title: The Journey
...
```

#### Example

```python
from tools.ywriter_tools import ReadOutlineTool

tool = ReadOutlineTool()

# Read all chapters
all_outlines = tool._run(yw7_path="my_novel.yw7")

# Read specific chapter
chapter_outline = tool._run(yw7_path="my_novel.yw7", chapter_id="ch1")
```

---

### ReadSceneTool

Reads the content of a specific scene from a yWriter 7 project file.

#### Input Schema

```python
class ReadSceneInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
    scene_id: str = Field(..., description="ID of the scene to read")
```

#### Tool Properties

| Property | Value |
|----------|-------|
| `name` | "Read Scene" |
| `description` | "Read the content of a specific scene from a yWriter 7 project file." |

#### Returns

JSON-formatted scene data:
```json
{
    "ID": "sc1",
    "Title": "Scene Title",
    "Content": "Full scene text...",
    "Description": "Scene summary",
    "Tags": "tag1, tag2",
    "Notes": "Author notes"
}
```

---

### ReadItemsTool

Reads item/object data from a yWriter 7 project file.

*(Referenced in imports but implementation similar to other read tools)*

---

## Write Tools

### WriteProjectNoteTool

Writes a project note to a yWriter 7 project file.

#### Input Schema

```python
class WriteProjectNoteInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
    title: str = Field(..., description="Title of the project note")
    content: str = Field(..., description="Content of the project note")
```

#### Tool Properties

| Property | Value |
|----------|-------|
| `name` | "Write Project Note" |
| `description` | "Write a project note to a yWriter 7 project file." |

#### Returns

Success message with note ID:
```
Project note 'Story Arc' written successfully with ID: pn3.
```

#### Example

```python
from tools.ywriter_tools import WriteProjectNoteTool

tool = WriteProjectNoteTool()
result = tool._run(
    yw7_path="my_novel.yw7",
    title="Story Arc",
    content="Act 1: Introduction..."
)
```

---

### CreateChapterTool

Creates a new chapter in a yWriter 7 project file.

#### Input Schema

```python
class CreateChapterInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
    title: str = Field(..., description="Title of the new chapter")
    description: Optional[str] = Field(None, description="Description of the chapter")
```

#### Tool Properties

| Property | Value |
|----------|-------|
| `name` | "Create Chapter" |
| `description` | "Create a new chapter in a yWriter 7 project file." |

#### Returns

Success message with chapter ID:
```
Chapter 'The Beginning' created successfully with ID: ch5.
```

#### Chapter Properties Set

| Property | Value |
|----------|-------|
| `chLevel` | 0 (Normal chapter) |
| `chType` | 0 (Normal type) |
| `srtScenes` | [] (Empty scene list) |

#### Example

```python
from tools.ywriter_tools import CreateChapterTool

tool = CreateChapterTool()
result = tool._run(
    yw7_path="my_novel.yw7",
    title="Chapter One: The Beginning",
    description="Our hero starts their journey"
)
```

---

### WriteSceneContentTool

Writes content to a specific scene in a yWriter 7 project file.

#### Input Schema

```python
class WriteSceneContentInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
    scene_id: str = Field(..., description="ID of the scene to write to")
    content: str = Field(..., description="Content to write to the scene")
```

#### Tool Properties

| Property | Value |
|----------|-------|
| `name` | "Write Scene Content" |
| `description` | "Write content to a specific scene in a yWriter 7 project file." |

#### Returns

Success message:
```
Content written to scene 'sc1' successfully.
```

#### Example

```python
from tools.ywriter_tools import WriteSceneContentTool

tool = WriteSceneContentTool()
result = tool._run(
    yw7_path="my_novel.yw7",
    scene_id="sc1",
    content="The morning sun filtered through the dusty curtains..."
)
```

---

## Error Handling

All tools return error messages as strings rather than raising exceptions:

```python
# File not found
"Error: yWriter 7 project file not found."

# Invalid file type
"Invalid file type. Expected a .yw7 file."

# General errors
"Error reading project notes: [error details]"
"Error writing project note: [error details]"
```

---

## Using Tools with CrewAI Agents

### Assigning Tools to Agents

```python
from crewai import Agent
from tools.ywriter_tools import (
    ReadProjectNotesTool,
    WriteProjectNoteTool,
    CreateChapterTool,
    ReadOutlineTool,
    ReadCharactersTool,
    ReadLocationsTool
)

# Create tools
read_tools = [
    ReadProjectNotesTool(),
    ReadOutlineTool(),
    ReadCharactersTool(),
    ReadLocationsTool()
]

write_tools = [
    WriteProjectNoteTool(),
    CreateChapterTool()
]

# Assign to agent
agent = Agent(
    role="Novel Editor",
    goal="Manage novel project files",
    backstory="Expert in yWriter project management",
    tools=read_tools + write_tools,
    verbose=True
)
```

### Tool Invocation in Tasks

When used by CrewAI agents, tools are invoked automatically based on task descriptions:

```python
from crewai import Task

task = Task(
    description="""
    Read the project notes from 'my_novel.yw7' and summarize the story arc.
    Then create a new chapter called 'Epilogue' with a brief description.
    """,
    agent=agent,
    expected_output="Summary and confirmation of chapter creation"
)
```

---

## Creating Custom Tools

### Basic Custom Tool

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class CustomToolInput(BaseModel):
    param1: str = Field(..., description="First parameter")
    param2: Optional[int] = Field(None, description="Optional parameter")

class CustomTool(BaseTool):
    name: str = "Custom Tool Name"
    description: str = "What this tool does"
    args_schema: type[BaseModel] = CustomToolInput

    def _run(self, param1: str, param2: int = None, **kwargs) -> str:
        # Implementation
        result = f"Processed {param1}"
        if param2:
            result += f" with value {param2}"
        return result
```

### Tool with yWriter Integration

```python
from tools.ywriter_tools import load_yw7_file

class CustomYWriterTool(BaseTool):
    name: str = "Custom yWriter Tool"
    description: str = "Custom operation on yWriter files"

    def _run(self, yw7_path: str, **kwargs) -> str:
        try:
            yw7_file = load_yw7_file(yw7_path)
            # Custom operations on yw7_file.novel
            return "Success"
        except FileNotFoundError:
            return "Error: yWriter 7 project file not found."
        except Exception as e:
            return f"Error: {e}"
```

---

## Placeholder Tools

The following tools are defined but have placeholder implementations:

### ChapterBreakdownTool

```python
class ChapterBreakdownTool(BaseTool):
    name: str = "Chapter Breakdown Tool"
    description: str = "Assists in dividing the story arc into chapters with appropriate pacing."

    def _run(self, **kwargs) -> str:
        return "Chapter breakdown logic executed."
```

### OutlineTemplateTool

```python
class OutlineTemplateTool(BaseTool):
    name: str = "Outline Template Tool"
    description: str = "Formats the outline according to genre conventions and project requirements."

    def _run(self, **kwargs) -> str:
        return "Outline formatting logic executed."
```

These are intended for future implementation to enhance the outline creation process.
