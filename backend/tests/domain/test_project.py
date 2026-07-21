"""Tests unitarios de la entidad Project (Python puro, sin DB ni mocks)."""

from datetime import datetime
from uuid import UUID

import pytest

from lifeos.domain import DomainValidationError, Project, ProjectStatus


def test_create_generates_id_and_timestamp():
    project = Project.create(name="Life OS")

    assert isinstance(project.id, UUID)
    assert isinstance(project.created_at, datetime)
    assert project.created_at.tzinfo is not None
    assert project.status is ProjectStatus.ACTIVE
    assert project.name == "Life OS"
    assert project.description is None


def test_create_normalizes_name():
    project = Project.create(name="  Life OS  ")

    assert project.name == "Life OS"


@pytest.mark.parametrize("invalid_name", ["", "   "])
def test_create_with_empty_name_raises(invalid_name):
    with pytest.raises(DomainValidationError):
        Project.create(name=invalid_name)


def test_rename_changes_name():
    project = Project.create(name="Viejo")

    project.rename("Nuevo")

    assert project.name == "Nuevo"


def test_rename_with_empty_name_raises():
    project = Project.create(name="Life OS")

    with pytest.raises(DomainValidationError):
        project.rename("   ")


def test_complete_sets_completed_status():
    project = Project.create(name="Life OS")

    project.complete()

    assert project.status is ProjectStatus.COMPLETED


def test_free_transitions_between_states():
    project = Project.create(name="Life OS")

    project.complete()
    assert project.status is ProjectStatus.COMPLETED

    # desde completado se puede reactivar
    project.activate()
    assert project.status is ProjectStatus.ACTIVE

    project.archive()
    assert project.status is ProjectStatus.ARCHIVED

    # desde archivado se puede volver a completar
    project.complete()
    assert project.status is ProjectStatus.COMPLETED

    # y volver a activo
    project.activate()
    assert project.status is ProjectStatus.ACTIVE
