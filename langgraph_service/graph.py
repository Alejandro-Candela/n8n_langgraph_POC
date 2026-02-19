"""LangGraph StateGraph definition — the core orchestration brain.

Defines the full agentic RAG pipeline:
  PII Filter → Router → [Databricks Agent | Azure Agent] → Synthesizer

The Router uses conditional edges to determine which agent(s) to invoke.
When route_decision is "both", both agents run (sequentially in this version,
parallel fan-out planned for v0.2).
"""

import logging

from langgraph.graph import StateGraph, START, END

from langgraph_service.state import AgentState
from langgraph_service.nodes.pii_filter import pii_filter_node
from langgraph_service.nodes.router import router_node
from langgraph_service.nodes.databricks_agent import databricks_agent_node
from langgraph_service.nodes.azure_agent import azure_agent_node
from langgraph_service.nodes.synthesizer import synthesizer_node

logger = logging.getLogger(__name__)


def _route_decision(state: AgentState) -> str:
    """Conditional edge function: route based on the Router's decision.

    Args:
        state: Current graph state containing route_decision.

    Returns:
        Next node name(s) based on the routing classification.
    """
    decision = state.get("route_decision", "both")
    logger.info("Routing decision: %s", decision)

    if decision == "silo_a":
        return "silo_a_only"
    elif decision == "silo_b":
        return "silo_b_only"
    else:
        return "both_silos"


def build_graph() -> StateGraph:
    """Construct the Hybrid Knowledge Synthesizer StateGraph.

    Graph topology:
        START → pii_filter → router → [conditional routing]:
            - silo_a_only → databricks_agent → synthesizer → END
            - silo_b_only → azure_agent → synthesizer → END
            - both_silos → databricks_agent → azure_agent → synthesizer → END

    Returns:
        Compiled LangGraph StateGraph ready for invocation.
    """
    graph = StateGraph(AgentState)

    # ── Add nodes ────────────────────────────────────
    graph.add_node("pii_filter", pii_filter_node)
    graph.add_node("router", router_node)
    graph.add_node("databricks_agent", databricks_agent_node)
    graph.add_node("azure_agent", azure_agent_node)
    graph.add_node("synthesizer", synthesizer_node)

    # ── Entry edge ───────────────────────────────────
    graph.add_edge(START, "pii_filter")
    graph.add_edge("pii_filter", "router")

    # ── Conditional routing ──────────────────────────
    graph.add_conditional_edges(
        "router",
        _route_decision,
        {
            "silo_a_only": "databricks_agent",
            "silo_b_only": "azure_agent",
            "both_silos": "databricks_agent",  # Start with silo A, then B
        },
    )

    # ── Silo A only path ─────────────────────────────
    # After databricks_agent, check if we need azure too
    graph.add_conditional_edges(
        "databricks_agent",
        lambda state: "azure_agent" if state.get("route_decision") == "both" else "synthesizer",
        {
            "azure_agent": "azure_agent",
            "synthesizer": "synthesizer",
        },
    )

    # ── Silo B exit ──────────────────────────────────
    graph.add_edge("azure_agent", "synthesizer")

    # ── Terminal edge ────────────────────────────────
    graph.add_edge("synthesizer", END)

    logger.info("Graph compiled successfully")
    return graph.compile()


# Singleton compiled graph
app_graph = build_graph()
