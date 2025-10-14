# Enterprise GitHub Configuration for AI Career Mentor
# ===================================================
# This file documents the required GitHub repository settings for enterprise deployment

## Repository Variables (Settings > Secrets and variables > Actions > Variables)

# Azure Configuration
AZURE_CONTAINER_REGISTRY=acmdevacr123456  # Your Azure Container Registry name (without .azurecr.io)
AZURE_SUBSCRIPTION_ID=12345678-1234-1234-1234-123456789012  # Your Azure subscription ID
MAINTAINER_EMAIL=admin@yourcompany.com  # Email for critical notifications

# Notification Configuration (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK  # Slack webhook URL
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR/TEAMS/WEBHOOK  # Teams webhook URL

## Repository Secrets (Settings > Secrets and variables > Actions > Secrets)

# Azure Service Principal Credentials (JSON format)
AZURE_CREDENTIALS_DEV={
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "your-dev-client-secret",
  "subscriptionId": "12345678-1234-1234-1234-123456789012",
  "tenantId": "12345678-1234-1234-1234-123456789012"
}

AZURE_CREDENTIALS_STAGING={
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "your-staging-client-secret",
  "subscriptionId": "12345678-1234-1234-1234-123456789012",
  "tenantId": "12345678-1234-1234-1234-123456789012"
}

AZURE_CREDENTIALS_PROD={
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "your-prod-client-secret",
  "subscriptionId": "12345678-1234-1234-1234-123456789012",
  "tenantId": "12345678-1234-1234-1234-123456789012"
}

# GitHub Token for advanced operations
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Auto-provided by GitHub

## GitHub Environments (Settings > Environments)

### Development Environment
- Name: development
- Protection Rules:
  - Required reviewers: 0 (for development)
  - Wait timer: 0 minutes
  - Restrict deployments to selected branches: main, develop

### Staging Environment  
- Name: staging
- Protection Rules:
  - Required reviewers: 1 (senior developer)
  - Wait timer: 0 minutes
  - Restrict deployments to selected branches: main
  - Environment secrets: AZURE_CREDENTIALS_STAGING

### Production Environment
- Name: production  
- Protection Rules:
  - Required reviewers: 2 (must include team lead)
  - Wait timer: 5 minutes
  - Restrict deployments to selected branches: main
  - Environment secrets: AZURE_CREDENTIALS_PROD

## Branch Protection Rules (Settings > Branches)

### Main Branch Protection
- Branch name pattern: main
- Protect matching branches: ✅
- Restrictions:
  - Require a pull request before merging: ✅
    - Require approvals: 2
    - Dismiss stale reviews when new commits are pushed: ✅
    - Require review from code owners: ✅
    - Restrict pushes that create files larger than 100MB: ✅
  - Require status checks to pass before merging: ✅
    - Require branches to be up to date before merging: ✅
    - Required status checks:
      - Code Quality & Security
      - Run Tests (unit)
      - Run Tests (integration)  
      - Frontend Build & Test
      - Build & Scan Container
      - Enterprise Standards
  - Require conversation resolution before merging: ✅
  - Require signed commits: ✅ (recommended)
  - Require linear history: ✅
  - Include administrators: ✅
  - Allow force pushes: ❌
  - Allow deletions: ❌

### Develop Branch Protection
- Branch name pattern: develop
- Protect matching branches: ✅
- Restrictions:
  - Require a pull request before merging: ✅
    - Require approvals: 1
    - Dismiss stale reviews when new commits are pushed: ✅
  - Require status checks to pass before merging: ✅
    - Required status checks:
      - Code Quality & Security
      - Run Tests (unit)
  - Allow force pushes: ❌
  - Allow deletions: ❌

## Required Status Checks Configuration

The following GitHub status checks must pass before merging:

1. **Code Quality & Security** - Linting, formatting, type checking, security scans
2. **Run Tests (unit)** - Unit test suite with minimum 80% coverage
3. **Run Tests (integration)** - Integration tests with external services
4. **Frontend Build & Test** - Frontend compilation and testing
5. **Build & Scan Container** - Container image build and security scanning
6. **Enterprise Standards** - Branch naming, PR format, compliance checks

## Labels Configuration (Issues and Pull Requests)

Create the following labels in your repository (Settings > Labels):

### Priority Labels
- `priority/critical` - Critical issues requiring immediate attention (red)
- `priority/high` - High priority issues (orange)  
- `priority/medium` - Medium priority issues (yellow)
- `priority/low` - Low priority issues (green)

### Type Labels
- `type/bug` - Bug reports (red)
- `type/feature` - Feature requests (blue)
- `type/enhancement` - Enhancements to existing features (light blue)
- `type/documentation` - Documentation updates (light green)
- `type/refactor` - Code refactoring (purple)

### Status Labels
- `status/needs-review` - Waiting for code review (orange)
- `status/needs-testing` - Needs testing (yellow)
- `status/in-progress` - Work in progress (blue)
- `status/blocked` - Blocked by dependencies (red)

### Security Labels
- `security-review` - Requires security team review (red)
- `security/vulnerability` - Security vulnerability (dark red)
- `security/audit` - Security audit required (orange)

### Automation Labels
- `automated` - Created by automation (gray)
- `workflow-failure` - Workflow failure notification (red)
- `deployment` - Deployment related (blue)

## Webhook Configuration (Optional)

For advanced integrations, configure webhooks in Settings > Webhooks:

### Deployment Webhooks
- Payload URL: https://your-deployment-service.com/webhook
- Content type: application/json
- Events: Deployment status, Release

### Monitoring Webhooks  
- Payload URL: https://your-monitoring-service.com/webhook
- Content type: application/json
- Events: Push, Issues, Pull requests, Workflow runs

## Security Configuration

### Dependabot (Security > Dependabot)
- Enable Dependabot alerts: ✅
- Enable Dependabot security updates: ✅
- Enable Dependabot version updates: ✅

### Code Scanning (Security > Code scanning)
- Enable CodeQL analysis: ✅
- Languages: Python, JavaScript, TypeScript
- Query suite: Security and quality

### Secret Scanning (Security > Secret scanning)
- Enable secret scanning: ✅
- Enable push protection: ✅

## Team Configuration

### Required Teams
Create the following teams with appropriate permissions:

1. **ai-career-mentor-admins** - Admin access to repository
2. **ai-career-mentor-maintainers** - Maintain access for core team
3. **ai-career-mentor-developers** - Write access for developers
4. **security-team** - Required reviewers for security-sensitive changes

## Repository Settings

### General Settings
- Default branch: main
- Allow merge commits: ✅
- Allow squash merging: ✅ (preferred)
- Allow rebase merging: ✅
- Automatically delete head branches: ✅

### Pull Requests
- Allow auto-merge: ✅
- Require conversation resolution before merging: ✅
- Suggest updating pull request branches: ✅

### Archives
- Include Git LFS objects in archives: ✅

This configuration ensures enterprise-grade security, compliance, and operational excellence for the AI Career Mentor project.