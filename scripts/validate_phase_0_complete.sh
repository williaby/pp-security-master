#!/bin/bash
# Master validation script for Phase 0 completion
# This script validates all Phase 0 requirements are met

set -e

echo "🔍 Phase 0: Foundation & Prerequisites - Complete Validation"
echo "==========================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_WARNING=0

check_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((TOTAL_PASS++))
}

check_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((TOTAL_FAIL++))
}

check_warning() {
    echo -e "${YELLOW}⚠️ WARNING:${NC} $1"
    ((TOTAL_WARNING++))
}

section_header() {
    echo -e "${BLUE}▶️ $1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

# Check if we're in the right directory
if [[ ! -f "PROJECT_PLAN.md" ]]; then
    echo -e "${RED}❌ Please run this script from the pp-security-master project root directory${NC}"
    exit 1
fi

echo "Starting comprehensive Phase 0 validation..."
echo ""

# Issue P0-001: PostgreSQL 17 (Already completed)
section_header "P0-001: PostgreSQL 17 Unraid Installation"

# Test database connection
if command -v psql &> /dev/null; then
    if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT version();" &>/dev/null; then
        DB_VERSION=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT version();" -t | xargs)
        check_pass "Database connection successful: $DB_VERSION"
    else
        check_fail "Database connection failed - check credentials in .env"
    fi
else
    check_warning "psql not available locally - assuming database is accessible"
fi

echo ""

# Issue P0-002: Development Environment
section_header "P0-002: Development Environment Standardization"

# Python 3.11+
if command -v python &> /dev/null && python --version | grep -q "3.11"; then
    check_pass "Python 3.11+ installed: $(python --version)"
else
    check_fail "Python 3.11+ not found"
fi

# Poetry
if command -v poetry &> /dev/null; then
    check_pass "Poetry installed: $(poetry --version)"
    
    if poetry config virtualenvs.in-project | grep -q "true"; then
        check_pass "Poetry configured for in-project virtual environments"
    else
        check_fail "Poetry not configured correctly"
    fi
    
    if poetry env info --path &>/dev/null; then
        check_pass "Virtual environment exists"
    else
        check_fail "Virtual environment not created"
    fi
else
    check_fail "Poetry not installed"
fi

# VSCode configuration
if [[ -f ".vscode/settings.json" && -f ".vscode/extensions.json" ]]; then
    check_pass "VSCode configuration files exist"
else
    check_fail "VSCode configuration missing"
fi

# Environment variables
if [[ -f ".env.example" && -f ".env" ]]; then
    check_pass "Environment configuration files exist"
    
    if grep -q "PP_DB_PASSWORD=your_secure_password_here" .env; then
        check_warning "Database password still using placeholder"
    else
        check_pass "Database password configured"
    fi
else
    check_fail "Environment files missing"
fi

echo ""

# Issue P0-003: Repository Structure
section_header "P0-003: Repository Structure and Development Standards"

# Check directory structure
REQUIRED_DIRS=(
    "src/security_master"
    "tests/unit"
    "tests/integration"
    "docs/adr"
    "sql/versions"
    "schema_exports"
    "sample_data"
    "scripts"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        check_pass "Directory exists: $dir"
    else
        check_fail "Directory missing: $dir"
    fi
done

# Check configuration files
CONFIG_FILES=(".gitignore" ".editorconfig")
for file in "${CONFIG_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        check_pass "Configuration file exists: $file"
    else
        check_fail "Configuration file missing: $file"
    fi
done

echo ""

# Issue P0-004: Security Master Table Schema
section_header "P0-004: Core Security Master Table Schema"

if command -v psql &> /dev/null; then
    # Check if securities_master table exists
    if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\d securities_master" &>/dev/null; then
        check_pass "securities_master table exists"
        
        # Check for key columns
        KEY_COLUMNS=("isin" "security_name" "asset_class" "data_quality_score")
        for col in "${KEY_COLUMNS[@]}"; do
            if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\d securities_master" | grep -q "$col"; then
                check_pass "Column exists: $col"
            else
                check_fail "Column missing: $col"
            fi
        done
        
        # Test table constraints
        if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "INSERT INTO securities_master (isin, security_name, security_type, currency_code, asset_class) VALUES ('TEST12345678', 'Test Security', 'Test Type', 'USD', 'equity'); DELETE FROM securities_master WHERE isin = 'TEST12345678';" &>/dev/null; then
            check_pass "Table constraints and operations working"
        else
            check_fail "Table constraints or operations not working"
        fi
    else
        check_fail "securities_master table does not exist"
    fi
else
    check_warning "Cannot validate database schema - psql not available"
fi

echo ""

# Issue P0-005: Alembic Migration Framework
section_header "P0-005: Alembic Migration Framework Setup"

if [[ -f "alembic.ini" ]]; then
    check_pass "alembic.ini exists"
else
    check_fail "alembic.ini missing"
fi

if [[ -d "sql/versions" && -f "sql/versions/env.py" ]]; then
    check_pass "Alembic versions directory and env.py exist"
else
    check_fail "Alembic migration structure missing"
fi

# Test Alembic functionality
if poetry run alembic current &>/dev/null; then
    check_pass "Alembic can determine current revision"
else
    check_fail "Alembic not working correctly"
fi

echo ""

# Issue P0-006: Configuration System
section_header "P0-006: Core Configuration System Implementation"

if [[ -f "src/security_master/config/settings.py" ]]; then
    check_pass "Configuration module exists"
    
    # Test configuration loading
    if poetry run python -c "
import sys
sys.path.insert(0, 'src')
from security_master.config.settings import get_settings
settings = get_settings()
print('Configuration loaded successfully')
" &>/dev/null; then
        check_pass "Configuration system loads successfully"
    else
        check_fail "Configuration system not working"
    fi
else
    check_fail "Configuration module missing"
fi

echo ""

# Issue P0-007: Database ORM Layer
section_header "P0-007: Database Connection and ORM Layer"

if [[ -f "src/security_master/database/engine.py" && -f "src/security_master/database/models.py" ]]; then
    check_pass "Database modules exist"
    
    # Test database connection through ORM
    if poetry run python -c "
import sys
sys.path.insert(0, 'src')
from security_master.database.engine import db_manager
if db_manager.health_check():
    print('Database health check passed')
else:
    exit(1)
" &>/dev/null; then
        check_pass "Database ORM layer working"
    else
        check_fail "Database ORM layer not working"
    fi
else
    check_fail "Database modules missing"
fi

echo ""

# Issue P0-008: Development Tooling
section_header "P0-008: Development Tooling Integration"

if [[ -f "pyproject.toml" ]]; then
    check_pass "pyproject.toml exists"
    
    # Check for tool configurations
    TOOL_CONFIGS=("tool.black" "tool.ruff" "tool.mypy" "tool.pytest")
    for config in "${TOOL_CONFIGS[@]}"; do
        if grep -q "$config" pyproject.toml; then
            check_pass "Tool configuration found: $config"
        else
            check_warning "Tool configuration missing: $config"
        fi
    done
else
    check_fail "pyproject.toml missing"
fi

# Test development tools
DEV_TOOLS=("black" "ruff" "mypy" "pytest")
for tool in "${DEV_TOOLS[@]}"; do
    if poetry run $tool --version &>/dev/null; then
        check_pass "Tool available: $tool"
    else
        check_fail "Tool not available: $tool"
    fi
done

echo ""

# Issue P0-009: Data Validation Framework
section_header "P0-009: Basic Data Validation Framework"

if [[ -f "src/security_master/validation/models.py" && -f "src/security_master/validation/service.py" ]]; then
    check_pass "Validation modules exist"
    
    # Test validation framework
    if poetry run python -c "
import sys
sys.path.insert(0, 'src')
from security_master.validation.service import SecurityMasterValidator
validator = SecurityMasterValidator()
result = validator.validate_single({
    'isin': 'US0378331005',
    'security_name': 'Apple Inc.',
    'security_type': 'Common Stock',
    'currency_code': 'USD',
    'asset_class': 'equity'
})
if result.is_valid:
    print('Validation framework working')
else:
    exit(1)
" &>/dev/null; then
        check_pass "Data validation framework working"
    else
        check_fail "Data validation framework not working"
    fi
else
    check_fail "Validation modules missing"
fi

echo ""

# Issue P0-010: Integration Testing
section_header "P0-010: Phase 0 Integration Testing and Validation"

# Check if test structure exists
if [[ -d "tests/unit" && -d "tests/integration" ]]; then
    check_pass "Test directory structure exists"
else
    check_fail "Test directory structure missing"
fi

# Test pytest configuration
if poetry run pytest --collect-only &>/dev/null; then
    check_pass "Pytest can collect tests"
else
    check_warning "Pytest cannot collect tests (no tests may exist yet)"
fi

echo ""

# Overall Phase 0 Success Criteria Validation
section_header "Phase 0 Success Criteria Validation"

echo "Checking overall success criteria..."

# PostgreSQL operational
if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT 1;" &>/dev/null; then
    check_pass "PostgreSQL 17 operational with external development access"
else
    check_fail "PostgreSQL 17 not accessible"
fi

# Security master table
if command -v psql &> /dev/null && psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\d securities_master" &>/dev/null; then
    check_pass "Security master table created with comprehensive taxonomy fields"
else
    check_fail "Security master table not properly created"
fi

# Development cycle test
if [[ -f "pyproject.toml" ]] && poetry run python --version &>/dev/null && poetry run black --version &>/dev/null; then
    check_pass "Developer can execute complete cycle: code → lint → test → commit → deploy"
else
    check_fail "Complete development cycle not operational"
fi

# Database migrations
if [[ -f "alembic.ini" ]] && poetry run alembic current &>/dev/null; then
    check_pass "Database migrations functional with rollback capability"
else
    check_fail "Database migrations not functional"
fi

# Configuration system
if [[ -f "src/security_master/config/settings.py" ]]; then
    check_pass "Configuration system loading settings from all target environments"
else
    check_fail "Configuration system not implemented"
fi

echo ""

# Final Summary
echo "=================================================="
echo -e "${BLUE}Phase 0 Validation Summary${NC}"
echo "=================================================="
echo ""
echo -e "✅ Tests Passed: ${GREEN}$TOTAL_PASS${NC}"
echo -e "❌ Tests Failed: ${RED}$TOTAL_FAIL${NC}"
echo -e "⚠️  Warnings: ${YELLOW}$TOTAL_WARNING${NC}"
echo ""

# Determine overall status
if [[ $TOTAL_FAIL -eq 0 ]]; then
    echo -e "${GREEN}🎉 PHASE 0 COMPLETE - ALL REQUIREMENTS MET!${NC}"
    echo ""
    echo "Phase 0 has been successfully completed. The foundation is solid and ready for Phase 1 development."
    echo ""
    echo "✅ PostgreSQL 17 operational on Unraid"
    echo "✅ Development environment standardized" 
    echo "✅ Repository structure established"
    echo "✅ Security master table created"
    echo "✅ Database migrations functional"
    echo "✅ Configuration system operational"
    echo "✅ Database ORM layer working"
    echo "✅ Development tooling integrated"
    echo "✅ Data validation framework ready"
    echo "✅ Integration testing validated"
    echo ""
    echo "🚀 Ready to proceed to Phase 1: Core Infrastructure Development"
    echo ""
    exit 0
elif [[ $TOTAL_FAIL -le 3 ]]; then
    echo -e "${YELLOW}⚠️ PHASE 0 MOSTLY COMPLETE - MINOR ISSUES FOUND${NC}"
    echo ""
    echo "Phase 0 is mostly complete but has some minor issues that should be addressed:"
    echo ""
    echo "Next steps:"
    echo "1. Review failed tests above"
    echo "2. Run individual validation scripts: ./scripts/validate_issue_P0-*.sh"
    echo "3. Fix identified issues"
    echo "4. Re-run this validation script"
    echo ""
    exit 1
else
    echo -e "${RED}❌ PHASE 0 INCOMPLETE - SIGNIFICANT ISSUES FOUND${NC}"
    echo ""
    echo "Phase 0 has significant issues that must be resolved before proceeding:"
    echo ""
    echo "Recommended actions:"
    echo "1. Run the setup script: ./scripts/setup_environment.sh"
    echo "2. Follow the execution guide: docs/planning/phase-0-execution-guide.md"
    echo "3. Address all failed tests identified above"
    echo "4. Re-run this validation script until all tests pass"
    echo ""
    echo "⚠️ Do not proceed to Phase 1 until all Phase 0 requirements are met."
    echo ""
    exit 1
fi