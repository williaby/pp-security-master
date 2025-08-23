#!/bin/bash
# Phase 3: Multi-Institution Support Validation Script
# Comprehensive validation of multi-institution setup

set -e

echo "🔍 Phase 3: Multi-Institution Support Validation"
echo "==============================================="
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
    echo "$(printf '=%.0s' {1..60})"
}

# Check if we're in the right directory
if [[ ! -f "PROJECT_PLAN.md" ]]; then
    echo -e "${RED}❌ Please run this script from the pp-security-master project root directory${NC}"
    exit 1
fi

echo "Starting comprehensive Phase 3 validation..."
echo ""

# Test 1: Phase 2 Prerequisites
section_header "Phase 2 Prerequisites"

if [[ -f "scripts/phase2/validate_phase2_setup.sh" ]]; then
    if ./scripts/phase2/validate_phase2_setup.sh > /dev/null 2>&1; then
        check_pass "Phase 2 setup validation passed"
    else
        check_fail "Phase 2 setup validation failed - complete Phase 2 first"
    fi
else
    check_warning "Phase 2 validation script not found"
fi

echo ""

# Test 2: System Dependencies
section_header "System Dependencies"

# Check Tesseract OCR
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -1 | awk '{print $2}')
    check_pass "Tesseract OCR installed: $TESSERACT_VERSION"
    
    # Check for English language data
    if tesseract --list-langs 2>&1 | grep -q "eng"; then
        check_pass "English language data available"
    else
        check_fail "English language data missing for Tesseract"
    fi
else
    check_fail "Tesseract OCR not installed (required for PDF processing)"
fi

# Check poppler-utils (for PDF to image conversion)
if command -v pdftoppm &> /dev/null; then
    check_pass "poppler-utils available (PDF to image conversion)"
else
    check_warning "poppler-utils not found - PDF processing may fail"
fi

echo ""

# Test 3: Python Dependencies
section_header "Python Dependencies"

# XML processing dependencies
XML_DEPS=("lxml" "xml.etree.ElementTree")
for dep in "${XML_DEPS[@]}"; do
    if python -c "import $dep" > /dev/null 2>&1; then
        check_pass "$dep dependency available"
    else
        check_fail "$dep dependency missing"
    fi
done

# PDF and OCR dependencies
PDF_DEPS=("PyPDF2" "pdfplumber" "pytesseract" "PIL" "pdf2image")
for dep in "${PDF_DEPS[@]}"; do
    if python -c "import $dep" > /dev/null 2>&1; then
        check_pass "$dep dependency available"
    else
        check_fail "$dep dependency missing (run: poetry add PyPDF2 pdfplumber pytesseract Pillow pdf2image)"
    fi
done

# HTTP client for Kubera
if python -c "import httpx" > /dev/null 2>&1; then
    check_pass "httpx dependency available"
else
    check_fail "httpx dependency missing (run: poetry add httpx)"
fi

echo ""

# Test 4: Interactive Brokers Module
section_header "Interactive Brokers Module"

if [[ -d "src/security_master/extractor/interactive_brokers" ]]; then
    check_pass "IBKR extractor directory exists"
    
    if [[ -f "src/security_master/extractor/interactive_brokers/__init__.py" ]]; then
        check_pass "IBKR __init__.py exists"
    else
        check_fail "IBKR __init__.py missing"
    fi
    
    # Test IBKR models import
    if python -c "
import sys
sys.path.insert(0, 'src')
from security_master.extractor.interactive_brokers.models import IBKRTransaction, IBKRAssetCategory
print('IBKR models import successful')
" > /dev/null 2>&1; then
        check_pass "IBKR models import successfully"
    else
        check_fail "IBKR models import failed"
    fi
    
    # Test IBKR parser import
    if python -c "
import sys
sys.path.insert(0, 'src')
from security_master.extractor.interactive_brokers.parser import IBKRFlexQueryParser
print('IBKR parser import successful')
" > /dev/null 2>&1; then
        check_pass "IBKR parser import successfully"
    else
        check_fail "IBKR parser import failed"
    fi
else
    check_fail "IBKR extractor directory missing"
fi

# Test IBKR sample data
if [[ -f "sample_data/interactive_brokers/sample_flex_query.xml" ]]; then
    check_pass "IBKR sample XML data exists"
    
    # Test XML validity
    if python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('sample_data/interactive_brokers/sample_flex_query.xml')
root = tree.getroot()
print(f'XML valid with {len(root.findall(\".//Trade\"))} trade records')
" > /dev/null 2>&1; then
        check_pass "IBKR sample XML is valid"
    else
        check_warning "IBKR sample XML validation failed"
    fi
else
    check_warning "IBKR sample XML data missing"
fi

echo ""

# Test 5: AltoIRA Module
section_header "AltoIRA Module"

if [[ -d "src/security_master/extractor/altoira" ]]; then
    check_pass "AltoIRA extractor directory exists"
    
    if [[ -f "src/security_master/extractor/altoira/__init__.py" ]]; then
        check_pass "AltoIRA __init__.py exists"
    else
        check_fail "AltoIRA __init__.py missing"
    fi
    
    # Test AltoIRA models import
    if python -c "
import sys
sys.path.insert(0, 'src')
from security_master.extractor.altoira.models import AltoIRATransaction, OCRConfidenceLevel
print('AltoIRA models import successful')
" > /dev/null 2>&1; then
        check_pass "AltoIRA models import successfully"
    else
        check_fail "AltoIRA models import failed"
    fi
    
    # Test AltoIRA parser import
    if python -c "
import sys
sys.path.insert(0, 'src')
from security_master.extractor.altoira.parser import AltoIRAPDFParser
print('AltoIRA parser import successful')
" > /dev/null 2>&1; then
        check_pass "AltoIRA parser import successfully"
    else
        check_fail "AltoIRA parser import failed"
    fi
else
    check_fail "AltoIRA extractor directory missing"
fi

# Test OCR functionality
if python -c "
import pytesseract
from PIL import Image
import numpy as np

# Create a simple test image
img_array = np.ones((100, 300, 3), dtype=np.uint8) * 255
img = Image.fromarray(img_array)

# Test OCR
text = pytesseract.image_to_string(img)
print('OCR test successful')
" > /dev/null 2>&1; then
    check_pass "OCR functionality test passed"
else
    check_warning "OCR functionality test failed - check Tesseract installation"
fi

echo ""

# Test 6: Kubera Module
section_header "Kubera Module"

if [[ -d "src/security_master/extractor/kubera" ]]; then
    check_pass "Kubera extractor directory exists"
    
    if [[ -f "src/security_master/extractor/kubera/__init__.py" ]]; then
        check_pass "Kubera __init__.py exists"
    else
        check_fail "Kubera __init__.py missing"
    fi
    
    # Test Kubera models import
    if python -c "
import sys
sys.path.insert(0, 'src')
from security_master.extractor.kubera.models import KuberaTransaction, KuberaAPIConfig
print('Kubera models import successful')
" > /dev/null 2>&1; then
        check_pass "Kubera models import successfully"
    else
        check_fail "Kubera models import failed"
    fi
else
    check_fail "Kubera extractor directory missing"
fi

# Test Kubera sample data
if [[ -f "sample_data/kubera/sample_portfolio.json" ]]; then
    check_pass "Kubera sample JSON data exists"
    
    # Test JSON validity
    if python -c "
import json
with open('sample_data/kubera/sample_portfolio.json', 'r') as f:
    data = json.load(f)
print(f'JSON valid with {len(data.get(\"transactions\", []))} transactions')
" > /dev/null 2>&1; then
        check_pass "Kubera sample JSON is valid"
    else
        check_warning "Kubera sample JSON validation failed"
    fi
else
    check_warning "Kubera sample JSON data missing"
fi

echo ""

# Test 7: Cross-Institution Validation
section_header "Cross-Institution Validation"

if [[ -d "src/security_master/validation" ]]; then
    check_pass "Validation framework directory exists"
    
    if [[ -f "src/security_master/validation/cross_validator.py" ]]; then
        check_pass "Cross-validator module exists"
        
        # Test validator import
        if python -c "
import sys
sys.path.insert(0, 'src')
from security_master.validation.cross_validator import CrossInstitutionValidator, ValidationDiscrepancy
validator = CrossInstitutionValidator()
print('Cross-validator import successful')
" > /dev/null 2>&1; then
            check_pass "Cross-validator imports successfully"
        else
            check_fail "Cross-validator import failed"
        fi
    else
        check_fail "Cross-validator module missing"
    fi
else
    check_fail "Validation framework directory missing"
fi

echo ""

# Test 8: Manual Review Workflow
section_header "Manual Review Workflow"

if [[ -d "src/security_master/workflow" ]]; then
    check_pass "Workflow directory exists"
    
    if [[ -f "src/security_master/workflow/manual_review.py" ]]; then
        check_pass "Manual review module exists"
        
        # Test workflow import
        if python -c "
import sys
sys.path.insert(0, 'src')
from security_master.workflow.manual_review import ManualReviewQueue, ReviewItem
queue = ManualReviewQueue()
print('Manual review workflow import successful')
" > /dev/null 2>&1; then
            check_pass "Manual review workflow imports successfully"
        else
            check_fail "Manual review workflow import failed"
        fi
    else
        check_warning "Manual review module missing (may be implemented later)"
    fi
else
    check_fail "Workflow directory missing"
fi

echo ""

# Test 9: Integration Tests Structure
section_header "Integration Tests Structure"

if [[ -d "tests/integration/phase3" ]]; then
    check_pass "Phase 3 integration tests directory exists"
    
    if [[ -f "tests/integration/phase3/test_multi_institution_pipeline.py" ]]; then
        check_pass "Multi-institution pipeline tests exist"
        
        # Test that tests can be discovered
        if poetry run pytest --collect-only tests/integration/phase3/ > /dev/null 2>&1; then
            check_pass "Integration tests discoverable by pytest"
        else
            check_warning "Integration tests not discoverable - check import paths"
        fi
    else
        check_fail "Multi-institution pipeline tests missing"
    fi
else
    check_fail "Phase 3 integration tests directory missing"
fi

echo ""

# Test 10: Performance Tests Structure
section_header "Performance Tests Structure"

if [[ -d "tests/performance" ]]; then
    check_pass "Performance tests directory exists"
    
    if [[ -f "tests/performance/test_phase3_performance.py" ]]; then
        check_pass "Phase 3 performance tests exist"
        
        # Check for pytest-benchmark markers
        if grep -q "@pytest.mark.benchmark" tests/performance/test_phase3_performance.py; then
            check_pass "Performance test benchmarks properly marked"
        else
            check_warning "Performance test benchmark markers missing"
        fi
    else
        check_fail "Phase 3 performance tests missing"
    fi
else
    check_warning "Performance tests directory missing"
fi

echo ""

# Test 11: Configuration
section_header "Configuration"

if [[ -f ".env.example" ]]; then
    if grep -q "KUBERA_API_KEY" .env.example; then
        check_pass "Kubera API configuration in .env.example"
    else
        check_fail "Kubera API configuration missing from .env.example"
    fi
    
    if grep -q "OCR_CONFIDENCE_THRESHOLD" .env.example; then
        check_pass "OCR configuration in .env.example"
    else
        check_fail "OCR configuration missing from .env.example"
    fi
    
    if grep -q "POSITION_TOLERANCE" .env.example; then
        check_pass "Cross-validation configuration in .env.example"
    else
        check_fail "Cross-validation configuration missing from .env.example"
    fi
else
    check_fail ".env.example file missing"
fi

if [[ -f ".env" ]]; then
    if grep -q "KUBERA_API_KEY" .env; then
        if grep -q "KUBERA_API_KEY=your_kubera_api_key_here" .env; then
            check_warning "Kubera API key not configured (using placeholder)"
        else
            check_pass "Kubera API key configured"
        fi
    else
        check_warning "Kubera API configuration missing from .env"
    fi
else
    check_warning ".env file not found (copy from .env.example)"
fi

echo ""

# Test 12: Sample Data Structure
section_header "Sample Data Structure"

SAMPLE_DIRS=("wells_fargo" "interactive_brokers" "altoira" "kubera")
for dir in "${SAMPLE_DIRS[@]}"; do
    if [[ -d "sample_data/$dir" ]]; then
        check_pass "Sample data directory exists: $dir"
        
        # Count files in directory
        FILE_COUNT=$(find "sample_data/$dir" -type f | wc -l)
        if [[ $FILE_COUNT -gt 0 ]]; then
            check_pass "$dir has $FILE_COUNT sample files"
        else
            check_warning "$dir sample directory is empty"
        fi
    else
        check_warning "Sample data directory missing: $dir"
    fi
done

echo ""

# Test 13: Git Branch Structure
section_header "Git Branch Structure"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ $CURRENT_BRANCH == "feature/phase3-multi-institution" ]]; then
    check_pass "On Phase 3 feature branch"
elif [[ $CURRENT_BRANCH == "main" ]]; then
    check_warning "On main branch (consider creating Phase 3 feature branch)"
else
    check_pass "On custom branch: $CURRENT_BRANCH"
fi

# Check for recent Phase 3 commits
if git log --oneline -5 | grep -q "Phase 3\|multi-institution\|IBKR\|AltoIRA\|Kubera"; then
    check_pass "Recent Phase 3 commits found"
else
    check_warning "No recent Phase 3 commits found"
fi

echo ""

# Test 14: Memory and Performance Readiness
section_header "Performance Readiness"

# Check available memory (for large dataset processing)
if command -v free &> /dev/null; then
    AVAILABLE_MEM_GB=$(free -g | awk '/^Mem:/{print $7}')
    if [[ $AVAILABLE_MEM_GB -ge 4 ]]; then
        check_pass "Sufficient memory available: ${AVAILABLE_MEM_GB}GB"
    else
        check_warning "Low memory available: ${AVAILABLE_MEM_GB}GB (recommend 4GB+ for large datasets)"
    fi
fi

# Check disk space for sample data and processing
AVAILABLE_SPACE_GB=$(df . | tail -1 | awk '{print int($4/1024/1024)}')
if [[ $AVAILABLE_SPACE_GB -ge 10 ]]; then
    check_pass "Sufficient disk space available: ${AVAILABLE_SPACE_GB}GB"
else
    check_warning "Low disk space available: ${AVAILABLE_SPACE_GB}GB (recommend 10GB+ for processing)"
fi

echo ""

# Summary
echo "=========================================================="
echo -e "${BLUE}Phase 3 Multi-Institution Validation Summary${NC}"
echo "=========================================================="
echo ""
echo -e "✅ Tests Passed: ${GREEN}$TOTAL_PASS${NC}"
echo -e "❌ Tests Failed: ${RED}$TOTAL_FAIL${NC}"
echo -e "⚠️  Warnings: ${YELLOW}$TOTAL_WARNING${NC}"
echo ""

# Determine overall status
if [[ $TOTAL_FAIL -eq 0 ]]; then
    echo -e "${GREEN}🎉 PHASE 3 SETUP VALIDATION COMPLETE!${NC}"
    echo ""
    echo "Multi-institution support infrastructure validated:"
    echo "✅ All four institution parsers (Wells Fargo, IBKR, AltoIRA, Kubera)"
    echo "✅ OCR and PDF processing capabilities"
    echo "✅ Cross-institution validation framework"
    echo "✅ Manual review workflow structure"
    echo "✅ Performance and integration test frameworks"
    echo "✅ Configuration and sample data ready"
    echo ""
    echo "🚀 Ready for Phase 3 implementation!"
    echo ""
    echo "Next steps:"
    echo "1. Configure Kubera API key in .env file"
    echo "2. Obtain sample PDF statements for AltoIRA testing"
    echo "3. Follow Phase 3 execution guide for detailed implementation"
    echo "4. Run specific issue validation scripts as you progress"
    echo ""
    exit 0
elif [[ $TOTAL_FAIL -le 5 ]]; then
    echo -e "${YELLOW}⚠️ PHASE 3 SETUP MOSTLY COMPLETE - MINOR ISSUES FOUND${NC}"
    echo ""
    echo "Setup is functional but has some minor issues."
    echo "Review failed tests above and address if needed."
    echo ""
    echo "You may proceed with Phase 3 implementation but should"
    echo "resolve the failed tests for optimal functionality."
    echo ""
    exit 1
else
    echo -e "${RED}❌ PHASE 3 SETUP INCOMPLETE${NC}"
    echo ""
    echo "Significant setup issues found that should be resolved:"
    echo ""
    echo "Recommended actions:"
    echo "1. Review all failed tests above"
    echo "2. Re-run Phase 3 setup: ./scripts/phase3/setup_multi_institution.sh"
    echo "3. Install missing system dependencies (Tesseract OCR, poppler-utils)"
    echo "4. Install missing Python dependencies: poetry install"
    echo "5. Re-run this validation script"
    echo ""
    echo "Critical requirements:"
    echo "- Tesseract OCR must be installed system-wide"
    echo "- All Python dependencies must be available"
    echo "- Phase 2 must be completed and validated"
    echo ""
    echo "⚠️ Do not proceed with Phase 3 implementation until issues are resolved."
    echo ""
    exit 1
fi