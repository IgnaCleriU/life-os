"""Endpoints de quick-add (spec 0002).

El overlay de Quickshell no puede importar Python, así que en vez de
reescribir el tokenizer en JavaScript consume estos dos endpoints: `preview`
en cada tecleo (con debounce) para mostrar cómo se interpreta el texto, y
`POST /quick-add` al confirmar. Ambos usan el mismo parser
(`adapters/shared/quick_add.py`) y la misma regla de proyecto destino
(`adapters/shared/capture_target.py`) que el CLI y la TUI.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, status

from lifeos.adapters.rest.deps import (
    get_create_project_use_case,
    get_create_task_use_case,
    get_get_project_use_case,
    get_list_projects_use_case,
)
from lifeos.adapters.rest.schemas import (
    ErrorDetail,
    QuickAddPreviewResponse,
    QuickAddProject,
    QuickAddRequest,
    TaskResponse,
)
from lifeos.adapters.shared.capture_target import (
    INBOX_PROJECT_NAME,
    AmbiguousProjectName,
    ProjectNameNotFound,
    resolve_capture_target,
)
from lifeos.adapters.shared.quick_add import parse_quick_add
from lifeos.application.use_cases.create_project import CreateProject
from lifeos.application.use_cases.create_task import CreateTask
from lifeos.application.use_cases.get_project import GetProject
from lifeos.application.use_cases.list_projects import ListProjects
from lifeos.domain import DomainValidationError, Project, ProjectNotFound

router = APIRouter(prefix="/quick-add", tags=["quick-add"])

ListProjectsDep = Annotated[ListProjects, Depends(get_list_projects_use_case)]
GetProjectDep = Annotated[GetProject, Depends(get_get_project_use_case)]


def _default(
    body: QuickAddRequest, get_project: GetProject
) -> Callable[[], Project] | None:
    if body.default_project_id is None:
        return None
    return lambda: get_project.execute(body.default_project_id)


@router.post("/preview", response_model=QuickAddPreviewResponse)
def preview_quick_add(
    body: QuickAddRequest,
    list_projects: ListProjectsDep,
    get_project: GetProjectDep,
) -> QuickAddPreviewResponse:
    """Interpreta el texto sin escribir: nunca crea el "inbox"."""
    parsed = parse_quick_add(body.text)
    project: QuickAddProject | None = None
    error: ErrorDetail | None = None

    try:
        target = resolve_capture_target(
            parsed.project_name,
            list_projects=list_projects.execute,
            default=_default(body, get_project),
        )
        project = QuickAddProject(id=target.id, name=target.name)
    except ProjectNameNotFound as exc:
        if parsed.project_name is None:
            # Solo puede faltar el inbox: se crearía al confirmar.
            project = QuickAddProject(id=None, name=INBOX_PROJECT_NAME)
        else:
            error = ErrorDetail(code="project_name_not_found", message=str(exc))
    except AmbiguousProjectName as exc:
        error = ErrorDetail(code="ambiguous_project_name", message=str(exc))
    except ProjectNotFound as exc:
        error = ErrorDetail(code="project_not_found", message=str(exc))

    if error is None and not parsed.title.strip():
        error = ErrorDetail(
            code="domain_validation_error", message="A task needs a title."
        )

    return QuickAddPreviewResponse(
        title=parsed.title,
        priority=parsed.priority,
        due_date=parsed.due_date,
        project=project,
        error=error,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_from_quick_add(
    body: QuickAddRequest,
    list_projects: ListProjectsDep,
    get_project: GetProjectDep,
    create_project: Annotated[CreateProject, Depends(get_create_project_use_case)],
    create_task: Annotated[CreateTask, Depends(get_create_task_use_case)],
) -> TaskResponse:
    """Crea la tarea descrita por el texto, en el proyecto que resuelva."""
    parsed = parse_quick_add(body.text)
    if not parsed.title.strip():
        # Antes de resolver: si no, un texto vacío crearía el inbox igual.
        raise DomainValidationError("A task needs a title.")
    target = resolve_capture_target(
        parsed.project_name,
        list_projects=list_projects.execute,
        default=_default(body, get_project),
        create_project=create_project.execute,
    )
    task = create_task.execute(
        target.id,
        parsed.title,
        priority=parsed.priority,
        due_date=parsed.due_date,
    )
    return TaskResponse.model_validate(task)
