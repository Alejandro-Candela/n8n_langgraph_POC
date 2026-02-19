# Hybrid Knowledge Synthesizer POC — Requirements

## Project Summary

Multi-agent RAG system solving the Data Silo Problem. Orchestrates queries across Databricks Vector Search (engineering docs) and Azure AI Search (patent docs) via a LangGraph graph exposed as a FastAPI microservice, triggered by n8n workflows.

## Functional Requirements

### FR-1: Query Routing

- System MUST classify incoming queries into: Silo A (Databricks), Silo B (Azure), or Both
- Router MUST use LLM-based classification with structured output
- Router MUST fallback to "both" on classification failure

### FR-2: Databricks RAG (Silo A)

- Agent MUST query Databricks Vector Search endpoint using `databricks-sdk`
- Agent MUST return top-k relevant document chunks (k=5 default)
- Agent MUST handle endpoint unavailability gracefully (mock fallback)

### FR-3: Azure RAG (Silo B)

- Agent MUST query Azure AI Search using `azure-search-documents`
- Agent MUST perform hybrid search (vector + keyword)
- Agent MUST apply PII filter before sending queries

### FR-4: Synthesis

- Synthesizer MUST merge contexts from both silos
- Synthesizer MUST include source attribution in the response
- Synthesizer MUST handle partial contexts (one silo failed)

### FR-5: n8n Orchestration

- n8n workflow MUST accept queries via Webhook
- n8n MUST call LangGraph FastAPI service
- n8n MUST handle errors with retry logic (Error Trigger nodes)
- n8n MUST format responses before delivery

### FR-6: PII Filtering

- System MUST detect emails, phone numbers, credit card numbers
- System MUST detect German-specific PII (Sozialversicherungsnummer)
- System MUST sanitize or reject queries containing PII

### FR-7: Observability

- System MUST emit LangSmith traces for every invocation
- Traces MUST show Router decisions, agent latencies, token usage

### FR-8: Evaluation

- System MUST provide an evaluation script with 10+ test questions
- Evaluation MUST measure Contextual Relevancy and Groundedness

## Non-Functional Requirements

### NFR-1: Cost

- Total cost MUST be $0 (using free tiers and trials only)
- System MUST document cost strategy per component

### NFR-2: Local-First

- Entire system MUST run locally via Docker Compose
- No cloud-hosted compute required (only cloud-hosted data stores)

### NFR-3: Reproducibility

- Infrastructure MUST be defined as code (Terraform + az CLI)
- Setup MUST be documented step-by-step in `doc/setup_guide.md`

### NFR-4: Test-First

- Every component MUST have unit tests before integration
- Tests MUST pass without cloud credentials (using mocks)

## Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Orchestration | n8n (Docker) | Free, visual workflows, webhook support |
| Agent Framework | LangGraph (Python) | Deterministic graphs, state management, LangSmith integration |
| API | FastAPI + Uvicorn | Async, fast, auto-docs, health checks |
| Vector DB (Silo A) | Databricks Vector Search | Enterprise-grade, 14-day trial |
| Vector DB (Silo B) | Azure AI Search (F0) | Free tier, hybrid search, Azure ecosystem |
| LLM | Azure OpenAI (gpt-4o-mini) | Quality + $200 free credits |
| Embeddings | Azure OpenAI (text-embedding-3-small) | Cheap, 512 dims sufficient for POC |
| Observability | LangSmith (Free Dev Tier) | 5,000 traces/month, LangGraph native |
| IaC | Terraform + az CLI | Cloud-agnostic + Azure-native options |
| Python Tooling | `uv` | Fast, modern, replaces pip/venv |
| Container | Docker Compose | Local multi-service orchestration |
