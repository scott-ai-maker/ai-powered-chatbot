#!/bin/bash

# AI Career Mentor - Streamlit Frontend Deployment Script
# This script deploys the Streamlit chat interface to Azure Container Apps

set -e

echo "🚀 AI Career Mentor - Frontend Deployment"
echo "========================================"

# Configuration
RESOURCE_GROUP="ai-career-mentor-prod-rg"
REGISTRY_NAME="aicareermentorprodregistry"
FRONTEND_APP_NAME="ai-career-mentor-frontend"
ENVIRONMENT_NAME="ai-career-mentor-prod-env"
IMAGE_NAME="ai-career-mentor-frontend"
FRONTEND_TAG="latest"

echo "[INFO] Getting registry credentials..."
REGISTRY_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query "passwords[0].value" --output tsv)

echo "[INFO] Logging into Azure Container Registry..."
echo $REGISTRY_PASSWORD | sudo docker login ${REGISTRY_NAME}.azurecr.io --username $REGISTRY_NAME --password-stdin

echo "[INFO] Tagging and pushing frontend Docker image..."
sudo docker tag ${IMAGE_NAME}:${FRONTEND_TAG} ${REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}:${FRONTEND_TAG}
sudo docker push ${REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}:${FRONTEND_TAG}

echo "[INFO] Creating Streamlit frontend Container App..."
az containerapp create \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --image ${REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}:${FRONTEND_TAG} \
  --registry-server ${REGISTRY_NAME}.azurecr.io \
  --registry-username $REGISTRY_NAME \
  --registry-password $REGISTRY_PASSWORD \
  --target-port 8501 \
  --ingress external \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars \
    API_BASE_URL="https://ai-career-mentor-prod-app.agreeablecoast-963be1b8.eastus2.azurecontainerapps.io" \
    ENVIRONMENT="production"

# Get the frontend URL
FRONTEND_URL=$(az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" --output tsv)

echo ""
echo "✅ Frontend deployment completed!"
echo "🌐 Frontend URL: https://$FRONTEND_URL"
echo "🔗 Backend API: https://ai-career-mentor-prod-app.agreeablecoast-963be1b8.eastus2.azurecontainerapps.io"
echo ""
echo "🎉 Your AI Career Mentor Chatbot is now live with a beautiful Streamlit interface!"