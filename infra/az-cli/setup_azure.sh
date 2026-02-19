#!/usr/bin/env bash
# ============================================
# Quick Azure Setup via az CLI
# ============================================
# Alternative to Terraform for fast POC setup.
# Requires: az CLI installed + az login completed.
#
# Usage:
#   chmod +x infra/az-cli/setup_azure.sh
#   ./infra/az-cli/setup_azure.sh
# ============================================
set -euo pipefail

# ── Configuration ────────────────────────────────────
RESOURCE_GROUP="rg-hybrid-poc"
LOCATION="swedencentral"
SEARCH_SERVICE_NAME="hybrid-poc-search-$(openssl rand -hex 3)"
OPENAI_ACCOUNT_NAME="hybrid-poc-openai-$(openssl rand -hex 3)"

echo "🚀 Setting up Azure resources for Hybrid Knowledge Synthesizer POC"
echo "   Resource Group:  $RESOURCE_GROUP"
echo "   Location:        $LOCATION"
echo "   Search Service:  $SEARCH_SERVICE_NAME"
echo "   OpenAI Account:  $OPENAI_ACCOUNT_NAME"
echo ""

# ── Resource Group ───────────────────────────────────
echo "📦 Creating resource group..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --tags project=hybrid-knowledge-synthesizer environment=poc cost-center=free-trial

# ── Azure AI Search (Free Tier) ─────────────────────
echo "🔍 Creating Azure AI Search (Free F0)..."
az search service create \
  --name "$SEARCH_SERVICE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --sku free \
  --location "$LOCATION"

SEARCH_KEY=$(az search admin-key show \
  --service-name "$SEARCH_SERVICE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query primaryKey -o tsv)

# ── Azure OpenAI ────────────────────────────────────
echo "🧠 Creating Azure OpenAI account..."
az cognitiveservices account create \
  --name "$OPENAI_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --kind OpenAI \
  --sku S0 \
  --location "$LOCATION" \
  --custom-domain "$OPENAI_ACCOUNT_NAME"

# Deploy gpt-4o-mini
echo "   Deploying gpt-4o-mini..."
az cognitiveservices account deployment create \
  --name "$OPENAI_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --deployment-name "gpt-4o-mini" \
  --model-name "gpt-4o-mini" \
  --model-version "2024-07-18" \
  --model-format OpenAI \
  --sku-capacity 1 \
  --sku-name "Standard"

# Deploy embedding model
echo "   Deploying text-embedding-3-small..."
az cognitiveservices account deployment create \
  --name "$OPENAI_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --deployment-name "text-embedding-3-small" \
  --model-name "text-embedding-3-small" \
  --model-version "1" \
  --model-format OpenAI \
  --sku-capacity 1 \
  --sku-name "Standard"

OPENAI_KEY=$(az cognitiveservices account keys list \
  --name "$OPENAI_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query key1 -o tsv)

OPENAI_ENDPOINT=$(az cognitiveservices account show \
  --name "$OPENAI_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query properties.endpoint -o tsv)

# ── Output ───────────────────────────────────────────
echo ""
echo "✅ Azure setup complete! Add these to your .env file:"
echo ""
echo "AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT"
echo "AZURE_OPENAI_API_KEY=$OPENAI_KEY"
echo "AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini"
echo "AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small"
echo "AZURE_SEARCH_ENDPOINT=https://${SEARCH_SERVICE_NAME}.search.windows.net"
echo "AZURE_SEARCH_API_KEY=$SEARCH_KEY"
echo "AZURE_SEARCH_INDEX_NAME=patents-index"
