# Aprendizaje

Apuntes de los conceptos que van apareciendo mientras se construye Life OS en
[`new/`](../new/README.md). Cada nota explica un concepto en general y
después cómo se aplica en el proyecto, con enlaces al diseño o al código.

Está en español a propósito. El resto de `new/` está en inglés.

## Organización

- [`patrones-de-diseno/`](patrones-de-diseno/): ideas de diseño
  independientes del lenguaje.
- [`java/`](java/): características del lenguaje y de su ecosistema.

La distinción importa: un patrón es una idea que se puede implementar en
cualquier lenguaje, y una característica de Java es una herramienta concreta
para implementarla. Por ejemplo, *Value Object* es el patrón y `record` es la
herramienta.

## Índice

### Patrones de diseño

| Nota | En una línea |
|---|---|
| [Aggregate](patrones-de-diseno/aggregate.md) | Cluster de objetos con una frontera de consistencia y una única puerta de entrada. |
| [Value Object](patrones-de-diseno/value-object.md) | Objeto definido por su valor: inmutable, comparable por contenido y auto-validado. |

### Java

| Nota | En una línea |
|---|---|
| [`record`](java/record.md) | Clase inmutable de datos con igualdad por valor generada por el compilador. |
| [`sealed`](java/sealed.md) | Jerarquía cerrada que el compilador conoce completa, con `switch` exhaustivo. |
