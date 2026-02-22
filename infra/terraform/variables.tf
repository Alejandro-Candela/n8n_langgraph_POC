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
