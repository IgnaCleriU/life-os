# CLAUDE.md

Guía para agentes de IA (ej. Claude Code) trabajando sobre este repo. Léela antes de empezar.

**Life OS** es un sistema operativo personal (notas, contraseñas, calendario, proyectos/tareas,
inventario) accesible por agentes de IA vía un servidor MCP propio.
**Estado actual:** Fase 0 / MVP de **Proyectos + Tareas** (ver roadmap en la guía de desarrollo).

## Documentación obligatoria

Antes de diseñar o implementar, tené en cuenta estos documentos:

- [ARCHITECTURE.md](ARCHITECTURE.md) — arquitectura hexagonal y regla de dependencia (estado actual).
- [docs/guia-de-desarrollo.md](docs/guia-de-desarrollo.md) — visión, stack, módulos y roadmap por fases.
- [docs/paso-a-paso-inicio.md](docs/paso-a-paso-inicio.md) — estructura de carpetas y pasos del MVP.
- [docs/flujo-agentico.md](docs/flujo-agentico.md) — cómo organizar el trabajo (orquestador + subagentes).
- [CONTRIBUTING.md](CONTRIBUTING.md) — convención de commits, commits atómicos y flujo de PRs.

## Reglas duras

- **Arquitectura hexagonal:** el dominio (`domain/`) es Python puro y **no importa** `fastapi`,
  `sqlmodel` ni `mcp`. Las dependencias apuntan hacia adentro
  (`adapters → application → domain`). Detalle en [ARCHITECTURE.md](ARCHITECTURE.md).
- **MCP no accede directo a la DB:** consume los mismos casos de uso que el adaptador REST.
- **Flujo agéntico:** entender → investigar (subagentes ∥) → planear (salvo tareas muy chicas) →
  implementar (∥ o serie según dependencias) → integrar y verificar. Ver
  [docs/flujo-agentico.md](docs/flujo-agentico.md).
- **Commits:** [Conventional Commits](CONTRIBUTING.md#convención-de-commits) y **atómicos** (varios
  commits por tarea, uno por cambio lógico).
- **PRs:** nunca commitear directo a `master`; trabajar en una rama `<tipo>/<descripción-corta>` y
  abrir PR contra `master`. Ver [CONTRIBUTING.md](CONTRIBUTING.md#flujo-de-pull-requests).

## Cómo correr y verificar

- **Tests:** `pytest` desde `backend/` (los tests de dominio y casos de uso corren sin DB, usando
  repositorios fake en memoria).
- **Validación de commits:** `pre-commit install --hook-type commit-msg` (una vez por clon); valida
  el formato del mensaje antes de crear el commit.
- **Entorno local:** `docker compose up` levanta el backend (ver
  [docs/paso-a-paso-inicio.md](docs/paso-a-paso-inicio.md)).
