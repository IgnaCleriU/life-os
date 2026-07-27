"""Endpoints REST de Task (crear, listar, actualizar, completar), delegando en
los casos de uso de application/use_cases.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from lifeos.adapters.rest.deps import (
    get_complete_task_use_case,
    get_create_task_use_case,
    get_list_tasks_use_case,
    get_update_task_use_case,
)
from lifeos.adapters.rest.schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)
from lifeos.application.use_cases.complete_task import CompleteTask
from lifeos.application.use_cases.create_task import CreateTask
from lifeos.application.use_cases.list_tasks import ListTasks
from lifeos.application.use_cases.update_task import UpdateTask

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
def list_tasks(
    project_id: UUID,
    use_case: Annotated[ListTasks, Depends(get_list_tasks_use_case)],
) -> list[TaskResponse]:
    """Lista las tareas de un proyecto."""
    tasks = use_case.execute(project_id)
    return [TaskResponse.model_validate(task) for task in tasks]


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    body: TaskUpdateRequest,
    use_case: Annotated[UpdateTask, Depends(get_update_task_use_case)],
) -> TaskResponse:
    """Actualiza parcialmente una tarea.

    `model_dump(exclude_unset=True)` solo incluye las claves que el cliente
    mandó en el JSON: un `due_date` omitido no llega a `execute` (que la deja
    intacta vía su propio centinela `_UNSET`), mientras que `due_date: null`
    sí llega como `due_date=None` (que la limpia). Esto también aplica de
    forma segura a `title`/`description`/`priority`, cuyo propio default
    (`None`) ya significa "no tocar" en `UpdateTask.execute`.
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
