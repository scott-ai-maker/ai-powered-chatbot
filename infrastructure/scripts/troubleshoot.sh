#!/bin/bash

# AI Career Mentor Infrastructure Troubleshooting & Monitoring Script
# ===================================================================
# 
# This script provides comprehensive troubleshooting and monitoring
# capabilities for the AI Career Mentor infrastructure.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="dev"
RESOURCE_GROUP_NAME="rg-ai-career-mentor-dev"
SUBSCRIPTION_ID=""
WATCH_MODE=false
VERBOSE=false

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

log_debug() {
    echo -e "${CYAN}[DEBUG]${NC} $1" >&2
}

log_section() {
    echo -e "${MAGENTA}[SECTION]${NC} $1" >&2
}

# Show help
show_help() {
    cat << EOF
AI Career Mentor Infrastructure Troubleshooting & Monitoring Script

USAGE:
    ./infrastructure/scripts/troubleshoot.sh [OPTIONS]

OPTIONS:
    -e, --environment ENV       Environment (dev, staging, prod) [default: dev]
    -g, --resource-group NAME   Resource group name [default: rg-ai-career-mentor-ENV]
    -s, --subscription ID       Azure subscription ID
    -w, --watch                 Enable watch mode (continuous monitoring)
    -v, --verbose               Enable verbose output
    -h, --help                  Show this help message

COMMANDS:
    status                      Show overall infrastructure status
    logs                        Show application logs
    health                      Check health of all services
    cleanup                     Clean up stuck/failed resources
    diagnostics                 Run comprehensive diagnostics
    monitor                     Start monitoring mode

EXAMPLES:
    # Show infrastructure status
    ./infrastructure/scripts/troubleshoot.sh status

    # Monitor logs continuously
    ./infrastructure/scripts/troubleshoot.sh logs --watch

    # Run comprehensive diagnostics
    ./infrastructure/scripts/troubleshoot.sh diagnostics --verbose

    # Clean up stuck resources
    ./infrastructure/scripts/troubleshoot.sh cleanup

EOF
}

# Get resource names dynamically
get_resource_names() {
    log_debug "Getting resource names for environment: $ENVIRONMENT"
    
    # Container Registry
    ACR_NAME=$(az acr list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    
    # Key Vault
    KV_NAME=$(az keyvault list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    
    # Container Apps Environment
    CAE_NAME=$(az containerapp env list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    
    # Container App
    CA_NAME=$(az containerapp list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    
    # OpenAI Service
    OPENAI_NAME=$(az cognitiveservices account list --resource-group "$RESOURCE_GROUP_NAME" --query '[?kind==`OpenAI`] | [0].name' -o tsv 2>/dev/null || echo "")
    
    # Search Service
    SEARCH_NAME=$(az search service list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    
    # Cosmos DB
    COSMOS_NAME=$(az cosmosdb list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
}

# Show infrastructure status
show_status() {
    log_section "Infrastructure Status for Environment: $ENVIRONMENT"
    echo
    
    get_resource_names
    
    # Resource Group
    echo -e "${BLUE}Resource Group:${NC}"
    if az group show --name "$RESOURCE_GROUP_NAME" >/dev/null 2>&1; then
        local rg_location=$(az group show --name "$RESOURCE_GROUP_NAME" --query location -o tsv)
        echo -e "  ✅ $RESOURCE_GROUP_NAME (${rg_location})"
    else
        echo -e "  ❌ $RESOURCE_GROUP_NAME (not found)"
        return 1
    fi
    echo
    
    # Core Services
    echo -e "${BLUE}Core Services:${NC}"
    
    # Container Registry
    if [[ -n "$ACR_NAME" ]]; then
        local acr_status=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query provisioningState -o tsv)
        echo -e "  ✅ Container Registry: $ACR_NAME ($acr_status)"
    else
        echo -e "  ❌ Container Registry: Not found"
    fi
    
    # Key Vault
    if [[ -n "$KV_NAME" ]]; then
        echo -e "  ✅ Key Vault: $KV_NAME"
    else
        echo -e "  ❌ Key Vault: Not found"
    fi
    
    # OpenAI Service
    if [[ -n "$OPENAI_NAME" ]]; then
        local openai_status=$(az cognitiveservices account show --name "$OPENAI_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query provisioningState -o tsv)
        echo -e "  ✅ OpenAI Service: $OPENAI_NAME ($openai_status)"
    else
        echo -e "  ❌ OpenAI Service: Not found"
    fi
    
    # Search Service
    if [[ -n "$SEARCH_NAME" ]]; then
        local search_status=$(az search service show --name "$SEARCH_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query status -o tsv)
        echo -e "  ✅ Search Service: $SEARCH_NAME ($search_status)"
    else
        echo -e "  ❌ Search Service: Not found"
    fi
    
    # Cosmos DB
    if [[ -n "$COSMOS_NAME" ]]; then
        echo -e "  ✅ Cosmos DB: $COSMOS_NAME"
    else
        echo -e "  ❌ Cosmos DB: Not found"
    fi
    echo
    
    # Container Services
    echo -e "${BLUE}Container Services:${NC}"
    
    # Container Apps Environment
    if [[ -n "$CAE_NAME" ]]; then
        local cae_status=$(az containerapp env show --name "$CAE_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query properties.provisioningState -o tsv)
        echo -e "  ✅ Container Apps Environment: $CAE_NAME ($cae_status)"
    else
        echo -e "  ❌ Container Apps Environment: Not found"
    fi
    
    # Container App
    if [[ -n "$CA_NAME" ]]; then
        local ca_status=$(az containerapp show --name "$CA_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query properties.provisioningState -o tsv)
        local ca_url=$(az containerapp show --name "$CA_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query properties.configuration.ingress.fqdn -o tsv 2>/dev/null || echo "")
        echo -e "  ✅ Container App: $CA_NAME ($ca_status)"
        if [[ -n "$ca_url" ]]; then
            echo -e "     🌐 URL: https://$ca_url"
        fi
    else
        echo -e "  ❌ Container App: Not found"
    fi
}

# Show application logs
show_logs() {
    log_section "Application Logs"
    
    get_resource_names
    
    if [[ -z "$CA_NAME" ]]; then
        log_error "No Container App found in resource group"
        return 1
    fi
    
    log_info "Fetching logs for Container App: $CA_NAME"
    
    if [[ "$WATCH_MODE" == "true" ]]; then
        log_info "Starting log streaming (Press Ctrl+C to stop)..."
        az containerapp logs show \
            --name "$CA_NAME" \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --follow
    else
        az containerapp logs show \
            --name "$CA_NAME" \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --tail 100
    fi
}

# Check health of all services
check_health() {
    log_section "Health Check"
    
    get_resource_names
    
    local health_score=0
    local total_checks=0
    
    # Check Container App health
    if [[ -n "$CA_NAME" ]]; then
        ((total_checks++))
        local ca_url=$(az containerapp show --name "$CA_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query properties.configuration.ingress.fqdn -o tsv 2>/dev/null || echo "")
        
        if [[ -n "$ca_url" ]]; then
            log_info "Checking Container App health endpoint..."
            if curl -s -f --max-time 10 "https://$ca_url/health" >/dev/null 2>&1; then
                log_success "Container App is healthy"
                ((health_score++))
            else
                log_warning "Container App health check failed"
            fi
        else
            log_warning "Container App has no public URL"
        fi
    fi
    
    # Check Key Vault access
    if [[ -n "$KV_NAME" ]]; then
        ((total_checks++))
        log_info "Checking Key Vault access..."
        if az keyvault secret list --vault-name "$KV_NAME" >/dev/null 2>&1; then
            log_success "Key Vault is accessible"
            ((health_score++))
        else
            log_warning "Key Vault access failed"
        fi
    fi
    
    # Check Container Registry
    if [[ -n "$ACR_NAME" ]]; then
        ((total_checks++))
        log_info "Checking Container Registry..."
        if az acr repository list --name "$ACR_NAME" >/dev/null 2>&1; then
            log_success "Container Registry is accessible"
            ((health_score++))
        else
            log_warning "Container Registry access failed"
        fi
    fi
    
    # Display health summary
    echo
    local health_percentage=$((health_score * 100 / total_checks))
    if [[ $health_percentage -ge 80 ]]; then
        log_success "Overall Health: $health_score/$total_checks ($health_percentage%) - GOOD"
    elif [[ $health_percentage -ge 60 ]]; then
        log_warning "Overall Health: $health_score/$total_checks ($health_percentage%) - FAIR"
    else
        log_error "Overall Health: $health_score/$total_checks ($health_percentage%) - POOR"
    fi
}

# Clean up stuck resources
cleanup_resources() {
    log_section "Resource Cleanup"
    
    get_resource_names
    
    log_warning "This will delete stuck Container App resources. Continue? (y/N)"
    read -r confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log_info "Cleanup cancelled"
        return 0
    fi
    
    # Clean up Container Apps
    if [[ -n "$CA_NAME" ]]; then
        log_info "Deleting Container App: $CA_NAME"
        az containerapp delete --name "$CA_NAME" --resource-group "$RESOURCE_GROUP_NAME" --yes || true
    fi
    
    # Clean up Container Apps Environment
    if [[ -n "$CAE_NAME" ]]; then
        log_info "Deleting Container Apps Environment: $CAE_NAME"
        az containerapp env delete --name "$CAE_NAME" --resource-group "$RESOURCE_GROUP_NAME" --yes || true
    fi
    
    log_success "Cleanup completed"
    log_info "You can now redeploy using the robust deployment script"
}

# Run comprehensive diagnostics
run_diagnostics() {
    log_section "Comprehensive Diagnostics"
    
    # Check Azure CLI
    log_info "Checking Azure CLI..."
    az --version
    echo
    
    # Check current subscription
    log_info "Current Azure subscription:"
    az account show --query '{name:name, id:id, tenantId:tenantId}' --output table
    echo
    
    # Check resource providers
    log_info "Checking resource providers..."
    local providers=("Microsoft.ContainerRegistry" "Microsoft.App" "Microsoft.KeyVault" "Microsoft.CognitiveServices" "Microsoft.Search" "Microsoft.DocumentDB")
    
    for provider in "${providers[@]}"; do
        local state=$(az provider show --namespace "$provider" --query registrationState -o tsv)
        if [[ "$state" == "Registered" ]]; then
            echo -e "  ✅ $provider: $state"
        else
            echo -e "  ❌ $provider: $state"
        fi
    done
    echo
    
    # Show infrastructure status
    show_status
    echo
    
    # Check health
    check_health
    echo
    
    # Check recent deployments
    log_info "Recent deployments:"
    az deployment group list --resource-group "$RESOURCE_GROUP_NAME" --query '[0:5].{Name:name, State:properties.provisioningState, Timestamp:properties.timestamp}' --output table 2>/dev/null || echo "No deployments found"
}

# Monitor mode
start_monitoring() {
    log_section "Starting Monitoring Mode"
    log_info "Press Ctrl+C to stop monitoring"
    
    while true; do
        clear
        echo "=== AI Career Mentor Infrastructure Monitor ==="
        echo "Environment: $ENVIRONMENT | $(date)"
        echo "=============================================="
        echo
        
        show_status
        echo
        check_health
        
        echo
        log_info "Next update in 30 seconds..."
        sleep 30
    done
}

# Main function
main() {
    local command="${1:-status}"
    
    case "$command" in
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        health)
            check_health
            ;;
        cleanup)
            cleanup_resources
            ;;
        diagnostics)
            run_diagnostics
            ;;
        monitor)
            start_monitoring
            ;;
        *)
            echo "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Parse command line arguments
COMMAND=""
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
        -s|--subscription)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        -w|--watch)
            WATCH_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            set -x
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        status|logs|health|cleanup|diagnostics|monitor)
            COMMAND="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set subscription if provided
if [[ -n "$SUBSCRIPTION_ID" ]]; then
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Run the specified command
main "$COMMAND"