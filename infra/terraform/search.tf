# ============================================
# Azure AI Search (Free Tier F0)
# ============================================
# F0: 50MB storage, 3 indexes, no replicas.

resource "azurerm_search_service" "poc" {
  name                = var.search_service_name
  resource_group_name = azurerm_resource_group.poc.name
  location            = azurerm_resource_group.poc.location
  sku                 = "free"

  tags = local.common_tags
}
