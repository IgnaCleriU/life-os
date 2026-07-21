# Life OS — Flujo Agéntico de Desarrollo

**Depende de:** [Life OS - Guía de Desarrollo](guia-de-desarrollo.md), [ARCHITECTURE.md](../ARCHITECTURE.md)
**Alcance de este documento:** define cómo un agente de IA (ej. Claude Code) debe organizar el
trabajo sobre este repo — desde que recibe una tarea hasta que la deja lista para revisión.
Es prescriptivo: describe el proceso que se espera que el agente siga, no una simple referencia.

Para las convenciones de commits y el flujo de Pull Requests, ver [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## 1. Roles

El desarrollo se organiza alrededor de un **modelo orquestador** que puede delegar en **subagentes**.

| Rol | Responsabilidad |
|---|---|
| **Orquestador** | Entiende la tarea, decide la estrategia, lanza subagentes, integra sus resultados, commitea de forma atómica y abre la PR. No escribe toda la implementación de una sola vez: coordina. |
| **Subagente de investigación** | Explora el repo (patrones existentes, archivos afectados, utilidades reutilizables) y devuelve conclusiones, no cambios. Es de solo lectura. |
| **Subagente de implementación** | Recibe una porción acotada del trabajo (una capa, un módulo, un archivo) y produce los cambios de esa porción. |

El orquestador es el único responsable del estado final: aunque delegue, revisa e integra todo
antes de considerar la tarea terminada.

---

## 2. Ciclo de trabajo

```
┌──────────────────────────────────────────────────────────────────────┐
│ 1. Entender  →  2. Investigar  →  3. Planear  →  4. Implementar  →  5. Integrar │
│                     (∥ subagentes)   (si aplica)   (∥ o serie)      y verificar │
└──────────────────────────────────────────────────────────────────────┘
```

### 1. Entender la tarea
El orquestador reformula el objetivo y el alcance con sus propias palabras: qué se pide, qué queda
fuera, y qué significa "hecho". Si hay ambigüedad de diseño que condiciona el resultado, pregunta
antes de seguir.

### 2. Investigar
Antes de diseñar, el orquestador lanza **subagentes de investigación** para mapear el repo:
patrones existentes, archivos afectados, utilidades y casos de uso reutilizables. Cuando las áreas
a investigar son independientes (ej. "cómo está el dominio" vs "cómo se testean los casos de uso"),
se lanzan **en paralelo**. La regla es reutilizar lo que ya existe antes de proponer código nuevo.

### 3. Planear
El orquestador arma un plan **salvo que la tarea sea muy chica**. Umbral:

- **Sin plan** — cambio trivial y acotado: un solo archivo, sin ambigüedad de diseño, sin efectos
  en otras capas (ej. corregir un typo, ajustar un mensaje, renombrar una variable local).
- **Con plan** — todo lo demás: cualquier tarea que toque más de un archivo o capa, agregue
  comportamiento, o tenga decisiones de diseño. El plan describe los pasos, los archivos a tocar y
  cómo se va a verificar.

Ante la duda, se hace plan.

### 4. Implementar
El orquestador reparte el trabajo en **subagentes de implementación**, decidiendo el modo según las
dependencias entre los cambios (ver sección 3):

- **En paralelo** cuando las porciones no se pisan (capas o módulos distintos, sin dependencia mutua).
- **En serie** cuando una porción depende de otra (lo que produce una debe existir antes de empezar la siguiente).

### 5. Integrar y verificar
El orquestador junta los resultados de los subagentes, resuelve conflictos, corre tests y lint, y
confirma que se cumple la definición de "hecho". Recién entonces commitea (de forma atómica, ver
[CONTRIBUTING.md](../CONTRIBUTING.md)) y abre la PR.

---

## 3. Cuándo paralelizar vs. serializar

La [arquitectura hexagonal](../ARCHITECTURE.md) del proyecto define una regla de dependencia que
sirve de guía directa: **las flechas apuntan hacia adentro**
(`adapters → application → domain`, e `infrastructure → application`). Se serializa a favor de esa
dirección y se paraleliza lo que queda en ramas independientes.

| Situación | Modo | Ejemplo |
|---|---|---|
| Una porción usa un contrato/entidad que otra debe crear primero | **Serie** | Definir el puerto `TaskRepository` **antes** de implementar `SQLiteTaskRepository`; definir la entidad `Task` **antes** del caso de uso `CompleteTask` |
| Porciones en capas o módulos sin dependencia mutua | **Paralelo** | Escribir el adaptador REST y el adaptador MCP de un caso de uso ya existente; trabajar el módulo `projects` y el módulo `tasks` cuando no comparten cambios |
| Investigación de áreas distintas del repo | **Paralelo** | Un subagente mapea el dominio mientras otro revisa los patrones de testing |
| Tests de una capa recién implementada | **Serie** (después de esa capa) | Tests de casos de uso una vez que existen los casos de uso y su repositorio fake |

Regla práctica: si el resultado de A es entrada de B, van en serie (A → B). Si A y B pueden fallar o
cambiar sin afectarse, van en paralelo.

---

## 4. Diagrama del flujo

```
                      ┌─────────────────────────────┐
     tarea  ─────────►│        ORQUESTADOR          │
                      │  entiende · coordina · integra │
                      └───┬───────────┬───────────┬──┘
                          │           │           │
              investigación (∥)   planear     implementación
                  ┌───────┼───────┐   │      ┌──────┼──────┐
                  ▼       ▼       ▼   ▼      ▼      ▼      ▼
               [sub]   [sub]   [sub] (plan) [sub]  [sub]  [sub]
              dominio  tests  patrones      dominio→puerto  adaptadores
                                            (serie)          (∥)
                          │           │           │
                          └───────────┴───────────┴──► integrar + verificar
                                                             │
                                                             ▼
                                              rama · commits atómicos · PR a master
```

---

## 5. Agentes en paralelo: aislamiento con git worktrees

Cuando se corren **varios agentes a la vez sobre la misma máquina**, cada uno debe trabajar en su
propia rama sin pisarse. Un repo git tiene un solo working tree y un solo índice, así que dos
agentes en el mismo directorio se mezclan los cambios y las ramas.

La solución es un **git worktree por agente**: cada uno obtiene su propio directorio de trabajo con
su propia rama checkouteada, respaldados por el mismo `.git`. En Claude Code esto se activa con la
opción de **worktree** (aislamiento por worktree) al lanzar agentes en paralelo.

Ventajas:

- Cada agente commitea en su rama (`<tipo>/<descripción-corta>`) sin afectar a los demás.
- Git impide checkoutear la misma rama en dos worktrees → guardarraíl contra colisiones.

Como comparten el `.git`, tener en cuenta:

- **`pre-commit`** se instala una vez (hooks en el git-dir común) y valida en todos los worktrees.
- **Entorno Python de `backend/`**: cada worktree es un directorio nuevo; si el venv vive dentro del
  worktree hay que instalar deps por worktree.
- **Puertos y DB de dev**: dos agentes que levanten la app o la SQLite a la vez chocan (puerto 8000,
  archivo de DB). Correr la app en paralelo requiere puertos/DB distintos.
- **Integración a `master`** sigue siendo secuencial vía PRs; los worktrees evitan el pisón durante
  el desarrollo, no el merge.

---

## 6. Relación con PRs y commits

El flujo agéntico termina en una entrega que sigue las convenciones de [CONTRIBUTING.md](../CONTRIBUTING.md):

- **Cada tarea = una rama = una PR** contra `master`.
- El orquestador convierte el trabajo de los subagentes en **varios commits atómicos** (uno por
  cambio lógico coherente), no en un único commit gigante, para que la PR se lea como una historia
  clara.
- Los mensajes siguen [Conventional Commits](../CONTRIBUTING.md#convención-de-commits) y se validan
  localmente con `pre-commit`.

---

*Documento vivo — actualizar a medida que evolucione la forma de trabajar con agentes.*
