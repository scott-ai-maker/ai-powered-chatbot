# 🚀 Azure Deployment Guide - AI Career Mentor Chatbot

> **Deploy your AI Career Mentor Chatbot to Azure Cloud**

## 📋 Pre-Deployment Checklist

### **Prerequisites**
- [ ] Azure CLI installed (`az --version`)
- [ ] Docker installed (`docker --version`)
- [ ] Azure subscription with sufficient credits (~$50-80/month)
- [ ] Logged into Azure CLI (`az login`)

### **Required Azure Services**
The deployment will create these services automatically:
- [ ] **Azure Container Apps** - Host the FastAPI application
- [ ] **Azure OpenAI** - GPT-4 and embedding models
- [ ] **Azure Cognitive Search** - RAG knowledge base
- [ ] **Azure Cosmos DB** - Conversation storage
- [ ] **Azure Key Vault** - Secrets management
- [ ] **Azure Container Registry** - Docker images
- [ ] **Azure Application Insights** - Monitoring

## 💰 Cost Estimate

### **Expected Monthly Costs**
| Service | Cost | Purpose |
|---------|------|---------|
| **Azure OpenAI (GPT-4)** | $20-40 | AI text generation |
| **Container Apps** | $15-25 | Application hosting |
| **Cosmos DB** | $5-10 | Database storage |
| **Cognitive Search** | $5-10 | Knowledge search |
| **Other services** | $5-10 | Monitoring, storage, etc. |
| **Total** | **$50-95/month** | Full production system |

## 🚀 Quick Deployment

### **Step 1: Run the Deployment Script**
```bash
# Make sure you're in the project directory
cd ~/repos/ai-powered-chatbot

# Run the automated deployment
./deploy-to-azure.sh
```

### **Step 2: Monitor the Deployment**
The script will:
1. ✅ Check prerequisites
2. ✅ Create Azure resource group  
3. ✅ Deploy infrastructure with Bicep
4. ✅ Build and push Docker container
5. ✅ Deploy application to Container Apps
6. ✅ Provide access URLs

**Deployment time: ~15-20 minutes**

### **Step 3: Initial Testing**
Once deployed, test these endpoints:
- **Main App**: `https://your-app-url/`
- **API Docs**: `https://your-app-url/docs`
- **Health Check**: `https://your-app-url/health`
- **Monitoring**: `https://your-app-url/monitoring/dashboard`

## 🔧 Post-Deployment Configuration

### **Knowledge Base Setup**
After deployment, you'll need to populate the knowledge base:

```bash
# Run the knowledge seeder (this will be automated in deployment)
python -m src.services.knowledge_seeder
```

### **Environment Verification**
Check that all services are working:

```bash
# Test Azure OpenAI connection
curl -X POST "https://your-app-url/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me with AI career advice?"}'
```

### **Monitoring Setup**
- **Azure Portal**: Monitor costs and resource usage
- **Application Insights**: View telemetry and performance
- **Custom Dashboard**: Real-time metrics at `/monitoring/dashboard`

## 🔒 Security Configuration

### **Secrets Management**
All secrets are automatically stored in Azure Key Vault:
- Azure OpenAI API keys
- Cosmos DB connection strings  
- Search service keys
- Application secrets

### **Network Security**
- HTTPS-only communication
- Azure private networking
- CORS configuration for frontend
- Rate limiting on API endpoints

## 📊 Monitoring & Maintenance

### **Built-in Monitoring**
- **Health Checks**: Automatic container health monitoring
- **Application Insights**: Performance and error tracking
- **Custom Metrics**: AI usage, costs, and business KPIs
- **Alerting**: Automatic notifications for issues

### **Cost Monitoring**
- **Budget Alerts**: Set up in Azure Portal
- **Usage Tracking**: Monitor AI token consumption
- **Resource Optimization**: Auto-scaling based on traffic

## 🛠️ Troubleshooting

### **Common Issues**

**1. Deployment Fails**
```bash
# Check Azure CLI login
az account show

# Verify subscription has necessary permissions
az account list-locations
```

**2. Container Build Fails**
```bash
# Test local build
docker build -t test-build .

# Check Dockerfile syntax
docker build --no-cache -t test-build .
```

**3. Application Not Starting**
```bash
# Check container logs
az containerapp logs show \
  --name ai-career-mentor-prod-app \
  --resource-group ai-career-mentor-prod-rg \
  --follow
```

**4. High Costs**
- Monitor Azure OpenAI usage in portal
- Check auto-scaling settings
- Review conversation patterns for optimization

### **Getting Help**
- **Azure Support**: Use Azure Portal support
- **Application Logs**: Check Container Apps logs
- **GitHub Issues**: Report deployment issues

## 🎯 Success Criteria

After successful deployment, you should have:

- [ ] **Live Application** accessible via HTTPS URL
- [ ] **API Documentation** at `/docs` endpoint
- [ ] **Health Monitoring** showing all services healthy
- [ ] **Cost Tracking** under budget expectations
- [ ] **Performance Metrics** in Application Insights
- [ ] **Security** with all secrets in Key Vault

## 🚀 Next Steps

Once your first app is deployed:

1. **Test Thoroughly** - Verify all features work in production
2. **Monitor Costs** - Track usage for first week
3. **Optimize Performance** - Tune based on real usage
4. **Plan Multi-App Architecture** - Prepare for 4 additional apps
5. **Document Learnings** - Note any deployment insights

**You'll have a production-ready AI application running on Azure, ready to demonstrate to employers!** 🎉

---

## 📞 Support

- **Deployment Issues**: Check troubleshooting section above
- **Azure Costs**: Monitor in Azure Portal > Cost Management
- **Application Performance**: View in Application Insights
- **Security Concerns**: Review Key Vault and network settings