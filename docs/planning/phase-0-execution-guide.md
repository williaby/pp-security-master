# Phase 0: Foundation & Prerequisites - Execution Guide

**Duration**: 2 weeks (Weeks 1-2)  
**Team Size**: 1-2 developers  
**Prerequisites**: PostgreSQL 17 already operational on Unraid  

This document provides step-by-step instructions for executing Phase 0 tasks. Each step includes specific commands, expected outputs, and validation checks.

---

## Quick Start Checklist

Before starting, ensure you have:

- [x] PostgreSQL 17 running on Unraid (already completed)
- [x] .env.example verified to connect to database (already completed)
- [ ] Development machine with terminal access
- [ ] Git installed and configured
- [ ] Text editor or IDE available

---

## Week 1: Infrastructure Setup

### Day 1: Development Environment (P0-002)

**Time Estimate**: 2 hours

#### Step 1: Install Python 3.11 with pyenv

```bash
# Check if pyenv is already installed
which pyenv

# If not installed, install pyenv
curl https://pyenv.run | bash

# Add to shell profile (choose your shell)
# For bash:
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# For zsh:
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Reload shell
source ~/.bashrc  # or source ~/.zshrc

# Install Python 3.11.8
pyenv install 3.11.8
pyenv global 3.11.8
```

## Validation (1)

```bash
python --version
# Expected: Python 3.11.8
```

### Step 2: Install Poetry

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Configure Poetry
poetry config virtualenvs.in-project true
poetry config virtualenvs.prefer-active-python true
```

## Validation (2)

```bash
poetry --version
# Expected: Poetry (version 1.6.0) or similar

poetry config --list | grep "virtualenvs.in-project"
# Expected: virtualenvs.in-project = true
```

### Step 3: Navigate to Project and Set Up Environment

```bash
# Navigate to project directory
cd /path/to/pp-security-master

# Initialize basic pyproject.toml if it doesn't exist
poetry init --no-interaction --name pp-security-master --python "^3.11"

# Add basic dependencies
poetry add python-dotenv psycopg2-binary sqlalchemy pydantic

# Add development dependencies
poetry add --group dev black ruff mypy pytest pytest-cov pre-commit

# Install dependencies and create virtual environment
poetry install

# Activate virtual environment
poetry shell
```

## Validation (3)

```bash
# Check virtual environment
poetry env info --path
# Expected: /path/to/pp-security-master/.venv

# Check Python in virtual environment
which python
# Expected: /path/to/pp-security-master/.venv/bin/python
```

### Step 4: VSCode Configuration

```bash
# Create VSCode workspace directory
mkdir -p .vscode

# Create settings.json
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

# Create extensions.json
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
```

## Validation (4)

```bash
# Verify VSCode files exist
ls -la .vscode/
# Expected: settings.json and extensions.json

# If VSCode is installed, test it
code . # Should open project with Python interpreter detected
```

### Step 5: Environment Variables

```bash
# Create .env.example (this contains working values for Unraid PostgreSQL)
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

# Copy to actual .env file
cp .env.example .env

echo "⚠️  IMPORTANT: Edit .env file and replace 'your_secure_password_here' with your actual PostgreSQL password"
```

## Validation (5)

```bash
# Verify files exist
ls -la .env*
# Expected: .env and .env.example

# Test environment loading (after adding real password to .env)
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Environment loaded successfully')
print('DB Host:', os.getenv('PP_DB_HOST'))
print('DB Database:', os.getenv('PP_DB_DATABASE'))
"
# Expected: Shows environment variables loaded
```

## ✅ Day 1 Complete - Development environment operational

---

### Day 2: Repository Structure (P0-003)

**Time Estimate**: 2 hours

#### Step 1: Create Directory Structure

```bash
# Ensure you're in project root
pwd
# Expected: /path/to/pp-security-master

# Create main source directories
mkdir -p src/security_master/{extractor,classifier,storage,patch,config,database,validation}

# Create test directories
mkdir -p tests/{unit,integration,performance,fixtures}

# Create documentation directories (some may already exist)
mkdir -p docs/{adr,planning,api}

# Create utility directories
mkdir -p sql/versions
mkdir -p schema_exports
mkdir -p sample_data/{wells_fargo,ibkr,altoira,kubera}
mkdir -p scripts
mkdir -p pytest_plugins

# Create initial __init__.py files for Python packages
touch src/__init__.py
touch src/security_master/__init__.py
touch src/security_master/{extractor,classifier,storage,patch,config,database,validation}/__init__.py
touch tests/__init__.py
touch pytest_plugins/__init__.py
```

## Validation (6)

```bash
# Verify directory structure
find . -type d -name "__pycache__" -prune -o -type d -print | sort
# Expected to see all the directories created above

# Check Python package structure
find src -name "__init__.py" | sort
# Expected: Multiple __init__.py files in each Python package
```

### Step 2: Create Configuration Files

```bash
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
```

## Validation (7)

```bash
# Check configuration files
ls -la .gitignore .editorconfig
# Expected: Both files should exist

# Test .gitignore works
echo "test.pyc" > test.pyc
git status  # Should not show test.pyc file
rm test.pyc
```

## ✅ Day 2 Complete - Repository structure established

---

### Day 3: Database Schema (P0-004)

**Time Estimate**: 3 hours

#### Step 1: Test Database Connection

```bash
# First verify the database connection works
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT version();"
# Expected: Shows PostgreSQL 17.x version info

# Test basic operations
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT current_database(), current_user;"
# Expected: Shows pp_master database and pp_user
```

#### Step 2: Create Security Master Table

```bash
# Create SQL file for schema
cat > sql/001_create_security_master.sql << 'EOF'
-- Create securities_master table with comprehensive taxonomy fields
CREATE TABLE IF NOT EXISTS securities_master (
    -- Primary identification
    id SERIAL PRIMARY KEY,
    isin VARCHAR(12) UNIQUE NOT NULL CHECK (LENGTH(isin) = 12),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Security identifiers
    symbol VARCHAR(20),
    cusip VARCHAR(9) CHECK (LENGTH(cusip) = 9 OR cusip IS NULL),
    wkn VARCHAR(6),
    internal_id UUID DEFAULT gen_random_uuid(),
    
    -- Basic security information
    security_name VARCHAR(255) NOT NULL,
    security_type VARCHAR(50) NOT NULL,
    currency_code VARCHAR(3) NOT NULL CHECK (LENGTH(currency_code) = 3),
    
    -- GICS Classification
    gics_sector_code VARCHAR(2),
    gics_sector_name VARCHAR(100),
    gics_industry_group_code VARCHAR(4),
    gics_industry_group_name VARCHAR(100),
    gics_industry_code VARCHAR(6),
    gics_industry_name VARCHAR(100),
    gics_sub_industry_code VARCHAR(8),
    gics_sub_industry_name VARCHAR(100),
    
    -- TRBC Classification
    trbc_economic_sector_code VARCHAR(10),
    trbc_economic_sector_name VARCHAR(100),
    trbc_business_sector_code VARCHAR(10),
    trbc_business_sector_name VARCHAR(100),
    trbc_industry_group_code VARCHAR(10),
    trbc_industry_group_name VARCHAR(100),
    trbc_industry_code VARCHAR(10),
    trbc_industry_name VARCHAR(100),
    trbc_activity_code VARCHAR(10),
    trbc_activity_name VARCHAR(100),
    
    -- CFI and other classifications
    cfi_code VARCHAR(6),
    asset_class VARCHAR(20) NOT NULL,
    
    -- Data quality tracking
    data_quality_score DECIMAL(3,2) CHECK (data_quality_score >= 0.00 AND data_quality_score <= 1.00),
    completeness_score DECIMAL(3,2) CHECK (completeness_score >= 0.00 AND completeness_score <= 1.00),
    classification_confidence DECIMAL(3,2) CHECK (classification_confidence >= 0.00 AND classification_confidence <= 1.00),
    
    -- Data source and lineage
    primary_data_source VARCHAR(50),
    last_classification_update TIMESTAMP WITH TIME ZONE,
    manual_override BOOLEAN DEFAULT FALSE,
    
    -- Market information
    primary_exchange VARCHAR(10),
    trading_status VARCHAR(20) DEFAULT 'ACTIVE',
    market_cap_category VARCHAR(20),
    
    -- Audit fields
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_securities_master_isin ON securities_master(isin);
CREATE INDEX IF NOT EXISTS idx_securities_master_symbol ON securities_master(symbol);
CREATE INDEX IF NOT EXISTS idx_securities_master_gics_sector ON securities_master(gics_sector_code);
CREATE INDEX IF NOT EXISTS idx_securities_master_asset_class ON securities_master(asset_class);
CREATE INDEX IF NOT EXISTS idx_securities_master_updated_at ON securities_master(updated_at);

-- Create trigger function for updating timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger
DROP TRIGGER IF EXISTS update_securities_master_updated_at ON securities_master;
CREATE TRIGGER update_securities_master_updated_at 
    BEFORE UPDATE ON securities_master 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
EOF

# Execute the schema
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/001_create_security_master.sql
```

## Validation (8)

```bash
# Verify table was created
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\d securities_master"
# Expected: Shows table structure with all columns

# Test constraint enforcement
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
INSERT INTO securities_master (isin, security_name, security_type, currency_code, asset_class)
VALUES ('US0378331005', 'Apple Inc.', 'Common Stock', 'USD', 'equity');"
# Expected: Success

# Test duplicate constraint
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
INSERT INTO securities_master (isin, security_name, security_type, currency_code, asset_class)
VALUES ('US0378331005', 'Duplicate Apple', 'Common Stock', 'USD', 'equity');"
# Expected: Error due to unique constraint on ISIN

# Clean up test data
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "DELETE FROM securities_master WHERE isin = 'US0378331005';"
```

## ✅ Day 3 Complete - Security master table operational

---

## Week 2: Development Foundation

### Day 4: Alembic Migrations (P0-005)

**Time Estimate**: 2 hours

#### Step 1: Install and Initialize Alembic

```bash
# Add Alembic to dependencies
poetry add alembic

# Initialize Alembic
poetry run alembic init sql/versions

# This creates alembic.ini and sql/versions/env.py
```

#### Step 2: Configure Alembic

```bash
# Edit alembic.ini to point to our database
sed -i 's|sqlalchemy.url = driver://user:pass@localhost/dbname|sqlalchemy.url = |' alembic.ini

# Create custom env.py that reads from our config
cat > sql/versions/env.py << 'EOF'
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# this is the Alembic Config object
config = context.config

# Set the database URL from environment
config.set_main_option(
    "sqlalchemy.url",
    f"postgresql://{os.getenv('PP_DB_USERNAME')}:{os.getenv('PP_DB_PASSWORD')}@{os.getenv('PP_DB_HOST')}:{os.getenv('PP_DB_PORT')}/{os.getenv('PP_DB_DATABASE')}"
)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for autogenerate support
# target_metadata = mymodel.Base.metadata
target_metadata = None

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF
```

#### Step 3: Create Initial Migration

```bash
# Create first migration for existing schema
poetry run alembic revision --autogenerate -m "Initial schema with securities_master table"

# Apply migration
poetry run alembic upgrade head
```

## Validation (9)

```bash
# Check migration history
poetry run alembic history
# Expected: Shows the initial migration

# Check current revision
poetry run alembic current
# Expected: Shows current revision at head

# Test downgrade/upgrade
poetry run alembic downgrade -1
poetry run alembic upgrade head
# Expected: Both commands succeed
```

## ✅ Day 4 Complete - Alembic migrations operational

---

### Day 5: Configuration System (P0-006)

**Time Estimate**: 3 hours

#### Step 1: Create Configuration Module

```bash
# Add pydantic for settings
poetry add pydantic[dotenv]

# Create configuration module
cat > src/security_master/config/__init__.py << 'EOF'
"""Configuration package for security master application."""
EOF

cat > src/security_master/config/settings.py << 'EOF'
"""Application configuration using Pydantic Settings."""
from pydantic import BaseSettings, Field, validator
from typing import Optional
from pathlib import Path


class DatabaseSettings(BaseSettings):
    """Database connection settings."""
    
    host: str = Field(..., env="PP_DB_HOST")
    port: int = Field(5432, env="PP_DB_PORT")
    username: str = Field(..., env="PP_DB_USERNAME")  
    password: str = Field(..., env="PP_DB_PASSWORD")
    database: str = Field("pp_master", env="PP_DB_DATABASE")
    
    # Connection pool settings
    pool_size: int = Field(10, env="PP_DB_POOL_SIZE")
    max_overflow: int = Field(20, env="PP_DB_MAX_OVERFLOW")
    pool_timeout: int = Field(30, env="PP_DB_POOL_TIMEOUT")
    
    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class ApplicationSettings(BaseSettings):
    """Main application configuration."""
    
    # Environment settings
    environment: str = Field("development", env="PP_ENVIRONMENT")
    debug: bool = Field(False, env="PP_DEBUG")
    log_level: str = Field("INFO", env="PP_LOG_LEVEL")
    
    # Database configuration
    database: DatabaseSettings = DatabaseSettings()
    
    # Application settings
    data_quality_min_score: float = Field(0.7, env="PP_DATA_QUALITY_MIN_SCORE")
    classification_confidence_threshold: float = Field(0.8, env="PP_CLASSIFICATION_CONFIDENCE_THRESHOLD")
    
    @validator("environment")
    def validate_environment(cls, v):
        valid_envs = ["development", "testing", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
_settings: Optional[ApplicationSettings] = None


def get_settings() -> ApplicationSettings:
    """Get global settings instance with caching."""
    global _settings
    if _settings is None:
        _settings = ApplicationSettings()
    return _settings


def reload_settings() -> ApplicationSettings:
    """Reload settings (for development hot-reload)."""
    global _settings
    _settings = None
    return get_settings()
EOF
```

#### Step 2: Test Configuration Loading

```bash
# Create test script
cat > scripts/test_config.py << 'EOF'
#!/usr/bin/env python3
"""Test configuration loading."""
import sys
sys.path.insert(0, 'src')

from security_master.config.settings import get_settings

def main():
    try:
        settings = get_settings()
        print("✅ Configuration loaded successfully")
        print(f"Environment: {settings.environment}")
        print(f"Debug: {settings.debug}")
        print(f"Database Host: {settings.database.host}")
        print(f"Database Name: {settings.database.database}")
        print(f"Connection String: {settings.database.connection_string}")
        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

chmod +x scripts/test_config.py

# Run test
poetry run python scripts/test_config.py
```

## Validation (10)

```bash
# Test configuration loading
poetry run python scripts/test_config.py
# Expected: Shows configuration values loaded successfully

# Test invalid environment
PP_ENVIRONMENT=invalid poetry run python scripts/test_config.py
# Expected: Should show validation error
```

## ✅ Day 5 Complete - Configuration system operational

---

### Day 6: Database ORM Layer (P0-007)

**Time Estimate**: 3 hours

#### Step 1: Create Database Module

```bash
# Add SQLAlchemy
poetry add sqlalchemy[asyncio]

# Create database engine module
cat > src/security_master/database/__init__.py << 'EOF'
"""Database package for security master application."""
EOF

cat > src/security_master/database/engine.py << 'EOF'
"""Database engine and session management."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from security_master.config.settings import get_settings
import logging
import time

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def _create_engine(self):
        """Create SQLAlchemy engine with optimized configuration."""
        connection_string = self.settings.database.connection_string
        
        engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=self.settings.database.pool_size,
            max_overflow=self.settings.database.max_overflow,
            pool_timeout=self.settings.database.pool_timeout,
            pool_pre_ping=True,  # Validate connections before use
            echo=self.settings.debug,  # Log SQL queries in debug mode
        )
        
        # Add event listeners for monitoring
        event.listen(engine, "connect", self._on_connect)
        
        return engine
    
    def _on_connect(self, dbapi_connection, connection_record):
        """Handle new database connections."""
        logger.debug("New database connection established")
        
        # Set connection-level configuration
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET timezone = 'UTC'")
            cursor.execute("SET statement_timeout = '300s'")
    
    def get_session(self) -> Session:
        """Get database session with proper error handling."""
        try:
            session = self.SessionLocal()
            return session
        except Exception as e:
            logger.error(f"Failed to create database session: {e}")
            raise
    
    def health_check(self) -> bool:
        """Perform database health check."""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


def get_db_session() -> Session:
    """Dependency injection for database sessions."""
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
EOF
```

#### Step 2: Create Models

```bash
# Create models module
cat > src/security_master/database/models.py << 'EOF'
"""Database models for security master application."""
from sqlalchemy import Column, Integer, String, DateTime, Decimal, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields for all tables."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(50), nullable=True)
    updated_by = Column(String(50), nullable=True)


class SecurityMaster(BaseModel):
    """Security master table model."""
    __tablename__ = "securities_master"
    
    # Primary identification
    isin = Column(String(12), unique=True, nullable=False, index=True)
    internal_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    
    # Security identifiers
    symbol = Column(String(20), index=True)
    cusip = Column(String(9))
    wkn = Column(String(6))
    
    # Basic security information
    security_name = Column(String(255), nullable=False)
    security_type = Column(String(50), nullable=False)
    currency_code = Column(String(3), nullable=False)
    
    # GICS Classification
    gics_sector_code = Column(String(2))
    gics_sector_name = Column(String(100))
    gics_industry_group_code = Column(String(4))
    gics_industry_group_name = Column(String(100))
    gics_industry_code = Column(String(6))
    gics_industry_name = Column(String(100))
    gics_sub_industry_code = Column(String(8))
    gics_sub_industry_name = Column(String(100))
    
    # Data quality tracking
    data_quality_score = Column(Decimal(3, 2))
    completeness_score = Column(Decimal(3, 2))
    classification_confidence = Column(Decimal(3, 2))
    
    # Data source and lineage
    primary_data_source = Column(String(50))
    last_classification_update = Column(DateTime(timezone=True))
    manual_override = Column(Boolean, default=False)
    
    # Market information
    primary_exchange = Column(String(10))
    trading_status = Column(String(20), default='ACTIVE')
    market_cap_category = Column(String(20))
    asset_class = Column(String(20), nullable=False)
    
    def __repr__(self):
        return f"<SecurityMaster(isin='{self.isin}', name='{self.security_name}')>"
    
    def calculate_data_quality_score(self) -> float:
        """Calculate data quality score based on field completeness."""
        required_fields = [
            self.security_name, self.security_type, self.currency_code,
            self.asset_class, self.primary_data_source
        ]
        optional_fields = [
            self.symbol, self.gics_sector_code, self.primary_exchange
        ]
        
        required_score = sum(1 for field in required_fields if field) / len(required_fields)
        optional_score = sum(1 for field in optional_fields if field) / len(optional_fields)
        
        # Weight required fields more heavily
        return (required_score * 0.7) + (optional_score * 0.3)
EOF
```

#### Step 3: Test Database Connection

```bash
# Create database test script
cat > scripts/test_database.py << 'EOF'
#!/usr/bin/env python3
"""Test database connection and operations."""
import sys
sys.path.insert(0, 'src')

from security_master.database.engine import db_manager
from security_master.database.models import SecurityMaster

def main():
    try:
        # Test health check
        if not db_manager.health_check():
            print("❌ Database health check failed")
            return False
        
        print("✅ Database health check passed")
        
        # Test session creation
        with db_manager.get_session() as session:
            # Test basic query
            result = session.execute("SELECT version()").fetchone()
            print(f"✅ Database version: {result[0]}")
            
            # Test model operations
            test_security = SecurityMaster(
                isin="TEST12345678",
                security_name="Test Security",
                security_type="Test Type",
                currency_code="USD",
                asset_class="equity"
            )
            
            session.add(test_security)
            session.flush()  # Get ID without committing
            
            print(f"✅ Test security created with ID: {test_security.id}")
            
            # Calculate data quality score
            score = test_security.calculate_data_quality_score()
            print(f"✅ Data quality score calculated: {score:.2f}")
            
            # Rollback to avoid leaving test data
            session.rollback()
            print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

chmod +x scripts/test_database.py

# Run test
poetry run python scripts/test_database.py
```

## Validation (11)

```bash
# Test database operations
poetry run python scripts/test_database.py
# Expected: All tests pass, shows database version and test operations
```

## ✅ Day 6 Complete - Database ORM layer operational

---

### Days 7-10: Complete Remaining Issues

Follow the same pattern for the remaining issues:

- P0-008: Development Tooling (Day 7)
- P0-009: Data Validation Framework (Day 8)
- P0-010: Integration Testing (Days 9-10)

Each issue should follow this format:

1. **Step-by-step commands**
2. **Expected outputs**
3. **Validation checks**
4. **Troubleshooting tips**

---

## Phase 0 Completion Validation

### Final Validation Script

```bash
# Create master validation script
cat > scripts/validate_phase_0.sh << 'EOF'
#!/bin/bash
echo "=== Phase 0 Validation Script ==="
echo ""

# Test 1: Development Environment
echo "1. Testing development environment..."
python --version | grep "3.11" && echo "✅ Python 3.11 installed"
poetry --version && echo "✅ Poetry installed"

# Test 2: Configuration System
echo ""
echo "2. Testing configuration system..."
poetry run python scripts/test_config.py && echo "✅ Configuration working"

# Test 3: Database Connection
echo ""
echo "3. Testing database connection..."
poetry run python scripts/test_database.py && echo "✅ Database working"

# Test 4: Repository Structure
echo ""
echo "4. Testing repository structure..."
[ -d "src/security_master" ] && echo "✅ Source structure exists"
[ -d "tests/unit" ] && echo "✅ Test structure exists"
[ -f ".gitignore" ] && echo "✅ Configuration files exist"

echo ""
echo "=== Phase 0 Validation Complete ==="
EOF

chmod +x scripts/validate_phase_0.sh

# Run validation
./scripts/validate_phase_0.sh
```

**Expected Output**: All validation checks should pass with ✅ markers.

---

## Troubleshooting Guide

### Common Issues

#### Python/Poetry Issues

```bash
# If pyenv doesn't work
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"

# If Poetry doesn't activate virtual environment
poetry config virtualenvs.in-project true
poetry shell

# If dependencies fail to install
poetry update
poetry install --verbose
```

#### Database Connection Issues

```bash
# Test connection manually
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT 1;"

# Check environment variables
cat .env | grep PP_DB

# Verify network connectivity
ping unraid.lan
```

#### Permission Issues

```bash
# Fix Python script permissions
chmod +x scripts/*.py

# Fix shell script permissions
chmod +x scripts/*.sh
```

---

## Next Steps

Upon successful completion of Phase 0:

1. **Commit all changes**:

   ```bash
   git add .
   git commit -m "feat: Complete Phase 0 foundation setup"
   ```

2. **Validate team readiness**:
   - All team members can run validation script successfully
   - Development environment works on all machines
   - Database accessible from all development machines

3. **Prepare for Phase 1**:
   - Review Phase 1 requirements
   - Assign Phase 1 issues to team members
   - Set up Phase 1 development branches

### 🎉 Phase 0 Complete - Ready for Phase 1 Development
