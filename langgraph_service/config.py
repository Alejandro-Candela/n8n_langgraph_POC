"""Application configuration via environment variables.

Uses pydantic-settings to validate all required config at startup,
preventing runtime failures from missing credentials.
"""

import re

from pydantic_settings import BaseSettings, SettingsConfigDict

# Patterns that indicate a value is a placeholder, not a real credential
_PLACEHOLDER_RE = re.compile(
    r"(your[-_]|changeme|replace[-_]?me|TODO|FIXME|example\.com|placeholder)",
    re.IGNORECASE,
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Azure OpenAI ---
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment_name: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    azure_openai_api_version: str = "2024-10-21"

    # --- Azure AI Search ---
    azure_search_endpoint: str = ""
    azure_search_api_key: str = ""
    azure_search_index_name: str = "patents-index"

    # --- Databricks ---
    databricks_host: str = ""
    databricks_token: str = ""
    databricks_vs_endpoint_name: str = ""
    databricks_vs_index_name: str = ""
    databricks_timeout_seconds: int = 30  # Per-request timeout (was SDK default: 300s)

    # --- Observability ---
    azure_app_insights_connection_string: str | None = None
    langsmith_api_key: str | None = None
    langsmith_project: str = "hybrid-knowledge-synthesizer"
    langchain_tracing_v2: bool = False

    # --- Application ---
    log_level: str = "INFO"
    embedding_dimensions: int = 512

    @staticmethod
    def _is_real_value(value: str) -> bool:
        """Return True only if the value is non-empty and not a placeholder."""
        return bool(value) and not _PLACEHOLDER_RE.search(value)

    @property
    def azure_openai_configured(self) -> bool:
        """Check if Azure OpenAI credentials are real (not placeholders)."""
        return self._is_real_value(self.azure_openai_endpoint) and self._is_real_value(self.azure_openai_api_key)

    @property
    def azure_search_configured(self) -> bool:
        """Check if Azure AI Search credentials are real (not placeholders)."""
        return self._is_real_value(self.azure_search_endpoint) and self._is_real_value(self.azure_search_api_key)

    @property
    def databricks_configured(self) -> bool:
        """Check if Databricks credentials are real (not placeholders)."""
        return self._is_real_value(self.databricks_host) and self._is_real_value(self.databricks_token)

    @property
    def langsmith_configured(self) -> bool:
        """Check if LangSmith tracing is enabled."""
        return bool(self.langsmith_api_key and self.langchain_tracing_v2)


settings = Settings()
