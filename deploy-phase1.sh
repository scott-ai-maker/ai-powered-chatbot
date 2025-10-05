#!/bin/bash

# Simplified Azure Deployment - Phase 1
# =====================================
# Deploy basic infrastructure first, then add complexity

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

echo "🚀 AI Career Mentor - Simplified Azure Deployment"
echo "=============================================="

# Configuration
APP_NAME="ai-career-mentor"
ENVIRONMENT="prod"
LOCATION="eastus2"
RESOURCE_GROUP="${APP_NAME}-${ENVIRONMENT}-rg"

log_info "Resource Group: $RESOURCE_GROUP"
log_info "Location: $LOCATION"

# Check if resource group exists
if az group show --name $RESOURCE_GROUP &> /dev/null; then
    log_info "Resource group already exists"
else
    log_error "Resource group not found. Please run main deployment script first."
    exit 1
fi

# Deploy Container Apps Environment first
log_info "Creating Container Apps Environment..."

CONTAINER_ENV_NAME="${APP_NAME}-${ENVIRONMENT}-env"
LOG_ANALYTICS_NAME="${APP_NAME}-${ENVIRONMENT}-logs"

# Create Log Analytics workspace
log_info "Creating Log Analytics workspace..."
az monitor log-analytics workspace create \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_NAME \
    --location $LOCATION \
    --sku PerGB2018

# Get Log Analytics workspace ID
WORKSPACE_ID=$(az monitor log-analytics workspace show \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_NAME \
    --query customerId \
    --output tsv)

WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_NAME \
    --query primarySharedKey \
    --output tsv)

log_success "Log Analytics workspace created"

# Create Container Apps Environment  
log_info "Creating Container Apps Environment..."
az containerapp env create \
    --name $CONTAINER_ENV_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --logs-workspace-id $WORKSPACE_ID \
    --logs-workspace-key $WORKSPACE_KEY

log_success "Container Apps Environment created"

# Create a basic Container App with a simple image first
log_info "Creating basic Container App..."

CONTAINER_APP_NAME="${APP_NAME}-${ENVIRONMENT}-app"

az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_ENV_NAME \
    --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest \
    --target-port 80 \
    --ingress external \
    --query properties.configuration.ingress.fqdn

log_success "Basic Container App created"

# Get the app URL
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    --output tsv)

echo ""
echo "🎉 Phase 1 Deployment Complete!"
echo "==============================="
echo "Basic Container App URL: https://$APP_URL"
echo ""
echo "Next Steps:"
echo "1. Verify the basic app is working"
echo "2. Deploy AI services (OpenAI, Cosmos DB, etc.)"  
echo "3. Build and deploy your custom container"
echo ""

log_success "Phase 1 completed successfully! 🚀"