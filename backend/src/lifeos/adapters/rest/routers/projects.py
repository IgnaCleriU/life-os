"""Endpoints REST de Project (crear, listar), delegando en los casos de uso de
application/use_cases.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from lifeos.adapters.rest.deps import (
    get_create_project_use_case,
    get_list_projects_use_case,
)
from lifeos.adapters.rest.schemas import ProjectCreateRequest, ProjectResponse
from lifeos.application.use_cases.create_project import CreateProject
from lifeos.application.use_cases.list_projects import ListProjects

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
) -> list[ProjectResponse]:
    """Lista todos los proyectos."""
    projects = use_case.execute()
    return [ProjectResponse.model_validate(project) for project in projects]
