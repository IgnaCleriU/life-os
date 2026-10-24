# Value Object

**Tipo:** patrón táctico de Domain-Driven Design (DDD). Martin Fowler también
lo describe en su catálogo de patrones de arquitectura.
**Herramienta en Java:** [`record`](../java/record.md).

## Qué es

Un objeto que **se define por su valor, no por su identidad**.

- Dos `Title("Comprar pan")` son el mismo título aunque sean instancias
  distintas.
- Dos tareas con el mismo título siguen siendo dos tareas distintas, porque
  una tarea es una **entidad**: tiene identidad (su id) y su estado cambia
  con el tiempo.

## Sus tres propiedades

1. **Inmutable.** No se modifica: para "cambiarlo" se crea otro. Así se
   puede compartir sin miedo a que alguien lo altere.
2. **Igualdad por valor.** `equals` compara el contenido, no la referencia.
3. **Auto-validado.** Valida sus reglas al construirse, así que no puede
   existir en un estado inválido.

## Qué problema resuelve

La alternativa es usar tipos primitivos (`String`, `int`, `UUID`) para todo,
lo que se conoce como *primitive obsession*. Trae tres problemas:

- **La validación se repite** en cada lugar que recibe el dato, o se olvida
  en alguno.
- **El compilador no distingue significados:** un `String` de título y uno de
  descripción son intercambiables.
- **Las reglas del concepto no tienen dónde vivir,** y terminan esparcidas.

Con un Value Object, el tipo `Title` *garantiza* que el texto es un título
válido. Quien recibe un `Title` no necesita volver a verificarlo.

## Entidad vs. Value Object

| | Entidad | Value Object |
|---|---|---|
| Igualdad | por identidad (id) | por valor |
| Cambia con el tiempo | sí | no, es inmutable |
| Ejemplo en Life OS | `Task`, `Project`, `Area` | `Title`, `Name`, `TaskId`, `TaskLocation` |

## En Life OS

En el [modelo de dominio](../../new/docs/domain-model.md):

- **Textos con reglas:** `Name`, `Title` y `Description`. Por ejemplo, un
  `Title` sale sin espacios sobrantes, no vacío y con como máximo 200
  caracteres.
- **Ids tipados:** `TaskId`, `ProjectId` y `AreaId`. Envuelven un `UUID`, y
  el compilador rechaza pasar un `TaskId` donde se espera un `ProjectId`.
- **`TaskLocation`:** dónde vive una tarea. Es un Value Object con tres
  formas posibles (ver [`sealed`](../java/sealed.md)).
- **`TrashState`:** si un ítem está en la papelera, y quién lo arrastró.
