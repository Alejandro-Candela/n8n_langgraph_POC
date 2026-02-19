# ── Stage 1: Build ──────────────────────────────────
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first (cache layer)
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

# Copy source code
COPY langgraph_service/ ./langgraph_service/

# ── Stage 2: Runtime ────────────────────────────────
FROM python:3.12-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY --from=builder /app/langgraph_service /app/langgraph_service

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "langgraph_service.server:app", "--host", "0.0.0.0", "--port", "8000"]
