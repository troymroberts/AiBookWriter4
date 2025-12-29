# yWriter 7 Integration

## Overview

AiBookWriter4 includes an embedded implementation of PyWriter, providing full integration with yWriter 7 project files (`.yw7`). This enables:

- Export generated content to professional writing software
- Read existing projects for continuation or analysis
- Manage chapters, scenes, characters, locations, and items
- Preserve project structure and metadata

## yWriter 7 Background

[yWriter](http://spacejock.com/yWriter7.html) is a free word processor designed for writing novels. It organizes projects into:

- **Chapters**: Main structural divisions
- **Scenes**: Individual scenes within chapters
- **Characters**: Character profiles with notes
- **Locations**: Setting descriptions
- **Items**: Objects/props in the story
- **Project Notes**: Miscellaneous notes and planning

## File Format

yWriter 7 uses `.yw7` files, which are XML-based project containers storing:

```
project.yw7
├── PROJECT metadata
├── CHAPTERS[]
│   └── SCENES[]
├── CHARACTERS[]
├── LOCATIONS[]
├── ITEMS[]
└── PROJECTNOTES[]
```

---

## Library Structure

**Location:** `ywriter7/`

```
ywriter7/
├── model/           # Data models
│   ├── novel.py         # Main Novel container
│   ├── chapter.py       # Chapter model
│   ├── scene.py         # Scene model
│   ├── character.py     # Character model
│   ├── location.py      # Location model
│   ├── item.py          # Item model
│   ├── project_note.py  # Project note model
│   ├── id_generator.py  # UUID generation
│   └── cross_references.py  # Element relationships
├── file/            # File I/O operations
├── yw/              # yWriter format handlers
│   └── yw7_file.py      # Main file handler (1,703 lines)
├── ui/              # UI components
├── config/          # Configuration
└── test/            # Tests
```

---

## Core Classes

### Novel

**Location:** `ywriter7/model/novel.py`

The main container for all project data.

#### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `title` | str | Project title |
| `desc` | str | Project description |
| `authorName` | str | Author name |
| `chapters` | dict | Chapter objects by ID |
| `scenes` | dict | Scene objects by ID |
| `characters` | dict | Character objects by ID |
| `locations` | dict | Location objects by ID |
| `items` | dict | Item objects by ID |
| `projectNotes` | dict | Project notes by ID |
| `srtChapters` | list | Ordered chapter IDs |
| `srtCharacters` | list | Ordered character IDs |
| `srtLocations` | list | Ordered location IDs |
| `srtItems` | list | Ordered item IDs |
| `srtPrjNotes` | list | Ordered project note IDs |

---

### Chapter

**Location:** `ywriter7/model/chapter.py`

Represents a chapter in the novel.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `title` | str | Chapter title |
| `desc` | str | Chapter description/summary |
| `chLevel` | int | Chapter level (0=normal, 1=part) |
| `chType` | int | Chapter type (0=normal, 1=notes, 2=todo) |
| `srtScenes` | list | Ordered scene IDs in this chapter |

---

### Scene

**Location:** `ywriter7/model/scene.py`

Represents a scene within a chapter.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `title` | str | Scene title |
| `desc` | str | Scene summary/description |
| `sceneContent` | str | Full scene text content |
| `notes` | str | Author notes |
| `tags` | list | Scene tags |
| `status` | int | Scene status |
| `characters` | list | Character IDs in scene |
| `locations` | list | Location IDs in scene |
| `items` | list | Item IDs in scene |

---

### Character

**Location:** `ywriter7/model/character.py`

Represents a character in the novel.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `title` | str | Character name |
| `desc` | str | Character description |
| `fullName` | str | Full character name |
| `notes` | str | Character notes |
| `aka` | str | Also known as |
| `bio` | str | Character biography |
| `goals` | str | Character goals |

---

### Location

**Location:** `ywriter7/model/location.py`

Represents a location/setting.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `title` | str | Location name |
| `desc` | str | Location description |
| `aka` | str | Also known as |

---

### Item

**Location:** `ywriter7/model/item.py`

Represents an object/item in the story.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `title` | str | Item name |
| `desc` | str | Item description |
| `aka` | str | Also known as |

---

### ProjectNote

**Location:** `ywriter7/model/project_note.py`

Represents a project note (planning, research, etc.).

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `title` | str | Note title |
| `desc` | str | Note content |

---

## Yw7File Handler

**Location:** `ywriter7/yw/yw7_file.py`

Main class for reading and writing `.yw7` files.

### Usage

```python
from ywriter7.yw.yw7_file import Yw7File

# Read existing project
yw7 = Yw7File("my_novel.yw7")
yw7.read()

# Access data
print(yw7.novel.title)
for ch_id in yw7.novel.srtChapters:
    chapter = yw7.novel.chapters[ch_id]
    print(f"Chapter: {chapter.title}")

# Modify and save
yw7.novel.title = "New Title"
yw7.write()
```

### Methods

| Method | Description |
|--------|-------------|
| `read()` | Load project from file |
| `write()` | Save project to file |

---

## ID Generation

**Location:** `ywriter7/model/id_generator.py`

Generates unique IDs for new elements.

```python
from ywriter7.model.id_generator import create_id

# Create new chapter ID
chapter_id = create_id(yw7.novel.chapters)  # Returns "ch1", "ch2", etc.

# Create new scene ID
scene_id = create_id(yw7.novel.scenes)  # Returns "sc1", "sc2", etc.
```

---

## Integration Examples

### Reading a Project

```python
from ywriter7.yw.yw7_file import Yw7File

# Load project
yw7 = Yw7File("novel.yw7")
yw7.read()

# Get project info
print(f"Title: {yw7.novel.title}")
print(f"Author: {yw7.novel.authorName}")
print(f"Chapters: {len(yw7.novel.chapters)}")
print(f"Characters: {len(yw7.novel.characters)}")

# Iterate chapters
for ch_id in yw7.novel.srtChapters:
    chapter = yw7.novel.chapters[ch_id]
    print(f"\n{chapter.title}")
    print(f"  Description: {chapter.desc}")

    # Iterate scenes in chapter
    for sc_id in chapter.srtScenes:
        scene = yw7.novel.scenes[sc_id]
        print(f"  - {scene.title}: {scene.desc[:50]}...")
```

### Creating a New Project

```python
from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.novel import Novel
from ywriter7.model.chapter import Chapter
from ywriter7.model.scene import Scene
from ywriter7.model.id_generator import create_id

# Create new project
yw7 = Yw7File("new_novel.yw7")
yw7.novel = Novel()
yw7.novel.title = "My New Novel"
yw7.novel.authorName = "AI Author"

# Add a chapter
ch_id = create_id(yw7.novel.chapters)
chapter = Chapter()
chapter.title = "Chapter One"
chapter.desc = "The beginning of our story"
chapter.chLevel = 0
chapter.chType = 0
chapter.srtScenes = []
yw7.novel.chapters[ch_id] = chapter
yw7.novel.srtChapters.append(ch_id)

# Add a scene to the chapter
sc_id = create_id(yw7.novel.scenes)
scene = Scene()
scene.title = "Opening Scene"
scene.desc = "Introduction to the protagonist"
scene.sceneContent = "The morning sun filtered through dusty curtains..."
yw7.novel.scenes[sc_id] = scene
chapter.srtScenes.append(sc_id)

# Save project
yw7.write()
```

### Adding Characters and Locations

```python
from ywriter7.model.character import Character
from ywriter7.model.location import Location
from ywriter7.model.id_generator import create_id

# Add character
char_id = create_id(yw7.novel.characters)
character = Character()
character.title = "John Smith"
character.fullName = "Jonathan Michael Smith"
character.desc = "A weary detective seeking redemption"
character.bio = "Born in Chicago, 1975..."
character.goals = "Find the truth about his partner's death"
yw7.novel.characters[char_id] = character
yw7.novel.srtCharacters.append(char_id)

# Add location
loc_id = create_id(yw7.novel.locations)
location = Location()
location.title = "The Old Pier"
location.desc = "A weathered wooden pier at the edge of town"
location.aka = "Murphy's Landing"
yw7.novel.locations[loc_id] = location
yw7.novel.srtLocations.append(loc_id)

# Save
yw7.write()
```

### Using with AI Agents

```python
from tools.ywriter_tools import (
    load_yw7_file,
    ReadProjectNotesTool,
    WriteProjectNoteTool,
    CreateChapterTool
)

# Read project notes for context
read_tool = ReadProjectNotesTool()
notes = read_tool._run(yw7_path="novel.yw7")
print("Story context:", notes)

# Write AI-generated story arc as project note
write_tool = WriteProjectNoteTool()
result = write_tool._run(
    yw7_path="novel.yw7",
    title="AI Story Arc",
    content=story_arc_from_agent
)
print(result)

# Create chapters from outline
chapter_tool = CreateChapterTool()
for i, chapter_outline in enumerate(outlines):
    result = chapter_tool._run(
        yw7_path="novel.yw7",
        title=f"Chapter {i+1}: {chapter_outline['title']}",
        description=chapter_outline['summary']
    )
    print(result)
```

---

## Best Practices

### 1. Always Read Before Modifying

```python
yw7 = Yw7File("project.yw7")
yw7.read()  # Load existing data first
# Make modifications
yw7.write()  # Save changes
```

### 2. Use ID Generator for New Elements

```python
# Correct: Use create_id
chapter_id = create_id(yw7.novel.chapters)

# Incorrect: Manual IDs may conflict
chapter_id = "ch999"  # Don't do this
```

### 3. Maintain Sorted Lists

```python
# When adding elements, update both dict and sorted list
yw7.novel.chapters[ch_id] = chapter
yw7.novel.srtChapters.append(ch_id)  # Don't forget this!
```

### 4. Handle Missing Data Gracefully

```python
# Check for None values
scene_content = scene.sceneContent or "No content yet"
scene_tags = scene.tags or []
```

---

## Compatibility Notes

- **yWriter 7**: Full support for `.yw7` format
- **yWriter 6**: Not directly supported (different format)
- **yWriter 5**: Not supported

The embedded library is based on PyWriter and maintains compatibility with yWriter 7's XML schema.

---

## Troubleshooting

### File Not Found

```python
try:
    yw7 = load_yw7_file("project.yw7")
except FileNotFoundError:
    print("Project file does not exist")
```

### Invalid File Type

```python
try:
    yw7 = load_yw7_file("project.docx")
except ValueError as e:
    print(e)  # "Invalid file type. Expected a .yw7 file."
```

### Corrupted File

If a `.yw7` file is corrupted:
1. Check for backup files (yWriter creates `.yw7.bak`)
2. Open in yWriter to attempt recovery
3. Check XML structure manually

---

## Testing

Test files are located in `ywriter7/test/`:

```bash
# Run yWriter integration tests
python -m pytest ywriter7/test/

# Run specific test
python -m pytest test/test_ywriter_integration.py
```
