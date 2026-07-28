"""Implementación SQLite del puerto TaskRepository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timezone
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from lifeos.domain import Priority, Task, TaskStatus
from lifeos.infrastructure.db.models import TaskModel


def _live() -> Any:
    """`SELECT` base que excluye las tareas borradas lógicamente.

    Toda lectura arranca de acá. Es el único lugar donde vive el filtro de
    borrado: si cada método lo escribiera por su cuenta, alcanzaría con
    olvidarlo una vez —en un método que todavía no existe— para que la TUI
    empiece a mostrar tareas borradas.
    """
    return select(TaskModel).where(TaskModel.deleted_at.is_(None))  # type: ignore[union-attr]


class SQLiteTaskRepository:
    """`TaskRepository` respaldado por SQLite vía SQLModel."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, task: Task) -> None:
        """Persiste una tarea nueva."""
        self._session.add(_to_model(task))
        self._session.commit()

    def get(self, task_id: UUID, *, include_deleted: bool = False) -> Task | None:
        """Devuelve la tarea con ese id, o `None` si no existe.

        Con `include_deleted` se usa `select(TaskModel)` pelado en vez del
        `_live()` de siempre: es el único camino que alcanza una fila borrada,
        y lo usa sólo `RestoreTask`.
        """
        statement = select(TaskModel) if include_deleted else _live()
        statement = statement.where(TaskModel.id == str(task_id))
        model = self._session.exec(statement).first()
        return _to_domain(model) if model is not None else None

    def list(
        self,
        *,
        project_id: UUID | None = None,
        statuses: Sequence[TaskStatus] | None = None,
        due_before: date | None = None,
        text: str | None = None,
    ) -> list[Task]:
        """Devuelve las tareas vivas que cumplen todos los filtros dados."""
        statement = _live()
        if project_id is not None:
            statement = statement.where(TaskModel.project_id == str(project_id))
        if statuses is not None:
            statement = statement.where(
                TaskModel.status.in_([status.value for status in statuses])  # type: ignore[attr-defined]
            )
        if due_before is not None:
            # `is_not(None)` es redundante en SQL —una comparación contra NULL
            # nunca es verdadera— pero deja explícito que "vence antes de X" no
            # incluye a las tareas sin fecha.
            statement = statement.where(
                TaskModel.due_date.is_not(None),  # type: ignore[union-attr]
                TaskModel.due_date <= due_before,  # type: ignore[operator]
            )
        if text is not None:
            statement = statement.where(TaskModel.title.ilike(f"%{text}%"))  # type: ignore[attr-defined]

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
        deleted_at=task.deleted_at,
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
        deleted_at=(
            model.deleted_at.replace(tzinfo=timezone.utc)
            if model.deleted_at is not None
            else None
        ),
    )
