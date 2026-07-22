"""Tests del caso de uso ListProjects (con repositorio fake, sin mocks)."""

from lifeos.application.use_cases.create_project import CreateProject
from lifeos.application.use_cases.list_projects import ListProjects

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
