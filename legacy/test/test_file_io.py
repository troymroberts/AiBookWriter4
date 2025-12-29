import unittest
import tempfile
import os
from crewai import Agent, Task

# Import your agent definitions (or a subset for this test)
from crew import (
    StoryPlanner,
    StoryPlannerConfig,
    OutlineCreator,
    OutlineCreatorConfig,
    # ... other agents you want to test
)

class FileIOTest(unittest.TestCase):

    def setUp(self):
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".txt")
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

        # Create a minimal LLM configuration for the dummy agent
        self.minimal_llm_config = {
            "llm_endpoint": "http://localhost:11434",
            "llm_model": "ollama/llama3:latest",
            "temperature": 0.5,
            "max_tokens": 100,
            "top_p": 0.9,
        }

    def tearDown(self):
        # Clean up the temporary file
        os.unlink(self.temp_file_path)

    def test_dummy_agent_file_io(self):
        # Create a dummy agent with minimal configuration
        dummy_agent = StoryPlanner(config=StoryPlannerConfig(**self.minimal_llm_config))

        # Define a simple write task
        write_task = Task(
            description=f'Write "Hello from Dummy" to the file: {self.temp_file_path}',
            agent=dummy_agent,
            tools=[
                type(
                    "WriteToFile",
                    (BaseTool,),
                    {
                        "name": "WriteToFile",
                        "description": f"Write text to a file. Input should be a JSON string with 'content' and 'path' keys. The path should be: {self.temp_file_path}",
                        "args_schema": type(
                            "WriteToFileInput",
                            (BaseModel,),
                            {
                                "content": Field(..., description="Text to write"),
                                "path": Field(..., description="File path"),
                            },
                        ),
                        "_run": lambda self, content, path: self._write_to_file(content, path),
                        "_write_to_file": lambda _, content, path: self._write_to_file(content, path),
                    },
                )()
            ],
        )

        # Define a simple read task
        read_task = Task(
            description=f"Read the content of the file: {self.temp_file_path}",
            agent=dummy_agent,
            tools=[
                type(
                    "ReadFromFile",
                    (BaseTool,),
                    {
                        "name": "ReadFromFile",
                        "description": f"Read text from a file. Input should be the file path. The path should be: {self.temp_file_path}",
                        "args_schema": type(
                            "ReadFromFileInput",
                            (BaseModel,),
                            {"path": Field(..., description="File path")},
                        ),
                        "_run": lambda self, path: self._read_from_file(path),
                        "_read_from_file": lambda _, path: self._read_from_file(path),
                    },
                )()
            ],
        )

        # Execute the tasks
        write_task.execute(
            json.dumps({"content": "Hello from Dummy", "path": self.temp_file_path})
        )
        read_result = read_task.execute(self.temp_file_path)

        # Assertions
        self.assertEqual(
            read_result, "Hello from Dummy", "File content does not match."
        )

    def _write_to_file(self, content, path):
        """Helper function to write to a file."""
        with open(path, "w") as f:
            f.write(content)
        return "Content written to file."

    def _read_from_file(self, path):
        """Helper function to read from a file."""
        with open(path, "r") as f:
            return f.read()

if __name__ == "__main__":
    unittest.main()