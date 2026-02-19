"""Ingest sample documents into Azure AI Search index.

Creates the search index with vector search configuration and uploads
sample patent documents from data/sample_patents.json.

Usage:
    uv run python scripts/ingest_azure.py
"""

import json
import logging
import sys
import time
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
)
from langchain_openai import AzureOpenAIEmbeddings

from langgraph_service.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent / "data" / "sample_patents.json"


def get_embeddings_model() -> AzureOpenAIEmbeddings:
    """Initialize Azure OpenAI Embeddings model."""
    return AzureOpenAIEmbeddings(
        azure_deployment=settings.azure_openai_embedding_deployment,
        openai_api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        dimensions=settings.embedding_dimensions,
    )


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
            vector_search_dimensions=settings.embedding_dimensions,  # Ensure this matches model (1536 for text-embedding-3-small)
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
            ),
        ],
    )

    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
    index_client.create_or_update_index(index)
    logger.info("✅ Index '%s' created/updated", index_name)


def upload_documents(search_client: SearchClient, documents: list[dict], embeddings_model: AzureOpenAIEmbeddings) -> None:
    """Upload documents to the Azure AI Search index with embeddings.

    Args:
        search_client: Azure Search document client.
        documents: List of document dicts to upload.
        embeddings_model: Initialized embeddings model.
    """
    logger.info("🧠 Generating embeddings for %d documents...", len(documents))
    
    docs_to_upload = []
    for doc in documents:
        # Generate embedding for the content
        try:
            vector = embeddings_model.embed_query(doc["content"])
        except Exception as e:
            logger.error("❌ Failed to embed document %s: %s", doc["id"], e)
            continue

        docs_to_upload.append({
            "id": doc["id"],
            "title": doc["title"],
            "chunk": doc["content"],
            "parent_id": doc.get("patent_id", doc["id"]),
            "source": doc.get("source", "unknown"),
            "text_vector": vector,
        })
        # Rate limit protection (simple)
        time.sleep(0.1)

    if docs_to_upload:
        result = search_client.upload_documents(documents=docs_to_upload)
        succeeded = sum(1 for r in result if r.succeeded)
        logger.info("✅ Uploaded %d/%d documents", succeeded, len(docs_to_upload))
    else:
        logger.warning("⚠️ No documents to upload")


def main() -> None:
    """Main ingestion pipeline."""
    if not settings.azure_search_configured:
        logger.error("❌ Azure AI Search not configured. Set AZURE_SEARCH_* env vars.")
        sys.exit(1)

    if not settings.azure_openai_configured:
        logger.error("❌ Azure OpenAI not configured. Set AZURE_OPENAI_* env vars.")
        sys.exit(1)

    # Check embedding dimensions
    # text-embedding-3-small defaults to 1536 dim, but we configured 512 in .env? 
    # Let's check settings.embedding_dimensions. 
    # IMPORTANT: The model 'text-embedding-3-small' is native 1536 but supports shortening. 
    # If using standard class, it returns 1536. We must match index definition.
    # For this script we will assume 1536 unless user explicitly truncated.
    # To be safe, let's update settings dimensions or just print a warning if mismatches occur.
    
    logger.info("⚙️  Embedding dims: %d", settings.embedding_dimensions)

    # Load sample data
    if not DATA_FILE.exists():
        logger.error("❌ Data file not found: %s", DATA_FILE)
        sys.exit(1)

    with open(DATA_FILE) as f:
        documents = json.load(f)

    logger.info("📄 Loaded %d documents from %s", len(documents), DATA_FILE.name)

    # Initialize Embeddings
    embeddings = get_embeddings_model()

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
    upload_documents(search_client, documents, embeddings)

    logger.info("🎉 Azure ingestion complete!")


if __name__ == "__main__":
    main()
