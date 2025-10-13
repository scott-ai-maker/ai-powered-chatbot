/*
Container App Deployment for AI Career Mentor Chatbot
=====================================================

This template deploys only the Container App and its role assignments.
Used as a second phase after the main infrastructure is deployed.
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

@description('Container Registry login server')
param containerRegistryLoginServer string

@description('Key Vault name')
param keyVaultName string

@description('Container Apps Environment name')
param containerAppsEnvironmentName string

// Naming variables
var resourcePrefix = '${appName}-${environment}'
var containerAppName = '${resourcePrefix}-app'

// Reference existing resources
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: split(containerRegistryLoginServer, '.')[0]
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: containerAppsEnvironmentName
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: imageTag == 'latest' ? 80 : 8000
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
          server: containerRegistryLoginServer
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
          image: imageTag == 'latest' ? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' : '${containerRegistryLoginServer}/${appName}:${imageTag}'
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
              value: 'https://${resourcePrefix}-openai.openai.azure.com/'
            }
            {
              name: 'AZURE_OPENAI_KEY'
              secretRef: 'azure-openai-key'
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
              value: 'gpt-4o'
            }
            {
              name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
              value: 'text-embedding-ada-002'
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: 'https://${resourcePrefix}-search.search.windows.net'
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
              value: 'https://${resourcePrefix}-cosmos.documents.azure.com:443/'
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
              value: 'InstrumentationKey=${reference(resourceId('Microsoft.Insights/components', '${resourcePrefix}-insights'), '2020-02-02-preview').InstrumentationKey};IngestionEndpoint=https://${location}.in.applicationinsights.azure.com/;LiveEndpoint=https://${location}.livediagnostics.monitor.azure.com/'
            }
            {
              name: 'SECRET_KEY'
              secretRef: 'secret-key'
            }
            {
              name: 'DEBUG'
              value: environment == 'prod' ? 'false' : 'true'
            }
            {
              name: 'LOG_LEVEL'
              value: environment == 'prod' ? 'INFO' : 'DEBUG'
            }
          ]
          probes: imageTag == 'latest' ? [
            {
              type: 'Liveness'
              httpGet: {
                path: '/'
                port: 80
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              timeoutSeconds: 10
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/'
                port: 80
              }
              initialDelaySeconds: 10
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
          ] : [
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
        minReplicas: 1
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

// Key Vault Secrets User role for Container App
resource containerAppKeyVaultSecretUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, containerApp.id, '4633458b-17de-408a-b874-0445c86b69e6')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ACR Pull role for Container App
resource containerAppAcrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: containerRegistry
  name: guid(containerRegistry.id, containerApp.id, '7f951dda-4ed3-4680-a7ca-43fe172d538d')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output containerAppUrl string = containerApp.properties.configuration.ingress.fqdn
output containerAppName string = containerApp.name
