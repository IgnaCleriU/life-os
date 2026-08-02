"""DTOs Pydantic para requests/responses REST de Project y Task.

Reutiliza los enums de dominio (`ProjectStatus`, `TaskStatus`, `Priority`)
tal cual como tipos de campo: son `str, Enum`, así que Pydantic los valida
y serializa de forma nativa sin necesitar un enum paralelo en esta capa.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from lifeos.domain import Priority, ProjectStatus, TaskStatus

# --- Errores -----------------------------------------------------------


class ErrorDetail(BaseModel):
    """Detalle estructurado de un error de la API."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Forma de respuesta uniforme para todos los errores de la API."""

    error: ErrorDetail


# --- Project -------------------------------------------------------------


class ProjectCreateRequest(BaseModel):
    """Body de `POST /projects`."""

    name: str
    description: str | None = None


class ProjectUpdateRequest(BaseModel):
    """Body de `PATCH /projects/{project_id}` — actualización parcial.

    Un campo omitido en el JSON no se toca; `description` explícitamente
    `null` la limpia. Igual que en `TaskUpdateRequest`, la distinción se
    resuelve en el router con `model_dump(exclude_unset=True)`.
    """

    name: str | None = None
    description: str | None = None


class ProjectResponse(BaseModel):
    """Representación de un Project en las respuestas REST."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
    position: int


# --- Task ------------------------------------------------------------


class TaskCreateRequest(BaseModel):
    """Body de `POST /projects/{project_id}/tasks`."""

    title: str
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    due_date: date | None = None


class TaskUpdateRequest(BaseModel):
    """Body de `PATCH /tasks/{task_id}` — actualización parcial.

    Un campo omitido en el JSON no se toca; `due_date` explícitamente
    `null` la limpia. La distinción se resuelve en el router con
    `model_dump(exclude_unset=True)`, no en este modelo.
    """

    title: str | None = None
    description: str | None = None
    priority: Priority | None = None
    due_date: date | None = None


class TaskMoveRequest(BaseModel):
    """Body de `POST /tasks/{task_id}/move`."""

    project_id: UUID


class TaskResponse(BaseModel):
    """Representación de una Task en las respuestas REST."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: Priority
    due_date: date | None
    created_at: datetime
