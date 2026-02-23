# ============================================
# Outputs — For downstream CI/CD and .env
# ============================================

# ── AI Search ───────────────────────────────────────
output "search_endpoint" {
  value       = "https://${azurerm_search_service.poc.name}.search.windows.net"
  description = "Azure AI Search endpoint URL"
}

output "search_admin_key" {
  value       = azurerm_search_service.poc.primary_key
  sensitive   = true
  description = "Azure AI Search admin API key"
}

# ── Azure OpenAI ────────────────────────────────────
output "openai_endpoint" {
  value       = azurerm_cognitive_account.openai.endpoint
  description = "Azure OpenAI endpoint URL"
}

output "openai_key" {
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
  description = "Azure OpenAI API key"
}

# ── Observability ───────────────────────────────────
output "app_insights_connection_string" {
  value       = azurerm_application_insights.poc.connection_string
  sensitive   = true
  description = "Application Insights Connection String for OpenTelemetry"
}

output "resource_group_name" {
  value       = azurerm_resource_group.poc.name
  description = "Resource group name for reference"
}

# ── Container Apps ──────────────────────────────────
output "container_app_fqdn" {
  value       = azurerm_container_app.langgraph.ingress[0].fqdn
  description = "Container App FQDN for HTTPS access (e.g. https://<fqdn>/invoke)"
}

output "acr_login_server" {
  value       = azurerm_container_registry.poc.login_server
  description = "ACR login server for docker push (e.g. az acr build --registry <name>)"
}

output "key_vault_uri" {
  value       = azurerm_key_vault.poc.vault_uri
  description = "Key Vault URI for secret references"
}
