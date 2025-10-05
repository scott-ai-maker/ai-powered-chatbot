#!/bin/bash

# Container Build and Push Script
# ===============================
# 
# This script builds the Docker container for the AI Career Mentor Chatbot
# and pushes it to Azure Container Registry. It supports multi-environment
# builds with proper tagging and security scanning.

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default values
ENVIRONMENT="dev"
IMAGE_TAG=""
REGISTRY_NAME=""
SUBSCRIPTION_ID=""
RESOURCE_GROUP=""
BUILD_NUMBER=""
PUSH_IMAGE=true
SCAN_IMAGE=false
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
Container Build and Push Script for AI Career Mentor Chatbot

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV       Environment (dev, staging, prod) [default: dev]
    -t, --tag TAG              Image tag [default: generated from git/timestamp]
    -r, --registry NAME        Azure Container Registry name (required)
    -s, --subscription ID      Azure subscription ID (required)
    -g, --resource-group NAME  Resource group name (required)
    -b, --build-number NUM     Build number for CI/CD
    --no-push                  Build only, don't push to registry
    --scan                     Enable container security scanning
    -v, --verbose              Enable verbose output
    -h, --help                 Show this help message

EXAMPLES:
    # Build and push for development
    $0 -e dev -r myregistry -s "12345678-1234-1234-1234-123456789012" -g "rg-chatbot-dev"

    # Build with custom tag
    $0 -e prod -t "v1.2.3" -r myregistry -s "12345678-1234-1234-1234-123456789012" -g "rg-chatbot-prod"

    # Build only without pushing
    $0 -e dev -r myregistry -s "12345678-1234-1234-1234-123456789012" -g "rg-chatbot-dev" --no-push

PREREQUISITES:
    - Docker installed and running
    - Azure CLI installed and authenticated
    - Access to the specified Azure Container Registry

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY_NAME="$2"
            shift 2
            ;;
        -s|--subscription)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -b|--build-number)
            BUILD_NUMBER="$2"
            shift 2
            ;;
        --no-push)
            PUSH_IMAGE=false
            shift
            ;;
        --scan)
            SCAN_IMAGE=true
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
if [[ -z "$REGISTRY_NAME" ]]; then
    log_error "Registry name is required. Use -r or --registry."
    usage
    exit 1
fi

if [[ -z "$SUBSCRIPTION_ID" ]]; then
    log_error "Subscription ID is required. Use -s or --subscription."
    usage
    exit 1
fi

if [[ -z "$RESOURCE_GROUP" ]]; then
    log_error "Resource group is required. Use -g or --resource-group."
    usage
    exit 1
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod."
    exit 1
fi

# Generate image tag if not provided
if [[ -z "$IMAGE_TAG" ]]; then
    if [[ -n "$BUILD_NUMBER" ]]; then
        # CI/CD build
        IMAGE_TAG="build-$BUILD_NUMBER"
    elif command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
        # Git-based tag
        git_hash=$(git rev-parse --short HEAD)
        git_branch=$(git rev-parse --abbrev-ref HEAD | sed 's/[^a-zA-Z0-9.-]/-/g')
        if [[ "$git_branch" == "main" || "$git_branch" == "master" ]]; then
            IMAGE_TAG="$git_hash"
        else
            IMAGE_TAG="$git_branch-$git_hash"
        fi
    else
        # Timestamp-based tag
        IMAGE_TAG="$(date +%Y%m%d-%H%M%S)"
    fi
fi

# Set registry login server
REGISTRY_LOGIN_SERVER="$REGISTRY_NAME.azurecr.io"
APP_NAME="ai-career-mentor"
FULL_IMAGE_NAME="$REGISTRY_LOGIN_SERVER/$APP_NAME:$IMAGE_TAG"

# Enable verbose mode if requested
if [[ "$VERBOSE" == "true" ]]; then
    set -x
fi

# Build and push function
build_and_push() {
    log_info "Building and pushing container image"
    log_info "Environment: $ENVIRONMENT"
    log_info "Registry: $REGISTRY_LOGIN_SERVER"
    log_info "Image: $FULL_IMAGE_NAME"
    log_info "Push: $PUSH_IMAGE"

    # Check prerequisites
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH."
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running."
        exit 1
    fi

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed."
        exit 1
    fi

    # Check if logged in to Azure
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi

    # Set subscription
    log_info "Setting active subscription..."
    az account set --subscription "$SUBSCRIPTION_ID"

    # Login to Azure Container Registry
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        log_info "Logging in to Azure Container Registry..."
        az acr login --name "$REGISTRY_NAME"
    fi

    # Build arguments
    BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    VCS_REF=""
    VERSION="$ENVIRONMENT-$IMAGE_TAG"

    if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
        VCS_REF=$(git rev-parse HEAD)
    fi

    # Build the Docker image
    log_info "Building Docker image..."
    cd "$PROJECT_ROOT"
    
    if docker build \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg VCS_REF="$VCS_REF" \
        --build-arg VERSION="$VERSION" \
        --tag "$FULL_IMAGE_NAME" \
        --tag "$REGISTRY_LOGIN_SERVER/$APP_NAME:$ENVIRONMENT-latest" \
        .; then
        log_success "Docker image built successfully"
    else
        log_error "Docker build failed"
        exit 1
    fi

    # Scan image for vulnerabilities if requested
    if [[ "$SCAN_IMAGE" == "true" ]]; then
        log_info "Scanning image for vulnerabilities..."
        if command -v trivy &> /dev/null; then
            trivy image --severity HIGH,CRITICAL "$FULL_IMAGE_NAME"
        else
            log_warning "Trivy not installed. Skipping vulnerability scan."
        fi
    fi

    # Push image to registry
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        log_info "Pushing image to Azure Container Registry..."
        
        if docker push "$FULL_IMAGE_NAME" && \
           docker push "$REGISTRY_LOGIN_SERVER/$APP_NAME:$ENVIRONMENT-latest"; then
            log_success "Image pushed successfully"
            
            # Get image digest
            image_digest=$(az acr repository show-tags \
                --name "$REGISTRY_NAME" \
                --repository "$APP_NAME" \
                --query "[?name=='$IMAGE_TAG'].digest" \
                --output tsv)
            
            if [[ -n "$image_digest" ]]; then
                log_info "Image digest: $image_digest"
            fi
            
        else
            log_error "Failed to push image"
            exit 1
        fi
    else
        log_info "Skipping image push (--no-push specified)"
    fi

    # Output image information
    echo
    log_success "🐳 Container build completed successfully!"
    log_info "Image Details:"
    log_info "  Registry: $REGISTRY_LOGIN_SERVER"
    log_info "  Image: $APP_NAME"
    log_info "  Tag: $IMAGE_TAG"
    log_info "  Full Name: $FULL_IMAGE_NAME"
    log_info "  Environment: $ENVIRONMENT"
    
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        echo
        log_info "Next steps:"
        log_info "  1. Update your Container App with the new image"
        log_info "  2. Deploy using: az containerapp update --name <app-name> --resource-group $RESOURCE_GROUP --image $FULL_IMAGE_NAME"
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

# Run the build and push
build_and_push