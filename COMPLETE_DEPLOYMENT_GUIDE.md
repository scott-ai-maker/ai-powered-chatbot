# Complete Deployment Guide for AI Career Mentor Chatbot

This comprehensive guide covers all aspects of deploying the AI Career Mentor Chatbot from development through production.

## 📋 Prerequisites

### Required Tools
- **Azure CLI**: Version 2.50+ with Bicep extension
- **Docker**: For container operations
- **Git**: For source control
- **Node.js**: Version 18+ (for frontend)
- **Python**: Version 3.11+ (for backend)

### Azure Setup
1. **Azure Subscription** with sufficient quota for:
   - Container Apps (2 vCPU minimum)
   - OpenAI Service (GPT-4 access)
   - Cosmos DB
   - Container Registry

2. **Service Principal** with roles:
   - Contributor (for resource management)
   - User Access Administrator (for role assignments)

3. **Resource Providers** registered:
   - Microsoft.App
   - Microsoft.ContainerRegistry
   - Microsoft.KeyVault
   - Microsoft.CognitiveServices
   - Microsoft.Search
   - Microsoft.DocumentDB

## 🚀 Deployment Methods

### Method 1: Robust Three-Phase Deployment (Recommended)

This is the most reliable method, especially after infrastructure issues:

```bash
# Navigate to project directory
cd ai-powered-chatbot

# Run the robust deployment script
./infrastructure/scripts/deploy-robust.sh \
  --environment dev \
  --location eastus2 \
  --subscription "YOUR_SUBSCRIPTION_ID" \
  --admin-email "your-email@example.com" \
  --force-cleanup \
  --verbose
```

#### What this does:
1. **Phase 1 (Minimal)**: Deploys core services only
   - Container Registry, Key Vault, OpenAI, Cosmos DB, Search, App Insights
   - Avoids Container Apps Environment (source of corruption)

2. **Phase 2 (Infrastructure)**: Adds Container Apps Environment
   - Creates clean Container Apps Environment
   - Sets up networking and monitoring

3. **Phase 3 (Full)**: Deploys Container App
   - Deploys the application container
   - Configures ingress and scaling

### Method 2: CI/CD Pipeline Deployment

For automated deployments through GitHub Actions:

1. **Configure Repository Secrets**:
   ```
   AZURE_CLIENT_ID: <service-principal-app-id>
   AZURE_CLIENT_SECRET: <service-principal-password>
   AZURE_TENANT_ID: <azure-tenant-id>
   ADMIN_EMAIL: <your-admin-email>
   ```

2. **Configure Repository Variables**:
   ```
   AZURE_SUBSCRIPTION_ID: <subscription-id>
   MAINTAINER_EMAIL: <maintainer-email>
   ```

3. **Trigger Deployment**:
   - Push to `main` branch for development
   - Create release tag for production

### Method 3: Manual Step-by-Step Deployment

For learning or troubleshooting:

```bash
# 1. Deploy minimal infrastructure
az deployment group create \
  --resource-group rg-ai-career-mentor-dev \
  --name "minimal-$(date +%Y%m%d-%H%M%S)" \
  --template-file infrastructure/bicep/main.bicep \
  --parameters @infrastructure/bicep/parameters.dev.json \
  --parameters deploymentMode=minimal \
  --parameters adminEmail="your-email@example.com"

# 2. Add Container Apps Environment
az deployment group create \
  --resource-group rg-ai-career-mentor-dev \
  --name "infrastructure-$(date +%Y%m%d-%H%M%S)" \
  --template-file infrastructure/bicep/main.bicep \
  --parameters @infrastructure/bicep/parameters.dev.json \
  --parameters deploymentMode=infrastructure \
  --parameters adminEmail="your-email@example.com"

# 3. Deploy Container App
az deployment group create \
  --resource-group rg-ai-career-mentor-dev \
  --name "full-$(date +%Y%m%d-%H%M%S)" \
  --template-file infrastructure/bicep/main.bicep \
  --parameters @infrastructure/bicep/parameters.dev.json \
  --parameters deploymentMode=full \
  --parameters adminEmail="your-email@example.com"
```

## 🔧 Configuration

### Environment Parameters

The deployment uses three parameter files:
- `parameters.dev.json` - Development environment
- `parameters.staging.json` - Staging environment  
- `parameters.prod.json` - Production environment

Key parameters to customize:

```json
{
  "appName": "ai-career-mentor",
  "environment": "dev",
  "location": "eastus2",
  "deploymentMode": "minimal",  // minimal|infrastructure|full
  "openAiSku": "S0",
  "cosmosDbThroughput": 400,
  "searchServiceSku": "basic",
  "containerMinReplicas": 1,
  "containerMaxReplicas": 3
}
```

### Deployment Modes Explained

1. **minimal**: Core services only (safest for initial deployment)
2. **infrastructure**: Core services + Container Apps Environment
3. **full**: All services including Container App (complete deployment)

## 🏥 Troubleshooting

### Common Issues and Solutions

#### 1. Container Apps Environment Corruption
**Symptoms**: AKS control plane errors, stuck deployments
**Solution**: Use force cleanup and redeploy
```bash
./infrastructure/scripts/deploy-robust.sh --force-cleanup
```

#### 2. Resource Provider Not Registered
**Error**: `The subscription is not registered to use namespace 'Microsoft.App'`
**Solution**:
```bash
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.ContainerRegistry
# Wait for registration to complete
az provider show --namespace Microsoft.App --query registrationState
```

#### 3. Insufficient Permissions
**Error**: Permission denied for role assignments
**Solution**: Ensure service principal has User Access Administrator role
```bash
az role assignment create \
  --assignee <service-principal-id> \
  --role "User Access Administrator" \
  --scope "/subscriptions/<subscription-id>"
```

#### 4. Container Image Not Found
**Error**: Container app fails to start with image pull errors
**Solution**: Check container registry and image tags
```bash
# List available images
az acr repository list --name <registry-name>
az acr repository show-tags --name <registry-name> --repository ai-career-mentor
```

### Diagnostic Tools

#### Infrastructure Status
```bash
./infrastructure/scripts/troubleshoot.sh status --environment dev
```

#### Health Check
```bash
./infrastructure/scripts/troubleshoot.sh health --environment dev
```

#### View Logs
```bash
./infrastructure/scripts/troubleshoot.sh logs --environment dev --watch
```

#### Comprehensive Diagnostics
```bash
./infrastructure/scripts/troubleshoot.sh diagnostics --environment dev --verbose
```

#### Monitor Infrastructure
```bash
./infrastructure/scripts/troubleshoot.sh monitor --environment dev
```

## 🧪 Validation

After deployment, validate the infrastructure:

```bash
# Run validation script
./infrastructure/scripts/validate-deployment.sh --environment dev

# Check specific endpoints
curl -f https://<your-app-url>/health
curl -f https://<your-app-url>/api/v1/chat/health
```

Expected validation results:
- ✅ All Azure resources created successfully
- ✅ Container App running and healthy
- ✅ Public endpoint accessible
- ✅ Health checks passing
- ✅ Security configurations in place

## 📊 Monitoring and Maintenance

### Application Insights
Monitor application performance and errors:
- Navigate to Application Insights in Azure Portal
- Review Performance, Failures, and Live Metrics

### Container App Logs
```bash
az containerapp logs show \
  --name <app-name> \
  --resource-group <resource-group> \
  --follow
```

### Resource Health
```bash
# Check all resources
az resource list --resource-group <resource-group> --output table

# Check specific service health
az containerapp show --name <app-name> --resource-group <resource-group> \
  --query properties.provisioningState
```

## 🔄 Updates and Maintenance

### Code Updates
1. Push changes to GitHub
2. CI/CD pipeline automatically builds and deploys
3. Validate deployment with health checks

### Infrastructure Updates
1. Modify Bicep templates
2. Update parameter files
3. Run deployment with updated configuration

### Scale Adjustments
```bash
# Scale Container App
az containerapp update \
  --name <app-name> \
  --resource-group <resource-group> \
  --min-replicas 2 \
  --max-replicas 5
```

## 🚨 Emergency Procedures

### Complete Infrastructure Reset
If infrastructure is completely corrupted:

```bash
# 1. Delete resource group (DESTRUCTIVE!)
az group delete --name rg-ai-career-mentor-dev --yes

# 2. Recreate and redeploy
az group create --name rg-ai-career-mentor-dev --location eastus2
./infrastructure/scripts/deploy-robust.sh --environment dev --force-cleanup
```

### Service Recovery
If specific services fail:

```bash
# Restart Container App
az containerapp revision restart \
  --name <app-name> \
  --resource-group <resource-group>

# Clean up and redeploy Container App only
./infrastructure/scripts/troubleshoot.sh cleanup
# Then redeploy with full mode
```

## 📞 Support

For deployment issues:
1. Check troubleshooting section above
2. Run diagnostics script for detailed analysis
3. Review Azure Portal for error details
4. Check GitHub Actions logs for CI/CD issues

## 🎓 Learning Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Bicep Documentation](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure OpenAI Service](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [GitHub Actions for Azure](https://docs.microsoft.com/en-us/azure/developer/github/github-actions)