"""Tests del caso de uso ListProjects (con repositorio fake, sin mocks)."""

from lifeos.application.use_cases.create_project import CreateProject
from lifeos.application.use_cases.list_projects import ListProjects
from lifeos.domain import Project, ProjectStatus

from .fakes import InMemoryProjectRepository


def test_list_empty_repo_returns_empty_list():
    repo = InMemoryProjectRepository()
    use_case = ListProjects(repo)

    assert use_case.execute() == []


def test_list_returns_all_created_projects():
    repo = InMemoryProjectRepository()
    create = CreateProject(repo)
    list_projects = ListProjects(repo)

    created = [create.execute(name=f"Proyecto {i}") for i in range(3)]

    result = list_projects.execute()

    assert len(result) == 3
    assert {p.id for p in result} == {p.id for p in created}


def test_list_filters_by_status():
    repo = InMemoryProjectRepository()
    activo = Project.create(name="Activo")
    archivado = Project.create(name="Archivado")
    archivado.archive()
    repo.add(activo)
    repo.add(archivado)

    result = ListProjects(repo).execute(statuses=[ProjectStatus.ARCHIVED])

    assert {p.id for p in result} == {archivado.id}


def test_list_filters_by_text_case_insensitively():
    repo = InMemoryProjectRepository()
    casa = Project.create(name="Casa de campo")
    finanzas = Project.create(name="Finanzas")
    repo.add(casa)
    repo.add(finanzas)

    result = ListProjects(repo).execute(text="CASA")

    assert {p.id for p in result} == {casa.id}
