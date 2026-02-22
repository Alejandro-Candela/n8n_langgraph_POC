# ============================================
# Observability — Log Analytics + App Insights
# ============================================
# OpenTelemetry-compatible telemetry sink for the
# LangGraph service and future Azure-hosted workloads.

resource "azurerm_log_analytics_workspace" "poc" {
  name                = local.log_analytics_name
  location            = var.location
  resource_group_name = azurerm_resource_group.poc.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = local.common_tags
}

resource "azurerm_application_insights" "poc" {
  name                = local.app_insights_name
  location            = var.location
  resource_group_name = azurerm_resource_group.poc.name
  workspace_id        = azurerm_log_analytics_workspace.poc.id
  application_type    = "other" # Optimized for OpenTelemetry

  tags = local.common_tags
}
