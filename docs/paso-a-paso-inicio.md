# Life OS — Paso a Paso: Inicio (Proyectos + Tareas + MCP)

**Depende de:** Life OS - Guía de Desarrollo
**Alcance de este documento:** desde repo vacío hasta tener Proyectos/Tareas funcionando end-to-end (API + MCP), listo para empezar a usar la propia app para gestionar el resto del roadmap.

---

## 0. Decisiones de inicio (ya tomadas)

- **Organización:** monorepo, arquitectura hexagonal (puertos y adaptadores)
- **Entorno local:** Docker Compose desde el día 1
- **DB:** SQLite para arrancar (migración a Postgres queda para cuando haya multi-dispositivo/concurrencia real)
- **Usuario:** single-user, sin multi-tenant
- **Alcance funcional:** solo Proyecto + Tarea (sin Notas/Calendario/Passwords/Inventario todavía)

---

## 1. Por qué arquitectura hexagonal acá

Con hexagonal, el **dominio** (Proyecto, Tarea, reglas) no sabe nada de FastAPI, SQLite ni MCP. Eso significa que cuando en la Fase 2 agregues Notas, o cuando cambies SQLite por Postgres, o cuando agregues un segundo "adaptador de entrada" (la app Android hablando directo, o el CLI), **no tocás el dominio ni los casos de uso** — solo agregás una implementación nueva de un puerto ya definido. Para este proyecto en particular es clave porque el MCP y el REST API son dos "entradas" distintas al mismo negocio: ambas deben ejecutar exactamente la misma lógica de casos de uso.

**Regla de dependencia:** las flechas de dependencia siempre apuntan hacia adentro.

```
adapters (REST, MCP) ──► application (casos de uso) ──► domain (entidades)
                                    ▲
infrastructure (DB) ────────────────┘ (implementa los puertos que application define)
```

---

## 2. Estructura de carpetas

```
life-os/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   └── lifeos/
│   │       ├── domain/
│   │       │   ├── __init__.py
│   │       │   ├── project.py          # entidad Project (dataclass, sin deps externas)
│   │       │   ├── task.py             # entidad Task
│   │       │   └── exceptions.py       # excepciones de dominio (ej. TaskNotFound)
│   │       │
│   │       ├── application/
│   │       │   ├── ports/              # interfaces abstractas (Protocol/ABC)
│   │       │   │   ├── project_repository.py
│   │       │   │   └── task_repository.py
│   │       │   └── use_cases/
│   │       │       ├── create_project.py
│   │       │       ├── list_projects.py
│   │       │       ├── create_task.py
│   │       │       ├── list_tasks.py
│   │       │       ├── update_task.py
│   │       │       └── complete_task.py
│   │       │
│   │       ├── infrastructure/
│   │       │   ├── config.py           # settings (pydantic-settings)
│   │       │   └── db/
│   │       │       ├── models.py       # SQLModel: ProjectORM, TaskORM
│   │       │       ├── session.py      # engine + sessionmaker
│   │       │       └── repositories/
│   │       │           ├── sqlite_project_repository.py   # implementa ProjectRepository
│   │       │           └── sqlite_task_repository.py      # implementa TaskRepository
│   │       │
│   │       └── adapters/
│   │           ├── rest/
│   │           │   ├── main.py         # instancia FastAPI, incluye routers
│   │           │   ├── deps.py         # inyección de dependencias (repos, use cases)
│   │           │   ├── schemas.py      # DTOs Pydantic (request/response)
│   │           │   └── routers/
│   │           │       ├── projects.py
│   │           │       └── tasks.py
│   │           └── mcp/
│   │               ├── server.py       # servidor MCP (stdio)
│   │               └── tools.py        # define tools, llaman a los mismos use cases
│   │
│   └── tests/
│       ├── domain/
│       ├── application/
│       └── adapters/
│
└── docs/
    └── (documentos de planificación existentes)
```

**Notas de implementación:**
- `domain/` no importa nada de `sqlmodel`, `fastapi` ni `mcp`. Solo Python puro (dataclasses/enums).
- Los `ports/` son interfaces (`Protocol` de `typing` o `ABC`) que `application/use_cases` usa sin saber la implementación concreta.
- `rest/deps.py` y `mcp/server.py` son los únicos lugares donde se "conecta" la implementación real (SQLite) con los casos de uso — inyección de dependencias manual, sin frameworks de DI adicionales por ahora.

---

## 3. Pasos concretos

### Paso 1 — Scaffolding del repo
- [ ] Crear estructura de carpetas de la sección 2 (vacía, con `__init__.py`)
- [ ] `pyproject.toml` con dependencias: `fastapi`, `uvicorn`, `sqlmodel`, `pydantic-settings`, `mcp`, `pytest`
- [ ] `docker-compose.yml` con un servicio `backend` (build desde `backend/`, monta volumen para hot-reload, expone puerto 8000)
- [ ] `Dockerfile` en `backend/` (imagen `python:3.12-slim`, instala deps, `uvicorn` con `--reload`)
- [ ] Levantar con `docker compose up` y verificar que un endpoint `/health` responda

### Paso 2 — Dominio
- [ ] Definir `Project` (id, nombre, descripción, estado, created_at)
- [ ] Definir `Task` (id, project_id, título, estado [todo/doing/done], prioridad, due_date, created_at)
- [ ] Definir excepciones de dominio (`ProjectNotFound`, `TaskNotFound`)
- [ ] Tests unitarios del dominio (sin DB, sin mocks — son solo objetos Python)

### Paso 3 — Puertos (interfaces)
- [ ] `ProjectRepository` (Protocol): `add`, `get`, `list`, `update`
- [ ] `TaskRepository` (Protocol): `add`, `get`, `list_by_project`, `update`, `delete`

### Paso 4 — Casos de uso
- [ ] `CreateProject`, `ListProjects`
- [ ] `CreateTask`, `ListTasks` (con filtro opcional por proyecto/estado), `UpdateTask`, `CompleteTask`
- [ ] Cada caso de uso recibe el/los repositorios por constructor (inyección) y depende solo de los puertos, nunca de SQLModel directamente
- [ ] Tests de casos de uso usando un repositorio **fake en memoria** (no SQLite) — esto es lo que hace rápida la suite de tests

### Paso 5 — Infraestructura (SQLite)
- [ ] Modelos SQLModel (`ProjectORM`, `TaskORM`) con sus relaciones
- [ ] Implementar `SQLiteProjectRepository` y `SQLiteTaskRepository` cumpliendo los puertos del Paso 3
- [ ] Configurar `session.py` (engine SQLite, `create_all` para MVP; Alembic queda para cuando el esquema empiece a cambiar seguido)

### Paso 6 — Adaptador REST
- [ ] `schemas.py`: DTOs de entrada/salida (`ProjectCreate`, `ProjectOut`, `TaskCreate`, `TaskOut`, etc.)
- [ ] `deps.py`: funciones `get_project_repository()`, `get_task_use_cases()` etc., usando `Depends` de FastAPI
- [ ] Routers: `POST/GET /projects`, `POST/GET /projects/{id}/tasks`, `PATCH /tasks/{id}`, `POST /tasks/{id}/complete`
- [ ] Probar todo con `/docs` (Swagger autogenerado por FastAPI)

### Paso 7 — Adaptador MCP
- [ ] `server.py`: instancia servidor MCP (transporte stdio)
- [ ] `tools.py`: define las tools (`create_project`, `list_projects`, `create_task`, `list_tasks`, `update_task`, `complete_task`), cada una llamando al caso de uso correspondiente (mismo código que usa el REST, distinta "puerta de entrada")
- [ ] Configurar Claude Desktop o Claude Code para levantar este servidor MCP localmente y probar los comandos en una conversación real

### Paso 8 — Cierre del MVP
- [ ] Cargar el roadmap completo (Fases 1-7 del documento de Guía) como Proyecto + Tareas dentro de la propia app, usando el agente vía MCP
- [ ] A partir de acá, usar la app + MCP para gestionar el desarrollo de los siguientes módulos

---

## 4. Definición de "hecho" para este documento

Vas a saber que terminaste esta etapa cuando puedas, en una sola conversación con Claude conectado al MCP local, decir *"creá un proyecto llamado Life OS Roadmap y cargale como tareas las fases 2 a 7"* y verlas aparecer correctamente al consultarlas por API o por MCP.

---

*Siguiente documento: paso a paso de Notas (Fase 2), una vez cerrado este MVP.*
