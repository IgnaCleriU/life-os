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

## Commits atómicos

Una tarea no se resuelve con un único commit gigante: se parte en **varios commits atómicos**
para que la Pull Request se lea como una historia clara y sea fácil de revisar.

Reglas:

- **Un commit = un cambio lógico completo y coherente**, que idealmente compila y pasa tests por
  sí solo.
- **No mezclar** feature + refactor + fix en el mismo commit. Cada commit usa el `tipo` que le
  corresponde.
- Ordenar los commits siguiendo la [regla de dependencia de la arquitectura](ARCHITECTURE.md)
  (de adentro hacia afuera): dominio → puertos → casos de uso → infraestructura → adaptadores →
  tests.

### Ejemplo: una tarea partida en commits atómicos

Tarea: "agregar la funcionalidad de completar una tarea (Task)".

```
feat(domain): agregar transición de estado a done en Task
feat(application): agregar puerto TaskRepository
feat(application): agregar caso de uso CompleteTask
feat(infrastructure): implementar SQLiteTaskRepository
feat(adapters-rest): agregar endpoint POST /tasks/{id}/complete
feat(adapters-mcp): agregar tool complete_task
test(application): tests del caso de uso CompleteTask
```

Cada línea es revisable de forma aislada, y la secuencia cuenta qué se hizo y en qué orden.

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

## Flujo de Pull Requests

Nunca se commitea directo a `master`. Toda tarea se trabaja en una **rama propia** y se integra
mediante una Pull Request.

1. **Partir de `master` actualizado** y crear una rama nueva para la tarea.
2. **Trabajar en la rama**, dejando la tarea en [commits atómicos](#commits-atómicos).
3. **Abrir una PR contra `master`** al terminar; la PR contiene esos commits.

### Nombre de rama

Formato `<tipo>/<descripción-corta>` en kebab-case, usando el mismo `<tipo>` que el commit
principal de la tarea (los tipos de la [convención de commits](#tipos)):

```
feat/completar-tarea
fix/validacion-project-id
docs/flujo-agentico
refactor/extraer-validacion-task
```

### Contenido de la PR

- **Título** en estilo Conventional Commits (mismo formato que un commit), ej.
  `feat(tasks): agregar completar tarea`.
- **Descripción** con: qué se hizo, por qué, y cómo verificarlo (tests a correr, endpoint/tool a
  probar).
- Los mensajes de los commits ya vienen validados localmente por `pre-commit`
  (ver sección anterior).

El flujo de trabajo agéntico que produce estas PRs está descrito en
[docs/flujo-agentico.md](docs/flujo-agentico.md).
