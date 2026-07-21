"""Entidad Task, su estado y prioridad.

Python puro (dataclasses/enums). Las transiciones de estado y las invariantes
viven acá.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from .exceptions import DomainValidationError


class TaskStatus(str, Enum):
    """Estado de una tarea dentro de su ciclo de vida."""

    TODO = "todo"
    DOING = "doing"
    DONE = "done"


class Priority(str, Enum):
    """Prioridad de una tarea."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def _validate_title(title: str) -> str:
    """Valida que el título no sea vacío y lo devuelve normalizado."""
    cleaned = title.strip()
    if not cleaned:
        raise DomainValidationError("El título de la tarea no puede estar vacío")
    return cleaned


@dataclass
class Task:
    """Una tarea perteneciente a un proyecto."""

    id: UUID
    project_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: Priority
    due_date: date | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        project_id: UUID,
        title: str,
        priority: Priority = Priority.MEDIUM,
        due_date: date | None = None,
        description: str | None = None,
    ) -> Task:
        """Crea una tarea nueva, generando id y timestamp en el dominio."""
        return cls(
            id=uuid4(),
            project_id=project_id,
            title=_validate_title(title),
            description=description,
            status=TaskStatus.TODO,
            priority=priority,
            due_date=due_date,
            created_at=datetime.now(timezone.utc),
        )

    def rename(self, new_title: str) -> None:
        """Cambia el título de la tarea, validando la invariante."""
        self.title = _validate_title(new_title)

    def change_priority(self, priority: Priority) -> None:
        """Cambia la prioridad de la tarea."""
        self.priority = priority

    def reschedule(self, due_date: date | None) -> None:
        """Reprograma la fecha límite (o la quita si es None)."""
        self.due_date = due_date

    def start(self) -> None:
        """Marca la tarea como en curso."""
        self.status = TaskStatus.DOING

    def complete(self) -> None:
        """Marca la tarea como completada (idempotente)."""
        self.status = TaskStatus.DONE

    def reopen(self) -> None:
        """Vuelve la tarea a pendiente."""
        self.status = TaskStatus.TODO
