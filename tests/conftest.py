"""Pytest fixtures shared across all test modules."""

import pytest

from langgraph_service.state import AgentState


@pytest.fixture
def empty_state() -> AgentState:
    """Return an empty AgentState for testing."""
    return {
        "messages": [],
        "query": "",
        "route_decision": "",
        "context_silo_a": "",
        "context_silo_b": "",
        "synthesized_answer": "",
        "sources": [],
        "errors": [],
        "pii_detected": False,
    }


@pytest.fixture
def sample_engineering_query() -> str:
    """Return a query that should route to Silo A (engineering docs)."""
    return "What is the architecture of our ML inference pipeline?"


@pytest.fixture
def sample_patent_query() -> str:
    """Return a query that should route to Silo B (patents)."""
    return "What recent patents exist for real-time audio classification on edge devices?"


@pytest.fixture
def sample_hybrid_query() -> str:
    """Return a query that should route to both silos."""
    return "How does our internal feature engineering compare to published patent approaches?"


@pytest.fixture
def state_with_eng_query(empty_state: AgentState, sample_engineering_query: str) -> AgentState:
    """Return a state with an engineering query pre-loaded."""
    empty_state["query"] = sample_engineering_query
    return empty_state


@pytest.fixture
def state_with_pii() -> AgentState:
    """Return a state with PII in the query."""
    return {
        "messages": [],
        "query": "My email is john.doe@company.com and my phone is +49 151 1234 5678",
        "route_decision": "",
        "context_silo_a": "",
        "context_silo_b": "",
        "synthesized_answer": "",
        "sources": [],
        "errors": [],
        "pii_detected": False,
    }
