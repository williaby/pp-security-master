#!/bin/bash
# Validation script for Issue P0-002: Development Environment Standardization

set -e

echo "🔍 Validating P0-002: Development Environment Standardization"
echo "============================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
PASS=0
FAIL=0

check_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((FAIL++))
}

check_warning() {
    echo -e "${YELLOW}⚠️ WARNING:${NC} $1"
}

echo "Test 1: Python 3.11+ Installation"
echo "--------------------------------"

if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    if echo "$PYTHON_VERSION" | grep -q "3.11"; then
        check_pass "Python 3.11+ installed: $PYTHON_VERSION"
    else
        check_fail "Python 3.11+ not found. Current: $PYTHON_VERSION"
    fi
else
    check_fail "Python not found in PATH"
fi

# Check pyenv if available
if command -v pyenv &> /dev/null; then
    PYENV_VERSION=$(pyenv version)
    check_pass "pyenv available: $PYENV_VERSION"
else
    check_warning "pyenv not installed (optional)"
fi

echo ""

echo "Test 2: Poetry Configuration"
echo "---------------------------"

if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version)
    check_pass "Poetry installed: $POETRY_VERSION"
    
    # Check Poetry configuration
    if poetry config virtualenvs.in-project | grep -q "true"; then
        check_pass "Poetry configured with in-project virtual environments"
    else
        check_fail "Poetry not configured for in-project virtual environments"
    fi
    
    # Check if virtual environment exists
    if poetry env info --path &>/dev/null; then
        VENV_PATH=$(poetry env info --path)
        check_pass "Virtual environment exists at: $VENV_PATH"
        
        # Check if it's in the project directory
        if [[ "$VENV_PATH" == *"/.venv"* ]]; then
            check_pass "Virtual environment is in project directory"
        else
            check_warning "Virtual environment not in project directory"
        fi
    else
        check_fail "Virtual environment not created"
    fi
else
    check_fail "Poetry not installed"
fi

echo ""

echo "Test 3: VSCode Configuration"
echo "---------------------------"

if [[ -f ".vscode/settings.json" ]]; then
    check_pass "VSCode settings.json exists"
    
    # Check for Python interpreter path
    if grep -q "python.defaultInterpreterPath.*\.venv" .vscode/settings.json; then
        check_pass "Python interpreter path configured"
    else
        check_fail "Python interpreter path not configured correctly"
    fi
    
    # Check for format on save
    if grep -q "editor.formatOnSave.*true" .vscode/settings.json; then
        check_pass "Format on save enabled"
    else
        check_fail "Format on save not enabled"
    fi
else
    check_fail "VSCode settings.json not found"
fi

if [[ -f ".vscode/extensions.json" ]]; then
    check_pass "VSCode extensions.json exists"
    
    # Check for essential extensions
    ESSENTIAL_EXTENSIONS=("ms-python.python" "ms-python.black-formatter" "charliermarsh.ruff")
    for ext in "${ESSENTIAL_EXTENSIONS[@]}"; do
        if grep -q "$ext" .vscode/extensions.json; then
            check_pass "Extension recommended: $ext"
        else
            check_fail "Extension missing: $ext"
        fi
    done
else
    check_fail "VSCode extensions.json not found"
fi

echo ""

echo "Test 4: Environment Variables"
echo "----------------------------"

if [[ -f ".env.example" ]]; then
    check_pass ".env.example file exists"
    
    # Check for essential variables
    ESSENTIAL_VARS=("PP_ENVIRONMENT" "PP_DB_HOST" "PP_DB_USERNAME" "PP_DB_DATABASE")
    for var in "${ESSENTIAL_VARS[@]}"; do
        if grep -q "^$var=" .env.example; then
            check_pass "Environment variable defined: $var"
        else
            check_fail "Environment variable missing: $var"
        fi
    done
else
    check_fail ".env.example file not found"
fi

if [[ -f ".env" ]]; then
    check_pass ".env file exists"
    
    # Check if password is set (not the placeholder)
    if grep -q "PP_DB_PASSWORD=your_secure_password_here" .env; then
        check_warning "Database password still using placeholder - needs to be updated"
    else
        check_pass "Database password appears to be configured"
    fi
else
    check_fail ".env file not found"
fi

echo ""

echo "Test 5: Development Dependencies"
echo "-------------------------------"

if [[ -f "pyproject.toml" ]]; then
    check_pass "pyproject.toml exists"
    
    # Check for essential dependencies
    ESSENTIAL_DEPS=("python-dotenv" "psycopg2-binary" "sqlalchemy" "pydantic")
    for dep in "${ESSENTIAL_DEPS[@]}"; do
        if grep -q "$dep" pyproject.toml; then
            check_pass "Dependency found: $dep"
        else
            check_fail "Dependency missing: $dep"
        fi
    done
    
    # Check for development dependencies
    DEV_DEPS=("black" "ruff" "mypy" "pytest")
    for dep in "${DEV_DEPS[@]}"; do
        if grep -q "$dep" pyproject.toml; then
            check_pass "Dev dependency found: $dep"
        else
            check_fail "Dev dependency missing: $dep"
        fi
    done
else
    check_fail "pyproject.toml not found"
fi

echo ""

echo "Test 6: Virtual Environment Validation"
echo "-------------------------------------"

if poetry run python --version &>/dev/null; then
    VENV_PYTHON_VERSION=$(poetry run python --version)
    check_pass "Python accessible in virtual environment: $VENV_PYTHON_VERSION"
    
    # Test importing essential packages
    PACKAGES=("dotenv" "psycopg2" "sqlalchemy" "pydantic")
    for pkg in "${PACKAGES[@]}"; do
        if poetry run python -c "import $pkg" 2>/dev/null; then
            check_pass "Package importable: $pkg"
        else
            check_fail "Package not importable: $pkg"
        fi
    done
else
    check_fail "Cannot execute Python in virtual environment"
fi

echo ""

echo "Test 7: Development Tools Integration"
echo "-----------------------------------"

# Test Black
if poetry run black --version &>/dev/null; then
    BLACK_VERSION=$(poetry run black --version)
    check_pass "Black formatter available: $BLACK_VERSION"
else
    check_fail "Black formatter not available"
fi

# Test Ruff
if poetry run ruff --version &>/dev/null; then
    RUFF_VERSION=$(poetry run ruff --version)
    check_pass "Ruff linter available: $RUFF_VERSION"
else
    check_fail "Ruff linter not available"
fi

# Test MyPy
if poetry run mypy --version &>/dev/null; then
    MYPY_VERSION=$(poetry run mypy --version)
    check_pass "MyPy type checker available: $MYPY_VERSION"
else
    check_fail "MyPy type checker not available"
fi

# Test Pytest
if poetry run pytest --version &>/dev/null; then
    PYTEST_VERSION=$(poetry run pytest --version)
    check_pass "Pytest testing framework available: $PYTEST_VERSION"
else
    check_fail "Pytest testing framework not available"
fi

echo ""

echo "Test 8: Git Configuration"
echo "------------------------"

if [[ -f ".gitignore" ]]; then
    check_pass ".gitignore file exists"
    
    # Check for essential patterns
    GITIGNORE_PATTERNS=("__pycache__" ".env" ".venv" "*.pyc")
    for pattern in "${GITIGNORE_PATTERNS[@]}"; do
        if grep -q "$pattern" .gitignore; then
            check_pass "Gitignore pattern found: $pattern"
        else
            check_fail "Gitignore pattern missing: $pattern"
        fi
    done
else
    check_fail ".gitignore file not found"
fi

if [[ -f ".editorconfig" ]]; then
    check_pass ".editorconfig file exists"
    
    # Check for Python configuration
    if grep -q "\[*.{py,pyi}\]" .editorconfig; then
        check_pass "Python configuration found in .editorconfig"
    else
        check_fail "Python configuration missing in .editorconfig"
    fi
else
    check_fail ".editorconfig file not found"
fi

echo ""

# Summary
echo "=========================================="
echo "P0-002 Validation Summary"
echo "=========================================="
echo "Tests Passed: $PASS"
echo "Tests Failed: $FAIL"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}🎉 All tests passed! P0-002 requirements met.${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAIL test(s) failed. Please address the issues above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Run './scripts/setup_environment.sh' to set up the environment"
    echo "2. Edit .env file and add your PostgreSQL password"
    echo "3. Run 'poetry install' to install dependencies"
    echo "4. Configure Poetry: 'poetry config virtualenvs.in-project true'"
    exit 1
fi