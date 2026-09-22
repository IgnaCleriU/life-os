"""Puertos de la capa de aplicación: contratos de persistencia (`Protocol`)."""

from .project_repository import ProjectRepository
from .revision_source import RevisionSource
from .task_repository import TaskRepository

__all__ = [
    "ProjectRepository",
    "RevisionSource",
    "TaskRepository",
]
