"""Unit tests for Router and Agent nodes (mocked external calls)."""

import pytest
from unittest.mock import patch, MagicMock

from langgraph_service.nodes.router import router_node, VALID_ROUTES
from langgraph_service.nodes.databricks_agent import databricks_agent_node
from langgraph_service.nodes.azure_agent import azure_agent_node
from langgraph_service.nodes.synthesizer import synthesizer_node


class TestRouterNode:
    """Test the Router node with mocked LLM."""

    def test_empty_query_defaults_to_both(self, empty_state):
        result = router_node(empty_state)
        assert result["route_decision"] == "both"

    @patch("langgraph_service.nodes.router.settings")
    def test_no_azure_defaults_to_both(self, mock_settings, state_with_eng_query):
        mock_settings.azure_openai_configured = False
        result = router_node(state_with_eng_query)
        assert result["route_decision"] == "both"

    @patch("langgraph_service.nodes.router._get_llm")
    def test_valid_silo_a_route(self, mock_get_llm, state_with_eng_query):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="silo_a")
        mock_get_llm.return_value = mock_llm
        result = router_node(state_with_eng_query)
        assert result["route_decision"] == "silo_a"

    @patch("langgraph_service.nodes.router._get_llm")
    def test_invalid_route_defaults_to_both(self, mock_get_llm, state_with_eng_query):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="invalid_route")
        mock_get_llm.return_value = mock_llm
        result = router_node(state_with_eng_query)
        assert result["route_decision"] == "both"

    @patch("langgraph_service.nodes.router._get_llm")
    def test_llm_exception_defaults_to_both(self, mock_get_llm, state_with_eng_query):
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API error")
        mock_get_llm.return_value = mock_llm
        result = router_node(state_with_eng_query)
        assert result["route_decision"] == "both"
        assert len(result.get("errors", [])) > 0


class TestDatabricksAgentNode:
    """Test the Databricks Agent node."""

    @patch("langgraph_service.nodes.databricks_agent.settings")
    def test_unconfigured_returns_mock(self, mock_settings, state_with_eng_query):
        mock_settings.databricks_configured = False
        result = databricks_agent_node(state_with_eng_query)
        assert "[MOCK DATA" in result["context_silo_a"]
        assert len(result["sources"]) > 0

    def test_empty_query_returns_error(self, empty_state):
        result = databricks_agent_node(empty_state)
        assert result["context_silo_a"] == ""
        assert len(result["errors"]) > 0


class TestAzureAgentNode:
    """Test the Azure Agent node."""

    @patch("langgraph_service.nodes.azure_agent.settings")
    def test_unconfigured_returns_mock(self, mock_settings, state_with_eng_query):
        mock_settings.azure_search_configured = False
        result = azure_agent_node(state_with_eng_query)
        assert "[MOCK DATA" in result["context_silo_b"]
        assert len(result["sources"]) > 0

    def test_empty_query_returns_error(self, empty_state):
        result = azure_agent_node(empty_state)
        assert result["context_silo_b"] == ""
        assert len(result["errors"]) > 0


class TestSynthesizerNode:
    """Test the Synthesizer node."""

    @patch("langgraph_service.nodes.synthesizer.settings")
    def test_no_context_returns_empty_message(self, mock_settings, empty_state):
        mock_settings.azure_openai_configured = False
        result = synthesizer_node(empty_state)
        assert "No relevant information" in result["synthesized_answer"]

    @patch("langgraph_service.nodes.synthesizer.settings")
    def test_fallback_concatenation_without_llm(self, mock_settings, empty_state):
        mock_settings.azure_openai_configured = False
        empty_state["query"] = "test query"
        empty_state["context_silo_a"] = "Engineering context"
        empty_state["context_silo_b"] = "Patent context"
        result = synthesizer_node(empty_state)
        assert "Engineering context" in result["synthesized_answer"]
        assert "Patent context" in result["synthesized_answer"]
