# Aggregate

**Tipo:** patrón táctico de Domain-Driven Design (DDD).
**Origen:** Eric Evans, *Domain-Driven Design* (2003). Vaughn Vernon lo
refinó en *Implementing Domain-Driven Design* (2013) con cuatro reglas
prácticas que hoy son la referencia.

## Qué problema resuelve

En un modelo con muchos objetos relacionados aparece una pregunta: **¿qué
tiene que ser consistente al mismo tiempo?** Si cualquier objeto puede
modificar a cualquier otro, las reglas de negocio quedan desparramadas y
nadie las garantiza.

El patrón agrupa objetos en un **cluster con una frontera de consistencia**.
Adentro de esa frontera, las reglas (invariantes) se cumplen siempre,
después de cada operación.

## Las piezas

- **Raíz del agregado (*aggregate root*):** la única entidad del cluster a la
  que se accede desde afuera. Todo cambio pasa por sus métodos, y por eso
  ella puede hacer cumplir las invariantes.
- **Miembros internos:** otras entidades u objetos de valor (ver
  [Value Object](value-object.md)) que solo se modifican a través de la raíz.
- **Frontera:** lo que está adentro se guarda y se carga entero, como una
  unidad.

## Las reglas de Vernon

1. **Proteger las invariantes verdaderas dentro de la frontera.** Lo que
   tiene que ser consistente en el mismo instante va en el mismo agregado.
2. **Diseñar agregados chicos.** Uno grande se carga entero para cualquier
   cambio y genera conflictos de concurrencia.
3. **Referenciar otros agregados solo por id,** nunca con una referencia
   directa al objeto.
4. **Fuera de la frontera, consistencia eventual,** o coordinada por la capa
   de aplicación.

De ellas sale una regla práctica: **una transacción modifica un solo
agregado.**

## Cómo elegir la frontera

La tentación es seguir la estructura "natural" del mundo: un proyecto
*contiene* tareas, así que `Project` debería contener a `Task`. La pregunta
correcta es otra: **¿qué regla obliga a que estas cosas cambien juntas?**

- Si una regla necesita que dos cosas sean consistentes *en el mismo
  instante*, van en el mismo agregado.
- Si no, van separadas y se referencian por id.

## En Life OS

En el [modelo de dominio](../../new/docs/domain-model.md), `Task`, `Project`
y `Area` son **tres agregados separados**, cada uno raíz de sí mismo.

- **Por qué no `Project` conteniendo a sus tareas:**
  - las tareas también viven en el inbox y directo en áreas;
  - las tareas se mueven entre contenedores;
  - para cambiar una sola tarea habría que cargar el proyecto entero.
- **Invariantes internas:** cada agregado cuida las suyas. Por ejemplo, un
  título válido, o que un proyecto solo cambie de estado según su tabla de
  transiciones.
- **Referencias por id:** `Task` apunta a su proyecto con un `ProjectId`, no
  con un objeto `Project` (regla 3).
- **Reglas que cruzan agregados:** la regla L1 ("no se completa un proyecto
  con tareas abiertas") involucra a `Project` y a `Task`. La decisión igual
  vive en el dominio: el método recibe el dato que necesita,
  `complete(openTasks)`, y el caso de uso solo se encarga de juntarlo. Así la
  regla se testea sin base de datos.

### Dónde nos apartamos de la ortodoxia

La papelera en cascada (reglas X2 y X3) modifica varios agregados en una
misma transacción, lo que rompe "una transacción, un agregado". Para un
sistema de un solo usuario sobre una base local es razonable: no hay
concurrencia real que haga caro bloquear varios agregados juntos. Si Life OS
llegara a tener muchos usuarios concurrentes, esta es la primera decisión a
revisar.

## Para seguir

- Vaughn Vernon, *Effective Aggregate Design* (tres artículos breves y
  gratuitos que resumen las reglas).
- Eric Evans, *Domain-Driven Design*, capítulo 6.
