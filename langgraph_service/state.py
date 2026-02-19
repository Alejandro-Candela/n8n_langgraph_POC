"""Agent state definition for the Hybrid Knowledge Synthesizer graph.

Uses TypedDict with Annotated reducers for proper state management:
- Messages use add_messages reducer (append-only)
- Errors use operator.add (accumulate)
- Other fields overwrite (no reducer)
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared state across all nodes in the LangGraph.

    Fields:
        messages: Conversation history (append-only via add_messages reducer).
        query: Extracted user query string.
        route_decision: Router output — "silo_a", "silo_b", or "both".
        context_silo_a: Retrieved context from Databricks Vector Search.
        context_silo_b: Retrieved context from Azure AI Search.
        synthesized_answer: Final merged response from the Synthesizer.
        sources: List of source references for attribution.
        errors: Accumulated error messages from any node.
        pii_detected: Whether PII was detected in the query.
    """

    messages: Annotated[list, add_messages]
    query: str
    route_decision: str
    context_silo_a: str
    context_silo_b: str
    synthesized_answer: str
    sources: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]
    pii_detected: bool
