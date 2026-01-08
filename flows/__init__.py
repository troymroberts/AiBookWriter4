# AiBookWriter4 Flows Module
# CrewAI Flow-based orchestration for book generation

# IMPORTANT: Import IPv4 fix FIRST before any network-using modules
from . import ipv4_fix  # noqa: F401 - side effect import

from .state import BookState
from .book_writer_flow import BookWriterFlow

__all__ = ["BookState", "BookWriterFlow"]
