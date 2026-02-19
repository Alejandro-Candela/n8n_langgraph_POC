"""Integration tests for the full graph and FastAPI endpoints."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from langgraph_service.server import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test the /health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "services" in data

    def test_health_lists_services(self, client):
        response = client.get("/health")
        services = response.json()["services"]
        assert "azure_openai" in services
        assert "azure_search" in services
        assert "databricks" in services
        assert "langsmith" in services


class TestGraphEndpoint:
    """Test the /graph debug endpoint."""

    def test_graph_returns_nodes(self, client):
        response = client.get("/graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert len(data["nodes"]) > 0


class TestInvokeEndpoint:
    """Test the /invoke endpoint with mocked external services."""

    @patch("langgraph_service.nodes.router.settings")
    @patch("langgraph_service.nodes.databricks_agent.settings")
    @patch("langgraph_service.nodes.azure_agent.settings")
    @patch("langgraph_service.nodes.synthesizer.settings")
    def test_invoke_with_mock_data(
        self, mock_synth, mock_azure, mock_db, mock_router, client
    ):
        """Test full pipeline with all external services mocked."""
        mock_router.azure_openai_configured = False
        mock_db.databricks_configured = False
        mock_azure.azure_search_configured = False
        mock_synth.azure_openai_configured = False

        response = client.post(
            "/invoke",
            json={"query": "What ML pipelines do we use?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "route_decision" in data
        assert "latency_ms" in data
        assert data["latency_ms"] > 0

    def test_invoke_empty_query_returns_422(self, client):
        """Test validation: empty query returns 422."""
        response = client.post("/invoke", json={"query": ""})
        assert response.status_code == 422

    def test_invoke_missing_query_returns_422(self, client):
        """Test validation: missing query field returns 422."""
        response = client.post("/invoke", json={})
        assert response.status_code == 422
