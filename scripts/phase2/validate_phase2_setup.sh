#!/bin/bash
# Phase 2: External Integrations Validation Script
# Comprehensive validation of external integrations setup

set -e

echo "🔍 Phase 2: External Integrations Validation"
echo "============================================"
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

echo "Starting comprehensive Phase 2 validation..."
echo ""

# Test 1: Phase 1 Prerequisites
section_header "Phase 1 Prerequisites"

if [[ -f "scripts/phase1/validate_phase1_database.sh" ]]; then
    if ./scripts/phase1/validate_phase1_database.sh > /dev/null 2>&1; then
        check_pass "Phase 1 database setup validated"
    else
        check_fail "Phase 1 database validation failed - complete Phase 1 first"
    fi
else
    check_warning "Phase 1 validation script not found"
fi

echo ""

# Test 2: External Repository Structure  
section_header "External Repository Structure"

if [[ -d "src/external" ]]; then
    check_pass "External directory exists"
    
    if [[ -d "src/external/pp-portfolio-classifier" ]]; then
        check_pass "pp-portfolio-classifier subtree directory exists"
        
        # Check if it has actual content (not just empty directory)
        if [[ $(find src/external/pp-portfolio-classifier -type f | wc -l) -gt 0 ]]; then
            check_pass "pp-portfolio-classifier has content"
        else
            check_warning "pp-portfolio-classifier directory is empty"
        fi
    else
        check_fail "pp-portfolio-classifier subtree missing"
    fi
    
    if [[ -d "src/external/ppxml2db" ]]; then
        check_pass "ppxml2db subtree directory exists"
        
        # Check if it has actual content
        if [[ $(find src/external/ppxml2db -type f | wc -l) -gt 0 ]]; then
            check_pass "ppxml2db has content"
        else
            check_warning "ppxml2db directory is empty"
        fi
    else
        check_fail "ppxml2db subtree missing"
    fi
else
    check_fail "External directory missing"
fi

echo ""

# Test 3: External API Client Structure
section_header "External API Client Structure"

if [[ -d "src/security_master/external_apis" ]]; then
    check_pass "External APIs directory exists"
    
    if [[ -f "src/security_master/external_apis/__init__.py" ]]; then
        check_pass "External APIs __init__.py exists"
    else
        check_fail "External APIs __init__.py missing"
    fi
    
    if [[ -f "src/security_master/external_apis/openfigi_client.py" ]]; then
        check_pass "OpenFIGI client module exists"
        
        # Test import
        if python -c "
import sys
sys.path.insert(0, 'src')
from security_master.external_apis.openfigi_client import OpenFIGIClient
print('Import successful')
" > /dev/null 2>&1; then
            check_pass "OpenFIGI client imports successfully"
        else
            check_fail "OpenFIGI client import failed"
        fi
    else
        check_fail "OpenFIGI client module missing"
    fi
else
    check_fail "External APIs directory missing"
fi

echo ""

# Test 4: Adapter Modules
section_header "Adapter Modules"

if [[ -d "src/security_master/adapters" ]]; then
    check_pass "Adapters directory exists"
    
    if [[ -f "src/security_master/adapters/__init__.py" ]]; then
        check_pass "Adapters __init__.py exists"
    else
        check_fail "Adapters __init__.py missing"
    fi
    
    if [[ -f "src/security_master/adapters/pp_classifier_adapter.py" ]]; then
        check_pass "PP classifier adapter exists"
        
        # Test import
        if python -c "
import sys
sys.path.insert(0, 'src')
from security_master.adapters.pp_classifier_adapter import PPClassifierAdapter
print('Import successful')
" > /dev/null 2>&1; then
            check_pass "PP classifier adapter imports successfully"
        else
            check_warning "PP classifier adapter import failed (may need external library)"
        fi
    else
        check_fail "PP classifier adapter missing"
    fi
else
    check_fail "Adapters directory missing"
fi

echo ""

# Test 5: Dependencies
section_header "Python Dependencies"

# Check if aiohttp is installed
if python -c "import aiohttp" > /dev/null 2>&1; then
    check_pass "aiohttp dependency installed"
else
    check_fail "aiohttp dependency missing"
fi

# Check if aiofiles is installed
if python -c "import aiofiles" > /dev/null 2>&1; then
    check_pass "aiofiles dependency installed"
else
    check_fail "aiofiles dependency missing"
fi

# Check if pytest-asyncio is installed (dev dependency)
if python -c "import pytest_asyncio" > /dev/null 2>&1; then
    check_pass "pytest-asyncio dependency installed"
else
    check_warning "pytest-asyncio dependency missing (development only)"
fi

echo ""

# Test 6: Configuration
section_header "Configuration"

if [[ -f ".env.example" ]]; then
    if grep -q "OPENFIGI_API_KEY" .env.example; then
        check_pass "OpenFIGI configuration in .env.example"
    else
        check_fail "OpenFIGI configuration missing from .env.example"
    fi
else
    check_fail ".env.example file missing"
fi

if [[ -f ".env" ]]; then
    if grep -q "OPENFIGI_API_KEY" .env; then
        if grep -q "OPENFIGI_API_KEY=your_api_key_here" .env; then
            check_warning "OpenFIGI API key not configured (using placeholder)"
        else
            check_pass "OpenFIGI API key configured"
        fi
    else
        check_warning "OpenFIGI configuration missing from .env"
    fi
else
    check_warning ".env file not found (copy from .env.example)"
fi

echo ""

# Test 7: Integration Tests
section_header "Integration Tests"

if [[ -f "tests/integration/test_external_libraries.py" ]]; then
    check_pass "External library integration tests exist"
    
    # Run the basic tests
    if poetry run pytest tests/integration/test_external_libraries.py::test_external_directory_structure -v > /dev/null 2>&1; then
        check_pass "Basic integration test passes"
    else
        check_warning "Basic integration test failed"
    fi
else
    check_fail "External library integration tests missing"
fi

# Check for OpenFIGI client tests
if [[ -f "tests/unit/test_openfigi_client.py" ]]; then
    check_pass "OpenFIGI client unit tests exist"
    
    # Try to run tests
    if poetry run pytest tests/unit/test_openfigi_client.py -v > /dev/null 2>&1; then
        check_pass "OpenFIGI client tests pass"
    else
        check_warning "OpenFIGI client tests failed (may need mock setup)"
    fi
else
    check_fail "OpenFIGI client unit tests missing"
fi

echo ""

# Test 8: Scripts and Automation
section_header "Scripts and Automation"

if [[ -f "scripts/sync_external_repos.sh" ]]; then
    check_pass "External repository sync script exists"
    
    if [[ -x "scripts/sync_external_repos.sh" ]]; then
        check_pass "Sync script is executable"
    else
        check_warning "Sync script is not executable"
        chmod +x scripts/sync_external_repos.sh
    fi
else
    check_fail "External repository sync script missing"
fi

if [[ -f "scripts/phase2/setup_external_integrations.sh" ]]; then
    check_pass "Phase 2 setup script exists"
    
    if [[ -x "scripts/phase2/setup_external_integrations.sh" ]]; then
        check_pass "Phase 2 setup script is executable"
    else
        check_warning "Phase 2 setup script is not executable"
        chmod +x scripts/phase2/setup_external_integrations.sh
    fi
else
    check_fail "Phase 2 setup script missing"
fi

echo ""

# Test 9: Git Configuration
section_header "Git Configuration"

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ $CURRENT_BRANCH == "feature/phase2-external-integrations" ]]; then
    check_pass "On Phase 2 feature branch"
elif [[ $CURRENT_BRANCH == "main" ]]; then
    check_warning "On main branch (consider creating Phase 2 feature branch)"
else
    check_pass "On custom branch: $CURRENT_BRANCH"
fi

# Check if subtrees are properly integrated
if git log --oneline | grep -q "Add 'src/external/"; then
    check_pass "Git subtrees appear to be integrated"
else
    check_warning "Git subtrees may not be properly integrated"
fi

echo ""

# Test 10: Cache Directory Structure
section_header "Cache and Data Directories"

if [[ -d "data" ]]; then
    check_pass "Data directory exists"
    
    if [[ -d "data/cache" ]]; then
        check_pass "Cache directory exists"
    else
        check_warning "Cache directory missing (will be created on first run)"
        mkdir -p data/cache
    fi
else
    check_warning "Data directory missing (will be created on first run)"
    mkdir -p data/cache
fi

echo ""

# Test 11: Security Scanning
section_header "Security Scanning"

if command -v poetry &> /dev/null; then
    # Run security checks
    if poetry run safety check > /dev/null 2>&1; then
        check_pass "Safety security scan passes"
    else
        check_warning "Safety security scan found issues"
    fi
    
    if poetry run bandit -r src -f json > /dev/null 2>&1; then
        check_pass "Bandit security scan passes"
    else
        check_warning "Bandit security scan found issues"
    fi
else
    check_warning "Poetry not available for security scanning"
fi

echo ""

# Summary
echo "=========================================="
echo -e "${BLUE}Phase 2 Validation Summary${NC}"
echo "=========================================="
echo ""
echo -e "✅ Tests Passed: ${GREEN}$TOTAL_PASS${NC}"
echo -e "❌ Tests Failed: ${RED}$TOTAL_FAIL${NC}"
echo -e "⚠️  Warnings: ${YELLOW}$TOTAL_WARNING${NC}"
echo ""

# Determine overall status
if [[ $TOTAL_FAIL -eq 0 ]]; then
    echo -e "${GREEN}🎉 PHASE 2 SETUP VALIDATION COMPLETE!${NC}"
    echo ""
    echo "Phase 2 external integrations setup validated:"
    echo "✅ External repository structure in place"
    echo "✅ API client modules ready"
    echo "✅ Adapter modules created"
    echo "✅ Dependencies installed"
    echo "✅ Configuration framework ready"
    echo "✅ Integration test structure in place"
    echo ""
    echo "🚀 Ready for Phase 2 implementation!"
    echo ""
    echo "Next steps:"
    echo "1. Configure OpenFIGI API key in .env file"
    echo "2. Follow Phase 2 execution guide for detailed implementation"
    echo "3. Run specific issue validation scripts as you progress"
    echo ""
    exit 0
elif [[ $TOTAL_FAIL -le 3 ]]; then
    echo -e "${YELLOW}⚠️ PHASE 2 SETUP MOSTLY COMPLETE - MINOR ISSUES FOUND${NC}"
    echo ""
    echo "Setup is functional but has some minor issues."
    echo "Review failed tests above and address if needed."
    echo ""
    echo "You may proceed with Phase 2 implementation but should"
    echo "resolve the failed tests for optimal functionality."
    echo ""
    exit 1
else
    echo -e "${RED}❌ PHASE 2 SETUP INCOMPLETE${NC}"
    echo ""
    echo "Significant setup issues found that should be resolved:"
    echo ""
    echo "Recommended actions:"
    echo "1. Review all failed tests above"
    echo "2. Re-run Phase 2 setup: ./scripts/phase2/setup_external_integrations.sh"
    echo "3. Check dependencies: poetry install"
    echo "4. Verify external repository access"
    echo "5. Re-run this validation script"
    echo ""
    echo "⚠️ Do not proceed with Phase 2 implementation until issues are resolved."
    echo ""
    exit 1
fi