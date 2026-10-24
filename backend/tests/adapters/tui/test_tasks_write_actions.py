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


def _entry(module: ProjectsTasksModule, key: str):  # noqa: ANN201
    matches = [
        e
        for e in module.keymap_entries()
        if e.scope is Scope.COLLECTION and e.key == key
    ]
    assert len(matches) == 1, f"expected exactly one COLLECTION/{key!r} entry"
    return matches[0]


def _current_task(task_id):  # noqa: ANN001, ANN202
    with deps.get_task_use_case() as use_case:
        return use_case.execute(task_id)


def _select(module: ProjectsTasksModule, fake_shell, project) -> None:  # noqa: ANN001
    fake_shell.current_context_item = next(
        i for i in module.context_pane().items if i.payload.id == project.id
    )
    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]


# --- a / o: quick-add create -------------------------------------------------


def test_a_and_o_open_insert_prompt_for_quick_add(module, fake_shell) -> None:
    project = _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]
    for key in ("a", "o"):
        _entry(module, key).action()
        fake_shell.commit_pending_prompt("buy air filters !high @2026-08-03")
    tasks = module.collection_pane(fake_shell.current_context_item).items
    assert len(tasks) == 2
    task = _current_task(tasks[0].payload.id)
    assert task.title == "buy air filters"
    assert task.priority is Priority.HIGH
    assert task.due_date == date(2026, 8, 3)
    assert task.project_id == project.id


def test_a_selects_the_newly_created_task(module, fake_shell) -> None:
    _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "a").action()
    fake_shell.commit_pending_prompt("buy air filters")

    tasks = module.collection_pane(fake_shell.current_context_item).items
    assert len(tasks) == 1
    assert fake_shell.last_collection_select_id == str(tasks[0].payload.id)


def test_quick_add_hash_project_targets_a_different_project(module, fake_shell) -> None:
    _create_project("life os")
    casa = _create_project("casa")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "a").action()
    fake_shell.commit_pending_prompt("buy air filters #casa")

    casa_item = next(i for i in module.context_pane().items if i.payload.id == casa.id)
    tasks = module.collection_pane(casa_item).items
    assert len(tasks) == 1
    assert tasks[0].label == "buy air filters"


def test_quick_add_unresolved_hash_project_shows_an_error(module, fake_shell) -> None:
    _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "a").action()
    fake_shell.commit_pending_prompt("buy air filters #doesnotexist")

    assert any("project" in e for e in fake_shell.errors)
    assert module.collection_pane(fake_shell.current_context_item).items == []


def test_quick_add_hash_project_ambiguous_name_shows_an_error(
    module, fake_shell
) -> None:
    """Two projects can legally share a name (no uniqueness constraint) -
    silently picking the first match would route the task into whichever
    one happened to sort first; refuse instead, like the CLI's capture
    command does (cli/capture.py's AmbiguousProjectName)."""
    _create_project("casa")
    _create_project("casa")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "a").action()
    fake_shell.commit_pending_prompt("buy air filters #casa")

    assert any("ambiguous_project_name" in e for e in fake_shell.errors)
    for item in module.context_pane().items:
        assert module.collection_pane(item).items == []


def test_undo_quick_add_create_soft_deletes_and_redo_restores(
    module, fake_shell
) -> None:
    project = _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]
    _entry(module, "a").action()
    fake_shell.commit_pending_prompt("buy air filters")

    fake_shell.undo_stack.undo()
    assert module.collection_pane(fake_shell.current_context_item).items == []

    fake_shell.undo_stack.redo()
    tasks = module.collection_pane(fake_shell.current_context_item).items
    assert len(tasks) == 1
    assert _current_task(tasks[0].payload.id).project_id == project.id


# --- Space / c / s / r: status transitions -----------------------------------


def test_space_cycles_status_todo_doing_done_todo(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "space").action()
    assert _current_task(task.id).status is TaskStatus.DOING

    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]
    _entry(module, "space").action()
    assert _current_task(task.id).status is TaskStatus.DONE

    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]
    _entry(module, "space").action()
    assert _current_task(task.id).status is TaskStatus.TODO


def test_c_s_r_set_status_directly(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "c").action()
    assert _current_task(task.id).status is TaskStatus.DONE

    _entry(module, "r").action()
    assert _current_task(task.id).status is TaskStatus.TODO

    _entry(module, "s").action()
    assert _current_task(task.id).status is TaskStatus.DOING


def test_undo_status_change_restores_the_prior_status(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "c").action()
    fake_shell.undo_stack.undo()
    assert _current_task(task.id).status is TaskStatus.TODO


# --- e: rename title ---------------------------------------------------------


def test_e_renames_the_task_title(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "old title")
    _select(module, fake_shell, project)

    _entry(module, "e").action()
    fake_shell.commit_pending_prompt("new title")

    assert _current_task(task.id).title == "new title"


def test_undo_rename_title_restores_the_old_title(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "old title")
    _select(module, fake_shell, project)

    _entry(module, "e").action()
    fake_shell.commit_pending_prompt("new title")
    fake_shell.undo_stack.undo()

    assert _current_task(task.id).title == "old title"


# --- E: edit description in $EDITOR -------------------------------------------


def test_capital_e_edits_description_via_external_editor(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "a task", description="old description")
    _select(module, fake_shell, project)

    def fake_edit(initial_text: str) -> str:
        assert initial_text == "old description"
        return "new description"

    fake_shell.edit_in_external_editor = fake_edit

    _entry(module, "E").action()

    assert _current_task(task.id).description == "new description"


def test_undo_description_edit_restores_the_old_description(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "a task", description="old description")
    _select(module, fake_shell, project)
    fake_shell.edit_in_external_editor = lambda initial_text: "new description"  # noqa: ARG005

    _entry(module, "E").action()
    fake_shell.undo_stack.undo()

    assert _current_task(task.id).description == "old description"


# --- @: due date ---------------------------------------------------------------


def test_at_sign_sets_the_due_date_via_quick_add_syntax(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "at").action()
    fake_shell.commit_pending_prompt("2026-08-03")

    assert _current_task(task.id).due_date == date(2026, 8, 3)


def test_due_date_prompt_tolerates_a_leading_at_sign(module, fake_shell) -> None:
    """The due-date-only prompt expects bare input ("sat", no "@"), but
    quick-add trains "@sat" everywhere else in the app - typing it here out
    of habit must resolve the same date, not double up into "@@sat" and
    fail to parse."""
    project = _create_project("life os")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "at").action()
    fake_shell.commit_pending_prompt("@2026-08-03")

    assert _current_task(task.id).due_date == date(2026, 8, 3)
    assert fake_shell.errors == []


def test_undo_due_date_change_restores_the_old_due_date(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "a task", due_date=date(2026, 1, 1))
    _select(module, fake_shell, project)

    _entry(module, "at").action()
    fake_shell.commit_pending_prompt("2026-08-03")
    fake_shell.undo_stack.undo()

    assert _current_task(task.id).due_date == date(2026, 1, 1)


# --- p: priority picker ---------------------------------------------------------


def test_p_sets_priority_via_picker(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "p").action()
    fake_shell.pick("high")

    assert _current_task(task.id).priority is Priority.HIGH


def test_undo_priority_change_restores_the_old_priority(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "a task", priority=Priority.LOW)
    _select(module, fake_shell, project)

    _entry(module, "p").action()
    fake_shell.pick("high")
    fake_shell.undo_stack.undo()

    assert _current_task(task.id).priority is Priority.LOW


# --- m: move to another project -------------------------------------------------


def test_m_moves_the_task_via_picker(module, fake_shell) -> None:
    project = _create_project("life os")
    casa = _create_project("casa")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "m").action()
    fake_shell.pick("casa")

    assert _current_task(task.id).project_id == casa.id


def test_undo_move_restores_the_old_project(module, fake_shell) -> None:
    project = _create_project("life os")
    _create_project("casa")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "m").action()
    fake_shell.pick("casa")
    fake_shell.undo_stack.undo()

    assert _current_task(task.id).project_id == project.id


def test_moving_to_an_ambiguous_project_name_shows_an_error(module, fake_shell) -> None:
    project = _create_project("life os")
    _create_project("casa")
    _create_project("casa")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "m").action()
    fake_shell.pick("casa")

    assert any("ambiguous_project_name" in e for e in fake_shell.errors)
    assert _current_task(task.id).project_id == project.id


# --- dd: delete ------------------------------------------------------------------


def test_dd_asks_for_confirmation_before_deleting(module, fake_shell) -> None:
    from lifeos.domain import TaskNotFound

    project = _create_project("life os")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "dd").action()
    # not deleted yet - awaiting confirm
    assert _current_task(task.id).is_deleted is False

    fake_shell.confirm_yes()
    # Soft-deleted tasks are excluded from live lookups, same as everywhere
    # else in the app - GetTask raises rather than returning is_deleted=True.
    with pytest.raises(TaskNotFound):
        _current_task(task.id)
    assert fake_shell.reload_count == 1


def test_undo_delete_restores_the_task(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "a task")
    _select(module, fake_shell, project)

    _entry(module, "dd").action()
    fake_shell.confirm_yes()
    fake_shell.undo_stack.undo()

    assert _current_task(task.id).is_deleted is False
