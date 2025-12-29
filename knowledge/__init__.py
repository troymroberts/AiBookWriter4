"""
AiBookWriter4 - Knowledge Sources
Custom knowledge sources for CrewAI integration.
"""

from .ywriter7_knowledge_source import YWriter7KnowledgeSource
from .character_knowledge import CharacterKnowledgeSource
from .world_knowledge import WorldKnowledgeSource

__all__ = [
    'YWriter7KnowledgeSource',
    'CharacterKnowledgeSource',
    'WorldKnowledgeSource',
]
