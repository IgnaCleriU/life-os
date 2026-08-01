from __future__ import annotations

from datetime import date
from uuid import UUID

from lifeos.adapters.tui import deps
from lifeos.adapters.tui.keymap import KeymapEntry, Scope
from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.undo import UndoableWrite
from lifeos.domain import (
    Priority,
    Project,
    ProjectNotEmpty,
    ProjectStatus,
    Task,
    TaskStatus,
)

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
        return [
            KeymapEntry(
                Scope.CONTEXT, "a", "create a project", self._start_create_project
            ),
            KeymapEntry(
                Scope.CONTEXT, "e", "rename project", self._start_rename_project
            ),
            KeymapEntry(
                Scope.CONTEXT, "c", "complete project", self._complete_project
            ),
            KeymapEntry(
                Scope.CONTEXT,
                "A",
                "archive/activate project",
                self._toggle_archive_project,
            ),
            KeymapEntry(
                Scope.CONTEXT, "dd", "delete project", self._start_delete_project
            ),
        ]

    # --- projects-pane write actions -------------------------------------

    def _push_undo(self, description: str, *, undo, redo) -> None:  # noqa: ANN001
        self.shell.undo_stack.push(  # type: ignore[attr-defined]
            UndoableWrite(description=description, undo=undo, redo=redo)
        )

    def _start_create_project(self) -> None:
        shell = self.shell
        assert shell is not None
        shell.prompt_insert(  # type: ignore[attr-defined]
            placeholder="new project name", on_commit=self._commit_create_project
        )

    def _commit_create_project(self, name: str) -> None:
        if not name:
            return
        with deps.create_project_use_case() as use_case:
            project = use_case.execute(name=name)
        self._push_undo(
            f"create project {name!r}",
            undo=lambda: self._delete_project(project.id),
            redo=lambda: self._restore_project(project.id),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _start_rename_project(self) -> None:
        shell = self.shell
        assert shell is not None
        item = shell.current_context_item  # type: ignore[attr-defined]
        if item is None:
            return
        project: Project = item.payload
        shell.prompt_insert(  # type: ignore[attr-defined]
            placeholder=project.name,
            on_commit=lambda text: self._commit_rename_project(
                project.id, project.name, text
            ),
        )

    def _commit_rename_project(
        self, project_id: UUID, old_name: str, new_name: str
    ) -> None:
        if not new_name:
            return
        self._rename_project(project_id, new_name)
        self._push_undo(
            f"rename project to {new_name!r}",
            undo=lambda: self._rename_project(project_id, old_name),
            redo=lambda: self._rename_project(project_id, new_name),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _rename_project(self, project_id: UUID, name: str) -> None:
        with deps.update_project_use_case() as use_case:
            use_case.execute(project_id, name=name)

    def _complete_project(self) -> None:
        shell = self.shell
        assert shell is not None
        item = shell.current_context_item  # type: ignore[attr-defined]
        if item is None:
            return
        project: Project = item.payload
        prior_status = project.status
        self._set_project_status(project.id, ProjectStatus.COMPLETED)
        self._push_undo(
            "complete project",
            undo=lambda: self._set_project_status(project.id, prior_status),
            redo=lambda: self._set_project_status(project.id, ProjectStatus.COMPLETED),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _toggle_archive_project(self) -> None:
        shell = self.shell
        assert shell is not None
        item = shell.current_context_item  # type: ignore[attr-defined]
        if item is None:
            return
        project: Project = item.payload
        prior_status = project.status
        if prior_status is ProjectStatus.ARCHIVED:
            new_status = ProjectStatus.ACTIVE
            description = "activate project"
        else:
            new_status = ProjectStatus.ARCHIVED
            description = "archive project"
        self._set_project_status(project.id, new_status)
        self._push_undo(
            description,
            undo=lambda: self._set_project_status(project.id, prior_status),
            redo=lambda: self._set_project_status(project.id, new_status),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _set_project_status(self, project_id: UUID, status: ProjectStatus) -> None:
        if status is ProjectStatus.COMPLETED:
            with deps.complete_project_use_case() as use_case:
                use_case.execute(project_id)
        elif status is ProjectStatus.ARCHIVED:
            with deps.archive_project_use_case() as use_case:
                use_case.execute(project_id)
        else:
            with deps.activate_project_use_case() as use_case:
                use_case.execute(project_id)

    def _start_delete_project(self) -> None:
        shell = self.shell
        assert shell is not None
        item = shell.current_context_item  # type: ignore[attr-defined]
        if item is None:
            return
        project: Project = item.payload
        shell.confirm(  # type: ignore[attr-defined]
            f"delete project {project.name!r}?",
            on_yes=lambda: self._commit_delete_project(project.id, project.name),
        )

    def _commit_delete_project(self, project_id: UUID, name: str) -> None:
        try:
            self._delete_project(project_id)
        except ProjectNotEmpty:
            self.shell.show_error(  # type: ignore[attr-defined]
                f"project_not_empty: project {name!r} still has live tasks"
            )
            return
        self._push_undo(
            f"delete project {name!r}",
            undo=lambda: self._restore_project(project_id),
            redo=lambda: self._delete_project(project_id),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _delete_project(self, project_id: UUID) -> None:
        with deps.delete_project_use_case() as use_case:
            use_case.execute(project_id)

    def _restore_project(self, project_id: UUID) -> None:
        with deps.restore_project_use_case() as use_case:
            use_case.execute(project_id)

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
