"""
AiBookWriter4 - Configuration Module
"""

from .project_types import (
    ProjectType,
    ProjectTypeConfig,
    ScaleConfig,
    StructureConfig,
    SerializationConfig,
    QualityConfig,
    FantasyConfig,
    AgentConfig,
    VectorDBConfig,
    get_project_type,
    list_project_types,
    create_custom_config,
    PROJECT_TYPES,
    STANDARD_NOVEL,
    LIGHT_NOVEL,
    LITERARY_FICTION,
    FANTASY_NOVEL,
    EPIC_FANTASY,
)

__all__ = [
    'ProjectType',
    'ProjectTypeConfig',
    'ScaleConfig',
    'StructureConfig',
    'SerializationConfig',
    'QualityConfig',
    'FantasyConfig',
    'AgentConfig',
    'VectorDBConfig',
    'get_project_type',
    'list_project_types',
    'create_custom_config',
    'PROJECT_TYPES',
    'STANDARD_NOVEL',
    'LIGHT_NOVEL',
    'LITERARY_FICTION',
    'FANTASY_NOVEL',
    'EPIC_FANTASY',
]
