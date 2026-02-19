"""Azure AI Search Agent node — performs RAG against Azure AI Search (Silo B).

Queries the Azure AI Search index for patent/external research documents.
Uses hybrid search (vector + keyword) for better recall.
Gracefully degrades to mock data if the endpoint is unavailable.
"""

import logging
import time

from langgraph_service.config import settings
from langgraph_service.state import AgentState

logger = logging.getLogger(__name__)

# Mock data for development/testing when Azure is unavailable
_MOCK_CONTEXT = """[MOCK DATA - Azure AI Search unavailable]

Patent: US-2024-0112233 - Neural Architecture for Low-Latency Audio Classification
- A novel neural network architecture optimized for real-time audio event detection
  on edge devices. Uses depthwise separable convolutions with attention mechanisms.
- Claims improved accuracy over prior art by 12% while reducing inference time by 40%.

Patent: EP-3987654 - Distributed Feature Engineering Pipeline
- A system and method for distributed feature computation across heterogeneous
  data sources with automatic schema reconciliation.
- Key innovation: lazy materialization of feature vectors with caching at the
  serving layer to minimize computation during inference."""

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.5  # seconds


def _query_azure_search(query: str) -> tuple[str, list[str]]:
    """Query Azure AI Search index with hybrid search.

    Args:
        query: The search query string.

    Returns:
        Tuple of (context_text, source_references).

    Raises:
        Exception: If the query fails after all retries.
    """
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizedQuery
    from langchain_openai import AzureOpenAIEmbeddings

    # Initialize embeddings model
    embeddings_model = AzureOpenAIEmbeddings(
        azure_deployment=settings.azure_openai_embedding_deployment,
        openai_api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
    )

    search_client = SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Generate embedding for the query
            vector = embeddings_model.embed_query(query)

            # Hybrid search: combines keyword + vector search
            vector_query = VectorizedQuery(
                vector=vector,
                k_nearest_neighbors=5,
                fields="text_vector",
            )

            results = search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                top=5,
                select=["chunk", "title", "parent_id"],
            )

            context_parts: list[str] = []
            sources: list[str] = []
            for result in results:
                title = result.get("title", "Unknown Patent")
                chunk = result.get("chunk", "")
                parent_id = result.get("parent_id", "azure")
                context_parts.append(f"[{title}]: {chunk}")
                sources.append(f"Azure/{parent_id}/{title}")

            if not context_parts:
                return "No relevant patent documents found.", []

            return "\n\n".join(context_parts), sources

        except Exception as e:
            if attempt < MAX_RETRIES:
                wait_time = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "Azure Search query attempt %d/%d failed: %s. Retrying in %.1fs",
                    attempt, MAX_RETRIES, e, wait_time,
                )
                time.sleep(wait_time)
            else:
                raise


def azure_agent_node(state: AgentState) -> dict:
    """LangGraph node: query Azure AI Search for patent/research documents.

    Falls back to mock data if Azure is not configured or if the query fails.

    Returns:
        Updated state with context_silo_b and sources.
    """
    query = state.get("query", "")
    if not query:
        return {"context_silo_b": "", "errors": ["Azure agent received empty query"]}

    if not settings.azure_search_configured:
        logger.info("Azure AI Search not configured, using mock data")
        return {
            "context_silo_b": _MOCK_CONTEXT,
            "sources": ["[MOCK] Azure/US-2024-0112233/Neural Architecture",
                        "[MOCK] Azure/EP-3987654/Distributed Feature Engineering"],
        }

    try:
        context, sources = _query_azure_search(query)
        logger.info("Azure agent retrieved %d sources", len(sources))
        return {
            "context_silo_b": context,
            "sources": sources,
        }
    except Exception as e:
        logger.error("Azure agent failed: %s", e)
        return {
            "context_silo_b": _MOCK_CONTEXT,
            "sources": ["[MOCK/FALLBACK] Azure data"],
            "errors": [f"Azure agent error (using mock fallback): {e}"],
        }
