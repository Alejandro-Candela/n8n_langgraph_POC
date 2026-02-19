"""Unit tests for PII filter node."""

import pytest
from langgraph_service.nodes.pii_filter import detect_pii, sanitize_query, pii_filter_node


class TestDetectPII:
    """Test PII detection patterns."""

    def test_detect_email(self):
        assert "email" in detect_pii("Contact me at user@example.com")

    def test_detect_phone_international(self):
        assert "phone_international" in detect_pii("Call +49 151 1234 5678")

    def test_detect_credit_card(self):
        assert "credit_card" in detect_pii("Card: 4111-1111-1111-1111")

    def test_detect_german_ssn(self):
        assert "german_ssn" in detect_pii("SSN: 12 345678 A 123")

    def test_detect_iban_de(self):
        assert "iban_de" in detect_pii("IBAN: DE89 3704 0044 0532 0130 00")

    def test_no_pii_in_clean_text(self):
        assert detect_pii("What is the ML pipeline architecture?") == []

    def test_multiple_pii_types(self):
        text = "Email: a@b.com, Phone: +49 151 1234 5678"
        detected = detect_pii(text)
        assert "email" in detected
        assert "phone_international" in detected


class TestSanitizeQuery:
    """Test PII sanitization."""

    def test_sanitize_email(self):
        result = sanitize_query("Contact user@example.com for details")
        assert "[REDACTED_EMAIL]" in result
        assert "user@example.com" not in result

    def test_sanitize_preserves_non_pii(self):
        result = sanitize_query("What is the architecture of our ML pipeline?")
        assert result == "What is the architecture of our ML pipeline?"


class TestPiiFilterNode:
    """Test the PII filter graph node."""

    def test_clean_query_no_detection(self, empty_state):
        empty_state["query"] = "What is vector search?"
        result = pii_filter_node(empty_state)
        assert result["pii_detected"] is False
        assert "query" not in result  # query unchanged

    def test_pii_query_detection_and_sanitization(self, state_with_pii):
        result = pii_filter_node(state_with_pii)
        assert result["pii_detected"] is True
        assert "[REDACTED_EMAIL]" in result["query"]
        assert "john.doe@company.com" not in result["query"]
        assert len(result["errors"]) > 0

    def test_empty_query(self, empty_state):
        result = pii_filter_node(empty_state)
        assert result["pii_detected"] is False
