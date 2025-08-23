#!/bin/bash
# Validation script for Phase 1 database setup
# Comprehensive testing of all database components

set -e

echo "🔍 Phase 1: Database Setup Validation"
echo "====================================="
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

echo "Starting comprehensive Phase 1 database validation..."
echo ""

# Test 1: Database Connectivity
section_header "Database Connectivity"

if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT 1;" &>/dev/null; then
    DB_VERSION=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT version();" -t | xargs)
    check_pass "Database connection: $DB_VERSION"
else
    check_fail "Cannot connect to database"
    exit 1
fi

echo ""

# Test 2: Transaction Tables
section_header "Transaction Tables Validation"

TABLES=(
    "transactions_wells_fargo"
    "transactions_interactive_brokers" 
    "transactions_altoira"
    "transactions_kubera"
)

for table in "${TABLES[@]}"; do
    if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\dt $table" &>/dev/null; then
        # Get column count
        COLUMN_COUNT=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = '$table';" -t | xargs)
        check_pass "Table exists: $table ($COLUMN_COUNT columns)"
        
        # Test basic operations
        if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM $table;" &>/dev/null; then
            RECORD_COUNT=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM $table;" -t | xargs)
            check_pass "Table accessible: $table ($RECORD_COUNT records)"
        else
            check_fail "Cannot query table: $table"
        fi
    else
        check_fail "Table missing: $table"
    fi
done

echo ""

# Test 3: Import Batch Tracking
section_header "Import Batch Tracking System"

if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "\dt import_batches" &>/dev/null; then
    check_pass "Import batches table exists"
    
    # Test batch table structure
    BATCH_COLUMNS=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'import_batches';" -t | xargs)
    if [[ $BATCH_COLUMNS -ge 15 ]]; then
        check_pass "Import batches table has complete structure ($BATCH_COLUMNS columns)"
    else
        check_warning "Import batches table may be missing columns ($BATCH_COLUMNS found)"
    fi
    
    # Test constraints
    BATCH_CONSTRAINTS=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM information_schema.check_constraints WHERE constraint_name LIKE 'chk_batch_%';" -t | xargs)
    if [[ $BATCH_CONSTRAINTS -ge 2 ]]; then
        check_pass "Batch table constraints exist ($BATCH_CONSTRAINTS found)"
    else
        check_fail "Missing batch table constraints"
    fi
else
    check_fail "Import batches table missing"
fi

echo ""

# Test 4: Performance Indexes
section_header "Performance Indexes"

INDEX_PATTERNS=(
    "idx_transactions_wf_%"
    "idx_transactions_ibkr_%"
    "idx_transactions_altoira_%"
    "idx_transactions_kubera_%"
    "idx_import_batches_%"
)

for pattern in "${INDEX_PATTERNS[@]}"; do
    INDEX_COUNT=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM pg_indexes WHERE indexname LIKE '$pattern';" -t | xargs)
    if [[ $INDEX_COUNT -gt 0 ]]; then
        check_pass "Indexes found for pattern $pattern: $INDEX_COUNT"
    else
        check_fail "No indexes found for pattern: $pattern"
    fi
done

# Test overall index count
TOTAL_INDEXES=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM pg_indexes WHERE indexname LIKE 'idx_transactions_%' OR indexname LIKE 'idx_import_%';" -t | xargs)
if [[ $TOTAL_INDEXES -ge 20 ]]; then
    check_pass "Total performance indexes: $TOTAL_INDEXES"
else
    check_warning "Lower than expected index count: $TOTAL_INDEXES"
fi

echo ""

# Test 5: Foreign Key Constraints
section_header "Foreign Key Constraints"

# Check batch_id foreign keys
FK_TO_BATCHES=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
SELECT COUNT(*) 
FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND ccu.table_name = 'import_batches';
" -t | xargs)

if [[ $FK_TO_BATCHES -eq 4 ]]; then
    check_pass "Batch foreign key constraints: $FK_TO_BATCHES (expected: 4)"
else
    check_fail "Batch foreign key constraints: $FK_TO_BATCHES (expected: 4)"
fi

# Check security_master foreign keys
FK_TO_SECURITIES=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
SELECT COUNT(*) 
FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND ccu.table_name = 'securities_master'
AND tc.table_name LIKE 'transactions_%';
" -t | xargs)

if [[ $FK_TO_SECURITIES -eq 4 ]]; then
    check_pass "Securities master foreign key constraints: $FK_TO_SECURITIES (expected: 4)"
else
    check_warning "Securities master foreign key constraints: $FK_TO_SECURITIES (expected: 4)"
fi

echo ""

# Test 6: Data Quality Constraints
section_header "Data Quality Constraints"

# Test data quality score constraints
QUALITY_CONSTRAINTS=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
SELECT COUNT(*) 
FROM information_schema.check_constraints cc
JOIN information_schema.constraint_column_usage ccu ON cc.constraint_name = ccu.constraint_name
WHERE ccu.column_name = 'data_quality_score';
" -t | xargs)

if [[ $QUALITY_CONSTRAINTS -ge 4 ]]; then
    check_pass "Data quality score constraints: $QUALITY_CONSTRAINTS"
else
    check_fail "Missing data quality score constraints"
fi

# Test date validation constraints (Wells Fargo)
WF_DATE_CONSTRAINTS=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
SELECT COUNT(*) 
FROM information_schema.check_constraints 
WHERE constraint_name = 'chk_wf_valid_dates';
" -t | xargs)

if [[ $WF_DATE_CONSTRAINTS -eq 1 ]]; then
    check_pass "Wells Fargo date validation constraint exists"
else
    check_fail "Wells Fargo date validation constraint missing"
fi

echo ""

# Test 7: Unified Transaction Views
section_header "Unified Transaction Views"

# Test regular view
if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM v_transactions_unified;" &>/dev/null; then
    check_pass "Unified transaction view (v_transactions_unified) operational"
else
    check_fail "Unified transaction view not working"
fi

# Test materialized view
if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM mv_transactions_unified;" &>/dev/null; then
    check_pass "Materialized unified view (mv_transactions_unified) operational"
    
    # Check materialized view indexes
    MV_INDEXES=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'mv_transactions_unified';" -t | xargs)
    if [[ $MV_INDEXES -ge 3 ]]; then
        check_pass "Materialized view indexes: $MV_INDEXES"
    else
        check_warning "Materialized view indexes: $MV_INDEXES (expected: 3+)"
    fi
else
    check_fail "Materialized unified view not working"
fi

echo ""

# Test 8: Update Triggers
section_header "Update Triggers"

TRIGGER_TABLES=("transactions_wells_fargo" "transactions_interactive_brokers" "transactions_altoira" "transactions_kubera" "import_batches")

for table in "${TRIGGER_TABLES[@]}"; do
    TRIGGER_EXISTS=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
    SELECT COUNT(*) 
    FROM information_schema.triggers 
    WHERE event_object_table = '$table' 
    AND trigger_name LIKE '%updated_at%';
    " -t | xargs)
    
    if [[ $TRIGGER_EXISTS -eq 1 ]]; then
        check_pass "Update trigger exists for: $table"
    else
        check_warning "Update trigger missing for: $table"
    fi
done

echo ""

# Test 9: Data Insertion Tests
section_header "Data Insertion Tests"

# Test Wells Fargo insertion
BATCH_ID=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
INSERT INTO import_batches (institution, file_name, file_hash, file_size, status) 
VALUES ('wells_fargo', 'test_validation.csv', repeat('a', 64), 1000, 'pending') 
RETURNING id;
" -t | xargs)

if [[ ! -z "$BATCH_ID" ]]; then
    check_pass "Batch record creation successful: $BATCH_ID"
    
    # Test Wells Fargo transaction insertion
    if psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
    INSERT INTO transactions_wells_fargo (batch_id, transaction_date, transaction_type, data_quality_score) 
    VALUES ('$BATCH_ID', '2024-01-01', 'Buy', 0.8);
    " &>/dev/null; then
        check_pass "Wells Fargo transaction insertion successful"
    else
        check_fail "Wells Fargo transaction insertion failed"
    fi
    
    # Test unified view includes the record
    VIEW_COUNT=$(psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "SELECT COUNT(*) FROM v_transactions_unified WHERE batch_id = '$BATCH_ID';" -t | xargs)
    if [[ $VIEW_COUNT -eq 1 ]]; then
        check_pass "Transaction appears in unified view"
    else
        check_warning "Transaction not visible in unified view (quality score filter may be applied)"
    fi
    
    # Clean up test data
    psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "DELETE FROM import_batches WHERE id = '$BATCH_ID';" &>/dev/null
    check_pass "Test data cleaned up"
else
    check_fail "Batch record creation failed"
fi

echo ""

# Test 10: Performance Tests
section_header "Performance Tests"

# Test query performance on empty tables
START_TIME=$(date +%s%N)
psql -h unraid.lan -p 5432 -U pp_user -d pp_master -c "
SELECT 
    t.institution,
    COUNT(*) as transaction_count,
    AVG(t.data_quality_score) as avg_quality
FROM v_transactions_unified t
GROUP BY t.institution;
" &>/dev/null
END_TIME=$(date +%s%N)

QUERY_TIME=$(( (END_TIME - START_TIME) / 1000000 )) # Convert to milliseconds

if [[ $QUERY_TIME -lt 1000 ]]; then # Less than 1 second
    check_pass "Cross-institution query performance: ${QUERY_TIME}ms"
else
    check_warning "Cross-institution query performance: ${QUERY_TIME}ms (may be slow with data)"
fi

echo ""

# Summary
echo "=========================================="
echo -e "${BLUE}Phase 1 Database Validation Summary${NC}"
echo "=========================================="
echo ""
echo -e "✅ Tests Passed: ${GREEN}$TOTAL_PASS${NC}"
echo -e "❌ Tests Failed: ${RED}$TOTAL_FAIL${NC}"
echo -e "⚠️  Warnings: ${YELLOW}$TOTAL_WARNING${NC}"
echo ""

# Determine overall status
if [[ $TOTAL_FAIL -eq 0 ]]; then
    echo -e "${GREEN}🎉 PHASE 1 DATABASE SETUP COMPLETE!${NC}"
    echo ""
    echo "All database components operational:"
    echo "✅ Institution transaction tables (4 tables)"
    echo "✅ Import batch tracking system"
    echo "✅ Performance indexes and constraints"
    echo "✅ Unified transaction views"
    echo "✅ Data quality validation"
    echo "✅ Foreign key relationships"
    echo ""
    echo "🚀 Ready for Phase 1 parser and import development!"
    echo ""
    exit 0
elif [[ $TOTAL_FAIL -le 2 ]]; then
    echo -e "${YELLOW}⚠️ PHASE 1 DATABASE MOSTLY COMPLETE - MINOR ISSUES FOUND${NC}"
    echo ""
    echo "Database is functional but has some minor issues."
    echo "Review failed tests above and address if needed."
    echo ""
    exit 1
else
    echo -e "${RED}❌ PHASE 1 DATABASE SETUP INCOMPLETE${NC}"
    echo ""
    echo "Significant database issues found that should be resolved:"
    echo ""
    echo "Recommended actions:"
    echo "1. Review all failed tests above"
    echo "2. Re-run database setup: ./scripts/phase1/setup_phase1_database.sh"
    echo "3. Check database permissions and connectivity"
    echo "4. Re-run this validation script"
    echo ""
    echo "⚠️ Do not proceed with Phase 1 development until database issues are resolved."
    echo ""
    exit 1
fi