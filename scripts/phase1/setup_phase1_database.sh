#!/bin/bash
# Phase 1 Database Setup Script
# Automates the complete database schema setup for Phase 1

set -e

echo "🚀 Phase 1: Database Schema Setup"
echo "=================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Verify Phase 0 is complete
if ! ./scripts/validate_phase_0_complete.sh &>/dev/null; then
    print_error "Phase 0 must be completed before running Phase 1 setup"
    echo "Please run: ./scripts/validate_phase_0_complete.sh"
    exit 1
fi

print_info "Phase 0 validation passed - proceeding with Phase 1 setup"
echo ""

# Step 1: Create Phase 1 schema directory
echo "Step 1: Creating Phase 1 Schema Structure"
echo "----------------------------------------"

mkdir -p sql/phase1
print_status "Phase 1 SQL directory created"

# Step 2: Test database connection
echo ""
echo "Step 2: Testing Database Connection"
echo "----------------------------------"

if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT 1;" &>/dev/null; then
    DB_VERSION=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT version();" -t | xargs)
    print_status "Database connection successful: $DB_VERSION"
else
    print_error "Cannot connect to database. Check connection settings."
    exit 1
fi

# Step 3: Create Wells Fargo transaction table
echo ""
echo "Step 3: Creating Wells Fargo Transaction Table"
echo "---------------------------------------------"

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

-- Update trigger
DROP TRIGGER IF EXISTS update_transactions_wf_updated_at ON transactions_wells_fargo;
CREATE TRIGGER update_transactions_wf_updated_at 
    BEFORE UPDATE ON transactions_wells_fargo 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
EOF

psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/002_create_wells_fargo_transactions.sql
print_status "Wells Fargo transaction table created with indexes and constraints"

# Step 4: Create Interactive Brokers transaction table
echo ""
echo "Step 4: Creating Interactive Brokers Transaction Table"
echo "----------------------------------------------------"

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

-- Update trigger
DROP TRIGGER IF EXISTS update_transactions_ibkr_updated_at ON transactions_interactive_brokers;
CREATE TRIGGER update_transactions_ibkr_updated_at 
    BEFORE UPDATE ON transactions_interactive_brokers 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
EOF

psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/003_create_ibkr_transactions.sql
print_status "Interactive Brokers transaction table created with indexes"

# Step 5: Create AltoIRA transaction table
echo ""
echo "Step 5: Creating AltoIRA Transaction Table"
echo "----------------------------------------"

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

-- Update trigger
DROP TRIGGER IF EXISTS update_transactions_altoira_updated_at ON transactions_altoira;
CREATE TRIGGER update_transactions_altoira_updated_at 
    BEFORE UPDATE ON transactions_altoira 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
EOF

psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/004_create_altoira_transactions.sql
print_status "AltoIRA transaction table created with OCR confidence tracking"

# Step 6: Create Kubera transaction table
echo ""
echo "Step 6: Creating Kubera Transaction Table"
echo "---------------------------------------"

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

-- Update trigger
DROP TRIGGER IF EXISTS update_transactions_kubera_updated_at ON transactions_kubera;
CREATE TRIGGER update_transactions_kubera_updated_at 
    BEFORE UPDATE ON transactions_kubera 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
EOF

psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/005_create_kubera_transactions.sql
print_status "Kubera transaction table created with multi-currency support"

# Step 7: Create import batch tracking table
echo ""
echo "Step 7: Creating Import Batch Tracking System"
echo "--------------------------------------------"

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

-- Update trigger
DROP TRIGGER IF EXISTS update_import_batches_updated_at ON import_batches;
CREATE TRIGGER update_import_batches_updated_at 
    BEFORE UPDATE ON import_batches 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
EOF

psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/007_create_import_batches.sql
print_status "Import batch tracking system created"

# Step 8: Add foreign key constraints
echo ""
echo "Step 8: Adding Foreign Key Constraints"
echo "-------------------------------------"

psql -h unraid.lan -p 5432 -U pp_user -d pp_master << 'EOF'
-- Add batch_id foreign key constraints
ALTER TABLE transactions_wells_fargo 
DROP CONSTRAINT IF EXISTS fk_wf_batch_id;
ALTER TABLE transactions_wells_fargo 
ADD CONSTRAINT fk_wf_batch_id 
FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE CASCADE;

ALTER TABLE transactions_interactive_brokers 
DROP CONSTRAINT IF EXISTS fk_ibkr_batch_id;
ALTER TABLE transactions_interactive_brokers 
ADD CONSTRAINT fk_ibkr_batch_id 
FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE CASCADE;

ALTER TABLE transactions_altoira 
DROP CONSTRAINT IF EXISTS fk_altoira_batch_id;
ALTER TABLE transactions_altoira 
ADD CONSTRAINT fk_altoira_batch_id 
FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE CASCADE;

ALTER TABLE transactions_kubera 
DROP CONSTRAINT IF EXISTS fk_kubera_batch_id;
ALTER TABLE transactions_kubera 
ADD CONSTRAINT fk_kubera_batch_id 
FOREIGN KEY (batch_id) REFERENCES import_batches(id) ON DELETE CASCADE;
EOF

print_status "Foreign key constraints added for data lineage"

# Step 9: Create unified transaction view
echo ""
echo "Step 9: Creating Unified Transaction View"
echo "---------------------------------------"

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
DROP MATERIALIZED VIEW IF EXISTS mv_transactions_unified;
CREATE MATERIALIZED VIEW mv_transactions_unified AS
SELECT * FROM v_transactions_unified;

-- Index on materialized view
CREATE INDEX IF NOT EXISTS idx_mv_transactions_institution ON mv_transactions_unified(institution);
CREATE INDEX IF NOT EXISTS idx_mv_transactions_date ON mv_transactions_unified(transaction_date);
CREATE INDEX IF NOT EXISTS idx_mv_transactions_symbol ON mv_transactions_unified(symbol);
EOF

psql -h unraid.lan -p 5432 -U pp_user -d pp_master -f sql/phase1/006_create_common_transaction_view.sql
print_status "Unified transaction view created with materialized view for performance"

# Step 10: Validate setup
echo ""
echo "Step 10: Validating Database Setup"
echo "--------------------------------"

# Check all tables exist
TABLES=("transactions_wells_fargo" "transactions_interactive_brokers" "transactions_altoira" "transactions_kubera" "import_batches")
for table in "${TABLES[@]}"; do
    if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\dt $table" &>/dev/null; then
        print_status "Table verified: $table"
    else
        print_error "Table missing: $table"
    fi
done

# Check unified view
if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM v_transactions_unified" &>/dev/null; then
    print_status "Unified view operational"
else
    print_error "Unified view not working"
fi

# Check indexes
INDEX_COUNT=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM pg_indexes WHERE indexname LIKE 'idx_transactions_%';" -t | xargs)
print_status "Performance indexes created: $INDEX_COUNT"

# Check constraints
CONSTRAINT_COUNT=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY' AND table_name LIKE 'transactions_%';" -t | xargs)
print_status "Foreign key constraints: $CONSTRAINT_COUNT"

echo ""
echo "🎉 Phase 1 Database Setup Complete!"
echo "===================================="
echo ""
echo "Database schema successfully created:"
echo "✅ Institution transaction tables (4 tables)"
echo "✅ Import batch tracking system"
echo "✅ Unified transaction view with materialization"
echo "✅ Performance indexes and constraints"
echo "✅ Data lineage and audit capabilities"
echo ""
echo "Next steps:"
echo "1. Proceed with Wells Fargo parser implementation"
echo "2. Test with sample CSV data"
echo "3. Implement remaining Phase 1 issues (P1-004 through P1-008)"
echo "4. Run validation: ./scripts/phase1/validate_phase1_database.sh"
echo ""
print_status "Phase 1 database foundation ready for development!"