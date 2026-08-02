"""Tests end-to-end de las tools MCP contra una DB SQLite en memoria.

Ejercitan cada tool a través de una `ClientSession` real del SDK (no
llamando a las funciones de `tools.py` directamente), para validar también
la traducción de argumentos/errores que hace FastMCP.
"""

from __future__ import annotations


def _create_project(call_tool, name: str = "Roadmap") -> dict:
    result = call_tool("create_project", {"name": name})
    assert result.isError is False
    return result.structuredContent


def _create_task(call_tool, project_id: str, **kwargs) -> dict:
    result = call_tool("create_task", {"project_id": project_id, **kwargs})
    assert result.isError is False
    return result.structuredContent


class TestCreateProject:
    def test_creates_and_returns_project(self, call_tool):
        project = _create_project(call_tool, "Life OS MVP")

        assert project["name"] == "Life OS MVP"
        assert project["description"] is None
        assert project["status"] == "active"
        assert project["id"]
        assert project["created_at"]

    def test_empty_name_is_a_domain_validation_error(self, call_tool):
        result = call_tool("create_project", {"name": "   "})

        assert result.isError is True
        assert "domain_validation_error" in result.content[0].text


class TestListProjects:
    def test_lists_created_projects(self, call_tool):
        _create_project(call_tool, "Project A")
        _create_project(call_tool, "Project B")

        result = call_tool("list_projects")

        assert result.isError is False
        names = {p["name"] for p in result.structuredContent["result"]}
        assert names == {"Project A", "Project B"}

    def test_empty_when_no_projects(self, call_tool):
        result = call_tool("list_projects")

        assert result.isError is False
        assert result.structuredContent["result"] == []


class TestCreateTask:
    def test_creates_task_under_existing_project(self, call_tool):
        project = _create_project(call_tool)

        task = _create_task(call_tool, project["id"], title="Write ADRs")

        assert task["project_id"] == project["id"]
        assert task["title"] == "Write ADRs"
        assert task["status"] == "todo"
        assert task["priority"] == "medium"
        assert task["due_date"] is None

    def test_accepts_priority_and_due_date(self, call_tool):
        project = _create_project(call_tool)

        task = _create_task(
            call_tool,
            project["id"],
            title="Ship MCP adapter",
            priority="high",
            due_date="2026-08-01",
        )

        assert task["priority"] == "high"
        assert task["due_date"] == "2026-08-01"

    def test_unknown_project_is_project_not_found(self, call_tool):
        result = call_tool(
            "create_task",
            {"project_id": "00000000-0000-0000-0000-000000000000", "title": "x"},
        )

        assert result.isError is True
        assert "project_not_found" in result.content[0].text

    def test_empty_title_is_a_domain_validation_error(self, call_tool):
        project = _create_project(call_tool)

        result = call_tool(
            "create_task", {"project_id": project["id"], "title": "   "}
        )

        assert result.isError is True
        assert "domain_validation_error" in result.content[0].text


class TestListTasks:
    def test_lists_tasks_of_a_project(self, call_tool):
        project = _create_project(call_tool)
        _create_task(call_tool, project["id"], title="Task 1")
        _create_task(call_tool, project["id"], title="Task 2")

        result = call_tool("list_tasks", {"project_id": project["id"]})

        assert result.isError is False
        titles = {t["title"] for t in result.structuredContent["result"]}
        assert titles == {"Task 1", "Task 2"}

    def test_empty_for_project_without_tasks(self, call_tool):
        project = _create_project(call_tool)

        result = call_tool("list_tasks", {"project_id": project["id"]})

        assert result.isError is False
        assert result.structuredContent["result"] == []


class TestUpdateTask:
    def test_updates_only_provided_fields(self, call_tool):
        project = _create_project(call_tool)
        task = _create_task(
            call_tool, project["id"], title="Draft", due_date="2026-08-01"
        )

        result = call_tool(
            "update_task", {"task_id": task["id"], "title": "Draft v2"}
        )

        assert result.isError is False
        updated = result.structuredContent
        assert updated["title"] == "Draft v2"
        assert updated["due_date"] == "2026-08-01"

    def test_omitted_due_date_leaves_it_untouched(self, call_tool):
        project = _create_project(call_tool)
        task = _create_task(
            call_tool, project["id"], title="Draft", due_date="2026-08-01"
        )

        result = call_tool(
            "update_task", {"task_id": task["id"], "priority": "high"}
        )

        assert result.structuredContent["due_date"] == "2026-08-01"

    def test_explicit_null_due_date_clears_it(self, call_tool):
        project = _create_project(call_tool)
        task = _create_task(
            call_tool, project["id"], title="Draft", due_date="2026-08-01"
        )

        result = call_tool(
            "update_task", {"task_id": task["id"], "due_date": None}
        )

        assert result.isError is False
        assert result.structuredContent["due_date"] is None

    def test_unknown_task_is_task_not_found(self, call_tool):
        result = call_tool(
            "update_task",
            {
                "task_id": "00000000-0000-0000-0000-000000000000",
                "title": "x",
            },
        )

        assert result.isError is True
        assert "task_not_found" in result.content[0].text


class TestCompleteTask:
    def test_marks_task_as_done(self, call_tool):
        project = _create_project(call_tool)
        task = _create_task(call_tool, project["id"], title="Draft")

        result = call_tool("complete_task", {"task_id": task["id"]})

        assert result.isError is False
        assert result.structuredContent["status"] == "done"

    def test_is_idempotent(self, call_tool):
        project = _create_project(call_tool)
        task = _create_task(call_tool, project["id"], title="Draft")
        call_tool("complete_task", {"task_id": task["id"]})

        result = call_tool("complete_task", {"task_id": task["id"]})

        assert result.isError is False
        assert result.structuredContent["status"] == "done"

    def test_unknown_task_is_task_not_found(self, call_tool):
        result = call_tool(
            "complete_task", {"task_id": "00000000-0000-0000-0000-000000000000"}
        )

        assert result.isError is True
        assert "task_not_found" in result.content[0].text


class TestGetProject:
    def test_returns_the_project(self, call_tool):
        project = _create_project(call_tool)

        result = call_tool("get_project", {"project_id": project["id"]})

        assert result.isError is False
        assert result.structuredContent["id"] == project["id"]

    def test_unknown_project_is_project_not_found(self, call_tool):
        result = call_tool(
            "get_project", {"project_id": "00000000-0000-0000-0000-000000000000"}
        )

        assert result.isError is True
        assert "project_not_found" in result.content[0].text


class TestUpdateProject:
    def test_updates_name(self, call_tool):
        project = _create_project(call_tool, "Original")

        result = call_tool(
            "update_project", {"project_id": project["id"], "name": "Renamed"}
        )

        assert result.isError is False
        assert result.structuredContent["name"] == "Renamed"

    def test_omitted_description_leaves_it_untouched(self, call_tool):
        result = call_tool(
            "create_project", {"name": "Life OS", "description": "original"}
        )
        project = result.structuredContent

        updated = call_tool(
            "update_project", {"project_id": project["id"], "name": "Life OS v2"}
        )

        assert updated.structuredContent["description"] == "original"

    def test_explicit_null_description_clears_it(self, call_tool):
        result = call_tool(
            "create_project", {"name": "Life OS", "description": "original"}
        )
        project = result.structuredContent

        updated = call_tool(
            "update_project", {"project_id": project["id"], "description": None}
        )

        assert updated.isError is False
        assert updated.structuredContent["description"] is None


class TestProjectStatusTransitions:
    def test_complete_archive_activate(self, call_tool):
        project = _create_project(call_tool)

        assert (
            call_tool(
                "complete_project", {"project_id": project["id"]}
            ).structuredContent["status"]
            == "completed"
        )
        assert (
            call_tool(
                "archive_project", {"project_id": project["id"]}
            ).structuredContent["status"]
            == "archived"
        )
        assert (
            call_tool(
                "activate_project", {"project_id": project["id"]}
            ).structuredContent["status"]
            == "active"
        )

    def test_unknown_project_is_project_not_found(self, call_tool):
        result = call_tool(
            "complete_project",
            {"project_id": "00000000-0000-0000-0000-000000000000"},
        )

        assert result.isError is True
        assert "project_not_found" in result.content[0].text


class TestReorderProject:
    def test_reorder_up_and_down_swap_with_the_neighbor(self, call_tool):
        first = _create_project(call_tool, "First")
        second = _create_project(call_tool, "Second")
        assert (first["position"], second["position"]) == (0, 1)

        up = call_tool("reorder_project_up", {"project_id": second["id"]})
        assert up.isError is False
        assert up.structuredContent["position"] == 0

        listed = call_tool("list_projects")
        assert [p["id"] for p in listed.structuredContent["result"]] == [
            second["id"],
            first["id"],
        ]

        down = call_tool("reorder_project_down", {"project_id": second["id"]})
        assert down.isError is False
        assert down.structuredContent["position"] == 1

    def test_reorder_up_on_the_first_project_is_a_noop(self, call_tool):
        first = _create_project(call_tool, "First")
        _create_project(call_tool, "Second")

        result = call_tool("reorder_project_up", {"project_id": first["id"]})

        assert result.isError is False
        assert result.structuredContent["position"] == 0

    def test_reorder_unknown_project_is_project_not_found(self, call_tool):
        result = call_tool(
            "reorder_project_up",
            {"project_id": "00000000-0000-0000-0000-000000000000"},
        )

        assert result.isError is True
        assert "project_not_found" in result.content[0].text


class TestDeleteAndRestoreProject:
    def test_delete_empty_project_hides_it(self, call_tool):
        project = _create_project(call_tool)

        deleted = call_tool("delete_project", {"project_id": project["id"]})
        assert deleted.isError is False

        result = call_tool("get_project", {"project_id": project["id"]})
        assert result.isError is True

    def test_delete_project_with_live_tasks_is_project_not_empty(self, call_tool):
        project = _create_project(call_tool)
        _create_task(call_tool, project["id"], title="Tarea")

        result = call_tool("delete_project", {"project_id": project["id"]})

        assert result.isError is True
        assert "project_not_empty" in result.content[0].text

    def test_restore_makes_it_visible_again(self, call_tool):
        project = _create_project(call_tool)
        call_tool("delete_project", {"project_id": project["id"]})

        restored = call_tool("restore_project", {"project_id": project["id"]})

        assert restored.isError is False
        assert call_tool("get_project", {"project_id": project["id"]}).isError is False


class TestListProjectsFilters:
    def test_filters_by_status(self, call_tool):
        _create_project(call_tool, "Active")
        archived = _create_project(call_tool, "Archived")
        call_tool("archive_project", {"project_id": archived["id"]})

        result = call_tool("list_projects", {"status": ["archived"]})

        names = {p["name"] for p in result.structuredContent["result"]}
        assert names == {"Archived"}

    def test_filters_by_text(self, call_tool):
        _create_project(call_tool, "Casa de campo")
        _create_project(call_tool, "Finanzas")

        result = call_tool("list_projects", {"text": "CASA"})

        names = {p["name"] for p in result.structuredContent["result"]}
        assert names == {"Casa de campo"}


class TestGetTask:
    def test_returns_the_task(self, call_tool):
        project = _create_project(call_tool)
        task = _create_task(call_tool, project["id"], title="Tarea")

        result = call_tool("get_task", {"task_id": task["id"]})

        assert result.isError is False
        assert result.structuredContent["id"] == task["id"]

    def test_unknown_task_is_task_not_found(self, call_tool):
        result = call_tool(
            "get_task", {"task_id": "00000000-0000-0000-0000-000000000000"}
        )

        assert result.isError is True
        assert "task_not_found" in result.content[0].text


class TestUpdateTaskDescription:
    def test_omitted_description_leaves_it_untouched(self, call_tool):
        project = _create_project(call_tool)
        task = _create_task(
            call_tool, project["id"], title="Tarea", description="original"
        )

        updated = call_tool(
            "update_task", {"task_id": task["id"], "priority": "high"}
        )

        assert updated.structuredContent["description"] == "original"

    def test_explicit_null_description_clears_it(self, call_tool):
        """Antes era imposible: `description` no tenía centinela y un `None`
        explícito se confundía con "no tocar"."""
        project = _create_project(call_tool)
        task = _create_task(
            call_tool, project["id"], title="Tarea", description="original"
        )

        updated = call_tool(
            "update_task", {"task_id": task["id"], "description": None}
        )

        assert updated.isError is False
        assert updated.structuredContent["description"] is None


class TestTaskStatusTransitions:
    def test_start_and_reopen(self, call_tool):
        project = _create_project(call_tool)
        task = _create_task(call_tool, project["id"], title="Tarea")

        assert (
            call_tool("start_task", {"task_id": task["id"]}).structuredContent[
                "status"
            ]
            == "doing"
        )
        assert (
            call_tool("reopen_task", {"task_id": task["id"]}).structuredContent[
                "status"
            ]
            == "todo"
        )

    def test_unknown_task_is_task_not_found(self, call_tool):
        result = call_tool(
            "start_task", {"task_id": "00000000-0000-0000-0000-000000000000"}
        )

        assert result.isError is True
        assert "task_not_found" in result.content[0].text


class TestMoveTask:
    def test_moves_to_another_project(self, call_tool):
        origin = _create_project(call_tool, "Origin")
        destination = _create_project(call_tool, "Destination")
        task = _create_task(call_tool, origin["id"], title="Tarea")

        result = call_tool(
            "move_task", {"task_id": task["id"], "project_id": destination["id"]}
        )

        assert result.isError is False
        assert result.structuredContent["project_id"] == destination["id"]

    def test_unknown_destination_is_project_not_found(self, call_tool):
        project = _create_project(call_tool)
        task = _create_task(call_tool, project["id"], title="Tarea")

        result = call_tool(
            "move_task",
            {
                "task_id": task["id"],
                "project_id": "00000000-0000-0000-0000-000000000000",
            },
        )

        assert result.isError is True
        assert "project_not_found" in result.content[0].text


class TestDeleteAndRestoreTask:
    def test_delete_hides_it_and_restore_brings_it_back(self, call_tool):
        project = _create_project(call_tool)
        task = _create_task(call_tool, project["id"], title="Tarea")

        deleted = call_tool("delete_task", {"task_id": task["id"]})
        assert deleted.isError is False
        assert call_tool("get_task", {"task_id": task["id"]}).isError is True

        restored = call_tool("restore_task", {"task_id": task["id"]})
        assert restored.isError is False
        assert call_tool("get_task", {"task_id": task["id"]}).isError is False


class TestListTasksFilters:
    def test_lists_across_projects_without_project_id(self, call_tool):
        project_a = _create_project(call_tool, "A")
        project_b = _create_project(call_tool, "B")
        _create_task(call_tool, project_a["id"], title="Task A")
        _create_task(call_tool, project_b["id"], title="Task B")

        result = call_tool("list_tasks")

        titles = {t["title"] for t in result.structuredContent["result"]}
        assert titles == {"Task A", "Task B"}

    def test_filters_by_due_before(self, call_tool):
        project = _create_project(call_tool)
        vencida = _create_task(
            call_tool, project["id"], title="Vencida", due_date="2026-07-01"
        )
        _create_task(call_tool, project["id"], title="Futura", due_date="2026-12-01")

        result = call_tool("list_tasks", {"due_before": "2026-07-28"})

        ids = {t["id"] for t in result.structuredContent["result"]}
        assert ids == {vencida["id"]}

    def test_filters_by_text(self, call_tool):
        project = _create_project(call_tool)
        match = _create_task(call_tool, project["id"], title="Pagar EXPENSAS")
        _create_task(call_tool, project["id"], title="Otra cosa")

        result = call_tool("list_tasks", {"text": "expensas"})

        ids = {t["id"] for t in result.structuredContent["result"]}
        assert ids == {match["id"]}
