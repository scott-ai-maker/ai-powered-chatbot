#!/bin/bash

# Quick Azure Deployment for AI Career Mentor Chatbot
# ===================================================
# This script deploys the current chatbot to Azure Cloud

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
APP_NAME="ai-career-mentor"
ENVIRONMENT="prod"
LOCATION="eastus2"
RESOURCE_GROUP="${APP_NAME}-${ENVIRONMENT}-rg"
SUBSCRIPTION_ID=""

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🚀 AI Career Mentor Chatbot - Azure Deployment"
echo "=============================================="

# Step 1: Prerequisites Check
log_info "Checking prerequisites..."

if ! command -v az &> /dev/null; then
    log_error "Azure CLI not found. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Please install it first."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    log_warning "Not logged in to Azure. Please log in."
    az login
fi

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
log_info "Using subscription: $SUBSCRIPTION_ID"

# Step 2: Create Resource Group
log_info "Creating resource group: $RESOURCE_GROUP"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --tags Environment=$ENVIRONMENT Project="AI-Career-Mentor" Owner="Scott"

log_success "Resource group created successfully"

# Step 3: Deploy Infrastructure
log_info "Deploying Azure infrastructure..."

ADMIN_EMAIL="scott.ai.maker@example.com"

az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file infrastructure/bicep/main.bicep \
    --parameters \
        appName=$APP_NAME \
        environment=$ENVIRONMENT \
        location=$LOCATION \
        adminEmail=$ADMIN_EMAIL \
        openAiModelName="gpt-4" \
        openAiEmbeddingModelName="text-embedding-ada-002"

if [ $? -eq 0 ]; then
    log_success "Infrastructure deployed successfully!"
else
    log_error "Infrastructure deployment failed!"
    exit 1
fi

# Step 4: Get Infrastructure Outputs
log_info "Retrieving infrastructure details..."

CONTAINER_REGISTRY=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main \
    --query properties.outputs.containerRegistryName.value \
    --output tsv)

CONTAINER_APP_NAME=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main \
    --query properties.outputs.containerAppName.value \
    --output tsv)

APP_INSIGHTS_KEY=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main \
    --query properties.outputs.applicationInsightsKey.value \
    --output tsv)

log_info "Container Registry: $CONTAINER_REGISTRY"
log_info "Container App: $CONTAINER_APP_NAME"

# Step 5: Build and Push Container
log_info "Building and pushing container image..."

# Login to ACR
az acr login --name $CONTAINER_REGISTRY

# Build and tag image
IMAGE_NAME="${CONTAINER_REGISTRY}.azurecr.io/${APP_NAME}:latest"
docker build -t $IMAGE_NAME .

# Push image
docker push $IMAGE_NAME

log_success "Container image pushed successfully!"

# Step 6: Deploy Application
log_info "Deploying application to Container Apps..."

az containerapp update \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image $IMAGE_NAME

log_success "Application deployed successfully!"

# Step 7: Get Application URL
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    --output tsv)

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "Application URL: https://$APP_URL"
echo "API Documentation: https://$APP_URL/docs"
echo "Health Check: https://$APP_URL/health"
echo "Monitoring Dashboard: https://$APP_URL/monitoring/dashboard"
echo ""
echo "💰 Expected Monthly Cost: ~$50-80"
echo "📊 Monitor costs in Azure Portal"
echo ""
echo "Next Steps:"
echo "1. Test the application at the URL above"
echo "2. Check monitoring dashboard for metrics"  
echo "3. Review Azure costs in the portal"
echo "4. Configure custom domain (optional)"
echo ""

log_success "Deployment completed successfully! 🚀"