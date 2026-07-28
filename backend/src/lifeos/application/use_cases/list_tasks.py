"""Caso de uso: listar Task, con filtros opcionales.

Consulta las tareas a través del `TaskRepository` sin aplicar reglas de negocio
adicionales. Todos los filtros son opcionales y se combinan con AND; sin
ninguno, devuelve todas las tareas vivas de todos los proyectos —lo que
alimenta las vistas de vencidas y la búsqueda de la paleta en la TUI.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from lifeos.application.ports import TaskRepository
from lifeos.domain import Task, TaskStatus


class ListTasks:
    """Lista tareas, opcionalmente filtradas."""

    def __init__(self, task_repo: TaskRepository) -> None:
        self._task_repo = task_repo

    def execute(
        self,
        project_id: UUID | None = None,
        *,
        statuses: Sequence[TaskStatus] | None = None,
        due_before: date | None = None,
        text: str | None = None,
    ) -> list[Task]:
        """Devuelve las tareas que cumplen los filtros dados.

        `project_id` queda posicional y primero para no romper a quien ya
        llamaba `execute(project_id)`; en `None` significa "de todos los
        proyectos".
        """
        return self._task_repo.list(
            project_id=project_id,
            statuses=statuses,
            due_before=due_before,
            text=text,
        )
