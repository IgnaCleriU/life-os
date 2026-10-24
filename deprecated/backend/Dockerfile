# Imagen de contenedor para el backend (FastAPI), usada por docker-compose en
# desarrollo y despliegue. Base pinneada a la versión mínima de requires-python.
FROM python:3.12-slim

# No escribir .pyc y salida sin buffer (logs inmediatos en el contenedor).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias primero para aprovechar la cache de capas.
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

# Usuario no-root para higiene mínima; /app/data queda escribible para el
# archivo SQLite (montado como volumen desde docker-compose).
RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown appuser:appuser /app/data
USER appuser

EXPOSE 8000

CMD ["uvicorn", "lifeos.adapters.rest.main:app", "--host", "0.0.0.0", "--port", "8000"]
