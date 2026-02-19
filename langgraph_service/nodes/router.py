"""Router node — classifies the query to determine which data silo(s) to query.

Uses LLM-based classification with structured output. Falls back to "both"
if the LLM call fails or returns an invalid decision.
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import AzureChatOpenAI

from langgraph_service.config import settings
from langgraph_service.state import AgentState

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """You are a query router for a Hybrid Knowledge Synthesizer system.
Your job is to classify the user's query into one of three categories:

- "silo_a": The query is about internal engineering documentation, system architecture,
  ML pipelines, API design, or technical specifications.
- "silo_b": The query is about patents, external research, published innovations,
  or intellectual property.
- "both": The query requires comparing or synthesizing information from both
  internal engineering docs AND external patents/research.

Respond with ONLY one of: silo_a, silo_b, both
Do not include any other text."""

VALID_ROUTES = {"silo_a", "silo_b", "both"}


def _get_llm() -> AzureChatOpenAI | None:
    """Initialize Azure OpenAI LLM if configured."""
    if not settings.azure_openai_configured:
        return None
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_deployment_name,
        temperature=0,
        max_tokens=10,
    )


def router_node(state: AgentState) -> dict:
    """LangGraph node: classify the query into a routing decision.

    Falls back to "both" if:
    - Azure OpenAI is not configured
    - LLM returns an invalid route
    - Any exception occurs

    Returns:
        Updated state with route_decision.
    """
    query = state.get("query", "")
    if not query:
        logger.warning("Router received empty query, defaulting to 'both'")
        return {"route_decision": "both"}

    llm = _get_llm()
    if llm is None:
        logger.info("Azure OpenAI not configured, defaulting route to 'both'")
        return {"route_decision": "both"}

    try:
        response = llm.invoke([
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=query),
        ])
        decision = response.content.strip().lower()

        if decision not in VALID_ROUTES:
            logger.warning("Router returned invalid decision '%s', defaulting to 'both'", decision)
            return {"route_decision": "both"}

        logger.info("Router decision: %s for query: %s", decision, query[:80])
        return {"route_decision": decision}

    except Exception as e:
        logger.error("Router LLM call failed: %s", e)
        return {
            "route_decision": "both",
            "errors": [f"Router error: {e}"],
        }
