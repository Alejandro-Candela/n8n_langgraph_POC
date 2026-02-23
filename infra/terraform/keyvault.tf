# ============================================
# Azure Key Vault — Secret Management
# ============================================
# Standard SKU, RBAC authorization (no legacy access policies).
# Purge protection disabled for POC easy cleanup.

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "poc" {
  name                       = var.key_vault_name
  location                   = azurerm_resource_group.poc.location
  resource_group_name        = azurerm_resource_group.poc.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  purge_protection_enabled   = false
  soft_delete_retention_days = 7

  tags = local.common_tags
}

# Grant the deployer (current user/SP) "Key Vault Administrator"
# so Terraform can manage secrets in the vault.
resource "azurerm_role_assignment" "kv_admin" {
  scope                = azurerm_key_vault.poc.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}
