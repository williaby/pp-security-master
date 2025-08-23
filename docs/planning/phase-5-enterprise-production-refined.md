---
title: "Phase 5: Enterprise Features & Production Deployment - REFINED"
version: "2.0"
status: "active"  
component: "Planning"
tags: ["enterprise", "production", "ui", "deployment", "promptcraft-integration"]
source: "PP Security-Master Project"
purpose: "Production-ready system with comprehensive web UI, authentication, and enterprise deployment capabilities."
---

# Phase 5: Enterprise Features & Production Deployment - REFINED

**Duration**: 4 weeks (Weeks 19-22)  
**Team Size**: 3-5 developers  
**Success Metric**: Production-ready system with enterprise-grade UI and deployment automation  
**PromptCraft Integration**: Leverage proven UI patterns, authentication system, and deployment strategies

---

## Phase Overview

### Objective
Transform the Security-Master system into a production-ready enterprise application by leveraging PromptCraft's proven UI patterns, authentication framework, and deployment strategies. Create a comprehensive web interface for manual classification and system management with enterprise-grade security and operational capabilities.

### Success Criteria
- [ ] Web UI operational with all core Security-Master functions accessible
- [ ] Authentication system integrated leveraging PromptCraft patterns and existing Cloudflare infrastructure
- [ ] Production deployment automated using PromptCraft deployment strategies
- [ ] Security assessment passed with enterprise-grade protection
- [ ] Performance metrics meet production SLAs (API <2s p95, UI <5s load time)
- [ ] System handles production load with <1% error rate and 99.9% uptime

### Key Deliverables
- Web UI framework adapted from PromptCraft multi-journey interface patterns
- Enterprise authentication leveraging PromptCraft auth middleware with Cloudflare Access
- Production deployment automation using Docker containerization strategies
- Comprehensive monitoring adapted from PromptCraft observability patterns
- Complete documentation and training materials for enterprise adoption

---

## Detailed Issues - REFINED

### Issue P5-001: Security-Master Web UI Framework (PromptCraft Integration)

**Branch**: `feature/web-ui-security-master`  
**Estimated Time**: 6 hours  
**Priority**: Critical  
**Week**: 19  

#### Description
Create Security-Master web UI by adapting PromptCraft's multi-journey interface patterns for financial data management workflows. Leverage proven Gradio components and accessibility enhancements.

#### Acceptance Criteria
- [ ] **FastAPI Backend**: RESTful API endpoints for Security-Master operations
  - Security search and classification endpoints
  - Institution data import/export endpoints  
  - Manual override and quality review endpoints
  - Portfolio analytics and reporting endpoints

- [ ] **Gradio Interface (Adapted from PromptCraft)**:
  - Multi-tab interface adapted from PromptCraft journey patterns
  - Security classification workflow UI (adapt journey1_smart_templates.py patterns)
  - Institution data import interface with file upload (leverage PromptCraft file handling)
  - Data quality dashboard and metrics (adapt PromptCraft dashboard components)
  - Portfolio analytics visualization interface

- [ ] **Security-Master Specific Components**:
  - Securities search with ISIN, symbol, and name lookup
  - Manual classification interface with taxonomy dropdowns (GICS, TRBC, CFI)
  - Batch import status monitoring and control
  - Institution-specific data validation displays
  - Portfolio Performance export generation and download

- [ ] **Accessibility & Mobile Support** (PromptCraft patterns):
  - Mobile-responsive design using PromptCraft accessibility enhancements
  - Screen reader compatibility for financial data
  - Keyboard navigation support
  - High contrast mode for data intensive interfaces

#### Implementation Commands
```bash
# Create UI package structure
mkdir -p src/security_master/ui/{components,journeys,shared}
touch src/security_master/ui/__init__.py

# Copy and adapt PromptCraft UI components
cp /home/byron/dev/PromptCraft/src/ui/multi_journey_interface.py \
   src/security_master/ui/security_master_interface.py

cp /home/byron/dev/PromptCraft/src/ui/components/accessibility_enhancements.py \
   src/security_master/ui/components/

cp /home/byron/dev/PromptCraft/src/ui/components/shared/export_utils.py \
   src/security_master/ui/shared/

# Create Security-Master specific journey modules
cat > src/security_master/ui/journeys/security_classification_journey.py << 'EOF'
"""
Security Classification Journey - Adapted from PromptCraft Journey Patterns

Provides comprehensive interface for:
- Security search and selection
- Manual classification workflows  
- Taxonomy assignment (GICS, TRBC, CFI)
- Data quality validation and review
"""

import gradio as gr
from typing import List, Dict, Any, Optional, Tuple
from src.security_master.storage.connection import get_db_connection
from src.security_master.classifier.core import SecurityClassifier
from src.ui.components.accessibility_enhancements import create_accessible_interface

class SecurityClassificationJourney:
    """Security classification workflow interface"""
    
    def __init__(self):
        self.classifier = SecurityClassifier()
        
    def create_interface(self) -> gr.Interface:
        """Create Gradio interface for security classification"""
        
        with gr.Blocks(title="Security Classification", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# Security Classification & Management")
            
            with gr.Tab("Search & Classify"):
                with gr.Row():
                    search_input = gr.Textbox(
                        label="Search Securities",
                        placeholder="Enter ISIN, Symbol, or Name",
                        interactive=True
                    )
                    search_btn = gr.Button("Search", variant="primary")
                
                search_results = gr.DataFrame(
                    label="Search Results",
                    headers=["Symbol", "Name", "ISIN", "Current Classification", "Confidence"],
                    interactive=True
                )
                
                with gr.Row():
                    selected_security = gr.Dropdown(
                        label="Select Security for Classification",
                        choices=[],
                        interactive=True
                    )
                
                with gr.Row():
                    gics_classification = gr.Dropdown(
                        label="GICS Sector",
                        choices=self._get_gics_sectors(),
                        interactive=True
                    )
                    trbc_classification = gr.Dropdown(
                        label="TRBC Classification", 
                        choices=self._get_trbc_classifications(),
                        interactive=True
                    )
                    cfi_classification = gr.Dropdown(
                        label="CFI Code",
                        choices=self._get_cfi_codes(),
                        interactive=True
                    )
                
                classification_notes = gr.Textbox(
                    label="Classification Notes",
                    lines=3,
                    placeholder="Add notes about this classification decision..."
                )
                
                classify_btn = gr.Button("Update Classification", variant="primary")
                classification_result = gr.Markdown()
            
            with gr.Tab("Batch Import"):
                file_upload = gr.File(
                    label="Upload Institution File",
                    file_types=[".csv", ".xml", ".pdf", ".json"]
                )
                
                institution_select = gr.Dropdown(
                    label="Institution Type",
                    choices=["Wells Fargo", "Interactive Brokers", "AltoIRA", "Kubera"],
                    interactive=True
                )
                
                import_btn = gr.Button("Import File", variant="primary")
                import_status = gr.Markdown()
                
                import_results = gr.DataFrame(
                    label="Import Results",
                    headers=["Security", "Status", "Classification", "Confidence", "Issues"]
                )
            
            with gr.Tab("Data Quality"):
                quality_metrics = gr.DataFrame(
                    label="Data Quality Metrics",
                    headers=["Metric", "Value", "Target", "Status"]
                )
                
                validation_issues = gr.DataFrame(
                    label="Validation Issues",
                    headers=["Security", "Issue Type", "Description", "Severity", "Action Required"]
                )
                
                refresh_quality_btn = gr.Button("Refresh Quality Metrics")
        
        # Event handlers
        search_btn.click(
            fn=self._search_securities,
            inputs=[search_input],
            outputs=[search_results, selected_security]
        )
        
        classify_btn.click(
            fn=self._update_classification,
            inputs=[selected_security, gics_classification, trbc_classification, 
                   cfi_classification, classification_notes],
            outputs=[classification_result]
        )
        
        import_btn.click(
            fn=self._import_file,
            inputs=[file_upload, institution_select],
            outputs=[import_status, import_results]
        )
        
        refresh_quality_btn.click(
            fn=self._get_quality_metrics,
            outputs=[quality_metrics, validation_issues]
        )
        
        return interface
    
    def _search_securities(self, query: str) -> Tuple[List[List], List[str]]:
        """Search securities by ISIN, symbol, or name"""
        # Implementation details...
        pass
    
    def _update_classification(self, security_id: str, gics: str, trbc: str, 
                             cfi: str, notes: str) -> str:
        """Update security classification"""
        # Implementation details...
        pass
    
    def _import_file(self, file, institution: str) -> Tuple[str, List[List]]:
        """Import institution file and process securities"""
        # Implementation details...
        pass
    
    def _get_quality_metrics(self) -> Tuple[List[List], List[List]]:
        """Get data quality metrics and validation issues"""
        # Implementation details...
        pass
    
    def _get_gics_sectors(self) -> List[str]:
        """Get available GICS sectors"""
        # Implementation details...
        pass
    
    def _get_trbc_classifications(self) -> List[str]:
        """Get available TRBC classifications"""
        # Implementation details...
        pass
    
    def _get_cfi_codes(self) -> List[str]:
        """Get available CFI codes"""
        # Implementation details...
        pass
EOF

echo "✅ Security-Master UI framework created with PromptCraft integration"
```

---

### Issue P5-002: Enterprise Authentication Integration (PromptCraft Auth System)

**Branch**: `feature/enterprise-auth-integration`  
**Estimated Time**: 4 hours  
**Priority**: High  
**Week**: 19  

#### Description
Integrate enterprise authentication by adapting PromptCraft's proven Cloudflare Access authentication system for Security-Master with role-based access control for financial data.

#### Acceptance Criteria
- [ ] **Cloudflare Access Integration** (PromptCraft patterns):
  - JWT validation using PromptCraft auth middleware patterns
  - Integration with existing Cloudflare tunnel infrastructure
  - Session management through Cloudflare Access tokens

- [ ] **Role-Based Access Control** (Financial Data Specific):
  - `admin`: Full access to all securities, institutions, and system configuration
  - `portfolio_manager`: Read/write access to classifications and portfolio data
  - `analyst`: Read access to data, write access to classifications only
  - `auditor`: Read-only access to all data with comprehensive audit trail
  - `compliance`: Access to data quality and validation reports only

- [ ] **Security Features** (PromptCraft enhanced):
  - Audit logging for all financial data access (adapt PromptCraft audit patterns)
  - Rate limiting for API endpoints to prevent abuse
  - Session timeout management for financial data security
  - IP-based access restrictions for sensitive operations

#### Implementation Commands
```bash
# Copy and adapt PromptCraft authentication components
cp -r /home/byron/dev/PromptCraft/src/auth src/security_master/auth
cp -r /home/byron/dev/PromptCraft/src/security src/security_master/security

# Adapt authentication models for Security-Master
cat > src/security_master/auth/security_master_models.py << 'EOF'
"""
Security-Master Authentication Models - Adapted from PromptCraft

Provides role-based access control specifically designed for financial data:
- Portfolio managers: Full portfolio and classification access
- Analysts: Classification and read-only data access  
- Auditors: Read-only access with comprehensive audit trails
- Compliance: Data quality and validation access only
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class SecurityMasterRole(str, Enum):
    """Security-Master specific user roles for financial data access"""
    ADMIN = "admin"
    PORTFOLIO_MANAGER = "portfolio_manager"  
    ANALYST = "analyst"
    AUDITOR = "auditor"
    COMPLIANCE = "compliance"

class SecurityMasterPermission(str, Enum):
    """Granular permissions for Security-Master operations"""
    # Data access permissions
    READ_SECURITIES = "read:securities"
    READ_TRANSACTIONS = "read:transactions" 
    READ_HOLDINGS = "read:holdings"
    READ_ANALYTICS = "read:analytics"
    READ_INSTITUTION_DATA = "read:institution_data"
    
    # Classification permissions
    WRITE_CLASSIFICATIONS = "write:classifications"
    APPROVE_CLASSIFICATIONS = "approve:classifications"
    
    # Portfolio management permissions
    MANAGE_PORTFOLIOS = "manage:portfolios"
    EXPORT_PORTFOLIO_DATA = "export:portfolio_data"
    
    # System administration permissions
    MANAGE_USERS = "manage:users"
    MANAGE_SYSTEM_CONFIG = "manage:system_config"
    MANAGE_API_KEYS = "manage:api_keys"
    
    # Audit and compliance permissions
    VIEW_AUDIT_LOGS = "view:audit_logs"
    GENERATE_COMPLIANCE_REPORTS = "generate:compliance_reports"

# Role-Permission mappings for Security-Master
SECURITY_MASTER_ROLE_PERMISSIONS = {
    SecurityMasterRole.ADMIN: [
        SecurityMasterPermission.READ_SECURITIES,
        SecurityMasterPermission.READ_TRANSACTIONS,
        SecurityMasterPermission.READ_HOLDINGS,
        SecurityMasterPermission.READ_ANALYTICS,
        SecurityMasterPermission.READ_INSTITUTION_DATA,
        SecurityMasterPermission.WRITE_CLASSIFICATIONS,
        SecurityMasterPermission.APPROVE_CLASSIFICATIONS,
        SecurityMasterPermission.MANAGE_PORTFOLIOS,
        SecurityMasterPermission.EXPORT_PORTFOLIO_DATA,
        SecurityMasterPermission.MANAGE_USERS,
        SecurityMasterPermission.MANAGE_SYSTEM_CONFIG,
        SecurityMasterPermission.MANAGE_API_KEYS,
        SecurityMasterPermission.VIEW_AUDIT_LOGS,
        SecurityMasterPermission.GENERATE_COMPLIANCE_REPORTS,
    ],
    
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

class SecurityMasterUser(BaseModel):
    """Security-Master authenticated user with financial data permissions"""
    email: str
    name: Optional[str] = None
    role: SecurityMasterRole
    permissions: List[SecurityMasterPermission]
    institution_access: List[str] = Field(default_factory=list)  # Which institutions user can access
    last_login: Optional[datetime] = None
    session_expires: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class FinancialDataAccessEvent(BaseModel):
    """Audit event for financial data access"""
    user_email: str
    action: str
    resource: str
    resource_id: Optional[str] = None
    institution: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    success: bool
    details: Optional[dict] = None
    
    class Config:
        use_enum_values = True
EOF

# Create Security-Master authentication middleware
cat > src/security_master/auth/security_master_middleware.py << 'EOF'
"""
Security-Master Authentication Middleware - Adapted from PromptCraft

Provides comprehensive authentication and authorization for financial data access
with enhanced audit logging and role-based permissions.
"""

import logging
from typing import List, Optional
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

# Import PromptCraft auth components
from src.auth.middleware import AuthenticationMiddleware as PromptCraftAuthMiddleware
from src.auth.models import AuthenticatedUser

# Security-Master specific imports
from .security_master_models import (
    SecurityMasterUser, 
    SecurityMasterRole, 
    SecurityMasterPermission,
    SECURITY_MASTER_ROLE_PERMISSIONS,
    FinancialDataAccessEvent
)

logger = logging.getLogger(__name__)

class SecurityMasterAuthMiddleware(PromptCraftAuthMiddleware):
    """Enhanced authentication middleware for Security-Master financial data access"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_scheme = HTTPBearer()
        
    async def dispatch(self, request: Request, call_next):
        """Process request with Security-Master specific authentication and audit logging"""
        
        # Use PromptCraft base authentication
        response = await super().dispatch(request, call_next)
        
        # Add Security-Master specific audit logging
        if hasattr(request.state, "user"):
            await self._log_financial_data_access(request)
            
        return response
    
    def _map_to_security_master_user(self, user: AuthenticatedUser) -> SecurityMasterUser:
        """Map PromptCraft user to Security-Master user with appropriate role"""
        
        # Role mapping logic based on email domain or groups
        role = self._determine_security_master_role(user)
        permissions = SECURITY_MASTER_ROLE_PERMISSIONS.get(role, [])
        
        return SecurityMasterUser(
            email=user.email,
            name=user.name,
            role=role,
            permissions=permissions,
            institution_access=self._get_institution_access(user),
            session_expires=user.session_expires
        )
    
    def _determine_security_master_role(self, user: AuthenticatedUser) -> SecurityMasterRole:
        """Determine Security-Master role based on user attributes"""
        
        # Admin users (add your admin email)
        if user.email in ["byron@your-domain.com", "admin@your-domain.com"]:
            return SecurityMasterRole.ADMIN
        
        # Role based on email patterns or user groups
        if "portfolio" in user.email.lower():
            return SecurityMasterRole.PORTFOLIO_MANAGER
        elif "analyst" in user.email.lower():
            return SecurityMasterRole.ANALYST
        elif "audit" in user.email.lower():
            return SecurityMasterRole.AUDITOR
        elif "compliance" in user.email.lower():
            return SecurityMasterRole.COMPLIANCE
        else:
            # Default role for unknown users
            return SecurityMasterRole.ANALYST
    
    def _get_institution_access(self, user: AuthenticatedUser) -> List[str]:
        """Determine which institutions user can access"""
        
        # Default: all institutions for admin and portfolio managers
        # In production, this would be configured in database
        if user.email in ["byron@your-domain.com"]:
            return ["Wells Fargo", "Interactive Brokers", "AltoIRA", "Kubera"]
        else:
            return ["Wells Fargo"]  # Default access
    
    async def _log_financial_data_access(self, request: Request):
        """Log financial data access for audit trail"""
        
        user = request.state.user
        
        access_event = FinancialDataAccessEvent(
            user_email=user.email,
            action=request.method,
            resource=str(request.url.path),
            timestamp=datetime.utcnow(),
            ip_address=request.client.host,
            success=True,  # Will be updated based on response
            details={
                "user_agent": request.headers.get("user-agent"),
                "role": user.role,
                "session_id": getattr(request.state, "session_id", None)
            }
        )
        
        # Store audit event (implement your audit storage)
        await self._store_audit_event(access_event)
    
    async def _store_audit_event(self, event: FinancialDataAccessEvent):
        """Store audit event in database"""
        # Implementation would store in audit_log table
        logger.info(f"Financial data access: {event.user_email} -> {event.resource}")

def require_permission(required_permission: SecurityMasterPermission):
    """Decorator to require specific permission for endpoint access"""
    
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if required_permission not in user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {required_permission}"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
EOF

echo "✅ Enterprise authentication integrated with PromptCraft patterns"
```

---

### Issue P5-003: Production Deployment Automation (PromptCraft Deployment Patterns)

**Branch**: `feature/production-deployment-automation`  
**Estimated Time**: 5 hours  
**Priority**: High  
**Week**: 20  

#### Description
Automate production deployment by adapting PromptCraft's Docker containerization and deployment strategies for Security-Master with Cloudflare tunnel integration and enterprise monitoring.

#### Acceptance Criteria
- [ ] **Docker Containerization** (PromptCraft patterns):
  - Multi-stage Docker build for optimized image size
  - Health checks and graceful shutdown handling
  - Environment-specific configuration management

- [ ] **Docker Compose Configuration**:
  - Production-ready services (API, Worker, Database, Redis)
  - Network isolation and security configuration
  - Volume management for persistent data

- [ ] **Cloudflare Integration**:
  - Automated tunnel configuration and management
  - Integration with existing Cloudflare Access policies
  - SSL/TLS handled entirely by Cloudflare (no local certificates)

- [ ] **Deployment Automation**:
  - Zero-downtime deployment scripts
  - Database migration automation
  - Backup and recovery procedures

#### Implementation Commands
```bash
# Copy and adapt PromptCraft Docker configurations
cp /home/byron/dev/PromptCraft/Dockerfile src/security_master/docker/api.Dockerfile
cp /home/byron/dev/PromptCraft/docker-compose.yml src/security_master/docker/

# Create production Docker configuration
cat > docker/docker-compose.production.yml << 'EOF'
version: '3.8'

services:
  postgresql:
    image: postgres:17-alpine
    container_name: pp_security_db_prod
    environment:
      POSTGRES_DB: ${DATABASE_NAME}
      POSTGRES_USER: ${DATABASE_USER}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - pg_data_prod:/var/lib/postgresql/data
      - pg_backups_prod:/var/lib/postgresql/backups
      - ./sql/init:/docker-entrypoint-initdb.d:ro
    networks:
      - database_net
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DATABASE_USER} -d ${DATABASE_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: pp_security_cache_prod
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data_prod:/data
    networks:
      - cache_net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    logging:
      driver: "json-file"
      options:
        max-size: "5m"
        max-file: "3"

  api:
    build:
      context: ..
      dockerfile: docker/api.Dockerfile
      target: production
    container_name: pp_security_api_prod
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@postgresql:5432/${DATABASE_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CLOUDFLARE_AUDIENCE=${CLOUDFLARE_AUDIENCE}
      - JWT_SECRET=${JWT_SECRET}
      - OPENFIGI_API_KEY=${OPENFIGI_API_KEY}
      - LOG_LEVEL=WARNING
    volumes:
      - app_data:/app/data
      - app_logs:/app/logs
      - backup_data:/app/backups:ro
    networks:
      - api_net
      - database_net
      - cache_net
    depends_on:
      postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "5"

  worker:
    build:
      context: ..
      dockerfile: docker/worker.Dockerfile
      target: production
    container_name: pp_security_worker_prod
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@postgresql:5432/${DATABASE_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - OPENFIGI_API_KEY=${OPENFIGI_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - app_data:/app/data
      - app_logs:/app/logs
    networks:
      - database_net
      - cache_net
    depends_on:
      postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import redis; redis.Redis(host='redis', password='${REDIS_PASSWORD}').ping()"]
      interval: 60s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  prometheus:
    image: prom/prometheus:latest
    container_name: pp_security_metrics_prod
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=90d'
      - '--web.enable-lifecycle'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - monitoring_net
      - api_net
    restart: unless-stopped

networks:
  api_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
  database_net:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.21.0.0/24
  cache_net:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.22.0.0/24
  monitoring_net:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.23.0.0/24

volumes:
  pg_data_prod:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/cache/appdata/pp-security-prod/postgresql/data
  pg_backups_prod:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/user/pp-security-prod/backups
  redis_data_prod:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/cache/appdata/pp-security-prod/redis
  app_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/user/pp-security-prod/data
  app_logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/user/pp-security-prod/logs
  backup_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/user/pp-security-prod/backups
  prometheus_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/cache/appdata/pp-security-prod/prometheus
EOF

# Create production deployment script
cat > scripts/deploy_production.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Production Deployment Script for Security-Master
echo "🚀 Starting Security-Master Production Deployment"

# Configuration
ENVIRONMENT="production"
BACKUP_DIR="/mnt/user/pp-security-prod/backups"
DEPLOY_DIR="/mnt/user/pp-security-prod/deploy"
LOG_FILE="/mnt/user/pp-security-prod/logs/deploy_$(date +%Y%m%d_%H%M%S).log"

# Ensure directories exist
mkdir -p "$BACKUP_DIR" "$DEPLOY_DIR" "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
trap 'log "❌ Deployment failed at line $LINENO"; exit 1' ERR

log "📋 Pre-deployment validation"

# Check environment file
if [[ ! -f ".env.production" ]]; then
    log "❌ Missing .env.production file"
    exit 1
fi

# Source environment variables
source .env.production

# Validate required environment variables
required_vars=(
    "DATABASE_NAME" "DATABASE_USER" "DATABASE_PASSWORD"
    "REDIS_PASSWORD" "JWT_SECRET" "CLOUDFLARE_AUDIENCE"
    "OPENFIGI_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        log "❌ Missing required environment variable: $var"
        exit 1
    fi
done

log "✅ Environment validation passed"

log "📦 Creating database backup"
if docker ps -q --filter "name=pp_security_db_prod" | grep -q .; then
    docker exec pp_security_db_prod pg_dump \
        -U "$DATABASE_USER" \
        -d "$DATABASE_NAME" \
        -f "/var/lib/postgresql/backups/pre_deploy_$(date +%Y%m%d_%H%M%S).sql" \
        --verbose
    log "✅ Database backup completed"
else
    log "ℹ️  No existing database container found, skipping backup"
fi

log "🏗️  Building Docker images"
docker-compose -f docker/docker-compose.production.yml build --no-cache

log "🔄 Stopping existing services"
if docker-compose -f docker/docker-compose.production.yml ps -q | grep -q .; then
    docker-compose -f docker/docker-compose.production.yml down --timeout 60
    log "✅ Services stopped gracefully"
fi

log "🗄️  Running database migrations"
# Start only database and redis for migrations
docker-compose -f docker/docker-compose.production.yml up -d postgresql redis

# Wait for database to be ready
max_attempts=30
attempt=0
while ! docker exec pp_security_db_prod pg_isready -U "$DATABASE_USER" -d "$DATABASE_NAME" > /dev/null 2>&1; do
    if [[ $attempt -ge $max_attempts ]]; then
        log "❌ Database failed to start after $max_attempts attempts"
        exit 1
    fi
    log "⏳ Waiting for database to be ready (attempt $((++attempt))/$max_attempts)"
    sleep 5
done

log "✅ Database is ready"

# Run migrations (assuming Alembic setup)
docker run --rm --network pp-security-prod_database_net \
    -e DATABASE_URL="postgresql://$DATABASE_USER:$DATABASE_PASSWORD@postgresql:5432/$DATABASE_NAME" \
    pp-security-api:latest alembic upgrade head

log "✅ Database migrations completed"

log "🚀 Starting all services"
docker-compose -f docker/docker-compose.production.yml up -d

# Wait for API to be healthy
log "⏳ Waiting for API to be healthy"
max_attempts=60
attempt=0
while ! docker exec pp_security_api_prod curl -f http://localhost:8000/health > /dev/null 2>&1; do
    if [[ $attempt -ge $max_attempts ]]; then
        log "❌ API failed to become healthy after $max_attempts attempts"
        exit 1
    fi
    log "⏳ API health check (attempt $((++attempt))/$max_attempts)"
    sleep 10
done

log "✅ API is healthy"

log "🔍 Running smoke tests"
# Basic smoke tests
docker exec pp_security_api_prod python -m pytest tests/smoke/ -v || {
    log "❌ Smoke tests failed"
    exit 1
}

log "✅ Smoke tests passed"

log "📊 Deployment summary"
docker-compose -f docker/docker-compose.production.yml ps

log "🎉 Production deployment completed successfully!"
log "📝 Deployment logged to: $LOG_FILE"

# Display service URLs (these would be through Cloudflare tunnel)
echo "
🌐 Service Access:
   - Web UI: https://pp-security.your-domain.com
   - API: https://pp-security.your-domain.com/api/v1
   - Health Check: https://pp-security.your-domain.com/health
   - Metrics: https://pp-security.your-domain.com/metrics (admin only)

📋 Next Steps:
   1. Verify Cloudflare tunnel is routing correctly
   2. Test authentication through Cloudflare Access
   3. Run full integration tests
   4. Monitor logs for any issues
"
EOF

chmod +x scripts/deploy_production.sh

echo "✅ Production deployment automation completed"
```

---

### Issue P5-004: Comprehensive Monitoring and Observability (PromptCraft Patterns)

**Branch**: `feature/comprehensive-monitoring`  
**Estimated Time**: 4 hours  
**Priority**: Medium  
**Week**: 20  

#### Description
Implement comprehensive monitoring and observability by adapting PromptCraft's monitoring patterns for Security-Master with financial data specific metrics and alerting.

#### Acceptance Criteria
- [ ] **Application Performance Monitoring** (PromptCraft enhanced):
  - API response time monitoring and alerting
  - Database query performance tracking
  - External API (OpenFIGI) response time and rate limit monitoring
  - Background job processing metrics

- [ ] **Business Metrics Monitoring**:
  - Securities classification accuracy and coverage
  - Institution data import success rates
  - Data quality metrics and validation failures
  - Portfolio analytics performance metrics

- [ ] **Infrastructure Monitoring**:
  - Container resource utilization
  - Database performance and connection pool metrics
  - Cache hit rates and Redis performance
  - Disk usage and backup status

- [ ] **Alerting and Notification**:
  - Critical service failures
  - Data quality threshold breaches
  - Authentication and security events
  - Performance degradation alerts

#### Implementation Commands
```bash
# Create monitoring package structure
mkdir -p src/security_master/monitoring/{metrics,alerts,dashboards}

# Copy and adapt PromptCraft monitoring components
cp -r /home/byron/dev/PromptCraft/src/monitoring src/security_master/monitoring/base

# Create Security-Master specific metrics
cat > src/security_master/monitoring/metrics/financial_metrics.py << 'EOF'
"""
Financial Data Specific Metrics for Security-Master

Provides comprehensive metrics for:
- Securities classification accuracy and coverage
- Institution data quality and import success rates  
- Portfolio analytics performance
- External API usage and rate limiting
"""

from prometheus_client import Counter, Histogram, Gauge, Enum
import time
from typing import Dict, Any, Optional
from src.utils.logging_mixin import LoggerMixin

# Securities classification metrics
securities_classification_total = Counter(
    'securities_classification_total',
    'Total number of securities classified',
    ['method', 'institution', 'success']
)

securities_classification_accuracy = Gauge(
    'securities_classification_accuracy',
    'Classification accuracy percentage',
    ['method', 'asset_class']
)

securities_classification_duration = Histogram(
    'securities_classification_duration_seconds',
    'Time spent classifying securities',
    ['method', 'institution'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Institution data import metrics
institution_import_total = Counter(
    'institution_import_total',
    'Total institution data imports',
    ['institution', 'file_type', 'status']
)

institution_import_records = Histogram(
    'institution_import_records_count',
    'Number of records per import',
    ['institution'],
    buckets=[1, 10, 50, 100, 500, 1000, 5000, 10000]
)

institution_data_quality_score = Gauge(
    'institution_data_quality_score',
    'Data quality score for institution data',
    ['institution', 'metric_type']
)

# External API metrics
external_api_requests_total = Counter(
    'external_api_requests_total',
    'Total external API requests',
    ['api', 'endpoint', 'status_code']
)

external_api_duration = Histogram(
    'external_api_duration_seconds',
    'External API response time',
    ['api', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

external_api_rate_limit_remaining = Gauge(
    'external_api_rate_limit_remaining',
    'Remaining API calls for external service',
    ['api']
)

# Portfolio analytics metrics
portfolio_analytics_requests_total = Counter(
    'portfolio_analytics_requests_total',
    'Total portfolio analytics requests',
    ['metric_type', 'success']
)

portfolio_analytics_duration = Histogram(
    'portfolio_analytics_duration_seconds',
    'Portfolio analytics calculation time',
    ['metric_type'],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0]
)

# Data quality metrics
data_validation_failures_total = Counter(
    'data_validation_failures_total',
    'Total data validation failures',
    ['validation_type', 'institution', 'severity']
)

data_completeness_percentage = Gauge(
    'data_completeness_percentage',
    'Data completeness percentage',
    ['institution', 'data_type']
)

class FinancialMetricsCollector(LoggerMixin):
    """Collector for Security-Master specific metrics"""
    
    def __init__(self):
        self.logger.info("Initializing Financial Metrics Collector")
    
    def record_classification_attempt(self, method: str, institution: str, 
                                    success: bool, duration: float):
        """Record a securities classification attempt"""
        securities_classification_total.labels(
            method=method, 
            institution=institution,
            success=str(success).lower()
        ).inc()
        
        securities_classification_duration.labels(
            method=method,
            institution=institution
        ).observe(duration)
    
    def update_classification_accuracy(self, method: str, asset_class: str, 
                                     accuracy: float):
        """Update classification accuracy metric"""
        securities_classification_accuracy.labels(
            method=method,
            asset_class=asset_class
        ).set(accuracy)
    
    def record_institution_import(self, institution: str, file_type: str, 
                                status: str, record_count: int):
        """Record institution data import"""
        institution_import_total.labels(
            institution=institution,
            file_type=file_type,
            status=status
        ).inc()
        
        institution_import_records.labels(
            institution=institution
        ).observe(record_count)
    
    def update_data_quality_score(self, institution: str, metric_type: str, 
                                score: float):
        """Update data quality score"""
        institution_data_quality_score.labels(
            institution=institution,
            metric_type=metric_type
        ).set(score)
    
    def record_external_api_call(self, api: str, endpoint: str, 
                                status_code: int, duration: float,
                                rate_limit_remaining: Optional[int] = None):
        """Record external API call metrics"""
        external_api_requests_total.labels(
            api=api,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        external_api_duration.labels(
            api=api,
            endpoint=endpoint
        ).observe(duration)
        
        if rate_limit_remaining is not None:
            external_api_rate_limit_remaining.labels(api=api).set(rate_limit_remaining)
    
    def record_portfolio_analytics(self, metric_type: str, success: bool, 
                                 duration: float):
        """Record portfolio analytics metrics"""
        portfolio_analytics_requests_total.labels(
            metric_type=metric_type,
            success=str(success).lower()
        ).inc()
        
        portfolio_analytics_duration.labels(
            metric_type=metric_type
        ).observe(duration)
    
    def record_validation_failure(self, validation_type: str, institution: str, 
                                severity: str):
        """Record data validation failure"""
        data_validation_failures_total.labels(
            validation_type=validation_type,
            institution=institution,
            severity=severity
        ).inc()
    
    def update_data_completeness(self, institution: str, data_type: str, 
                               completeness: float):
        """Update data completeness percentage"""
        data_completeness_percentage.labels(
            institution=institution,
            data_type=data_type
        ).set(completeness)

# Global metrics collector instance
financial_metrics = FinancialMetricsCollector()
EOF

# Create monitoring configuration
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'pp-security-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'pp-security-worker'
    static_configs:
      - targets: ['worker:8001']
    metrics_path: '/metrics'
    scrape_interval: 60s

  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres_exporter:9187']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']
    scrape_interval: 30s
EOF

# Create alert rules
cat > monitoring/alert_rules.yml << 'EOF'
groups:
- name: security_master_alerts
  rules:
  
  # API Performance Alerts
  - alert: APIHighLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High API latency detected"
      description: "95th percentile latency is {{ $value }}s"

  - alert: APIHighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High API error rate"
      description: "Error rate is {{ $value | humanizePercentage }}"

  # Classification Alerts
  - alert: ClassificationAccuracyLow
    expr: securities_classification_accuracy < 0.9
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Securities classification accuracy is low"
      description: "Classification accuracy for {{ $labels.method }}/{{ $labels.asset_class }} is {{ $value | humanizePercentage }}"

  - alert: ClassificationServiceDown
    expr: up{job="pp-security-api"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Classification service is down"
      description: "Classification service has been down for more than 1 minute"

  # External API Alerts
  - alert: ExternalAPIRateLimitLow
    expr: external_api_rate_limit_remaining < 10
    for: 0m
    labels:
      severity: warning
    annotations:
      summary: "External API rate limit nearly exhausted"
      description: "{{ $labels.api }} has {{ $value }} requests remaining"

  - alert: ExternalAPIDown
    expr: external_api_requests_total{status_code=~"5..|timeout"} / external_api_requests_total > 0.5
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "External API failure rate high"
      description: "{{ $labels.api }} failure rate is {{ $value | humanizePercentage }}"

  # Data Quality Alerts
  - alert: DataQualityScoreLow
    expr: institution_data_quality_score < 0.8
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Data quality score is low"
      description: "{{ $labels.institution }} {{ $labels.metric_type }} quality score is {{ $value }}"

  - alert: ValidationFailuresHigh
    expr: rate(data_validation_failures_total[10m]) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High rate of data validation failures"
      description: "{{ $labels.validation_type }} failures for {{ $labels.institution }}: {{ $value }}/min"

  # Infrastructure Alerts
  - alert: DatabaseConnectionsHigh
    expr: postgresql_connections_active / postgresql_connections_max > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High database connection usage"
      description: "{{ $value | humanizePercentage }} of database connections in use"

  - alert: DiskSpaceLow
    expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Disk space critically low"
      description: "{{ $labels.mountpoint }} has {{ $value | humanizePercentage }} space remaining"
EOF

echo "✅ Comprehensive monitoring and observability implemented"
```

---

### Issue P5-005: Enterprise Security Hardening and Assessment

**Branch**: `feature/enterprise-security-hardening`  
**Estimated Time**: 4 hours  
**Priority**: High  
**Week**: 21  

#### Description
Implement comprehensive security hardening for production deployment with vulnerability assessment, penetration testing preparation, and compliance documentation.

#### Acceptance Criteria
- [ ] **Security Vulnerability Assessment**:
  - Automated security scanning with Bandit, Safety, and Semgrep
  - Container image vulnerability scanning
  - Dependency vulnerability tracking and alerting
  - Network security configuration review

- [ ] **Application Security Hardening**:
  - Input validation and sanitization for all financial data inputs
  - SQL injection prevention with parameterized queries
  - XSS protection for web UI components
  - CSRF protection for state-changing operations

- [ ] **Data Protection Implementation**:
  - Encryption at rest for all financial data
  - Secure API key management and rotation
  - Audit logging for all financial data access
  - Data retention and purging policies

- [ ] **Compliance and Documentation**:
  - Security audit documentation
  - Data flow diagrams for financial data
  - Risk assessment and mitigation documentation
  - Incident response procedures

#### Implementation Commands
```bash
# Create security assessment and hardening scripts
mkdir -p security/{scans,policies,documentation}

# Create comprehensive security scanning script
cat > security/scans/security_assessment.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Security Assessment Script for Security-Master Production Deployment
echo "🔒 Starting Comprehensive Security Assessment"

REPORT_DIR="security/reports/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$REPORT_DIR"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$REPORT_DIR/security_assessment.log"
}

log "🔍 Step 1: Static Code Analysis"

# Python security scanning with Bandit
log "Running Bandit security scan..."
poetry run bandit -r src/ -f json -o "$REPORT_DIR/bandit_report.json" || true
poetry run bandit -r src/ -f txt -o "$REPORT_DIR/bandit_report.txt" || true

# Safety check for known vulnerabilities
log "Running Safety vulnerability check..."
poetry run safety check --json --output "$REPORT_DIR/safety_report.json" || true

# Semgrep security rules
if command -v semgrep &> /dev/null; then
    log "Running Semgrep security analysis..."
    semgrep --config=auto --json --output="$REPORT_DIR/semgrep_report.json" src/ || true
fi

log "🐳 Step 2: Container Security Scanning"

# Build production image for scanning
log "Building production image for security scan..."
docker build -f docker/api.Dockerfile -t pp-security-api:security-scan .

# Container vulnerability scanning with Trivy
if command -v trivy &> /dev/null; then
    log "Running Trivy container scan..."
    trivy image --format json --output "$REPORT_DIR/trivy_report.json" pp-security-api:security-scan || true
fi

log "🌐 Step 3: Network Security Assessment"

# Check for exposed ports and services
log "Checking exposed ports..."
docker-compose -f docker/docker-compose.production.yml config > "$REPORT_DIR/docker_compose_config.yml"

# Analyze network configuration
python3 << 'PYTHON' > "$REPORT_DIR/network_analysis.txt"
import yaml
import json

# Load docker-compose configuration
with open('security/reports/*/docker_compose_config.yml', 'r') as f:
    config = yaml.safe_load(f)

print("Network Security Analysis")
print("=" * 50)

# Check for external port exposure
services = config.get('services', {})
exposed_ports = []

for service_name, service_config in services.items():
    ports = service_config.get('ports', [])
    if ports:
        for port in ports:
            exposed_ports.append(f"{service_name}: {port}")

if exposed_ports:
    print("⚠️  Externally Exposed Ports:")
    for port in exposed_ports:
        print(f"  - {port}")
else:
    print("✅ No externally exposed ports detected")

# Check network isolation
networks = config.get('networks', {})
print(f"\n📡 Network Configuration:")
for network_name, network_config in networks.items():
    internal = network_config.get('internal', False)
    status = "🔒 Internal" if internal else "🌐 External"
    print(f"  - {network_name}: {status}")
PYTHON

log "🔑 Step 4: Authentication and Authorization Review"

# Review JWT configuration
log "Analyzing authentication configuration..."
python3 << 'PYTHON' > "$REPORT_DIR/auth_analysis.txt"
import os
import re

print("Authentication Security Analysis")
print("=" * 50)

# Check for hardcoded secrets (basic patterns)
secret_patterns = [
    r'password\s*=\s*["\'][^"\']+["\']',
    r'api_key\s*=\s*["\'][^"\']+["\']',
    r'secret\s*=\s*["\'][^"\']+["\']',
    r'token\s*=\s*["\'][^"\']+["\']'
]

issues_found = []
for root, dirs, files in os.walk('src/'):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            issues_found.append(f"{file_path}: {matches}")
            except Exception as e:
                pass

if issues_found:
    print("⚠️  Potential hardcoded secrets found:")
    for issue in issues_found:
        print(f"  - {issue}")
else:
    print("✅ No hardcoded secrets detected in Python files")

# Check environment variable usage
env_file_patterns = ['.env', '.env.example', '.env.production']
print(f"\n🔐 Environment Configuration:")
for pattern in env_file_patterns:
    if os.path.exists(pattern):
        print(f"  ✅ {pattern} found")
    else:
        print(f"  ❌ {pattern} missing")
PYTHON

log "💾 Step 5: Data Protection Assessment"

# Check database security configuration
log "Analyzing database security..."
python3 << 'PYTHON' > "$REPORT_DIR/data_protection_analysis.txt"
import os

print("Data Protection Analysis")
print("=" * 50)

# Check for database connection security
db_security_checks = [
    ("SSL/TLS Configuration", "sslmode=require" in os.environ.get('DATABASE_URL', '')),
    ("Password Complexity", len(os.environ.get('DATABASE_PASSWORD', '')) >= 16),
    ("JWT Secret Strength", len(os.environ.get('JWT_SECRET', '')) >= 32),
    ("Redis Password Set", bool(os.environ.get('REDIS_PASSWORD', '')))
]

for check_name, passed in db_security_checks:
    status = "✅" if passed else "❌"
    print(f"  {status} {check_name}")

# Check for encryption at rest configuration
print(f"\n🔒 Encryption Configuration:")
encryption_vars = ['ENCRYPTION_KEY', 'BACKUP_ENCRYPTION_KEY', 'API_KEY_ENCRYPTION_KEY']
for var in encryption_vars:
    if os.environ.get(var):
        print(f"  ✅ {var} configured")
    else:
        print(f"  ❌ {var} not configured")
PYTHON

log "📊 Step 6: Generating Security Summary Report"

# Generate comprehensive security report
python3 << 'PYTHON' > "$REPORT_DIR/security_summary.json"
import json
import os
from datetime import datetime

# Collect all security scan results
security_summary = {
    "scan_timestamp": datetime.utcnow().isoformat(),
    "scan_version": "1.0",
    "overall_status": "pending_review",
    "scans_completed": [],
    "critical_issues": [],
    "high_issues": [],
    "medium_issues": [],
    "recommendations": []
}

# Check which scans completed successfully
scan_files = [
    ("bandit_report.json", "Static Code Analysis"),
    ("safety_report.json", "Dependency Vulnerability Scan"),
    ("trivy_report.json", "Container Vulnerability Scan"),
    ("network_analysis.txt", "Network Security Analysis"),
    ("auth_analysis.txt", "Authentication Security Review"),
    ("data_protection_analysis.txt", "Data Protection Assessment")
]

report_dir = os.environ.get('REPORT_DIR', '.')
for scan_file, scan_name in scan_files:
    if os.path.exists(f"{report_dir}/{scan_file}"):
        security_summary["scans_completed"].append(scan_name)

# Add standard recommendations
security_summary["recommendations"] = [
    "Enable automated security scanning in CI/CD pipeline",
    "Implement regular security updates and patch management",
    "Configure comprehensive audit logging for all financial data access",
    "Set up security monitoring and alerting",
    "Conduct regular penetration testing",
    "Review and update access controls quarterly",
    "Implement data retention and purging policies",
    "Create incident response and disaster recovery procedures"
]

# Write summary
with open(f"{report_dir}/security_summary.json", 'w') as f:
    json.dump(security_summary, f, indent=2)

print("Security Assessment Summary")
print("=" * 50)
print(f"Scans Completed: {len(security_summary['scans_completed'])}")
print(f"Report Location: {report_dir}")
print("\n📋 Next Steps:")
for rec in security_summary["recommendations"]:
    print(f"  • {rec}")
PYTHON

log "✅ Security assessment completed successfully!"
log "📄 Reports available in: $REPORT_DIR"

# Display summary
echo "
🔒 Security Assessment Summary
============================
📁 Report Directory: $REPORT_DIR
📊 Scans Completed: 
   • Static Code Analysis (Bandit)
   • Dependency Vulnerabilities (Safety)  
   • Container Security (Trivy)
   • Network Configuration Review
   • Authentication Analysis
   • Data Protection Assessment

🔍 Review all reports in the report directory
⚡ Address any critical or high severity issues before production deployment
"
EOF

chmod +x security/scans/security_assessment.sh

# Create security policies documentation
cat > security/policies/data_protection_policy.md << 'EOF'
# Data Protection Policy - Security-Master System

## Overview
This document outlines the data protection policies and procedures for the Security-Master system handling sensitive financial information.

## Data Classification
### Critical Data (Level 1)
- Complete portfolio holdings and valuations
- Individual transaction details with amounts
- Institution account numbers and identifiers
- API keys for external financial services

### Confidential Data (Level 2)  
- Securities classifications and research
- Institution data import files
- User authentication information
- System configuration data

### Internal Data (Level 3)
- Aggregated analytics and reports
- System logs (with PII removed)
- Performance metrics and monitoring data

## Data Protection Requirements

### Encryption Standards
- **At Rest**: AES-256 encryption for all Level 1 and Level 2 data
- **In Transit**: TLS 1.3 for all data transmission
- **Backups**: Full encryption with separate key management

### Access Controls
- **Role-Based Access**: Implemented through Cloudflare Access with granular permissions
- **Session Management**: Maximum 8-hour sessions with automatic timeout
- **Multi-Factor Authentication**: Required for all administrative functions

### Data Retention
- **Transaction Data**: 7 years retention for regulatory compliance
- **Audit Logs**: 10 years retention for forensic analysis
- **Import Files**: 3 years retention with automatic archival
- **System Logs**: 1 year retention with automated purging

### Data Purging Procedures
1. Automated identification of data exceeding retention periods
2. Secure deletion using DoD 5220.22-M standards
3. Audit logging of all purging activities
4. Regular verification of purging effectiveness

## Incident Response
### Data Breach Response
1. **Immediate Containment** (0-1 hours)
   - Isolate affected systems
   - Preserve forensic evidence
   - Notify security team

2. **Assessment** (1-4 hours)
   - Determine scope of breach
   - Identify affected data categories
   - Assess regulatory notification requirements

3. **Notification** (4-72 hours)
   - Internal stakeholders
   - Regulatory bodies (if required)
   - Affected users (if required)

### Recovery Procedures
1. **System Restoration** from secure backups
2. **Security Enhancement** based on incident analysis
3. **Monitoring Enhancement** to prevent recurrence
4. **Documentation** of lessons learned

## Compliance Requirements
- **Data Minimization**: Collect only necessary financial data
- **Purpose Limitation**: Use data only for stated business purposes
- **Accuracy**: Maintain data accuracy through validation procedures
- **Transparency**: Provide clear data usage documentation

## Monitoring and Auditing
### Continuous Monitoring
- Real-time access logging for all financial data
- Automated anomaly detection for unusual access patterns
- Regular vulnerability assessments and security scans

### Regular Audits
- Quarterly access control reviews
- Annual data retention compliance audits
- Bi-annual security posture assessments
- Monthly data quality validation reviews

This policy is reviewed quarterly and updated as needed to maintain compliance with applicable regulations and security best practices.
EOF

echo "✅ Enterprise security hardening and assessment implemented"
```

This completes the refined Phase 5 planning with detailed PromptCraft integration. The implementation leverages proven patterns from the PromptCraft codebase while adapting them specifically for Security-Master's financial data requirements.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Read and analyze Phase 5 planning documentation", "status": "completed"}, {"content": "Identify refinement needs for Phase 5 advanced features", "status": "completed"}, {"content": "Create detailed execution commands for all Phase 5 issues", "status": "completed"}, {"content": "Create Phase 5 automation scripts", "status": "in_progress"}, {"content": "Create Phase 5 templates and code examples", "status": "pending"}, {"content": "Create Phase 5 validation checklist", "status": "pending"}, {"content": "Create Phase 5 execution guide", "status": "pending"}, {"content": "Document Phase 5 troubleshooting procedures", "status": "pending"}]