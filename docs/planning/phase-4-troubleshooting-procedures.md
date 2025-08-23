# Phase 4 Troubleshooting Procedures
## Analytics and Portfolio Performance Integration

Comprehensive troubleshooting guide for Phase 4 implementation issues, including diagnostics, solutions, and prevention strategies.

## Common Issues and Solutions

### Database Issues

#### Issue: Benchmark Security Tables Not Created
**Symptoms:**
- `relation "benchmark_securities" does not exist` error
- Missing benchmark functionality in CLI
- Analytics queries failing

**Diagnosis:**
```bash
# Check if tables exist
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('''SELECT table_name FROM information_schema.tables 
                  WHERE table_schema = 'public' AND table_name LIKE '%benchmark%' ''')
    tables = [row[0] for row in cur.fetchall()]
    print('Benchmark tables found:', tables)
"
```

**Solutions:**
```bash
# Re-run benchmark schema creation
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
with open('sql/phase4/benchmark_security_tables.sql', 'r') as f:
    sql = f.read()
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute(sql)
    conn.commit()
    print('✅ Benchmark tables created')
"

# Alternative: Run full Phase 4 setup
bash scripts/phase4/setup_analytics_pp_integration.sh
```

**Prevention:**
- Always validate database schema after migration
- Use transaction blocks for schema changes
- Maintain schema version tracking

#### Issue: Analytics Views Missing or Broken
**Symptoms:**
- `relation "vw_portfolio_analytics" does not exist`
- Analytics queries returning empty results
- Performance degradation in analytics queries

**Diagnosis:**
```bash
# Check analytics views
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('''SELECT table_name FROM information_schema.views 
                  WHERE table_schema = 'public' AND table_name LIKE 'vw_%' ''')
    views = [row[0] for row in cur.fetchall()]
    print('Analytics views found:', views)
    
    # Test a specific view
    try:
        cur.execute('SELECT COUNT(*) FROM vw_portfolio_analytics LIMIT 1')
        print('✅ vw_portfolio_analytics is accessible')
    except Exception as e:
        print('❌ vw_portfolio_analytics error:', e)
"
```

**Solutions:**
```bash
# Recreate analytics views
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
with open('sql/phase4/analytics_views.sql', 'r') as f:
    sql = f.read()
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute(sql)
    conn.commit()
    print('✅ Analytics views recreated')
"

# Drop and recreate specific problematic view
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('DROP VIEW IF EXISTS vw_portfolio_analytics CASCADE')
    # Re-run view creation SQL here
    conn.commit()
"
```

**Prevention:**
- Regular view performance monitoring
- Dependency tracking for view recreation
- Backup view definitions before changes

#### Issue: Database Connection Pool Exhaustion
**Symptoms:**
- `connection pool exhausted` errors
- Analytics operations timing out
- High database connection count

**Diagnosis:**
```bash
# Check active connections
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('SELECT count(*) FROM pg_stat_activity')
    active_connections = cur.fetchone()[0]
    print(f'Active connections: {active_connections}')
    
    cur.execute('SHOW max_connections')
    max_connections = cur.fetchone()[0]
    print(f'Max connections: {max_connections}')
"

# Check connection pool configuration
grep -n "pool" src/security_master/storage/connection.py
```

**Solutions:**
```bash
# Increase connection pool size (temporary)
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=10

# Optimize connection usage in code
poetry run python -c "
# Close idle connections
from src.security_master.storage.connection import get_db_connection
import psycopg2
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('''SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
                  WHERE state = 'idle' AND state_change < now() - interval '1 hour' ''')
    terminated = cur.rowcount
    print(f'Terminated {terminated} idle connections')
"

# Long-term solution: Implement connection pooling
# Edit src/security_master/storage/connection.py to use connection pooling library
```

**Prevention:**
- Use context managers for database connections
- Implement connection pooling with libraries like pgbouncer
- Monitor connection usage regularly
- Set appropriate timeout values

### Benchmark Generation Issues

#### Issue: Benchmark Price Calculation Errors
**Symptoms:**
- Benchmark prices showing as 0 or NULL
- `validate_benchmark_price_consistency()` failing
- Incorrect benchmark performance metrics

**Diagnosis:**
```bash
# Check benchmark price history
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('''
        SELECT bs.security_uuid, COUNT(ph.date), MIN(ph.close_price), MAX(ph.close_price)
        FROM benchmark_securities bs
        JOIN securities_master sm ON bs.security_uuid = sm.uuid
        JOIN pp_price_history ph ON sm.id = ph.security_master_id
        GROUP BY bs.security_uuid
    ''')
    for row in cur.fetchall():
        print(f'Benchmark {row[0]}: {row[1]} prices, range {row[2]}-{row[3]}')
"

# Check underlying securities data
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('''
        SELECT bs.underlying_securities, bs.static_weights
        FROM benchmark_securities bs
        LIMIT 5
    ''')
    for row in cur.fetchall():
        securities = row[0] if row[0] else []
        weights = row[1] if row[1] else []
        print(f'Securities: {len(securities)}, Weights: {len(weights)}')
        if len(securities) != len(weights):
            print('❌ Securities/weights mismatch!')
"
```

**Solutions:**
```bash
# Recalculate benchmark prices
poetry run python -c "
from src.security_master.analytics.benchmark_generator import BenchmarkSecurityGenerator
from datetime import date
import uuid

generator = BenchmarkSecurityGenerator()

# Get problematic benchmark
from src.security_master.storage.connection import get_db_connection
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('SELECT security_uuid FROM benchmark_securities WHERE id = 1')
    benchmark_uuid = cur.fetchone()[0]
    
    # Trigger recalculation
    success = generator.update_benchmark_security(
        benchmark_uuid=benchmark_uuid,
        end_date=date.today()
    )
    print(f'Recalculation result: {success}')
"

# Fix weight normalization issues
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
from decimal import Decimal

conn = get_db_connection()
with conn.cursor() as cur:
    # Normalize weights to sum to 1.0
    cur.execute('''
        UPDATE benchmark_securities 
        SET static_weights = ARRAY(
            SELECT (weight / total_weight)::decimal(8,6)
            FROM UNNEST(static_weights) AS weight,
                 (SELECT SUM(w) FROM UNNEST(static_weights) AS w) AS total_weight
        )
        WHERE array_length(static_weights, 1) > 0
    ''')
    conn.commit()
    print('✅ Weights normalized')
"
```

**Prevention:**
- Always validate weights sum to 1.0 before benchmark creation
- Implement robust error handling in price calculations
- Use database constraints to prevent invalid configurations
- Regular validation of benchmark price consistency

#### Issue: Rebalancing Not Executing
**Symptoms:**
- Benchmark compositions not updating on schedule
- Portfolio weights drifting from target allocation
- Missing entries in `benchmark_rebalance_schedule`

**Diagnosis:**
```bash
# Check rebalancing schedule
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
from datetime import date, timedelta

conn = get_db_connection()
with conn.cursor() as cur:
    # Check scheduled rebalances
    cur.execute('''
        SELECT COUNT(*) FROM benchmark_rebalance_schedule 
        WHERE scheduled_date <= %s AND executed = false
    ''', (date.today(),))
    pending = cur.fetchone()[0]
    print(f'Pending rebalances: {pending}')
    
    # Check last executed rebalance
    cur.execute('''
        SELECT MAX(executed_at) FROM benchmark_rebalance_schedule 
        WHERE executed = true
    ''')
    last_rebalance = cur.fetchone()[0]
    print(f'Last rebalance: {last_rebalance}')
"
```

**Solutions:**
```bash
# Manual rebalancing execution
poetry run python -c "
from src.security_master.analytics.benchmark_generator import BenchmarkSecurityGenerator
from datetime import date

generator = BenchmarkSecurityGenerator()

# Get benchmarks needing rebalancing
from src.security_master.storage.connection import get_db_connection
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('''
        SELECT DISTINCT brs.benchmark_security_id, bs.security_uuid
        FROM benchmark_rebalance_schedule brs
        JOIN benchmark_securities bs ON brs.benchmark_security_id = bs.id
        WHERE brs.scheduled_date <= %s AND brs.executed = false
    ''', (date.today(),))
    
    for row in cur.fetchall():
        benchmark_id, benchmark_uuid = row
        # Execute rebalancing logic here
        print(f'Processing rebalance for benchmark {benchmark_uuid}')
"

# Set up automated rebalancing
cat > scripts/automated_rebalancing.sh << 'EOF'
#!/bin/bash
# Automated benchmark rebalancing script
poetry run python -c "
from src.security_master.analytics.benchmark_generator import BenchmarkSecurityGenerator
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
generator = BenchmarkSecurityGenerator()

# Execute pending rebalances
pending_count = generator.execute_pending_rebalances()
print(f'Executed {pending_count} pending rebalances')
"
EOF

chmod +x scripts/automated_rebalancing.sh
```

**Prevention:**
- Set up scheduled cron jobs for rebalancing
- Implement monitoring for missed rebalances
- Add alerting for rebalancing failures
- Maintain rebalancing execution logs

### Portfolio Performance Integration Issues

#### Issue: XML Export Validation Failures
**Symptoms:**
- Portfolio Performance rejects XML imports
- XML validation errors during export
- Missing required elements in generated XML

**Diagnosis:**
```bash
# Validate XML structure
poetry run python -c "
from src.security_master.pp_integration.xml_generator import PPXMLGenerator
from xml.etree.ElementTree import XML
import xmlschema

generator = PPXMLGenerator()
xml_data = generator.generate_client_xml('test-client-123')

try:
    # Basic XML parsing
    root = XML(xml_data)
    print('✅ XML is well-formed')
    
    # Check required elements
    required_elements = ['client', 'securities', 'accounts', 'portfolios']
    for element in required_elements:
        if root.find(f'.//{element}') is not None:
            print(f'✅ {element} element found')
        else:
            print(f'❌ {element} element missing')
            
except Exception as e:
    print(f'❌ XML parsing error: {e}')
"

# Check for character encoding issues
poetry run python -c "
xml_file = 'test_export.xml'
with open(xml_file, 'r', encoding='utf-8') as f:
    content = f.read()
    # Check for invalid characters
    invalid_chars = [char for char in content if ord(char) < 32 and char not in ['\t', '\n', '\r']]
    if invalid_chars:
        print(f'❌ Found {len(invalid_chars)} invalid characters')
    else:
        print('✅ No invalid characters found')
"
```

**Solutions:**
```bash
# Fix XML encoding issues
poetry run python -c "
import re
from src.security_master.pp_integration.xml_generator import PPXMLGenerator

class FixedPPXMLGenerator(PPXMLGenerator):
    def _sanitize_text(self, text):
        if not text:
            return text
        # Remove invalid XML characters
        valid_chars = []
        for char in text:
            if ord(char) >= 32 or char in ['\t', '\n', '\r']:
                valid_chars.append(char)
        return ''.join(valid_chars)
    
    def _create_text_element(self, parent, tag, text):
        element = SubElement(parent, tag)
        element.text = self._sanitize_text(str(text)) if text else ''
        return element

# Replace original generator with fixed version
generator = FixedPPXMLGenerator()
xml_data = generator.generate_client_xml('test-client-123')
print('✅ XML generated with sanitized text')
"

# Add XML schema validation
poetry add lxml xmlschema
poetry run python -c "
import xmlschema
from src.security_master.pp_integration.xml_generator import PPXMLGenerator

# Download Portfolio Performance XSD schema if available
# For now, basic structure validation
generator = PPXMLGenerator()
xml_data = generator.generate_client_xml('test-client-123')

# Write to file for manual validation in Portfolio Performance
with open('validated_export.xml', 'w', encoding='utf-8') as f:
    f.write('<?xml version=\"1.0\" encoding=\"UTF-8\"?>\\n')
    f.write(xml_data)
print('✅ XML written with proper declaration')
"
```

**Prevention:**
- Implement comprehensive XML schema validation
- Use character encoding validation in export pipeline
- Test exports with actual Portfolio Performance imports
- Maintain sample valid XML files for reference

#### Issue: Synthetic Benchmark Securities Not Appearing in Portfolio Performance
**Symptoms:**
- Exported benchmarks missing from PP securities list
- Benchmark securities show as invalid or unknown
- Performance comparison not working in PP

**Diagnosis:**
```bash
# Check synthetic benchmark export
poetry run python -c "
from src.security_master.storage.connection import get_db_connection

conn = get_db_connection()
with conn.cursor() as cur:
    # Check synthetic benchmark securities
    cur.execute('''
        SELECT sm.uuid, sm.symbol, sm.name, sm.isin, sm.is_synthetic_benchmark
        FROM securities_master sm
        WHERE sm.is_synthetic_benchmark = true
    ''')
    
    benchmarks = cur.fetchall()
    print(f'Found {len(benchmarks)} synthetic benchmarks:')
    for benchmark in benchmarks:
        print(f'  {benchmark[1]} ({benchmark[0]}): {benchmark[2]}')
        
        # Check price history
        cur.execute('''
            SELECT COUNT(*) FROM pp_price_history ph
            WHERE ph.security_master_id = (
                SELECT id FROM securities_master WHERE uuid = %s
            )
        ''', (benchmark[0],))
        price_count = cur.fetchone()[0]
        print(f'    Price history: {price_count} points')
"
```

**Solutions:**
```bash
# Ensure proper ISIN format for synthetic securities
poetry run python -c "
from src.security_master.storage.connection import get_db_connection

conn = get_db_connection()
with conn.cursor() as cur:
    # Update ISIN format for synthetic benchmarks
    cur.execute('''
        UPDATE securities_master 
        SET isin = 'SYNTH' || UPPER(LEFT(symbol, 8))
        WHERE is_synthetic_benchmark = true AND (isin IS NULL OR isin = '')
    ''')
    updated = cur.rowcount
    conn.commit()
    print(f'✅ Updated ISIN for {updated} synthetic benchmarks')
    
    # Ensure all synthetic benchmarks have price history
    cur.execute('''
        SELECT sm.uuid, sm.symbol FROM securities_master sm
        WHERE sm.is_synthetic_benchmark = true
        AND NOT EXISTS (
            SELECT 1 FROM pp_price_history ph WHERE ph.security_master_id = sm.id
        )
    ''')
    
    missing_prices = cur.fetchall()
    for uuid, symbol in missing_prices:
        print(f'❌ {symbol} missing price history')
"

# Regenerate benchmark securities with proper metadata
poetry run python -c "
from src.security_master.analytics.benchmark_generator import BenchmarkSecurityGenerator
from datetime import date

generator = BenchmarkSecurityGenerator()

# Update existing benchmarks
from src.security_master.storage.connection import get_db_connection
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('SELECT security_uuid FROM benchmark_securities')
    benchmark_uuids = [row[0] for row in cur.fetchall()]
    
    for uuid in benchmark_uuids:
        success = generator.update_benchmark_security(uuid, end_date=date.today())
        print(f'Updated benchmark {uuid}: {success}')
"
```

**Prevention:**
- Standardize ISIN format for all synthetic securities
- Ensure complete price history before export
- Test actual import process in Portfolio Performance
- Maintain export validation checklist

### Analytics Performance Issues

#### Issue: Slow Analytics Queries
**Symptoms:**
- Portfolio metrics calculations timing out
- Analytics views taking > 30 seconds to execute
- High CPU usage on database server during analytics

**Diagnosis:**
```bash
# Check query performance
poetry run python -c "
import time
from src.security_master.storage.connection import get_db_connection

conn = get_db_connection()
with conn.cursor() as cur:
    # Test analytics view performance
    start_time = time.time()
    cur.execute('SELECT COUNT(*) FROM vw_portfolio_analytics')
    result = cur.fetchone()[0]
    duration = time.time() - start_time
    print(f'vw_portfolio_analytics: {result} rows in {duration:.2f}s')
    
    # Check for missing indexes
    cur.execute('''
        SELECT schemaname, tablename, indexname 
        FROM pg_indexes 
        WHERE tablename IN ('securities_master', 'pp_price_history', 'broker_transactions')
        ORDER BY tablename
    ''')
    indexes = cur.fetchall()
    print(f'Found {len(indexes)} indexes on core tables')
"

# Analyze query execution plans
poetry run python -c "
from src.security_master.storage.connection import get_db_connection

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute('EXPLAIN ANALYZE SELECT * FROM vw_portfolio_analytics LIMIT 100')
    plan = cur.fetchall()
    for row in plan:
        print(row[0])
"
```

**Solutions:**
```bash
# Add missing indexes
poetry run python -c "
from src.security_master.storage.connection import get_db_connection

conn = get_db_connection()
with conn.cursor() as cur:
    # Add common analytics indexes
    indexes_to_create = [
        'CREATE INDEX IF NOT EXISTS idx_pp_price_history_date_security ON pp_price_history(date, security_master_id)',
        'CREATE INDEX IF NOT EXISTS idx_broker_transactions_date_portfolio ON broker_transactions(transaction_date, portfolio_id)',
        'CREATE INDEX IF NOT EXISTS idx_securities_master_active ON securities_master(is_active) WHERE is_active = true',
        'CREATE INDEX IF NOT EXISTS idx_benchmark_performance_date ON benchmark_performance_attribution(attribution_date)',
    ]
    
    for index_sql in indexes_to_create:
        try:
            cur.execute(index_sql)
            print(f'✅ Created index: {index_sql.split()[-1]}')
        except Exception as e:
            print(f'❌ Index creation failed: {e}')
    
    conn.commit()
"

# Optimize analytics views
poetry run python -c "
from src.security_master.storage.connection import get_db_connection

# Replace slow views with optimized versions
optimized_view_sql = '''
DROP VIEW IF EXISTS vw_portfolio_analytics CASCADE;

CREATE VIEW vw_portfolio_analytics AS
SELECT 
    p.portfolio_id,
    p.portfolio_name,
    COUNT(DISTINCT bt.security_uuid) as security_count,
    SUM(bt.quantity * ph.close_price) as current_value,
    AVG(pa.sharpe_ratio) as avg_sharpe_ratio
FROM portfolios p
JOIN broker_transactions bt ON p.portfolio_id = bt.portfolio_id
JOIN securities_master sm ON bt.security_uuid = sm.uuid
JOIN LATERAL (
    SELECT close_price 
    FROM pp_price_history 
    WHERE security_master_id = sm.id 
    ORDER BY date DESC LIMIT 1
) ph ON true
LEFT JOIN portfolio_analytics pa ON p.portfolio_id = pa.portfolio_id
GROUP BY p.portfolio_id, p.portfolio_name;
'''

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute(optimized_view_sql)
    conn.commit()
    print('✅ Optimized analytics view created')
"
```

**Prevention:**
- Regular query performance monitoring
- Index usage analysis and optimization
- Implement query result caching
- Use materialized views for heavy computations
- Set up database performance alerts

#### Issue: Memory Issues with Large Datasets
**Symptoms:**
- Out of memory errors during benchmark generation
- Python processes consuming excessive RAM
- Analytics operations failing on large portfolios

**Diagnosis:**
```bash
# Monitor memory usage during operations
poetry run python -c "
import psutil
import gc
from src.security_master.analytics.benchmark_generator import BenchmarkSecurityGenerator

process = psutil.Process()
print(f'Initial memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')

generator = BenchmarkSecurityGenerator()

# Monitor memory during large operation
print('Creating large benchmark...')
memory_before = process.memory_info().rss / 1024 / 1024
print(f'Memory before benchmark: {memory_before:.1f} MB')

# Check for memory leaks
gc.collect()
memory_after_gc = process.memory_info().rss / 1024 / 1024
print(f'Memory after GC: {memory_after_gc:.1f} MB')
"
```

**Solutions:**
```bash
# Implement batch processing
poetry run python -c "
def process_large_dataset_in_batches(dataset, batch_size=1000):
    '''Process large datasets in smaller batches to prevent memory issues.'''
    for i in range(0, len(dataset), batch_size):
        batch = dataset[i:i + batch_size]
        yield batch
        
        # Force garbage collection after each batch
        import gc
        gc.collect()

# Example usage in benchmark generation
from src.security_master.analytics.benchmark_generator import BenchmarkSecurityGenerator
from datetime import date, timedelta

class OptimizedBenchmarkGenerator(BenchmarkSecurityGenerator):
    def _generate_price_history_batch(self, securities, start_date, end_date, batch_size=50):
        '''Generate price history in batches to manage memory.'''
        price_data = []
        
        for batch in process_large_dataset_in_batches(securities, batch_size):
            batch_data = self._calculate_batch_prices(batch, start_date, end_date)
            price_data.extend(batch_data)
            
        return price_data

print('✅ Batch processing implemented')
"

# Configure database connection pooling
poetry add psycopg2-pool
cat >> src/security_master/storage/connection.py << 'EOF'

from psycopg2 import pool

# Connection pool for memory management
connection_pool = None

def get_pooled_connection():
    global connection_pool
    if connection_pool is None:
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            1, 20,  # min and max connections
            host=os.getenv('DATABASE_HOST'),
            database=os.getenv('DATABASE_NAME'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD')
        )
    return connection_pool.getconn()

def return_pooled_connection(conn):
    global connection_pool
    if connection_pool:
        connection_pool.putconn(conn)
EOF
```

**Prevention:**
- Use streaming/batch processing for large datasets
- Implement proper connection pooling
- Monitor memory usage in production
- Set memory limits for analytics processes
- Use database cursors for large result sets

### Monitoring and Alerting Issues

#### Issue: Missing Phase 4 Monitoring
**Symptoms:**
- No visibility into benchmark generation health
- Analytics performance issues go unnoticed
- Failed exports not detected promptly

**Solutions:**
```bash
# Create comprehensive monitoring script
cat > scripts/phase4_health_check.py << 'EOF'
#!/usr/bin/env python3
"""Phase 4 system health monitoring script."""

import json
import time
from datetime import date, timedelta
from src.security_master.storage.connection import get_db_connection

def check_benchmark_health():
    """Check benchmark system health."""
    conn = get_db_connection()
    health = {
        'benchmark_securities_active': 0,
        'price_validation_failures': 0,
        'pending_rebalances': 0,
        'recent_benchmark_updates': 0
    }
    
    with conn.cursor() as cur:
        # Active benchmarks
        cur.execute('SELECT COUNT(*) FROM benchmark_securities WHERE is_active = true')
        health['benchmark_securities_active'] = cur.fetchone()[0]
        
        # Validation failures in last 24 hours
        cur.execute('''
            SELECT COUNT(*) FROM benchmark_quality_checks 
            WHERE passed = false AND created_at > NOW() - INTERVAL '24 hours'
        ''')
        health['price_validation_failures'] = cur.fetchone()[0]
        
        # Pending rebalances
        cur.execute('''
            SELECT COUNT(*) FROM benchmark_rebalance_schedule 
            WHERE executed = false AND scheduled_date <= %s
        ''', (date.today(),))
        health['pending_rebalances'] = cur.fetchone()[0]
        
        # Recent updates
        cur.execute('''
            SELECT COUNT(*) FROM benchmark_securities 
            WHERE last_calculated > %s
        ''', (date.today() - timedelta(days=7),))
        health['recent_benchmark_updates'] = cur.fetchone()[0]
    
    return health

def check_analytics_performance():
    """Check analytics query performance."""
    conn = get_db_connection()
    performance = {}
    
    # Test key analytics queries
    test_queries = {
        'portfolio_analytics': 'SELECT COUNT(*) FROM vw_portfolio_analytics',
        'security_performance': 'SELECT COUNT(*) FROM vw_security_performance_analytics',
        'benchmark_performance': 'SELECT COUNT(*) FROM vw_benchmark_performance_analytics'
    }
    
    with conn.cursor() as cur:
        for query_name, query_sql in test_queries.items():
            start_time = time.time()
            try:
                cur.execute(query_sql)
                result = cur.fetchone()[0]
                duration = time.time() - start_time
                performance[query_name] = {
                    'duration_seconds': round(duration, 2),
                    'result_count': result,
                    'status': 'healthy' if duration < 10 else 'slow'
                }
            except Exception as e:
                performance[query_name] = {
                    'duration_seconds': -1,
                    'error': str(e),
                    'status': 'error'
                }
    
    return performance

def check_pp_integration():
    """Check Portfolio Performance integration health."""
    from src.security_master.pp_integration.xml_generator import PPXMLGenerator
    
    integration_health = {
        'xml_generation': 'unknown',
        'synthetic_securities': 0,
        'export_errors': 0
    }
    
    try:
        generator = PPXMLGenerator()
        xml_data = generator.generate_client_xml('health-check-client')
        if len(xml_data) > 0 and '<client' in xml_data:
            integration_health['xml_generation'] = 'healthy'
        else:
            integration_health['xml_generation'] = 'error'
    except Exception as e:
        integration_health['xml_generation'] = f'error: {e}'
    
    # Count synthetic securities
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM securities_master WHERE is_synthetic_benchmark = true')
        integration_health['synthetic_securities'] = cur.fetchone()[0]
    
    return integration_health

def main():
    """Run complete Phase 4 health check."""
    print("🔍 Phase 4 Health Check")
    print("=" * 50)
    
    # Benchmark health
    benchmark_health = check_benchmark_health()
    print("📊 Benchmark System Health:")
    for metric, value in benchmark_health.items():
        status = "✅" if isinstance(value, int) and value >= 0 else "❌"
        print(f"   {status} {metric}: {value}")
    
    # Analytics performance
    analytics_performance = check_analytics_performance()
    print("\\n⚡ Analytics Performance:")
    for query, metrics in analytics_performance.items():
        status_icon = {"healthy": "✅", "slow": "⚠️", "error": "❌"}
        status = metrics.get('status', 'unknown')
        icon = status_icon.get(status, "❓")
        duration = metrics.get('duration_seconds', 'N/A')
        print(f"   {icon} {query}: {duration}s ({status})")
    
    # PP integration
    pp_health = check_pp_integration()
    print("\\n🔄 Portfolio Performance Integration:")
    for metric, value in pp_health.items():
        status = "✅" if not str(value).startswith('error') else "❌"
        print(f"   {status} {metric}: {value}")
    
    # Overall health summary
    print("\\n" + "=" * 50)
    
    # Health scoring
    total_issues = (
        benchmark_health['price_validation_failures'] + 
        benchmark_health['pending_rebalances'] +
        len([m for m in analytics_performance.values() if m.get('status') == 'error'])
    )
    
    if total_issues == 0:
        print("🎉 Phase 4 System: HEALTHY")
    elif total_issues < 5:
        print("⚠️  Phase 4 System: DEGRADED")
    else:
        print("❌ Phase 4 System: CRITICAL")
    
    return total_issues

if __name__ == "__main__":
    exit_code = main()
    exit(min(exit_code, 1))  # Cap at 1 for shell scripting
EOF

chmod +x scripts/phase4_health_check.py

# Set up automated monitoring
cat > scripts/phase4_monitoring.sh << 'EOF'
#!/bin/bash
# Phase 4 automated monitoring script

LOG_FILE="/var/log/phase4_health.log"
ALERT_THRESHOLD=3

echo "$(date): Starting Phase 4 health check" >> $LOG_FILE

# Run health check
poetry run python scripts/phase4_health_check.py >> $LOG_FILE 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -gt $ALERT_THRESHOLD ]; then
    echo "ALERT: Phase 4 system health critical (exit code: $EXIT_CODE)" >> $LOG_FILE
    # Send alert (implement your preferred alerting mechanism)
    # curl -X POST -H 'Content-type: application/json' --data '{"text":"Phase 4 system health critical"}' YOUR_SLACK_WEBHOOK_URL
fi

echo "$(date): Phase 4 health check completed" >> $LOG_FILE
EOF

chmod +x scripts/phase4_monitoring.sh

# Add to crontab for regular monitoring
echo "# Phase 4 health monitoring - every 15 minutes"
echo "*/15 * * * * /path/to/pp-security-master/scripts/phase4_monitoring.sh"

echo "✅ Comprehensive monitoring setup complete"
```

**Prevention:**
- Set up proactive monitoring from day one
- Implement graduated alerting (info, warning, critical)
- Create monitoring dashboards for visual tracking
- Regular health check automation
- Document monitoring procedures for operations team

## Escalation Procedures

### Level 1: Self-Service Resolution
**User Actions:**
- Check this troubleshooting guide
- Run diagnostic commands provided
- Attempt suggested solutions
- Review system logs for additional context

### Level 2: System Administrator
**Contact When:**
- Database connectivity issues persist
- Performance degradation affects multiple users
- Backup/recovery operations needed
- Configuration changes required

**Administrator Actions:**
- Review database performance metrics
- Check system resource utilization
- Analyze application logs for patterns
- Implement temporary workarounds
- Escalate to Level 3 if needed

### Level 3: Development Team
**Contact When:**
- Code-level issues identified
- Analytics calculations producing incorrect results
- New bugs discovered in Phase 4 functionality
- Schema changes or migrations required

**Developer Actions:**
- Review code and identify root cause
- Implement bug fixes or enhancements
- Deploy patches to production
- Update documentation and procedures

## Emergency Procedures

### System-Wide Analytics Failure
1. **Immediate Response:**
   - Switch to read-only mode for analytics
   - Disable automated benchmark generation
   - Notify all users of degraded service

2. **Investigation:**
   - Check database connectivity and performance
   - Review application logs for error patterns
   - Identify affected components

3. **Recovery:**
   - Restore from last known good backup if necessary
   - Apply emergency patches
   - Gradually restore full functionality
   - Post-incident review and documentation

### Data Corruption in Benchmark Securities
1. **Immediate Response:**
   - Stop all benchmark-related operations
   - Isolate affected benchmark securities
   - Preserve corrupted data for analysis

2. **Assessment:**
   - Identify scope of data corruption
   - Determine impact on dependent systems
   - Evaluate recovery options

3. **Recovery:**
   - Restore benchmark data from backups
   - Recalculate affected price histories
   - Validate data integrity before resuming operations
   - Implement additional safeguards to prevent recurrence

This troubleshooting guide provides comprehensive coverage of common Phase 4 issues with practical solutions and prevention strategies. Regular review and updates ensure it remains effective as the system evolves.