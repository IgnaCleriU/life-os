from __future__ import annotations

from datetime import date
from uuid import UUID

from lifeos.adapters.shared.error_codes import DOMAIN_ERROR_CODES
from lifeos.adapters.shared.quick_add import parse_quick_add
from lifeos.adapters.tui import deps
from lifeos.adapters.tui.keymap import KeymapEntry, Scope
from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.undo import UndoableWrite
from lifeos.domain import (
    Priority,
    Project,
    ProjectStatus,
    Task,
    TaskStatus,
)

_PRIORITY_OPTIONS = [Priority.LOW.value, Priority.MEDIUM.value, Priority.HIGH.value]

_FAILED = object()
"""Sentinel returned by `_try_call` on a caught domain error, distinct from
any real use-case return value (including `None`)."""

_STATUS_GLYPHS = {
    TaskStatus.TODO: "·",
    TaskStatus.DOING: "◐",
    TaskStatus.DONE: "✓",
}

_OPEN_TASK_STATUSES = [TaskStatus.TODO, TaskStatus.DOING]

_PROJECT_FILTER_OPTIONS = ["active", "completed", "archived", "all"]
_TASK_FILTER_OPTIONS = ["todo", "doing", "done", "all"]
_SORT_ORDERS = ["created", "due", "priority"]
_PRIORITY_SORT_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


class ProjectsTasksModule:
    """The real Projects/Tasks TUI module, replacing Step 12's stub. Calls
    the same use cases REST, MCP, and the CLI already expose, wired through
    `adapters/tui/deps.py`. Returns domain entities as `PaneItem.payload`,
    per ADR 0008: the shell never inspects them.
    """

    _FAILED = _FAILED

    def __init__(self) -> None:
        self.shell: object | None = None
        self._project_status_filter: list[ProjectStatus] | None = None
        self._task_status_filter: list[TaskStatus] | None = None
        self._task_sort_order: str = "created"

    def _try_call(self, action, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN201
        """Runs `action`; on a domain exception mapped in DOMAIN_ERROR_CODES,
        surfaces it via `shell.show_error()` instead of letting it crash the
        app, and returns the `_FAILED` sentinel. Returns `action`'s own
        result otherwise - a general safety net alongside the client-side
        blank/whitespace-only guards on text-input commit handlers, for
        whatever domain error those guards don't anticipate (e.g. an entity
        deleted out from under a still-open prompt)."""
        try:
            return action(*args, **kwargs)
        except tuple(DOMAIN_ERROR_CODES) as exc:
            code = DOMAIN_ERROR_CODES.get(type(exc), "domain_error")
            self.shell.show_error(f"{code}: {exc}")  # type: ignore[attr-defined]
            return self._FAILED

    def _guarded(self, fn):  # noqa: ANN001, ANN201
        """Wraps a keymap action or an on_commit/on_yes/on_select callback
        so a late domain error (e.g. the target deleted out from under a
        still-open prompt) surfaces via `_try_call` instead of crashing the
        app. Used both directly on keymap entries' actions (synchronous
        mutations) and on the deferred callbacks `_start_*` methods hand to
        `shell.prompt_insert`/`confirm`/`pick_option` (the mutation doesn't
        happen until the callback fires later)."""

        def _wrapped(*args, **kwargs):  # noqa: ANN002, ANN003
            self._try_call(fn, *args, **kwargs)

        return _wrapped

    # --- TuiModule contract ---------------------------------------------------

    def context_pane(self) -> PaneContents:
        with deps.list_projects_use_case() as use_case:
            projects = use_case.execute(statuses=self._project_status_filter)
        items = [self._project_to_item(project) for project in projects]
        return PaneContents(title="PROJECTS", items=items)

    def collection_pane(self, context_item: PaneItem | None) -> PaneContents:
        if context_item is None:
            return PaneContents(title="TASKS", items=[])
        project: Project = context_item.payload
        with deps.list_tasks_use_case() as use_case:
            tasks = use_case.execute(project.id, statuses=self._task_status_filter)
        tasks = self._sort_tasks(tasks)
        items = [self._task_to_item(task) for task in tasks]
        return PaneContents(title=f"TASKS - {project.name}", items=items)

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        if self._task_sort_order == "due":
            return sorted(
                tasks, key=lambda t: (t.due_date is None, t.due_date or date.max)
            )
        if self._task_sort_order == "priority":
            return sorted(tasks, key=lambda t: _PRIORITY_SORT_ORDER[t.priority])
        return tasks

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
        g = self._guarded
        return [
            KeymapEntry(
                Scope.CONTEXT, "a", "create a project", g(self._start_create_project)
            ),
            KeymapEntry(
                Scope.CONTEXT, "e", "rename project", g(self._start_rename_project)
            ),
            KeymapEntry(
                Scope.CONTEXT, "c", "complete project", g(self._complete_project)
            ),
            KeymapEntry(
                Scope.CONTEXT,
                "A",
                "archive/activate project",
                g(self._toggle_archive_project),
            ),
            KeymapEntry(
                Scope.CONTEXT, "K", "move project up", g(self._move_project_up)
            ),
            KeymapEntry(
                Scope.CONTEXT, "J", "move project down", g(self._move_project_down)
            ),
            KeymapEntry(
                Scope.CONTEXT, "dd", "delete project", g(self._start_delete_project)
            ),
            KeymapEntry(
                Scope.CONTEXT,
                "f",
                "filter by status",
                g(self._start_filter_projects),
            ),
            KeymapEntry(
                Scope.COLLECTION,
                "a",
                "add a task (quick-add)",
                g(self._start_add_task),
            ),
            KeymapEntry(
                Scope.COLLECTION,
                "o",
                "add a task (quick-add)",
                g(self._start_add_task),
            ),
            KeymapEntry(
                Scope.COLLECTION, "space", "cycle status", g(self._cycle_status)
            ),
            KeymapEntry(Scope.COLLECTION, "c", "complete task", g(self._complete_task)),
            KeymapEntry(
                Scope.COLLECTION, "s", "start task", g(self._start_task_status)
            ),
            KeymapEntry(Scope.COLLECTION, "r", "reopen task", g(self._reopen_task)),
            KeymapEntry(
                Scope.COLLECTION, "e", "rename task", g(self._start_rename_task)
            ),
            KeymapEntry(
                Scope.COLLECTION,
                "E",
                "edit description in $EDITOR",
                g(self._edit_description),
            ),
            KeymapEntry(
                Scope.COLLECTION, "at", "set due date", g(self._start_set_due_date)
            ),
            KeymapEntry(
                Scope.COLLECTION, "p", "priority picker", g(self._start_set_priority)
            ),
            KeymapEntry(
                Scope.COLLECTION,
                "m",
                "move to another project",
                g(self._start_move_task),
            ),
            KeymapEntry(
                Scope.COLLECTION, "dd", "delete task", g(self._start_delete_task)
            ),
            KeymapEntry(
                Scope.COLLECTION, "f", "filter menu", g(self._start_filter_tasks)
            ),
            KeymapEntry(
                Scope.COLLECTION, "S", "cycle sort order", g(self._cycle_sort_order)
            ),
            KeymapEntry(
                Scope.COLLECTION, "x", "toggle selection", g(self._toggle_select)
            ),
            KeymapEntry(
                Scope.COLLECTION, "v", "toggle selection", g(self._toggle_select)
            ),
            KeymapEntry(
                Scope.COLLECTION,
                "y",
                "copy task as markdown",
                g(self._copy_as_markdown),
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
            placeholder="new project name",
            on_commit=self._guarded(self._commit_create_project),
        )

    def _commit_create_project(self, name: str) -> None:
        if not name.strip():
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
            on_commit=self._guarded(
                lambda text: self._commit_rename_project(
                    project.id, project.name, text
                )
            ),
        )

    def _commit_rename_project(
        self, project_id: UUID, old_name: str, new_name: str
    ) -> None:
        if not new_name.strip():
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

    def _move_project_up(self) -> None:
        shell = self.shell
        assert shell is not None
        item = shell.current_context_item  # type: ignore[attr-defined]
        if item is None:
            return
        project: Project = item.payload
        moved = self._reorder_project(project.id, "up")
        if moved.position != project.position:
            self._push_undo(
                "move project up",
                undo=lambda: self._reorder_project(project.id, "down"),
                redo=lambda: self._reorder_project(project.id, "up"),
            )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _move_project_down(self) -> None:
        shell = self.shell
        assert shell is not None
        item = shell.current_context_item  # type: ignore[attr-defined]
        if item is None:
            return
        project: Project = item.payload
        moved = self._reorder_project(project.id, "down")
        if moved.position != project.position:
            self._push_undo(
                "move project down",
                undo=lambda: self._reorder_project(project.id, "up"),
                redo=lambda: self._reorder_project(project.id, "down"),
            )
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _reorder_project(self, project_id: UUID, direction: str) -> Project:
        """A swap is its own inverse, so undo/redo above just call this
        again with the opposite direction on the same id - no need to
        snapshot/restore raw position values. Callers compare the returned
        project's `position` against the pre-call value to detect a
        boundary no-op (nothing to undo)."""
        if direction == "up":
            with deps.reorder_project_up_use_case() as use_case:
                return use_case.execute(project_id)
        else:
            with deps.reorder_project_down_use_case() as use_case:
                return use_case.execute(project_id)

    def _start_delete_project(self) -> None:
        shell = self.shell
        assert shell is not None
        item = shell.current_context_item  # type: ignore[attr-defined]
        if item is None:
            return
        project: Project = item.payload
        shell.confirm(  # type: ignore[attr-defined]
            f"delete project {project.name!r}?",
            on_yes=self._guarded(
                lambda: self._commit_delete_project(project.id, project.name)
            ),
        )

    def _commit_delete_project(self, project_id: UUID, name: str) -> None:
        self._delete_project(project_id)
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

    def _start_filter_projects(self) -> None:
        shell = self.shell
        assert shell is not None
        shell.pick_option(  # type: ignore[attr-defined]
            "filter by status",
            _PROJECT_FILTER_OPTIONS,
            on_select=self._guarded(self._set_project_filter),
        )

    def _set_project_filter(self, choice: str) -> None:
        self._project_status_filter = (
            None if choice == "all" else [ProjectStatus(choice)]
        )
        self.shell.action_reload()  # type: ignore[attr-defined]

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
            on_commit=self._guarded(
                lambda text: self._commit_add_task(default_project, text)
            ),
        )

    def _commit_add_task(self, default_project: Project, text: str) -> None:
        parsed = parse_quick_add(text)
        if not parsed.title:
            return
        if parsed.project_name is not None:
            matches = self._find_projects_by_name(parsed.project_name)
            if not matches:
                self.shell.show_error(  # type: ignore[attr-defined]
                    f"project_name_not_found: no project named {parsed.project_name!r}"
                )
                return
            if len(matches) > 1:
                self._show_ambiguous_project_error(parsed.project_name, matches)
                return
            target = matches[0]
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

    def _find_projects_by_name(self, name: str) -> list[Project]:
        """All active-or-not projects whose name case-folds to `name`.

        Project names have no uniqueness constraint (unlike the CLI's
        equivalent resolver in `cli/capture.py`, this doesn't live in
        `adapters/shared/` yet - see that module's docstring), so callers
        must handle 0, 1, and >1 matches distinctly rather than picking a
        match silently.
        """
        needle = name.strip().casefold()
        with deps.list_projects_use_case() as use_case:
            projects = use_case.execute()
        return [p for p in projects if p.name.casefold() == needle]

    def _show_ambiguous_project_error(self, name: str, matches: list[Project]) -> None:
        self.shell.show_error(  # type: ignore[attr-defined]
            f"ambiguous_project_name: {len(matches)} projects named {name!r} - "
            "rename one to disambiguate"
        )

    def _current_task(self) -> Task | None:
        shell = self.shell
        assert shell is not None
        item = shell.current_collection_item  # type: ignore[attr-defined]
        return None if item is None else item.payload

    def _selected_or_current_task_ids(self) -> list[UUID]:
        """The bulk-selected task ids if any are selected (ADR's "toggle
        selection / bulk mode"), else just the currently-highlighted one."""
        shell = self.shell
        assert shell is not None
        selected = shell.selected_ids  # type: ignore[attr-defined]
        if selected:
            return [UUID(item_id) for item_id in selected]
        task = self._current_task()
        return [] if task is None else [task.id]

    def _clear_selection(self) -> None:
        self.shell.selected_ids.clear()  # type: ignore[attr-defined]

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
        task_ids = self._selected_or_current_task_ids()
        if not task_ids:
            return
        if len(task_ids) == 1:
            task = self._get_task(task_ids[0])
            self._change_task_status(
                task.id, task.status, TaskStatus.DONE, "complete task"
            )
            return
        prior_statuses = {
            task_id: self._get_task(task_id).status for task_id in task_ids
        }
        for task_id in task_ids:
            self._set_task_status(task_id, TaskStatus.DONE)
        self._push_undo(
            f"complete {len(task_ids)} tasks",
            undo=lambda: [
                self._set_task_status(task_id, prior_statuses[task_id])
                for task_id in task_ids
            ],
            redo=lambda: [
                self._set_task_status(task_id, TaskStatus.DONE) for task_id in task_ids
            ],
        )
        self._clear_selection()
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _get_task(self, task_id: UUID) -> Task:
        with deps.get_task_use_case() as use_case:
            return use_case.execute(task_id)

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
            on_commit=self._guarded(
                lambda text: self._commit_rename_task(task.id, task.title, text)
            ),
        )

    def _commit_rename_task(
        self, task_id: UUID, old_title: str, new_title: str
    ) -> None:
        if not new_title.strip():
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
            on_commit=self._guarded(
                lambda text: self._commit_set_due_date(task.id, task.due_date, text)
            ),
        )

    def _commit_set_due_date(self, task_id: UUID, old_due_date, text: str) -> None:  # noqa: ANN001
        if not text:
            return
        new_due_date = parse_quick_add(f"@{text.removeprefix('@')}").due_date
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
            on_select=self._guarded(
                lambda choice: self._commit_set_priority(
                    task.id, task.priority, choice
                )
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
            on_select=self._guarded(
                lambda choice: self._commit_move_task(
                    task.id, task.project_id, choice
                )
            ),
        )

    def _commit_move_task(
        self, task_id: UUID, old_project_id: UUID, choice: str
    ) -> None:
        matches = self._find_projects_by_name(choice)
        if not matches:
            return
        if len(matches) > 1:
            self._show_ambiguous_project_error(choice, matches)
            return
        target = matches[0]
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
        task_ids = self._selected_or_current_task_ids()
        if not task_ids:
            return
        if len(task_ids) == 1:
            title = self._get_task(task_ids[0]).title
            message = f"delete task {title!r}?"
        else:
            message = f"delete {len(task_ids)} tasks?"
        shell.confirm(  # type: ignore[attr-defined]
            message,
            on_yes=self._guarded(lambda: self._commit_delete_tasks(task_ids)),
        )

    def _commit_delete_tasks(self, task_ids: list[UUID]) -> None:
        for task_id in task_ids:
            self._delete_task(task_id)
        description = (
            "delete task" if len(task_ids) == 1 else f"delete {len(task_ids)} tasks"
        )
        self._push_undo(
            description,
            undo=lambda: [self._restore_task(task_id) for task_id in task_ids],
            redo=lambda: [self._delete_task(task_id) for task_id in task_ids],
        )
        self._clear_selection()
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _delete_task(self, task_id: UUID) -> None:
        with deps.delete_task_use_case() as use_case:
            use_case.execute(task_id)

    def _restore_task(self, task_id: UUID) -> None:
        with deps.restore_task_use_case() as use_case:
            use_case.execute(task_id)

    def _start_filter_tasks(self) -> None:
        shell = self.shell
        assert shell is not None
        shell.pick_option(  # type: ignore[attr-defined]
            "filter tasks by status",
            _TASK_FILTER_OPTIONS,
            on_select=self._guarded(self._set_task_filter),
        )

    def _set_task_filter(self, choice: str) -> None:
        self._task_status_filter = None if choice == "all" else [TaskStatus(choice)]
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _cycle_sort_order(self) -> None:
        index = _SORT_ORDERS.index(self._task_sort_order)
        self._task_sort_order = _SORT_ORDERS[(index + 1) % len(_SORT_ORDERS)]
        self.shell.action_reload()  # type: ignore[attr-defined]

    def _toggle_select(self) -> None:
        shell = self.shell
        assert shell is not None
        shell.enter_select_mode()  # type: ignore[attr-defined]
        item = shell.current_collection_item  # type: ignore[attr-defined]
        if item is not None:
            shell.toggle_selection(item.id)  # type: ignore[attr-defined]

    def _copy_as_markdown(self) -> None:
        shell = self.shell
        assert shell is not None
        task = self._current_task()
        if task is None:
            return
        checkbox = "x" if task.status is TaskStatus.DONE else " "
        line = f"- [{checkbox}] {task.title}"
        if task.due_date is not None:
            line += f" (due {task.due_date.isoformat()})"
        shell.copy_to_clipboard(line)  # type: ignore[attr-defined]

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
