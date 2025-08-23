#!/bin/bash
# Phase 0 Development Environment Setup Script
# This script automates the development environment setup process

set -e  # Exit on any error

echo "🚀 Phase 0 Development Environment Setup"
echo "========================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "PROJECT_PLAN.md" ]]; then
    print_error "Please run this script from the pp-security-master project root directory"
    exit 1
fi

print_info "Setting up development environment for Portfolio Performance Security Master..."
echo ""

# Step 1: Check Prerequisites
echo "Step 1: Checking Prerequisites"
echo "-----------------------------"

# Check if Python 3.11 is available
if command -v python3.11 &> /dev/null; then
    print_status "Python 3.11 found"
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null && python3 --version | grep -q "3.11"; then
    print_status "Python 3.11 found as python3"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null && python --version | grep -q "3.11"; then
    print_status "Python 3.11 found as python"
    PYTHON_CMD="python"
else
    print_warning "Python 3.11 not found. Attempting to install via pyenv..."
    
    # Check if pyenv is installed
    if ! command -v pyenv &> /dev/null; then
        print_info "Installing pyenv..."
        curl https://pyenv.run | bash
        
        # Add pyenv to PATH for this session
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
        
        print_status "pyenv installed"
    fi
    
    # Install Python 3.11.8
    print_info "Installing Python 3.11.8..."
    pyenv install 3.11.8
    pyenv global 3.11.8
    PYTHON_CMD="python"
    print_status "Python 3.11.8 installed via pyenv"
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    print_info "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | $PYTHON_CMD -
    
    # Add Poetry to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"
    
    print_status "Poetry installed"
else
    print_status "Poetry found"
fi

# Configure Poetry
print_info "Configuring Poetry..."
poetry config virtualenvs.in-project true
poetry config virtualenvs.prefer-active-python true
print_status "Poetry configured"

echo ""

# Step 2: Set up Project Environment
echo "Step 2: Setting up Project Environment"
echo "-------------------------------------"

# Check if pyproject.toml exists, if not create basic one
if [[ ! -f "pyproject.toml" ]]; then
    print_info "Creating pyproject.toml..."
    poetry init --no-interaction --name pp-security-master --python "^3.11"
    print_status "pyproject.toml created"
fi

# Add essential dependencies
print_info "Adding dependencies..."
poetry add python-dotenv psycopg2-binary sqlalchemy pydantic alembic
poetry add --group dev black ruff mypy pytest pytest-cov pre-commit
print_status "Dependencies added"

# Install dependencies and create virtual environment
print_info "Installing dependencies and creating virtual environment..."
poetry install
print_status "Virtual environment created and dependencies installed"

echo ""

# Step 3: Create Directory Structure
echo "Step 3: Creating Directory Structure"
echo "-----------------------------------"

# Create all necessary directories
directories=(
    "src/security_master/extractor"
    "src/security_master/classifier"
    "src/security_master/storage"
    "src/security_master/patch"
    "src/security_master/config"
    "src/security_master/database"
    "src/security_master/validation"
    "tests/unit"
    "tests/integration"
    "tests/performance"
    "tests/fixtures"
    "docs/adr"
    "docs/planning"
    "docs/api"
    "sql/versions"
    "schema_exports"
    "sample_data/wells_fargo"
    "sample_data/ibkr"
    "sample_data/altoira"
    "sample_data/kubera"
    "scripts"
    "pytest_plugins"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
done

# Create __init__.py files
init_files=(
    "src/__init__.py"
    "src/security_master/__init__.py"
    "src/security_master/extractor/__init__.py"
    "src/security_master/classifier/__init__.py"
    "src/security_master/storage/__init__.py"
    "src/security_master/patch/__init__.py"
    "src/security_master/config/__init__.py"
    "src/security_master/database/__init__.py"
    "src/security_master/validation/__init__.py"
    "tests/__init__.py"
    "pytest_plugins/__init__.py"
)

for file in "${init_files[@]}"; do
    touch "$file"
done

print_status "Directory structure created"

echo ""

# Step 4: Create Configuration Files
echo "Step 4: Creating Configuration Files"
echo "-----------------------------------"

# Create .vscode directory and settings
mkdir -p .vscode

# VSCode settings
cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": false,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": ["tests"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".mypy_cache": true,
        ".pytest_cache": true,
        "htmlcov": true
    }
}
EOF

# VSCode extensions
cat > .vscode/extensions.json << 'EOF'
{
    "recommendations": [
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.mypy-type-checker",
        "charliermarsh.ruff",
        "ms-python.isort",
        "ms-toolsai.jupyter",
        "redhat.vscode-yaml",
        "ms-vscode.makefile-tools",
        "ms-vscode-remote.remote-ssh"
    ]
}
EOF

print_status "VSCode configuration created"

# Create .gitignore
cat > .gitignore << 'EOF'
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/
.nox/

# Database
*.db
*.sqlite3

# Logs
*.log
logs/

# Data files
data/
*.csv
*.json
*.xml
*.pdf

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
schema_exports/*.svg
schema_exports/*.png
temp/
.env.local
.env.production
EOF

print_status ".gitignore created"

# Create .editorconfig
cat > .editorconfig << 'EOF'
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{py,pyi}]
indent_style = space
indent_size = 4
max_line_length = 88

[*.{yml,yaml}]
indent_style = space
indent_size = 2

[*.{md,rst}]
indent_style = space
indent_size = 2
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
EOF

print_status ".editorconfig created"

echo ""

# Step 5: Environment Variables
echo "Step 5: Setting up Environment Variables"
echo "---------------------------------------"

# Create .env.example with working PostgreSQL values
cat > .env.example << 'EOF'
# Portfolio Performance Security Master Configuration

# Environment Settings
PP_ENVIRONMENT=development
PP_DEBUG=true
PP_LOG_LEVEL=DEBUG

# Database Configuration (verified working with Unraid PostgreSQL)
PP_DB_HOST=unraid.lan
PP_DB_PORT=5432
PP_DB_USERNAME=pp_user
PP_DB_PASSWORD=your_secure_password_here
PP_DB_DATABASE=pp_master

# Database Pool Configuration
PP_DB_POOL_SIZE=10
PP_DB_MAX_OVERFLOW=20
PP_DB_POOL_TIMEOUT=30

# External Service Configuration (for future use)
PP_OPENFIGI_API_KEY=your_openfigi_api_key_here
PP_OPENFIGI_BASE_URL=https://api.openfigi.com/v3
PP_OPENFIGI_TIMEOUT=30
PP_OPENFIGI_RETRY_ATTEMPTS=3
PP_OPENFIGI_RPM=25
PP_OPENFIGI_RPD=10000

# Application Configuration
PP_DATA_QUALITY_MIN_SCORE=0.7
PP_CLASSIFICATION_CONFIDENCE_THRESHOLD=0.8
EOF

# Copy to .env if it doesn't exist
if [[ ! -f ".env" ]]; then
    cp .env.example .env
    print_warning "Created .env file - please edit and add your PostgreSQL password"
else
    print_info ".env file already exists, skipping"
fi

print_status "Environment configuration created"

echo ""

# Step 6: Test Configuration
echo "Step 6: Testing Configuration"
echo "-----------------------------"

# Test virtual environment
if poetry env info --path &>/dev/null; then
    print_status "Virtual environment accessible"
else
    print_error "Virtual environment not accessible"
    exit 1
fi

# Test Python in virtual environment
if poetry run python --version | grep -q "3.11"; then
    print_status "Python 3.11 available in virtual environment"
else
    print_error "Python 3.11 not available in virtual environment"
    exit 1
fi

# Test dependencies
if poetry run python -c "import dotenv, psycopg2, sqlalchemy, pydantic" 2>/dev/null; then
    print_status "Core dependencies installed correctly"
else
    print_error "Core dependencies not installed correctly"
    exit 1
fi

echo ""

# Final Summary
echo "🎉 Phase 0 Development Environment Setup Complete!"
echo "================================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your PostgreSQL password"
echo "2. Test database connection: poetry run python scripts/test_database.py"
echo "3. Run validation script: ./scripts/validate_phase_0.sh"
echo ""
echo "To activate the virtual environment:"
echo "  poetry shell"
echo ""
echo "To run commands in the virtual environment:"
echo "  poetry run <command>"
echo ""
print_status "Development environment ready for Phase 0 development!"