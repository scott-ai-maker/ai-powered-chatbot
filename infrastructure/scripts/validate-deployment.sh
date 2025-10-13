#!/bin/bash

# Validation and Testing Script for AI Career Mentor Infrastructure
# ================================================================
# 
# This script validates the infrastructure deployment and tests all components

set -euo pipefail

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

# Configuration
ENVIRONMENT="dev"
RESOURCE_GROUP_NAME="rg-ai-career-mentor-dev"
SUBSCRIPTION_ID=""

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Test functions
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    ((TESTS_TOTAL++))
    log_info "Running test: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        log_success "✓ $test_name"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "✗ $test_name"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Validate Azure CLI setup
validate_azure_cli() {
    log_info "=== Validating Azure CLI Setup ==="
    
    run_test "Azure CLI installed" "command -v az"
    run_test "Azure CLI authenticated" "az account show"
    run_test "Correct subscription selected" "az account show --query 'id' -o tsv | grep -q ."
    
    if [[ -n "$SUBSCRIPTION_ID" ]]; then
        run_test "Target subscription accessible" "az account set --subscription '$SUBSCRIPTION_ID'"
    fi
}

# Validate resource group
validate_resource_group() {
    log_info "=== Validating Resource Group ==="
    
    run_test "Resource group exists" "az group show --name '$RESOURCE_GROUP_NAME'"
    run_test "Resource group in correct location" "az group show --name '$RESOURCE_GROUP_NAME' --query location -o tsv | grep -q ."
}

# Validate core services
validate_core_services() {
    log_info "=== Validating Core Services ==="
    
    # Azure Container Registry
    run_test "Container Registry exists" "az acr list --resource-group '$RESOURCE_GROUP_NAME' --query '[0].name' -o tsv | grep -q ."
    
    # Key Vault
    run_test "Key Vault exists" "az keyvault list --resource-group '$RESOURCE_GROUP_NAME' --query '[0].name' -o tsv | grep -q ."
    
    # OpenAI Service
    run_test "OpenAI Service exists" "az cognitiveservices account list --resource-group '$RESOURCE_GROUP_NAME' --query '[?kind==\`OpenAI\`] | [0].name' -o tsv | grep -q ."
    
    # Cosmos DB
    run_test "Cosmos DB exists" "az cosmosdb list --resource-group '$RESOURCE_GROUP_NAME' --query '[0].name' -o tsv | grep -q ."
    
    # Search Service
    run_test "Search Service exists" "az search service list --resource-group '$RESOURCE_GROUP_NAME' --query '[0].name' -o tsv | grep -q ."
    
    # Application Insights
    run_test "Application Insights exists" "az monitor app-insights component show --resource-group '$RESOURCE_GROUP_NAME' --query '[0].name' -o tsv | grep -q ."
}

# Validate Container Apps Environment
validate_container_environment() {
    log_info "=== Validating Container Apps Environment ==="
    
    run_test "Container Apps Environment exists" "az containerapp env list --resource-group '$RESOURCE_GROUP_NAME' --query '[0].name' -o tsv | grep -q ."
    
    local env_name=$(az containerapp env list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    if [[ -n "$env_name" ]]; then
        run_test "Container Apps Environment is ready" "az containerapp env show --name '$env_name' --resource-group '$RESOURCE_GROUP_NAME' --query 'properties.provisioningState' -o tsv | grep -q 'Succeeded'"
    fi
}

# Validate Container App
validate_container_app() {
    log_info "=== Validating Container App ==="
    
    run_test "Container App exists" "az containerapp list --resource-group '$RESOURCE_GROUP_NAME' --query '[0].name' -o tsv | grep -q ."
    
    local app_name=$(az containerapp list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    if [[ -n "$app_name" ]]; then
        run_test "Container App is running" "az containerapp show --name '$app_name' --resource-group '$RESOURCE_GROUP_NAME' --query 'properties.provisioningState' -o tsv | grep -q 'Succeeded'"
        run_test "Container App has public endpoint" "az containerapp show --name '$app_name' --resource-group '$RESOURCE_GROUP_NAME' --query 'properties.configuration.ingress.fqdn' -o tsv | grep -q ."
    fi
}

# Validate networking and connectivity
validate_networking() {
    log_info "=== Validating Networking ==="
    
    # Check if Container App is accessible
    local app_name=$(az containerapp list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    if [[ -n "$app_name" ]]; then
        local fqdn=$(az containerapp show --name "$app_name" --resource-group "$RESOURCE_GROUP_NAME" --query 'properties.configuration.ingress.fqdn' -o tsv 2>/dev/null || echo "")
        if [[ -n "$fqdn" ]]; then
            run_test "Container App health endpoint responds" "curl -s -f --max-time 10 'https://$fqdn/health'"
        fi
    fi
}

# Validate security configuration
validate_security() {
    log_info "=== Validating Security Configuration ==="
    
    # Check Key Vault access policies
    local kv_name=$(az keyvault list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    if [[ -n "$kv_name" ]]; then
        run_test "Key Vault has access policies" "az keyvault show --name '$kv_name' --resource-group '$RESOURCE_GROUP_NAME' --query 'properties.accessPolicies[0]' -o tsv | grep -q ."
    fi
    
    # Check managed identity assignments
    local app_name=$(az containerapp list --resource-group "$RESOURCE_GROUP_NAME" --query '[0].name' -o tsv 2>/dev/null || echo "")
    if [[ -n "$app_name" ]]; then
        run_test "Container App has managed identity" "az containerapp show --name '$app_name' --resource-group '$RESOURCE_GROUP_NAME' --query 'identity.type' -o tsv | grep -q 'SystemAssigned'"
    fi
}

# Generate validation report
generate_report() {
    echo
    log_info "=== VALIDATION REPORT ==="
    log_info "Total tests: $TESTS_TOTAL"
    log_success "Passed: $TESTS_PASSED"
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        log_error "Failed: $TESTS_FAILED"
        echo
        log_error "Some validation tests failed. Please review the infrastructure deployment."
        return 1
    else
        echo
        log_success "🎉 All validation tests passed!"
        log_success "Your AI Career Mentor infrastructure is properly deployed and configured."
        return 0
    fi
}

# Main validation function
main() {
    log_info "Starting validation of AI Career Mentor infrastructure..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Resource Group: $RESOURCE_GROUP_NAME"
    
    validate_azure_cli
    validate_resource_group
    validate_core_services
    validate_container_environment
    validate_container_app
    validate_networking
    validate_security
    
    generate_report
}

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
        -s|--subscription)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [-e environment] [-g resource-group] [-s subscription-id]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run validation
main