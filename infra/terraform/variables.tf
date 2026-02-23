# ============================================
# Variables — POC Infrastructure
# ============================================

variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.subscription_id))
    error_message = "subscription_id must be a valid UUID."
  }
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "swedencentral"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-hybrid-poc"
}

variable "environment" {
  description = "Deployment environment (poc, dev, staging, prod)"
  type        = string
  default     = "poc"

  validation {
    condition     = contains(["poc", "dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: poc, dev, staging, prod."
  }
}

variable "project" {
  description = "Project identifier for tagging and naming"
  type        = string
  default     = "hybrid-knowledge-synthesizer"
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

# ── Container Apps ──────────────────────────────────

variable "acr_name" {
  description = "Azure Container Registry name (must be globally unique, alphanumeric only)"
  type        = string
  default     = "hybridpocreg"

  validation {
    condition     = can(regex("^[a-zA-Z0-9]{5,50}$", var.acr_name))
    error_message = "acr_name must be 5-50 alphanumeric characters."
  }
}

variable "container_app_name" {
  description = "Name for the Container App hosting langgraph-service"
  type        = string
  default     = "ca-langgraph"
}

variable "container_app_image_tag" {
  description = "Docker image tag to deploy (e.g. 'latest', 'v0.1.0', commit SHA)"
  type        = string
  default     = "latest"
}

variable "key_vault_name" {
  description = "Azure Key Vault name (must be globally unique, 3-24 chars)"
  type        = string
  default     = "kv-hybrid-poc"

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9-]{1,22}[a-zA-Z0-9]$", var.key_vault_name))
    error_message = "key_vault_name must be 3-24 chars, start with letter, alphanumeric and hyphens only."
  }
}
