"""FastAPI server — exposes the LangGraph agent as an HTTP API.

Endpoints:
    POST /invoke   — Execute the full RAG pipeline
    GET  /health   — Health check for Docker / load balancer
    GET  /graph    — Return the graph structure as JSON (debug)
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from langgraph_service.config import settings
from langgraph_service.graph import app_graph

# ── Logging setup ────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    logger.info("🚀 Hybrid Knowledge Synthesizer starting...")
    logger.info("  Azure OpenAI: %s", "✅ configured" if settings.azure_openai_configured else "❌ not configured")
    logger.info("  Azure Search: %s", "✅ configured" if settings.azure_search_configured else "❌ not configured")
    logger.info("  Databricks:   %s", "✅ configured" if settings.databricks_configured else "❌ not configured")
    logger.info("  LangSmith:    %s", "✅ enabled" if settings.langsmith_configured else "❌ disabled")
    yield
    logger.info("👋 Shutting down...")


# ── FastAPI app ──────────────────────────────────────
app = FastAPI(
    title="Hybrid Knowledge Synthesizer",
    description="Multi-agent LangGraph system for hybrid RAG across Databricks and Azure AI Search",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Request/Response models ──────────────────────────
class InvokeRequest(BaseModel):
    """Request body for the /invoke endpoint."""

    query: str = Field(
        ...,
        description="The user query to process through the hybrid RAG pipeline",
        min_length=1,
        max_length=2000,
        examples=["What ML pipeline architectures are used internally and how do they compare to recent patents?"],
    )


class InvokeResponse(BaseModel):
    """Response body from the /invoke endpoint."""

    answer: str = Field(description="Synthesized answer from the RAG pipeline")
    sources: list[str] = Field(default_factory=list, description="Source references for attribution")
    route_decision: str = Field(description="Which silo(s) were queried")
    pii_detected: bool = Field(default=False, description="Whether PII was detected and redacted")
    errors: list[str] = Field(default_factory=list, description="Non-fatal errors during processing")
    latency_ms: float = Field(description="Total processing time in milliseconds")


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str = "healthy"
    version: str = "0.1.0"
    services: dict[str, str] = Field(default_factory=dict)


# ── Endpoints ────────────────────────────────────────
@app.post("/invoke", response_model=InvokeResponse)
async def invoke_graph(request: InvokeRequest) -> InvokeResponse:
    """Execute the Hybrid Knowledge Synthesizer pipeline.

    Processes the user query through:
    1. PII filtering
    2. Query routing (Silo A, B, or Both)
    3. RAG retrieval from selected silo(s)
    4. Answer synthesis with source attribution
    """
    start_time = time.perf_counter()

    try:
        result: dict[str, Any] = app_graph.invoke({
            "query": request.query,
            "messages": [],
        })

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Pipeline completed in %.1fms | route=%s | sources=%d",
            latency_ms,
            result.get("route_decision", "unknown"),
            len(result.get("sources", [])),
        )

        return InvokeResponse(
            answer=result.get("synthesized_answer", "No answer generated"),
            sources=result.get("sources", []),
            route_decision=result.get("route_decision", "unknown"),
            pii_detected=result.get("pii_detected", False),
            errors=result.get("errors", []),
            latency_ms=round(latency_ms, 1),
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error("Pipeline failed after %.1fms: %s", latency_ms, e)
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {e}",
        ) from e


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for Docker and load balancers."""
    return HealthResponse(
        services={
            "azure_openai": "configured" if settings.azure_openai_configured else "not_configured",
            "azure_search": "configured" if settings.azure_search_configured else "not_configured",
            "databricks": "configured" if settings.databricks_configured else "not_configured",
            "langsmith": "enabled" if settings.langsmith_configured else "disabled",
        },
    )


@app.get("/graph")
async def get_graph_info() -> dict:
    """Return graph structure metadata for debugging."""
    return {
        "nodes": list(app_graph.nodes.keys()) if hasattr(app_graph, "nodes") else [],
        "description": "Hybrid Knowledge Synthesizer — Multi-agent RAG pipeline",
    }
