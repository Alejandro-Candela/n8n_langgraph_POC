"""Application configuration via environment variables.

Uses pydantic-settings to validate all required config at startup,
preventing runtime failures from missing credentials.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # --- LangSmith ---
    langsmith_api_key: str = ""
    langsmith_project: str = "hybrid-knowledge-synthesizer"
    langchain_tracing_v2: bool = False

    # --- Application ---
    log_level: str = "INFO"
    embedding_dimensions: int = 512

    @property
    def azure_openai_configured(self) -> bool:
        """Check if Azure OpenAI credentials are set."""
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)

    @property
    def azure_search_configured(self) -> bool:
        """Check if Azure AI Search credentials are set."""
        return bool(self.azure_search_endpoint and self.azure_search_api_key)

    @property
    def databricks_configured(self) -> bool:
        """Check if Databricks credentials are set."""
        return bool(self.databricks_host and self.databricks_token)

    @property
    def langsmith_configured(self) -> bool:
        """Check if LangSmith tracing is enabled."""
        return bool(self.langsmith_api_key and self.langchain_tracing_v2)


settings = Settings()
