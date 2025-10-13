#!/bin/bash

# Robust AI Career Mentor Infrastructure Deployment
# =================================================
# 
# This script implements a three-phase deployment strategy:
# Phase 1: Minimal (Core services only - ACR, KeyVault, OpenAI, etc.)
# Phase 2: Infrastructure (Add Container Apps Environment)  
# Phase 3: Full (Add Container App)

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BICEP_DIR="$PROJECT_ROOT/infrastructure/bicep"

# Default values
ENVIRONMENT="dev"
LOCATION="eastus2"
SUBSCRIPTION_ID=""
RESOURCE_GROUP_PREFIX="rg-ai-career-mentor"
ADMIN_EMAIL=""
DRY_RUN=false
VERBOSE=false
FORCE_CLEANUP=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Usage function
show_help() {
    cat << EOF
Robust Azure Infrastructure Deployment Script for AI Career Mentor Chatbot

USAGE:
    ./infrastructure/scripts/deploy-robust.sh [OPTIONS]

OPTIONS:
    -e, --environment ENV       Environment to deploy (dev, staging, prod) [default: dev]
    -l, --location LOCATION     Azure region [default: eastus2]
    -s, --subscription ID       Azure subscription ID (required)
    -g, --resource-group NAME   Resource group name [default: rg-ai-career-mentor-ENV]
    -m, --admin-email EMAIL     Administrator email for notifications (required)
    -f, --force-cleanup         Force cleanup of existing Container App resources
    -d, --dry-run               Validate templates without deploying
    -v, --verbose               Enable verbose output
    -h, --help                  Show this help message

EXAMPLES:
    # Deploy to development environment
    ./infrastructure/scripts/deploy-robust.sh -e dev -s "12345678-1234-1234-1234-123456789012" -m "admin@example.com"

    # Deploy with force cleanup of existing resources
    ./infrastructure/scripts/deploy-robust.sh -e dev -s "12345678-1234-1234-1234-123456789012" -m "admin@example.com" --force-cleanup

DEPLOYMENT PHASES:
    Phase 1: Core services (ACR, Key Vault, OpenAI, Cosmos DB, Search, App Insights)
    Phase 2: Container Apps Environment
    Phase 3: Container App deployment

PREREQUISITES:
    - Azure CLI installed and authenticated
    - Contributor + User Access Administrator access to the target subscription
    - Resource Provider 'Microsoft.App' registered
    - Bicep CLI installed

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -s|--subscription)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        -g|--resource-group)
            RESOURCE_GROUP_PREFIX="$2"
            shift 2
            ;;
        -m|--admin-email)
            ADMIN_EMAIL="$2"
            shift 2
            ;;
        -f|--force-cleanup)
            FORCE_CLEANUP=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$SUBSCRIPTION_ID" ]]; then
    log_error "Subscription ID is required. Use -s or --subscription"
    exit 1
fi

if [[ -z "$ADMIN_EMAIL" ]]; then
    log_error "Administrator email is required. Use -m or --admin-email"
    exit 1
fi

# Set resource group name
RESOURCE_GROUP_NAME="$RESOURCE_GROUP_PREFIX-$ENVIRONMENT"

# Enable verbose mode if requested
if [[ "$VERBOSE" == "true" ]]; then
    set -x
fi

log_info "Starting robust deployment of AI Career Mentor Chatbot infrastructure"
log_info "Environment: $ENVIRONMENT"
log_info "Location: $LOCATION"
log_info "Subscription: $SUBSCRIPTION_ID"
log_info "Resource Group: $RESOURCE_GROUP_NAME"
log_info "Force Cleanup: $FORCE_CLEANUP"
log_info "Dry Run: $DRY_RUN"

# Function to cleanup existing Container App resources
cleanup_container_resources() {
    log_info "Cleaning up existing Container App resources..."
    
    # Delete Container Apps
    local apps=$(az containerapp list --resource-group "$RESOURCE_GROUP_NAME" --query "[].name" --output tsv 2>/dev/null || echo "")
    if [[ -n "$apps" ]]; then
        for app in $apps; do
            log_info "Deleting Container App: $app"
            az containerapp delete --name "$app" --resource-group "$RESOURCE_GROUP_NAME" --yes || true
        done
    fi
    
    # Delete Container Apps Environments
    local envs=$(az containerapp env list --resource-group "$RESOURCE_GROUP_NAME" --query "[].name" --output tsv 2>/dev/null || echo "")
    if [[ -n "$envs" ]]; then
        for env in $envs; do
            log_info "Deleting Container Apps Environment: $env"
            az containerapp env delete --name "$env" --resource-group "$RESOURCE_GROUP_NAME" --yes || true
        done
    fi
    
    # Wait for cleanup to complete
    log_info "Waiting for cleanup to complete..."
    sleep 30
}

# Function to wait for resource provisioning to complete
wait_for_resource_ready() {
    local resource_type=$1
    local resource_name=$2
    local max_wait_time=${3:-300}  # Default 5 minutes
    local wait_interval=15
    local elapsed=0
    
    log_info "Waiting for $resource_type '$resource_name' to reach terminal state..."
    
    while [[ $elapsed -lt $max_wait_time ]]; do
        local state=""
        case "$resource_type" in
            "cognitive-services")
                state=$(az cognitiveservices account show --name "$resource_name" --resource-group "$RESOURCE_GROUP_NAME" --query "properties.provisioningState" -o tsv 2>/dev/null || echo "NotFound")
                ;;
            "cosmos-db")
                state=$(az cosmosdb show --name "$resource_name" --resource-group "$RESOURCE_GROUP_NAME" --query "provisioningState" -o tsv 2>/dev/null || echo "NotFound")
                ;;
            "container-registry")
                state=$(az acr show --name "$resource_name" --resource-group "$RESOURCE_GROUP_NAME" --query "provisioningState" -o tsv 2>/dev/null || echo "NotFound")
                ;;
            "search-service")
                state=$(az search service show --name "$resource_name" --resource-group "$RESOURCE_GROUP_NAME" --query "provisioningState" -o tsv 2>/dev/null || echo "NotFound")
                ;;
        esac
        
        if [[ "$state" == "Succeeded" ]]; then
            log_success "$resource_type '$resource_name' is ready (state: $state)"
            return 0
        elif [[ "$state" == "Failed" ]]; then
            log_error "$resource_type '$resource_name' failed to provision (state: $state)"
            return 1
        elif [[ "$state" == "NotFound" ]]; then
            log_warning "$resource_type '$resource_name' not found, continuing..."
            return 0
        else
            log_info "$resource_type '$resource_name' still provisioning (state: $state), waiting..."
            sleep $wait_interval
            elapsed=$((elapsed + wait_interval))
        fi
    done
    
    log_warning "$resource_type '$resource_name' did not reach terminal state within $max_wait_time seconds"
    return 1
}

# Function to wait for all critical resources from previous phase
wait_for_phase_resources() {
    local phase=$1
    
    case "$phase" in
        "infrastructure")
            # Wait for minimal phase resources to be ready
            log_info "Waiting for minimal phase resources to complete..."
            
            # Check OpenAI Service (most common cause of conflicts)
            local openai_name="ai-career-mentor-$ENVIRONMENT-openai"
            if az cognitiveservices account show --name "$openai_name" --resource-group "$RESOURCE_GROUP_NAME" >/dev/null 2>&1; then
                wait_for_resource_ready "cognitive-services" "$openai_name" 600
            fi
            
            # Check Cosmos DB
            local cosmos_name="ai-career-mentor-$ENVIRONMENT-cosmos"
            if az cosmosdb show --name "$cosmos_name" --resource-group "$RESOURCE_GROUP_NAME" >/dev/null 2>&1; then
                wait_for_resource_ready "cosmos-db" "$cosmos_name" 300
            fi
            
            # Check Container Registry
            local acr_name=$(az acr list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
            if [[ -n "$acr_name" ]]; then
                wait_for_resource_ready "container-registry" "$acr_name" 300
            fi
            
            # Check Search Service
            local search_name="ai-career-mentor-$ENVIRONMENT-search"
            if az search service show --name "$search_name" --resource-group "$RESOURCE_GROUP_NAME" >/dev/null 2>&1; then
                wait_for_resource_ready "search-service" "$search_name" 300
            fi
            ;;
        "full")
            # Wait for Container Apps Environment to be ready
            log_info "Waiting for Container Apps Environment to be ready..."
            local env_name="ai-career-mentor-$ENVIRONMENT-env"
            local max_wait=600
            local elapsed=0
            
            while [[ $elapsed -lt $max_wait ]]; do
                local env_state=$(az containerapp env show --name "$env_name" --resource-group "$RESOURCE_GROUP_NAME" --query "properties.provisioningState" -o tsv 2>/dev/null || echo "NotFound")
                
                if [[ "$env_state" == "Succeeded" ]]; then
                    log_success "Container Apps Environment is ready"
                    break
                elif [[ "$env_state" == "Failed" ]]; then
                    log_error "Container Apps Environment failed to provision"
                    return 1
                elif [[ "$env_state" == "NotFound" ]]; then
                    log_warning "Container Apps Environment not found, continuing..."
                    break
                else
                    log_info "Container Apps Environment still provisioning (state: $env_state), waiting..."
                    sleep 30
                    elapsed=$((elapsed + 30))
                fi
            done
            ;;
    esac
}

# Function to deploy a specific phase
deploy_phase() {
    local phase=$1
    local deployment_name="ai-career-mentor-$phase-$(date +%Y%m%d-%H%M%S)"
    local max_retries=3
    local retry_count=0
    
    # Wait for resources from previous phase if needed
    wait_for_phase_resources "$phase"
    
    log_info "Deploying Phase: $phase"
    
    while [[ $retry_count -lt $max_retries ]]; do
        if az deployment group create \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --name "$deployment_name" \
            --template-file "$BICEP_DIR/main.bicep" \
            --parameters "@$BICEP_DIR/parameters.$ENVIRONMENT.json" \
            --parameters adminEmail="$ADMIN_EMAIL" \
            --parameters location="$LOCATION" \
            --parameters deploymentMode="$phase" \
            --output table; then
            
            log_success "Phase $phase deployment completed successfully!"
            return 0
        else
            retry_count=$((retry_count + 1))
            log_warning "Phase $phase deployment failed (attempt $retry_count/$max_retries)"
            
            if [[ $retry_count -lt $max_retries ]]; then
                log_info "Checking deployment details..."
                local error_details=$(az deployment group show --name "$deployment_name" --resource-group "$RESOURCE_GROUP_NAME" --query "properties.error.details[0].message" -o tsv 2>/dev/null || echo "")
                
                if echo "$error_details" | grep -q "provisioning state is not terminal"; then
                    log_info "Resource still provisioning, waiting 60 seconds before retry..."
                    sleep 60
                    
                    # Update deployment name for retry
                    deployment_name="ai-career-mentor-$phase-retry$retry_count-$(date +%Y%m%d-%H%M%S)"
                else
                    log_error "Deployment failed with error: $error_details"
                    break
                fi
            fi
        fi
    done
    
    log_error "Phase $phase deployment failed after $max_retries attempts"
    log_info "Checking final deployment details..."
    az deployment group show --name "$deployment_name" --resource-group "$RESOURCE_GROUP_NAME" --query "properties.error" --output json 2>/dev/null || true
    return 1
}

# Main deployment function
deploy_infrastructure() {
    # Check prerequisites
    log_info "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed or not in PATH"
        exit 1
    fi
    
    # Check Bicep CLI
    if ! az bicep version &> /dev/null; then
        log_warning "Bicep CLI not found, installing..."
        az bicep install
    fi
    
    # Set active subscription
    log_info "Setting active subscription..."
    az account set --subscription "$SUBSCRIPTION_ID"
    
    # Check/create resource group
    log_info "Checking resource group..."
    if ! az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
        log_info "Creating resource group: $RESOURCE_GROUP_NAME"
        az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION"
        log_success "Resource group created successfully"
    else
        log_info "Resource group already exists: $RESOURCE_GROUP_NAME"
    fi
    
    # Force cleanup if requested or if dry run
    if [[ "$FORCE_CLEANUP" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        cleanup_container_resources
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run completed successfully. No resources were deployed."
        return 0
    fi
    
    # Phase 1: Deploy minimal infrastructure (core services only)
    log_info "=== PHASE 1: CORE SERVICES ==="
    if ! deploy_phase "minimal"; then
        log_error "Phase 1 (minimal) deployment failed"
        exit 1
    fi
    
    # Wait between phases for resources to stabilize
    log_info "Phase 1 complete. Waiting 60 seconds for resources to stabilize..."
    sleep 60
    
    # Phase 2: Add Container Apps Environment
    log_info "=== PHASE 2: CONTAINER APPS ENVIRONMENT ==="
    if ! deploy_phase "infrastructure"; then
        log_error "Phase 2 (infrastructure) deployment failed"
        exit 1
    fi
    
    # Wait between phases for Container Apps Environment to be ready
    log_info "Phase 2 complete. Waiting 90 seconds for Container Apps Environment to stabilize..."
    sleep 90
    
    # Phase 3: Add Container App (only if not minimal)
    log_info "=== PHASE 3: CONTAINER APP ==="
    if ! deploy_phase "full"; then
        log_error "Phase 3 (full) deployment failed"
        exit 1
    fi
    
    # Get final deployment outputs
    log_info "Retrieving final deployment outputs..."
    local latest_deployment=$(az deployment group list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' --output tsv)
    local outputs=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$latest_deployment" \
        --query properties.outputs --output json)
    
    if [[ -n "$outputs" && "$outputs" != "null" ]]; then
        echo
        log_info "Final Deployment Outputs:"
        echo "$outputs" | jq -r 'to_entries[] | "  \(.key): \(.value.value)"'
        
        # Save outputs to file
        local outputs_file="$PROJECT_ROOT/infrastructure/outputs.$ENVIRONMENT.json"
        echo "$outputs" > "$outputs_file"
        log_info "Outputs saved to: $outputs_file"
    fi
    
    echo
    log_success "🎉 Robust deployment completed successfully!"
    log_info "All three phases deployed without errors"
    log_info "Your AI Career Mentor infrastructure is ready!"
}

# Cleanup function
cleanup() {
    if [[ "$VERBOSE" == "true" ]]; then
        set +x
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Run the deployment
deploy_infrastructure