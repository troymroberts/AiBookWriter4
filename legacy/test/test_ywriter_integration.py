# test_ywriter_integration.py
import unittest
import os
import json
from crewai import Agent, Task, Crew, Process

# Import your agent definitions and configurations from crew.py
from crew import BookWritingCrew

# Import the ywriter tools
from tools.ywriter_tools import (
    ReadProjectNotesTool,
    WriteProjectNoteTool,
    CreateChapterTool,
    ReadOutlineTool,
    ReadCharactersTool,
    ReadLocationsTool,
    ReadSceneTool,
    WriteSceneContentTool
)

# Import pywriter for direct file verification
from pywriter.yw.yw7_file import Yw7File
from pywriter.model.scene import Scene
from pywriter.model.id_generator import create_id

class YWriterIntegrationTest(unittest.TestCase):

    def setUp(self):
        # Use a test .yw7 file
        self.test_yw7_file = "test_project.yw7" 
        
        # Create a dummy .yw7 file if it doesn't exist
        if not os.path.exists(self.test_yw7_file):
            yw7_file = Yw7File(self.test_yw7_file)
            yw7_file.write()  # This creates a minimal valid .yw7 file
            
        self.crew = BookWritingCrew(ywriter_project=self.test_yw7_file)
        self.crew.kickoff()

    def tearDown(self):
        # Clean up: delete the test file after each test
        if os.path.exists(self.test_yw7_file):
            os.remove(self.test_yw7_file)

    def test_project_notes_read_write(self):
        # Test WriteProjectNoteTool
        write_task = Task(
            description=f'Write a project note titled "Test Note" with content "This is a test note.".',
            agent=self.crew.story_planner,  # Assign the task to an appropriate agent
            tools=[WriteProjectNoteTool]
        )
        write_result = write_task.execute(
            json.dumps({"yw7_path": self.test_yw7_file, "title": "Test Note", "content": "This is a test note."})
        )
        self.assertEqual(write_result, "Project note 'Test Note' written successfully.")

        # Test ReadProjectNotesTool
        read_task = Task(
            description="Read all project notes.",
            agent=self.crew.story_planner,
            tools=[ReadProjectNotesTool]
        )
        read_result = read_task.execute(json.dumps({"yw7_path": self.test_yw7_file}))
        self.assertIn("Test Note", read_result)
        self.assertIn("This is a test note.", read_result)

        # Verify with pywriter
        yw7_file = Yw7File(self.test_yw7_file)
        yw7_file.read()
        self.assertIn("Test Note", [note.title for note in yw7_file.novel.projectNotes.values()])

    def test_create_chapter(self):
        # Test CreateChapterTool
        create_chapter_task = Task(
            description='Create a new chapter titled "Chapter 1".',
            agent=self.crew.outline_creator,
            tools=[CreateChapterTool]
        )
        create_result = create_chapter_task.execute(
            json.dumps({"yw7_path": self.test_yw7_file, "title": "Chapter 1", "description": "Chapter 1 Description"})
        )
        self.assertIn("Chapter 'Chapter 1' created successfully", create_result)

        # Verify with pywriter
        yw7_file = Yw7File(self.test_yw7_file)
        yw7_file.read()
        self.assertIn("Chapter 1", [chapter.title for chapter in yw7_file.novel.chapters.values()])

    def test_read_characters(self):
        # Test ReadCharactersTool
        read_characters_task = Task(
            description="Read all characters.",
            agent=self.crew.character_creator,
            tools=[ReadCharactersTool]
        )

        read_result = read_characters_task.execute(json.dumps({"yw7_path": self.test_yw7_file}))

        # Assert that the result is not empty or an error message
        self.assertNotEqual(read_result, "", "ReadCharactersTool returned an empty string.")
        self.assertNotEqual(read_result, "No characters found.", "ReadCharactersTool reported no characters found.")
        self.assertNotIn("Error", read_result, "ReadCharactersTool encountered an error.")

    def test_read_locations(self):
        # Test ReadLocationsTool
        read_locations_task = Task(
            description="Read all locations.",
            agent=self.crew.setting_builder,
            tools=[ReadLocationsTool]
        )

        read_result = read_locations_task.execute(json.dumps({"yw7_path": self.test_yw7_file}))

        # Assert that the result is not empty or an error message
        self.assertNotEqual(read_result, "", "ReadLocationsTool returned an empty string.")
        self.assertNotEqual(read_result, "No locations found.", "ReadLocationsTool reported no locations found.")
        self.assertNotIn("Error", read_result, "ReadLocationsTool encountered an error.")

    def test_read_outline(self):
        # Test ReadOutlineTool
        read_outline_task = Task(
            description="Read the outline of all chapters.",
            agent=self.crew.outline_creator,
            tools=[ReadOutlineTool]
        )

        read_result = read_outline_task.execute(json.dumps({"yw7_path": self.test_yw7_file}))

        # Assert that the result is not empty or an error message
        self.assertNotEqual(read_result, "", "ReadOutlineTool returned an empty string.")
        self.assertNotEqual(read_result, "No chapter outlines found.", "ReadOutlineTool reported no outlines found.")
        self.assertNotIn("Error", read_result, "ReadOutlineTool encountered an error.")

    def test_write_and_read_scene_content(self):
        # Test WriteSceneContentTool
        write_scene_task = Task(
            description="Create a new chapter.",
            agent=self.crew.writer,  # Assuming the Writer agent has the tool
            tools=[CreateChapterTool]
        )
        
        write_result = write_scene_task.execute(
            json.dumps({"yw7_path": self.test_yw7_file, "title": "Test Chapter for Scene", "description": "Test Description"})
        )
        
        # Extract chapter ID from the result
        chapter_id = write_result.split("ID: ")[1].replace(".", "")
        
        # Create a new scene using the retrieved chapter ID
        yw7_file = Yw7File(self.test_yw7_file)
        yw7_file.read()
        scene_id = create_id(yw7_file.novel.scenes)
        scene = Scene()
        scene.title = "Test Scene"
        scene.sceneContent = "This is a test scene content."
        yw7_file.novel.scenes[scene_id] = scene
        yw7_file.novel.chapters[chapter_id].srtScenes.append(scene_id)
        yw7_file.write()
        
        write_scene_task = Task(
            description=f'Write content to scene {scene_id}.',
            agent=self.crew.writer,  # Assuming the Writer agent has the tool
            tools=[WriteSceneContentTool]