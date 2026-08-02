# 0002. `list_tasks` includes the project name

No paired ADR — this is a payload shape addition, not a structural or
costly-to-reverse decision. Two use cases already implement everything
needed (`ListTasks`, `ListProjects`); nothing in the domain, ports, or
application layer changes.

## Problem

`GET /tasks` (REST) and the `list_tasks` MCP tool both return tasks with
`project_id` (a UUID) but no project name. Any client that wants to show
tasks grouped or labeled by project — the most common way to display a
cross-project task list — has to: call `list_tasks`, call `list_projects`
separately, and join `project_id -> name` itself. That join belongs on the
server, not duplicated in every client (life-os tracker task `35e31be3`,
filed against this exact gap).

`GET /projects/{project_id}/tasks` (REST) and `list_tasks` called with a
`project_id` filter are not affected by this problem: the caller already
knows the project, since they supplied its id.

## Design

Scope the change to the cross-project listing path only:

- REST: `GET /tasks` (`adapters/rest/routers/tasks.py::list_tasks`).
- MCP: the `list_tasks` tool (`adapters/mcp/tools.py::list_tasks`).

`GET /projects/{project_id}/tasks` (`list_tasks_of_project`) keeps
returning plain `TaskResponse` — adding a redundant `project_name` there
would just echo back a value the caller passed in as `project_id`.

Both handlers already have a `ListTasks` use case available; both add one
call to the already-wired `ListProjects` use case (`get_list_projects_use_case`
on REST, `deps.list_projects_use_case()` on MCP — both exist today, used
elsewhere) and build a `{project_id: name}` dict once per request, not one
`GetProject` call per task. `ListProjects` excludes soft-deleted projects
by default (same as everywhere else in the app), so a task whose project
was deleted out from under it simply gets `project_name: null` — the
dict lookup misses, no error, no special-casing.

**Always included, no opt-in parameter.** The task's own notes proposed an
`include=project` flag to preserve the exact old shape when unneeded. Not
adopted: this is a single-user system with no external API consumers to
keep backward-compatible, the extra `ListProjects` call is one query at
single-user data volumes (same reasoning already applied elsewhere in this
codebase — see spec 0001's "Sorting and open-task counts" note), and an
opt-in flag adds a permanent branch in both handlers for a cost that isn't
real yet. Revisit only if a real perf or compatibility need shows up.

### REST

Add `TaskWithProjectResponse(TaskResponse)` in `adapters/rest/schemas.py`,
adding one field: `project_name: str | None`. Change `list_tasks`'s
`response_model` to `list[TaskWithProjectResponse]`, and in the handler,
build the id-to-name dict from `ListProjects.execute()` and construct each
response as `TaskWithProjectResponse(**TaskResponse.model_validate(task).model_dump(), project_name=names.get(task.project_id))`.

`list_tasks_of_project` and every single-task endpoint (`create_task`,
`get_task`, `update_task`, ...) are untouched — they keep returning
`TaskResponse`.

### MCP

`_task_dict()` stays exactly as it is — shared by `create_task`, `get_task`,
`update_task`, and others that shouldn't pay for a project lookup on every
single-task call. Only the `list_tasks` tool changes: after building
`tasks`, call `list_projects_use_case()`, build the same
`{project_id: name}` dict, and return
`[{**_task_dict(task), "project_name": names.get(task.project_id)} for task in tasks]`.

## Implementation tasks

| # | Task | Notes |
|---|---|---|
| 1 | `TaskWithProjectResponse` schema in `adapters/rest/schemas.py` | Subclasses `TaskResponse`, adds `project_name: str \| None`. |
| 2 | Update `GET /tasks` (`list_tasks` in `adapters/rest/routers/tasks.py`) | `response_model=list[TaskWithProjectResponse]`; build the id-to-name dict via the already-injected `ListProjects` dependency. |
| 3 | Update the MCP `list_tasks` tool in `adapters/mcp/tools.py` | Add the `ListProjects` call and the dict merge; `_task_dict()` itself is unchanged. |
| 4 | Tests for both | `backend/tests/adapters/rest/test_tasks_endpoints.py` and `backend/tests/adapters/mcp/test_tools.py` — assert `project_name` present and correct on `GET /tasks`/`list_tasks`, assert it's `null`/absent-equivalent for a task under a soft-deleted project, assert `list_tasks_of_project`/single-task endpoints are unchanged. |

## Open questions

None — the design is fully scoped. The `include=project`-flag alternative
from the original task notes is deliberately not adopted (see Design); if
a future need for the lean shape shows up, revisit then rather than
building the flag speculatively now.
