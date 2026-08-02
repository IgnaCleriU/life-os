"""Endpoints REST de Task, delegando en los casos de uso de
application/use_cases.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response

from lifeos.adapters.rest.deps import (
    get_complete_task_use_case,
    get_create_task_use_case,
    get_delete_task_use_case,
    get_get_task_use_case,
    get_list_projects_use_case,
    get_list_tasks_use_case,
    get_move_task_use_case,
    get_reopen_task_use_case,
    get_restore_task_use_case,
    get_start_task_use_case,
    get_update_task_use_case,
)
from lifeos.adapters.rest.schemas import (
    TaskCreateRequest,
    TaskMoveRequest,
    TaskResponse,
    TaskUpdateRequest,
    TaskWithProjectResponse,
)
from lifeos.application.use_cases.complete_task import CompleteTask
from lifeos.application.use_cases.create_task import CreateTask
from lifeos.application.use_cases.delete_task import DeleteTask
from lifeos.application.use_cases.get_task import GetTask
from lifeos.application.use_cases.list_projects import ListProjects
from lifeos.application.use_cases.list_tasks import ListTasks
from lifeos.application.use_cases.move_task import MoveTask
from lifeos.application.use_cases.reopen_task import ReopenTask
from lifeos.application.use_cases.restore_task import RestoreTask
from lifeos.application.use_cases.start_task import StartTask
from lifeos.application.use_cases.update_task import UpdateTask
from lifeos.domain import TaskStatus

router = APIRouter(tags=["tasks"])


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    project_id: UUID,
    body: TaskCreateRequest,
    use_case: Annotated[CreateTask, Depends(get_create_task_use_case)],
) -> TaskResponse:
    """Crea una tarea bajo un proyecto existente."""
    task = use_case.execute(
        project_id=project_id,
        title=body.title,
        priority=body.priority,
        due_date=body.due_date,
        description=body.description,
    )
    return TaskResponse.model_validate(task)


@router.get("/projects/{project_id}/tasks", response_model=list[TaskResponse])
def list_tasks_of_project(
    project_id: UUID,
    use_case: Annotated[ListTasks, Depends(get_list_tasks_use_case)],
    status_filter: Annotated[list[TaskStatus] | None, Query(alias="status")] = None,
    due_before: date | None = None,
    q: str | None = None,
) -> list[TaskResponse]:
    """Lista las tareas de un proyecto, con los mismos filtros opcionales que
    `GET /tasks` (ver esa ruta para el significado de cada uno)."""
    tasks = use_case.execute(
        project_id, statuses=status_filter, due_before=due_before, text=q
    )
    return [TaskResponse.model_validate(task) for task in tasks]


@router.get("/tasks", response_model=list[TaskWithProjectResponse])
def list_tasks(
    use_case: Annotated[ListTasks, Depends(get_list_tasks_use_case)],
    list_projects_use_case: Annotated[
        ListProjects, Depends(get_list_projects_use_case)
    ],
    project_id: UUID | None = None,
    status_filter: Annotated[list[TaskStatus] | None, Query(alias="status")] = None,
    due_before: date | None = None,
    q: str | None = None,
) -> list[TaskWithProjectResponse]:
    """Lista tareas de todos los proyectos, con filtros opcionales.

    Incluye `project_name` por tarea - a diferencia de
    `GET /projects/{id}/tasks`, acá quien llama no sabe de antemano a qué
    proyecto pertenece cada tarea.
    """
    tasks = use_case.execute(
        project_id, statuses=status_filter, due_before=due_before, text=q
    )
    project_names = {p.id: p.name for p in list_projects_use_case.execute()}
    return [
        TaskWithProjectResponse(
            **TaskResponse.model_validate(task).model_dump(),
            project_name=project_names.get(task.project_id),
        )
        for task in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    use_case: Annotated[GetTask, Depends(get_get_task_use_case)],
) -> TaskResponse:
    """Devuelve una tarea por id."""
    return TaskResponse.model_validate(use_case.execute(task_id))


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    body: TaskUpdateRequest,
    use_case: Annotated[UpdateTask, Depends(get_update_task_use_case)],
) -> TaskResponse:
    """Actualiza parcialmente una tarea.

    `model_dump(exclude_unset=True)` solo incluye las claves que el cliente
    mandó en el JSON: un campo omitido no llega a `execute`. Para `due_date` y
    `description`, eso significa "no tocar" vía el centinela `_UNSET` propio de
    `UpdateTask.execute`; enviados explícitamente en `null`, se limpian. Para
    `title`/`priority`, en cambio, el propio default de `execute` (`None`) ya
    significa "no tocar" — no tienen forma de limpiarse a través de esta ruta,
    consistente con que el dominio no permite un título vacío.
    """
    kwargs = body.model_dump(exclude_unset=True)
    task = use_case.execute(task_id, **kwargs)
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: UUID,
    use_case: Annotated[CompleteTask, Depends(get_complete_task_use_case)],
) -> TaskResponse:
    """Marca una tarea como completada (idempotente)."""
    task = use_case.execute(task_id)
    return TaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/start", response_model=TaskResponse)
def start_task(
    task_id: UUID,
    use_case: Annotated[StartTask, Depends(get_start_task_use_case)],
) -> TaskResponse:
    """Marca una tarea como en curso (idempotente)."""
    return TaskResponse.model_validate(use_case.execute(task_id))


@router.post("/tasks/{task_id}/reopen", response_model=TaskResponse)
def reopen_task(
    task_id: UUID,
    use_case: Annotated[ReopenTask, Depends(get_reopen_task_use_case)],
) -> TaskResponse:
    """Vuelve una tarea a pendiente (idempotente)."""
    return TaskResponse.model_validate(use_case.execute(task_id))


@router.post("/tasks/{task_id}/restore", response_model=TaskResponse)
def restore_task(
    task_id: UUID,
    use_case: Annotated[RestoreTask, Depends(get_restore_task_use_case)],
) -> TaskResponse:
    """Deshace el borrado lógico de una tarea."""
    return TaskResponse.model_validate(use_case.execute(task_id))


@router.post("/tasks/{task_id}/move", response_model=TaskResponse)
def move_task(
    task_id: UUID,
    body: TaskMoveRequest,
    use_case: Annotated[MoveTask, Depends(get_move_task_use_case)],
) -> TaskResponse:
    """Mueve una tarea a otro proyecto."""
    task = use_case.execute(task_id, body.project_id)
    return TaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    use_case: Annotated[DeleteTask, Depends(get_delete_task_use_case)],
) -> Response:
    """Borra lógicamente una tarea."""
    use_case.execute(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
