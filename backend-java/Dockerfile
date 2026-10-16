# Imagen del backend Java (Spring Boot, ADR 0011/0012). Contexto de build:
# backend-java/. Dos etapas: se compila con el JDK y se corre solo con el JRE.

FROM eclipse-temurin:21-jdk AS build
WORKDIR /build

# Primero lo que cambia poco (wrapper y POMs) para aprovechar la cache de capas.
COPY .mvn .mvn
COPY mvnw pom.xml ./
COPY domain/pom.xml domain/pom.xml
COPY application/pom.xml application/pom.xml
COPY infrastructure/pom.xml infrastructure/pom.xml
COPY adapter-rest/pom.xml adapter-rest/pom.xml
RUN ./mvnw -B -q dependency:go-offline -pl adapter-rest -am || true

COPY domain domain
COPY application application
COPY infrastructure infrastructure
COPY adapter-rest adapter-rest
RUN ./mvnw -B -DskipTests -pl adapter-rest -am package \
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
