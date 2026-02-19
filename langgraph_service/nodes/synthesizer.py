"""Synthesizer node — merges RAG contexts and generates a unified answer.

Combines contexts from Silo A (Databricks) and Silo B (Azure) with source
attribution. Handles partial contexts gracefully (one silo failed).
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import AzureChatOpenAI

from langgraph_service.config import settings
from langgraph_service.state import AgentState

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM_PROMPT = """You are a Knowledge Synthesis Expert for a Hybrid Intelligence system.
You receive context from two data silos:

**Silo A (Internal Engineering Docs)**: Technical documentation, architecture specs,
ML pipeline designs, and engineering best practices from the organization.

**Silo B (External Patents/Research)**: Published patents, research papers,
and external innovations.

Your task is to:
1. Synthesize information from both silos into a coherent, actionable answer.
2. Highlight key comparisons or synergies between internal and external knowledge.
3. Always cite which silo (A or B) each piece of information comes from.
4. If only one silo has relevant data, acknowledge the gap and provide what's available.
5. Be precise, professional, and structured in your response.

Format your response with clear sections and bullet points where appropriate."""


def _get_llm() -> AzureChatOpenAI | None:
    """Initialize Azure OpenAI LLM if configured."""
    if not settings.azure_openai_configured:
        return None
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_deployment_name,
        temperature=0.3,
        max_tokens=1500,
    )


def _build_synthesis_prompt(query: str, context_a: str, context_b: str) -> str:
    """Build the synthesis prompt with both silo contexts.

    Args:
        query: Original user query.
        context_a: Context from Databricks (Silo A).
        context_b: Context from Azure (Silo B).

    Returns:
        Formatted prompt string.
    """
    parts = [f"## User Query\n{query}\n"]

    if context_a:
        parts.append(f"## Silo A — Internal Engineering Documentation\n{context_a}\n")
    else:
        parts.append("## Silo A — Internal Engineering Documentation\n*No data available.*\n")

    if context_b:
        parts.append(f"## Silo B — External Patents & Research\n{context_b}\n")
    else:
        parts.append("## Silo B — External Patents & Research\n*No data available.*\n")

    parts.append("## Instructions\nSynthesize the above into a comprehensive answer.")
    return "\n".join(parts)


def synthesizer_node(state: AgentState) -> dict:
    """LangGraph node: merge contexts from both silos and generate final answer.

    Falls back to a simple concatenation if the LLM is not available.

    Returns:
        Updated state with synthesized_answer.
    """
    query = state.get("query", "")
    context_a = state.get("context_silo_a", "")
    context_b = state.get("context_silo_b", "")

    if not context_a and not context_b:
        return {
            "synthesized_answer": "No relevant information found in either data silo.",
            "errors": ["Synthesizer: both silos returned empty context"],
        }

    llm = _get_llm()
    if llm is None:
        # Fallback: simple concatenation without LLM synthesis
        logger.info("Azure OpenAI not configured, returning raw concatenation")
        fallback_answer = f"## Query: {query}\n\n"
        if context_a:
            fallback_answer += f"### From Engineering Docs (Silo A)\n{context_a}\n\n"
        if context_b:
            fallback_answer += f"### From Patents (Silo B)\n{context_b}\n\n"
        return {"synthesized_answer": fallback_answer}

    try:
        prompt = _build_synthesis_prompt(query, context_a, context_b)
        response = llm.invoke([
            SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        logger.info("Synthesizer generated answer (%d chars)", len(response.content))
        return {"synthesized_answer": response.content}

    except Exception as e:
        logger.error("Synthesizer LLM call failed: %s", e)
        # Fallback to concatenation on error
        fallback = f"[Synthesis error — raw data follows]\n\n"
        if context_a:
            fallback += f"### Silo A\n{context_a}\n\n"
        if context_b:
            fallback += f"### Silo B\n{context_b}\n\n"
        return {
            "synthesized_answer": fallback,
            "errors": [f"Synthesizer error: {e}"],
        }
