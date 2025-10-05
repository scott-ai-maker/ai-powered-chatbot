#!/bin/bash

# Test Execution Script for AI Career Mentor Chatbot
# Demonstrates professional testing practices and CI/CD readiness

set -e  # Exit on any error

echo "🧪 AI Career Mentor Chatbot - Test Suite"
echo "======================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if virtual environment is activated
check_venv() {
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        print_success "Virtual environment detected: $VIRTUAL_ENV"
    else
        print_warning "No virtual environment detected. Attempting to activate..."
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
            print_success "Virtual environment activated: .venv"
        else
            print_error "No virtual environment found. Please create one first."
            exit 1
        fi
    fi
}

# Install test dependencies
install_dependencies() {
    print_status "Installing test dependencies..."
    pip install -q pytest pytest-asyncio pytest-cov pytest-mock pytest-html
    print_success "Test dependencies installed"
}

# Run unit tests
run_unit_tests() {
    print_status "Running unit tests..."
    echo ""
    
    # Run unit tests with coverage
    if pytest tests/unit/ -v --tb=short; then
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed"
        return 1
    fi
    echo ""
}

# Run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    echo ""
    
    # Run integration tests
    if pytest tests/integration/ -v --tb=short; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        return 1
    fi
    echo ""
}

# Generate comprehensive coverage report
generate_coverage() {
    print_status "Generating coverage report..."
    echo ""
    
    # Run all tests with coverage
    pytest tests/ \
        --cov=src \
        --cov-report=html \
        --cov-report=term-missing \
        --cov-report=xml \
        --cov-fail-under=80 \
        --html=reports/test-report.html \
        --self-contained-html \
        -v
    
    print_success "Coverage reports generated:"
    echo "  📊 HTML Report: htmlcov/index.html"
    echo "  📋 Test Report: reports/test-report.html"
    echo "  📄 XML Report: coverage.xml"
    echo ""
}

# Run performance benchmarks
run_benchmarks() {
    print_status "Running performance benchmarks..."
    echo ""
    
    # Run tests marked as performance
    if pytest tests/ -m performance -v --tb=short 2>/dev/null; then
        print_success "Performance benchmarks completed"
    else
        print_warning "No performance benchmarks found or they failed"
    fi
    echo ""
}

# Lint and quality checks
run_quality_checks() {
    print_status "Running code quality checks..."
    echo ""
    
    # Check if test files follow naming conventions
    if find tests/ -name "*.py" -not -name "test_*.py" -not -name "__init__.py" -not -name "conftest.py" | grep -q .; then
        print_warning "Some test files don't follow naming convention (test_*.py)"
    else
        print_success "Test file naming conventions followed"
    fi
    
    # Check for proper async test decorators
    if grep -r "async def test_" tests/ | grep -v "@pytest.mark.asyncio" >/dev/null; then
        print_warning "Some async tests may be missing pytest.mark.asyncio decorator"
    else
        print_success "Async test decorators properly used"
    fi
    
    echo ""
}

# Main execution
main() {
    echo "Starting comprehensive test suite..."
    echo ""
    
    # Create reports directory
    mkdir -p reports
    
    # Check environment
    check_venv
    install_dependencies
    
    # Run quality checks
    run_quality_checks
    
    # Run tests
    run_unit_tests
    run_integration_tests
    
    # Generate reports
    generate_coverage
    
    # Run benchmarks if available
    run_benchmarks
    
    print_success "🎉 Test suite completed successfully!"
    echo ""
    echo "📈 Next Steps:"
    echo "  1. Open htmlcov/index.html to view detailed coverage"
    echo "  2. Open reports/test-report.html for test execution details"
    echo "  3. Review any warnings or failed tests above"
    echo "  4. Consider adding more tests for uncovered code paths"
    echo ""
    echo "🚀 CI/CD Ready: This test suite can be integrated into GitHub Actions"
    echo "   or any other continuous integration platform."
}

# Handle script arguments
case "${1:-all}" in
    "unit")
        check_venv
        install_dependencies
        run_unit_tests
        ;;
    "integration")
        check_venv
        install_dependencies
        run_integration_tests
        ;;
    "coverage")
        check_venv
        install_dependencies
        generate_coverage
        ;;
    "quality")
        check_venv
        run_quality_checks
        ;;
    "all"|*)
        main
        ;;
esac