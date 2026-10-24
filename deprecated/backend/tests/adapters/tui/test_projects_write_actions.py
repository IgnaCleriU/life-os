from __future__ import annotations

import pytest

from lifeos.adapters.tui import deps
from lifeos.adapters.tui.keymap import Scope
from lifeos.adapters.tui.modules.projects_tasks import ProjectsTasksModule
from lifeos.domain import ProjectStatus


@pytest.fixture
def module(tui_env, fake_shell) -> ProjectsTasksModule:
    mod = ProjectsTasksModule()
    mod.shell = fake_shell
    return mod


def _create_project(name: str):  # noqa: ANN202
    with deps.create_project_use_case() as use_case:
        return use_case.execute(name=name)


def _entry(module: ProjectsTasksModule, key: str):  # noqa: ANN201
    matches = [
        e for e in module.keymap_entries() if e.scope is Scope.CONTEXT and e.key == key
    ]
    assert len(matches) == 1, f"expected exactly one CONTEXT/{key!r} entry"
    return matches[0]


def _current_projects() -> dict[str, ProjectStatus]:
    with deps.list_projects_use_case() as use_case:
        return {p.name: p.status for p in use_case.execute()}


# --- a: create -----------------------------------------------------------


def test_a_opens_insert_prompt_and_commits_a_new_project(module, fake_shell) -> None:
    _entry(module, "a").action()
    fake_shell.commit_pending_prompt("casa")
    assert "casa" in _current_projects()
    assert fake_shell.reload_count == 1


def test_undo_create_soft_deletes_and_redo_restores(module, fake_shell) -> None:
    _entry(module, "a").action()
    fake_shell.commit_pending_prompt("casa")

    write = fake_shell.undo_stack.undo()
    assert write is not None
    assert "casa" not in _current_projects()

    fake_shell.undo_stack.redo()
    assert "casa" in _current_projects()


# --- e: rename -------------------------------------------------------------


def test_e_renames_the_selected_project(module, fake_shell) -> None:
    project = _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "e").action()
    fake_shell.commit_pending_prompt("life-os")

    with deps.get_project_use_case() as use_case:
        assert use_case.execute(project.id).name == "life-os"


def test_undo_rename_restores_the_old_name(module, fake_shell) -> None:
    project = _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "e").action()
    fake_shell.commit_pending_prompt("life-os")
    fake_shell.undo_stack.undo()

    with deps.get_project_use_case() as use_case:
        assert use_case.execute(project.id).name == "life os"


# --- c: complete -----------------------------------------------------------


def test_c_completes_the_selected_project(module, fake_shell) -> None:
    _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "c").action()

    assert _current_projects()["life os"] is ProjectStatus.COMPLETED
    assert fake_shell.reload_count == 1


def test_undo_complete_restores_the_prior_status(module, fake_shell) -> None:
    _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "c").action()
    fake_shell.undo_stack.undo()

    assert _current_projects()["life os"] is ProjectStatus.ACTIVE


# --- A: archive/activate toggle ---------------------------------------------


def test_capital_a_archives_an_active_project(module, fake_shell) -> None:
    _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "A").action()

    assert _current_projects()["life os"] is ProjectStatus.ARCHIVED


def test_capital_a_activates_an_archived_project(module, fake_shell) -> None:
    project = _create_project("life os")
    with deps.archive_project_use_case() as use_case:
        use_case.execute(project.id)
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "A").action()

    assert _current_projects()["life os"] is ProjectStatus.ACTIVE


def test_undo_archive_toggle_restores_the_prior_status(module, fake_shell) -> None:
    _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "A").action()
    fake_shell.undo_stack.undo()

    assert _current_projects()["life os"] is ProjectStatus.ACTIVE


# --- dd: delete --------------------------------------------------------------


def test_dd_asks_for_confirmation_before_deleting(module, fake_shell) -> None:
    _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "dd").action()
    assert "life os" in _current_projects()  # not deleted yet - awaiting confirm

    fake_shell.confirm_yes()
    assert "life os" not in _current_projects()
    assert fake_shell.reload_count == 1


def test_undo_delete_restores_the_project(module, fake_shell) -> None:
    _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "dd").action()
    fake_shell.confirm_yes()
    fake_shell.undo_stack.undo()

    assert "life os" in _current_projects()


def test_deleting_a_non_empty_project_shows_an_error_not_a_crash(
    module, fake_shell
) -> None:
    project = _create_project("life os")
    with deps.create_task_use_case() as use_case:
        use_case.execute(project.id, "a live task")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, "dd").action()
    fake_shell.confirm_yes()

    assert "life os" in _current_projects()  # still there
    assert any("project_not_empty" in e for e in fake_shell.errors)
