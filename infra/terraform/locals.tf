# ============================================
# Locals — Computed Values
# ============================================

locals {
  # Common tags applied to all resources.
  common_tags = {
    project      = var.project
    environment  = var.environment
    cost-center  = "free-trial"
    managed-by   = "terraform"
  }

  # Computed resource names
  log_analytics_name = "${var.resource_group_name}-logs"
  app_insights_name  = "${var.resource_group_name}-insights"

  # Container Apps
  container_env_name = "cae-${var.project}-${var.environment}"
  container_image    = "${var.acr_name}.azurecr.io/langgraph-service:${var.container_app_image_tag}"
}
