# Life OS — Guía de Desarrollo

**Autor:** Juan Ignacio
**Fecha:** Julio 2026
**Estado:** Borrador inicial — sujeto a revisión

---

## 1. Visión del proyecto

Sistema operativo personal ("Life OS") que centraliza notas, contraseñas, calendario, proyectos/tareas, inventario del hogar y otros datos personales, con acceso y modificación vía agentes de IA a través de un servidor MCP propio.

**Componentes:**
1. Backend — Python + FastAPI
2. Servidor MCP — expone los datos/acciones a agentes de IA (Claude, etc.)
3. Frontend web
4. CLI / TUI
5. App Android

**Decisiones ya tomadas:**
- MVP inicial: módulo de **Proyectos + Tareas**
- Despliegue: aún no decidido (se detallan opciones abajo)
- Passwords: se recomienda enfoque abajo (sección 6)

---

## 2. Arquitectura general

```
                    ┌─────────────┐
                    │  Android    │
                    │    App      │
                    └──────┬──────┘
                           │ HTTPS/REST
┌───────────┐      ┌───────▼───────┐      ┌──────────────┐
│  Frontend │◄────►│   FastAPI     │◄────►│  PostgreSQL  │
│  (Web)    │      │   Backend     │      │  (o SQLite   │
└───────────┘      │               │      │   en MVP)    │
                    └───────┬───────┘
┌───────────┐              │
│  CLI/TUI  │◄─────────────┤
└───────────┘              │
                    ┌───────▼───────┐
                    │  Servidor MCP │◄──── Agentes IA (Claude, etc.)
                    │  (mismo repo, │
                    │  distinto     │
                    │  proceso)     │
                    └───────────────┘
```

**Principio clave:** el backend FastAPI es la única fuente de verdad. El servidor MCP **no accede directamente a la base de datos**: consume la misma API REST (o una capa de servicios compartida) que usan el frontend, CLI y app Android. Esto evita lógica duplicada y asegura que las reglas de negocio (validaciones, permisos, auditoría) se apliquen siempre, sin importar el cliente.

---

## 3. Stack tecnológico recomendado

| Capa | Recomendación | Alternativas |
|---|---|---|
| Backend | FastAPI + Pydantic v2 | — |
| ORM / DB | SQLModel o SQLAlchemy 2.0 + PostgreSQL | SQLite para desarrollo local |
| Migraciones | Alembic | — |
| Auth | JWT (access + refresh) con OAuth2 password flow | Passkeys/WebAuthn a futuro |
| MCP Server | `mcp` SDK oficial de Python (stdio o HTTP/SSE transport) | — |
| Frontend | React + Vite + TypeScript, TailwindCSS | SvelteKit |
| CLI/TUI | `Typer` (CLI) + `Textual` (TUI) | Click + Rich |
| Android | Kotlin + Jetpack Compose, Retrofit para consumir la API | React Native (si querés compartir más código con el frontend web) |
| Contenedores | Docker + docker-compose para desarrollo | — |
| Background jobs | APScheduler o Celery + Redis (recordatorios, notificaciones) | — |

---

## 4. Módulos de datos (dominio completo)

Aunque el MVP arranca en Proyectos + Tareas, conviene diseñar el modelo de datos pensando en todos los módulos desde el inicio, para no reescribir el core después.

1. **Proyectos y Tareas** (MVP) — proyectos, tareas, subtareas, estados, prioridades, fechas límite, tags
2. **Notas** — texto libre, markdown, vínculos entre notas (estilo Zettelkasten opcional), tags
3. **Calendario** — eventos, recordatorios, recurrencia, integración opcional con Google Calendar
4. **Contraseñas / Vault** — ver sección 6, es el módulo más sensible
5. **Inventario del hogar** — ítems, categorías, ubicación (ej. "Casa de campo"), fotos, garantías/vencimientos
6. **Módulos futuros** — finanzas personales, contactos, documentos/archivos

**Recomendación de modelado:** usar un modelo de "entidad + tags + relaciones" común (similar a Notion/Obsidian) para Notas, Proyectos e Inventario, de forma que compartan componentes de UI y endpoints genéricos (búsqueda, tags, adjuntos), y reservar modelos específicos y más rígidos para Calendario y Passwords, que tienen reglas propias.

---

## 5. Diseño del servidor MCP

**Transporte:** empezar con stdio para uso local (Claude Desktop/Claude Code) y migrar a HTTP/SSE cuando quieras acceso remoto (ej. desde el celular o un agente en la nube).

**Superficie de herramientas (tools) sugerida para el MVP:**
- `list_projects`, `create_project`, `update_project`
- `list_tasks(project_id, status?)`, `create_task`, `update_task`, `complete_task`
- `search` (búsqueda genérica cross-módulo, útil desde el día uno)

**Buenas prácticas:**
- Cada tool del MCP debe llamar a la API REST del backend (no a la DB directo), reusando autenticación.
- Definir permisos granulares desde el principio: qué puede leer/escribir un agente por defecto (ej. bloquear por defecto el módulo de Passwords para cualquier agente, y requerir confirmación explícita).
- Loggear toda acción de escritura hecha por un agente (auditoría), con timestamp y qué tool la originó.

---

## 6. Contraseñas: recomendación

Dado que no estabas seguro del enfoque, la recomendación es:

**No reinventar el cifrado de contraseñas.** Dos caminos razonables:

- **Opción A (recomendada para arrancar rápido y seguro):** integrar **Vaultwarden** (fork open-source de Bitwarden server) como servicio aparte, y que tu backend/MCP hable con su API para listar/crear entradas, en vez de guardar contraseñas en tu propia base de datos. Ganás cifrado end-to-end probado en producción, apps cliente existentes, y te enfocás en construir valor en los otros módulos.
- **Opción B:** si más adelante querés todo bajo un mismo esquema, podés implementar tu propio vault con cifrado AES-256 a nivel de campo, usando una clave derivada de tu master password (Argon2id) que nunca se guarda en el servidor. Es considerablemente más trabajo y riesgo, así que solo tiene sentido si el aprendizaje en sí es un objetivo.

Para el MVP (que es Proyectos + Tareas), esta decisión se puede posponer sin bloquear nada.

---

## 7. Despliegue (a definir)

Como todavía no decidiste dónde correr el sistema, estas son las opciones típicas con sus tradeoffs:

| Opción | Ventajas | Desventajas |
|---|---|---|
| Self-hosted en casa (ej. Raspberry Pi / mini PC) | Control total, sin costos recurrentes, datos nunca salen de tu red | Necesitás resolver acceso remoto (VPN/Tailscale) para usarlo fuera de casa o desde el Android |
| VPS propio (Hetzner, DigitalOcean, etc.) | Acceso remoto simple, buena disponibilidad | Costo mensual, tus datos sensibles viven en un servidor de terceros (mitigable con cifrado) |
| Solo local (PC/notebook) | Cero configuración de red | Sin acceso desde el celular salvo que estés en la misma red; no sirve para uso diario "en cualquier lado" |

**Sugerencia:** para el MVP, correr todo con Docker Compose en tu PC/notebook. Cuando el sistema sea usable, migrar a self-hosted en casa + Tailscale (VPN mesh gratuita) para acceder desde el Android sin exponer puertos a internet. Es el mejor balance de privacidad, costo y practicidad para un proyecto de datos personales sensibles.

---

## 8. Roadmap por fases

### Fase 0 — Fundaciones (1-2 semanas)
- Repo monorepo (o multi-repo) con estructura definida
- Docker Compose: FastAPI + Postgres
- Modelo de datos base (usuarios, auth JWT)
- CI básico (lint + tests)

### Fase 1 — MVP: Proyectos + Tareas
- Endpoints REST completos (CRUD proyectos/tareas)
- Frontend mínimo (lista + kanban, podés reusar ideas de tu proyecto `taskbase`)
- CLI/TUI básica para listar y completar tareas
- Servidor MCP con las tools listadas en sección 5, conectado a Claude Desktop/Code para probar el flujo agente → API

### Fase 2 — Notas + búsqueda
- Modelo de notas + endpoints
- Búsqueda cross-módulo (proyectos + notas)
- Extender MCP con tools de notas

### Fase 3 — Calendario
- Modelo de eventos + recurrencia
- Vista calendario en frontend
- Recordatorios (background jobs)

### Fase 4 — Inventario del hogar
- Modelo de ítems + ubicaciones + adjuntos (fotos)
- Caso de uso concreto: inventario de "Casa de campo"

### Fase 5 — Passwords / Vault
- Integración con Vaultwarden (Opción A) o vault propio
- Definir política de permisos de agentes para este módulo específicamente

### Fase 6 — App Android
- Puede arrancar en paralelo a Fase 2/3 una vez la API sea estable
- Kotlin + Compose consumiendo la misma API REST

### Fase 7 — Endurecimiento
- Rate limiting, auditoría completa de acciones de agentes IA
- Backups automáticos
- Tests end-to-end

---

## 9. Flujo de trabajo con agentes de IA para construir el proyecto

Ya que planeás usar agentes de IA (ej. Claude Code) para desarrollar el sistema, conviene:

1. Mantener este documento y un `ARCHITECTURE.md` versionados en el repo, para que cualquier agente tenga contexto persistente entre sesiones.
2. Definir un `CONTRIBUTING.md` con convenciones (estructura de carpetas, estilo de commits, cómo correr tests) para que el agente las siga consistentemente.
3. Trabajar módulo por módulo (siguiendo el roadmap), pidiéndole al agente que primero proponga el modelo de datos y los endpoints antes de escribir código, para revisar el diseño antes de la implementación.
4. Escribir tests desde el principio: le da al agente una forma objetiva de verificar que no rompió nada al iterar.

---

## 10. Próximos pasos inmediatos

1. Definir despliegue objetivo (sección 7) — condiciona configuración de auth y de red.
2. Crear el repo base con Fase 0 (Docker Compose + FastAPI + Postgres + auth).
3. Modelar Proyectos/Tareas y generar el primer endpoint funcionando end-to-end (API → MCP → agente).
4. Iterar sobre el roadmap ajustando fechas según disponibilidad real.

---

*Documento vivo — actualizar a medida que se tomen decisiones (especialmente despliegue y enfoque de passwords).*
