import json
import os

class WritingState:
    def __init__(self, project_name):
        self.project_name = project_name
        self.current_chapter_id = None
        self.current_scene_id = None
        self.completed_chapters = []
        self.completed_scenes = []
        # You can add more state variables as needed, like:
        # self.story_arc = None
        # self.character_arcs = {}

    def save_checkpoint(self, filename=None):
        """Saves the current writing state to a JSON file."""
        if filename is None:
            filename = f"{self.project_name}_checkpoint.json"

        state_data = {
            "current_chapter_id": self.current_chapter_id,
            "current_scene_id": self.current_scene_id,
            "completed_chapters": self.completed_chapters,
            "completed_scenes": self.completed_scenes,
            # Add other state variables here
        }

        with open(filename, "w") as f:
            json.dump(state_data, f, indent=4)

        print(f"Checkpoint saved to {filename}")

    def load_checkpoint(self, filename=None):
        """Loads the writing state from a JSON file."""
        if filename is None:
            filename = f"{self.project_name}_checkpoint.json"

        try:
            with open(filename, "r") as f:
                state_data = json.load(f)

            self.current_chapter_id = state_data.get("current_chapter_id")
            self.current_scene_id = state_data.get("current_scene_id")
            self.completed_chapters = state_data.get("completed_chapters", [])
            self.completed_scenes = state_data.get("completed_scenes", [])
            # Load other state variables

            print(f"Checkpoint loaded from {filename}")

        except FileNotFoundError:
            print(f"Checkpoint file not found: {filename}")