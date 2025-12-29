import json
import os
from typing import Optional
from uuid import uuid4

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Use absolute imports, from the ywriter7 directory:
from ywriter7.model.chapter import Chapter
from ywriter7.model.scene import Scene
from ywriter7.model.project_note import ProjectNote
from ywriter7.model.character import Character
from ywriter7.model.location import Location
from ywriter7.model.item import Item
from ywriter7.model.id_generator import create_id
from ywriter7.yw.yw7_file import Yw7File

# Helper function to load a yWriter 7 project
def load_yw7_file(file_path: str) -> Yw7File:
    """
    Loads a yWriter 7 project file.

    Args:
        file_path (str): The path to the .yw7 file.

    Returns:
        Yw7File: The loaded yWriter 7 project.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid .yw7 file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"yWriter 7 project file not found: {file_path}")

    if not file_path.lower().endswith(".yw7"):
        raise ValueError("Invalid file type. Expected a .yw7 file.")

    yw7_file = Yw7File(file_path)
    yw7_file.read()
    return yw7_file

# --- Tools for reading data ---

class ReadProjectNotesInput(BaseModel):
    yw7_path: str = Field(..., description="The path to the .yw7 file.")

class ReadProjectNotesTool(BaseTool):
    name: str = "Read Project Notes"
    description: str = "Read project notes from a yWriter 7 project file."
    args_schema: type[BaseModel] = ReadProjectNotesInput

    def _run(self, yw7_path: str, **kwargs) -> str:
        """Reads and returns project notes."""
        try:
            yw7_file = load_yw7_file(yw7_path)
            notes = yw7_file.novel.projectNotes
            if not notes:
                return "No project notes found."

            notes_data = []
            for note_id in yw7_file.novel.srtPrjNotes:
                note = notes[note_id]
                notes_data.append( f"Title: {note.title}\nContent: {note.desc}")
            return "\n---\n".join(notes_data)
        except FileNotFoundError:
            return "Error: yWriter 7 project file not found."
        except Exception as e:
            return f"Error reading project notes: {e}"

class ReadCharactersInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")

class ReadCharactersTool(BaseTool):
    name: str = "Read Characters"
    description: str = "Read character data from a yWriter 7 project file."
    args_schema: type[BaseModel] = ReadCharactersInput

    def _run(self, yw7_path: str, **kwargs) -> str:
        try:
            yw7_file = load_yw7_file(yw7_path)
            characters = yw7_file.novel.characters
            if not characters:
                return "No characters found."

            character_data = []
            for char_id in yw7_file.novel.srtCharacters:
                character = characters[char_id]
                character_info = {
                    "ID": char_id,
                    "Name": character.title,
                    "Description": character.desc,
                    "Full Name": character.fullName,
                    "Notes": character.notes,
                }
                character_data.append(json.dumps(character_info))

            return "\n".join(character_data)
        except FileNotFoundError:
            return "Error: yWriter 7 project file not found."
        except Exception as e:
            return f"Error reading characters: {e}"

class ReadLocationsInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")

class ReadLocationsTool(BaseTool):
    name: str = "Read Locations"
    description: str = "Read location data from a yWriter 7 project file."
    args_schema: type[BaseModel] = ReadLocationsInput

    def _run(self, yw7_path: str, **kwargs) -> str:
        try:
            yw7_file = load_yw7_file(yw7_path)
            locations = yw7_file.novel.locations
            if not locations:
                return "No locations found."

            location_data = []
            for loc_id in yw7_file.novel.srtLocations:
                location = locations[loc_id]
                location_info = {
                    "ID": loc_id,
                    "Name": location.title,
                    "Description": location.desc,
                    "AKA": location.aka,
                }
                location_data.append(json.dumps(location_info))

            return "\n".join(location_data)
        except FileNotFoundError:
            return "Error: yWriter 7 project file not found."
        except Exception as e:
            return f"Error reading locations: {e}"

class ReadOutlineInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
    chapter_id: Optional[str] = Field(
        None, description="Optional ID of a specific chapter to read"
    )

class ReadOutlineTool(BaseTool):
    name: str = "Read Outline"
    description: str = "Read chapter outlines from a yWriter 7 project file."
    args_schema: type[BaseModel] = ReadOutlineInput

    def _run(self, yw7_path: str, chapter_id: Optional[str] = None, **kwargs) -> str:
        try:
            yw7_file = load_yw7_file(yw7_path)
            output = ""
            for ch_id in yw7_file.novel.srtChapters:
                if chapter_id is None or ch_id == chapter_id:
                    chapter = yw7_file.novel.chapters[ch_id]
                    output += f"Chapter ID: {ch_id}, Title: {chapter.title}\n"
                    if chapter.desc:
                        output += f"Description: {chapter.desc}\n"

                    # Add Scene Summaries to the output
                    scene_summaries = []
                    for sc_id in chapter.srtScenes:
                        scene = yw7_file.novel.scenes.get(sc_id)
                        if scene:
                            scene_summaries.append(f"  Scene ID: {sc_id}, Title: {scene.title}, Summary: {scene.desc}")
                    if scene_summaries:
                        output += "  Scenes:\n" + "\n".join(scene_summaries) + "\n"

                    output += "\n"

            if not output:
                if chapter_id:
                    return f"No data found for chapter ID: {chapter_id}."
                else:
                    return "No chapter outlines found."
            return output
        except FileNotFoundError:
            return "Error: yWriter 7 project file not found."
        except Exception as e:
            return f"Error reading outline: {e}"

class ReadSceneInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
    scene_id: str = Field(..., description="ID of the scene to read")

class ReadSceneTool(BaseTool):
    name: str = "Read Scene"
    description: str = "Read the content of a specific scene from a yWriter 7 project file."
    args_schema: type[BaseModel] = ReadSceneInput

    def _run(self, yw7_path: str, scene_id: str, **kwargs) -> str:
        try:
            yw7_file = load_yw7_file(yw7_path)
            if scene_id in yw7_file.novel.scenes:
                scene = yw7_file.novel.scenes[scene_id]
                # Return scene content along with other details
                scene_info = {
                    "ID": scene_id,
                    "Title": scene.title,
                    "Content": scene.sceneContent or "Content not found.",
                    "Description": scene.desc or "Description not available.",
                    "Tags": ", ".join(scene.tags or []) or "No tags.",
                    "Notes": scene.notes or "Notes not available."
                }
                return json.dumps(scene_info)
            return "Scene not found."
        except FileNotFoundError:
            return "Error: yWriter 7 project file not found."
        except Exception as e:
            return f"Error reading scene: {e}"

# --- Tools for writing data ---

class WriteProjectNoteInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
    title: str = Field(..., description="Title of the project note")
    content: str = Field(..., description="Content of the project note")

class WriteProjectNoteTool(BaseTool):
    name: str = "Write Project Note"
    description: str = "Write a project note to a yWriter 7 project file."
    args_schema: type[BaseModel] = WriteProjectNoteInput

    def _run(self, yw7_path: str, title: str, content: str, **kwargs) -> str:
        try:
            yw7_file = load_yw7_file(yw7_path)
            note_id = create_id(yw7_file.novel.projectNotes)
            project_note = ProjectNote()
            project_note.title = title
            project_note.desc = content
            yw7_file.novel.projectNotes[note_id] = project_note
            yw7_file.novel.srtPrjNotes.append(note_id)
            yw7_file.write()
            return f"Project note '{title}' written successfully with ID: {note_id}."
        except FileNotFoundError:
            return "Error: yWriter 7 project file not found."
        except Exception as e:
            return f"Error writing project note: {e}"

class CreateChapterInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
    title: str = Field(..., description="Title of the new chapter")
    description: Optional[str] = Field(None, description="Description of the chapter")

class CreateChapterTool(BaseTool):
    name: str = "Create Chapter"
    description: str = "Create a new chapter in a yWriter 7 project file."
    args_schema: type[BaseModel] = CreateChapterInput

    def _run(
        self, yw7_path: str, title: str, description: Optional[str] = None, **kwargs
    ) -> str:
        try:
            yw7_file = load_yw7_file(yw7_path)
            chapter_id = create_id(yw7_file.novel.chapters)
            chapter = Chapter()
            chapter.title = title
            chapter.desc = description
            chapter.chLevel = 0
            chapter.chType = 0
            chapter.srtScenes = []
            yw7_file.novel.chapters[chapter_id] = chapter
            yw7_file.novel.srtChapters.append(chapter_id)
            yw7_file.write()
            return f"Chapter '{title}' created successfully with ID: {chapter_id}."
        except FileNotFoundError:
            return "Error: yWriter 7 project file not found."
        except Exception as e:
            return f"Error creating chapter: {e}"

# Writing the Scene Content
class WriteSceneContentInput(BaseModel):
    yw7_path: str = Field(..., description="Path to the .yw7 file")
    scene_id: str = Field(..., description="ID of the scene to write to")
    content: str = Field(..., description="Content to write to the scene")

class WriteSceneContentTool(BaseTool):
    name: str = "Write Scene Content"
    description: str = "Write content to a specific scene in a yWriter 7 project file."
    args_schema: type[BaseModel] = WriteSceneContentInput

    def _run(self, yw7_path: str, scene_id: str, content: str, **kwargs) -> str:
        try:
            yw7_file = load_yw7_file(yw7_path)
            if scene_id in yw7_file.novel.scenes:
                scene = yw7_file.novel.scenes[scene_id]
                scene.sceneContent = content
                yw7_file.write()
                return f"Content written to scene '{scene_id}' successfully."
            return "Scene not found."
        except FileNotFoundError:
            return "Error: yWriter 7 project file not found."
        except Exception as e:
            return f"Error writing scene content: {e}"