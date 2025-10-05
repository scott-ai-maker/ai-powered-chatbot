#!/bin/bash

# Azure Infrastructure Deployment Script
# ======================================
# 
# This script deploys the AI Career Mentor Chatbot infrastructure to Azure
# using Bicep templates. It supports multiple environments and includes
# proper error handling and logging.

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BICEP_DIR="$PROJECT_ROOT/infrastructure/bicep"

# Default values
ENVIRONMENT="dev"
LOCATION="eastus2"
SUBSCRIPTION_ID=""
RESOURCE_GROUP_PREFIX="rg-ai-career-mentor"
ADMIN_EMAIL=""
DRY_RUN=false
VERBOSE=false

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
usage() {
    cat << EOF
Azure Infrastructure Deployment Script for AI Career Mentor Chatbot

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV       Environment to deploy (dev, staging, prod) [default: dev]
    -l, --location LOCATION     Azure region [default: eastus2]
    -s, --subscription ID       Azure subscription ID (required)
    -g, --resource-group NAME   Resource group name [default: rg-ai-career-mentor-ENV]
    -m, --admin-email EMAIL     Administrator email for notifications (required)
    -d, --dry-run               Validate templates without deploying
    -v, --verbose               Enable verbose output
    -h, --help                  Show this help message

EXAMPLES:
    # Deploy to development environment
    $0 -e dev -s "12345678-1234-1234-1234-123456789012" -m "admin@example.com"

    # Deploy to production with custom resource group
    $0 -e prod -s "12345678-1234-1234-1234-123456789012" -g "rg-chatbot-prod" -m "admin@example.com"

    # Validate templates without deploying
    $0 -e dev -s "12345678-1234-1234-1234-123456789012" -m "admin@example.com" --dry-run

PREREQUISITES:
    - Azure CLI installed and authenticated
    - Contributor access to the target subscription
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
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$SUBSCRIPTION_ID" ]]; then
    log_error "Subscription ID is required. Use -s or --subscription."
    usage
    exit 1
fi

if [[ -z "$ADMIN_EMAIL" ]]; then
    log_error "Admin email is required. Use -m or --admin-email."
    usage
    exit 1
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod."
    exit 1
fi

# Set resource group name
if [[ "$RESOURCE_GROUP_PREFIX" == "rg-ai-career-mentor" ]]; then
    RESOURCE_GROUP_NAME="$RESOURCE_GROUP_PREFIX-$ENVIRONMENT"
else
    RESOURCE_GROUP_NAME="$RESOURCE_GROUP_PREFIX"
fi

# Enable verbose mode if requested
if [[ "$VERBOSE" == "true" ]]; then
    set -x
fi

# Main deployment function
deploy_infrastructure() {
    log_info "Starting deployment of AI Career Mentor Chatbot infrastructure"
    log_info "Environment: $ENVIRONMENT"
    log_info "Location: $LOCATION"
    log_info "Subscription: $SUBSCRIPTION_ID"
    log_info "Resource Group: $RESOURCE_GROUP_NAME"
    log_info "Dry Run: $DRY_RUN"

    # Check prerequisites
    log_info "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi

    # Check Bicep CLI
    if ! az bicep version &> /dev/null; then
        log_info "Installing Bicep CLI..."
        az bicep install
    fi

    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi

    # Set subscription
    log_info "Setting active subscription..."
    az account set --subscription "$SUBSCRIPTION_ID"

    # Verify subscription
    current_sub=$(az account show --query id --output tsv)
    if [[ "$current_sub" != "$SUBSCRIPTION_ID" ]]; then
        log_error "Failed to set subscription to $SUBSCRIPTION_ID"
        exit 1
    fi

    # Check if resource group exists, create if not
    log_info "Checking resource group..."
    if ! az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
        log_info "Creating resource group: $RESOURCE_GROUP_NAME"
        az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION"
        log_success "Resource group created successfully"
    else
        log_info "Resource group already exists: $RESOURCE_GROUP_NAME"
    fi

    # Validate Bicep template
    log_info "Validating Bicep template..."
    if ! az deployment group validate \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --template-file "$BICEP_DIR/main.bicep" \
        --parameters "@$BICEP_DIR/parameters.$ENVIRONMENT.json" \
        --parameters adminEmail="$ADMIN_EMAIL" location="$LOCATION" \
        --output table; then
        log_error "Template validation failed"
        exit 1
    fi
    log_success "Template validation passed"

    # Deploy or dry run
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run completed successfully. No resources were deployed."
        return 0
    fi

    # Deploy the infrastructure
    log_info "Deploying infrastructure..."
    deployment_name="ai-career-mentor-$(date +%Y%m%d-%H%M%S)"
    
    if az deployment group create \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$deployment_name" \
        --template-file "$BICEP_DIR/main.bicep" \
        --parameters "@$BICEP_DIR/parameters.$ENVIRONMENT.json" \
        --parameters adminEmail="$ADMIN_EMAIL" location="$LOCATION" \
        --output table; then
        
        log_success "Infrastructure deployment completed successfully!"
        
        # Get deployment outputs
        log_info "Retrieving deployment outputs..."
        outputs=$(az deployment group show \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --name "$deployment_name" \
            --query properties.outputs --output json)
        
        if [[ -n "$outputs" && "$outputs" != "null" ]]; then
            echo
            log_info "Deployment Outputs:"
            echo "$outputs" | jq -r 'to_entries[] | "  \(.key): \(.value.value)"'
            
            # Save outputs to file
            outputs_file="$PROJECT_ROOT/infrastructure/outputs.$ENVIRONMENT.json"
            echo "$outputs" > "$outputs_file"
            log_info "Outputs saved to: $outputs_file"
        fi
        
        echo
        log_success "🎉 Deployment completed successfully!"
        log_info "Next steps:"
        log_info "  1. Build and push your container image to the created ACR"
        log_info "  2. Update the Container App with your image"
        log_info "  3. Initialize the knowledge base in Azure Cognitive Search"
        
    else
        log_error "Infrastructure deployment failed"
        exit 1
    fi
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