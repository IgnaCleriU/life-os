# Life OS

Sistema operativo personal que centraliza notas, contraseñas, calendario,
proyectos/tareas, inventario del hogar y otros datos personales, con acceso
y modificación vía agentes de IA a través de un servidor MCP propio.

## Estado actual

🚧 **En planificación.** Todavía no hay código — el repo tiene la
documentación de arranque y las convenciones de contribución. Fase 0
(fundaciones) no arrancó.

## Stack

| Capa | Recomendación |
|---|---|
| Backend | FastAPI + Pydantic v2 |
| ORM / DB | SQLModel + SQLite (MVP) → PostgreSQL (multi-dispositivo) |
| MCP Server | `mcp` SDK oficial de Python (stdio → HTTP/SSE) |
| Frontend | React + Vite + TypeScript, TailwindCSS |
| CLI/TUI | `Typer` + `Textual` |
| Android | Kotlin + Jetpack Compose, Retrofit |
| Contenedores | Docker + docker-compose |

Detalle completo en [docs/guia-de-desarrollo.md](docs/guia-de-desarrollo.md).

## Arquitectura

Monorepo con arquitectura hexagonal: el dominio no depende de FastAPI,
SQLite ni MCP, y REST/MCP son dos adaptadores de entrada distintos que
ejecutan los mismos casos de uso. Ver [ARCHITECTURE.md](ARCHITECTURE.md).

## Roadmap

- [ ] **Fase 0** — Fundaciones (repo, Docker Compose, modelo base, CI básico) — *en progreso*
- [ ] **Fase 1** — MVP: Proyectos + Tareas (REST + frontend mínimo + CLI/TUI + servidor MCP)
- [ ] **Fase 2** — Notas + búsqueda cross-módulo
- [ ] **Fase 3** — Calendario + recordatorios
- [ ] **Fase 4** — Inventario del hogar
- [ ] **Fase 5** — Passwords / Vault (Vaultwarden)
- [ ] **Fase 6** — App Android
- [ ] **Fase 7** — Endurecimiento (rate limiting, auditoría, backups, e2e)

Detalle de cada fase en [docs/guia-de-desarrollo.md](docs/guia-de-desarrollo.md#8-roadmap-por-fases).
El arranque de Fase 0/1 está desglosado paso a paso en
[docs/paso-a-paso-inicio.md](docs/paso-a-paso-inicio.md).

## Contribuir

Convenciones de commits y setup de `pre-commit` en [CONTRIBUTING.md](CONTRIBUTING.md).
