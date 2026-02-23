# ============================================
# Identity — RBAC Role Assignments
# ============================================
# Zero Trust: Container App's System-Assigned Managed
# Identity gets ONLY the permissions it needs.

# ── ACR Pull (so Container Apps can pull images) ───
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.poc.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.langgraph.identity[0].principal_id
}

# ── Azure OpenAI — Cognitive Services OpenAI User ──
resource "azurerm_role_assignment" "openai_user" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_container_app.langgraph.identity[0].principal_id
}

# ── Azure AI Search — Search Index Data Reader ─────
resource "azurerm_role_assignment" "search_reader" {
  scope                = azurerm_search_service.poc.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = azurerm_container_app.langgraph.identity[0].principal_id
}

# ── Key Vault — Secrets User ──────────────────────
resource "azurerm_role_assignment" "kv_secrets_user" {
  scope                = azurerm_key_vault.poc.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_container_app.langgraph.identity[0].principal_id
}
