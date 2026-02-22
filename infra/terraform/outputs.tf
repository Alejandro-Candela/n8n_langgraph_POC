# ============================================
# Outputs — For downstream CI/CD and .env
# ============================================

output "search_endpoint" {
  value       = "https://${azurerm_search_service.poc.name}.search.windows.net"
  description = "Azure AI Search endpoint URL"
}

output "search_admin_key" {
  value       = azurerm_search_service.poc.primary_key
  sensitive   = true
  description = "Azure AI Search admin API key"
}

output "openai_endpoint" {
  value       = azurerm_cognitive_account.openai.endpoint
  description = "Azure OpenAI endpoint URL"
}

output "openai_key" {
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
  description = "Azure OpenAI API key"
}

output "app_insights_connection_string" {
  value       = azurerm_application_insights.poc.connection_string
  sensitive   = true
  description = "Application Insights Connection String for OpenTelemetry"
}

output "resource_group_name" {
  value       = azurerm_resource_group.poc.name
  description = "Resource group name for reference"
}
