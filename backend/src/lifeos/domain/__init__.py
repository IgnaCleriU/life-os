"""Capa de dominio de Life OS: entidades y reglas de negocio en Python puro."""

from .exceptions import (
    DomainError,
    DomainValidationError,
    ProjectNotEmpty,
    ProjectNotFound,
    TaskNotFound,
)
from .project import Project, ProjectStatus
from .task import Priority, Task, TaskStatus

__all__ = [
    "DomainError",
    "DomainValidationError",
    "ProjectNotEmpty",
    "ProjectNotFound",
    "TaskNotFound",
    "Project",
    "ProjectStatus",
    "Task",
    "TaskStatus",
    "Priority",
]
