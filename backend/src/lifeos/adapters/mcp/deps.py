"""Construcción de repositorios y casos de uso para las tools MCP.

Análogo a `adapters/rest/deps.py`, pero como funciones simples en lugar de
`Depends` de FastAPI: el servidor MCP es un único proceso de larga duración
(stdio), no un framework por-request. Cada helper abre su propia sesión de
DB por invocación de tool, igual que `get_db_session` hace por request en
REST.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

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


@contextmanager
def create_project_use_case() -> Iterator[CreateProject]:
    with get_session() as session:
        yield CreateProject(SQLiteProjectRepository(session))


@contextmanager
def list_projects_use_case() -> Iterator[ListProjects]:
    with get_session() as session:
        yield ListProjects(SQLiteProjectRepository(session))


@contextmanager
def create_task_use_case() -> Iterator[CreateTask]:
    with get_session() as session:
        yield CreateTask(
            SQLiteTaskRepository(session), SQLiteProjectRepository(session)
        )


@contextmanager
def list_tasks_use_case() -> Iterator[ListTasks]:
    with get_session() as session:
        yield ListTasks(SQLiteTaskRepository(session))


@contextmanager
def update_task_use_case() -> Iterator[UpdateTask]:
    with get_session() as session:
        yield UpdateTask(SQLiteTaskRepository(session))


@contextmanager
def complete_task_use_case() -> Iterator[CompleteTask]:
    with get_session() as session:
        yield CompleteTask(SQLiteTaskRepository(session))
