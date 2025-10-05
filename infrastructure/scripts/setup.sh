#!/bin/bash

# AI Career Mentor Chatbot - Quick Setup Script
# =============================================
# 
# This script helps set up the development environment and deploy
# the infrastructure for the AI Career Mentor Chatbot.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="AI Career Mentor Chatbot"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${PURPLE}[SETUP]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup function
main() {
    clear
    echo -e "${PURPLE}"
    cat << "EOF"
    ╔═══════════════════════════════════════════════════════════╗
    ║           AI Career Mentor Chatbot Setup                 ║
    ║                                                           ║
    ║   🤖 RAG-Enhanced Career Guidance System                 ║
    ║   ☁️  Azure Cloud Infrastructure                         ║
    ║   🚀 Production-Ready Deployment                         ║
    ╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    log_header "Starting setup process..."
    
    # Check prerequisites
    check_prerequisites
    
    # Setup development environment
    setup_development_environment
    
    # Provide deployment instructions
    provide_deployment_instructions
    
    log_success "🎉 Setup completed successfully!"
    echo
    log_info "Your AI Career Mentor Chatbot is ready for development and deployment!"
}

# Check prerequisites
check_prerequisites() {
    log_header "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check Python
    if command_exists python3; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python $python_version installed"
    else
        missing_tools+=("python3")
    fi
    
    # Check pip
    if command_exists pip3; then
        log_success "pip3 installed"
    else
        missing_tools+=("pip3")
    fi
    
    # Check Git
    if command_exists git; then
        local git_version=$(git --version | cut -d' ' -f3)
        log_success "Git $git_version installed"
    else
        missing_tools+=("git")
    fi
    
    # Check Docker (optional but recommended)
    if command_exists docker; then
        local docker_version=$(docker --version | cut -d' ' -f3 | tr -d ',')
        log_success "Docker $docker_version installed"
    else
        log_warning "Docker not found (optional for local development)"
    fi
    
    # Check Azure CLI (optional for deployment)
    if command_exists az; then
        local az_version=$(az version --query '"azure-cli"' -o tsv)
        log_success "Azure CLI $az_version installed"
    else
        log_warning "Azure CLI not found (required for Azure deployment)"
    fi
    
    # Report missing tools
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        echo
        log_info "Please install the missing tools and run this script again."
        log_info "Installation guides:"
        log_info "  Python: https://www.python.org/downloads/"
        log_info "  Git: https://git-scm.com/downloads"
        log_info "  Docker: https://docs.docker.com/get-docker/"
        log_info "  Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    log_success "All prerequisites are installed!"
}

# Setup development environment
setup_development_environment() {
    log_header "Setting up development environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv .venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment and install dependencies
    log_info "Installing Python dependencies..."
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Production dependencies installed"
    fi
    
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
        log_success "Development dependencies installed"
    fi
    
    # Create .env template if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating .env template..."
        cat > .env << 'EOF'
# AI Career Mentor Chatbot Environment Configuration
# =================================================
# Copy this file to .env and fill in your actual values

# Application Settings
APP_NAME=AI Career Mentor Chatbot
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=DEBUG
SECRET_KEY=your-secret-key-here

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-api-key
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Azure Cognitive Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-admin-key
AZURE_SEARCH_INDEX_NAME=career-knowledge

# Azure Cosmos DB Configuration
AZURE_COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
AZURE_COSMOS_KEY=your-cosmos-key
AZURE_COSMOS_DATABASE_NAME=chatbot
AZURE_COSMOS_CONTAINER_NAME=conversations

# Optional: Azure Application Insights
AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING=your-app-insights-connection-string

# RAG Configuration
RAG_MAX_SEARCH_RESULTS=5
RAG_MIN_CONFIDENCE_SCORE=0.7
RAG_ENABLE_BY_DEFAULT=true

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
EOF
        log_success ".env template created"
        log_warning "Please edit .env file with your actual Azure service credentials"
    else
        log_info ".env file already exists"
    fi
}

# Provide deployment instructions
provide_deployment_instructions() {
    log_header "Deployment Instructions"
    
    echo
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo
    echo "1. 🔧 Configure your environment:"
    echo "   - Edit the .env file with your Azure service credentials"
    echo "   - Make sure all required Azure services are set up"
    echo
    echo "2. 🧪 Test locally:"
    echo "   - Run: source .venv/bin/activate"
    echo "   - Run: python -m uvicorn src.main:app --reload"
    echo "   - Test: http://localhost:8000/docs"
    echo
    echo "3. 🐳 Build container (optional):"
    echo "   - Run: docker build -t ai-career-mentor ."
    echo "   - Run: docker run -p 8000:8000 --env-file .env ai-career-mentor"
    echo
    echo "4. ☁️  Deploy to Azure:"
    echo "   - Run: ./infrastructure/scripts/deploy.sh -e dev -s YOUR_SUBSCRIPTION_ID -m YOUR_EMAIL"
    echo "   - Run: ./infrastructure/scripts/build-push.sh -e dev -r YOUR_REGISTRY -s YOUR_SUBSCRIPTION_ID -g YOUR_RESOURCE_GROUP"
    echo
    echo "5. 📚 Initialize knowledge base:"
    echo "   - Run: python demo_rag_system.py (for demonstration)"
    echo "   - Use the /search endpoint to verify knowledge base"
    echo
    echo -e "${GREEN}🔗 Important Links:${NC}"
    echo "   - API Documentation: http://localhost:8000/docs"
    echo "   - Health Check: http://localhost:8000/health"
    echo "   - RAG Demo: python demo_rag_system.py"
    echo "   - Infrastructure Docs: ./infrastructure/README.md"
    echo
    echo -e "${YELLOW}⚠️  Important Notes:${NC}"
    echo "   - Ensure your Azure services are in the same region for better performance"
    echo "   - The knowledge base needs to be seeded before RAG functionality works"
    echo "   - Monitor your Azure OpenAI token usage to manage costs"
    echo "   - Use the health endpoints for monitoring in production"
    echo
}

# Run main function
main "$@"