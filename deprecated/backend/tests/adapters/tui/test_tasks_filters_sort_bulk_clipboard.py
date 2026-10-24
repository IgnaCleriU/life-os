from __future__ import annotations

from datetime import date

import pytest

from lifeos.adapters.tui import deps
from lifeos.adapters.tui.keymap import Scope
from lifeos.adapters.tui.modules.projects_tasks import ProjectsTasksModule
from lifeos.domain import Priority, TaskStatus


@pytest.fixture
def module(tui_env, fake_shell) -> ProjectsTasksModule:
    mod = ProjectsTasksModule()
    mod.shell = fake_shell
    return mod


def _create_project(name: str):  # noqa: ANN202
    with deps.create_project_use_case() as use_case:
        return use_case.execute(name=name)


def _create_task(project_id, title: str, **kwargs):  # noqa: ANN001, ANN202
    with deps.create_task_use_case() as use_case:
        return use_case.execute(project_id, title, **kwargs)


def _entry(module: ProjectsTasksModule, scope: Scope, key: str):  # noqa: ANN201
    matches = [e for e in module.keymap_entries() if e.scope is scope and e.key == key]
    assert len(matches) == 1, f"expected exactly one {scope}/{key!r} entry"
    return matches[0]


def _select(module: ProjectsTasksModule, fake_shell, project) -> None:  # noqa: ANN001
    fake_shell.current_context_item = next(
        i for i in module.context_pane().items if i.payload.id == project.id
    )


# --- f: projects status filter -----------------------------------------------


def test_projects_f_filters_by_status(module, fake_shell) -> None:
    _create_project("active one")
    archived = _create_project("archived one")
    with deps.archive_project_use_case() as use_case:
        use_case.execute(archived.id)

    _entry(module, Scope.CONTEXT, "f").action()
    fake_shell.pick("archived")

    labels = {i.label for i in module.context_pane().items}
    assert labels == {"archived one"}
    assert fake_shell.reload_count == 1


def test_projects_f_all_clears_the_filter(module, fake_shell) -> None:
    _create_project("active one")
    archived = _create_project("archived one")
    with deps.archive_project_use_case() as use_case:
        use_case.execute(archived.id)

    _entry(module, Scope.CONTEXT, "f").action()
    fake_shell.pick("archived")
    _entry(module, Scope.CONTEXT, "f").action()
    fake_shell.pick("all")

    labels = {i.label for i in module.context_pane().items}
    assert labels == {"active one", "archived one"}


# --- f: tasks status filter ---------------------------------------------------


def test_tasks_f_filters_by_status(module, fake_shell) -> None:
    project = _create_project("life os")
    _create_task(project.id, "todo task")
    doing = _create_task(project.id, "doing task")
    with deps.start_task_use_case() as use_case:
        use_case.execute(doing.id)
    _select(module, fake_shell, project)

    _entry(module, Scope.COLLECTION, "f").action()
    fake_shell.pick("doing")

    contents = module.collection_pane(fake_shell.current_context_item)
    labels = {i.label for i in contents.items}
    assert labels == {"doing task"}


def test_tasks_f_all_clears_the_filter(module, fake_shell) -> None:
    project = _create_project("life os")
    _create_task(project.id, "todo task")
    doing = _create_task(project.id, "doing task")
    with deps.start_task_use_case() as use_case:
        use_case.execute(doing.id)
    _select(module, fake_shell, project)

    _entry(module, Scope.COLLECTION, "f").action()
    fake_shell.pick("doing")
    _entry(module, Scope.COLLECTION, "f").action()
    fake_shell.pick("all")

    contents = module.collection_pane(fake_shell.current_context_item)
    labels = {i.label for i in contents.items}
    assert labels == {"todo task", "doing task"}


# --- S: cycle sort order -------------------------------------------------------


def test_capital_s_cycles_sort_order_by_due_date(module, fake_shell) -> None:
    project = _create_project("life os")
    _create_task(project.id, "no due date")
    _create_task(project.id, "later", due_date=date(2026, 12, 1))
    _create_task(project.id, "sooner", due_date=date(2026, 1, 1))
    _select(module, fake_shell, project)

    _entry(module, Scope.COLLECTION, "S").action()  # created -> due
    contents = module.collection_pane(fake_shell.current_context_item)
    labels = [i.label for i in contents.items]
    assert labels == ["sooner", "later", "no due date"]


def test_capital_s_cycles_sort_order_by_priority_next(module, fake_shell) -> None:
    project = _create_project("life os")
    _create_task(project.id, "low", priority=Priority.LOW)
    _create_task(project.id, "high", priority=Priority.HIGH)
    _create_task(project.id, "medium", priority=Priority.MEDIUM)
    _select(module, fake_shell, project)

    _entry(module, Scope.COLLECTION, "S").action()  # created -> due
    _entry(module, Scope.COLLECTION, "S").action()  # due -> priority
    contents = module.collection_pane(fake_shell.current_context_item)
    labels = [i.label for i in contents.items]
    assert labels == ["high", "medium", "low"]


def test_capital_s_cycles_back_to_created_order(module, fake_shell) -> None:
    project = _create_project("life os")
    _create_task(project.id, "first")
    _create_task(project.id, "second")
    _select(module, fake_shell, project)

    for _ in range(3):
        _entry(module, Scope.COLLECTION, "S").action()  # due -> priority -> created
    contents = module.collection_pane(fake_shell.current_context_item)
    labels = [i.label for i in contents.items]
    assert labels == ["first", "second"]


# --- x / v: bulk selection, then bulk c / dd ----------------------------------


def test_x_and_v_toggle_selection(module, fake_shell) -> None:
    project = _create_project("life os")
    _create_task(project.id, "task one")
    _select(module, fake_shell, project)
    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]

    _entry(module, Scope.COLLECTION, "x").action()
    assert fake_shell.current_collection_item.id in fake_shell.selected_ids

    _entry(module, Scope.COLLECTION, "v").action()
    assert fake_shell.current_collection_item.id not in fake_shell.selected_ids


def test_bulk_complete_acts_on_every_selected_task(module, fake_shell) -> None:
    project = _create_project("life os")
    one = _create_task(project.id, "one")
    two = _create_task(project.id, "two")
    _select(module, fake_shell, project)
    for task_id in (one.id, two.id):
        fake_shell.selected_ids.add(str(task_id))

    _entry(module, Scope.COLLECTION, "c").action()

    with deps.get_task_use_case() as use_case:
        assert use_case.execute(one.id).status is TaskStatus.DONE
        assert use_case.execute(two.id).status is TaskStatus.DONE
    assert fake_shell.selected_ids == set()


def test_undo_bulk_complete_restores_every_prior_status(module, fake_shell) -> None:
    project = _create_project("life os")
    one = _create_task(project.id, "one")
    two = _create_task(project.id, "two")
    with deps.start_task_use_case() as use_case:
        use_case.execute(two.id)
    _select(module, fake_shell, project)
    for task_id in (one.id, two.id):
        fake_shell.selected_ids.add(str(task_id))

    _entry(module, Scope.COLLECTION, "c").action()
    fake_shell.undo_stack.undo()

    with deps.get_task_use_case() as use_case:
        assert use_case.execute(one.id).status is TaskStatus.TODO
        assert use_case.execute(two.id).status is TaskStatus.DOING


def test_bulk_delete_acts_on_every_selected_task(module, fake_shell) -> None:
    from lifeos.domain import TaskNotFound

    project = _create_project("life os")
    one = _create_task(project.id, "one")
    two = _create_task(project.id, "two")
    _select(module, fake_shell, project)
    for task_id in (one.id, two.id):
        fake_shell.selected_ids.add(str(task_id))

    _entry(module, Scope.COLLECTION, "dd").action()
    fake_shell.confirm_yes()

    with deps.get_task_use_case() as use_case, pytest.raises(TaskNotFound):
        use_case.execute(one.id)
    with deps.get_task_use_case() as use_case, pytest.raises(TaskNotFound):
        use_case.execute(two.id)
    assert fake_shell.selected_ids == set()


# --- y: copy as markdown -------------------------------------------------------


def test_y_copies_the_task_as_markdown(module, fake_shell) -> None:
    project = _create_project("life os")
    _create_task(project.id, "write adr 0008", priority=Priority.HIGH)
    _select(module, fake_shell, project)
    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]

    _entry(module, Scope.COLLECTION, "y").action()

    assert len(fake_shell.clipboard) == 1
    assert "write adr 0008" in fake_shell.clipboard[0]
    assert fake_shell.clipboard[0].startswith("- [ ]")
