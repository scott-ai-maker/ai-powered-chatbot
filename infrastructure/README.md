# Azure Infrastructure Documentation

## Overview

This document describes the Azure infrastructure for the AI Career Mentor Chatbot, implemented using Infrastructure as Code (IaC) with Bicep templates. The infrastructure follows Azure best practices for security, scalability, and cost optimization.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Subscription                       │
├─────────────────────────────────────────────────────────────────┤
│  Resource Group: rg-ai-career-mentor-{environment}            │
│                                                                │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │ Container Apps  │    │   Azure Key     │                   │
│  │   Environment   │    │     Vault       │                   │
│  │                │    │                │                   │
│  │ ┌─────────────┐ │    │ - Secrets Mgmt  │                   │
│  │ │   FastAPI   │ │    │ - RBAC Access   │                   │
│  │ │  Container  │ │    │ - Audit Logs    │                   │
│  │ │    App      │ │    └─────────────────┘                   │
│  │ └─────────────┘ │                                          │
│  └─────────────────┘                                          │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                Azure Services                          │   │
│  │                                                        │   │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │   │
│  │ │   Azure     │ │  Cognitive  │ │  Cosmos DB  │      │   │
│  │ │   OpenAI    │ │   Search    │ │             │      │   │
│  │ │             │ │             │ │ - Sessions  │      │   │
│  │ │ - GPT-4     │ │ - Vector    │ │ - Audit     │      │   │
│  │ │ - Embeddings│ │ - Semantic  │ │ - Serverless│      │   │
│  │ └─────────────┘ └─────────────┘ └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Monitoring & Registry                     │   │
│  │                                                        │   │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │   │
│  │ │  App        │ │ Log         │ │ Container   │      │   │
│  │ │ Insights    │ │ Analytics   │ │ Registry    │      │   │
│  │ │             │ │             │ │             │      │   │
│  │ │ - Metrics   │ │ - Logs      │ │ - Images    │      │   │
│  │ │ - Alerts    │ │ - Queries   │ │ - Security  │      │   │
│  │ └─────────────┘ └─────────────┘ └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Resource Components

### Core Application Services

#### 1. Azure Container Apps
- **Purpose**: Hosts the FastAPI application with automatic scaling
- **Configuration**:
  - Environment-based resource allocation (dev: 0.5 CPU/1GB, prod: 1 CPU/2GB)
  - Auto-scaling: 1-3 replicas (dev), 2-10 replicas (prod)
  - Health checks with liveness and readiness probes
  - HTTPS ingress with custom domain support
- **Security**: Managed identity for Azure service authentication

#### 2. Container Apps Environment
- **Purpose**: Provides the runtime environment for container apps
- **Features**:
  - Integrated Log Analytics workspace
  - Network isolation and security
  - Zone redundancy for production environments

#### 3. Azure Container Registry (ACR)
- **Purpose**: Stores and manages container images
- **Configuration**:
  - Basic tier for dev, Premium for production
  - Admin user enabled for simplified CI/CD
  - Zone redundancy for production
  - Integrated vulnerability scanning

### AI and Search Services

#### 4. Azure OpenAI Service
- **Purpose**: Provides AI capabilities for the chatbot
- **Models Deployed**:
  - **GPT-4**: Main conversational AI model
    - Dev: 20 TPM capacity
    - Prod: 50 TPM capacity
  - **text-embedding-ada-002**: Vector embeddings for RAG
    - Dev: 10 TPM capacity
    - Prod: 30 TPM capacity
- **Security**: API keys stored in Key Vault

#### 5. Azure Cognitive Search
- **Purpose**: Enables RAG functionality with vector and semantic search
- **Configuration**:
  - Basic tier for dev, Standard for production
  - Semantic search enabled
  - HNSW vector search algorithm
  - Custom scoring profiles for relevance tuning
- **Features**:
  - Multi-field search across knowledge base
  - Faceted search and filtering
  - Auto-complete and suggestions

### Data Storage

#### 6. Azure Cosmos DB
- **Purpose**: Stores conversation history and user sessions
- **Configuration**:
  - Serverless billing model for cost optimization
  - Session consistency level
  - Automatic failover for production
  - Free tier for development
- **Collections**:
  - `conversations`: User conversation data
  - Partitioned by `conversation_id`
  - TTL enabled for data retention policies

### Security and Configuration

#### 7. Azure Key Vault
- **Purpose**: Centralized secrets management
- **Stored Secrets**:
  - Azure OpenAI API keys
  - Cognitive Search admin keys
  - Cosmos DB connection strings
  - Application secret keys
- **Security**:
  - RBAC-based access control
  - Audit logging enabled
  - Soft delete protection

### Monitoring and Observability

#### 8. Application Insights
- **Purpose**: Application performance monitoring and analytics
- **Features**:
  - Request/response tracking
  - Dependency monitoring
  - Custom telemetry and metrics
  - Alert rules and notifications
- **Integration**: Connected to Log Analytics workspace

#### 9. Log Analytics Workspace
- **Purpose**: Centralized logging and analysis
- **Configuration**:
  - Retention: 30 days (dev), 90 days (prod)
  - Pay-per-GB pricing model
  - Integration with all Azure services

## Environment Configurations

### Development (dev)
- **Purpose**: Development and testing
- **Resource Sizing**: Minimal resources for cost optimization
- **Features**:
  - Single region deployment
  - Basic service tiers
  - Reduced capacity allocations
  - Free tier services where available

### Production (prod)
- **Purpose**: Production workloads
- **Resource Sizing**: High availability and performance
- **Features**:
  - Zone redundancy
  - Premium service tiers
  - High capacity allocations
  - Multi-replica deployments
  - Enhanced monitoring and alerting

## Security Architecture

### Identity and Access Management
- **Managed Identities**: Container Apps use system-assigned managed identities
- **RBAC**: Role-based access control for all services
- **Service Principals**: Minimal permissions following least privilege principle

### Network Security
- **Private Endpoints**: Available for production environments
- **Network Security Groups**: Configured for Container Apps environment
- **HTTPS Only**: All external communication encrypted

### Secrets Management
- **Azure Key Vault**: Centralized secrets storage
- **Automatic Rotation**: Supported for compatible services
- **Audit Logging**: All secret access logged and monitored

## Deployment Process

### Prerequisites
1. Azure CLI installed and configured
2. Appropriate Azure permissions (Contributor role)
3. Bicep CLI installed
4. Docker for container building

### Deployment Steps

1. **Deploy Infrastructure**:
   ```bash
   ./infrastructure/scripts/deploy.sh \
     -e dev \
     -s "your-subscription-id" \
     -m "your-email@domain.com"
   ```

2. **Build and Push Container**:
   ```bash
   ./infrastructure/scripts/build-push.sh \
     -e dev \
     -r "your-registry-name" \
     -s "your-subscription-id" \
     -g "rg-ai-career-mentor-dev"
   ```

3. **Initialize Knowledge Base**:
   ```bash
   # Run the knowledge seeder script (future enhancement)
   python -m src.services.knowledge_seeder
   ```

### Environment Variables

The following environment variables are automatically configured:

| Variable | Description | Source |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | OpenAI service endpoint | Bicep output |
| `AZURE_OPENAI_KEY` | OpenAI API key | Key Vault secret |
| `AZURE_SEARCH_ENDPOINT` | Search service endpoint | Bicep output |
| `AZURE_SEARCH_KEY` | Search admin key | Key Vault secret |
| `AZURE_COSMOS_ENDPOINT` | Cosmos DB endpoint | Bicep output |
| `AZURE_COSMOS_KEY` | Cosmos DB key | Key Vault secret |
| `AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING` | App Insights connection | Bicep output |

## Cost Optimization

### Development Environment
- **Estimated Monthly Cost**: $50-100 USD
- **Cost Drivers**:
  - Azure OpenAI token usage
  - Container Apps compute time
  - Cosmos DB requests

### Production Environment
- **Estimated Monthly Cost**: $200-500 USD
- **Cost Drivers**:
  - Higher OpenAI capacity
  - Premium service tiers
  - Enhanced monitoring and storage

### Cost Management Strategies
1. **Serverless Services**: Cosmos DB serverless billing
2. **Auto-scaling**: Container Apps scale to zero
3. **Resource Scheduling**: Dev environment shutdown scripts
4. **Monitoring**: Cost alerts and budgets

## Monitoring and Alerting

### Key Metrics
- **Application Performance**: Response times, error rates
- **Service Health**: Service availability, dependency status
- **Resource Utilization**: CPU, memory, storage usage
- **Business Metrics**: Conversation counts, user engagement

### Alert Rules
- **Critical Alerts**: Service outages, high error rates
- **Warning Alerts**: Performance degradation, quota limits
- **Budget Alerts**: Cost thresholds exceeded

## Disaster Recovery

### Backup Strategy
- **Cosmos DB**: Automatic backups with point-in-time recovery
- **Key Vault**: Soft delete and purge protection
- **Container Images**: Geo-replicated ACR (production)

### High Availability
- **Zone Redundancy**: Enabled for production services
- **Auto-failover**: Cosmos DB automatic failover
- **Health Checks**: Automatic container restart on failure

## Scaling Considerations

### Horizontal Scaling
- **Container Apps**: Automatic scaling based on HTTP load and CPU usage
- **Cosmos DB**: Automatic partition scaling
- **Search Service**: Manual replica scaling

### Vertical Scaling
- **OpenAI Models**: Capacity can be increased through Azure portal
- **Container Resources**: CPU and memory limits adjustable
- **Search Tiers**: Service tier upgrades for higher performance

## Compliance and Governance

### Data Residency
- All data stored in specified Azure region
- Cross-region replication only for disaster recovery

### Compliance Features
- **Encryption**: Data encrypted at rest and in transit
- **Audit Logging**: All administrative actions logged
- **Access Controls**: RBAC and managed identities

### Governance
- **Resource Tags**: Consistent tagging for cost allocation
- **Naming Conventions**: Standardized resource naming
- **Policy Compliance**: Azure Policy integration ready

This infrastructure provides a robust, scalable, and secure foundation for the AI Career Mentor Chatbot, following Azure best practices and enabling efficient development, testing, and production operations.