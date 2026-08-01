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
