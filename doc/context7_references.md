# Context7 Library References for AI Agents

Use these Context7-compatible library IDs with the `mcp_context7-mcp_query-docs` tool to look up official documentation during development.

## Primary Libraries

| Library | Context7 ID | Snippets | Use For |
|---------|------------|----------|---------|
| LangGraph (Python docs) | `/websites/langchain_oss_python_langgraph` | 900 | StateGraph, nodes, edges, RAG patterns |
| LangGraph (GitHub) | `/langchain-ai/langgraph` | 234 | Source code reference, latest APIs |
| Azure AI Search | `/websites/learn_microsoft_en-us_azure_search` | 11,286 | Index creation, vector search, skillsets |
| Azure AI Docs | `/microsoftdocs/azure-ai-docs` | 34,624 | AI Foundry, OpenAI, Cognitive Services |
| Databricks SDK (Python) | `/databricks/databricks-sdk-py` | 5,754 | Vector Search endpoints, index management |
| Databricks API | `/websites/databricks_api` | 3,676 | REST API reference |

## Example Queries

```
# LangGraph multi-agent pattern
query-docs(libraryId="/websites/langchain_oss_python_langgraph", query="multi-agent graph conditional routing TypedDict state")

# Azure AI Search index creation
query-docs(libraryId="/websites/learn_microsoft_en-us_azure_search", query="create search index vector fields Python SDK free tier")

# Databricks Vector Search
query-docs(libraryId="/databricks/databricks-sdk-py", query="vector search index creation endpoint query Python")
```

## Recommendations

- **Start with official docs** library (higher snippet count = better coverage)
- Use **specific queries** ("How to create vector search index with HNSW") over vague ones ("vector search")
- **Max 3 calls per question** — if info isn't found, use the best available result
