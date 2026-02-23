# ============================================
# Dockerfile — Hybrid Knowledge Synthesizer
# ============================================
# Multi-stage build: build deps with uv, run as
# non-root user with minimal attack surface.
#
# Build:  docker build -t langgraph-service .
# Run:    docker run -p 8000:8000 --env-file .env langgraph-service
# ============================================

# ── Stage 1: Build ──────────────────────────────────
FROM ghcr.io/astral-sh/uv:0.6.3 AS uv
FROM python:3.12.8-slim AS builder

# Copy pinned uv binary from explicit version
COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY langgraph_service/ ./langgraph_service/

# ── Stage 2: Runtime ────────────────────────────────
FROM python:3.12.8-slim

LABEL org.opencontainers.image.source="https://github.com/Alejandro-Candela/n8n_langgraph_POC"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.description="Multi-agent LangGraph RAG service"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Create non-root user
RUN groupadd --system app && \
    useradd --system --gid app --no-create-home app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy source code
COPY --from=builder --chown=app:app /app/langgraph_service /app/langgraph_service

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Switch to non-root user
USER app

# Healthcheck using Python stdlib (no curl dependency)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "langgraph_service.server:app", "--host", "0.0.0.0", "--port", "8000"]
