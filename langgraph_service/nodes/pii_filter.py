"""PII filter node — detects and sanitizes personally identifiable information.

GDPR compliance: prevents PII from being sent to external LLM/search APIs.
Detects: emails, phone numbers, credit cards, German Sozialversicherungsnummer.
"""

import re
import logging
from langgraph_service.state import AgentState

logger = logging.getLogger(__name__)

# Compiled regex patterns for PII detection
_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone_international": re.compile(r"\+?\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}"),
    "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    "german_ssn": re.compile(r"\b\d{2}\s?\d{6}\s?[A-Z]\s?\d{3}\b"),  # Sozialversicherungsnummer
    "iban_de": re.compile(r"\bDE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b", re.IGNORECASE),
}


def detect_pii(text: str) -> list[str]:
    """Detect PII types present in the input text.

    Args:
        text: Input string to scan for PII.

    Returns:
        List of PII type names detected (empty if clean).
    """
    detected: list[str] = []
    for pii_type, pattern in _PII_PATTERNS.items():
        if pattern.search(text):
            detected.append(pii_type)
    return detected


def sanitize_query(text: str) -> str:
    """Replace detected PII with redaction markers.

    Args:
        text: Input string potentially containing PII.

    Returns:
        Sanitized string with PII replaced by [REDACTED_<type>].
    """
    sanitized = text
    for pii_type, pattern in _PII_PATTERNS.items():
        sanitized = pattern.sub(f"[REDACTED_{pii_type.upper()}]", sanitized)
    return sanitized


def pii_filter_node(state: AgentState) -> dict:
    """LangGraph node: scans the query for PII and sanitizes if needed.

    Returns:
        Updated state with sanitized query and pii_detected flag.
    """
    query = state.get("query", "")
    if not query:
        return {"pii_detected": False}

    detected_types = detect_pii(query)

    if detected_types:
        logger.warning("PII detected in query: %s", detected_types)
        sanitized = sanitize_query(query)
        return {
            "query": sanitized,
            "pii_detected": True,
            "errors": [f"PII detected and redacted: {', '.join(detected_types)}"],
        }

    return {"pii_detected": False}
