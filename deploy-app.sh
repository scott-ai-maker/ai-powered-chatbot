#!/bin/bash

# Deploy AI Career Mentor Application
# ==================================
# Push custom Docker image and update Container App

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

echo "🚀 AI Career Mentor - Application Deployment"
echo "============================================"

# Configuration
APP_NAME="ai-career-mentor"
ENVIRONMENT="prod"
RESOURCE_GROUP="${APP_NAME}-${ENVIRONMENT}-rg"
CONTAINER_APP_NAME="${APP_NAME}-${ENVIRONMENT}-app"
IMAGE_NAME="${APP_NAME}:latest"
REGISTRY_NAME="aicareermentorprodregistry"
REGISTRY_SERVER="${REGISTRY_NAME}.azurecr.io"

# Step 1: Create Azure Container Registry
log_info "Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $REGISTRY_NAME \
    --sku Basic \
    --admin-enabled true || {
    log_warning "Registry might already exist, continuing..."
}

# Step 2: Get registry credentials
log_info "Getting registry credentials..."
REGISTRY_PASSWORD=$(az acr credential show \
    --name $REGISTRY_NAME \
    --query "passwords[0].value" \
    --output tsv)

REGISTRY_USERNAME=$(az acr credential show \
    --name $REGISTRY_NAME \
    --query "username" \
    --output tsv)

# Step 3: Login to registry
log_info "Logging into registry..."
echo $REGISTRY_PASSWORD | docker login $REGISTRY_SERVER \
    --username $REGISTRY_USERNAME \
    --password-stdin

# Step 4: Tag and push image
log_info "Tagging and pushing Docker image..."
docker tag $IMAGE_NAME $REGISTRY_SERVER/$IMAGE_NAME
docker push $REGISTRY_SERVER/$IMAGE_NAME

log_success "Image pushed to registry"

# Step 5: Update Container App with our custom image
log_info "Updating Container App with custom image..."

# First, configure the registry
az containerapp registry set \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --server $REGISTRY_SERVER \
    --username $REGISTRY_USERNAME \
    --password $REGISTRY_PASSWORD

# Then update the image
az containerapp update \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image "$REGISTRY_SERVER/$IMAGE_NAME"

log_success "Container App updated with custom image"

# Step 6: Test the deployment
log_info "Testing deployment..."
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

sleep 30  # Wait for deployment to propagate

if curl -f -s "https://$APP_URL/health" > /dev/null; then
    log_success "Application health check passed!"
else
    log_warning "Health check endpoint not responding, but app may still be starting..."
fi

echo ""
echo "🎉 Application Deployment Complete!"
echo "=================================="
echo "🌐 Application URL: https://$APP_URL"
echo "🔧 Registry: $REGISTRY_SERVER"
echo "📊 Monitor: Azure Portal > Container Apps"
echo ""
echo "Next steps:"
echo "1. Test the application at the URL above"
echo "2. Monitor logs in Azure Portal"
echo "3. Set up custom domain (optional)"