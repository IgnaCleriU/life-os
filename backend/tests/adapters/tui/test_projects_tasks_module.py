from __future__ import annotations

from datetime import date, timedelta

import pytest

from lifeos.adapters.tui import deps
from lifeos.adapters.tui.modules.projects_tasks import ProjectsTasksModule
from lifeos.domain import Priority, TaskStatus


@pytest.fixture
def module(tui_env) -> ProjectsTasksModule:
    return ProjectsTasksModule()


def _create_project(name: str):  # noqa: ANN202
    with deps.create_project_use_case() as use_case:
        return use_case.execute(name=name)


def _create_task(project_id, title: str, **kwargs):  # noqa: ANN001, ANN202
    with deps.create_task_use_case() as use_case:
        return use_case.execute(project_id, title, **kwargs)


# --- context_pane (projects) ------------------------------------------------


def test_context_pane_has_one_item_per_project(module: ProjectsTasksModule) -> None:
    _create_project("life os")
    _create_project("casa")
    contents = module.context_pane()
    assert {item.label for item in contents.items} == {"life os", "casa"}


def test_context_pane_meta_shows_open_task_count(module: ProjectsTasksModule) -> None:
    project = _create_project("life os")
    _create_task(project.id, "todo task")
    _create_task(project.id, "doing task")
    with deps.start_task_use_case() as use_case:
        doing = _create_task(project.id, "started task")
        use_case.execute(doing.id)
    with deps.complete_task_use_case() as use_case:
        done = _create_task(project.id, "done task")
        use_case.execute(done.id)

    contents = module.context_pane()
    item = next(i for i in contents.items if i.label == "life os")
    assert item.meta == "3"  # 3 open (todo/doing), the done one excluded


def test_context_pane_item_payload_is_the_project_entity(
    module: ProjectsTasksModule,
) -> None:
    _create_project("life os")
    item = module.context_pane().items[0]
    assert item.payload.name == "life os"
    assert str(item.payload.id) == item.id


# --- collection_pane (tasks) -------------------------------------------------


def test_collection_pane_is_empty_for_none_context_item(
    module: ProjectsTasksModule,
) -> None:
    assert module.collection_pane(None).items == []


def test_collection_pane_lists_tasks_for_the_given_project(
    module: ProjectsTasksModule,
) -> None:
    project = _create_project("life os")
    _create_task(project.id, "write adr 0008")
    other = _create_project("casa")
    _create_task(other.id, "buy air filters")

    context_item = module.context_pane().items[0]
    contents = module.collection_pane(context_item)
    assert [i.label for i in contents.items] == ["write adr 0008"]


def test_collection_pane_meta_includes_status_glyph_and_priority_marker(
    module: ProjectsTasksModule,
) -> None:
    project = _create_project("life os")
    _create_task(project.id, "high priority todo", priority=Priority.HIGH)

    context_item = module.context_pane().items[0]
    item = module.collection_pane(context_item).items[0]
    assert "·" in item.meta  # todo glyph
    assert "!" in item.meta  # high priority marker


def test_collection_pane_meta_marks_overdue_dates_in_red(
    module: ProjectsTasksModule,
) -> None:
    project = _create_project("life os")
    yesterday = date.today() - timedelta(days=1)
    _create_task(project.id, "overdue task", due_date=yesterday)

    context_item = module.context_pane().items[0]
    item = module.collection_pane(context_item).items[0]
    assert f"[red]{yesterday.isoformat()}[/red]" in item.meta


def test_collection_pane_does_not_mark_future_dates_as_overdue(
    module: ProjectsTasksModule,
) -> None:
    project = _create_project("life os")
    tomorrow = date.today() + timedelta(days=1)
    _create_task(project.id, "future task", due_date=tomorrow)

    context_item = module.context_pane().items[0]
    item = module.collection_pane(context_item).items[0]
    assert "[red]" not in item.meta
    assert tomorrow.isoformat() in item.meta


# --- detail_pane -------------------------------------------------------------


def test_detail_pane_is_none_for_no_selection(module: ProjectsTasksModule) -> None:
    assert module.detail_pane(None) is None


def test_detail_pane_shows_task_fields_including_project_name(
    module: ProjectsTasksModule,
) -> None:
    project = _create_project("life os")
    _create_task(
        project.id,
        "write adr 0008",
        priority=Priority.HIGH,
        due_date=date(2026, 8, 3),
        description="amend the keymap",
    )

    context_item = module.context_pane().items[0]
    collection_item = module.collection_pane(context_item).items[0]
    detail = module.detail_pane(collection_item)

    assert detail is not None
    assert detail.title == "write adr 0008"
    fields = dict(detail.fields)
    assert fields["status"] == TaskStatus.TODO.value
    assert fields["priority"] == Priority.HIGH.value
    assert fields["due"] == "2026-08-03"
    assert fields["project"] == "life os"
    assert fields["description"] == "amend the keymap"
