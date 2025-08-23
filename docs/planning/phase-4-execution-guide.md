# Phase 4 Execution Guide
## Analytics and Portfolio Performance Integration

Complete step-by-step guide for implementing Phase 4 with all analytics, benchmark generation, and Portfolio Performance integration features.

## Prerequisites

### Environment Validation
```bash
# Verify PostgreSQL 17 connection
poetry run python -c "from src.security_master.storage.connection import get_db_connection; print('✅ Database connected')"

# Verify Phase 0-3 completion
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
conn = get_db_connection()
cur = conn.cursor()
cur.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \"public\"')
tables = [row[0] for row in cur.fetchall()]
required = ['securities_master', 'pp_price_history', 'broker_transactions', 'classification_requests']
missing = [t for t in required if t not in tables]
if missing:
    print(f'❌ Missing tables: {missing}')
    exit(1)
else:
    print('✅ All prerequisite tables exist')
"

# Verify external integrations (Phase 2)
ls -la external_repos/pp-portfolio-classifier/
ls -la external_repos/ppxml2db/
```

### Dependency Installation
```bash
# Install analytics dependencies
poetry add numpy pandas scipy scikit-learn plotly dash

# Install Portfolio Performance XML dependencies  
poetry add lxml xmlschema defusedxml

# Install benchmark generation dependencies
poetry add yfinance quantlib-python

# Development and testing dependencies
poetry add pytest-benchmark pytest-xdist pytest-html
```

## Step 1: Database Schema Implementation

### 1.1 Create Analytics Database Extensions
```bash
# Execute analytics schema
poetry run python -c "
import psycopg2
from src.security_master.storage.connection import get_db_connection

with open('sql/phase4/analytics_views.sql', 'r') as f:
    analytics_sql = f.read()

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute(analytics_sql)
    conn.commit()
    print('✅ Analytics views created')
"
```

### 1.2 Create Benchmark Security Tables
```bash
# Execute benchmark schema
poetry run python -c "
import psycopg2
from src.security_master.storage.connection import get_db_connection

with open('sql/phase4/benchmark_security_tables.sql', 'r') as f:
    benchmark_sql = f.read()

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute(benchmark_sql)
    conn.commit()
    print('✅ Benchmark security tables created')
"
```

### 1.3 Create Portfolio Performance Integration Schema
```bash
# Execute PP integration schema
poetry run python -c "
import psycopg2
from src.security_master.storage.connection import get_db_connection

with open('sql/phase4/pp_integration_tables.sql', 'r') as f:
    pp_sql = f.read()

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute(pp_sql)
    conn.commit()
    print('✅ Portfolio Performance integration schema created')
"
```

## Step 2: Analytics Framework Implementation

### 2.1 Create Analytics Core Module
```bash
# Create analytics package structure
mkdir -p src/security_master/analytics
touch src/security_master/analytics/__init__.py

# Copy analytics templates
cp docs/planning/phase-4-templates/analytics_framework.py src/security_master/analytics/core.py
cp docs/planning/phase-4-templates/performance_metrics.py src/security_master/analytics/metrics.py
cp docs/planning/phase-4-templates/risk_analytics.py src/security_master/analytics/risk.py
```

### 2.2 Implement Portfolio Analytics
```bash
# Create portfolio analytics module
cat > src/security_master/analytics/portfolio.py << 'EOF'
"""Portfolio-level analytics and performance calculations."""

from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

from ..storage.connection import get_db_connection

class PortfolioAnalytics:
    """Comprehensive portfolio analytics and performance calculations."""
    
    def __init__(self, portfolio_id: str):
        self.portfolio_id = portfolio_id
        self.conn = get_db_connection()
    
    def calculate_sharpe_ratio(self, start_date: date, end_date: date, 
                             risk_free_rate: Decimal = Decimal('0.02')) -> Decimal:
        """Calculate Sharpe ratio for portfolio over specified period."""
        returns = self._get_portfolio_returns(start_date, end_date)
        if not returns:
            return Decimal('0')
        
        excess_returns = [r - (risk_free_rate / 252) for r in returns]  # Daily risk-free rate
        
        if len(excess_returns) < 2:
            return Decimal('0')
        
        mean_excess = np.mean(excess_returns)
        std_excess = np.std(excess_returns, ddof=1)
        
        if std_excess == 0:
            return Decimal('0')
        
        sharpe = (mean_excess / std_excess) * np.sqrt(252)  # Annualized
        return Decimal(str(round(sharpe, 4)))
    
    def calculate_alpha_beta(self, benchmark_id: str, start_date: date, 
                           end_date: date) -> Tuple[Decimal, Decimal]:
        """Calculate alpha and beta relative to benchmark."""
        portfolio_returns = self._get_portfolio_returns(start_date, end_date)
        benchmark_returns = self._get_benchmark_returns(benchmark_id, start_date, end_date)
        
        if len(portfolio_returns) < 10 or len(benchmark_returns) < 10:
            return Decimal('0'), Decimal('1')
        
        # Align returns by date
        portfolio_df = pd.DataFrame({'date': self._get_return_dates(start_date, end_date), 
                                   'portfolio': portfolio_returns})
        benchmark_df = pd.DataFrame({'date': self._get_return_dates(start_date, end_date), 
                                   'benchmark': benchmark_returns})
        
        merged = portfolio_df.merge(benchmark_df, on='date')
        
        if len(merged) < 10:
            return Decimal('0'), Decimal('1')
        
        # Calculate beta using linear regression
        beta, alpha, r_value, p_value, std_err = stats.linregress(
            merged['benchmark'], merged['portfolio']
        )
        
        # Annualize alpha
        alpha_annualized = alpha * 252
        
        return Decimal(str(round(alpha_annualized, 4))), Decimal(str(round(beta, 4)))
    
    def calculate_tracking_error(self, benchmark_id: str, start_date: date, 
                               end_date: date) -> Decimal:
        """Calculate tracking error relative to benchmark."""
        portfolio_returns = self._get_portfolio_returns(start_date, end_date)
        benchmark_returns = self._get_benchmark_returns(benchmark_id, start_date, end_date)
        
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return Decimal('0')
        
        excess_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        tracking_error = np.std(excess_returns, ddof=1) * np.sqrt(252)  # Annualized
        
        return Decimal(str(round(tracking_error, 4)))
    
    def _get_portfolio_returns(self, start_date: date, end_date: date) -> List[float]:
        """Get daily portfolio returns for period."""
        query = """
        SELECT date, daily_return 
        FROM vw_portfolio_daily_returns 
        WHERE portfolio_id = %s 
        AND date BETWEEN %s AND %s
        ORDER BY date
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (self.portfolio_id, start_date, end_date))
            returns = [float(row[1]) for row in cur.fetchall()]
        
        return returns
    
    def _get_benchmark_returns(self, benchmark_id: str, start_date: date, 
                             end_date: date) -> List[float]:
        """Get daily benchmark returns for period."""
        query = """
        SELECT ph.date, 
               LAG(ph.close_price) OVER (ORDER BY ph.date) as prev_price,
               ph.close_price,
               CASE 
                   WHEN LAG(ph.close_price) OVER (ORDER BY ph.date) IS NOT NULL
                   THEN (ph.close_price - LAG(ph.close_price) OVER (ORDER BY ph.date)) 
                        / LAG(ph.close_price) OVER (ORDER BY ph.date)
                   ELSE 0 
               END as daily_return
        FROM pp_price_history ph
        JOIN securities_master sm ON ph.security_master_id = sm.id
        WHERE sm.uuid = %s
        AND ph.date BETWEEN %s AND %s
        ORDER BY ph.date
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (benchmark_id, start_date, end_date))
            returns = [float(row[3]) for row in cur.fetchall() if row[3] is not None]
        
        return returns
    
    def _get_return_dates(self, start_date: date, end_date: date) -> List[date]:
        """Get trading dates for period."""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates
EOF

echo "✅ Portfolio analytics module created"
```

### 2.3 Create Analytics Database Views
```bash
# Execute analytics views creation script
poetry run python scripts/phase4/setup_analytics_pp_integration.sh

echo "✅ Analytics views created"
```

## Step 3: Benchmark Security Generator Implementation

### 3.1 Create Benchmark Generator Module
```bash
# Copy benchmark generator template
cp docs/planning/phase-4-templates/benchmark_security_generator.py src/security_master/analytics/benchmark_generator.py

echo "✅ Benchmark generator module created"
```

### 3.2 Test Benchmark Generation
```bash
# Run benchmark usage examples
poetry run python docs/planning/phase-4-templates/benchmark_usage_examples.py

echo "✅ Benchmark generation tested"
```

### 3.3 Validate Benchmark Database Functions
```bash
# Test benchmark validation functions
poetry run python -c "
from src.security_master.storage.connection import get_db_connection
from decimal import Decimal
from datetime import date

conn = get_db_connection()

# Test validation function
with conn.cursor() as cur:
    # Create a test benchmark first
    cur.execute('''
        INSERT INTO benchmark_securities (
            security_uuid, benchmark_type, base_date, base_price,
            underlying_portfolio_id, rebalance_frequency
        ) 
        SELECT uuid, 'reference_portfolio', %s, %s, 'test-portfolio', 'monthly'
        FROM securities_master 
        WHERE symbol LIKE 'TEST_%' 
        LIMIT 1
        ON CONFLICT (security_uuid) DO NOTHING
        RETURNING id
    ''', (date.today(), Decimal('100.00')))
    
    result = cur.fetchone()
    if result:
        benchmark_id = result[0]
        
        # Test validation function
        cur.execute('SELECT validate_benchmark_price_consistency(%s)', (benchmark_id,))
        validation_result = cur.fetchone()[0]
        print(f'✅ Price validation function works: {validation_result}')
        
        # Test composition function
        cur.execute('SELECT get_benchmark_composition(%s)', (benchmark_id,))
        composition = cur.fetchone()[0]
        print(f'✅ Composition function works: {composition is not None}')
        
        # Test return calculation function
        cur.execute('SELECT calculate_benchmark_return(%s, %s, %s)', 
                   (benchmark_id, date.today(), date.today()))
        return_calc = cur.fetchone()[0]
        print(f'✅ Return calculation function works: {return_calc is not None}')
    else:
        print('⚠️  No test securities available for benchmark testing')

conn.commit()
"
```

## Step 4: Portfolio Performance Integration

### 4.1 Create PP XML Generator
```bash
# Create PP integration package
mkdir -p src/security_master/pp_integration
touch src/security_master/pp_integration/__init__.py

# Copy PP XML generator template
cp docs/planning/phase-4-templates/pp_xml_generator.py src/security_master/pp_integration/xml_generator.py

echo "✅ Portfolio Performance XML generator created"
```

### 4.2 Create PP JSON Exporter
```bash
# Create PP JSON exporter
cat > src/security_master/pp_integration/json_exporter.py << 'EOF'
"""Portfolio Performance JSON export functionality."""

import json
from decimal import Decimal
from datetime import date, datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from ..storage.connection import get_db_connection

@dataclass
class PPSecurity:
    """Portfolio Performance security data structure."""
    uuid: str
    name: str
    isin: str
    symbol: str
    currency: str
    note: str = ""
    is_retired: bool = False
    
class PPJSONExporter:
    """Export data in Portfolio Performance JSON format."""
    
    def __init__(self):
        self.conn = get_db_connection()
    
    def export_securities(self, include_synthetic: bool = True) -> Dict[str, Any]:
        """Export all securities in PP JSON format."""
        query = """
        SELECT sm.uuid, sm.name, sm.isin, sm.symbol, sm.currency,
               sm.is_synthetic_benchmark, sm.benchmark_metadata
        FROM securities_master sm
        WHERE sm.is_active = true
        """
        
        if not include_synthetic:
            query += " AND (sm.is_synthetic_benchmark = false OR sm.is_synthetic_benchmark IS NULL)"
        
        query += " ORDER BY sm.name"
        
        with self.conn.cursor() as cur:
            cur.execute(query)
            securities_data = []
            
            for row in cur.fetchall():
                security = PPSecurity(
                    uuid=row[0],
                    name=row[1],
                    isin=row[2] or "",
                    symbol=row[3] or "",
                    currency=row[4] or "USD",
                    note="Synthetic Benchmark Security" if row[5] else ""
                )
                securities_data.append(asdict(security))
        
        return {
            "version": "1.0",
            "securities": securities_data,
            "exported_at": datetime.now().isoformat()
        }
    
    def export_prices(self, security_uuid: str, start_date: Optional[date] = None,
                     end_date: Optional[date] = None) -> Dict[str, Any]:
        """Export price history for security in PP JSON format."""
        query = """
        SELECT ph.date, ph.close_price
        FROM pp_price_history ph
        JOIN securities_master sm ON ph.security_master_id = sm.id
        WHERE sm.uuid = %s
        """
        params = [security_uuid]
        
        if start_date:
            query += " AND ph.date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND ph.date <= %s"
            params.append(end_date)
        
        query += " ORDER BY ph.date"
        
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            price_data = []
            
            for row in cur.fetchall():
                price_data.append({
                    "date": row[0].isoformat(),
                    "close": float(row[1])
                })
        
        return {
            "version": "1.0",
            "security_uuid": security_uuid,
            "prices": price_data,
            "exported_at": datetime.now().isoformat()
        }
    
    def export_benchmark_metadata(self, benchmark_uuid: str) -> Dict[str, Any]:
        """Export benchmark metadata and composition."""
        query = """
        SELECT bs.benchmark_type, bs.base_date, bs.base_price,
               bs.rebalance_frequency, bs.underlying_portfolio_id,
               bs.underlying_securities, bs.static_weights,
               bs.composition_data, bs.performance_data
        FROM benchmark_securities bs
        WHERE bs.security_uuid = %s
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (benchmark_uuid,))
            row = cur.fetchone()
            
            if not row:
                return {"error": "Benchmark not found"}
            
            return {
                "version": "1.0",
                "benchmark_uuid": benchmark_uuid,
                "benchmark_type": row[0],
                "base_date": row[1].isoformat() if row[1] else None,
                "base_price": float(row[2]) if row[2] else 100.0,
                "rebalance_frequency": row[3],
                "underlying_portfolio_id": row[4],
                "underlying_securities": row[5] if row[5] else [],
                "static_weights": [float(w) for w in row[6]] if row[6] else [],
                "composition_data": row[7] if row[7] else {},
                "performance_data": row[8] if row[8] else {},
                "exported_at": datetime.now().isoformat()
            }

# Custom JSON encoder for Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)
EOF

echo "✅ Portfolio Performance JSON exporter created"
```

### 4.3 Test PP Integration
```bash
# Test PP XML generation
poetry run python -c "
from src.security_master.pp_integration.xml_generator import PPXMLGenerator
from datetime import date

generator = PPXMLGenerator()

# Test with sample client data
xml = generator.generate_client_xml('test-client-123')
print('✅ PP XML generation successful')
print(f'Generated XML length: {len(xml)} characters')

# Validate XML structure
if '<client' in xml and '</client>' in xml:
    print('✅ XML has proper structure')
else:
    print('❌ XML structure validation failed')
"

# Test PP JSON export
poetry run python -c "
from src.security_master.pp_integration.json_exporter import PPJSONExporter, DecimalEncoder
import json

exporter = PPJSONExporter()

# Test securities export
securities = exporter.export_securities()
print(f'✅ Exported {len(securities[\"securities\"])} securities')

# Test JSON serialization
json_output = json.dumps(securities, cls=DecimalEncoder, indent=2)
print('✅ JSON serialization successful')
"
```

## Step 5: User Interface and CLI Integration

### 5.1 Extend CLI with Analytics Commands
```bash
# Add analytics commands to CLI
cat >> src/security_master/cli.py << 'EOF'

@cli.group()
def analytics():
    """Portfolio analytics and performance commands."""
    pass

@analytics.command()
@click.argument('portfolio_id')
@click.option('--start-date', type=click.DateTime(formats=['%Y-%m-%d']), 
              default=None, help='Start date for analysis')
@click.option('--end-date', type=click.DateTime(formats=['%Y-%m-%d']), 
              default=None, help='End date for analysis')
@click.option('--benchmark', help='Benchmark security UUID for comparison')
def portfolio_metrics(portfolio_id, start_date, end_date, benchmark):
    """Calculate portfolio performance metrics."""
    from .analytics.portfolio import PortfolioAnalytics
    from datetime import date, timedelta
    
    if not start_date:
        start_date = date.today() - timedelta(days=365)
    else:
        start_date = start_date.date()
    
    if not end_date:
        end_date = date.today()
    else:
        end_date = end_date.date()
    
    analytics = PortfolioAnalytics(portfolio_id)
    
    # Calculate Sharpe ratio
    sharpe = analytics.calculate_sharpe_ratio(start_date, end_date)
    click.echo(f"Sharpe Ratio: {sharpe}")
    
    # Calculate alpha/beta if benchmark provided
    if benchmark:
        alpha, beta = analytics.calculate_alpha_beta(benchmark, start_date, end_date)
        tracking_error = analytics.calculate_tracking_error(benchmark, start_date, end_date)
        click.echo(f"Alpha: {alpha}")
        click.echo(f"Beta: {beta}")
        click.echo(f"Tracking Error: {tracking_error}")

@analytics.command()
@click.argument('portfolio_id')
@click.argument('benchmark_name')
@click.option('--start-date', type=click.DateTime(formats=['%Y-%m-%d']), 
              required=True, help='Benchmark start date')
@click.option('--rebalance', default='monthly', 
              type=click.Choice(['daily', 'weekly', 'monthly', 'quarterly']),
              help='Rebalancing frequency')
def create_benchmark(portfolio_id, benchmark_name, start_date, rebalance):
    """Create synthetic benchmark security from portfolio."""
    from .analytics.benchmark_generator import BenchmarkSecurityGenerator
    from decimal import Decimal
    
    generator = BenchmarkSecurityGenerator()
    
    benchmark = generator.create_portfolio_benchmark(
        portfolio_id=portfolio_id,
        benchmark_name=benchmark_name,
        start_date=start_date.date(),
        base_price=Decimal('100.00'),
        rebalance_frequency=rebalance
    )
    
    click.echo(f"✅ Created benchmark: {benchmark.symbol}")
    click.echo(f"   UUID: {benchmark.uuid}")
    click.echo(f"   ISIN: {benchmark.isin}")
    click.echo(f"   Price points: {len(benchmark.price_history)}")

@cli.group()
def pp_export():
    """Portfolio Performance export commands."""
    pass

@pp_export.command()
@click.argument('client_id')
@click.option('--output', '-o', default='client_export.xml', 
              help='Output XML filename')
@click.option('--include-benchmarks', is_flag=True, 
              help='Include synthetic benchmark securities')
def xml(client_id, output, include_benchmarks):
    """Export client data to Portfolio Performance XML."""
    from .pp_integration.xml_generator import PPXMLGenerator
    
    generator = PPXMLGenerator()
    xml_data = generator.generate_client_xml(client_id, include_synthetic=include_benchmarks)
    
    with open(output, 'w', encoding='utf-8') as f:
        f.write(xml_data)
    
    click.echo(f"✅ Exported client {client_id} to {output}")

@pp_export.command()  
@click.option('--output', '-o', default='securities_export.json',
              help='Output JSON filename')
@click.option('--include-benchmarks', is_flag=True,
              help='Include synthetic benchmark securities')
def securities(output, include_benchmarks):
    """Export securities to Portfolio Performance JSON."""
    from .pp_integration.json_exporter import PPJSONExporter, DecimalEncoder
    import json
    
    exporter = PPJSONExporter()
    securities_data = exporter.export_securities(include_synthetic=include_benchmarks)
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(securities_data, f, cls=DecimalEncoder, indent=2)
    
    click.echo(f"✅ Exported {len(securities_data['securities'])} securities to {output}")
EOF

echo "✅ CLI extended with analytics and PP export commands"
```

### 5.2 Test CLI Commands
```bash
# Test analytics CLI commands
poetry run python -m security_master.cli analytics portfolio-metrics test-portfolio-123 --start-date 2024-01-01

# Test benchmark creation CLI
poetry run python -m security_master.cli analytics create-benchmark test-portfolio-123 "Test Benchmark" --start-date 2024-01-01

# Test PP export CLI
poetry run python -m security_master.cli pp-export xml test-client-123 -o test_export.xml --include-benchmarks

# Test securities export CLI
poetry run python -m security_master.cli pp-export securities -o test_securities.json --include-benchmarks

echo "✅ CLI commands tested"
```

## Step 6: Testing and Validation

### 6.1 Run Phase 4 Test Suite
```bash
# Create Phase 4 test directory
mkdir -p tests/phase4

# Copy test templates
cp docs/planning/phase-4-templates/test_*.py tests/phase4/

# Run comprehensive test suite
poetry run pytest tests/phase4/ -v --cov=src/security_master/analytics --cov=src/security_master/pp_integration --cov-report=html --cov-report=term-missing

echo "✅ Phase 4 tests completed"
```

### 6.2 Performance Validation
```bash
# Run performance benchmarks
poetry run pytest tests/phase4/test_benchmark_performance.py -v --benchmark-only

# Test large data handling
poetry run python -c "
from src.security_master.analytics.benchmark_generator import BenchmarkSecurityGenerator
from datetime import date, timedelta
from decimal import Decimal
import time

generator = BenchmarkSecurityGenerator()

# Test large portfolio benchmark
start_time = time.time()
benchmark = generator.create_custom_index_benchmark(
    securities=[f'test-security-{i}' for i in range(100)],
    weights=[Decimal('0.01')] * 100,
    benchmark_name='Large Portfolio Test',
    start_date=date(2023, 1, 1),
    end_date=date.today(),
    rebalance_frequency='monthly'
)
duration = time.time() - start_time

print(f'✅ Created benchmark with 100 securities in {duration:.2f} seconds')
print(f'   Price points: {len(benchmark.price_history)}')
"
```

### 6.3 Integration Validation
```bash
# Validate database schema
poetry run python -c "
from src.security_master.storage.connection import get_db_connection

conn = get_db_connection()
with conn.cursor() as cur:
    # Check all Phase 4 tables exist
    cur.execute('''
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%benchmark%'
        OR table_name LIKE '%analytics%'
    ''')
    tables = [row[0] for row in cur.fetchall()]
    
    expected_tables = ['benchmark_securities', 'benchmark_rebalance_schedule', 
                      'benchmark_performance_attribution', 'benchmark_quality_checks']
    
    for table in expected_tables:
        if table in tables:
            print(f'✅ {table} exists')
        else:
            print(f'❌ {table} missing')
    
    # Check views exist
    cur.execute('''
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'vw_%analytics%'
    ''')
    views = [row[0] for row in cur.fetchall()]
    print(f'✅ Found {len(views)} analytics views')
"
```

## Step 7: Documentation and User Training

### 7.1 Generate API Documentation
```bash
# Install documentation dependencies
poetry add sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Create documentation structure
mkdir -p docs/api
cat > docs/api/conf.py << 'EOF'
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))

project = 'Security Master Analytics'
copyright = '2024, PP Security Master'
author = 'Development Team'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
]

html_theme = 'sphinx_rtd_theme'
EOF

# Generate API documentation
poetry run sphinx-apidoc -o docs/api src/security_master/analytics
poetry run sphinx-build docs/api docs/api/_build

echo "✅ API documentation generated"
```

### 7.2 Create User Guides
```bash
# Create user guide directory
mkdir -p docs/user_guides

# Copy user guide templates  
cp docs/planning/phase-4-templates/benchmark_user_guide.md docs/user_guides/
cp docs/planning/phase-4-templates/analytics_user_guide.md docs/user_guides/
cp docs/planning/phase-4-templates/pp_integration_guide.md docs/user_guides/

echo "✅ User guides created"
```

## Step 8: Production Deployment Preparation

### 8.1 Environment Configuration
```bash
# Create production environment template
cat > .env.production.template << 'EOF'
# Production Database Configuration
DATABASE_HOST=production-postgres-server
DATABASE_PORT=5432
DATABASE_NAME=security_master_prod
DATABASE_USER=security_master_app
DATABASE_PASSWORD=secure_production_password

# OpenFIGI API Configuration
OPENFIGI_API_KEY=production_api_key
OPENFIGI_RATE_LIMIT=25

# Analytics Configuration
ANALYTICS_CACHE_TTL=3600
BENCHMARK_CALCULATION_THREADS=4
PERFORMANCE_ATTRIBUTION_THREADS=2

# Portfolio Performance Integration
PP_EXPORT_DIRECTORY=/var/exports/portfolio_performance
PP_BACKUP_DIRECTORY=/var/backups/pp_exports
PP_XML_VALIDATION=true

# Monitoring and Logging
LOG_LEVEL=INFO
SENTRY_DSN=production_sentry_dsn
PROMETHEUS_METRICS=true
EOF

echo "✅ Production environment template created"
```

### 8.2 Database Migration Script
```bash
# Create production migration script
cat > scripts/deploy_phase4_production.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Deploying Phase 4 to Production"

# Backup existing database
echo "📦 Creating database backup..."
pg_dump $DATABASE_NAME > backups/pre_phase4_backup_$(date +%Y%m%d_%H%M%S).sql

# Apply database migrations
echo "🔧 Applying database migrations..."
poetry run python -c "
import psycopg2
from src.security_master.storage.connection import get_db_connection

# Apply Phase 4 schema
schema_files = [
    'sql/phase4/analytics_views.sql',
    'sql/phase4/benchmark_security_tables.sql', 
    'sql/phase4/pp_integration_tables.sql'
]

conn = get_db_connection()
for schema_file in schema_files:
    print(f'Applying {schema_file}...')
    with open(schema_file, 'r') as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()
    print(f'✅ {schema_file} applied')

print('✅ All Phase 4 database migrations completed')
"

# Validate deployment
echo "✅ Validating deployment..."
poetry run python scripts/phase4/validate_phase4_deployment.py

# Run smoke tests
echo "🧪 Running smoke tests..."
poetry run pytest tests/phase4/test_smoke.py -v

echo "🎉 Phase 4 production deployment complete!"
EOF

chmod +x scripts/deploy_phase4_production.sh
echo "✅ Production deployment script created"
```

### 8.3 Monitoring and Alerting Setup
```bash
# Create monitoring configuration
cat > monitoring/phase4_alerts.yml << 'EOF'
alerts:
  - name: benchmark_generation_failure
    condition: benchmark_creation_errors > 0
    severity: high
    description: "Benchmark security generation failing"
    
  - name: analytics_query_timeout
    condition: avg_analytics_query_time > 30s
    severity: medium
    description: "Analytics queries taking too long"
    
  - name: pp_export_failure
    condition: pp_export_errors > 0
    severity: high
    description: "Portfolio Performance export failing"
    
  - name: database_connection_pool_exhausted
    condition: db_pool_usage > 90%
    severity: high
    description: "Database connection pool nearly exhausted"

metrics:
  - name: benchmark_securities_count
    query: "SELECT COUNT(*) FROM benchmark_securities WHERE is_active = true"
    
  - name: daily_analytics_queries
    query: "SELECT COUNT(*) FROM analytics_query_log WHERE date = CURRENT_DATE"
    
  - name: pp_export_size_mb
    query: "SELECT AVG(export_size_mb) FROM pp_export_log WHERE date >= CURRENT_DATE - 7"
EOF

echo "✅ Monitoring configuration created"
```

## Step 9: Final Validation and Sign-off

### 9.1 Execute Complete Validation Checklist
```bash
# Run complete validation using the checklist
poetry run python scripts/phase4/run_validation_checklist.py

echo "✅ Complete validation checklist executed"
```

### 9.2 Generate Phase 4 Completion Report
```bash
# Generate completion report
poetry run python -c "
import json
from datetime import datetime
from src.security_master.storage.connection import get_db_connection

conn = get_db_connection()

# Collect statistics
with conn.cursor() as cur:
    # Count benchmark securities
    cur.execute('SELECT COUNT(*) FROM benchmark_securities WHERE is_active = true')
    benchmark_count = cur.fetchone()[0]
    
    # Count analytics views
    cur.execute('''SELECT COUNT(*) FROM information_schema.views 
                  WHERE table_schema = 'public' AND table_name LIKE 'vw_%analytics%' ''')
    analytics_views = cur.fetchone()[0]
    
    # Count total securities
    cur.execute('SELECT COUNT(*) FROM securities_master WHERE is_active = true')
    total_securities = cur.fetchone()[0]

report = {
    'phase': 'Phase 4 - Analytics and Portfolio Performance Integration',
    'completion_date': datetime.now().isoformat(),
    'statistics': {
        'benchmark_securities': benchmark_count,
        'analytics_views': analytics_views,
        'total_securities': total_securities
    },
    'features_implemented': [
        'Benchmark Security Generator',
        'Portfolio Analytics Framework', 
        'Performance Attribution Engine',
        'Portfolio Performance XML Export',
        'Portfolio Performance JSON Export',
        'Risk Analytics Module',
        'Database Analytics Views',
        'CLI Analytics Commands'
    ],
    'database_objects_created': [
        'benchmark_securities table',
        'benchmark_rebalance_schedule table', 
        'benchmark_performance_attribution table',
        'benchmark_quality_checks table',
        'Analytics views (portfolio, security, benchmark)',
        'Validation functions',
        'Performance calculation functions'
    ],
    'status': 'COMPLETED'
}

with open('phase4_completion_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print('✅ Phase 4 completion report generated')
print(json.dumps(report, indent=2))
"
```

## Summary

Phase 4 implementation provides:

1. **Synthetic Benchmark Securities** - Solve PP's single-security benchmark limitation
2. **Comprehensive Analytics** - Sharpe ratio, alpha/beta, tracking error, attribution
3. **Portfolio Performance Integration** - Native XML/JSON export with benchmark support
4. **Risk Analytics** - VaR, performance attribution, Monte Carlo simulation framework
5. **Database Analytics Views** - Optimized views for common analytics queries
6. **CLI Integration** - Command-line tools for analytics and benchmarking
7. **Production Readiness** - Monitoring, validation, and deployment automation

The system now enables sophisticated portfolio analytics while maintaining seamless integration with Portfolio Performance through synthetic benchmark securities that accurately replicate multi-asset portfolio performance as single securities.