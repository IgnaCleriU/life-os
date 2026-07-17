# Contributing

Este documento define convenciones para trabajar en Life OS. Aplica tanto a
contribuciones humanas como a agentes de IA (ej. Claude Code) operando sobre
el repo.

## Convención de commits

Los mensajes de commit siguen [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<scope opcional>)<!>: <descripción en imperativo, minúscula, sin punto final>
```

### Tipos

| Tipo | Cuándo usarlo |
|---|---|
| `feat` | Nueva funcionalidad visible para el usuario o el agente (nuevo endpoint, nueva tool MCP, nueva pantalla) |
| `fix` | Corrección de un bug |
| `docs` | Cambios solo en documentación (`docs/`, `README`, `CONTRIBUTING.md`, comentarios de arquitectura) |
| `refactor` | Cambio de código que no altera comportamiento externo ni agrega feature ni corrige bug |
| `test` | Agregar o corregir tests, sin tocar código de producción |
| `chore` | Tareas de mantenimiento que no encajan en las demás (dependencias, configuración de tooling, limpieza de archivos) |
| `build` | Cambios que afectan el sistema de build o dependencias externas (Dockerfile, docker-compose.yml, pyproject.toml) |
| `ci` | Cambios en configuración de integración continua |
| `style` | Cambios de formato/estilo que no afectan la lógica (whitespace, formateo automático) |
| `perf` | Cambios que mejoran el rendimiento |
| `revert` | Revertir un commit anterior |

### Scopes

Libres y opcionales — no hay una lista cerrada todavía. Usalos de forma
orgánica para indicar la capa (`domain`, `application`, `infrastructure`,
`adapters-rest`, `adapters-mcp`), el módulo (`projects`, `tasks`) o el
cliente (`frontend`, `cli`, `android`) afectado.

### Ejemplos

```
feat(tasks): agregar endpoint de completar tarea
fix(mcp): corregir validación de project_id en create_task
docs: definir convención de commits y agregar pre-commit hook
refactor(domain): extraer validación de estado de Task
chore: actualizar dependencias de fastapi
```

### Breaking changes

Los cambios que rompen contratos entre capas (ej. cambio de firma en un
puerto/`Protocol`) o contratos de API pública se marcan con `!` después del
tipo/scope, o con un footer `BREAKING CHANGE:` explicando el impacto:

```
feat(application)!: cambiar firma de TaskRepository.list_by_project
```

## Validación automática (pre-commit)

El formato del mensaje de commit se valida automáticamente con
[`pre-commit`](https://pre-commit.com) y el hook
[`conventional-pre-commit`](https://github.com/compilerla/conventional-pre-commit).

Instalación (una vez por clon del repo):

```
pip install pre-commit
pre-commit install --hook-type commit-msg
```

A partir de ahí, cualquier commit con un mensaje que no siga el formato de
arriba es rechazado localmente antes de crearse.
