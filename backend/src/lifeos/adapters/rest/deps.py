"""Inyección de dependencias de FastAPI: construye repositorios y casos de
uso para los routers.

Cadena de `Depends`: sesión de DB -> repositorio(s) -> caso de uso. Cada
capa depende solo de la anterior; los routers solo dependen del caso de
uso que necesitan invocar.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from lifeos.application.ports import ProjectRepository, TaskRepository
from lifeos.application.use_cases.complete_task import CompleteTask
from lifeos.application.use_cases.create_project import CreateProject
from lifeos.application.use_cases.create_task import CreateTask
from lifeos.application.use_cases.list_projects import ListProjects
from lifeos.application.use_cases.list_tasks import ListTasks
from lifeos.application.use_cases.update_task import UpdateTask
from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
    SQLiteProjectRepository,
)
from lifeos.infrastructure.db.repositories.sqlite_task_repository import (
    SQLiteTaskRepository,
)
from lifeos.infrastructure.db.session import get_session


def get_db_session() -> Iterator[Session]:
    """Adapta el `@contextmanager get_session()` a una dependencia FastAPI.

    FastAPI trata una función generadora usada con `Depends` como un context
    manager: ejecuta hasta el `yield` antes de la ruta y reanuda (para el
    cleanup) después de construir la respuesta.
    """
    with get_session() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db_session)]


def get_project_repository(session: DbSession) -> ProjectRepository:
    return SQLiteProjectRepository(session)


def get_task_repository(session: DbSession) -> TaskRepository:
    return SQLiteTaskRepository(session)


ProjectRepo = Annotated[ProjectRepository, Depends(get_project_repository)]
TaskRepo = Annotated[TaskRepository, Depends(get_task_repository)]


def get_create_project_use_case(project_repo: ProjectRepo) -> CreateProject:
    return CreateProject(project_repo)


def get_list_projects_use_case(project_repo: ProjectRepo) -> ListProjects:
    return ListProjects(project_repo)


def get_create_task_use_case(
    task_repo: TaskRepo, project_repo: ProjectRepo
) -> CreateTask:
    return CreateTask(task_repo, project_repo)


def get_list_tasks_use_case(task_repo: TaskRepo) -> ListTasks:
    return ListTasks(task_repo)


def get_update_task_use_case(task_repo: TaskRepo) -> UpdateTask:
    return UpdateTask(task_repo)


def get_complete_task_use_case(task_repo: TaskRepo) -> CompleteTask:
    return CompleteTask(task_repo)
