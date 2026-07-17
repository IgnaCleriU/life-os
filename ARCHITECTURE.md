# Architecture

Documento vivo — se actualiza a medida que se agregan módulos de dominio
(Notas, Calendario, Inventario, Passwords) o nuevos adaptadores. A
diferencia de [docs/paso-a-paso-inicio.md](docs/paso-a-paso-inicio.md), que
queda como registro histórico del arranque del MVP, este documento describe
el estado actual de la arquitectura.

## Principio: arquitectura hexagonal

El **dominio** (entidades y reglas de negocio) no sabe nada de FastAPI,
SQLite ni MCP — es Python puro. Esto es clave en Life OS porque el servidor
MCP y la API REST son dos "entradas" distintas al mismo negocio: ambas
deben ejecutar exactamente la misma lógica de casos de uso, sin
duplicarla. Cuando se agregue un módulo nuevo o se cambie de motor de DB,
no se toca el dominio ni los casos de uso — solo se agrega/reemplaza una
implementación de un puerto ya definido.

## Regla de dependencia

Las flechas de dependencia siempre apuntan hacia adentro:

```
adapters (REST, MCP) ──► application (casos de uso) ──► domain (entidades)
                                    ▲
infrastructure (DB) ────────────────┘ (implementa los puertos que application define)
```

## Capas

| Capa | Responsabilidad | No depende de |
|---|---|---|
| `domain/` | Entidades (`Project`, `Task`, ...) y excepciones de dominio | `sqlmodel`, `fastapi`, `mcp` |
| `application/ports/` | Interfaces (`Protocol`/`ABC`) que definen contratos de persistencia, ej. `ProjectRepository` | Implementación concreta |
| `application/use_cases/` | Lógica de negocio (`CreateProject`, `CompleteTask`, ...), recibe repositorios por constructor | `sqlmodel`, `fastapi`, `mcp` |
| `infrastructure/` | Implementación concreta de los puertos (ej. `SQLiteProjectRepository`), config, sesión de DB | — |
| `adapters/rest/` | FastAPI: routers, DTOs Pydantic, inyección de dependencias | Lógica de negocio propia (delega a `application`) |
| `adapters/mcp/` | Servidor MCP: cada tool llama al mismo caso de uso que usa REST | Lógica de negocio propia (delega a `application`) |

Estructura de carpetas completa (con archivos concretos del MVP) en
[docs/paso-a-paso-inicio.md](docs/paso-a-paso-inicio.md#2-estructura-de-carpetas).

## Servidor MCP

El servidor MCP **no accede directamente a la base de datos**: consume los
mismos casos de uso que expone el adaptador REST. Esto garantiza que las
reglas de negocio (validaciones, permisos, auditoría) se apliquen siempre,
sin importar si la acción vino de un agente de IA, del frontend o del CLI.

## Mantenimiento de este documento

Actualizar cuando:
- Se agrega un nuevo módulo de dominio (Notas, Calendario, Inventario, Passwords — Fases 2+)
- Se agrega un nuevo adaptador de entrada (ej. app Android hablando directo a la API)
- Se reemplaza SQLite por PostgreSQL, o cambia algún puerto existente
