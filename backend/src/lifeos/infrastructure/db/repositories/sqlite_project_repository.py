"""Implementación SQLite del puerto ProjectRepository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from lifeos.domain import Project, ProjectStatus
from lifeos.infrastructure.db.models import ProjectModel


def _live() -> Any:
    """`SELECT` base que excluye los proyectos borrados lógicamente.

    Toda lectura arranca de acá, por el mismo motivo que en
    `sqlite_task_repository`: el filtro de borrado vive en un solo lugar.

    `position` no tiene restricción de unicidad; el `order_by` secundario
    en `created_at` sólo evita que un duplicado (de existir) se muestre en
    orden no determinístico entre lecturas - no reemplaza a
    `next_position()`, que es lo que evita el duplicado en primer lugar.
    """
    return (
        select(ProjectModel)
        .where(ProjectModel.deleted_at.is_(None))  # type: ignore[union-attr]
        .order_by(ProjectModel.position, ProjectModel.created_at)
    )


class SQLiteProjectRepository:
    """`ProjectRepository` respaldado por SQLite vía SQLModel."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: Project) -> None:
        """Persiste un proyecto nuevo."""
        self._session.add(_to_model(project))
        self._session.commit()

    def get(
        self, project_id: UUID, *, include_deleted: bool = False
    ) -> Project | None:
        """Devuelve el proyecto con ese id, o `None` si no existe.

        Con `include_deleted` se alcanza una fila borrada; lo usa sólo
        `RestoreProject`.
        """
        statement = select(ProjectModel) if include_deleted else _live()
        statement = statement.where(ProjectModel.id == str(project_id))
        model = self._session.exec(statement).first()
        return _to_domain(model) if model is not None else None

    def list(
        self,
        *,
        statuses: Sequence[ProjectStatus] | None = None,
        text: str | None = None,
    ) -> list[Project]:
        """Devuelve los proyectos vivos que cumplen todos los filtros dados."""
        statement = _live()
        if statuses is not None:
            statement = statement.where(
                ProjectModel.status.in_([status.value for status in statuses])  # type: ignore[attr-defined]
            )
        if text is not None:
            statement = statement.where(ProjectModel.name.ilike(f"%{text}%"))  # type: ignore[attr-defined]

        models = self._session.exec(statement).all()
        return [_to_domain(model) for model in models]

    def update(self, project: Project) -> None:
        """Persiste los cambios de un proyecto existente.

        Mismo criterio que `SQLiteTaskRepository.update`: reemplazo total de la
        fila con `merge`, porque `_to_model` construye siempre una instancia
        nueva que puede no estar en el identity map de esta sesión.
        """
        self._session.merge(_to_model(project))
        self._session.commit()

    def next_position(self) -> int:
        """`max(position) + 1` sobre *todos* los proyectos, borrados
        incluidos (0 si no hay ninguno) - un scalar query, no un
        list-and-hydrate completo."""
        max_position = self._session.exec(select(func.max(ProjectModel.position))).one()
        return 0 if max_position is None else max_position + 1


def _to_model(project: Project) -> ProjectModel:
    return ProjectModel(
        id=str(project.id),
        name=project.name,
        description=project.description,
        status=project.status.value,
        created_at=project.created_at,
        deleted_at=project.deleted_at,
        position=project.position,
    )


def _to_domain(model: ProjectModel) -> Project:
    return Project(
        id=UUID(model.id),
        name=model.name,
        description=model.description,
        status=ProjectStatus(model.status),
        created_at=model.created_at.replace(tzinfo=timezone.utc),
        deleted_at=(
            model.deleted_at.replace(tzinfo=timezone.utc)
            if model.deleted_at is not None
            else None
        ),
        position=model.position,
    )
