# ============================================
# Terraform — Azure Infrastructure for POC
# ============================================
# Primary IaC: Provisions Azure AI Search (Free F0),
# Azure OpenAI, and Application Insights for observability.
#
# Usage:
#   terraform init
#   terraform plan  -var-file="poc.tfvars"
#   terraform apply -var-file="poc.tfvars"
# ============================================

terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # ── Remote State (uncomment after creating the storage account) ──
  # backend "azurerm" {
  #   resource_group_name  = "rg-terraform-state"
  #   storage_account_name = "tfstatehybridpoc"
  #   container_name       = "tfstate"
  #   key                  = "poc.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id

  # Enforce common tags across ALL resources in this configuration.
  # Resource-level tags are merged on top of these.
}

# ── Resource Group ───────────────────────────────────
resource "azurerm_resource_group" "poc" {
  name     = var.resource_group_name
  location = var.location

  tags = local.common_tags
}
