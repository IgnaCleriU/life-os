"""Dependency wiring for the TUI's Projects/Tasks module.

Mirrors `adapters/cli/deps.py` exactly - plain functions (not FastAPI
`Depends`), one session per use-case call. Copied rather than imported:
each colocated driver adapter owns its own wiring per ADR 0002/0008, the
same reasoning behind the CLI/MCP serializer duplication.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from lifeos.application.use_cases.activate_project import ActivateProject
from lifeos.application.use_cases.archive_project import ArchiveProject
from lifeos.application.use_cases.complete_project import CompleteProject
from lifeos.application.use_cases.complete_task import CompleteTask
from lifeos.application.use_cases.create_project import CreateProject
from lifeos.application.use_cases.create_task import CreateTask
from lifeos.application.use_cases.delete_project import DeleteProject
from lifeos.application.use_cases.delete_task import DeleteTask
from lifeos.application.use_cases.get_project import GetProject
from lifeos.application.use_cases.get_task import GetTask
from lifeos.application.use_cases.list_projects import ListProjects
from lifeos.application.use_cases.list_tasks import ListTasks
from lifeos.application.use_cases.move_task import MoveTask
from lifeos.application.use_cases.reopen_task import ReopenTask
from lifeos.application.use_cases.reorder_project import (
    ReorderProjectDown,
    ReorderProjectUp,
)
from lifeos.application.use_cases.restore_project import RestoreProject
from lifeos.application.use_cases.restore_task import RestoreTask
from lifeos.application.use_cases.start_task import StartTask
from lifeos.application.use_cases.update_project import UpdateProject
from lifeos.application.use_cases.update_task import UpdateTask
from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
    SQLiteProjectRepository,
)
from lifeos.infrastructure.db.repositories.sqlite_task_repository import (
    SQLiteTaskRepository,
)
from lifeos.infrastructure.db.session import get_session

# --- Project -----------------------------------------------------------


@contextmanager
def create_project_use_case() -> Iterator[CreateProject]:
    with get_session() as session:
        yield CreateProject(SQLiteProjectRepository(session))


@contextmanager
def list_projects_use_case() -> Iterator[ListProjects]:
    with get_session() as session:
        yield ListProjects(SQLiteProjectRepository(session))


@contextmanager
def get_project_use_case() -> Iterator[GetProject]:
    with get_session() as session:
        yield GetProject(SQLiteProjectRepository(session))


@contextmanager
def update_project_use_case() -> Iterator[UpdateProject]:
    with get_session() as session:
        yield UpdateProject(SQLiteProjectRepository(session))


@contextmanager
def complete_project_use_case() -> Iterator[CompleteProject]:
    with get_session() as session:
        yield CompleteProject(SQLiteProjectRepository(session))


@contextmanager
def archive_project_use_case() -> Iterator[ArchiveProject]:
    with get_session() as session:
        yield ArchiveProject(SQLiteProjectRepository(session))


@contextmanager
def activate_project_use_case() -> Iterator[ActivateProject]:
    with get_session() as session:
        yield ActivateProject(SQLiteProjectRepository(session))


@contextmanager
def reorder_project_up_use_case() -> Iterator[ReorderProjectUp]:
    with get_session() as session:
        yield ReorderProjectUp(SQLiteProjectRepository(session))


@contextmanager
def reorder_project_down_use_case() -> Iterator[ReorderProjectDown]:
    with get_session() as session:
        yield ReorderProjectDown(SQLiteProjectRepository(session))


@contextmanager
def delete_project_use_case() -> Iterator[DeleteProject]:
    with get_session() as session:
        yield DeleteProject(
            SQLiteProjectRepository(session), SQLiteTaskRepository(session)
        )


@contextmanager
def restore_project_use_case() -> Iterator[RestoreProject]:
    with get_session() as session:
        yield RestoreProject(SQLiteProjectRepository(session))


# --- Task ----------------------------------------------------------------


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
def get_task_use_case() -> Iterator[GetTask]:
    with get_session() as session:
        yield GetTask(SQLiteTaskRepository(session))


@contextmanager
def update_task_use_case() -> Iterator[UpdateTask]:
    with get_session() as session:
        yield UpdateTask(SQLiteTaskRepository(session))


@contextmanager
def complete_task_use_case() -> Iterator[CompleteTask]:
    with get_session() as session:
        yield CompleteTask(SQLiteTaskRepository(session))


@contextmanager
def start_task_use_case() -> Iterator[StartTask]:
    with get_session() as session:
        yield StartTask(SQLiteTaskRepository(session))


@contextmanager
def reopen_task_use_case() -> Iterator[ReopenTask]:
    with get_session() as session:
        yield ReopenTask(SQLiteTaskRepository(session))


@contextmanager
def move_task_use_case() -> Iterator[MoveTask]:
    with get_session() as session:
        yield MoveTask(SQLiteTaskRepository(session), SQLiteProjectRepository(session))


@contextmanager
def delete_task_use_case() -> Iterator[DeleteTask]:
    with get_session() as session:
        yield DeleteTask(SQLiteTaskRepository(session))


@contextmanager
def restore_task_use_case() -> Iterator[RestoreTask]:
    with get_session() as session:
        yield RestoreTask(
            SQLiteTaskRepository(session), SQLiteProjectRepository(session)
        )
