# Backend Java — guía de estudio

Material producido durante una revisión guiada de `backend-java/`, con Claude
como tutor. El objetivo es entender en qué se apoya el backend (arquitectura,
patrones, decisiones y sus razones) antes de seguir desarrollándolo. Cuando la
revisión termine, este material es la base de la documentación oficial del
backend Java.

## Acuerdo de trabajo

- **Alcance:** las cuatro capas de `backend-java/` y el deploy (Docker, Caddy,
  VPS) que las corre. El backend Python (`backend/`) queda afuera.
- **Orden:** de adentro hacia afuera. Cada capa se apoya en la anterior.
- **Modo:** solo lectura y discusión. Durante la revisión no se escribe ni se
  modifica código, ni de producción ni de tests; lo único que se escribe es
  este material.
- **Nivel:** Java intermedio, conceptos (hexagonal, inyección de dependencias,
  Repository, TDD) ya conocidos. La teoría se omite y el foco está en cómo se
  aplican acá y por qué.
- **Código nuevo:** ninguno hasta que el usuario entienda qué hace. Ver la regla
  en [CLAUDE.md](../../CLAUDE.md).
- **Commits:** los hace el usuario. Claude deja los cambios en el working tree y
  propone el mensaje.
- **Preguntas:** Claude las hace con su herramienta de preguntas estructuradas,
  no como lista en prosa.

## Formato del material

- Texto en Markdown, en español, solo donde haga falta explicación escrita.
- Diagramas en PlantUML (`diagrams/*.puml`). El `.puml` es la fuente; el `.svg`
  se genera con `plantuml -tsvg docs/backend-java/diagrams/<archivo>.puml` y se
  versiona al lado para que el Markdown lo pueda mostrar.
- Artifacts (páginas web) solo para las partes que el usuario pida.

Cada lección sigue esta estructura, salteando las secciones que no apliquen:

1. **Qué resuelve:** el rol de la capa en el sistema.
2. **Recorrido:** los archivos en orden de lectura, con lo que hay que mirar en
   cada uno.
3. **Decisiones y por qué:** lo que se eligió, lo que se descartó y el motivo,
   enlazando el ADR cuando existe.
4. **Puntos débiles:** deudas, rarezas o riesgos encontrados durante la lectura.
   Se anotan, no se corrigen.
5. **Preguntas de repaso:** para comprobar que la capa quedó entendida.

## Lecciones

| # | Tema | Código | Estado |
|---|---|---|---|
| 00 | Panorama: qué es el sistema, por qué Java convive con Python, cómo los módulos Maven imponen la arquitectura | `backend-java/pom.xml`, [ADR 0011](../adr/0011-java-spring-backend.md) | Pendiente |
| 01 | Dominio | `backend-java/domain/` | Pendiente |
| 02 | Aplicación: casos de uso y puertos | `backend-java/application/` | Pendiente |
| 03 | Infraestructura: SQLite con JDBC | `backend-java/infrastructure/` | Pendiente |
| 04 | Adaptador REST: Spring Boot, errores, seguridad, cableado | `backend-java/adapter-rest/` | Pendiente |
| 05 | Deploy: Docker, Caddy, VPS | `deploy/`, [docs/deployment.md](../deployment.md) | Pendiente |
