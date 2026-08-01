from __future__ import annotations

from datetime import date
from uuid import UUID

from lifeos.adapters.tui import deps
from lifeos.adapters.tui.keymap import KeymapEntry
from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.domain import Priority, Project, Task, TaskStatus

_STATUS_GLYPHS = {
    TaskStatus.TODO: "·",
    TaskStatus.DOING: "◐",
    TaskStatus.DONE: "✓",
}

_OPEN_TASK_STATUSES = [TaskStatus.TODO, TaskStatus.DOING]


class ProjectsTasksModule:
    """The real Projects/Tasks TUI module, replacing Step 12's stub. Calls
    the same use cases REST, MCP, and the CLI already expose, wired through
    `adapters/tui/deps.py`. Returns domain entities as `PaneItem.payload`,
    per ADR 0008: the shell never inspects them.
    """

    def __init__(self) -> None:
        self.shell: object | None = None

    # --- TuiModule contract ---------------------------------------------------

    def context_pane(self) -> PaneContents:
        with deps.list_projects_use_case() as use_case:
            projects = use_case.execute()
        items = [self._project_to_item(project) for project in projects]
        return PaneContents(title="PROJECTS", items=items)

    def collection_pane(self, context_item: PaneItem | None) -> PaneContents:
        if context_item is None:
            return PaneContents(title="TASKS", items=[])
        project: Project = context_item.payload
        with deps.list_tasks_use_case() as use_case:
            tasks = use_case.execute(project.id)
        items = [self._task_to_item(task) for task in tasks]
        return PaneContents(title=f"TASKS - {project.name}", items=items)

    def detail_pane(self, collection_item: PaneItem | None) -> DetailContents | None:
        if collection_item is None:
            return None
        task: Task = collection_item.payload
        with deps.get_project_use_case() as use_case:
            project = use_case.execute(task.project_id)
        fields = [
            ("status", task.status.value),
            ("priority", task.priority.value),
            ("due", task.due_date.isoformat() if task.due_date else "-"),
            ("project", project.name),
            ("created", task.created_at.date().isoformat()),
            ("description", task.description or "-"),
        ]
        return DetailContents(title=task.title, fields=fields)

    def keymap_entries(self) -> list[KeymapEntry]:
        return []

    # --- rendering helpers ------------------------------------------------

    def _project_to_item(self, project: Project) -> PaneItem:
        return PaneItem(
            id=str(project.id),
            label=project.name,
            payload=project,
            meta=str(self._open_task_count(project.id)),
        )

    def _open_task_count(self, project_id: UUID) -> int:
        with deps.list_tasks_use_case() as use_case:
            tasks = use_case.execute(project_id, statuses=_OPEN_TASK_STATUSES)
        return len(tasks)

    def _task_to_item(self, task: Task) -> PaneItem:
        parts = [_STATUS_GLYPHS[task.status]]
        if task.priority is Priority.HIGH:
            parts.append("!")
        if task.due_date is not None:
            due_text = task.due_date.isoformat()
            is_past = task.due_date < date.today()
            overdue = is_past and task.status is not TaskStatus.DONE
            parts.append(f"[red]{due_text}[/red]" if overdue else due_text)
        meta = " ".join(parts)
        return PaneItem(id=str(task.id), label=task.title, payload=task, meta=meta)
