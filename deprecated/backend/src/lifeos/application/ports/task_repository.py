"""Puerto de persistencia de Task.

Interfaz abstracta (`Protocol`) que define cómo los casos de uso persisten y
consultan `Task`, sin atarse a SQLite ni a ningún motor concreto. La
implementación real vive en `infrastructure/`; los tests usan un fake en
memoria.

Las tareas borradas (`deleted_at` no nulo) quedan fuera de todas las lecturas
salvo que se pida `include_deleted`. Ese filtro es responsabilidad de la
implementación, no de quien llama: si viviera en los casos de uso, un método
nuevo del repositorio podría olvidarlo y filtrar registros borrados.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol
from uuid import UUID

from lifeos.domain import Task, TaskStatus


class TaskRepository(Protocol):
    """Contrato de persistencia para la entidad `Task`."""

    def add(self, task: Task) -> None:
        """Persiste una tarea nueva."""
        ...

    def get(self, task_id: UUID, *, include_deleted: bool = False) -> Task | None:
        """Devuelve la tarea con ese id, o `None` si no existe.

        `include_deleted` existe sólo para que `RestoreTask` pueda alcanzar una
        tarea borrada; ningún listado la expone.
        """
        ...

    def list(
        self,
        *,
        project_id: UUID | None = None,
        statuses: Sequence[TaskStatus] | None = None,
        due_before: date | None = None,
        text: str | None = None,
    ) -> list[Task]:
        """Devuelve las tareas vivas que cumplen todos los filtros dados.

        Un filtro en `None` no restringe. `due_before` es inclusivo y descarta
        las tareas sin fecha; `text` busca subcadena en el título, sin
        distinguir mayúsculas.
        """
        ...

    def update(self, task: Task) -> None:
        """Persiste los cambios de una tarea existente."""
        ...
