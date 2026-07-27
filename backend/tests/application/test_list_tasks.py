"""Tests del caso de uso ListTasks (sin DB ni mocks, fakes en memoria)."""

from uuid import uuid4

from lifeos.application.use_cases.list_tasks import ListTasks
from lifeos.domain import Task

from .fakes import InMemoryTaskRepository


def test_list_tasks_returns_only_tasks_of_given_project():
    task_repo = InMemoryTaskRepository()
    project_a = uuid4()
    project_b = uuid4()

    task_a1 = Task.create(project_id=project_a, title="A1")
    task_a2 = Task.create(project_id=project_a, title="A2")
    task_b1 = Task.create(project_id=project_b, title="B1")
    for task in (task_a1, task_a2, task_b1):
        task_repo.add(task)

    use_case = ListTasks(task_repo)

    result = use_case.execute(project_a)

    assert {t.id for t in result} == {task_a1.id, task_a2.id}


def test_list_tasks_empty_project_returns_empty_list():
    use_case = ListTasks(InMemoryTaskRepository())

    assert use_case.execute(uuid4()) == []
