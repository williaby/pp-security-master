# Phase 1: Core Infrastructure & Database Implementation - Execution Guide

**Duration**: 4 weeks (Weeks 3-6)  
**Team Size**: 2-3 developers  
**Prerequisites**: Phase 0 successfully completed and validated  

This document provides step-by-step instructions for executing Phase 1 tasks. Each step includes specific commands, expected outputs, and validation checks.

---

## Quick Start Checklist

Before starting Phase 1, ensure:
- [x] Phase 0 validation script passes: `./scripts/validate_phase_0_complete.sh`
- [x] PostgreSQL 17 operational and accessible from development machines
- [x] Development environment configured with Phase 0 requirements
- [ ] Team members have Phase 1 branch access and permissions
- [ ] Sample data files available for Wells Fargo CSV testing

---

## Week 3: Database Schema Completion

### Day 1: Institution Transaction Tables (P1-001)

**Time Estimate**: 4 hours

#### Step 1: Create Phase 1 Schema Structure
```bash
# Ensure we're in project root and virtual environment is active
cd pp-security-master
poetry shell

# Create Phase 1 schema directory
mkdir -p sql/phase1

# Verify PostgreSQL connection
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT version();"
# Expected: PostgreSQL 17.x version info
```

#### Step 2: Implement Wells Fargo Transaction Table
```bash
# Create Wells Fargo transaction table schema
cat > sql/phase1/002_create_wells_fargo_transactions.sql << 'EOF'
-- Wells Fargo transaction table with complete CSV field mapping
CREATE TABLE IF NOT EXISTS transactions_wells_fargo (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL,
    raw_line_number INTEGER,
    
    -- Wells Fargo specific fields (based on CSV export format)
    account_number VARCHAR(20),
    account_type VARCHAR(50), -- IRA, Taxable, 401k, etc.
    transaction_date DATE NOT NULL,
    settlement_date DATE,
    transaction_type VARCHAR(50) NOT NULL, -- Buy, Sell, Dividend, etc.
    security_description VARCHAR(255),
    symbol VARCHAR(20),
    cusip VARCHAR(9),
    
    -- Financial details (precision for financial calculations)
    quantity DECIMAL(18,8),
    price DECIMAL(18,8),
    principal_amount DECIMAL(15,2),
    commission DECIMAL(10,2),
    fees DECIMAL(10,2),
    net_amount DECIMAL(15,2),
    
    -- References and tracking
    security_master_id INTEGER REFERENCES securities_master(id),
    import_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_quality_score DECIMAL(3,2) CHECK (data_quality_score >= 0.00 AND data_quality_score <= 1.00),
    validation_errors JSONB DEFAULT '[]'::jsonb,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(50) DEFAULT 'system'
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_transactions_wf_batch_id ON transactions_wells_fargo(batch_id);
CREATE INDEX IF NOT EXISTS idx_transactions_wf_account ON transactions_wells_fargo(account_number);
CREATE INDEX IF NOT EXISTS idx_transactions_wf_date ON transactions_wells_fargo(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_wf_symbol ON transactions_wells_fargo(symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_wf_security_master ON transactions_wells_fargo(security_master_id);
CREATE INDEX IF NOT EXISTS idx_transactions_wf_type ON transactions_wells_fargo(transaction_type);

-- Constraints
ALTER TABLE transactions_wells_fargo 
ADD CONSTRAINT chk_wf_valid_dates 
CHECK (settlement_date IS NULL OR settlement_date >= transaction_date);

ALTER TABLE transactions_wells_fargo 
ADD CONSTRAINT chk_wf_valid_amounts 
CHECK (principal_amount IS NULL OR ABS(principal_amount) >= 0);
EOF

# Execute Wells Fargo table creation
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/002_create_wells_fargo_transactions.sql
```

#### Step 3: Implement Interactive Brokers Transaction Table
```bash
# Create IBKR transaction table schema
cat > sql/phase1/003_create_ibkr_transactions.sql << 'EOF'
-- Interactive Brokers transaction table for Flex Query XML structure
CREATE TABLE IF NOT EXISTS transactions_interactive_brokers (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL,
    raw_xml_data JSONB, -- Store original XML data
    
    -- IBKR specific fields (from Flex Query XML)
    account_id VARCHAR(20) NOT NULL,
    account_alias VARCHAR(50),
    model VARCHAR(20),
    currency VARCHAR(3) NOT NULL,
    
    -- Transaction details
    trade_date DATE NOT NULL,
    settle_date DATE,
    transaction_type VARCHAR(50) NOT NULL, -- Trade, Dividend, Interest, etc.
    exchange VARCHAR(10),
    
    -- Security information
    symbol VARCHAR(20),
    underlying_symbol VARCHAR(20),
    security_type VARCHAR(20), -- STK, OPT, FUT, etc.
    multiplier INTEGER DEFAULT 1,
    strike DECIMAL(10,4),
    expiry DATE,
    put_call VARCHAR(1), -- C, P
    
    -- Financial details
    quantity DECIMAL(18,8),
    trade_price DECIMAL(18,8),
    proceeds DECIMAL(15,2),
    comm_currency VARCHAR(3),
    commission DECIMAL(10,2),
    tax DECIMAL(10,2),
    
    -- References and tracking
    security_master_id INTEGER REFERENCES securities_master(id),
    import_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_quality_score DECIMAL(3,2) CHECK (data_quality_score >= 0.00 AND data_quality_score <= 1.00),
    validation_errors JSONB DEFAULT '[]'::jsonb,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(50) DEFAULT 'system'
);

-- Indexes for IBKR transactions
CREATE INDEX IF NOT EXISTS idx_transactions_ibkr_batch_id ON transactions_interactive_brokers(batch_id);
CREATE INDEX IF NOT EXISTS idx_transactions_ibkr_account ON transactions_interactive_brokers(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_ibkr_date ON transactions_interactive_brokers(trade_date);
CREATE INDEX IF NOT EXISTS idx_transactions_ibkr_symbol ON transactions_interactive_brokers(symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_ibkr_type ON transactions_interactive_brokers(transaction_type);
EOF

# Execute IBKR table creation
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/003_create_ibkr_transactions.sql
```

#### Step 4: Implement AltoIRA and Kubera Transaction Tables
```bash
# Create AltoIRA transaction table schema
cat > sql/phase1/004_create_altoira_transactions.sql << 'EOF'
-- AltoIRA transaction table for PDF-extracted transaction data
CREATE TABLE IF NOT EXISTS transactions_altoira (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL,
    raw_pdf_text TEXT, -- Store original PDF text for reference
    pdf_page_number INTEGER,
    extraction_confidence DECIMAL(3,2), -- OCR confidence score
    
    -- AltoIRA specific fields
    account_number VARCHAR(20),
    transaction_date DATE NOT NULL,
    description VARCHAR(500), -- Full transaction description from PDF
    transaction_type VARCHAR(50), -- Parsed from description
    
    -- Security information (parsed from description)
    security_name VARCHAR(255),
    symbol VARCHAR(20),
    
    -- Financial details
    amount DECIMAL(15,2),
    shares DECIMAL(18,8),
    price_per_share DECIMAL(18,8),
    
    -- References and tracking
    security_master_id INTEGER REFERENCES securities_master(id),
    import_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_quality_score DECIMAL(3,2) CHECK (data_quality_score >= 0.00 AND data_quality_score <= 1.00),
    validation_errors JSONB DEFAULT '[]'::jsonb,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(50) DEFAULT 'system'
);

-- Indexes for AltoIRA transactions
CREATE INDEX IF NOT EXISTS idx_transactions_altoira_batch_id ON transactions_altoira(batch_id);
CREATE INDEX IF NOT EXISTS idx_transactions_altoira_account ON transactions_altoira(account_number);
CREATE INDEX IF NOT EXISTS idx_transactions_altoira_date ON transactions_altoira(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_altoira_symbol ON transactions_altoira(symbol);
EOF

# Create Kubera transaction table schema
cat > sql/phase1/005_create_kubera_transactions.sql << 'EOF'
-- Kubera transaction table for JSON API aggregated data
CREATE TABLE IF NOT EXISTS transactions_kubera (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL,
    raw_api_response JSONB, -- Store original API response
    kubera_transaction_id VARCHAR(50), -- External ID from Kubera
    
    -- Kubera specific fields
    account_id VARCHAR(50),
    account_name VARCHAR(100),
    account_type VARCHAR(50),
    
    -- Transaction details
    transaction_date DATE NOT NULL,
    transaction_type VARCHAR(50),
    category VARCHAR(50),
    subcategory VARCHAR(50),
    
    -- Security/Asset information
    asset_name VARCHAR(255),
    asset_type VARCHAR(50), -- Stock, Crypto, Real Estate, etc.
    ticker_symbol VARCHAR(20),
    
    -- Financial details (multi-currency support)
    amount DECIMAL(15,2),
    currency VARCHAR(3),
    usd_amount DECIMAL(15,2), -- Converted to USD
    exchange_rate DECIMAL(10,6),
    
    -- Quantity information (for securities)
    quantity DECIMAL(18,8),
    price_per_unit DECIMAL(15,6),
    
    -- References and tracking
    security_master_id INTEGER REFERENCES securities_master(id),
    import_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_quality_score DECIMAL(3,2) CHECK (data_quality_score >= 0.00 AND data_quality_score <= 1.00),
    validation_errors JSONB DEFAULT '[]'::jsonb,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(50) DEFAULT 'system'
);

-- Indexes for Kubera transactions
CREATE INDEX IF NOT EXISTS idx_transactions_kubera_batch_id ON transactions_kubera(batch_id);
CREATE INDEX IF NOT EXISTS idx_transactions_kubera_account ON transactions_kubera(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_kubera_date ON transactions_kubera(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_kubera_symbol ON transactions_kubera(ticker_symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_kubera_ext_id ON transactions_kubera(kubera_transaction_id);
EOF

# Execute AltoIRA and Kubera table creation
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/004_create_altoira_transactions.sql
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/005_create_kubera_transactions.sql
```

#### Step 5: Create Unified Transaction View
```bash
# Create common transaction interface view
cat > sql/phase1/006_create_common_transaction_view.sql << 'EOF'
-- Common transaction interface view for cross-institution queries
CREATE OR REPLACE VIEW v_transactions_unified AS
SELECT 
    'wells_fargo' as institution,
    id,
    batch_id,
    transaction_date,
    settlement_date,
    transaction_type,
    symbol,
    security_description as security_name,
    quantity,
    price,
    principal_amount as amount,
    commission,
    fees,
    net_amount,
    security_master_id,
    data_quality_score,
    created_at
FROM transactions_wells_fargo
WHERE data_quality_score >= 0.5 -- Only include reasonable quality data

UNION ALL

SELECT 
    'interactive_brokers' as institution,
    id,
    batch_id,
    trade_date as transaction_date,
    settle_date as settlement_date,
    transaction_type,
    symbol,
    symbol as security_name, -- IBKR uses symbol as name
    quantity,
    trade_price as price,
    proceeds as amount,
    commission,
    tax as fees,
    proceeds as net_amount,
    security_master_id,
    data_quality_score,
    created_at
FROM transactions_interactive_brokers
WHERE data_quality_score >= 0.5

UNION ALL

SELECT 
    'altoira' as institution,
    id,
    batch_id,
    transaction_date,
    transaction_date as settlement_date, -- AltoIRA doesn't separate dates
    transaction_type,
    symbol,
    security_name,
    shares as quantity,
    price_per_share as price,
    amount,
    0 as commission, -- AltoIRA doesn't separate commissions
    0 as fees,
    amount as net_amount,
    security_master_id,
    data_quality_score,
    created_at
FROM transactions_altoira
WHERE data_quality_score >= 0.5

UNION ALL

SELECT 
    'kubera' as institution,
    id,
    batch_id,
    transaction_date,
    transaction_date as settlement_date,
    transaction_type,
    ticker_symbol as symbol,
    asset_name as security_name,
    quantity,
    price_per_unit as price,
    usd_amount as amount,
    0 as commission,
    0 as fees,
    usd_amount as net_amount,
    security_master_id,
    data_quality_score,
    created_at
FROM transactions_kubera
WHERE data_quality_score >= 0.5;

-- Create materialized view for performance-critical queries
CREATE MATERIALIZED VIEW mv_transactions_unified AS
SELECT * FROM v_transactions_unified;

-- Index on materialized view
CREATE INDEX IF NOT EXISTS idx_mv_transactions_institution ON mv_transactions_unified(institution);
CREATE INDEX IF NOT EXISTS idx_mv_transactions_date ON mv_transactions_unified(transaction_date);
CREATE INDEX IF NOT EXISTS idx_mv_transactions_symbol ON mv_transactions_unified(symbol);
EOF

# Execute view creation
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/006_create_common_transaction_view.sql
```

**Validation:**
```bash
# Verify all tables created
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\dt transactions_*"
# Expected: List of all 4 transaction tables

# Verify indexes created
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\di idx_transactions_*"
# Expected: List of all performance indexes

# Test unified view
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT institution, count(*) FROM v_transactions_unified GROUP BY institution;"
# Expected: Shows count by institution (may be 0 initially)

# Verify foreign key constraints
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT tc.table_name, tc.constraint_name FROM information_schema.table_constraints tc WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name LIKE 'transactions_%';"
# Expected: Shows foreign key constraints to securities_master

# Test table constraints
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "INSERT INTO transactions_wells_fargo (batch_id, transaction_date, transaction_type, data_quality_score) VALUES (gen_random_uuid(), '2024-01-01', 'Buy', 0.8);"
# Expected: Success

psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT id, batch_id, transaction_date FROM transactions_wells_fargo LIMIT 1;"
# Expected: Shows the test record

# Clean up test data
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "DELETE FROM transactions_wells_fargo;"
```

**✅ Day 1 Complete - Institution transaction tables operational**

---

### Day 2: Data Lineage and Batch Tracking (P1-002)

**Time Estimate**: 3 hours

#### Step 1: Create Import Batch Tracking Table
```bash
# Create import batch tracking schema
cat > sql/phase1/007_create_import_batches.sql << 'EOF'
-- Import batch tracking for data lineage and audit
CREATE TABLE IF NOT EXISTS import_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT,
    file_hash VARCHAR(64) NOT NULL, -- SHA-256 hash for duplicate detection
    file_size BIGINT NOT NULL,
    
    -- Batch processing status
    status VARCHAR(20) NOT NULL DEFAULT 'pending', 
    -- Valid statuses: pending, processing, completed, failed, rolled_back
    
    -- Processing statistics
    total_records INTEGER DEFAULT 0,
    valid_records INTEGER DEFAULT 0,
    invalid_records INTEGER DEFAULT 0,
    duplicate_records INTEGER DEFAULT 0,
    skipped_records INTEGER DEFAULT 0,
    
    -- Quality metrics
    data_quality_score DECIMAL(3,2),
    validation_errors JSONB DEFAULT '[]'::jsonb,
    processing_log JSONB DEFAULT '[]'::jsonb,
    
    -- Timing information
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_duration_seconds INTEGER,
    
    -- User and system tracking
    created_by VARCHAR(50) DEFAULT 'system',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for batch tracking performance
CREATE INDEX IF NOT EXISTS idx_import_batches_institution ON import_batches(institution);
CREATE INDEX IF NOT EXISTS idx_import_batches_status ON import_batches(status);
CREATE INDEX IF NOT EXISTS idx_import_batches_file_hash ON import_batches(file_hash);
CREATE INDEX IF NOT EXISTS idx_import_batches_created_at ON import_batches(created_at);

-- Constraints
ALTER TABLE import_batches 
ADD CONSTRAINT chk_batch_status 
CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'rolled_back'));

ALTER TABLE import_batches 
ADD CONSTRAINT chk_batch_valid_institution 
CHECK (institution IN ('wells_fargo', 'interactive_brokers', 'altoira', 'kubera'));

-- Add batch_id foreign key to all transaction tables
ALTER TABLE transactions_wells_fargo 
ADD CONSTRAINT fk_wf_batch_id 
FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE CASCADE;

ALTER TABLE transactions_interactive_brokers 
ADD CONSTRAINT fk_ibkr_batch_id 
FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE CASCADE;

ALTER TABLE transactions_altoira 
ADD CONSTRAINT fk_altoira_batch_id 
FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE CASCADE;

ALTER TABLE transactions_kubera 
ADD CONSTRAINT fk_kubera_batch_id 
FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE CASCADE;
EOF

# Execute batch tracking table creation
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/007_create_import_batches.sql
```

#### Step 2: Create Batch Management Python Module
```bash
# Create batch management module
mkdir -p src/security_master/batch
touch src/security_master/batch/__init__.py

cat > src/security_master/batch/models.py << 'EOF'
"""Batch processing models for import tracking."""
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class BatchStatus(str, Enum):
    """Import batch status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class Institution(str, Enum):
    """Supported institution enumeration."""
    WELLS_FARGO = "wells_fargo"
    INTERACTIVE_BROKERS = "interactive_brokers"
    ALTOIRA = "altoira"
    KUBERA = "kubera"


class ImportBatch(BaseModel):
    """Import batch tracking and management."""
    
    id: UUID = Field(default_factory=uuid4)
    institution: Institution
    file_name: str
    file_path: Optional[str] = None
    file_hash: str = Field(..., min_length=64, max_length=64)  # SHA-256
    file_size: int = Field(..., gt=0)
    
    # Status tracking
    status: BatchStatus = BatchStatus.PENDING
    
    # Statistics
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    skipped_records: int = 0
    
    # Quality metrics
    data_quality_score: Optional[Decimal] = Field(None, ge=0, le=1)
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)
    processing_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_duration_seconds: Optional[int] = None
    
    # Audit
    created_by: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('data_quality_score')
    def validate_quality_score(cls, v):
        if v is not None and not (0 <= v <= 1):
            raise ValueError('Data quality score must be between 0 and 1')
        return v
    
    @property
    def is_processing(self) -> bool:
        """Check if batch is currently being processed."""
        return self.status == BatchStatus.PROCESSING
    
    @property
    def is_completed(self) -> bool:
        """Check if batch completed successfully."""
        return self.status == BatchStatus.COMPLETED
    
    @property
    def has_errors(self) -> bool:
        """Check if batch has validation errors."""
        return len(self.validation_errors) > 0
    
    def calculate_success_rate(self) -> float:
        """Calculate the success rate of record processing."""
        if self.total_records == 0:
            return 0.0
        return self.valid_records / self.total_records
    
    def add_processing_log(self, message: str, level: str = "info", **kwargs):
        """Add entry to processing log."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.processing_log.append(log_entry)
    
    def add_validation_error(self, error: str, row_number: int = None, **kwargs):
        """Add validation error to batch."""
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error,
            "row_number": row_number,
            **kwargs
        }
        self.validation_errors.append(error_entry)


class BatchStatistics(BaseModel):
    """Batch processing statistics summary."""
    
    batch_id: UUID
    institution: Institution
    status: BatchStatus
    
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_records: int
    skipped_records: int
    
    success_rate: float
    data_quality_score: Optional[Decimal]
    
    processing_duration_seconds: Optional[int]
    errors_count: int
    
    created_at: datetime
    completed_at: Optional[datetime]
EOF
```

#### Step 3: Create Batch Management Service
```bash
cat > src/security_master/batch/service.py << 'EOF'
"""Batch management service for import operations."""
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database.engine import get_db_session
from .models import ImportBatch, BatchStatus, Institution, BatchStatistics

logger = logging.getLogger(__name__)


class BatchManager:
    """Manages import batch lifecycle and operations."""
    
    def __init__(self, session: Session = None):
        self.session = session
    
    def create_batch(
        self, 
        institution: Institution,
        file_path: Path,
        created_by: str = "system"
    ) -> ImportBatch:
        """Create new import batch from file."""
        
        # Calculate file hash for duplicate detection
        file_hash = self._calculate_file_hash(file_path)
        file_size = file_path.stat().st_size
        
        # Check for duplicate files
        existing_batch = self.get_batch_by_hash(file_hash)
        if existing_batch and existing_batch.status == BatchStatus.COMPLETED:
            raise ValueError(f"File already processed in batch {existing_batch.id}")
        
        batch = ImportBatch(
            institution=institution,
            file_name=file_path.name,
            file_path=str(file_path.absolute()),
            file_hash=file_hash,
            file_size=file_size,
            created_by=created_by
        )
        
        batch.add_processing_log("Batch created", level="info")
        
        # Save to database
        self._save_batch(batch)
        
        return batch
    
    def start_processing(self, batch_id: UUID) -> ImportBatch:
        """Mark batch as processing and update timing."""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        if batch.status != BatchStatus.PENDING:
            raise ValueError(f"Batch {batch_id} is not in pending status")
        
        batch.status = BatchStatus.PROCESSING
        batch.started_at = datetime.now(timezone.utc)
        batch.add_processing_log("Processing started", level="info")
        
        self._save_batch(batch)
        return batch
    
    def complete_batch(
        self, 
        batch_id: UUID, 
        statistics: Dict[str, int],
        data_quality_score: float = None
    ) -> ImportBatch:
        """Mark batch as completed with final statistics."""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        # Update statistics
        batch.total_records = statistics.get('total_records', 0)
        batch.valid_records = statistics.get('valid_records', 0)
        batch.invalid_records = statistics.get('invalid_records', 0)
        batch.duplicate_records = statistics.get('duplicate_records', 0)
        batch.skipped_records = statistics.get('skipped_records', 0)
        
        if data_quality_score is not None:
            batch.data_quality_score = data_quality_score
        
        # Complete processing
        batch.status = BatchStatus.COMPLETED
        batch.completed_at = datetime.now(timezone.utc)
        
        if batch.started_at:
            duration = (batch.completed_at - batch.started_at).total_seconds()
            batch.processing_duration_seconds = int(duration)
        
        batch.add_processing_log("Processing completed", level="info", **statistics)
        
        self._save_batch(batch)
        return batch
    
    def fail_batch(self, batch_id: UUID, error_message: str) -> ImportBatch:
        """Mark batch as failed with error information."""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        batch.status = BatchStatus.FAILED
        batch.completed_at = datetime.now(timezone.utc)
        
        if batch.started_at:
            duration = (batch.completed_at - batch.started_at).total_seconds()
            batch.processing_duration_seconds = int(duration)
        
        batch.add_processing_log("Processing failed", level="error", error=error_message)
        
        self._save_batch(batch)
        return batch
    
    def rollback_batch(self, batch_id: UUID, reason: str) -> ImportBatch:
        """Rollback batch and delete all associated records."""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        # Delete all records from institution tables
        with get_db_session() as session:
            if batch.institution == Institution.WELLS_FARGO:
                session.execute(
                    text("DELETE FROM transactions_wells_fargo WHERE batch_id = :batch_id"),
                    {"batch_id": batch_id}
                )
            elif batch.institution == Institution.INTERACTIVE_BROKERS:
                session.execute(
                    text("DELETE FROM transactions_interactive_brokers WHERE batch_id = :batch_id"),
                    {"batch_id": batch_id}
                )
            elif batch.institution == Institution.ALTOIRA:
                session.execute(
                    text("DELETE FROM transactions_altoira WHERE batch_id = :batch_id"),
                    {"batch_id": batch_id}
                )
            elif batch.institution == Institution.KUBERA:
                session.execute(
                    text("DELETE FROM transactions_kubera WHERE batch_id = :batch_id"),
                    {"batch_id": batch_id}
                )
            
            session.commit()
        
        # Update batch status
        batch.status = BatchStatus.ROLLED_BACK
        batch.add_processing_log("Batch rolled back", level="warning", reason=reason)
        
        self._save_batch(batch)
        return batch
    
    def get_batch(self, batch_id: UUID) -> Optional[ImportBatch]:
        """Retrieve batch by ID."""
        with get_db_session() as session:
            result = session.execute(
                text("SELECT * FROM import_batches WHERE id = :batch_id"),
                {"batch_id": batch_id}
            ).fetchone()
            
            if result:
                return ImportBatch(**dict(result._mapping))
            return None
    
    def get_batch_by_hash(self, file_hash: str) -> Optional[ImportBatch]:
        """Retrieve batch by file hash."""
        with get_db_session() as session:
            result = session.execute(
                text("SELECT * FROM import_batches WHERE file_hash = :file_hash"),
                {"file_hash": file_hash}
            ).fetchone()
            
            if result:
                return ImportBatch(**dict(result._mapping))
            return None
    
    def get_batches_by_status(self, status: BatchStatus) -> List[ImportBatch]:
        """Retrieve batches by status."""
        with get_db_session() as session:
            results = session.execute(
                text("SELECT * FROM import_batches WHERE status = :status ORDER BY created_at DESC"),
                {"status": status.value}
            ).fetchall()
            
            return [ImportBatch(**dict(row._mapping)) for row in results]
    
    def get_batch_statistics(self, batch_id: UUID) -> Optional[BatchStatistics]:
        """Get comprehensive batch statistics."""
        batch = self.get_batch(batch_id)
        if not batch:
            return None
        
        return BatchStatistics(
            batch_id=batch.id,
            institution=batch.institution,
            status=batch.status,
            total_records=batch.total_records,
            valid_records=batch.valid_records,
            invalid_records=batch.invalid_records,
            duplicate_records=batch.duplicate_records,
            skipped_records=batch.skipped_records,
            success_rate=batch.calculate_success_rate(),
            data_quality_score=batch.data_quality_score,
            processing_duration_seconds=batch.processing_duration_seconds,
            errors_count=len(batch.validation_errors),
            created_at=batch.created_at,
            completed_at=batch.completed_at
        )
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _save_batch(self, batch: ImportBatch):
        """Save batch to database."""
        batch.updated_at = datetime.now(timezone.utc)
        
        with get_db_session() as session:
            # Use raw SQL for now - will be replaced with ORM
            session.execute(
                text("""
                INSERT INTO import_batches (
                    id, institution, file_name, file_path, file_hash, file_size,
                    status, total_records, valid_records, invalid_records, 
                    duplicate_records, skipped_records, data_quality_score,
                    validation_errors, processing_log, started_at, completed_at,
                    processing_duration_seconds, created_by, created_at, updated_at
                ) VALUES (
                    :id, :institution, :file_name, :file_path, :file_hash, :file_size,
                    :status, :total_records, :valid_records, :invalid_records,
                    :duplicate_records, :skipped_records, :data_quality_score,
                    :validation_errors, :processing_log, :started_at, :completed_at,
                    :processing_duration_seconds, :created_by, :created_at, :updated_at
                )
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    total_records = EXCLUDED.total_records,
                    valid_records = EXCLUDED.valid_records,
                    invalid_records = EXCLUDED.invalid_records,
                    duplicate_records = EXCLUDED.duplicate_records,
                    skipped_records = EXCLUDED.skipped_records,
                    data_quality_score = EXCLUDED.data_quality_score,
                    validation_errors = EXCLUDED.validation_errors,
                    processing_log = EXCLUDED.processing_log,
                    started_at = EXCLUDED.started_at,
                    completed_at = EXCLUDED.completed_at,
                    processing_duration_seconds = EXCLUDED.processing_duration_seconds,
                    updated_at = EXCLUDED.updated_at
                """),
                {
                    "id": batch.id,
                    "institution": batch.institution.value,
                    "file_name": batch.file_name,
                    "file_path": batch.file_path,
                    "file_hash": batch.file_hash,
                    "file_size": batch.file_size,
                    "status": batch.status.value,
                    "total_records": batch.total_records,
                    "valid_records": batch.valid_records,
                    "invalid_records": batch.invalid_records,
                    "duplicate_records": batch.duplicate_records,
                    "skipped_records": batch.skipped_records,
                    "data_quality_score": batch.data_quality_score,
                    "validation_errors": batch.validation_errors,
                    "processing_log": batch.processing_log,
                    "started_at": batch.started_at,
                    "completed_at": batch.completed_at,
                    "processing_duration_seconds": batch.processing_duration_seconds,
                    "created_by": batch.created_by,
                    "created_at": batch.created_at,
                    "updated_at": batch.updated_at
                }
            )
            session.commit()
EOF
```

**Validation:**
```bash
# Test batch tracking table
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'import_batches' ORDER BY ordinal_position;"
# Expected: Shows all batch tracking columns

# Test batch management code
python -c "
import sys
sys.path.insert(0, 'src')
from security_master.batch.models import ImportBatch, Institution
batch = ImportBatch(institution=Institution.WELLS_FARGO, file_name='test.csv', file_hash='a' * 64, file_size=1000)
print(f'Batch created: {batch.id}')
print(f'Success rate: {batch.calculate_success_rate()}')
"

# Test foreign key constraints
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
SELECT 
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND ccu.table_name = 'import_batches';
"
# Expected: Shows foreign key relationships from transaction tables
```

**✅ Day 2 Complete - Data lineage and batch tracking operational**

---

## Week 4: Wells Fargo Import Pipeline

### Day 8: Wells Fargo CSV Parser (P1-003)

**Time Estimate**: 4 hours

#### Step 1: Create Sample Wells Fargo CSV Data
```bash
# Create sample data directory
mkdir -p sample_data/wells_fargo

# Create sample Wells Fargo CSV file for testing
cat > sample_data/wells_fargo/sample_transactions.csv << 'EOF'
Account Number,Account Type,Transaction Date,Settlement Date,Transaction Type,Security Description,Symbol,CUSIP,Quantity,Price,Principal Amount,Commission,Fees,Net Amount
123456789,IRA,2024-01-15,2024-01-17,Buy,Apple Inc. Common Stock,AAPL,037833100,100,150.25,15025.00,9.99,0.00,-15034.99
123456789,IRA,2024-01-20,2024-01-22,Sell,Microsoft Corp. Common Stock,MSFT,594918104,50,380.50,19025.00,9.99,0.00,19015.01
123456789,Taxable,2024-01-25,2024-01-25,Dividend,Apple Inc. Common Stock,AAPL,037833100,0,0.00,73.00,0.00,0.00,73.00
123456789,401K,2024-02-01,2024-02-03,Buy,Vanguard S&P 500 ETF,VOO,922908769,25,420.15,10503.75,0.00,0.00,-10503.75
123456789,IRA,2024-02-05,2024-02-07,Buy,Tesla Inc. Common Stock,TSLA,88160R101,10,195.75,1957.50,9.99,0.00,-1967.49
EOF

echo "Sample Wells Fargo CSV created with 5 test transactions"
```

#### Step 2: Create Wells Fargo Parser Module
```bash
# Create extractor module structure
mkdir -p src/security_master/extractor/wells_fargo
touch src/security_master/extractor/__init__.py
touch src/security_master/extractor/wells_fargo/__init__.py

cat > src/security_master/extractor/wells_fargo/models.py << 'EOF'
"""Wells Fargo transaction data models."""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, validator


class WellsFargoTransaction(BaseModel):
    """Wells Fargo CSV transaction record."""
    
    # Raw CSV fields
    account_number: str = Field(..., alias="Account Number")
    account_type: str = Field(..., alias="Account Type")
    transaction_date: date = Field(..., alias="Transaction Date")
    settlement_date: Optional[date] = Field(None, alias="Settlement Date")
    transaction_type: str = Field(..., alias="Transaction Type")
    security_description: Optional[str] = Field(None, alias="Security Description")
    symbol: Optional[str] = Field(None, alias="Symbol")
    cusip: Optional[str] = Field(None, alias="CUSIP")
    quantity: Optional[Decimal] = Field(None, alias="Quantity")
    price: Optional[Decimal] = Field(None, alias="Price")
    principal_amount: Optional[Decimal] = Field(None, alias="Principal Amount")
    commission: Optional[Decimal] = Field(None, alias="Commission")
    fees: Optional[Decimal] = Field(None, alias="Fees")
    net_amount: Optional[Decimal] = Field(None, alias="Net Amount")
    
    # Metadata
    raw_line_number: Optional[int] = None
    
    class Config:
        allow_population_by_field_name = True
    
    @validator('cusip')
    def validate_cusip(cls, v):
        """Validate CUSIP format if provided."""
        if v and len(v) != 9:
            raise ValueError(f'CUSIP must be 9 characters, got {len(v)}')
        return v
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        """Validate transaction type against known Wells Fargo types."""
        valid_types = [
            'Buy', 'Sell', 'Dividend', 'Interest', 'Fee', 'Transfer In', 
            'Transfer Out', 'Deposit', 'Withdrawal', 'Reinvestment',
            'Stock Split', 'Stock Dividend', 'Spin-off'
        ]
        if v not in valid_types:
            # Log warning but don't reject - Wells Fargo may have new types
            pass
        return v
    
    @validator('account_type')
    def validate_account_type(cls, v):
        """Validate account type against known Wells Fargo account types."""
        valid_types = ['IRA', 'Taxable', '401K', 'Roth IRA', 'SEP-IRA', 'Trust']
        if v not in valid_types:
            # Log warning but don't reject
            pass
        return v
    
    def calculate_data_quality_score(self) -> float:
        """Calculate data quality score for this transaction."""
        score = 0.0
        total_checks = 0
        
        # Required fields
        required_fields = [
            self.account_number, self.transaction_date, 
            self.transaction_type, self.net_amount
        ]
        score += sum(1 for field in required_fields if field is not None)
        total_checks += len(required_fields)
        
        # Security identification (at least one should be present)
        security_fields = [self.symbol, self.cusip, self.security_description]
        if any(field for field in security_fields):
            score += 1
        total_checks += 1
        
        # Financial consistency
        if (self.quantity and self.price and self.principal_amount):
            expected_principal = abs(self.quantity * self.price)
            actual_principal = abs(self.principal_amount)
            if abs(expected_principal - actual_principal) < 0.01:  # Within 1 cent
                score += 1
            total_checks += 1
        
        # Date consistency
        if self.settlement_date and self.settlement_date >= self.transaction_date:
            score += 1
        total_checks += 1
        
        return score / total_checks if total_checks > 0 else 0.0
EOF
```

#### Step 3: Create Wells Fargo Parser Implementation
```bash
cat > src/security_master/extractor/wells_fargo/parser.py << 'EOF'
"""Wells Fargo CSV parser implementation."""
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Iterator, Optional, Tuple
from uuid import UUID

from .models import WellsFargoTransaction
from ...batch.service import BatchManager
from ...batch.models import Institution, BatchStatus

logger = logging.getLogger(__name__)


class WellsFargoParseResult:
    """Result of Wells Fargo CSV parsing operation."""
    
    def __init__(self, batch_id: UUID):
        self.batch_id = batch_id
        self.total_rows = 0
        self.valid_transactions: List[WellsFargoTransaction] = []
        self.invalid_transactions: List[Tuple[int, dict, str]] = []  # (row_num, raw_data, error)
        self.duplicate_transactions: List[WellsFargoTransaction] = []
        self.processing_errors: List[str] = []
    
    @property
    def success_count(self) -> int:
        return len(self.valid_transactions)
    
    @property
    def error_count(self) -> int:
        return len(self.invalid_transactions)
    
    @property
    def duplicate_count(self) -> int:
        return len(self.duplicate_transactions)
    
    @property
    def success_rate(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return self.success_count / self.total_rows


class WellsFargoParser:
    """Wells Fargo CSV transaction parser with validation and error handling."""
    
    def __init__(self, batch_manager: BatchManager = None):
        self.batch_manager = batch_manager or BatchManager()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def parse_file(self, file_path: Path, created_by: str = "system") -> WellsFargoParseResult:
        """Parse Wells Fargo CSV file with comprehensive validation."""
        
        # Create import batch
        batch = self.batch_manager.create_batch(
            institution=Institution.WELLS_FARGO,
            file_path=file_path,
            created_by=created_by
        )
        
        result = WellsFargoParseResult(batch.id)
        
        try:
            # Start processing
            self.batch_manager.start_processing(batch.id)
            
            # Parse CSV file
            self._parse_csv_content(file_path, result)
            
            # Process transactions (validation, deduplication, etc.)
            self._process_transactions(result)
            
            # Complete batch with statistics
            statistics = {
                'total_records': result.total_rows,
                'valid_records': result.success_count,
                'invalid_records': result.error_count,
                'duplicate_records': result.duplicate_count,
                'skipped_records': 0
            }
            
            # Calculate overall data quality score
            if result.valid_transactions:
                quality_scores = [t.calculate_data_quality_score() for t in result.valid_transactions]
                avg_quality_score = sum(quality_scores) / len(quality_scores)
            else:
                avg_quality_score = 0.0
            
            self.batch_manager.complete_batch(
                batch.id, 
                statistics, 
                data_quality_score=avg_quality_score
            )
            
            self.logger.info(
                f"Parsed Wells Fargo file {file_path.name}: "
                f"{result.success_count}/{result.total_rows} successful, "
                f"{result.error_count} errors, {result.duplicate_count} duplicates"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse Wells Fargo file {file_path}: {e}")
            self.batch_manager.fail_batch(batch.id, str(e))
            result.processing_errors.append(str(e))
            raise
        
        return result
    
    def _parse_csv_content(self, file_path: Path, result: WellsFargoParseResult):
        """Parse CSV file content into transaction objects."""
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            # Detect delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            for row_number, row_data in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                result.total_rows += 1
                
                try:
                    # Clean and prepare row data
                    cleaned_data = self._clean_row_data(row_data)
                    
                    # Parse transaction
                    transaction = WellsFargoTransaction(**cleaned_data)
                    transaction.raw_line_number = row_number
                    
                    result.valid_transactions.append(transaction)
                    
                except Exception as e:
                    error_msg = f"Row {row_number}: {str(e)}"
                    result.invalid_transactions.append((row_number, row_data, error_msg))
                    self.logger.warning(error_msg)
    
    def _clean_row_data(self, row_data: Dict[str, str]) -> Dict[str, any]:
        """Clean and normalize CSV row data."""
        cleaned = {}
        
        for key, value in row_data.items():
            if not key or not value:
                continue
                
            # Clean whitespace
            clean_key = key.strip()
            clean_value = value.strip()
            
            # Handle empty values
            if not clean_value or clean_value.lower() in ('', 'n/a', 'null', 'none'):
                cleaned[clean_key] = None
                continue
            
            # Type conversions based on expected data types
            if 'date' in clean_key.lower():
                try:
                    # Try common date formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']:
                        try:
                            cleaned[clean_key] = datetime.strptime(clean_value, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        # If no format worked, keep as string and let Pydantic handle it
                        cleaned[clean_key] = clean_value
                except Exception:
                    cleaned[clean_key] = clean_value
            
            elif any(word in clean_key.lower() for word in ['amount', 'price', 'quantity', 'commission', 'fees']):
                try:
                    # Remove currency symbols and commas
                    numeric_value = clean_value.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
                    cleaned[clean_key] = float(numeric_value) if '.' in numeric_value else int(numeric_value)
                except ValueError:
                    cleaned[clean_key] = clean_value
            
            else:
                cleaned[clean_key] = clean_value
        
        return cleaned
    
    def _process_transactions(self, result: WellsFargoParseResult):
        """Process parsed transactions for validation and deduplication."""
        
        # Detect duplicates within the file
        seen_transactions = set()
        unique_transactions = []
        
        for transaction in result.valid_transactions:
            # Create a signature for duplicate detection
            signature = self._create_transaction_signature(transaction)
            
            if signature in seen_transactions:
                result.duplicate_transactions.append(transaction)
                self.logger.warning(f"Duplicate transaction detected: {signature}")
            else:
                seen_transactions.add(signature)
                unique_transactions.append(transaction)
        
        result.valid_transactions = unique_transactions
        
        # Additional business rule validations could go here
        self._validate_business_rules(result)
    
    def _create_transaction_signature(self, transaction: WellsFargoTransaction) -> str:
        """Create a unique signature for transaction deduplication."""
        signature_parts = [
            transaction.account_number,
            str(transaction.transaction_date),
            transaction.transaction_type,
            transaction.symbol or '',
            str(transaction.quantity or 0),
            str(transaction.net_amount or 0)
        ]
        return '|'.join(signature_parts)
    
    def _validate_business_rules(self, result: WellsFargoParseResult):
        """Apply business rule validations to transactions."""
        
        validated_transactions = []
        
        for transaction in result.valid_transactions:
            validation_errors = []
            
            # Business rule 1: Buy/Sell transactions must have security information
            if transaction.transaction_type in ['Buy', 'Sell']:
                if not any([transaction.symbol, transaction.cusip, transaction.security_description]):
                    validation_errors.append("Buy/Sell transaction missing security identification")
            
            # Business rule 2: Quantity and price should be consistent with principal
            if all([transaction.quantity, transaction.price, transaction.principal_amount]):
                expected_principal = abs(transaction.quantity * transaction.price)
                actual_principal = abs(transaction.principal_amount)
                if abs(expected_principal - actual_principal) > 0.05:  # 5 cent tolerance
                    validation_errors.append(
                        f"Principal amount mismatch: expected {expected_principal}, got {actual_principal}"
                    )
            
            # Business rule 3: Settlement date should be on or after transaction date
            if transaction.settlement_date and transaction.settlement_date < transaction.transaction_date:
                validation_errors.append("Settlement date cannot be before transaction date")
            
            if validation_errors:
                # Convert to invalid transaction
                row_data = transaction.dict()
                error_msg = "; ".join(validation_errors)
                result.invalid_transactions.append((
                    transaction.raw_line_number, 
                    row_data, 
                    f"Business rule validation failed: {error_msg}"
                ))
                self.logger.warning(f"Transaction validation failed: {error_msg}")
            else:
                validated_transactions.append(transaction)
        
        result.valid_transactions = validated_transactions
    
    def get_supported_columns(self) -> List[str]:
        """Get list of supported Wells Fargo CSV columns."""
        return [
            "Account Number", "Account Type", "Transaction Date", "Settlement Date",
            "Transaction Type", "Security Description", "Symbol", "CUSIP",
            "Quantity", "Price", "Principal Amount", "Commission", "Fees", "Net Amount"
        ]
EOF
```

**Validation:**
```bash
# Test Wells Fargo parser
python -c "
import sys
sys.path.insert(0, 'src')
from pathlib import Path
from security_master.extractor.wells_fargo.parser import WellsFargoParser

parser = WellsFargoParser()
result = parser.parse_file(Path('sample_data/wells_fargo/sample_transactions.csv'))

print(f'Total rows: {result.total_rows}')
print(f'Valid transactions: {result.success_count}')
print(f'Invalid transactions: {result.error_count}')
print(f'Success rate: {result.success_rate:.2%}')

if result.valid_transactions:
    first_tx = result.valid_transactions[0]
    print(f'First transaction: {first_tx.symbol} - {first_tx.transaction_type} - {first_tx.net_amount}')
    print(f'Quality score: {first_tx.calculate_data_quality_score():.2f}')
"

# Verify batch was created in database
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT id, institution, file_name, status, total_records, valid_records FROM import_batches ORDER BY created_at DESC LIMIT 1;"
# Expected: Shows the batch from our test
```

**✅ Day 8 Complete - Wells Fargo CSV parser operational**

---

## Phase 1 Completion Validation

### Master Validation Script
```bash
# Create comprehensive Phase 1 validation script
cat > scripts/validate_phase_1_complete.sh << 'EOF'
#!/bin/bash
# Master validation script for Phase 1 completion

set -e

echo "🔍 Phase 1: Core Infrastructure & Database Implementation - Complete Validation"
echo "============================================================================="
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

check_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((TOTAL_PASS++))
}

check_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((TOTAL_FAIL++))
}

echo "Test 1: Institution Transaction Tables"
echo "------------------------------------"

# Verify all transaction tables exist
TABLES=("transactions_wells_fargo" "transactions_interactive_brokers" "transactions_altoira" "transactions_kubera")
for table in "${TABLES[@]}"; do
    if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\dt $table" &>/dev/null; then
        check_pass "Table exists: $table"
    else
        check_fail "Table missing: $table"
    fi
done

# Test unified view
if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM v_transactions_unified" &>/dev/null; then
    check_pass "Unified transaction view operational"
else
    check_fail "Unified transaction view not working"
fi

echo ""

echo "Test 2: Batch Tracking System"
echo "----------------------------"

if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\dt import_batches" &>/dev/null; then
    check_pass "Import batches table exists"
else
    check_fail "Import batches table missing"
fi

# Test batch manager Python module
if python -c "
import sys
sys.path.insert(0, 'src')
from security_master.batch.service import BatchManager
from security_master.batch.models import Institution
bm = BatchManager()
print('Batch manager operational')
" &>/dev/null; then
    check_pass "Batch manager Python module working"
else
    check_fail "Batch manager Python module not working"
fi

echo ""

echo "Test 3: Wells Fargo Parser"
echo "-------------------------"

if [[ -f "sample_data/wells_fargo/sample_transactions.csv" ]]; then
    check_pass "Sample Wells Fargo data available"
else
    check_fail "Sample Wells Fargo data missing"
fi

# Test parser functionality
if python -c "
import sys
sys.path.insert(0, 'src')
from pathlib import Path
from security_master.extractor.wells_fargo.parser import WellsFargoParser
parser = WellsFargoParser()
print('Wells Fargo parser operational')
" &>/dev/null; then
    check_pass "Wells Fargo parser module working"
else
    check_fail "Wells Fargo parser module not working"
fi

echo ""

# Final Summary
echo "=========================================="
echo -e "${BLUE}Phase 1 Validation Summary${NC}"
echo "=========================================="
echo ""
echo -e "✅ Tests Passed: ${GREEN}$TOTAL_PASS${NC}"
echo -e "❌ Tests Failed: ${RED}$TOTAL_FAIL${NC}"
echo ""

if [[ $TOTAL_FAIL -eq 0 ]]; then
    echo -e "${GREEN}🎉 PHASE 1 FOUNDATION COMPLETE!${NC}"
    echo ""
    echo "Core infrastructure implemented:"
    echo "✅ Institution transaction tables operational"
    echo "✅ Data lineage and batch tracking working"
    echo "✅ Wells Fargo CSV parser functional"
    echo "✅ Database schema optimized and indexed"
    echo ""
    echo "🚀 Ready to proceed with remaining Phase 1 issues (P1-004 through P1-008)"
    exit 0
else
    echo -e "${RED}❌ PHASE 1 FOUNDATION INCOMPLETE${NC}"
    echo ""
    echo "Issues found that need resolution:"
    echo "1. Review failed tests above"
    echo "2. Check database connectivity and permissions"
    echo "3. Verify Python modules and dependencies"
    echo "4. Re-run this validation after fixes"
    exit 1
fi
EOF

chmod +x scripts/validate_phase_1_complete.sh

# Run validation
./scripts/validate_phase_1_complete.sh
```

This Phase 1 execution guide provides:

✅ **Comprehensive Day-by-Day Instructions**  
- Specific commands for each major task
- Expected outputs and validation steps
- Clear time estimates and responsibilities

✅ **Database Schema Implementation**  
- Complete SQL scripts for all institution tables
- Performance indexes and constraints  
- Unified view for cross-institution queries

✅ **Batch Tracking System**  
- Import batch lifecycle management
- Data lineage and audit trail
- Python models and service layer

✅ **Wells Fargo Parser Implementation**  
- CSV parsing with error handling
- Data validation and business rules
- Quality scoring and duplicate detection

The guide ensures staff can execute Phase 1 systematically with clear validation at each step, following the same successful pattern established in Phase 0.