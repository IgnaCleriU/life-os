"""Endpoint de revisión para clientes con datos en vivo (ADR 0009).

El overlay de Quickshell lo sondea cada ~1 s: es una consulta barata que no
toca las tablas, y solo cuando el valor cambia vuelve a pedir proyectos y
tareas.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from lifeos.adapters.rest.deps import get_get_revision_use_case
from lifeos.adapters.rest.schemas import RevisionResponse
from lifeos.application.use_cases.get_revision import GetRevision

router = APIRouter(tags=["sync"])


@router.get("/revision", response_model=RevisionResponse)
def get_revision(
    use_case: Annotated[GetRevision, Depends(get_get_revision_use_case)],
) -> RevisionResponse:
    return RevisionResponse(revision=use_case.execute())
