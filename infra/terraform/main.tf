# ============================================
# Terraform — Azure Infrastructure for POC
# ============================================
# Primary IaC: Creates Azure AI Search (Free F0) and
# Azure OpenAI resources within free-tier limits.
#
# Usage:
#   terraform init
#   terraform plan -var-file="poc.tfvars"
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
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# ── Variables ────────────────────────────────────────
variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "swedencentral"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-hybrid-poc"
}

variable "search_service_name" {
  description = "Azure AI Search service name (must be globally unique)"
  type        = string
  default     = "hybrid-poc-search"
}

variable "openai_account_name" {
  description = "Azure OpenAI account name (must be globally unique)"
  type        = string
  default     = "hybrid-poc-openai"
}

# ── Resource Group ───────────────────────────────────
resource "azurerm_resource_group" "poc" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    project     = "hybrid-knowledge-synthesizer"
    environment = "poc"
    cost-center = "free-trial"
  }
}

# ── Azure AI Search (Free Tier F0) ──────────────────
resource "azurerm_search_service" "poc" {
  name                = var.search_service_name
  resource_group_name = azurerm_resource_group.poc.name
  location            = azurerm_resource_group.poc.location
  sku                 = "free"  # F0: 50MB storage, 3 indexes, no replicas

  tags = azurerm_resource_group.poc.tags
}

# ── Azure OpenAI ────────────────────────────────────
resource "azurerm_cognitive_account" "openai" {
  name                  = var.openai_account_name
  resource_group_name   = azurerm_resource_group.poc.name
  location              = var.location
  kind                  = "OpenAI"
  sku_name              = "S0"  # Only SKU available for OpenAI
  custom_subdomain_name = var.openai_account_name

  tags = azurerm_resource_group.poc.tags
}

# ── Deployments: gpt-4o-mini + text-embedding-3-small ─
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
    capacity = 1  # Minimum TPM
  }
}

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
}

# ── Outputs ──────────────────────────────────────────
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
