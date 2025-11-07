"""
Workflow State Management

Provides checkpoint and resume functionality for the book generation workflow.
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkflowState:
    """
    Complete workflow state for pause/resume functionality.

    Tracks completion of each workflow step and stores relevant data
    to enable resuming from any point in the workflow.
    """

    # Define all workflow steps in order
    WORKFLOW_STEPS = [
        'story_planning',
        'character_creation',
        'location_creation',
        'chapter_outlining',
        'scene_structuring',
        'prose_writing',
        'editorial_refinement',
        'rag_sync'
    ]

    def __init__(self, project_name: str, project_path: str):
        """
        Initialize workflow state.

        Args:
            project_name: Name of the project (e.g., "Ten_Chapter_Novel")
            project_path: Path to the yWriter7 file
        """
        self.project_name = project_name
        self.project_path = project_path

        # Step completion tracking
        self.completed_steps: List[str] = []
        self.current_step: Optional[str] = None
        self.failed_step: Optional[str] = None

        # Step-specific state
        self.story_arc: Optional[str] = None
        self.characters_created: List[str] = []  # List of character IDs
        self.locations_created: List[str] = []   # List of location IDs
        self.chapters_outlined: List[str] = []   # List of chapter IDs
        self.scenes_structured: List[str] = []   # List of scene IDs
        self.scenes_written: List[str] = []      # List of scene IDs
        self.scenes_edited: List[str] = []       # List of scene IDs

        # Metadata
        self.start_time: Optional[str] = None
        self.last_checkpoint_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.total_api_calls: int = 0
        self.provider_usage: Dict[str, int] = {}  # {provider: call_count}

        # Error tracking
        self.errors: List[Dict[str, Any]] = []  # [{step, error, timestamp, recovery_action}]

        # Configuration
        self.genre: Optional[str] = None
        self.num_chapters: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON serialization."""
        return {
            'project_name': self.project_name,
            'project_path': self.project_path,
            'completed_steps': self.completed_steps,
            'current_step': self.current_step,
            'failed_step': self.failed_step,
            'story_arc': self.story_arc,
            'characters_created': self.characters_created,
            'locations_created': self.locations_created,
            'chapters_outlined': self.chapters_outlined,
            'scenes_structured': self.scenes_structured,
            'scenes_written': self.scenes_written,
            'scenes_edited': self.scenes_edited,
            'start_time': self.start_time,
            'last_checkpoint_time': self.last_checkpoint_time,
            'end_time': self.end_time,
            'total_api_calls': self.total_api_calls,
            'provider_usage': self.provider_usage,
            'errors': self.errors,
            'genre': self.genre,
            'num_chapters': self.num_chapters,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """Create state from dictionary."""
        state = cls(data['project_name'], data['project_path'])

        state.completed_steps = data.get('completed_steps', [])
        state.current_step = data.get('current_step')
        state.failed_step = data.get('failed_step')
        state.story_arc = data.get('story_arc')
        state.characters_created = data.get('characters_created', [])
        state.locations_created = data.get('locations_created', [])
        state.chapters_outlined = data.get('chapters_outlined', [])
        state.scenes_structured = data.get('scenes_structured', [])
        state.scenes_written = data.get('scenes_written', [])
        state.scenes_edited = data.get('scenes_edited', [])
        state.start_time = data.get('start_time')
        state.last_checkpoint_time = data.get('last_checkpoint_time')
        state.end_time = data.get('end_time')
        state.total_api_calls = data.get('total_api_calls', 0)
        state.provider_usage = data.get('provider_usage', {})
        state.errors = data.get('errors', [])
        state.genre = data.get('genre')
        state.num_chapters = data.get('num_chapters')

        return state

    def save(self, checkpoint_dir: str = "output") -> str:
        """
        Save state to checkpoint file.

        Args:
            checkpoint_dir: Directory to save checkpoint

        Returns:
            Path to checkpoint file
        """
        Path(checkpoint_dir).mkdir(exist_ok=True)
        checkpoint_path = os.path.join(
            checkpoint_dir,
            f"{self.project_name}_workflow_checkpoint.json"
        )

        data = self.to_dict()
        data['last_checkpoint_time'] = datetime.now().isoformat()

        with open(checkpoint_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"💾 Checkpoint saved: {checkpoint_path}")
        return checkpoint_path

    @classmethod
    def load(cls, project_name: str, checkpoint_dir: str = "output") -> Optional['WorkflowState']:
        """
        Load state from checkpoint file.

        Args:
            project_name: Name of the project
            checkpoint_dir: Directory containing checkpoint

        Returns:
            WorkflowState if checkpoint exists, None otherwise
        """
        checkpoint_path = os.path.join(
            checkpoint_dir,
            f"{project_name}_workflow_checkpoint.json"
        )

        if not os.path.exists(checkpoint_path):
            logger.info(f"No checkpoint found: {checkpoint_path}")
            return None

        try:
            with open(checkpoint_path, 'r') as f:
                data = json.load(f)

            state = cls.from_dict(data)
            logger.info(f"📂 Checkpoint loaded: {checkpoint_path}")
            logger.info(f"   Completed steps: {', '.join(state.completed_steps) if state.completed_steps else 'none'}")
            logger.info(f"   Current step: {state.current_step or 'none'}")

            return state

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def can_skip_step(self, step_name: str) -> bool:
        """
        Check if a step can be skipped (already completed).

        Args:
            step_name: Name of the step to check

        Returns:
            True if step is already completed
        """
        return step_name in self.completed_steps

    def mark_step_start(self, step_name: str):
        """
        Mark a step as started.

        Args:
            step_name: Name of the step
        """
        self.current_step = step_name
        if not self.start_time:
            self.start_time = datetime.now().isoformat()
        logger.info(f"🚀 Starting step: {step_name}")

    def mark_step_complete(self, step_name: str, result_summary: Optional[str] = None):
        """
        Mark a step as completed.

        Args:
            step_name: Name of the completed step
            result_summary: Optional summary of the result
        """
        if step_name not in self.completed_steps:
            self.completed_steps.append(step_name)

        self.current_step = None
        self.failed_step = None

        logger.info(f"✅ Completed step: {step_name}")
        if result_summary:
            logger.info(f"   {result_summary}")

        self.save()

    def mark_step_failed(self, step_name: str, error: Exception):
        """
        Mark a step as failed.

        Args:
            step_name: Name of the failed step
            error: The exception that caused the failure
        """
        self.failed_step = step_name
        self.current_step = None

        error_entry = {
            'step': step_name,
            'error': str(error),
            'error_type': type(error).__name__,
            'timestamp': datetime.now().isoformat()
        }
        self.errors.append(error_entry)

        logger.error(f"❌ Step failed: {step_name} - {error}")
        self.save()

    def increment_api_calls(self, provider: str):
        """
        Increment API call counter.

        Args:
            provider: Name of the LLM provider
        """
        self.total_api_calls += 1
        self.provider_usage[provider] = self.provider_usage.get(provider, 0) + 1

    def get_progress_percentage(self) -> float:
        """
        Calculate workflow completion percentage.

        Returns:
            Percentage complete (0-100)
        """
        if not self.WORKFLOW_STEPS:
            return 0.0

        return (len(self.completed_steps) / len(self.WORKFLOW_STEPS)) * 100

    def get_next_step(self) -> Optional[str]:
        """
        Get the next step to execute.

        Returns:
            Name of next step, or None if all complete
        """
        for step in self.WORKFLOW_STEPS:
            if step not in self.completed_steps:
                return step
        return None

    def get_status_report(self) -> Dict[str, Any]:
        """
        Generate a status report.

        Returns:
            Dictionary with status information
        """
        return {
            'project_name': self.project_name,
            'progress': f"{self.get_progress_percentage():.1f}%",
            'completed_steps': self.completed_steps,
            'current_step': self.current_step,
            'failed_step': self.failed_step,
            'next_step': self.get_next_step(),
            'total_errors': len(self.errors),
            'total_api_calls': self.total_api_calls,
            'provider_usage': self.provider_usage,
            'scenes_written': len(self.scenes_written),
            'scenes_edited': len(self.scenes_edited),
            'start_time': self.start_time,
            'last_checkpoint': self.last_checkpoint_time,
        }

    def print_status(self):
        """Print a formatted status report."""
        report = self.get_status_report()

        print("\n" + "="*80)
        print(f"📊 Workflow Status: {report['project_name']}")
        print("="*80)
        print(f"Progress: {report['progress']}")
        print(f"\nCompleted Steps:")
        for step in report['completed_steps']:
            print(f"  ✅ {step}")

        if report['current_step']:
            print(f"\nCurrent Step:")
            print(f"  ⏳ {report['current_step']}")

        if report['next_step']:
            print(f"\nNext Step:")
            print(f"  ⏭️  {report['next_step']}")

        if report['failed_step']:
            print(f"\nFailed Step:")
            print(f"  ❌ {report['failed_step']}")

        print(f"\nStatistics:")
        print(f"  API Calls: {report['total_api_calls']}")
        print(f"  Errors: {report['total_errors']}")
        print(f"  Scenes Written: {report['scenes_written']}")
        print(f"  Scenes Edited: {report['scenes_edited']}")

        if report['provider_usage']:
            print(f"\nProvider Usage:")
            for provider, count in report['provider_usage'].items():
                print(f"  {provider}: {count} calls")

        print("="*80 + "\n")

    def __repr__(self) -> str:
        return (
            f"WorkflowState(project='{self.project_name}', "
            f"completed={len(self.completed_steps)}/{len(self.WORKFLOW_STEPS)}, "
            f"current='{self.current_step}')"
        )
