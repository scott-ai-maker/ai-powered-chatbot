# CI/CD Guide

## Overview

This document outlines the Continuous Integration and Continuous Deployment (CI/CD) practices for the AI Powered Chatbot project. Our CI/CD pipeline ensures code quality, security, and reliable deployments across multiple environments.

## Pipeline Architecture

### Pipeline Stages

1. **Code Quality & Security Analysis**
2. **Testing & Coverage**
3. **Security Scanning**
4. **Build & Package**
5. **Deployment**
6. **Post-Deployment Testing**
7. **Monitoring & Alerting**

## Branch Strategy

### Git Flow Model

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: Individual feature branches
- **hotfix/***: Critical production fixes
- **release/***: Release preparation branches

### Branch Protection Rules

- **main branch**:
  - Require pull request reviews (2 approvers)
  - Require status checks to pass
  - Require up-to-date branches
  - Include administrators in restrictions

- **develop branch**:
  - Require pull request reviews (1 approver)
  - Require status checks to pass
  - Allow force pushes by administrators

## CI/CD Workflows

### 1. Code Quality & Security Analysis

**Trigger**: Push to any branch, Pull Request creation

```yaml
# Automated checks performed:
- Pre-commit hooks validation
- Code linting with Ruff
- Type checking with MyPy
- Security scanning with Bandit
- Dependency vulnerability scanning with Safety
- Code formatting validation
```

**Quality Gates**:
- All linting issues must be resolved
- Type checking must pass
- No high-severity security issues
- Code coverage must be >90%

### 2. Testing Pipeline

**Trigger**: All code changes

**Test Types**:

#### Unit Tests
```bash
# Run unit tests with coverage
pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=html
```

#### Integration Tests
```bash
# Run integration tests
pytest tests/integration/ -v --cov-append
```

#### End-to-End Tests
```bash
# Run E2E tests against staging environment
pytest tests/e2e/ -v --environment=staging
```

**Coverage Requirements**:
- Unit test coverage: ≥90%
- Integration test coverage: ≥80%
- Critical path coverage: 100%

### 3. Security Scanning

**Tools Used**:

#### Static Application Security Testing (SAST)
- **Bandit**: Python security linter
- **Safety**: Python dependency vulnerability scanner
- **Trivy**: Container and filesystem vulnerability scanner

#### Dynamic Application Security Testing (DAST)
- **OWASP ZAP**: Web application security scanner
- **Custom security tests**: API endpoint testing

#### Infrastructure Security
- **Trivy**: Infrastructure as Code scanning
- **Azure Security Center**: Cloud security posture management

**Security Gates**:
- No critical vulnerabilities allowed
- High vulnerabilities require approval
- All dependencies must be up-to-date

### 4. Build & Package

**Container Build Process**:

```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as builder
# ... build dependencies

FROM python:3.11-slim as runtime  
# ... runtime configuration
```

**Build Optimizations**:
- Multi-stage builds for smaller images
- Layer caching for faster builds
- Security scanning of container images
- Multi-architecture builds (AMD64, ARM64)

### 5. Deployment Strategy

#### Environment Progression

1. **Development**
   - Automatic deployment from `develop` branch
   - Basic smoke tests
   - Development database

2. **Staging**
   - Automatic deployment from `main` branch
   - Full test suite execution
   - Production-like environment
   - Performance testing

3. **Production**
   - Manual approval required
   - Blue-green deployment
   - Automated rollback capability
   - Health checks and monitoring

#### Deployment Methods

**Blue-Green Deployment**:
```yaml
# Azure Container Apps deployment slots
- Slot A (Blue): Current production traffic
- Slot B (Green): New version deployment
- Traffic switching after validation
- Instant rollback capability
```

**Canary Deployment** (Future):
```yaml
# Gradual traffic routing
- 5% traffic to new version
- Monitor metrics for 10 minutes
- Increase to 25% if healthy
- Full deployment after validation
```

## Environment Configuration

### Development Environment

```yaml
Environment: development
Resources:
  - CPU: 0.5 vCPU
  - Memory: 1 GB
  - Instances: 1-2
Features:
  - Debug logging enabled
  - Development database
  - Relaxed security settings
  - Hot reloading
```

### Staging Environment

```yaml
Environment: staging  
Resources:
  - CPU: 1 vCPU
  - Memory: 2 GB
  - Instances: 2-4
Features:
  - Production-like data
  - Full security enabled
  - Performance monitoring
  - Load testing
```

### Production Environment

```yaml
Environment: production
Resources:
  - CPU: 2 vCPU
  - Memory: 4 GB  
  - Instances: 3-10 (auto-scaling)
Features:
  - High availability
  - Disaster recovery
  - Advanced monitoring
  - Security hardening
```

## Quality Gates & Approvals

### Automated Gates

1. **Code Quality Gate**
   - All tests pass
   - Code coverage >90%
   - No linting errors
   - Security scan clean

2. **Security Gate**
   - No critical vulnerabilities
   - Dependency scan clean
   - Container scan passed
   - SAST/DAST results acceptable

3. **Performance Gate**
   - Response time <500ms (95th percentile)
   - Error rate <1%
   - Memory usage <80%
   - CPU usage <70%

### Manual Approvals

#### Staging Deployment
- **Approvers**: Development team lead
- **Criteria**: 
  - All automated gates passed
  - Feature testing completed
  - Documentation updated

#### Production Deployment  
- **Approvers**: Product owner + DevOps lead
- **Criteria**:
  - Staging validation successful
  - Business approval obtained
  - Maintenance window scheduled

## Monitoring & Observability

### Pipeline Monitoring

**Key Metrics**:
- Pipeline success rate
- Average pipeline duration
- Time to deployment
- Rollback frequency

**Alerts**:
- Pipeline failures
- Security gate violations
- Performance degradation
- Deployment rollbacks

### Application Monitoring

**Health Checks**:
```python
# Automated health endpoints
GET /health          # Basic service health
GET /health/detailed # Comprehensive health check
GET /ready          # Readiness probe for K8s
```

**SLI/SLO Monitoring**:
- **Availability**: 99.9% uptime
- **Performance**: <500ms response time  
- **Error Rate**: <1% of requests
- **Throughput**: Handle 1000 req/sec

## Rollback Procedures

### Automated Rollback Triggers

```yaml
Triggers:
  - Error rate >5% for 2 minutes
  - Response time >2s for 5 minutes  
  - Health check failures >3 consecutive
  - Critical security alert
```

### Manual Rollback Process

1. **Immediate Rollback**
   ```bash
   # Azure Container Apps
   az containerapp revision set-mode --name <app> --mode single --revision <previous>
   ```

2. **Database Rollback** (if needed)
   ```bash
   # Point-in-time restore
   az postgres flexible-server restore --name <server> --restore-point-in-time <timestamp>
   ```

3. **Validation**
   - Health check verification
   - Smoke test execution
   - User impact assessment

## Secrets Management

### Azure Key Vault Integration

```yaml
Secrets Storage:
  - Database connection strings
  - API keys and tokens
  - TLS certificates
  - Encryption keys

Access Control:
  - Service principal authentication
  - Role-based access control
  - Audit logging enabled
  - Rotation policies enforced
```

### Environment Variables

```bash
# Production secrets (Azure Key Vault)
DATABASE_URL="@Microsoft.KeyVault(SecretUri=https://vault.vault.azure.net/secrets/db-url/)"
OPENAI_API_KEY="@Microsoft.KeyVault(SecretUri=https://vault.vault.azure.net/secrets/openai-key/)"

# Non-sensitive configuration
ENVIRONMENT="production"
LOG_LEVEL="INFO"
```

## Performance Testing

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class ChatbotUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def send_message(self):
        self.client.post("/api/chat", json={"message": "Hello"})
        
    @task(1)  
    def health_check(self):
        self.client.get("/health")
```

**Performance Targets**:
- **Concurrent Users**: 1000
- **Response Time**: <500ms (95th percentile)
- **Throughput**: 1000 requests/second
- **Error Rate**: <1%

### Continuous Performance Monitoring

```yaml
# Performance benchmarks in CI/CD
- name: Performance Test
  run: |
    locust --host=${{ env.STAGING_URL }} \
           --users 100 \
           --spawn-rate 10 \
           --run-time 5m \
           --headless \
           --html performance-report.html
```

## Troubleshooting Guide

### Common Pipeline Issues

#### 1. Test Failures
```bash
# Debug test failures
pytest tests/ -v --tb=long --capture=no

# Run specific test
pytest tests/test_api.py::test_chat_endpoint -v
```

#### 2. Security Scan Failures
```bash
# Check Bandit results
bandit -r src/ -f json -o bandit-report.json

# Review safety issues  
safety check --config .safety-policy.yml --json
```

#### 3. Build Failures
```bash
# Check Docker build logs
docker build --progress=plain --no-cache -t app:debug .

# Inspect image layers
docker history app:debug
```

### Pipeline Recovery

1. **Identify Root Cause**
   - Review pipeline logs
   - Check error messages  
   - Analyze failure patterns

2. **Quick Fixes**
   - Retry transient failures
   - Skip non-critical steps
   - Use previous known-good version

3. **Permanent Solutions**
   - Fix underlying issues
   - Update pipeline configuration
   - Improve error handling

## Best Practices

### Code Quality

1. **Pre-commit Hooks**
   ```bash
   # Install pre-commit hooks
   pre-commit install
   
   # Run on all files
   pre-commit run --all-files
   ```

2. **Code Reviews**
   - Mandatory for all changes
   - Focus on security and performance
   - Include architectural decisions
   - Document review comments

3. **Documentation**
   - Update README for new features
   - Maintain API documentation
   - Document deployment procedures
   - Keep architecture diagrams current

### Security Best Practices

1. **Secrets Handling**
   - Never commit secrets to code
   - Use Azure Key Vault for all secrets
   - Rotate secrets regularly
   - Audit secret access

2. **Dependency Management**
   - Pin exact versions in production
   - Regular dependency updates
   - Security vulnerability monitoring
   - License compliance checking

3. **Container Security**
   - Use official base images
   - Regular security scanning
   - Minimal attack surface
   - Non-root user execution

### Deployment Best Practices

1. **Infrastructure as Code**
   - Version control all infrastructure
   - Use Terraform/Bicep templates
   - Environment parity
   - Automated provisioning

2. **Zero-Downtime Deployments**
   - Blue-green deployment strategy
   - Health check validation
   - Automated rollback procedures
   - Database migration safety

3. **Monitoring & Alerting**
   - Comprehensive health checks
   - Business metric monitoring
   - Proactive alerting
   - Incident response procedures

## Compliance & Governance

### Audit Requirements

- **Change Tracking**: All deployments logged
- **Approval Records**: Manual approval evidence  
- **Security Compliance**: Regular security assessments
- **Data Governance**: Data handling procedures

### Reporting

- **Weekly**: Pipeline performance metrics
- **Monthly**: Security scan summaries
- **Quarterly**: Infrastructure cost analysis
- **Annually**: Disaster recovery testing