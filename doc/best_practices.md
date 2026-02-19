# Best Practices Reference for AI Agents

This document is intended to be read by AI agents working on tasks in this project. It consolidates patterns, anti-patterns, and conventions extracted from research and `.agent/rules/`.

## LangGraph Patterns

### State Management

- **ALWAYS** use `TypedDict` with `Annotated` reducers for shared state
- **ALWAYS** return partial state updates from nodes (never the full state)
- **ALWAYS** use `add_messages` reducer for the messages field
- **NEVER** create a monolithic state — keep fields focused per agent responsibility
- Use `operator.add` for list accumulation, custom `merge_dicts` for dict merging

### Graph Construction

- **ALWAYS** add exit conditions to prevent infinite loops (max iterations counter)
- **ALWAYS** use `conditional_edges` for routing decisions
- **ALWAYS** compile the graph before use
- Use `START` and `END` constants from `langgraph.graph`
- For parallel execution, add multiple edges from the router to different agents

### Error Handling

- **NEVER** let exceptions propagate unhandled from nodes
- **ALWAYS** catch exceptions in each node and append to `errors` list in state
- **ALWAYS** implement timeout logic for external API calls
- Use exponential backoff for retries (3 attempts max)

### Anti-Patterns (from `.agent/rules/langgraph/SKILL.md`)

- ❌ Infinite loops without exit conditions
- ❌ Stateless nodes (loses LangGraph's benefits)
- ❌ Giant monolithic state (hard to reason about)
- ❌ Using `eval()` or dynamic code execution

## n8n Workflow Patterns

### Node Types (from `.agent/rules/n8n-mcp-tools-expert/SKILL.md`)

- Use `nodes-base.*` prefix for search/validate tools
- Use `n8n-nodes-base.*` prefix for workflow creation tools
- **ALWAYS** specify validation profile explicitly (`profile: "runtime"`)
- **ALWAYS** include `intent` parameter in workflow updates

### Error Handling

- **ALWAYS** use Error Trigger nodes for failure handling
- **NEVER** connect nodes with simple arrows for critical paths
- Implement retry logic on HTTP Request nodes (3 retries, exponential backoff)
- Use the IF node to check HTTP status codes before processing responses

### Workflow Building

- Build workflows iteratively (not one-shot)
- Validate after every significant change
- Activate only after full validation

## Azure AI Search Patterns

### Index Design

- Use HNSW algorithm for vector search (default, good balance of speed/accuracy)
- Set `vector_search_dimensions` to match your embedding model (512 for text-embedding-3-small)
- Use `keyword` analyzer for ID fields
- Mark `chunk` fields as not sortable, not filterable, not facetable

### SDK Usage

- Use `azure-search-documents` Python SDK
- Use `AzureKeyCredential` for authentication (simpler for POC)
- Use `DefaultAzureCredential` for production (more secure)
- Import from `azure.search.documents.indexes.models` for index creation
- Import from `azure.search.documents` for querying

## Databricks Vector Search Patterns

### Index Types

- Use `DIRECT_ACCESS` for this POC (simpler, no Delta Table dependency)
- Use `query_index` API with `query_text` for semantic search
- Set `num_results=5` for top-k retrieval

### SDK Usage

- Use `databricks-sdk` Python SDK
- Authenticate via `DATABRICKS_HOST` and `DATABRICKS_TOKEN` env vars
- Use `WorkspaceClient()` for simplified authentication

## Python Conventions

### Package Management

- **ALWAYS** use `uv` — never `pip`
- Run scripts via `uv run python script.py`
- Run tests via `uv run pytest`
- Add dependencies via `uv add package-name`

### Code Style

- **ALWAYS** use type hints on all function signatures
- **ALWAYS** write docstrings for all public functions
- **ALWAYS** use `pydantic.BaseSettings` for configuration
- **ALWAYS** use `python-dotenv` for env var loading
- Follow PEP 8 naming conventions

### Testing

- Use `pytest` with `conftest.py` fixtures
- Mock external services (Azure, Databricks, LLM calls)
- Unit tests require no network access
- Integration tests may use Docker services

## Security Conventions (GDPR/PII)

- **NEVER** log raw user queries containing PII
- **ALWAYS** apply PII filter before sending to external APIs
- **NEVER** hardcode credentials — use `.env` files
- **ALWAYS** document PII handling in architecture docs
- Detect: emails, phone numbers, credit cards, German Sozialversicherungsnummer
