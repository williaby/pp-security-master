---
title: "Phase 5: Production Deployment (Steps 4-7)"
version: "1.0"
status: "active" 
component: "Planning"
tags: ["phase-5", "production", "docker", "monitoring", "security"]
source: "PP Security-Master Project"
purpose: "Phase 5 production deployment configuration including authentication, Docker, monitoring, and security."
---

# Phase 5: Production Deployment (Steps 4-7)

## Enterprise Features & Production Deployment

### Production Infrastructure and Security Configuration

> **Navigation**:
>
> - [Prerequisites & Setup](./phase-5-prerequisites-setup.md) (Steps 1-3)
> - **Current**: Production Deployment (Steps 4-7)
> - [Testing & Completion](./phase-5-testing-completion.md) (Steps 8-10)

---

## Step 4: Enhanced Authentication System

```bash
echo "🔐 Step 4: Enhanced Authentication System Setup"

# Create Security-Master specific authentication models
cat > src/security_master/auth/security_master_auth.py << 'EOF'
"""
Security-Master Authentication System

Enterprise authentication with Cloudflare Access integration and role-based permissions.
"""

import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

class SecurityMasterRole(str, Enum):
    """Security-Master user roles with enterprise permissions."""
    ADMIN = "admin"
    PORTFOLIO_MANAGER = "portfolio_manager"
    ANALYST = "analyst" 
    AUDITOR = "auditor"
    COMPLIANCE = "compliance"

class SecurityMasterPermission(str, Enum):
    """Granular permissions for Security-Master operations."""
    # Data access permissions
    READ_SECURITIES = "read:securities"
    READ_TRANSACTIONS = "read:transactions"
    READ_HOLDINGS = "read:holdings"
    READ_ANALYTICS = "read:analytics"
    READ_INSTITUTION_DATA = "read:institution_data"
    
    # Write permissions
    WRITE_CLASSIFICATIONS = "write:classifications"
    APPROVE_CLASSIFICATIONS = "approve:classifications"
    MANAGE_PORTFOLIOS = "manage:portfolios"
    EXPORT_PORTFOLIO_DATA = "export:portfolio_data"
    
    # Administrative permissions
    MANAGE_USERS = "manage:users"
    MANAGE_SYSTEM_CONFIG = "manage:system_config"
    MANAGE_API_KEYS = "manage:api_keys"
    
    # Audit and compliance
    VIEW_AUDIT_LOGS = "view:audit_logs"
    GENERATE_COMPLIANCE_REPORTS = "generate:compliance_reports"

# Role-permission mappings
ROLE_PERMISSIONS = {
    SecurityMasterRole.ADMIN: list(SecurityMasterPermission),
    SecurityMasterRole.PORTFOLIO_MANAGER: [
        SecurityMasterPermission.READ_SECURITIES,
        SecurityMasterPermission.READ_TRANSACTIONS,
        SecurityMasterPermission.READ_HOLDINGS,
        SecurityMasterPermission.READ_ANALYTICS,
        SecurityMasterPermission.READ_INSTITUTION_DATA,
        SecurityMasterPermission.WRITE_CLASSIFICATIONS,
        SecurityMasterPermission.MANAGE_PORTFOLIOS,
        SecurityMasterPermission.EXPORT_PORTFOLIO_DATA,
    ],
    SecurityMasterRole.ANALYST: [
        SecurityMasterPermission.READ_SECURITIES,
        SecurityMasterPermission.READ_HOLDINGS,
        SecurityMasterPermission.READ_ANALYTICS,
        SecurityMasterPermission.WRITE_CLASSIFICATIONS,
    ],
    SecurityMasterRole.AUDITOR: [
        SecurityMasterPermission.READ_SECURITIES,
        SecurityMasterPermission.READ_TRANSACTIONS,
        SecurityMasterPermission.READ_HOLDINGS,
        SecurityMasterPermission.READ_ANALYTICS,
        SecurityMasterPermission.READ_INSTITUTION_DATA,
        SecurityMasterPermission.VIEW_AUDIT_LOGS,
        SecurityMasterPermission.GENERATE_COMPLIANCE_REPORTS,
    ],
    SecurityMasterRole.COMPLIANCE: [
        SecurityMasterPermission.READ_SECURITIES,
        SecurityMasterPermission.VIEW_AUDIT_LOGS,
        SecurityMasterPermission.GENERATE_COMPLIANCE_REPORTS,
    ],
}

class SecurityMasterUser:
    """Authenticated user with Security-Master permissions."""
    
    def __init__(self, email: str, name: str = None, role: SecurityMasterRole = SecurityMasterRole.ANALYST):
        self.email = email
        self.name = name or email.split('@')[0]
        self.role = role
        self.permissions = ROLE_PERMISSIONS.get(role, [])
        self.login_time = datetime.utcnow()
        self.session_expires = self.login_time + timedelta(hours=8)
    
    def has_permission(self, permission: SecurityMasterPermission) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for serialization."""
        return {
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "permissions": [p.value for p in self.permissions],
            "login_time": self.login_time.isoformat(),
            "session_expires": self.session_expires.isoformat()
        }

class SecurityMasterAuth:
    """Security-Master authentication manager with Cloudflare Access integration."""
    
    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET", "development-secret-change-in-production")
        self.cloudflare_audience = os.getenv("CLOUDFLARE_AUDIENCE", "")
        self.security_scheme = HTTPBearer()
    
    async def authenticate_user(self, request: Request) -> Optional[SecurityMasterUser]:
        """Authenticate user from Cloudflare Access JWT or development token."""
        
        # Check for Cloudflare Access JWT in headers
        cf_access_jwt = request.headers.get("Cf-Access-Jwt-Assertion")
        
        if cf_access_jwt:
            return await self._verify_cloudflare_token(cf_access_jwt)
        
        # Fallback to Authorization header for development
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            return await self._verify_internal_token(token)
        
        return None
    
    async def _verify_cloudflare_token(self, token: str) -> Optional[SecurityMasterUser]:
        """Verify Cloudflare Access JWT token."""
        try:
            # In production, verify against Cloudflare's public keys
            # For development, we'll do basic JWT parsing
            payload = jwt.decode(token, verify=False)  # WARNING: Only for development
            
            email = payload.get("email", "")
            name = payload.get("name", "")
            
            # Determine role based on email or payload
            role = self._determine_user_role(email, payload)
            
            return SecurityMasterUser(email=email, name=name, role=role)
            
        except Exception as e:
            logger.warning(f"Cloudflare token verification failed: {e}")
            return None
    
    def _determine_user_role(self, email: str, payload: Dict[str, Any]) -> SecurityMasterRole:
        """Determine user role based on email domain or payload information."""
        
        # Admin users
        admin_emails = ["byron@your-domain.com", "admin@your-domain.com"]
        if email in admin_emails:
            return SecurityMasterRole.ADMIN
        
        # Role based on email patterns
        if "portfolio" in email.lower() or "pm@" in email.lower():
            return SecurityMasterRole.PORTFOLIO_MANAGER
        elif "audit" in email.lower():
            return SecurityMasterRole.AUDITOR
        elif "compliance" in email.lower():
            return SecurityMasterRole.COMPLIANCE
        else:
            return SecurityMasterRole.ANALYST

# Global authentication instance
security_master_auth = SecurityMasterAuth()
EOF

echo "✅ Enhanced authentication system created"
```

---

## Step 5: Docker Production Configuration

```bash
echo "🐳 Step 5: Docker Production Configuration Setup"

# Create Docker configuration directory
mkdir -p docker/{api,worker,monitoring}

# Install production Docker Compose configuration
cp docs/planning/phase-5-templates/production_docker_compose.yml docker/docker-compose.production.yml

# Create optimized production API Dockerfile
cat > docker/api.Dockerfile << 'EOF'
# Multi-stage Dockerfile for Security-Master API - Production Optimized
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r security_master && useradd -r -g security_master security_master

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry==1.7.1
RUN poetry config virtualenvs.create false

# Development stage
FROM base as development

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install all dependencies including dev
RUN poetry install

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY scripts/ ./scripts/

# Set ownership
RUN chown -R security_master:security_master /app

USER security_master

# Development command
CMD ["python", "-m", "uvicorn", "src.security_master.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install production dependencies only
RUN poetry install --only=main --no-dev

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY sql/ ./sql/

# Copy PromptCraft integration files if they exist
COPY --from=development /app/src/security_master/ui/ ./src/security_master/ui/ || true
COPY --from=development /app/src/security_master/auth/ ./src/security_master/auth/ || true

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/backups /app/exports

# Set ownership
RUN chown -R security_master:security_master /app

USER security_master

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command with Gunicorn
CMD ["gunicorn", "src.security_master.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "300"]
EOF

# Create worker Dockerfile
cat > docker/worker.Dockerfile << 'EOF'
# Security-Master Worker Dockerfile for Background Processing
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r security_master && useradd -r -g security_master security_master

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.7.1
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install production dependencies
RUN poetry install --only=main --no-dev

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create directories
RUN mkdir -p /app/logs /app/data

# Set ownership
RUN chown -R security_master:security_master /app

USER security_master

# Health check for Celery worker
HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
    CMD celery inspect ping -A src.security_master.worker.celery_app || exit 1

# Worker command
CMD ["celery", "worker", "-A", "src.security_master.worker.celery_app", "--loglevel=info", "--concurrency=4", "--prefetch-multiplier=1"]
EOF

# Create production environment template
cat > .env.production.template << 'EOF'
# Security-Master Production Environment Configuration
# Copy to .env.production and customize values

# Database Configuration
DATABASE_HOST=postgresql
DATABASE_PORT=5432
DATABASE_NAME=pp_security_master_prod
DATABASE_USER=pp_security_admin
DATABASE_PASSWORD=CHANGE_ME_TO_SECURE_PASSWORD

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE_ME_TO_SECURE_REDIS_PASSWORD

# Authentication Configuration
JWT_SECRET=CHANGE_ME_TO_64_CHAR_JWT_SECRET_KEY
CLOUDFLARE_AUDIENCE=pp-security-master-production
CLOUDFLARE_DOMAIN=pp-security.your-domain.com

# External API Keys
OPENFIGI_API_KEY=YOUR_OPENFIGI_API_KEY
ALPHA_VANTAGE_API_KEY=YOUR_ALPHA_VANTAGE_API_KEY

# Security Configuration
ENCRYPTION_KEY=CHANGE_ME_TO_32_CHAR_ENCRYPTION_KEY
BACKUP_ENCRYPTION_KEY=CHANGE_ME_TO_BACKUP_ENCRYPTION_KEY
API_KEY_ENCRYPTION_KEY=CHANGE_ME_TO_API_KEY_ENCRYPTION

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=WARNING
DEBUG=false
WORKERS=4
MAX_REQUESTS=1000

# Monitoring Configuration
ENABLE_METRICS=true
PROMETHEUS_PORT=8001
GRAFANA_ADMIN_PASSWORD=CHANGE_ME_TO_SECURE_GRAFANA_PASSWORD

# Backup Configuration
BACKUP_RETENTION_DAYS=2555  # 7 years
OFFSITE_BACKUP_ENABLED=true
BACKUP_ENCRYPTION_ENABLED=true
EOF

echo "✅ Docker production configuration completed"
```

---

## Step 6: Monitoring and Observability Setup

```bash
echo "📊 Step 6: Monitoring and Observability Setup"

# Create monitoring configuration directory
mkdir -p monitoring/{prometheus,grafana,alertmanager}

# Create Prometheus configuration
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: 'production'
    project: 'security-master'

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Security-Master API metrics
  - job_name: 'security-master-api'
    static_configs:
      - targets: ['api:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s

  # Security-Master Worker metrics  
  - job_name: 'security-master-worker'
    static_configs:
      - targets: ['worker:8001']
    metrics_path: '/metrics'
    scrape_interval: 60s

  # PostgreSQL metrics
  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres_exporter:9187']
    scrape_interval: 30s

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']
    scrape_interval: 30s

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s
EOF

# Create comprehensive alert rules
cat > monitoring/alert_rules.yml << 'EOF'
groups:
- name: security_master_critical
  rules:
  # Service availability alerts
  - alert: SecurityMasterAPIDown
    expr: up{job="security-master-api"} == 0
    for: 1m
    labels:
      severity: critical
      component: api
    annotations:
      summary: "Security-Master API is down"
      description: "The Security-Master API has been down for more than 1 minute"

  - alert: DatabaseDown
    expr: up{job="postgresql"} == 0
    for: 1m
    labels:
      severity: critical
      component: database
    annotations:
      summary: "PostgreSQL database is down"
      description: "PostgreSQL database has been unreachable for more than 1 minute"

  - alert: CacheDown
    expr: up{job="redis"} == 0
    for: 1m
    labels:
      severity: critical
      component: cache
    annotations:
      summary: "Redis cache is down"
      description: "Redis cache has been unreachable for more than 1 minute"

- name: security_master_performance
  rules:
  # Performance alerts
  - alert: HighAPILatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="security-master-api"}[5m])) > 5
    for: 5m
    labels:
      severity: warning
      component: api
    annotations:
      summary: "High API response time detected"
      description: "95th percentile API response time is {{ $value }}s"

  - alert: HighErrorRate
    expr: rate(http_requests_total{job="security-master-api",status=~"5.."}[5m]) / rate(http_requests_total{job="security-master-api"}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
      component: api
    annotations:
      summary: "High API error rate detected"
      description: "API error rate is {{ $value | humanizePercentage }} over the last 5 minutes"

- name: security_master_business
  rules:
  # Business logic alerts
  - alert: ClassificationAccuracyLow
    expr: securities_classification_accuracy < 0.9
    for: 10m
    labels:
      severity: warning
      component: classification
    annotations:
      summary: "Securities classification accuracy below threshold"
      description: "Classification accuracy is {{ $value | humanizePercentage }}"

  - alert: ExternalAPIRateLimitApproaching
    expr: external_api_rate_limit_remaining < 50
    for: 0m
    labels:
      severity: warning
      component: external_api
    annotations:
      summary: "External API rate limit approaching"
      description: "{{ $labels.api }} has {{ $value }} API calls remaining"
EOF

# Create AlertManager configuration
cat > monitoring/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@your-domain.com'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'critical-alerts'
  webhook_configs:
  - url: 'YOUR_CRITICAL_WEBHOOK_URL'
    send_resolved: true
    title: 'Security-Master Critical Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}: {{ .Annotations.description }}{{ end }}'

- name: 'warning-alerts'
  webhook_configs:
  - url: 'YOUR_WARNING_WEBHOOK_URL'
    send_resolved: true
    title: 'Security-Master Warning'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}: {{ .Annotations.description }}{{ end }}'
EOF

echo "✅ Monitoring and observability setup completed"
```

---

## Step 7: Security Configuration and Hardening

```bash
echo "🔒 Step 7: Security Configuration and Hardening"

# Create security directory structure
mkdir -p security/{scans,policies,certificates,keys}

# Copy security scanning script from templates
cp docs/planning/phase-5-templates/security_assessment.sh security/scans/comprehensive_security_scan.sh
chmod +x security/scans/comprehensive_security_scan.sh

# Create production security configuration
cat > security/policies/production_security_config.yaml << 'EOF'
# Security-Master Production Security Configuration

# Authentication Configuration
authentication:
  jwt_algorithm: "HS256"
  session_timeout_hours: 8
  password_min_length: 16
  require_mfa: false  # Handled by Cloudflare Access
  cloudflare_integration: true

# API Security Configuration
api_security:
  rate_limiting:
    default: "1000/hour"
    authentication: "100/minute" 
    classification: "500/hour"
    import: "50/hour"
    export: "20/hour"
  
  cors_policy:
    allow_origins: ["https://pp-security.your-domain.com"]
    allow_methods: ["GET", "POST", "PUT", "DELETE"]
    allow_headers: ["Authorization", "Content-Type"]
    max_age: 3600

  security_headers:
    hsts_max_age: 31536000
    content_type_options: "nosniff"
    frame_options: "DENY"
    xss_protection: "1; mode=block"

# Data Protection Configuration
data_protection:
  encryption_at_rest:
    algorithm: "AES-256"
    key_rotation_days: 90
    backup_encryption: true
  
  encryption_in_transit:
    min_tls_version: "1.3"
    cipher_suites: ["TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256"]
  
  sensitive_data_handling:
    log_sanitization: true
    pii_masking: true
    financial_data_encryption: true

# Audit Configuration
audit_logging:
  enabled: true
  log_level: "INFO"
  retention_days: 3653  # 10 years
  log_format: "JSON"
  include_fields:
    - timestamp
    - user_id
    - action
    - resource
    - ip_address
    - user_agent
    - result

# Compliance Configuration
compliance:
  gdpr_compliance: true
  data_retention:
    transaction_data_years: 7
    audit_logs_years: 10
    user_data_years: 3
  
  privacy_controls:
    data_anonymization: true
    right_to_deletion: true
    data_portability: true

# Infrastructure Security
infrastructure:
  container_security:
    run_as_non_root: true
    read_only_filesystem: false  # Application needs write access
    drop_capabilities: ["ALL"]
    add_capabilities: []
  
  network_security:
    internal_only_services: ["postgresql", "redis", "prometheus"]
    firewall_rules: "restrictive"
    network_isolation: true
EOF

echo "✅ Security configuration and hardening completed"
```

---

## Completion Status for Steps 4-7

### ✅ Step 4: Enhanced Authentication System

- Role-based authentication with enterprise permissions
- Cloudflare Access integration
- JWT token management
- User role and permission mappings

### ✅ Step 5: Docker Production Configuration  

- Multi-stage production Dockerfiles created
- Production environment template configured
- Container security and optimization implemented
- Worker and API service separation

### ✅ Step 6: Monitoring and Observability Setup

- Prometheus metrics collection configured
- Comprehensive alert rules implemented
- AlertManager notification system
- Business logic and infrastructure monitoring

### ✅ Step 7: Security Configuration and Hardening

- Production security policies established
- API security with rate limiting and CORS
- Data protection and encryption configuration
- Audit logging and compliance controls

---

## Next Steps

Continue with [Testing & Completion](./phase-5-testing-completion.md) for:

- Production Deployment Scripts (Step 8)
- Testing and Validation (Step 9)
- Final Validation and Completion (Step 10)

---

### Generated from the original phase-5-execution-guide.md file for improved LLM processing
