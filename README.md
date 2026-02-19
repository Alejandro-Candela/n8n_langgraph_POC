# Hybrid Knowledge Synthesizer — POC

> **Multi-agent RAG system** that synthesizes knowledge from internal engineering docs (Databricks Vector Search) and external patents (Azure AI Search), orchestrated by n8n.

## Architecture

```
┌──────────┐     HTTP      ┌──────────────────────────────────┐
│   n8n    │ ───────────▶  │   LangGraph FastAPI Service      │
│ (UI/Orch)│               │                                  │
│ port:5678│  ◀────────── │  PII Filter                      │
└──────────┘   Response    │     ↓                            │
                           │  Router (LLM classification)     │
                           │     ↓                            │
                           │  ┌──────────┐  ┌──────────┐     │
                           │  │Databricks│  │  Azure    │     │
                           │  │ Agent    │  │  Agent    │     │
                           │  │(Silo A)  │  │(Silo B)  │     │
                           │  └────┬─────┘  └────┬─────┘     │
                           │       └──────┬──────┘           │
                           │         Synthesizer              │
                           │         (Final answer)           │
                           │  port:8000                       │
                           └──────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd n8n_langgraph_POC
cp .env.example .env
# Edit .env with your credentials
```

### 2. Install Python dependencies (for local dev)

```bash
uv sync
```

### 3. Run tests

```bash
uv run pytest -v --tb=short
```

### 4. Start services

```bash
docker compose up --build
```

- **n8n**: <http://localhost:5678>
- **LangGraph API**: <http://localhost:8000>
- **Health check**: <http://localhost:8000/health>

### 5. Test the pipeline

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"query": "What ML pipelines do we use?"}'
```

## Project Structure

```
n8n_langgraph_POC/
├── langgraph_service/          # LangGraph FastAPI service
│   ├── nodes/                  # Graph nodes
│   │   ├── pii_filter.py       # PII detection & sanitization
│   │   ├── router.py           # Query classification
│   │   ├── databricks_agent.py # Silo A: engineering docs
│   │   ├── azure_agent.py      # Silo B: patents
│   │   └── synthesizer.py      # Context merging & answer
│   ├── state.py                # AgentState (TypedDict)
│   ├── graph.py                # StateGraph definition
│   ├── config.py               # Settings (pydantic-settings)
│   └── server.py               # FastAPI endpoints
├── infra/
│   ├── terraform/              # Primary IaC (Azure resources)
│   └── az-cli/                 # Quick-start alternative
├── scripts/
│   ├── ingest_azure.py         # Upload docs to Azure AI Search
│   └── evaluate_llm_judge.py   # LLM-as-a-Judge evaluation
├── data/                       # Sample documents & eval dataset
├── tests/                      # pytest suite
├── doc/                        # Requirements, best practices
├── reporting/                  # Evaluation results, weekly logs
├── docker-compose.yaml
├── Dockerfile
└── pyproject.toml
```

## Zero-Cost Strategy

| Component | Free Tier / Strategy |
|---|---|
| n8n | Self-hosted via Docker (free) |
| LangGraph | Local Python (free) |
| Azure AI Search | Free F0 tier (50MB, 3 indexes) |
| Azure OpenAI | $200 free trial credits |
| Databricks | 14-day Community Edition trial |
| LangSmith | Free tier (5K traces/month) |

## Tech Stack

- **Orchestration**: LangGraph + FastAPI
- **LLM**: Azure OpenAI gpt-4o-mini
- **Embeddings**: text-embedding-3-small (512 dims)
- **Vector Search**: Databricks Vector Search + Azure AI Search
- **Workflow**: n8n (webhooks, chat interface)
- **IaC**: Terraform (primary) + az CLI (alternative)
- **Observability**: LangSmith tracing
- **Evaluation**: LLM-as-a-Judge

## License

MIT
