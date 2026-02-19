"""LLM-as-a-Judge evaluation script for the Hybrid Knowledge Synthesizer.

Evaluates the RAG pipeline on two axes:
1. Contextual Relevancy: Is the retrieved context relevant to the query?
2. Groundedness: Is the answer grounded in the retrieved context?

Usage:
    uv run python scripts/evaluate_llm_judge.py
"""

import json
import logging
import sys
import time
from pathlib import Path

import httpx
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import AzureChatOpenAI

from langgraph_service.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

EVAL_DATA_FILE = Path(__file__).parent.parent / "data" / "evaluation_dataset.json"
LANGGRAPH_URL = "http://localhost:8000/invoke"

# Judge prompts
RELEVANCY_PROMPT = """You are evaluating the CONTEXTUAL RELEVANCY of a RAG system.
Given a user query and retrieved context, rate how relevant the context is to answering the query.

Score on a scale of 1-5:
1 = Completely irrelevant
2 = Mostly irrelevant
3 = Partially relevant
4 = Mostly relevant
5 = Highly relevant

Respond with ONLY a JSON object: {"score": <int>, "reasoning": "<brief explanation>"}"""

GROUNDEDNESS_PROMPT = """You are evaluating the GROUNDEDNESS of a RAG system.
Given retrieved context and a generated answer, rate how well the answer is supported by the context.

Score on a scale of 1-5:
1 = Fabricated, no support in context
2 = Mostly fabricated
3 = Partially grounded
4 = Mostly grounded
5 = Fully grounded in context

Respond with ONLY a JSON object: {"score": <int>, "reasoning": "<brief explanation>"}"""


def get_judge_llm() -> AzureChatOpenAI:
    """Initialize the judge LLM."""
    if not settings.azure_openai_configured:
        logger.error("❌ Azure OpenAI not configured for evaluation")
        sys.exit(1)
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_deployment_name,
        temperature=0,
        max_tokens=200,
    )


def invoke_pipeline(query: str) -> dict:
    """Call the LangGraph pipeline via HTTP.

    Args:
        query: User query to evaluate.

    Returns:
        Pipeline response dict.
    """
    response = httpx.post(LANGGRAPH_URL, json={"query": query}, timeout=60.0)
    response.raise_for_status()
    return response.json()


def judge_relevancy(llm: AzureChatOpenAI, query: str, context: str) -> dict:
    """Judge contextual relevancy of retrieved context.

    Args:
        llm: The judge LLM.
        query: Original user query.
        context: Retrieved context from the pipeline.

    Returns:
        Dict with score and reasoning.
    """
    prompt = f"Query: {query}\n\nRetrieved Context:\n{context}"
    response = llm.invoke([
        SystemMessage(content=RELEVANCY_PROMPT),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {"score": 0, "reasoning": f"Failed to parse judge response: {response.content}"}


def judge_groundedness(llm: AzureChatOpenAI, context: str, answer: str) -> dict:
    """Judge groundedness of the generated answer.

    Args:
        llm: The judge LLM.
        context: Retrieved context.
        answer: Generated answer from the pipeline.

    Returns:
        Dict with score and reasoning.
    """
    prompt = f"Context:\n{context}\n\nGenerated Answer:\n{answer}"
    response = llm.invoke([
        SystemMessage(content=GROUNDEDNESS_PROMPT),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {"score": 0, "reasoning": f"Failed to parse judge response: {response.content}"}


def main() -> None:
    """Run evaluation on the evaluation dataset."""
    if not EVAL_DATA_FILE.exists():
        logger.error("❌ Evaluation dataset not found: %s", EVAL_DATA_FILE)
        sys.exit(1)

    with open(EVAL_DATA_FILE) as f:
        eval_data = json.load(f)

    logger.info("📊 Starting evaluation with %d queries", len(eval_data))

    llm = get_judge_llm()
    results: list[dict] = []

    for i, item in enumerate(eval_data, 1):
        query = item["query"]
        logger.info("  [%d/%d] Evaluating: %s", i, len(eval_data), query[:60])

        try:
            # Call pipeline
            pipeline_result = invoke_pipeline(query)
            answer = pipeline_result.get("answer", "")
            route = pipeline_result.get("route_decision", "unknown")

            # Reconstruct context from sources
            context = f"Route: {route}\nSources: {', '.join(pipeline_result.get('sources', []))}"

            # Judge
            relevancy = judge_relevancy(llm, query, context)
            groundedness = judge_groundedness(llm, context, answer)

            result = {
                "query": query,
                "expected_route": item.get("expected_route"),
                "actual_route": route,
                "route_correct": route == item.get("expected_route"),
                "relevancy_score": relevancy.get("score", 0),
                "relevancy_reasoning": relevancy.get("reasoning", ""),
                "groundedness_score": groundedness.get("score", 0),
                "groundedness_reasoning": groundedness.get("reasoning", ""),
                "latency_ms": pipeline_result.get("latency_ms", 0),
            }
            results.append(result)

        except Exception as e:
            logger.error("  ❌ Failed: %s", e)
            results.append({"query": query, "error": str(e)})

        time.sleep(1)  # Rate limit respect

    # Summary
    valid_results = [r for r in results if "error" not in r]
    if valid_results:
        avg_relevancy = sum(r["relevancy_score"] for r in valid_results) / len(valid_results)
        avg_groundedness = sum(r["groundedness_score"] for r in valid_results) / len(valid_results)
        route_accuracy = sum(1 for r in valid_results if r["route_correct"]) / len(valid_results)
        avg_latency = sum(r["latency_ms"] for r in valid_results) / len(valid_results)

        logger.info("\n📊 EVALUATION RESULTS")
        logger.info("=" * 50)
        logger.info("  Queries evaluated:     %d", len(valid_results))
        logger.info("  Avg Relevancy:         %.1f/5", avg_relevancy)
        logger.info("  Avg Groundedness:      %.1f/5", avg_groundedness)
        logger.info("  Route Accuracy:        %.0f%%", route_accuracy * 100)
        logger.info("  Avg Latency:           %.0fms", avg_latency)
        logger.info("=" * 50)

    # Save detailed results
    output_file = Path(__file__).parent.parent / "reporting" / "evaluation_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump({"summary": {
            "total_queries": len(eval_data),
            "successful": len(valid_results),
            "avg_relevancy": round(avg_relevancy, 2) if valid_results else 0,
            "avg_groundedness": round(avg_groundedness, 2) if valid_results else 0,
            "route_accuracy": round(route_accuracy, 2) if valid_results else 0,
        }, "details": results}, f, indent=2)
    logger.info("📁 Detailed results saved to %s", output_file)


if __name__ == "__main__":
    main()
