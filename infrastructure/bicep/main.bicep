/*
Azure Infrastructure for AI Career Mentor Chatbot
==================================================

This Bicep template creates a complete production-ready infrastructure for the
AI-powered chatbot including:
- Azure Container Apps for hosting the FastAPI application
- Azure OpenAI Service for AI capabilities
- Azure Cognitive Search for RAG functionality
- Azure Cosmos DB for conversation storage
- Azure Key Vault for secrets management
- Azure Application Insights for monitoring
- Azure Container Registry for container images

The infrastructure follows Azure best practices with proper networking,
security, and resource organization.
*/

@description('The name of the application')
param appName string = 'ai-career-mentor'

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for deployment')
param location string = resourceGroup().location

@description('Container image tag to deploy')
param imageTag string = 'latest'

@description('Deployment mode: minimal, infrastructure, or full')
@allowed(['minimal', 'infrastructure', 'full'])
param deploymentMode string = 'infrastructure'

@description('Administrator email for notifications')
param adminEmail string

@description('OpenAI model deployment name')
param openAiModelName string = 'gpt-4'

@description('OpenAI embedding model deployment name')
param openAiEmbeddingModelName string = 'text-embedding-ada-002'

// Naming variables
var resourcePrefix = '${appName}-${environment}'
var containerAppName = '${resourcePrefix}-app'
var containerEnvName = '${resourcePrefix}-env'
var logAnalyticsName = '${resourcePrefix}-logs'
var appInsightsName = '${resourcePrefix}-insights'
var keyVaultName = 'acm${environment}kv${uniqueString(resourceGroup().id)}' // ai-career-mentor -> acm, max 24 chars
var cosmosDbName = '${resourcePrefix}-cosmos'
var openAiName = '${resourcePrefix}-openai'
var searchServiceName = '${resourcePrefix}-search'
var containerRegistryName = 'acm${environment}acr${uniqueString(resourceGroup().id)}' // Alphanumeric only, 5-50 chars

// Common tags applied to all resources
var commonTags = {
  Environment: environment
  Application: appName
  ManagedBy: 'Bicep'
  Owner: adminEmail
  CostCenter: 'Engineering'
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: commonTags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: environment == 'prod' ? 90 : 30
    features: {
      immediatePurgeDataOn30Days: true
    }
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: commonTags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Azure Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: commonTags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenant().tenantId
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: environment == 'prod' ? 90 : 7
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Azure Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: containerRegistryName
  location: location
  tags: commonTags
  sku: {
    name: environment == 'prod' ? 'Premium' : 'Basic'
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: environment == 'prod' ? 'Enabled' : 'Disabled'
  }
}

// Azure Cosmos DB Account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosDbName
  location: location
  tags: commonTags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: environment == 'prod'
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    enableAutomaticFailover: environment == 'prod'
    enableMultipleWriteLocations: false
    isVirtualNetworkFilterEnabled: false
    virtualNetworkRules: []
    ipRules: []
    enableFreeTier: environment == 'dev'
    analyticalStorageConfiguration: {
      schemaType: 'WellDefined'
    }
  }
}

// Cosmos DB Database
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosDbAccount
  name: 'chatbot'
  properties: {
    resource: {
      id: 'chatbot'
    }
  }
}

// Cosmos DB Container for conversations
resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: cosmosDatabase
  name: 'conversations'
  properties: {
    resource: {
      id: 'conversations'
      partitionKey: {
        paths: ['/conversation_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      defaultTtl: environment == 'prod' ? -1 : 2592000 // 30 days for non-prod
    }
  }
}

// Azure OpenAI Service
resource openAiService 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: openAiName
  location: location
  tags: commonTags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// OpenAI GPT-4 Model Deployment
resource openAiGptDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiService
  name: openAiModelName
  properties: {
    model: {
      format: 'OpenAI'
      name: openAiModelName
      version: openAiModelName == 'gpt-4o' ? '2024-08-06' : '2024-02-01'
    }
    raiPolicyName: 'Microsoft.Default'
  }
  sku: {
    name: 'Standard'
    capacity: environment == 'prod' ? 50 : 20
  }
}

// OpenAI Embedding Model Deployment
resource openAiEmbeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAiService
  name: openAiEmbeddingModelName
  dependsOn: [openAiGptDeployment] // Ensure sequential deployment
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-ada-002'
      version: '2'
    }
    raiPolicyName: 'Microsoft.Default'
  }
  sku: {
    name: 'Standard'
    capacity: environment == 'prod' ? 30 : 10
  }
}

// Azure Cognitive Search Service
resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: searchServiceName
  location: location
  tags: commonTags
  sku: {
    name: environment == 'prod' ? 'standard' : 'basic'
  }
  properties: {
    replicaCount: environment == 'prod' ? 2 : 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    networkRuleSet: {
      ipRules: []
    }
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    disableLocalAuth: false
    authOptions: {
      apiKeyOnly: {}
    }
    semanticSearch: environment == 'prod' ? 'standard' : 'free'
  }
}

// Container Apps Environment (only deploy in infrastructure or full mode)
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = if (deploymentMode != 'minimal') {
  name: containerEnvName
  location: location
  tags: commonTags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    zoneRedundant: environment == 'prod'
  }
}

// Container App (only deploy in full mode)
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = if (deploymentMode == 'full') {
  name: containerAppName
  location: location
  tags: commonTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment!.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: 'system'
        }
      ]
      secrets: [
        {
          name: 'azure-openai-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-openai-key'
          identity: 'system'
        }
        {
          name: 'azure-search-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-search-key'
          identity: 'system'
        }
        {
          name: 'azure-cosmos-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-cosmos-key'
          identity: 'system'
        }
        {
          name: 'secret-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/secret-key'
          identity: 'system'
        }
      ]
    }
    template: {
      revisionSuffix: imageTag
      containers: [
        {
          image: imageTag == 'latest' ? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' : '${containerRegistry.properties.loginServer}/${appName}:${imageTag}'
          name: containerAppName
          resources: {
            cpu: json(environment == 'prod' ? '1.0' : '0.5')
            memory: environment == 'prod' ? '2Gi' : '1Gi'
          }
          env: [
            {
              name: 'APP_NAME'
              value: appName
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAiService.properties.endpoint
            }
            {
              name: 'AZURE_OPENAI_KEY'
              secretRef: 'azure-openai-key'
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
              value: openAiModelName
            }
            {
              name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
              value: openAiEmbeddingModelName
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT' 
              value: 'https://${searchService.name}.search.windows.net'
            }
            {
              name: 'AZURE_SEARCH_KEY'
              secretRef: 'azure-search-key'
            }
            {
              name: 'AZURE_SEARCH_INDEX_NAME'
              value: 'career-knowledge'
            }
            {
              name: 'AZURE_COSMOS_ENDPOINT'
              value: cosmosDbAccount.properties.documentEndpoint
            }
            {
              name: 'AZURE_COSMOS_KEY'
              secretRef: 'azure-cosmos-key'
            }
            {
              name: 'AZURE_COSMOS_DATABASE_NAME'
              value: 'chatbot'
            }
            {
              name: 'AZURE_COSMOS_CONTAINER_NAME'
              value: 'conversations'
            }
            {
              name: 'AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
            {
              name: 'SECRET_KEY'
              secretRef: 'secret-key'
            }
            {
              name: 'DEBUG'
              value: environment == 'dev' ? 'true' : 'false'
            }
            {
              name: 'LOG_LEVEL'
              value: environment == 'prod' ? 'INFO' : 'DEBUG'
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              timeoutSeconds: 10
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: environment == 'prod' ? 2 : 1
        maxReplicas: environment == 'prod' ? 10 : 3
        rules: [
          {
            name: 'http-scaler'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
          {
            name: 'cpu-scaler'
            custom: {
              type: 'cpu'
              metadata: {
                type: 'Utilization'
                value: '70'
              }
            }
          }
        ]
      }
    }
  }
}

// Role assignments for Container App managed identity

// Key Vault Secrets User role for Container App
resource containerAppKeyVaultSecretUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deploymentMode == 'full') {
  scope: keyVault
  name: guid(keyVault.id, containerApp!.id, '4633458b-17de-408a-b874-0445c86b69e6')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: containerApp!.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ACR Pull role for Container App
resource containerAppAcrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deploymentMode == 'full') {
  scope: containerRegistry
  name: guid(containerRegistry.id, containerApp!.id, '7f951dda-4ed3-4680-a7ca-43fe172d538d')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: containerApp!.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Store secrets in Key Vault
resource secretKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'secret-key'
  properties: {
    value: base64(guid(resourceGroup().id, appName, environment))
    contentType: 'text/plain'
  }
}

resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-openai-key'
  properties: {
    value: openAiService.listKeys().key1
    contentType: 'text/plain'
  }
}

resource searchKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-search-key'
  properties: {
    value: searchService.listAdminKeys().primaryKey
    contentType: 'text/plain'
  }
}

resource cosmosKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-cosmos-key'
  properties: {
    value: cosmosDbAccount.listKeys().primaryMasterKey
    contentType: 'text/plain'
  }
}

// Outputs
output containerAppUrl string = deploymentMode == 'full' ? containerApp!.properties.configuration.ingress.fqdn : ''
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output keyVaultName string = keyVault.name
output applicationInsightsConnectionString string = appInsights.properties.ConnectionString
output openAiEndpoint string = openAiService.properties.endpoint
output searchServiceEndpoint string = 'https://${searchService.name}.search.windows.net'
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint
output resourceGroupName string = resourceGroup().name
output containerAppName string = deploymentMode == 'full' ? containerApp!.name : containerAppName
output containerAppsEnvironmentName string = deploymentMode != 'minimal' ? containerAppsEnvironment!.name : ''
output environment string = environment
