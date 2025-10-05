#!/bin/bash

# Azure Deployment Verification Script
# ====================================
# This script verifies that the AI Career Mentor Chatbot is properly deployed

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🔍 AI Career Mentor Chatbot - Deployment Verification"
echo "==================================================="

# Get deployment details
RESOURCE_GROUP="ai-career-mentor-prod-rg"
CONTAINER_APP_NAME="ai-career-mentor-prod-app"

# Check if resource group exists
log_info "Checking resource group: $RESOURCE_GROUP"
if az group show --name $RESOURCE_GROUP &> /dev/null; then
    log_success "Resource group exists"
else
    log_error "Resource group not found. Please run deployment first."
    exit 1
fi

# Get application URL
log_info "Getting application URL..."
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    --output tsv 2>/dev/null || echo "")

if [ -z "$APP_URL" ]; then
    log_error "Could not retrieve application URL"
    exit 1
fi

BASE_URL="https://$APP_URL"
log_info "Application URL: $BASE_URL"

# Test endpoints
test_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local description=$3
    
    log_info "Testing $description..."
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" || echo "000")
    
    if [ "$status_code" == "$expected_status" ]; then
        log_success "$description: HTTP $status_code ✅"
        return 0
    else
        log_error "$description: HTTP $status_code (expected $expected_status) ❌"
        return 1
    fi
}

# Run endpoint tests
test_results=0

echo ""
echo "🧪 Running Endpoint Tests"
echo "========================"

test_endpoint "/" "200" "Main Application" || ((test_results++))
test_endpoint "/health" "200" "Health Check" || ((test_results++))
test_endpoint "/health/ready" "200" "Readiness Probe" || ((test_results++))
test_endpoint "/docs" "200" "API Documentation" || ((test_results++))
test_endpoint "/monitoring/dashboard" "200" "Monitoring Dashboard" || ((test_results++))

# Test API functionality
echo ""
echo "🤖 Testing AI Chat Functionality"
echo "==============================="

log_info "Testing chat endpoint..."
chat_response=$(curl -s -X POST "$BASE_URL/api/v1/chat/message" \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello, can you help me with AI career advice?", "session_id": "test-session"}' \
    2>/dev/null || echo "")

if echo "$chat_response" | grep -q "response"; then
    log_success "Chat API responding ✅"
    echo "Sample response: $(echo "$chat_response" | head -c 100)..."
else
    log_error "Chat API not responding properly ❌"
    ((test_results++))
fi

# Check Azure resources
echo ""
echo "☁️ Checking Azure Resources"
echo "=========================="

# Check Container App status
log_info "Checking Container App status..."
app_status=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.runningStatus \
    --output tsv 2>/dev/null || echo "Unknown")

if [ "$app_status" == "Running" ]; then
    log_success "Container App: $app_status ✅"
else
    log_warning "Container App: $app_status ⚠️"
fi

# Check replicas
replicas=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.template.scale.minReplicas \
    --output tsv 2>/dev/null || echo "0")

log_info "Container replicas: $replicas"

# Get cost estimate
echo ""
echo "💰 Cost Information"
echo "=================="

log_info "Checking current month costs..."
current_cost=$(az consumption usage list \
    --top 5 \
    --query '[0].pretaxCost' \
    --output tsv 2>/dev/null || echo "N/A")

if [ "$current_cost" != "N/A" ]; then
    log_info "Current month cost: \$$current_cost"
else
    log_info "Cost data may take 24-48 hours to appear in Azure Portal"
fi

# Summary
echo ""
echo "📊 Deployment Summary"
echo "===================="

if [ $test_results -eq 0 ]; then
    log_success "All tests passed! 🎉"
    echo ""
    echo "✅ Your AI Career Mentor Chatbot is successfully deployed!"
    echo ""
    echo "🔗 Access URLs:"
    echo "   • Application: $BASE_URL"
    echo "   • API Docs: $BASE_URL/docs"
    echo "   • Monitoring: $BASE_URL/monitoring/dashboard"
    echo ""
    echo "📊 Next Steps:"
    echo "   1. Test the chat functionality thoroughly"
    echo "   2. Monitor costs in Azure Portal"
    echo "   3. Set up budget alerts"
    echo "   4. Plan the multi-app architecture"
    echo ""
else
    log_warning "$test_results test(s) failed"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Check Container App logs: az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP"
    echo "   2. Verify all Azure services are provisioned"
    echo "   3. Check Application Insights for errors"
    echo ""
fi

echo "🎯 Ready to build the remaining 4 applications for your portfolio!"