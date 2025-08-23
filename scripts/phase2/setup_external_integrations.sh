#!/bin/bash
# Phase 2: External Integrations Setup Script
# Automates external repository integration and API client setup

set -e

echo "🚀 Phase 2: External Integrations Setup"
echo "======================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ORG_NAME="your-org"  # Replace with actual organization name
PHASE2_BRANCH="feature/phase2-external-integrations"

log_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is required but not installed"
        echo "Install with: sudo apt install gh"
        exit 1
    fi
    
    if ! command -v poetry &> /dev/null; then
        log_error "Poetry is required but not installed"
        exit 1
    fi
    
    # Check if authenticated with GitHub
    if ! gh auth status &> /dev/null; then
        log_error "Please authenticate with GitHub CLI: gh auth login"
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

create_phase2_branch() {
    log_info "Creating Phase 2 feature branch..."
    
    # Ensure we're on main branch
    git checkout main
    git pull origin main
    
    # Create new branch for Phase 2
    if git show-ref --verify --quiet refs/heads/$PHASE2_BRANCH; then
        log_warning "Branch $PHASE2_BRANCH already exists, switching to it"
        git checkout $PHASE2_BRANCH
    else
        git checkout -b $PHASE2_BRANCH
        log_success "Created branch: $PHASE2_BRANCH"
    fi
}

setup_external_repositories() {
    log_info "Setting up external repository integration..."
    
    # Create temporary directory for cloning
    TEMP_DIR=$(mktemp -d)
    cd $TEMP_DIR
    
    log_info "Forking pp-portfolio-classifier..."
    if gh repo view $ORG_NAME/pp-portfolio-classifier &> /dev/null; then
        log_warning "Repository $ORG_NAME/pp-portfolio-classifier already exists"
    else
        gh repo fork fizban99/pp-portfolio-classifier --org $ORG_NAME --clone
        cd pp-portfolio-classifier
        
        # Enable branch protection
        log_info "Setting up branch protection for pp-portfolio-classifier..."
        gh api repos/$ORG_NAME/pp-portfolio-classifier/branches/main/protection \
          --method PUT \
          --field required_status_checks='{}' \
          --field enforce_admins=true \
          --field required_pull_request_reviews='{"required_approving_review_count":1}' \
          2>/dev/null || log_warning "Branch protection setup failed (may need admin rights)"
        
        cd ..
    fi
    
    log_info "Forking ppxml2db..."
    if gh repo view $ORG_NAME/ppxml2db &> /dev/null; then
        log_warning "Repository $ORG_NAME/ppxml2db already exists"
    else
        gh repo fork pfalcon/ppxml2db --org $ORG_NAME --clone
        cd ppxml2db
        
        # Enable branch protection
        log_info "Setting up branch protection for ppxml2db..."
        gh api repos/$ORG_NAME/ppxml2db/branches/main/protection \
          --method PUT \
          --field required_status_checks='{}' \
          --field enforce_admins=true \
          --field required_pull_request_reviews='{"required_approving_review_count":1}' \
          2>/dev/null || log_warning "Branch protection setup failed (may need admin rights)"
        
        cd ..
    fi
    
    # Return to project directory
    cd - > /dev/null
    
    # Clean up temp directory
    rm -rf $TEMP_DIR
    
    log_success "External repository forks created"
}

integrate_subtrees() {
    log_info "Integrating external repositories as git subtrees..."
    
    # Create external directory structure
    mkdir -p src/external
    
    # Add pp-portfolio-classifier as subtree
    if [ ! -d "src/external/pp-portfolio-classifier" ]; then
        log_info "Adding pp-portfolio-classifier subtree..."
        git subtree add --prefix=src/external/pp-portfolio-classifier \
          https://github.com/$ORG_NAME/pp-portfolio-classifier.git main --squash
        log_success "pp-portfolio-classifier subtree added"
    else
        log_warning "pp-portfolio-classifier subtree already exists"
    fi
    
    # Add ppxml2db as subtree  
    if [ ! -d "src/external/ppxml2db" ]; then
        log_info "Adding ppxml2db subtree..."
        git subtree add --prefix=src/external/ppxml2db \
          https://github.com/$ORG_NAME/ppxml2db.git main --squash
        log_success "ppxml2db subtree added"
    else
        log_warning "ppxml2db subtree already exists"
    fi
}

create_sync_script() {
    log_info "Creating external repository sync script..."
    
    cat > scripts/sync_external_repos.sh << 'EOF'
#!/bin/bash
# Sync external repository subtrees with upstream

set -e

echo "🔄 Syncing external repositories..."

ORG_NAME="your-org"  # Replace with actual organization name

# Sync pp-portfolio-classifier
echo "Syncing pp-portfolio-classifier..."
git subtree pull --prefix=src/external/pp-portfolio-classifier \
  https://github.com/$ORG_NAME/pp-portfolio-classifier.git main --squash

# Sync ppxml2db  
echo "Syncing ppxml2db..."
git subtree pull --prefix=src/external/ppxml2db \
  https://github.com/$ORG_NAME/ppxml2db.git main --squash

echo "✅ External repositories synced successfully"
EOF
    
    chmod +x scripts/sync_external_repos.sh
    log_success "Sync script created: scripts/sync_external_repos.sh"
}

setup_external_apis() {
    log_info "Setting up external API clients..."
    
    # Create external APIs directory
    mkdir -p src/security_master/external_apis
    
    # Create __init__.py
    cat > src/security_master/external_apis/__init__.py << 'EOF'
"""External API client modules."""
EOF
    
    log_success "External APIs directory structure created"
}

install_dependencies() {
    log_info "Installing Python dependencies for Phase 2..."
    
    # Add external API dependencies
    poetry add aiohttp aiofiles
    
    # Add development dependencies for testing
    poetry add --group dev pytest-asyncio
    
    log_success "Dependencies installed"
}

create_adapter_modules() {
    log_info "Creating adapter modules for external libraries..."
    
    # Create adapters directory
    mkdir -p src/security_master/adapters
    
    # Create __init__.py
    cat > src/security_master/adapters/__init__.py << 'EOF'
"""Adapter modules for external library integration."""
EOF
    
    log_success "Adapter modules structure created"
}

setup_configuration() {
    log_info "Setting up Phase 2 configuration..."
    
    # Add OpenFIGI configuration to .env.example
    if ! grep -q "OPENFIGI_API_KEY" .env.example; then
        cat >> .env.example << 'EOF'

# OpenFIGI API Configuration
OPENFIGI_API_KEY=your_api_key_here
EOF
        log_success "OpenFIGI configuration added to .env.example"
    else
        log_warning "OpenFIGI configuration already exists in .env.example"
    fi
}

create_integration_tests() {
    log_info "Creating integration test structure..."
    
    # Create integration test directory if not exists
    mkdir -p tests/integration
    
    # Create basic integration test file
    cat > tests/integration/test_external_libraries.py << 'EOF'
"""Integration tests for external library functionality."""
import pytest
import sys
from pathlib import Path

# Add external libraries to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "external"))

def test_external_directory_structure():
    """Test that external library directories exist."""
    external_path = Path(__file__).parent.parent.parent / "src" / "external"
    
    assert external_path.exists(), "External directory should exist"
    
    pp_classifier_path = external_path / "pp-portfolio-classifier"
    ppxml2db_path = external_path / "ppxml2db"
    
    # These may not exist if subtrees haven't been integrated yet
    if pp_classifier_path.exists():
        assert pp_classifier_path.is_dir(), "pp-portfolio-classifier should be a directory"
    
    if ppxml2db_path.exists():
        assert ppxml2db_path.is_dir(), "ppxml2db should be a directory"

@pytest.mark.skip(reason="Requires external libraries to be integrated")
def test_pp_portfolio_classifier_import():
    """Test that pp-portfolio-classifier can be imported."""
    try:
        # Test basic import - adjust import path based on actual structure
        import pp_portfolio_classifier
        assert pp_portfolio_classifier is not None
    except ImportError as e:
        pytest.skip(f"pp-portfolio-classifier not available: {e}")

@pytest.mark.skip(reason="Requires external libraries to be integrated")  
def test_ppxml2db_import():
    """Test that ppxml2db can be imported."""
    try:
        # Test basic import - adjust import path based on actual structure  
        import ppxml2db
        assert ppxml2db is not None
    except ImportError as e:
        pytest.skip(f"ppxml2db not available: {e}")
EOF
    
    log_success "Integration test structure created"
}

commit_changes() {
    log_info "Committing Phase 2 setup changes..."
    
    # Add all changes
    git add .
    
    # Check if there are changes to commit
    if git diff --staged --quiet; then
        log_warning "No changes to commit"
        return
    fi
    
    # Commit changes
    git commit -m "Phase 2: Setup external integrations infrastructure

🔧 Setup external repository integration:
- Created external API client structure
- Added adapter modules for external libraries  
- Created integration test framework
- Added configuration for OpenFIGI API
- Created sync script for external repositories

🤖 Generated with Claude Code (https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    log_success "Changes committed to $PHASE2_BRANCH"
}

main() {
    # Check if we're in the right directory
    if [[ ! -f "PROJECT_PLAN.md" ]]; then
        log_error "Please run this script from the pp-security-master project root directory"
        exit 1
    fi
    
    echo "Starting Phase 2 external integrations setup..."
    echo ""
    
    check_dependencies
    create_phase2_branch
    setup_external_repositories
    integrate_subtrees
    create_sync_script
    setup_external_apis
    install_dependencies
    create_adapter_modules
    setup_configuration
    create_integration_tests
    commit_changes
    
    echo ""
    echo "==========================================="
    echo -e "${GREEN}🎉 Phase 2 Setup Complete!${NC}"
    echo "==========================================="
    echo ""
    echo "Next steps:"
    echo "1. Update organization name in scripts/sync_external_repos.sh"
    echo "2. Get OpenFIGI API key and add to .env file"
    echo "3. Run validation script: ./scripts/phase2/validate_phase2_setup.sh"
    echo "4. Continue with Phase 2 implementation following the execution guide"
    echo ""
    echo -e "Current branch: ${BLUE}$PHASE2_BRANCH${NC}"
    echo -e "Push changes: ${BLUE}git push -u origin $PHASE2_BRANCH${NC}"
}

main "$@"