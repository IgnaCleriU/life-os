from __future__ import annotations

from datetime import date
from uuid import UUID

from lifeos.adapters.shared.quick_add import parse_quick_add
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

_PRIORITY_OPTIONS = [Priority.LOW.value, Priority.MEDIUM.value, Priority.HIGH.value]

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
            KeymapEntry(
                Scope.COLLECTION, "a", "add a task (quick-add)", self._start_add_task
            ),
            KeymapEntry(
                Scope.COLLECTION, "o", "add a task (quick-add)", self._start_add_task
            ),
            KeymapEntry(Scope.COLLECTION, "space", "cycle status", self._cycle_status),
            KeymapEntry(Scope.COLLECTION, "c", "complete task", self._complete_task),
            KeymapEntry(Scope.COLLECTION, "s", "start task", self._start_task_status),
            KeymapEntry(Scope.COLLECTION, "r", "reopen task", self._reopen_task),
            KeymapEntry(Scope.COLLECTION, "e", "rename task", self._start_rename_task),
            KeymapEntry(
                Scope.COLLECTION,
                "E",
                "edit description in $EDITOR",
                self._edit_description,
            ),
            KeymapEntry(
                Scope.COLLECTION, "at", "set due date", self._start_set_due_date
            ),
            KeymapEntry(
                Scope.COLLECTION, "p", "priority picker", self._start_set_priority
            ),
            KeymapEntry(
                Scope.COLLECTION,
                "m",
                "move to another project",
                self._start_move_task,
            ),
            KeymapEntry(
                Scope.COLLECTION, "dd", "delete task", self._start_delete_task
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

    # --- tasks-pane write actions -------------------------------------------

    def _start_add_task(self) -> None:
        shell = self.shell
        assert shell is not None
        context_item = shell.current_context_item  # type: ignore[attr-defined]
        if context_item is None:
            return
        default_project: Project = context_item.payload
        shell.prompt_insert(  # type: ignore[attr-defined]
            placeholder="quick-add: buy milk !high @sat #casa",
            on_commit=lambda text: self._commit_add_task(default_project, text),
        )

    def _commit_add_task(self, default_project: Project, text: str) -> None:
        parsed = parse_quick_add(text)
        if not parsed.title:
            return
        if parsed.project_name is not None:
            target = self._find_project_by_name(parsed.project_name)
            if target is None:
                self.shell.show_error(  # type: ignore[attr-defined]
                    f"project_name_not_found: no project named {parsed.project_name!r}"
                )
                return
        else:
            target = default_project
        with deps.create_task_use_case() as use_case:
            task = use_case.execute(
                target.id,
                parsed.title,
                priority=parsed.priority,
                due_date=parsed.due_date,
            )
        self._push_undo(
            f"add task {parsed.title!r}",
            undo=lambda: self._delete_task(task.id),
            redo=lambda: self._restore_task(task.id),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _find_project_by_name(self, name: str) -> Project | None:
        needle = name.strip().casefold()
        with deps.list_projects_use_case() as use_case:
            projects = use_case.execute()
        return next((p for p in projects if p.name.casefold() == needle), None)

    def _current_task(self) -> Task | None:
        shell = self.shell
        assert shell is not None
        item = shell.current_collection_item  # type: ignore[attr-defined]
        return None if item is None else item.payload

    def _cycle_status(self) -> None:
        task = self._current_task()
        if task is None:
            return
        next_status = {
            TaskStatus.TODO: TaskStatus.DOING,
            TaskStatus.DOING: TaskStatus.DONE,
            TaskStatus.DONE: TaskStatus.TODO,
        }[task.status]
        self._change_task_status(task.id, task.status, next_status, "cycle status")

    def _complete_task(self) -> None:
        task = self._current_task()
        if task is None:
            return
        self._change_task_status(task.id, task.status, TaskStatus.DONE, "complete task")

    def _start_task_status(self) -> None:
        task = self._current_task()
        if task is None:
            return
        self._change_task_status(task.id, task.status, TaskStatus.DOING, "start task")

    def _reopen_task(self) -> None:
        task = self._current_task()
        if task is None:
            return
        self._change_task_status(task.id, task.status, TaskStatus.TODO, "reopen task")

    def _change_task_status(
        self,
        task_id: UUID,
        prior_status: TaskStatus,
        new_status: TaskStatus,
        description: str,
    ) -> None:
        self._set_task_status(task_id, new_status)
        self._push_undo(
            description,
            undo=lambda: self._set_task_status(task_id, prior_status),
            redo=lambda: self._set_task_status(task_id, new_status),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _set_task_status(self, task_id: UUID, status: TaskStatus) -> None:
        if status is TaskStatus.DONE:
            with deps.complete_task_use_case() as use_case:
                use_case.execute(task_id)
        elif status is TaskStatus.DOING:
            with deps.start_task_use_case() as use_case:
                use_case.execute(task_id)
        else:
            with deps.reopen_task_use_case() as use_case:
                use_case.execute(task_id)

    def _start_rename_task(self) -> None:
        shell = self.shell
        assert shell is not None
        task = self._current_task()
        if task is None:
            return
        shell.prompt_insert(  # type: ignore[attr-defined]
            placeholder=task.title,
            on_commit=lambda text: self._commit_rename_task(task.id, task.title, text),
        )

    def _commit_rename_task(
        self, task_id: UUID, old_title: str, new_title: str
    ) -> None:
        if not new_title:
            return
        self._rename_task(task_id, new_title)
        self._push_undo(
            f"rename task to {new_title!r}",
            undo=lambda: self._rename_task(task_id, old_title),
            redo=lambda: self._rename_task(task_id, new_title),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _rename_task(self, task_id: UUID, title: str) -> None:
        with deps.update_task_use_case() as use_case:
            use_case.execute(task_id, title=title)

    def _edit_description(self) -> None:
        shell = self.shell
        assert shell is not None
        task = self._current_task()
        if task is None:
            return
        new_description = shell.edit_in_external_editor(task.description or "")  # type: ignore[attr-defined]
        old_description = task.description
        self._set_description(task.id, new_description)
        self._push_undo(
            "edit description",
            undo=lambda: self._set_description(task.id, old_description),
            redo=lambda: self._set_description(task.id, new_description),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _set_description(self, task_id: UUID, description: str | None) -> None:
        with deps.update_task_use_case() as use_case:
            use_case.execute(task_id, description=description)

    def _start_set_due_date(self) -> None:
        shell = self.shell
        assert shell is not None
        task = self._current_task()
        if task is None:
            return
        shell.prompt_insert(  # type: ignore[attr-defined]
            placeholder="sat, tomorrow, 2026-08-03",
            on_commit=lambda text: self._commit_set_due_date(
                task.id, task.due_date, text
            ),
        )

    def _commit_set_due_date(self, task_id: UUID, old_due_date, text: str) -> None:  # noqa: ANN001
        if not text:
            return
        new_due_date = parse_quick_add(f"@{text}").due_date
        if new_due_date is None:
            self.shell.show_error(f"invalid date: {text!r}")  # type: ignore[attr-defined]
            return
        self._set_due_date(task_id, new_due_date)
        self._push_undo(
            f"set due date to {new_due_date.isoformat()}",
            undo=lambda: self._set_due_date(task_id, old_due_date),
            redo=lambda: self._set_due_date(task_id, new_due_date),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _set_due_date(self, task_id: UUID, due_date) -> None:  # noqa: ANN001
        with deps.update_task_use_case() as use_case:
            use_case.execute(task_id, due_date=due_date)

    def _start_set_priority(self) -> None:
        shell = self.shell
        assert shell is not None
        task = self._current_task()
        if task is None:
            return
        shell.pick_option(  # type: ignore[attr-defined]
            "priority",
            _PRIORITY_OPTIONS,
            on_select=lambda choice: self._commit_set_priority(
                task.id, task.priority, choice
            ),
        )

    def _commit_set_priority(
        self, task_id: UUID, old_priority: Priority, choice: str
    ) -> None:
        new_priority = Priority(choice)
        self._set_priority(task_id, new_priority)
        self._push_undo(
            f"set priority to {choice}",
            undo=lambda: self._set_priority(task_id, old_priority),
            redo=lambda: self._set_priority(task_id, new_priority),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _set_priority(self, task_id: UUID, priority: Priority) -> None:
        with deps.update_task_use_case() as use_case:
            use_case.execute(task_id, priority=priority)

    def _start_move_task(self) -> None:
        shell = self.shell
        assert shell is not None
        task = self._current_task()
        if task is None:
            return
        with deps.list_projects_use_case() as use_case:
            project_names = [p.name for p in use_case.execute()]
        shell.pick_option(  # type: ignore[attr-defined]
            "move to project",
            project_names,
            on_select=lambda choice: self._commit_move_task(
                task.id, task.project_id, choice
            ),
        )

    def _commit_move_task(
        self, task_id: UUID, old_project_id: UUID, choice: str
    ) -> None:
        target = self._find_project_by_name(choice)
        if target is None:
            return
        self._move_task(task_id, target.id)
        self._push_undo(
            f"move task to {choice!r}",
            undo=lambda: self._move_task(task_id, old_project_id),
            redo=lambda: self._move_task(task_id, target.id),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _move_task(self, task_id: UUID, project_id: UUID) -> None:
        with deps.move_task_use_case() as use_case:
            use_case.execute(task_id, project_id)

    def _start_delete_task(self) -> None:
        shell = self.shell
        assert shell is not None
        task = self._current_task()
        if task is None:
            return
        shell.confirm(  # type: ignore[attr-defined]
            f"delete task {task.title!r}?",
            on_yes=lambda: self._commit_delete_task(task.id, task.title),
        )

    def _commit_delete_task(self, task_id: UUID, title: str) -> None:
        self._delete_task(task_id)
        self._push_undo(
            f"delete task {title!r}",
            undo=lambda: self._restore_task(task_id),
            redo=lambda: self._delete_task(task_id),
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _delete_task(self, task_id: UUID) -> None:
        with deps.delete_task_use_case() as use_case:
            use_case.execute(task_id)

    def _restore_task(self, task_id: UUID) -> None:
        with deps.restore_task_use_case() as use_case:
            use_case.execute(task_id)

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
