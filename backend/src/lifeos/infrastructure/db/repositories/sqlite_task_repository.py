"""Implementación SQLite del puerto TaskRepository."""

from __future__ import annotations

from datetime import timezone
from uuid import UUID

from sqlmodel import Session, select

from lifeos.domain import Priority, Task, TaskStatus
from lifeos.infrastructure.db.models import TaskModel


class SQLiteTaskRepository:
    """`TaskRepository` respaldado por SQLite vía SQLModel."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, task: Task) -> None:
        """Persiste una tarea nueva."""
        self._session.add(_to_model(task))
        self._session.commit()

    def get(self, task_id: UUID) -> Task | None:
        """Devuelve la tarea con ese id, o `None` si no existe."""
        model = self._session.get(TaskModel, str(task_id))
        return _to_domain(model) if model is not None else None

    def list_by_project(self, project_id: UUID) -> list[Task]:
        """Devuelve las tareas de un proyecto."""
        statement = select(TaskModel).where(TaskModel.project_id == str(project_id))
        models = self._session.exec(statement).all()
        return [_to_domain(model) for model in models]

    def update(self, task: Task) -> None:
        """Persiste los cambios de una tarea existente.

        La capa de aplicación ya hizo `get`, mutó la tarea vía métodos de
        dominio y entrega acá el estado final completo: esto es un
        reemplazo total de la fila, no un patch por campo. Se usa `merge`
        en vez de `add` porque `_to_model` siempre construye una instancia
        nueva de `TaskModel`, que puede no estar en el identity map de esta
        sesión aunque su id ya exista en la tabla.
        """
        self._session.merge(_to_model(task))
        self._session.commit()


def _to_model(task: Task) -> TaskModel:
    return TaskModel(
        id=str(task.id),
        project_id=str(task.project_id),
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        due_date=task.due_date,
        created_at=task.created_at,
    )


def _to_domain(model: TaskModel) -> Task:
    return Task(
        id=UUID(model.id),
        project_id=UUID(model.project_id),
        title=model.title,
        description=model.description,
        status=TaskStatus(model.status),
        priority=Priority(model.priority),
        due_date=model.due_date,
        created_at=model.created_at.replace(tzinfo=timezone.utc),
    )
