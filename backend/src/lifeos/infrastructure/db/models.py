"""Modelos SQLModel (tablas ProjectModel, TaskModel) que mapean las entidades
de dominio a SQLite.

Declaraciones de esquema puras: sin comportamiento ni imports de
`lifeos.domain`. Los UUID y los enums se guardan como columnas `str`; la
conversión hacia/desde los tipos de dominio vive en
`infrastructure/db/repositories/`, dejando este módulo como un artefacto
aburrido que sólo describe filas de SQLite.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlmodel import Field, SQLModel


class ProjectModel(SQLModel, table=True):
    """Forma de fila SQLite para `Project`."""

    __tablename__ = "projects"

    id: str = Field(primary_key=True)
    name: str
    description: str | None = None
    status: str
    created_at: datetime


class TaskModel(SQLModel, table=True):
    """Forma de fila SQLite para `Task`."""

    __tablename__ = "tasks"

    id: str = Field(primary_key=True)
    project_id: str = Field(foreign_key="projects.id", index=True)
    title: str
    description: str | None = None
    status: str
    priority: str
    due_date: date | None = None
    created_at: datetime
