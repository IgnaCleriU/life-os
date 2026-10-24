"""Endpoints REST de Project, delegando en los casos de uso de
application/use_cases.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response

from lifeos.adapters.rest.deps import (
    get_activate_project_use_case,
    get_archive_project_use_case,
    get_complete_project_use_case,
    get_create_project_use_case,
    get_delete_project_use_case,
    get_get_project_use_case,
    get_list_projects_use_case,
    get_restore_project_use_case,
    get_update_project_use_case,
)
from lifeos.adapters.rest.schemas import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from lifeos.application.use_cases.activate_project import ActivateProject
from lifeos.application.use_cases.archive_project import ArchiveProject
from lifeos.application.use_cases.complete_project import CompleteProject
from lifeos.application.use_cases.create_project import CreateProject
from lifeos.application.use_cases.delete_project import DeleteProject
from lifeos.application.use_cases.get_project import GetProject
from lifeos.application.use_cases.list_projects import ListProjects
from lifeos.application.use_cases.restore_project import RestoreProject
from lifeos.application.use_cases.update_project import UpdateProject
from lifeos.domain import ProjectStatus

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreateRequest,
    use_case: Annotated[CreateProject, Depends(get_create_project_use_case)],
) -> ProjectResponse:
    """Crea un proyecto nuevo."""
    project = use_case.execute(name=body.name, description=body.description)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    use_case: Annotated[ListProjects, Depends(get_list_projects_use_case)],
    status_filter: Annotated[list[ProjectStatus] | None, Query(alias="status")] = None,
    q: str | None = None,
) -> list[ProjectResponse]:
    """Lista los proyectos, opcionalmente filtrados por estado y/o texto."""
    projects = use_case.execute(statuses=status_filter, text=q)
    return [ProjectResponse.model_validate(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    use_case: Annotated[GetProject, Depends(get_get_project_use_case)],
) -> ProjectResponse:
    """Devuelve un proyecto por id."""
    return ProjectResponse.model_validate(use_case.execute(project_id))


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    body: ProjectUpdateRequest,
    use_case: Annotated[UpdateProject, Depends(get_update_project_use_case)],
) -> ProjectResponse:
    """Actualiza parcialmente un proyecto.

    `model_dump(exclude_unset=True)` solo incluye las claves que el cliente
    mandó en el JSON: un `description` omitido no llega a `execute` (que la
    deja intacta vía su propio centinela `_UNSET`), mientras que
    `description: null` sí llega como `description=None` (que la limpia).
    """
    kwargs = body.model_dump(exclude_unset=True)
    project = use_case.execute(project_id, **kwargs)
    return ProjectResponse.model_validate(project)


@router.post("/{project_id}/complete", response_model=ProjectResponse)
def complete_project(
    project_id: UUID,
    use_case: Annotated[CompleteProject, Depends(get_complete_project_use_case)],
) -> ProjectResponse:
    """Marca un proyecto como finalizado (idempotente)."""
    return ProjectResponse.model_validate(use_case.execute(project_id))


@router.post("/{project_id}/archive", response_model=ProjectResponse)
def archive_project(
    project_id: UUID,
    use_case: Annotated[ArchiveProject, Depends(get_archive_project_use_case)],
) -> ProjectResponse:
    """Archiva un proyecto (idempotente)."""
    return ProjectResponse.model_validate(use_case.execute(project_id))


@router.post("/{project_id}/activate", response_model=ProjectResponse)
def activate_project(
    project_id: UUID,
    use_case: Annotated[ActivateProject, Depends(get_activate_project_use_case)],
) -> ProjectResponse:
    """Reactiva un proyecto (idempotente)."""
    return ProjectResponse.model_validate(use_case.execute(project_id))


@router.post("/{project_id}/restore", response_model=ProjectResponse)
def restore_project(
    project_id: UUID,
    use_case: Annotated[RestoreProject, Depends(get_restore_project_use_case)],
) -> ProjectResponse:
    """Deshace el borrado lógico de un proyecto."""
    return ProjectResponse.model_validate(use_case.execute(project_id))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    use_case: Annotated[DeleteProject, Depends(get_delete_project_use_case)],
) -> Response:
    """Borra lógicamente un proyecto; falla si todavía tiene tareas vivas."""
    use_case.execute(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
