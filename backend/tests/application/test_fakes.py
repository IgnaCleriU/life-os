"""Tests de los repositorios fake en memoria usados por el resto de la suite."""

from uuid import uuid4

from lifeos.domain import Project, Task

from .fakes import InMemoryProjectRepository, InMemoryTaskRepository


def test_project_repo_add_get_and_list():
    repo = InMemoryProjectRepository()
    project = Project.create(name="Life OS")

    repo.add(project)

    assert repo.get(project.id) is project
    assert repo.list_all() == [project]


def test_project_repo_get_missing_returns_none():
    repo = InMemoryProjectRepository()

    assert repo.get(uuid4()) is None


def test_task_repo_add_get_and_list_by_project():
    repo = InMemoryTaskRepository()
    project_id = uuid4()
    task = Task.create(project_id=project_id, title="Escribir ports")
    other = Task.create(project_id=uuid4(), title="Tarea de otro proyecto")

    repo.add(task)
    repo.add(other)

    assert repo.get(task.id) is task
    assert repo.list_by_project(project_id) == [task]


def test_task_repo_update_persists_changes():
    repo = InMemoryTaskRepository()
    task = Task.create(project_id=uuid4(), title="Tarea")
    repo.add(task)

    task.complete()
    repo.update(task)

    assert repo.get(task.id).status is task.status
