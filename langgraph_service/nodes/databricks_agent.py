"""Databricks Agent node — performs RAG against Databricks Vector Search (Silo A).

Queries the Databricks Vector Search endpoint for engineering documentation.
Gracefully degrades to mock data if the endpoint is unavailable.
"""

import logging
import time

from langgraph_service.config import settings
from langgraph_service.state import AgentState

logger = logging.getLogger(__name__)

# Mock data for development/testing when Databricks is unavailable
_MOCK_CONTEXT = """[MOCK DATA - Databricks Vector Search unavailable]

Engineering Document: ML Pipeline Architecture v2.3
- The system uses a modular pipeline with separate stages for data ingestion,
  feature engineering, model training, and inference serving.
- Real-time inference is handled via a gRPC endpoint with <50ms p99 latency.
- Model artifacts are versioned in MLflow and deployed via Databricks Model Serving.

Engineering Document: Signal Processing Module
- The DSP module implements a custom FFT-based approach for audio feature extraction.
- Supports sampling rates from 8kHz to 48kHz with configurable window sizes.
- Integrates with the ML pipeline via Apache Kafka for streaming inference."""

MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 1.5  # seconds


def _query_databricks_vector_search(query: str) -> tuple[str, list[str]]:
    """Query Databricks Vector Search endpoint.

    Args:
        query: The search query string.

    Returns:
        Tuple of (context_text, source_references).

    Raises:
        Exception: If the query fails after all retries.
    """
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.config import Config

    cfg = Config(
        host=settings.databricks_host,
        token=settings.databricks_token,
    )
    # Override the default 300s timeout to fail fast on unreachable hosts
    w = WorkspaceClient(config=cfg)
    w.config.http_timeout_seconds = settings.databricks_timeout_seconds

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            results = w.vector_search_indexes.query_index(
                index_name=settings.databricks_vs_index_name,
                columns=["content", "title", "source"],
                query_text=query,
                num_results=5,
            )

            if not results.result or not results.result.data_array:
                return "No relevant engineering documents found.", []

            context_parts: list[str] = []
            sources: list[str] = []
            for row in results.result.data_array:
                title = row[1] if len(row) > 1 else "Unknown"
                content = row[0] if len(row) > 0 else ""
                source = row[2] if len(row) > 2 else "databricks"
                context_parts.append(f"[{title}]: {content}")
                sources.append(f"Databricks/{source}/{title}")

            return "\n\n".join(context_parts), sources

        except Exception as e:
            if attempt < MAX_RETRIES:
                wait_time = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "Databricks query attempt %d/%d failed: %s. Retrying in %.1fs",
                    attempt, MAX_RETRIES, e, wait_time,
                )
                time.sleep(wait_time)
            else:
                raise


def databricks_agent_node(state: AgentState) -> dict:
    """LangGraph node: query Databricks Vector Search for engineering docs.

    Falls back to mock data if Databricks is not configured or if the query fails.

    Returns:
        Updated state with context_silo_a and sources.
    """
    query = state.get("query", "")
    if not query:
        return {"context_silo_a": "", "errors": ["Databricks agent received empty query"]}

    if not settings.databricks_configured:
        logger.info("Databricks not configured, using mock data")
        return {
            "context_silo_a": _MOCK_CONTEXT,
            "sources": ["[MOCK] Databricks/ML Pipeline Architecture v2.3",
                        "[MOCK] Databricks/Signal Processing Module"],
        }

    try:
        context, sources = _query_databricks_vector_search(query)
        logger.info("Databricks agent retrieved %d sources", len(sources))
        return {
            "context_silo_a": context,
            "sources": sources,
        }
    except Exception as e:
        logger.error("Databricks agent failed: %s", e)
        return {
            "context_silo_a": _MOCK_CONTEXT,
            "sources": ["[MOCK/FALLBACK] Databricks data"],
            "errors": [f"Databricks agent error (using mock fallback): {e}"],
        }
