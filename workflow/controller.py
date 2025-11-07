"""
Workflow Controller

Manages workflow execution with pause/resume capabilities and
signal handling for graceful shutdown.
"""

import os
import sys
import signal
import logging
from typing import Optional
from pathlib import Path

from .state import WorkflowState

logger = logging.getLogger(__name__)


class WorkflowController:
    """
    Controls workflow execution with pause/resume capabilities.

    Features:
    - Graceful handling of Ctrl+C (SIGINT)
    - Support for pause files (remote pause)
    - Automatic checkpoint saving on pause
    - Resume from checkpoint
    """

    def __init__(self, state: WorkflowState):
        """
        Initialize workflow controller.

        Args:
            state: Workflow state object
        """
        self.state = state
        self.paused = False
        self.should_stop = False
        self._original_sigint_handler = None
        self._original_sigterm_handler = None

    def setup_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        # Store original handlers
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._handle_interrupt)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_interrupt)

        logger.debug("Signal handlers registered (Ctrl+C for graceful pause)")

    def cleanup_signal_handlers(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)

        logger.debug("Signal handlers restored")

    def _handle_interrupt(self, signum, frame):
        """
        Handle interrupt signal (Ctrl+C or SIGTERM).

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name

        print("\n")  # New line after ^C
        logger.info(f"⏸️  Received {signal_name}. Saving checkpoint...")

        self.paused = True
        self.should_stop = True

        # Save checkpoint
        try:
            checkpoint_path = self.state.save()
            logger.info(f"✅ Checkpoint saved successfully")
            logger.info(f"📍 Resume with: python test_complete_workflow_v2.py --project {self.state.project_name} --resume")
        except Exception as e:
            logger.error(f"❌ Failed to save checkpoint: {e}")

        # Exit gracefully
        logger.info("👋 Exiting gracefully...")
        sys.exit(0)

    def check_should_pause(self) -> bool:
        """
        Check if workflow should pause.

        Checks for:
        1. Pause file existence
        2. Manual pause flag

        Returns:
            True if workflow should pause
        """
        # Check pause file
        pause_file = self._get_pause_file_path()
        if os.path.exists(pause_file):
            logger.info(f"⏸️  Pause file detected: {pause_file}")
            self.paused = True
            self.should_stop = True

            # Remove pause file
            try:
                os.remove(pause_file)
                logger.info("🗑️  Pause file removed")
            except Exception as e:
                logger.warning(f"Failed to remove pause file: {e}")

        return self.paused or self.should_stop

    def _get_pause_file_path(self) -> str:
        """
        Get path to pause file.

        Returns:
            Path to pause file
        """
        return f"output/{self.state.project_name}.pause"

    def create_pause_file(self):
        """
        Create pause file to trigger pause from external process.

        This allows pausing the workflow without Ctrl+C, useful for
        remote/automated workflows.
        """
        pause_file = self._get_pause_file_path()
        Path(pause_file).parent.mkdir(exist_ok=True)

        try:
            Path(pause_file).touch()
            logger.info(f"📝 Pause file created: {pause_file}")
            logger.info("   Workflow will pause at next checkpoint")
        except Exception as e:
            logger.error(f"Failed to create pause file: {e}")

    def handle_step_checkpoint(self, step_name: str) -> bool:
        """
        Handle checkpoint after a step.

        Checks for pause condition and saves checkpoint.

        Args:
            step_name: Name of the completed step

        Returns:
            True if workflow should continue, False if paused
        """
        # Save checkpoint
        self.state.save()

        # Check for pause
        if self.check_should_pause():
            logger.info(f"⏸️  Workflow paused after {step_name}")
            logger.info(f"📍 Resume with: python test_complete_workflow_v2.py --project {self.state.project_name} --resume")
            return False

        return True

    def print_resume_instructions(self):
        """Print instructions for resuming the workflow."""
        print("\n" + "="*80)
        print("⏸️  WORKFLOW PAUSED")
        print("="*80)
        print(f"\nCheckpoint saved at: output/{self.state.project_name}_workflow_checkpoint.json")
        print(f"\nTo resume:")
        print(f"  python test_complete_workflow_v2.py --project {self.state.project_name} --resume")
        print("\n" + "="*80 + "\n")

    def __enter__(self):
        """Context manager entry."""
        self.setup_signal_handlers()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup_signal_handlers()

        # If exception occurred, save checkpoint
        if exc_type is not None:
            logger.error(f"❌ Exception during workflow: {exc_val}")
            try:
                self.state.save()
                logger.info("💾 Emergency checkpoint saved")
            except Exception as save_err:
                logger.error(f"Failed to save emergency checkpoint: {save_err}")

        return False  # Don't suppress exceptions


def get_pause_file_path(project_name: str) -> str:
    """
    Get path to pause file for a project.

    Args:
        project_name: Name of the project

    Returns:
        Path to pause file
    """
    return f"output/{project_name}.pause"


def create_pause_file(project_name: str):
    """
    Create pause file to trigger pause.

    This is a utility function that can be called externally
    to pause a running workflow.

    Args:
        project_name: Name of the project to pause
    """
    pause_file = get_pause_file_path(project_name)
    Path(pause_file).parent.mkdir(exist_ok=True)

    try:
        Path(pause_file).touch()
        print(f"✅ Pause file created: {pause_file}")
        print("   Workflow will pause at next checkpoint")
    except Exception as e:
        print(f"❌ Failed to create pause file: {e}")


def remove_pause_file(project_name: str):
    """
    Remove pause file.

    Args:
        project_name: Name of the project
    """
    pause_file = get_pause_file_path(project_name)

    if os.path.exists(pause_file):
        try:
            os.remove(pause_file)
            print(f"✅ Pause file removed: {pause_file}")
        except Exception as e:
            print(f"❌ Failed to remove pause file: {e}")
    else:
        print(f"ℹ️  No pause file found: {pause_file}")


# CLI utility for creating/removing pause files
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Workflow pause file utility")
    parser.add_argument('action', choices=['create', 'remove'], help='Action to perform')
    parser.add_argument('project', help='Project name')

    args = parser.parse_args()

    if args.action == 'create':
        create_pause_file(args.project)
    elif args.action == 'remove':
        remove_pause_file(args.project)
