# syntax=docker/dockerfile:1
# Imagen del backend Java (Spring Boot, ADR 0011) con la web incluida.
# Contexto de build: la raíz del repo (necesita frontend/ y backend-java/).
# Tres etapas: la web con Node, el jar con el JDK y se corre solo con el JRE.

FROM node:22 AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM eclipse-temurin:21-jdk AS build
WORKDIR /build

# Primero lo que cambia poco (wrapper y POMs); el repositorio Maven se cachea
# con un cache mount en el paso de package.
COPY backend-java/.mvn .mvn
COPY backend-java/mvnw backend-java/pom.xml ./
COPY backend-java/domain/pom.xml domain/pom.xml
COPY backend-java/application/pom.xml application/pom.xml
COPY backend-java/infrastructure/pom.xml infrastructure/pom.xml
COPY backend-java/adapter-rest/pom.xml adapter-rest/pom.xml

COPY backend-java/domain domain
COPY backend-java/application application
COPY backend-java/infrastructure infrastructure
COPY backend-java/adapter-rest adapter-rest
# La web llega ya armada desde la etapa anterior: Maven la empaqueta como un
# recurso más (static/app/) y no ejecuta npm.
COPY --from=web /web/dist adapter-rest/src/main/resources/static/app
RUN --mount=type=cache,target=/root/.m2 ./mvnw -B -DskipTests -pl adapter-rest -am package \
    && cp adapter-rest/target/lifeos-adapter-rest-*.jar /build/app.jar

FROM eclipse-temurin:21-jre
WORKDIR /app

# Usuario no-root; /app/data queda escribible para el archivo SQLite (montado
# como volumen `lifeos-data` desde docker-compose, el mismo que usa Python).
# El uid 1000 es el mismo que le toca a appuser en la imagen de Python: el
# volumen compartido tiene un solo dueño. La imagen base trae un usuario
# `ubuntu` con ese uid, que se descarta.
RUN (userdel -r ubuntu 2>/dev/null || true) \
    && useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/data \
    && chown appuser:appuser /app/data
COPY --from=build /build/app.jar /app/app.jar
USER appuser

# Dentro del contenedor hay que escuchar en todas las interfaces para que el
# puerto publicado llegue. La exposición real la decide compose: en un VPS se
# publica solo en 127.0.0.1 del host.
ENV LIFEOS_BIND_ADDRESS=0.0.0.0 \
    DATABASE_URL=sqlite:////app/data/lifeos.db

EXPOSE 8000

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
