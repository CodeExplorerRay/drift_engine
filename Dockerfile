FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md* /app/
COPY config /app/config
COPY drift_engine /app/drift_engine
COPY alembic /app/alembic
COPY --from=frontend-build /drift_engine/api/static/dashboard /app/drift_engine/api/static/dashboard

RUN pip install --upgrade pip \
    && pip install .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/health/live || exit 1

CMD ["uvicorn", "drift_engine.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
