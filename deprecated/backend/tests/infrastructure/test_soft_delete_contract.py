"""Guarda de contrato: la exclusión de borrados vive en los repositorios.

La ADR 0008 avisa que el costo del borrado lógico es "una condición de filtro en
cada lectura", y que olvidarla en un método nuevo hace aparecer registros
borrados. Esa clase de bug es silenciosa: nada falla, simplemente reaparece algo
que el usuario borró.

Estos tests no verifican comportamiento sino *cobertura*: si alguien agrega un
método de lectura a un repositorio, fallan hasta que lo agregue acá con su caso
de borrado escrito. La lista blanca es deliberadamente molesta de actualizar.
"""

from __future__ import annotations

import pytest

from lifeos.domain import Project, Task
from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
    SQLiteProjectRepository,
)
from lifeos.infrastructure.db.repositories.sqlite_task_repository import (
    SQLiteTaskRepository,
)

_EXPECTED_PUBLIC_METHODS = {"add", "get", "list", "update"}


@pytest.mark.parametrize(
    "repo_cls", [SQLiteTaskRepository, SQLiteProjectRepository]
)
def test_repository_surface_is_fully_audited_for_soft_delete(repo_cls):
    """Si esto falla, hay un método nuevo sin test de borrado lógico."""
    public = {name for name in vars(repo_cls) if not name.startswith("_")}

    assert public == _EXPECTED_PUBLIC_METHODS, (
        f"{repo_cls.__name__} cambió su superficie pública. Antes de tocar esta "
        "lista, escribí el test que verifica que el método nuevo excluye los "
        "registros borrados."
    )


def test_every_task_read_path_hides_deleted_rows(session):
    """Barrido explícito de todas las lecturas de `SQLiteTaskRepository`."""
    project = Project.create(name="Proyecto")
    SQLiteProjectRepository(session).add(project)
    repo = SQLiteTaskRepository(session)
    task = Task.create(project_id=project.id, title="Tarea")
    repo.add(task)
    task.delete()
    repo.update(task)

    assert repo.get(task.id) is None
    assert repo.list() == []
    assert repo.list(project_id=project.id) == []
    assert repo.list(statuses=[task.status]) == []
    assert repo.list(text="Tarea") == []


def test_every_project_read_path_hides_deleted_rows(session):
    """Barrido explícito de todas las lecturas de `SQLiteProjectRepository`."""
    repo = SQLiteProjectRepository(session)
    project = Project.create(name="Proyecto")
    repo.add(project)
    project.delete()
    repo.update(project)

    assert repo.get(project.id) is None
    assert repo.list() == []
    assert repo.list(statuses=[project.status]) == []
    assert repo.list(text="Proyecto") == []
