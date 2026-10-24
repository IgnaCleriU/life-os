# `record`

**Tipo:** característica del lenguaje, no un patrón.
**Versión:** Java 16 (JEP 395); estuvo en preview en Java 14 y 15.
**Implementa el patrón:** [Value Object](../patrones-de-diseno/value-object.md).

## Qué es

Una clase cuyo propósito es **transportar datos inmutables**. Se declara
nombrando sus componentes:

```java
public record Title(String value) { }
```

Con esa línea, el compilador genera:

- un campo `private final` por componente;
- el **constructor canónico**, que recibe todos los componentes;
- un accessor por componente, con el mismo nombre (`value()`, no
  `getValue()`);
- `equals`, `hashCode` y `toString` basados en los valores.

Equivale a unas 40 líneas de una clase escrita a mano, y sin el riesgo de
olvidarse un campo en `equals`.

## Validar con el constructor compacto

El **constructor compacto** omite la lista de parámetros y corre antes de
asignar los campos. Ahí se valida, y también se puede normalizar el valor:

```java
public record Title(String value) {
    public Title {
        value = value.strip();
        if (value.isEmpty() || value.length() > 200) {
            throw new IllegalArgumentException("invalid title");
        }
    }
}
```

Como no hay otra forma de crear un `Title`, un título inválido no puede
existir. Esto es lo que convierte al record en un Value Object de verdad.

## Qué se puede y qué no

| Se puede | No se puede |
|---|---|
| Implementar interfaces | Extender otra clase (todo record extiende `java.lang.Record`) |
| Agregar métodos y campos `static` | Declarar campos de instancia fuera de los componentes |
| Declarar otros constructores, que delegan en el canónico | Ser extendido: un record es implícitamente `final` |

## Límites que conviene saber

- **La inmutabilidad es superficial.** Si un componente es una `List`
  mutable, la lista se puede modificar desde afuera. Hay que copiarla en el
  constructor:

  ```java
  record Tags(List<String> values) {
      Tags { values = List.copyOf(values); }
  }
  ```

- **No sirve para entidades.** Una entidad, como `Task`, se compara por id y
  su estado cambia con el tiempo. Un record se compara por todos sus valores
  y no cambia.

## Records en patrones de `switch`

Desde Java 21 (JEP 440, *record patterns*), un `switch` puede desarmar un
record y extraer sus componentes directamente:

```java
switch (location) {
    case InArea(AreaId area)       -> ...
    case InProject(ProjectId id)   -> ...
    case Inbox()                   -> ...
}
```

Esto se combina con [`sealed`](sealed.md) para que el `switch` sea
exhaustivo.

## En Life OS

Los Value Objects del [modelo de dominio](../../new/docs/domain-model.md)
van a ser records:

- **Textos:** `Name`, `Title` y `Description`.
- **Ids:** `TaskId`, `ProjectId` y `AreaId`.
- **Variantes:** las de `TaskLocation` (`Inbox`, `InArea` e `InProject`) y
  las de `TrashState`.

`Task`, `Project` y `Area` no van a ser records, porque son entidades.
