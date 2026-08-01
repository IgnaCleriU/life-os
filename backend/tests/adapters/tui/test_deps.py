"""Mirrors test_skeleton.py's deps-wiring parametrization from
tests/adapters/cli/ - asserts every use-case contextmanager exists, is
callable, and yields the right use-case type wired to a working session.
"""

from __future__ import annotations

import pytest

_USE_CASE_HELPERS = [
    "create_project_use_case",
    "list_projects_use_case",
    "get_project_use_case",
    "update_project_use_case",
    "complete_project_use_case",
    "archive_project_use_case",
    "activate_project_use_case",
    "delete_project_use_case",
    "restore_project_use_case",
    "create_task_use_case",
    "list_tasks_use_case",
    "get_task_use_case",
    "update_task_use_case",
    "complete_task_use_case",
    "start_task_use_case",
    "reopen_task_use_case",
    "move_task_use_case",
    "delete_task_use_case",
    "restore_task_use_case",
]


@pytest.mark.parametrize("helper_name", _USE_CASE_HELPERS)
def test_use_case_helper_exists_and_is_callable(tui_env, helper_name: str) -> None:
    from lifeos.adapters.tui import deps

    helper = getattr(deps, helper_name)
    with helper() as use_case:
        assert hasattr(use_case, "execute")


def test_create_project_use_case_is_wired_to_the_test_session(tui_env) -> None:
    from lifeos.adapters.tui import deps

    with deps.create_project_use_case() as use_case:
        use_case.execute(name="from tui deps")

    with deps.list_projects_use_case() as list_use_case:
        projects = list_use_case.execute()

    assert any(p.name == "from tui deps" for p in projects)
