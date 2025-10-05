#!/bin/bash

# Azure Deployment Phase 2 - AI Services & Application
# ====================================================
# Deploy AI services and update Container App with your chatbot

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🤖 AI Career Mentor - Phase 2: AI Services Deployment"
echo "===================================================="

# Configuration
APP_NAME="ai-career-mentor"
ENVIRONMENT="prod"
LOCATION="eastus2"
RESOURCE_GROUP="${APP_NAME}-${ENVIRONMENT}-rg"
CONTAINER_APP_NAME="${APP_NAME}-${ENVIRONMENT}-app"

# Step 1: Create Azure OpenAI Service
log_info "Creating Azure OpenAI Service..."
OPENAI_NAME="${APP_NAME}-${ENVIRONMENT}-openai"

az cognitiveservices account create \
    --name $OPENAI_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --kind OpenAI \
    --sku S0 \
    --custom-domain $OPENAI_NAME

log_success "Azure OpenAI Service created"

# Deploy GPT-4 model
# Deploy GPT-4 model
log_info "Deploying GPT-4 model..."
az cognitiveservices account deployment create \
    --resource-group $RESOURCE_GROUP \
    --name $OPENAI_NAME \
    --deployment-name "gpt-4" \
    --model-name "gpt-4o" \
    --model-version "2024-08-06" \
    --model-format "OpenAI" \
    --sku-capacity 10 \
    --sku-name "Standard" || {
    log_error "Failed to deploy GPT-4 model"
    exit 1
}
log_success "GPT-4 model deployed"

# Deploy text embedding model
log_info "Deploying text embedding model..."
az cognitiveservices account deployment create \
    --name $OPENAI_NAME \
    --resource-group $RESOURCE_GROUP \
    --deployment-name text-embedding-ada-002 \
    --model-name text-embedding-ada-002 \
    --model-version "2" \
    --model-format OpenAI \
    --sku-capacity 10 \
    --sku-name "Standard"

log_success "AI models deployed"

# Step 2: Create Cosmos DB
log_info "Creating Cosmos DB..."
COSMOS_NAME="${APP_NAME}-${ENVIRONMENT}-cosmos"

az cosmosdb create \
    --name $COSMOS_NAME \
    --resource-group $RESOURCE_GROUP \
    --locations regionName=$LOCATION failoverPriority=0 \
    --default-consistency-level Session \
    --enable-automatic-failover false

# Create database and container
az cosmosdb sql database create \
    --account-name $COSMOS_NAME \
    --resource-group $RESOURCE_GROUP \
    --name chatbot

az cosmosdb sql container create \
    --account-name $COSMOS_NAME \
    --resource-group $RESOURCE_GROUP \
    --database-name chatbot \
    --name conversations \
    --partition-key-path "/session_id" \
    --throughput 400

log_success "Cosmos DB created"

# Step 3: Create Cognitive Search
log_info "Creating Cognitive Search..."
SEARCH_NAME="${APP_NAME}-${ENVIRONMENT}-search"

az search service create \
    --name $SEARCH_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Basic

log_success "Cognitive Search created"

# Step 4: Get service endpoints and keys
log_info "Retrieving service configuration..."

OPENAI_ENDPOINT=$(az cognitiveservices account show \
    --name $OPENAI_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.endpoint \
    --output tsv)

OPENAI_KEY=$(az cognitiveservices account keys list \
    --name $OPENAI_NAME \
    --resource-group $RESOURCE_GROUP \
    --query key1 \
    --output tsv)

COSMOS_ENDPOINT=$(az cosmosdb show \
    --name $COSMOS_NAME \
    --resource-group $RESOURCE_GROUP \
    --query documentEndpoint \
    --output tsv)

COSMOS_KEY=$(az cosmosdb keys list \
    --name $COSMOS_NAME \
    --resource-group $RESOURCE_GROUP \
    --query primaryMasterKey \
    --output tsv)

SEARCH_ENDPOINT="https://${SEARCH_NAME}.search.windows.net"
SEARCH_KEY=$(az search admin-key show \
    --service-name $SEARCH_NAME \
    --resource-group $RESOURCE_GROUP \
    --query primaryKey \
    --output tsv)

log_success "Service configuration retrieved"

# Step 5: Build and deploy your application
log_info "Building your AI Career Mentor application..."

# Build Docker image
IMAGE_NAME="ai-career-mentor:latest"
sudo docker build -t $IMAGE_NAME .

log_success "Application built"

# For now, let's update the container app with environment variables
# In a production setup, you'd push to Azure Container Registry
log_info "Updating Container App with AI service configuration..."

az containerapp update \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --set-env-vars \
        AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT \
        AZURE_OPENAI_KEY=$OPENAI_KEY \
        AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4 \
        COSMOS_DB_ENDPOINT=$COSMOS_ENDPOINT \
        COSMOS_DB_KEY=$COSMOS_KEY \
        AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT \
        AZURE_SEARCH_KEY=$SEARCH_KEY \
        ENVIRONMENT=production

log_success "Container App updated with AI services"

# Get final app URL
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    --output tsv)

echo ""
echo "🎉 Phase 2 Deployment Complete!"
echo "==============================="
echo "AI Services Deployed:"
echo "  ✅ Azure OpenAI (GPT-4 + Embeddings)"
echo "  ✅ Cosmos DB (Conversations)"
echo "  ✅ Cognitive Search (Knowledge Base)"
echo ""
echo "Application URL: https://$APP_URL"
echo ""
echo "💰 Expected Monthly Cost: ~$50-80"
echo ""
echo "Next Steps:"
echo "1. Test the AI services integration"
echo "2. Deploy your custom container image"
echo "3. Set up monitoring and alerting"
echo "4. Plan the multi-app portfolio architecture"
echo ""

log_success "Phase 2 completed successfully! 🤖"