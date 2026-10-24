"""Tests del caso de uso MoveTask (sin DB ni mocks, fakes en memoria)."""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.move_task import MoveTask
from lifeos.domain import Project, ProjectNotFound, Task, TaskNotFound

from .fakes import InMemoryProjectRepository, InMemoryTaskRepository


def _seed():
    project_repo = InMemoryProjectRepository()
    task_repo = InMemoryTaskRepository()
    origen = Project.create(name="Origen")
    destino = Project.create(name="Destino")
    project_repo.add(origen)
    project_repo.add(destino)
    task = Task.create(project_id=origen.id, title="Tarea")
    task_repo.add(task)
    return MoveTask(task_repo, project_repo), task_repo, task, destino


def test_move_reassigns_project_and_persists():
    use_case, task_repo, task, destino = _seed()

    moved = use_case.execute(task.id, destino.id)

    assert moved.project_id == destino.id
    assert task_repo.get(task.id).project_id == destino.id


def test_move_missing_task_raises():
    use_case, _, _, destino = _seed()

    with pytest.raises(TaskNotFound):
        use_case.execute(uuid4(), destino.id)


def test_move_to_missing_project_raises_and_leaves_task_untouched():
    use_case, task_repo, task, _ = _seed()
    proyecto_original = task.project_id

    with pytest.raises(ProjectNotFound):
        use_case.execute(task.id, uuid4())

    assert task_repo.get(task.id).project_id == proyecto_original
