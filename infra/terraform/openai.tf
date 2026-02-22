# ============================================
# Azure OpenAI — Account + Model Deployments
# ============================================

resource "azurerm_cognitive_account" "openai" {
  name                  = var.openai_account_name
  resource_group_name   = azurerm_resource_group.poc.name
  location              = var.location
  kind                  = "OpenAI"
  sku_name              = "S0" # Only SKU available for Azure OpenAI
  custom_subdomain_name = var.openai_account_name

  tags = local.common_tags

  lifecycle {
    prevent_destroy = true
  }
}

# ── gpt-4o-mini (Chat/Completion) ───────────────────
resource "azurerm_cognitive_deployment" "gpt4o_mini" {
  name                 = "gpt-4o-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }

  sku {
    name     = "Standard"
    capacity = 1 # Minimum TPM
  }
}

# ── text-embedding-ada-002 (Embeddings) ─────────────
resource "azurerm_cognitive_deployment" "embedding" {
  name                 = "text-embedding-ada-002"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-ada-002"
    version = "2"
  }

  sku {
    name     = "Standard"
    capacity = 1
  }

  depends_on = [azurerm_cognitive_deployment.gpt4o_mini]
}
