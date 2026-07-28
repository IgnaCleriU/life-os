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
