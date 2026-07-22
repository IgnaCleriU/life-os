"""Puertos de la capa de aplicación: contratos de persistencia (`Protocol`)."""

from .project_repository import ProjectRepository
from .task_repository import TaskRepository

__all__ = [
    "ProjectRepository",
    "TaskRepository",
]
