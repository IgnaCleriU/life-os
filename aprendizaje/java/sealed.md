# `sealed`

**Tipo:** característica del lenguaje, no un patrón.
**Versión:** Java 17 (JEP 409); estuvo en preview en Java 15 y 16. Su
complemento, el *pattern matching* en `switch`, es de Java 21 (JEP 441).

## Qué es

Una clase o interfaz `sealed` declara **quiénes, y solo quiénes, pueden
extenderla o implementarla**:

```java
sealed interface TaskLocation permits Inbox, InArea, InProject { }

record Inbox() implements TaskLocation { }
record InArea(AreaId area) implements TaskLocation { }
record InProject(ProjectId project) implements TaskLocation { }
```

Si alguien escribe `record Garage() implements TaskLocation` en otro lado,
no compila. La jerarquía queda **cerrada**: el compilador conoce la lista
completa de variantes.

## Reglas

Cada subtipo permitido tiene que declarar cómo sigue la jerarquía:

- **`final`:** nadie lo extiende. Los records ya son `final` implícitamente.
- **`sealed`:** sigue cerrado, con su propio `permits`.
- **`non-sealed`:** se vuelve a abrir a propósito.

Además:

- Los subtipos tienen que estar en el mismo paquete, o en el mismo módulo si
  se usan módulos de Java.
- Si están en el mismo archivo, el `permits` se puede omitir.

## Para qué sirve: exhaustividad

Combinado con el *pattern matching* en `switch`, el compilador verifica que
se cubrieron todos los casos:

```java
String describe(TaskLocation location) {
    return switch (location) {
        case Inbox i     -> "inbox";
        case InArea a    -> "area " + a.area();
        case InProject p -> "project " + p.project();
    };
}
```

- **No hay `default`.** No hace falta, porque el compilador sabe que no hay
  más casos.
- **Agregar una variante rompe la compilación a propósito.** Si mañana
  aparece una cuarta (por ejemplo `Someday`), cada `switch` que no la
  contemple deja de compilar. El compilador te lleva a cada lugar que hay que
  actualizar. Con un `default`, ese olvido pasaría en silencio.

## El concepto detrás: tipos suma

Una interfaz sellada con records es un **tipo suma** (*sum type*, o tipo
algebraico de datos): un valor que es exactamente una de varias formas
cerradas, y cada forma puede llevar datos distintos. Es un concepto de
teoría de tipos que viene de lenguajes funcionales (Haskell, ML, Rust); no
es un patrón de diseño. Java lo incorporó con `sealed`, `record` y el
*pattern matching*.

## Contra qué compite

| Alternativa | Cuándo es la correcta |
|---|---|
| **Interfaz abierta** (normal) | Cuando se busca extensibilidad: un puerto como `TaskRepository` que admite varias implementaciones. |
| **`enum`** | Conjunto cerrado de **instancias** con la misma forma. `Priority` (LOW, MEDIUM, HIGH) es un enum perfecto. No sirve para `TaskLocation`, porque cada variante lleva datos distintos. |
| **Patrón Visitor** (Gang of Four) | La forma clásica de recorrer una jerarquía cerrada con el compilador obligando a manejar cada tipo. `sealed` + `switch` logra lo mismo con mucho menos código, así que en Java moderno es casi innecesario para este uso. |

## Regla práctica

- **El conjunto de variantes lo define el dominio** y no debería crecer sin
  que lo decidas: usá `sealed`.
- **Lo define quien extiende el sistema** (nuevas implementaciones de un
  puerto): usá una interfaz abierta.

## En Life OS

En el [modelo de dominio](../../new/docs/domain-model.md) hay dos interfaces
selladas:

- **`TaskLocation`:** `Inbox`, `InArea` e `InProject`. Reemplaza a dos
  campos que admiten `null` (`areaId` y `projectId`) más una regla de "como
  mucho uno de los dos": con un tipo sellado, esa regla no se puede romper.
- **`TrashState`:** `Live` y `Trashed`. Un ítem está en la papelera o no; si
  está, lleva el dato de quién lo arrastró.
