"""Tests del caso de uso ListTasks (sin DB ni mocks, fakes en memoria)."""

from datetime import date
from uuid import uuid4

from lifeos.application.use_cases.list_tasks import ListTasks
from lifeos.domain import Task, TaskStatus

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


def _seed_filterable():
    """Cuatro tareas del mismo proyecto, una por combinación a filtrar."""
    task_repo = InMemoryTaskRepository()
    project_id = uuid4()
    vencida = Task.create(
        project_id=project_id, title="Pagar expensas", due_date=date(2026, 7, 1)
    )
    futura = Task.create(
        project_id=project_id, title="Renovar seguro", due_date=date(2026, 12, 1)
    )
    sin_fecha = Task.create(project_id=project_id, title="Leer sobre expensas")
    hecha = Task.create(project_id=project_id, title="Tarea hecha")
    hecha.complete()
    for task in (vencida, futura, sin_fecha, hecha):
        task_repo.add(task)
    return ListTasks(task_repo), project_id, vencida, futura, sin_fecha, hecha


def test_list_without_project_returns_tasks_across_projects():
    task_repo = InMemoryTaskRepository()
    una = Task.create(project_id=uuid4(), title="Una")
    otra = Task.create(project_id=uuid4(), title="Otra")
    task_repo.add(una)
    task_repo.add(otra)

    result = ListTasks(task_repo).execute()

    assert {t.id for t in result} == {una.id, otra.id}


def test_list_filters_by_status():
    use_case, project_id, vencida, futura, sin_fecha, hecha = _seed_filterable()

    result = use_case.execute(project_id, statuses=[TaskStatus.DONE])

    assert {t.id for t in result} == {hecha.id}


def test_list_filters_by_due_before_and_excludes_undated_tasks():
    use_case, project_id, vencida, futura, sin_fecha, _ = _seed_filterable()

    result = use_case.execute(project_id, due_before=date(2026, 7, 28))

    assert {t.id for t in result} == {vencida.id}


def test_list_due_before_is_inclusive():
    use_case, project_id, vencida, *_ = _seed_filterable()

    result = use_case.execute(project_id, due_before=date(2026, 7, 1))

    assert vencida.id in {t.id for t in result}


def test_list_filters_by_text_case_insensitively():
    use_case, project_id, vencida, _, sin_fecha, _ = _seed_filterable()

    result = use_case.execute(project_id, text="EXPENSAS")

    assert {t.id for t in result} == {vencida.id, sin_fecha.id}


def test_list_combines_filters_with_and():
    use_case, project_id, vencida, *_ = _seed_filterable()

    result = use_case.execute(
        project_id, statuses=[TaskStatus.TODO], text="expensas",
        due_before=date(2026, 7, 28),
    )

    assert {t.id for t in result} == {vencida.id}
