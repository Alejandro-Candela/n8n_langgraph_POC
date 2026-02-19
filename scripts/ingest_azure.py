"""Ingest sample documents into Azure AI Search index.

Creates the search index with vector search configuration and uploads
sample patent documents from data/sample_patents.json.

Usage:
    uv run python scripts/ingest_azure.py
"""

import json
import logging
import sys
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
)

from langgraph_service.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent / "data" / "sample_patents.json"


def create_index(index_client: SearchIndexClient, index_name: str) -> None:
    """Create the Azure AI Search index with vector search configuration.

    Args:
        index_client: Azure Search index management client.
        index_name: Name of the index to create.
    """
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="chunk", type=SearchFieldDataType.String),
        SimpleField(name="parent_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SearchField(
            name="text_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=settings.embedding_dimensions,
            vector_search_profile_name="myHnswProfile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="myHnsw"),
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
                vectorizer_name="myOpenAI",
            ),
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="myOpenAI",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=settings.azure_openai_endpoint.rstrip("/"),
                    deployment_name=settings.azure_openai_embedding_deployment,
                    model_name=settings.azure_openai_embedding_deployment,
                    api_key=settings.azure_openai_api_key,
                ),
            ),
        ],
    )

    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
    index_client.create_or_update_index(index)
    logger.info("✅ Index '%s' created/updated", index_name)


def upload_documents(search_client: SearchClient, documents: list[dict]) -> None:
    """Upload documents to the Azure AI Search index.

    Args:
        search_client: Azure Search document client.
        documents: List of document dicts to upload.
    """
    # Transform to index schema
    docs_to_upload = []
    for doc in documents:
        docs_to_upload.append({
            "id": doc["id"],
            "title": doc["title"],
            "chunk": doc["content"],
            "parent_id": doc.get("patent_id", doc["id"]),
            "source": doc.get("source", "unknown"),
        })

    result = search_client.upload_documents(documents=docs_to_upload)
    succeeded = sum(1 for r in result if r.succeeded)
    logger.info("✅ Uploaded %d/%d documents", succeeded, len(docs_to_upload))


def main() -> None:
    """Main ingestion pipeline."""
    if not settings.azure_search_configured:
        logger.error("❌ Azure AI Search not configured. Set AZURE_SEARCH_* env vars.")
        sys.exit(1)

    if not settings.azure_openai_configured:
        logger.error("❌ Azure OpenAI not configured. Set AZURE_OPENAI_* env vars.")
        sys.exit(1)

    # Load sample data
    if not DATA_FILE.exists():
        logger.error("❌ Data file not found: %s", DATA_FILE)
        sys.exit(1)

    with open(DATA_FILE) as f:
        documents = json.load(f)

    logger.info("📄 Loaded %d documents from %s", len(documents), DATA_FILE.name)

    # Create index
    credential = AzureKeyCredential(settings.azure_search_api_key)
    index_client = SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=credential,
    )
    create_index(index_client, settings.azure_search_index_name)

    # Upload documents
    search_client = SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=credential,
    )
    upload_documents(search_client, documents)

    logger.info("🎉 Azure ingestion complete!")


if __name__ == "__main__":
    main()
