"""Serialización de entidades de dominio para el CLI.

`project_dict`/`task_dict` son una copia deliberada de `_project_dict`/
`_task_dict` de `adapters/mcp/tools.py`: mismo campo a campo, para que
`lifeos --json ...` produzca el mismo shape que las tools MCP. Se copian en
vez de importarse porque cada adaptador es dueño de su propia traducción de
protocolo (ver docstring de `mcp/tools.py`); `mcp/tools.py` no se modifica
desde acá.

Además se agregan renderers de texto plano (`format_project`/`format_task`
y sus variantes de lista) para el modo por defecto (sin `--json`): una
línea por entidad, sin colores, pensada para ser fácil de parsear en
scripts.
"""

from __future__ import annotations

from typing import Any

from lifeos.domain import Project, Task

# --- JSON (mismo shape que adapters/mcp/tools.py) -----------------------


def project_dict(project: Project) -> dict[str, Any]:
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "created_at": project.created_at.isoformat(),
    }


def task_dict(task: Task) -> dict[str, Any]:
    return {
        "id": str(task.id),
        "project_id": str(task.project_id),
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat(),
    }


# --- Texto plano ---------------------------------------------------------


def format_project(project: Project) -> str:
    """Una línea por proyecto: id, status, nombre."""
    return f"{project.id}  {project.status.value:<10}  {project.name}"


def format_task(task: Task) -> str:
    """Una línea por tarea: id, status, priority, due date, título."""
    due = task.due_date.isoformat() if task.due_date else "-"
    return (
        f"{task.id}  {task.status.value:<5}  {task.priority.value:<6}  "
        f"{due:<10}  {task.title}"
    )


def format_projects(projects: list[Project]) -> str:
    """Un `format_project` por línea, en el orden recibido."""
    return "\n".join(format_project(project) for project in projects)


def format_tasks(tasks: list[Task]) -> str:
    """Un `format_task` por línea, en el orden recibido."""
    return "\n".join(format_task(task) for task in tasks)
