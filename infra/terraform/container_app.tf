# ============================================
# Container Apps — Environment + App
# ============================================
# Consumption workload profile: scale-to-zero,
# pay only for active vCPU-seconds and memory.

resource "azurerm_container_app_environment" "poc" {
  name                       = local.container_env_name
  location                   = azurerm_resource_group.poc.location
  resource_group_name        = azurerm_resource_group.poc.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.poc.id

  # Consumption-only plan (no dedicated workload profiles)
  # = zero base cost when no containers are running.

  tags = local.common_tags
}

resource "azurerm_container_app" "langgraph" {
  name                         = var.container_app_name
  container_app_environment_id = azurerm_container_app_environment.poc.id
  resource_group_name          = azurerm_resource_group.poc.name
  revision_mode                = "Single"

  tags = local.common_tags

  # ── Managed Identity ─────────────────────────────
  identity {
    type = "SystemAssigned"
  }

  # ── ACR Pull via Managed Identity ────────────────
  registry {
    server   = azurerm_container_registry.poc.login_server
    identity = "System"
  }

  # ── Ingress ──────────────────────────────────────
  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  # ── Container Template ───────────────────────────
  template {
    min_replicas = 0
    max_replicas = 2

    container {
      name   = "langgraph-service"
      image  = local.container_image
      cpu    = 1.0
      memory = "2.0Gi"

      # ── Environment Variables (non-sensitive) ────
      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }

      env {
        name  = "AZURE_OPENAI_DEPLOYMENT_NAME"
        value = "gpt-4o-mini"
      }

      env {
        name  = "AZURE_OPENAI_API_VERSION"
        value = "2024-10-21"
      }

      env {
        name  = "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        value = "text-embedding-3-small"
      }

      env {
        name  = "AZURE_SEARCH_INDEX_NAME"
        value = "patents-index"
      }

      env {
        name  = "EMBEDDING_DIMENSIONS"
        value = "1536"
      }

      # ── Sensitive vars from Key Vault secrets ────
      env {
        name        = "AZURE_OPENAI_ENDPOINT"
        secret_name = "azure-openai-endpoint"
      }

      env {
        name        = "AZURE_OPENAI_API_KEY"
        secret_name = "azure-openai-api-key"
      }

      env {
        name        = "AZURE_SEARCH_ENDPOINT"
        secret_name = "azure-search-endpoint"
      }

      env {
        name        = "AZURE_SEARCH_API_KEY"
        secret_name = "azure-search-api-key"
      }

      env {
        name        = "AZURE_APP_INSIGHTS_CONNECTION_STRING"
        secret_name = "app-insights-connection-string"
      }

      # ── Health Probes ────────────────────────────
      liveness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 8000

        initial_delay    = 30
        interval_seconds = 30
        timeout          = 5
        failure_count_threshold = 3
      }

      readiness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 8000

        interval_seconds = 10
        timeout          = 3
        failure_count_threshold = 3
      }
    }
  }

  # ── Secrets (values populated after Key Vault is seeded) ──
  # These are Container App-level secrets; they reference
  # values you must set via `az containerapp secret set`
  # or via Key Vault references once secrets are seeded.
  secret {
    name  = "azure-openai-endpoint"
    value = "placeholder-set-via-cli-or-keyvault"
  }

  secret {
    name  = "azure-openai-api-key"
    value = "placeholder-set-via-cli-or-keyvault"
  }

  secret {
    name  = "azure-search-endpoint"
    value = "placeholder-set-via-cli-or-keyvault"
  }

  secret {
    name  = "azure-search-api-key"
    value = "placeholder-set-via-cli-or-keyvault"
  }

  secret {
    name  = "app-insights-connection-string"
    value = "placeholder-set-via-cli-or-keyvault"
  }

  lifecycle {
    # Secrets are managed out-of-band via CLI/CI after first apply.
    # Prevent Terraform from resetting them to placeholders.
    # ignore_changes = [
    #   secret,
    #   template[0].container[0].env,
    # ]
  }

  depends_on = [
    azurerm_container_app_environment.poc,
    azurerm_container_registry.poc,
  ]
}
