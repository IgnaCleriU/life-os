from __future__ import annotations

import pytest

from lifeos.adapters.tui import deps
from lifeos.adapters.tui.keymap import Scope
from lifeos.adapters.tui.modules.projects_tasks import ProjectsTasksModule
from lifeos.domain import DomainValidationError


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
    assert len(matches) == 1
    return matches[0]


def _current_projects() -> list[str]:
    with deps.list_projects_use_case() as use_case:
        return [p.name for p in use_case.execute()]


# --- whitespace-only text input is treated as cancel, not an error -----------


def test_whitespace_only_project_name_is_silently_ignored(module, fake_shell) -> None:
    _entry(module, Scope.CONTEXT, "a").action()
    fake_shell.commit_pending_prompt("   ")
    assert _current_projects() == []
    assert fake_shell.reload_count == 0
    assert fake_shell.errors == []


def test_whitespace_only_project_rename_is_silently_ignored(module, fake_shell) -> None:
    project = _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, Scope.CONTEXT, "e").action()
    fake_shell.commit_pending_prompt("   ")

    with deps.get_project_use_case() as use_case:
        assert use_case.execute(project.id).name == "life os"


def test_whitespace_only_quick_add_title_is_silently_ignored(
    module, fake_shell
) -> None:
    _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, Scope.COLLECTION, "a").action()
    fake_shell.commit_pending_prompt("   !high @sat")  # sigils, no real title

    assert module.collection_pane(fake_shell.current_context_item).items == []


def test_whitespace_only_task_rename_is_silently_ignored(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "old title")
    fake_shell.current_context_item = module.context_pane().items[0]
    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]

    _entry(module, Scope.COLLECTION, "e").action()
    fake_shell.commit_pending_prompt("   ")

    with deps.get_task_use_case() as use_case:
        assert use_case.execute(task.id).title == "old title"


# --- the general safety net: an unexpected domain error surfaces, doesn't crash


def test_try_call_shows_a_mapped_domain_error_instead_of_raising(
    module, fake_shell
) -> None:
    def _raises() -> None:
        raise DomainValidationError("the title cannot be empty")

    result = module._try_call(_raises)  # noqa: SLF001

    assert result is module._FAILED  # noqa: SLF001
    assert len(fake_shell.errors) == 1
    assert "domain_validation_error" in fake_shell.errors[0]
    assert "the title cannot be empty" in fake_shell.errors[0]


def test_try_call_returns_the_action_result_on_success(module, fake_shell) -> None:
    result = module._try_call(lambda: 42)  # noqa: SLF001
    assert result == 42
    assert fake_shell.errors == []


# --- the safety net actually wraps every real write action, not just itself --
#
# _try_call's own docstring names the trigger: "an entity deleted out from
# under a still-open prompt". These simulate exactly that (delete via deps
# directly, as a concurrent REST/MCP client sharing the same DB would) and
# assert the mid-flow action degrades to a status-bar error instead of
# raising through on_commit/on_select/on_yes and crashing the app.


def test_renaming_a_project_deleted_out_from_under_the_prompt_shows_an_error(
    module, fake_shell
) -> None:
    project = _create_project("life os")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, Scope.CONTEXT, "e").action()
    with deps.delete_project_use_case() as use_case:
        use_case.execute(project.id)
    fake_shell.commit_pending_prompt("renamed")

    assert any("project_not_found" in e for e in fake_shell.errors)


def test_renaming_a_task_deleted_out_from_under_the_prompt_shows_an_error(
    module, fake_shell
) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "old title")
    fake_shell.current_context_item = module.context_pane().items[0]
    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]

    _entry(module, Scope.COLLECTION, "e").action()
    with deps.delete_task_use_case() as use_case:
        use_case.execute(task.id)
    fake_shell.commit_pending_prompt("renamed")

    assert any("task_not_found" in e for e in fake_shell.errors)


def test_setting_priority_on_a_deleted_task_shows_an_error(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "task")
    fake_shell.current_context_item = module.context_pane().items[0]
    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]

    _entry(module, Scope.COLLECTION, "p").action()
    with deps.delete_task_use_case() as use_case:
        use_case.execute(task.id)
    fake_shell.pick("high")

    assert any("task_not_found" in e for e in fake_shell.errors)


def test_setting_due_date_on_a_deleted_task_shows_an_error(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "task")
    fake_shell.current_context_item = module.context_pane().items[0]
    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]

    _entry(module, Scope.COLLECTION, "at").action()
    with deps.delete_task_use_case() as use_case:
        use_case.execute(task.id)
    fake_shell.commit_pending_prompt("tomorrow")

    assert any("task_not_found" in e for e in fake_shell.errors)


def test_moving_a_deleted_task_shows_an_error(module, fake_shell) -> None:
    project = _create_project("life os")
    _create_project("other")
    task = _create_task(project.id, "task")
    fake_shell.current_context_item = module.context_pane().items[0]
    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]

    _entry(module, Scope.COLLECTION, "m").action()
    with deps.delete_task_use_case() as use_case:
        use_case.execute(task.id)
    fake_shell.pick("other")

    assert any("task_not_found" in e for e in fake_shell.errors)


def test_completing_an_already_deleted_task_shows_an_error(module, fake_shell) -> None:
    project = _create_project("life os")
    task = _create_task(project.id, "task")
    fake_shell.current_context_item = module.context_pane().items[0]
    fake_shell.current_collection_item = module.collection_pane(
        fake_shell.current_context_item
    ).items[0]
    with deps.delete_task_use_case() as use_case:
        use_case.execute(task.id)

    _entry(module, Scope.COLLECTION, "c").action()

    assert any("task_not_found" in e for e in fake_shell.errors)


def test_bulk_completing_tasks_when_one_was_deleted_shows_an_error(
    module, fake_shell
) -> None:
    project = _create_project("life os")
    task1 = _create_task(project.id, "task 1")
    task2 = _create_task(project.id, "task 2")
    fake_shell.selected_ids = {str(task1.id), str(task2.id)}
    with deps.delete_task_use_case() as use_case:
        use_case.execute(task2.id)

    _entry(module, Scope.COLLECTION, "c").action()

    assert any("task_not_found" in e for e in fake_shell.errors)
    with deps.get_task_use_case() as use_case:
        assert use_case.execute(task1.id).status.value == "todo"  # untouched


def test_deleting_a_non_empty_project_still_shows_the_mapped_error(
    module, fake_shell
) -> None:
    """Regression: _commit_delete_project's hand-rolled except ProjectNotEmpty
    is being replaced by the generic _guarded/_try_call wrapper - this must
    keep working the same way."""
    project = _create_project("life os")
    _create_task(project.id, "a live task")
    fake_shell.current_context_item = module.context_pane().items[0]

    _entry(module, Scope.CONTEXT, "dd").action()
    fake_shell.confirm_yes()

    assert any("project_not_empty" in e for e in fake_shell.errors)
