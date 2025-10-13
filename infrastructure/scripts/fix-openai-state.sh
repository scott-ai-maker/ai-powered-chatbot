#!/bin/bash

# Quick Fix Script for OpenAI Resource Provisioning State Issues
# ============================================================
# 
# This script addresses the specific error where OpenAI resources
# are stuck in non-terminal provisioning states during deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="dev"
RESOURCE_GROUP_NAME="rg-ai-career-mentor-dev"

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

# Function to check and wait for OpenAI service
check_openai_status() {
    local openai_name="ai-career-mentor-$ENVIRONMENT-openai"
    
    log_info "Checking OpenAI service status: $openai_name"
    
    if ! az cognitiveservices account show --name "$openai_name" --resource-group "$RESOURCE_GROUP_NAME" >/dev/null 2>&1; then
        log_info "OpenAI service not found, nothing to wait for"
        return 0
    fi
    
    local max_wait=600  # 10 minutes
    local wait_interval=15
    local elapsed=0
    
    while [[ $elapsed -lt $max_wait ]]; do
        local state=$(az cognitiveservices account show \
            --name "$openai_name" \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --query "properties.provisioningState" \
            -o tsv 2>/dev/null || echo "Unknown")
        
        log_info "Current OpenAI provisioning state: $state"
        
        case "$state" in
            "Succeeded")
                log_success "OpenAI service is ready!"
                return 0
                ;;
            "Failed")
                log_error "OpenAI service failed to provision"
                return 1
                ;;
            "Creating"|"Updating"|"Accepted")
                log_info "OpenAI service still provisioning, waiting..."
                sleep $wait_interval
                elapsed=$((elapsed + wait_interval))
                ;;
            *)
                log_warning "Unknown OpenAI state: $state, continuing to wait..."
                sleep $wait_interval
                elapsed=$((elapsed + wait_interval))
                ;;
        esac
    done
    
    log_warning "OpenAI service did not reach terminal state within $max_wait seconds"
    return 1
}

# Function to check all critical resources
check_all_resources() {
    log_info "Checking status of all critical resources..."
    
    # OpenAI Service
    check_openai_status
    
    # Cosmos DB
    local cosmos_name="ai-career-mentor-$ENVIRONMENT-cosmos"
    if az cosmosdb show --name "$cosmos_name" --resource-group "$RESOURCE_GROUP_NAME" >/dev/null 2>&1; then
        local cosmos_state=$(az cosmosdb show --name "$cosmos_name" --resource-group "$RESOURCE_GROUP_NAME" --query "provisioningState" -o tsv)
        log_info "Cosmos DB state: $cosmos_state"
    fi
    
    # Container Registry
    local acr_name=$(az acr list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    if [[ -n "$acr_name" ]]; then
        local acr_state=$(az acr show --name "$acr_name" --resource-group "$RESOURCE_GROUP_NAME" --query "provisioningState" -o tsv)
        log_info "Container Registry state: $acr_state"
    fi
    
    # Search Service
    local search_name="ai-career-mentor-$ENVIRONMENT-search"
    if az search service show --name "$search_name" --resource-group "$RESOURCE_GROUP_NAME" >/dev/null 2>&1; then
        local search_state=$(az search service show --name "$search_name" --resource-group "$RESOURCE_GROUP_NAME" --query "provisioningState" -o tsv)
        log_info "Search Service state: $search_state"
    fi
}

# Function to retry infrastructure deployment
retry_infrastructure_deployment() {
    log_info "Retrying infrastructure deployment..."
    
    # First, wait for all resources to be ready
    check_all_resources
    
    # Then retry the infrastructure deployment
    local deployment_name="ai-career-mentor-infrastructure-fix-$(date +%Y%m%d-%H%M%S)"
    
    log_info "Starting infrastructure deployment: $deployment_name"
    
    if az deployment group create \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$deployment_name" \
        --template-file "./infrastructure/bicep/main.bicep" \
        --parameters "@./infrastructure/bicep/parameters.$ENVIRONMENT.json" \
        --parameters deploymentMode=infrastructure \
        --parameters adminEmail="${ADMIN_EMAIL:-scott.gordon72@outlook.com}" \
        --parameters location=eastus2 \
        --output table; then
        
        log_success "Infrastructure deployment completed successfully!"
        return 0
    else
        log_error "Infrastructure deployment still failing"
        return 1
    fi
}

# Main function
main() {
    log_info "Starting OpenAI provisioning state fix..."
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                RESOURCE_GROUP_NAME="rg-ai-career-mentor-$ENVIRONMENT"
                shift 2
                ;;
            -g|--resource-group)
                RESOURCE_GROUP_NAME="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    log_info "Environment: $ENVIRONMENT"
    log_info "Resource Group: $RESOURCE_GROUP_NAME"
    
    # Check current resource states
    check_all_resources
    
    # If we're in a script or CI environment, also retry deployment
    if [[ -n "${CI:-}" ]] || [[ "$1" == "--retry-deployment" ]]; then
        retry_infrastructure_deployment
    else
        log_info "Resource check complete. To retry deployment, run:"
        log_info "  $0 --retry-deployment"
    fi
}

# Show help
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    cat << EOF
OpenAI Provisioning State Fix Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV       Environment (dev, staging, prod) [default: dev]
    -g, --resource-group NAME   Resource group name
    --retry-deployment          Also retry the infrastructure deployment
    -h, --help                  Show this help

EXAMPLES:
    # Check resource states
    $0

    # Check and retry deployment
    $0 --retry-deployment

    # Check specific environment
    $0 -e prod --retry-deployment

EOF
    exit 0
fi

# Run main function with all arguments
main "$@"