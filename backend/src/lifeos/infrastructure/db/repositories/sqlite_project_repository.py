"""Implementación SQLite del puerto ProjectRepository."""

from __future__ import annotations

from datetime import timezone
from uuid import UUID

from sqlmodel import Session, select

from lifeos.domain import Project, ProjectStatus
from lifeos.infrastructure.db.models import ProjectModel


class SQLiteProjectRepository:
    """`ProjectRepository` respaldado por SQLite vía SQLModel."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: Project) -> None:
        """Persiste un proyecto nuevo."""
        self._session.add(_to_model(project))
        self._session.commit()

    def get(self, project_id: UUID) -> Project | None:
        """Devuelve el proyecto con ese id, o `None` si no existe."""
        model = self._session.get(ProjectModel, str(project_id))
        return _to_domain(model) if model is not None else None

    def list_all(self) -> list[Project]:
        """Devuelve todos los proyectos."""
        models = self._session.exec(select(ProjectModel)).all()
        return [_to_domain(model) for model in models]


def _to_model(project: Project) -> ProjectModel:
    return ProjectModel(
        id=str(project.id),
        name=project.name,
        description=project.description,
        status=project.status.value,
        created_at=project.created_at,
    )


def _to_domain(model: ProjectModel) -> Project:
    return Project(
        id=UUID(model.id),
        name=model.name,
        description=model.description,
        status=ProjectStatus(model.status),
        created_at=model.created_at.replace(tzinfo=timezone.utc),
    )
