import time
import logging
from datetime import datetime

class WritingProgress:
    def __init__(self, total_chapters):
        self.total_chapters = total_chapters
        self.completed_chapters = 0
        self.chapter_start_times = {}  # Track start time of each chapter
        self.chapter_completion_times = {} # Track completion time of each chapter

    def start_chapter(self, chapter_id):
        """Record the start time of a chapter."""
        self.chapter_start_times[chapter_id] = time.time()

    def complete_chapter(self, chapter_id):
        """Record the completion of a chapter and update progress."""
        if chapter_id in self.chapter_start_times:
            time_taken = time.time() - self.chapter_start_times[chapter_id]
            self.chapter_completion_times[chapter_id] = time_taken
            self.completed_chapters += 1

    def get_average_chapter_time(self):
        """Calculate the average time taken to complete a chapter."""
        if not self.chapter_completion_times:
            return None
        return sum(self.chapter_completion_times.values()) / len(self.chapter_completion_times)

    def estimate_completion_time(self):
        """Estimate the remaining time to complete the book."""
        average_time = self.get_average_chapter_time()
        if average_time is None:
            return None
        remaining_chapters = self.total_chapters - self.completed_chapters
        return remaining_chapters * average_time

    def get_progress_summary(self):
        """Generate a summary of the writing progress."""
        average_time = self.get_average_chapter_time()
        estimated_remaining_time = self.estimate_completion_time()

        summary = f"Total Chapters: {self.total_chapters}\n"
        summary += f"Completed Chapters: {self.completed_chapters}\n"
        if average_time is not None:
            summary += f"Average Time per Chapter: {average_time:.2f} seconds\n"
        if estimated_remaining_time is not None:
            summary += f"Estimated Time Remaining: {estimated_remaining_time:.2f} seconds\n"
        return summary

class WritingProgressMonitor:
    def __init__(self, total_chapters):
        self.logger = logging.getLogger('book_writing')
        self.logger.setLevel(logging.INFO)  # Set the logging level (INFO, DEBUG, etc.)
        
        # Configure a handler to write log messages to a file.
        log_file = 'writing_log.txt'
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.start_time = None
        self.metrics = {}
        self.progress = WritingProgress(total_chapters)

    def start_session(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting writing session at {self.start_time}")

    def log_agent_action(self, agent_name, action, details=""):
        self.logger.info(f"{agent_name}: {action} - {details}")

    def track_metric(self, name, value):
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    def start_chapter(self, chapter_id):
        self.progress.start_chapter(chapter_id)
        self.logger.info(f"Starting chapter: {chapter_id}")

    def complete_chapter(self, chapter_id):
        self.progress.complete_chapter(chapter_id)
        self.logger.info(f"Completed chapter: {chapter_id}")

    def log_progress_summary(self):
        summary = self.progress.get_progress_summary()
        self.logger.info(summary)

    def end_session(self):
        end_time = datetime.now()
        duration = end_time - self.start_time
        self.logger.info(f"Ending writing session at {end_time}")
        self.logger.info(f"Total session duration: {duration}")
        self.log_progress_summary()