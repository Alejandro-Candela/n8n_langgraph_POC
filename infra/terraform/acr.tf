# ============================================
# Azure Container Registry — Basic SKU
# ============================================
# Basic: ~€4.2/mo, 10GB storage, sufficient for POC.
# Admin disabled — image pull via Managed Identity + AcrPull RBAC.

resource "azurerm_container_registry" "poc" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.poc.name
  location            = azurerm_resource_group.poc.location
  sku                 = "Basic"
  admin_enabled       = false

  tags = local.common_tags
}
