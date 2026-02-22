# ============================================
# Locals — Computed Values
# ============================================

locals {
  # Common tags applied via provider default_tags
  # Additional resource-specific tags can be merged as needed.
  common_tags = {
    project      = var.project
    environment  = var.environment
    cost-center  = "free-trial"
    managed-by   = "terraform"
  }

  # Computed resource names
  log_analytics_name = "${var.resource_group_name}-logs"
  app_insights_name  = "${var.resource_group_name}-insights"
}
