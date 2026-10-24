"""Entidad Project y su estado.

Python puro (dataclasses/enums). Las reglas de negocio (invariantes y
transiciones) viven acá; ninguna capa externa debería duplicarlas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from .exceptions import DomainValidationError


class ProjectStatus(str, Enum):
    """Estado de un proyecto.

    Los tres estados son mutuamente excluyentes y las transiciones entre ellos
    son libres (cualquiera → cualquiera): un proyecto puede completarse y volver
    a activarse, o archivarse desde cualquier estado y desarchivarse.
    """

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


def _validate_name(name: str) -> str:
    """Valida que el nombre no sea vacío y lo devuelve normalizado."""
    cleaned = name.strip()
    if not cleaned:
        raise DomainValidationError("El nombre del proyecto no puede estar vacío")
    return cleaned


@dataclass
class Project:
    """Un proyecto que agrupa tareas."""

    id: UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        """Si el proyecto está borrado lógicamente."""
        return self.deleted_at is not None

    @classmethod
    def create(cls, name: str, description: str | None = None) -> Project:
        """Crea un proyecto nuevo, generando id y timestamp en el dominio."""
        return cls(
            id=uuid4(),
            name=_validate_name(name),
            description=description,
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )

    def rename(self, new_name: str) -> None:
        """Cambia el nombre del proyecto, validando la invariante."""
        self.name = _validate_name(new_name)

    def describe(self, description: str | None) -> None:
        """Cambia la descripción (o la quita si es None)."""
        self.description = description

    def complete(self) -> None:
        """Marca el proyecto como finalizado."""
        self.status = ProjectStatus.COMPLETED

    def archive(self) -> None:
        """Marca el proyecto como archivado."""
        self.status = ProjectStatus.ARCHIVED

    def activate(self) -> None:
        """Vuelve a poner el proyecto como activo (desde completado o archivado)."""
        self.status = ProjectStatus.ACTIVE

    def delete(self) -> None:
        """Borra el proyecto lógicamente (idempotente).

        No se pisa un `deleted_at` ya puesto: reborrar no debe mover la marca
        de tiempo del borrado original.
        """
        if self.deleted_at is None:
            self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Deshace el borrado lógico (idempotente)."""
        self.deleted_at = None
