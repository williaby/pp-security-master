# Phase 5 Troubleshooting Guide
## Enterprise Production Deployment Issues & Solutions

Comprehensive troubleshooting guide for Phase 5 enterprise features including web UI, authentication, Docker deployment, monitoring, and production operations.

---

## Quick Diagnosis Commands

### System Health Check
```bash
# Overall system status
docker-compose -f docker/docker-compose.production.yml ps
curl -f https://pp-security.your-domain.com/health
./scripts/validate_production.sh

# Service-specific health
docker exec pp_security_api_prod curl -f http://localhost:8000/health
docker exec pp_security_db_prod pg_isready -U ${DATABASE_USER} -d ${DATABASE_NAME}
docker exec pp_security_cache_prod redis-cli --raw incr ping

# Authentication check
curl -H "Cf-Access-Jwt-Assertion: ${TEST_JWT}" https://pp-security.your-domain.com/auth/user
```

### Log Analysis
```bash
# Service logs with timestamps
docker logs pp_security_api_prod --since 1h --timestamps
docker logs pp_security_worker_prod --since 1h --timestamps
docker logs pp_security_db_prod --since 1h --timestamps

# Application logs
tail -f /mnt/user/pp-security-prod/logs/security-master.log
tail -f /mnt/user/pp-security-prod/logs/auth.log
tail -f /mnt/user/pp-security-prod/logs/worker.log

# Monitoring logs
docker logs pp_security_metrics_prod --since 30m
docker logs pp_security_dashboards_prod --since 30m
```

---

## Web UI & Gradio Interface Issues

### Issue: Gradio App Won't Start
**Symptoms:**
- `ImportError: No module named 'gradio'`
- `AttributeError: module 'gradio' has no attribute 'Blocks'`
- Application crashes on startup

**Diagnosis:**
```bash
# Check Gradio installation
poetry show gradio
python -c "import gradio; print(gradio.__version__)"

# Check PromptCraft component availability
ls -la /home/byron/dev/PromptCraft/src/ui/components/
python -c "from src.security_master.ui.components import accessibility_enhancements"
```

**Solutions:**
```bash
# Install/upgrade Gradio
poetry add gradio@^4.0.0
poetry install --sync

# Re-copy PromptCraft components
./scripts/phase5/setup_enterprise_production.sh --component ui-only

# Reset UI dependencies
rm -rf src/security_master/ui/components/__pycache__
poetry run python -m src.security_master.ui.gradio_interface --validate
```

### Issue: UI Components Not Loading
**Symptoms:**
- Missing tabs or interface elements
- `ModuleNotFoundError` for PromptCraft components
- Blank or partially loaded interface

**Diagnosis:**
```bash
# Check component structure
find src/security_master/ui -name "*.py" | head -10
ls -la src/security_master/ui/components/

# Test component imports
python -c "
from src.security_master.ui.components.accessibility_enhancements import enhance_interface
from src.security_master.ui.components.securities_classification_tab import create_classification_tab
print('Components loaded successfully')
"
```

**Solutions:**
```bash
# Regenerate UI components
./scripts/phase5/setup_enterprise_production.sh --component ui-regenerate

# Manual component fix
cp /home/byron/dev/PromptCraft/src/ui/components/*.py src/security_master/ui/components/

# Fix import paths
find src/security_master/ui -name "*.py" -exec sed -i 's/from src\.ui\./from src.security_master.ui./g' {} \;
```

### Issue: Mobile/Responsive Layout Problems
**Symptoms:**
- Interface not responsive on mobile devices
- Elements overlapping or cut off
- Poor accessibility on small screens

**Diagnosis:**
```bash
# Check CSS customization
grep -r "mobile" src/security_master/ui/
grep -r "@media" src/security_master/ui/

# Test responsive components
python -c "
from src.security_master.ui.gradio_interface import SecurityMasterInterface
app = SecurityMasterInterface()
print('CSS:', app._get_custom_css()[:200])
"
```

**Solutions:**
```bash
# Apply PromptCraft responsive fixes
cp /home/byron/dev/PromptCraft/src/ui/static/responsive.css src/security_master/ui/static/
cp /home/byron/dev/PromptCraft/src/ui/static/mobile-optimizations.css src/security_master/ui/static/

# Update interface CSS
poetry run python scripts/ui/update_responsive_css.py
```

### Issue: Tab Navigation Not Working
**Symptoms:**
- Clicking tabs doesn't switch content
- JavaScript errors in browser console
- Tabs appear but content doesn't change

**Diagnosis:**
```bash
# Check tab implementation
grep -A 10 -B 5 "gr.Tabs" src/security_master/ui/gradio_interface.py
grep -r "tabIndex" src/security_master/ui/

# Test tab creation
python -c "
import gradio as gr
with gr.Blocks() as test:
    with gr.Tabs():
        with gr.Tab('Test'):
            gr.Markdown('Working')
print('Tab test successful')
"
```

**Solutions:**
```bash
# Reset Gradio tab configuration
sed -i 's/gr.Tabs(/gr.Tabs(selected=0, /g' src/security_master/ui/gradio_interface.py

# Apply PromptCraft tab fixes
cp /home/byron/dev/PromptCraft/src/ui/components/enhanced_tabs.py src/security_master/ui/components/

# Restart with tab debugging
DEBUG_TABS=true poetry run python -m src.security_master.ui.gradio_interface
```

---

## Authentication & Cloudflare Access Issues

### Issue: JWT Token Validation Failing
**Symptoms:**
- `401 Unauthorized` responses
- `Invalid JWT signature` errors
- Users can't access authenticated endpoints

**Diagnosis:**
```bash
# Check JWT configuration
echo "JWT_SECRET: ${JWT_SECRET:0:10}..." 
echo "CLOUDFLARE_AUDIENCE: ${CLOUDFLARE_AUDIENCE}"

# Test JWT validation
curl -H "Cf-Access-Jwt-Assertion: ${TEST_JWT}" https://pp-security.your-domain.com/auth/validate

# Check Cloudflare Access headers
curl -I https://pp-security.your-domain.com/
```

**Solutions:**
```bash
# Update JWT secret
gpg --decrypt .env.gpg | grep JWT_SECRET
# Update .env with correct JWT_SECRET

# Restart authentication services
docker-compose -f docker/docker-compose.production.yml restart api
docker-compose -f docker/docker-compose.production.yml restart worker

# Test with known good token
export TEST_JWT="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6..."
curl -H "Cf-Access-Jwt-Assertion: ${TEST_JWT}" https://pp-security.your-domain.com/auth/user
```

### Issue: Role-Based Access Control Not Working
**Symptoms:**
- Users seeing unauthorized interface elements
- Permission checks failing
- Admin functions available to non-admin users

**Diagnosis:**
```bash
# Check user role assignment
psql ${DATABASE_URL} -c "SELECT username, role, permissions FROM security_master_users LIMIT 5;"

# Test role validation
python -c "
from src.security_master.auth.rbac import get_user_permissions
from src.security_master.auth.models import SecurityMasterUser
# Test role validation logic
"

# Check middleware integration
grep -r "require_role" src/security_master/
```

**Solutions:**
```bash
# Reset user roles
psql ${DATABASE_URL} -c "
UPDATE security_master_users 
SET role = 'admin', permissions = '{}' 
WHERE username = 'your-admin@company.com';
"

# Reload RBAC configuration
docker-compose -f docker/docker-compose.production.yml restart api

# Apply PromptCraft RBAC fixes
cp /home/byron/dev/PromptCraft/src/auth/rbac_enhanced.py src/security_master/auth/rbac.py
```

### Issue: Session Management Problems
**Symptoms:**
- Users logged out unexpectedly
- Session timeout not working correctly
- Multiple session conflicts

**Diagnosis:**
```bash
# Check session configuration
redis-cli -h redis -a ${REDIS_PASSWORD} keys "session:*" | wc -l
redis-cli -h redis -a ${REDIS_PASSWORD} ttl "session:example-user"

# Check session middleware
grep -r "SESSION_TIMEOUT" src/security_master/
docker exec pp_security_cache_prod redis-cli --raw info keyspace
```

**Solutions:**
```bash
# Clear problematic sessions
redis-cli -h redis -a ${REDIS_PASSWORD} flushdb

# Update session configuration
export SESSION_TIMEOUT=28800  # 8 hours
docker-compose -f docker/docker-compose.production.yml restart api

# Apply PromptCraft session management
cp /home/byron/dev/PromptCraft/src/auth/session_manager.py src/security_master/auth/
```

---

## Docker Deployment & Container Issues

### Issue: Container Build Failures
**Symptoms:**
- `docker build` fails with dependency errors
- `poetry install` timing out in container
- Missing system dependencies in container

**Diagnosis:**
```bash
# Check Dockerfile syntax
docker build --no-cache -f docker/api.Dockerfile . --target development
docker build --no-cache -f docker/worker.Dockerfile . --target development

# Check base image availability
docker pull python:3.11-slim
docker images | grep python

# Analyze build context
ls -la docker/
du -sh . | head -20
```

**Solutions:**
```bash
# Fix base image issues
sed -i 's/python:3.11-slim/python:3.11.6-slim-bookworm/g' docker/api.Dockerfile
sed -i 's/python:3.11-slim/python:3.11.6-slim-bookworm/g' docker/worker.Dockerfile

# Clear Docker cache and rebuild
docker system prune -f
docker-compose -f docker/docker-compose.production.yml build --no-cache

# Fix dependency issues
poetry export -f requirements.txt --output docker/requirements.txt --without-hashes
```

### Issue: Container Health Check Failures
**Symptoms:**
- Services marked as unhealthy
- Continuous restart loops
- Health check endpoints returning errors

**Diagnosis:**
```bash
# Check health check configuration
docker inspect pp_security_api_prod | jq '.[0].Config.Healthcheck'
docker inspect pp_security_db_prod | jq '.[0].State.Health'

# Test health endpoints manually
docker exec pp_security_api_prod curl -f http://localhost:8000/health
docker exec pp_security_db_prod pg_isready -U ${DATABASE_USER} -d ${DATABASE_NAME}
```

**Solutions:**
```bash
# Fix API health check
docker exec pp_security_api_prod curl -v http://localhost:8000/health

# Update health check configuration
# Edit docker-compose.production.yml:
sed -i 's/interval: 10s/interval: 30s/g' docker/docker-compose.production.yml
sed -i 's/timeout: 5s/timeout: 15s/g' docker/docker-compose.production.yml

# Restart with new health checks
docker-compose -f docker/docker-compose.production.yml up -d
```

### Issue: Network Connectivity Problems
**Symptoms:**
- Services can't communicate with each other
- External API calls failing
- Database connection refused

**Diagnosis:**
```bash
# Check network configuration
docker network ls | grep pp_
docker network inspect pp_security_api_net

# Test inter-service connectivity
docker exec pp_security_api_prod ping postgresql
docker exec pp_security_api_prod nslookup redis
docker exec pp_security_worker_prod telnet postgresql 5432
```

**Solutions:**
```bash
# Recreate networks
docker-compose -f docker/docker-compose.production.yml down
docker network prune -f
docker-compose -f docker/docker-compose.production.yml up -d

# Fix network isolation issues
# Edit docker-compose.production.yml networks section
# Ensure services are on correct networks

# Test connectivity after fix
docker exec pp_security_api_prod ping -c 3 postgresql
```

### Issue: Volume Mount Problems
**Symptoms:**
- Data not persisting across restarts
- Permission denied errors in containers
- Volume mounts not working

**Diagnosis:**
```bash
# Check volume configuration
docker volume ls | grep pp_security
docker volume inspect pp_security_pg_data_prod

# Check mount points
docker exec pp_security_db_prod ls -la /var/lib/postgresql/data
docker exec pp_security_api_prod ls -la /app/data

# Check host filesystem
ls -la /mnt/user/pp-security-prod/
ls -la /mnt/cache/appdata/pp-security-prod/
```

**Solutions:**
```bash
# Create missing directories
sudo mkdir -p /mnt/user/pp-security-prod/{data,logs,backups}
sudo mkdir -p /mnt/cache/appdata/pp-security-prod/{postgresql,redis,prometheus,grafana}

# Fix permissions
sudo chown -R 999:999 /mnt/cache/appdata/pp-security-prod/postgresql
sudo chown -R 999:999 /mnt/cache/appdata/pp-security-prod/redis
sudo chown -R 1000:1000 /mnt/user/pp-security-prod/

# Recreate volumes
docker-compose -f docker/docker-compose.production.yml down -v
docker-compose -f docker/docker-compose.production.yml up -d
```

---

## Database & PostgreSQL Issues

### Issue: Database Connection Failures
**Symptoms:**
- `psycopg2.OperationalError: could not connect to server`
- `FATAL: password authentication failed`
- Connection pool exhaustion errors

**Diagnosis:**
```bash
# Test direct database connection
psql ${DATABASE_URL}
docker exec pp_security_db_prod pg_isready -U ${DATABASE_USER} -d ${DATABASE_NAME}

# Check database logs
docker logs pp_security_db_prod --since 1h | grep ERROR
docker logs pp_security_db_prod --since 1h | grep FATAL

# Check connection pool status
psql ${DATABASE_URL} -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

**Solutions:**
```bash
# Reset database credentials
export DATABASE_PASSWORD="$(openssl rand -base64 32)"
echo "DATABASE_PASSWORD=${DATABASE_PASSWORD}" >> .env

# Update database configuration
docker-compose -f docker/docker-compose.production.yml restart postgresql
docker-compose -f docker/docker-compose.production.yml restart api

# Fix connection pool settings
sed -i 's/DATABASE_POOL_SIZE=20/DATABASE_POOL_SIZE=10/g' docker/docker-compose.production.yml
sed -i 's/DATABASE_MAX_OVERFLOW=30/DATABASE_MAX_OVERFLOW=20/g' docker/docker-compose.production.yml
```

### Issue: Migration Failures
**Symptoms:**
- `alembic.util.exc.CommandError` during migrations
- Tables not created or updated correctly
- Data corruption after migration

**Diagnosis:**
```bash
# Check current migration status
poetry run alembic current
poetry run alembic history --verbose

# Check database schema
psql ${DATABASE_URL} -c "\dt" # List tables
psql ${DATABASE_URL} -c "\d securities" # Describe table

# Check for migration conflicts
poetry run alembic show-migrations
ls -la sql/versions/
```

**Solutions:**
```bash
# Reset to clean migration state
poetry run alembic stamp base
poetry run alembic upgrade head

# Manual schema fixes if needed
psql ${DATABASE_URL} -f sql/manual_fixes/fix_corrupted_schema.sql

# Generate new migration for current state
poetry run alembic revision --autogenerate -m "Fix schema inconsistencies"
poetry run alembic upgrade head
```

### Issue: Performance Problems
**Symptoms:**
- Slow query responses
- High CPU usage on database
- Connection timeouts

**Diagnosis:**
```bash
# Check database performance metrics
psql ${DATABASE_URL} -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Check active connections
psql ${DATABASE_URL} -c "
SELECT count(*) as active_connections, state 
FROM pg_stat_activity 
GROUP BY state;
"

# Check slow queries
docker logs pp_security_db_prod | grep "slow query"
```

**Solutions:**
```bash
# Apply performance optimizations
psql ${DATABASE_URL} -c "
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET work_mem = '256MB';
SELECT pg_reload_conf();
"

# Rebuild indexes
psql ${DATABASE_URL} -c "REINDEX DATABASE ${DATABASE_NAME};"

# Update statistics
psql ${DATABASE_URL} -c "ANALYZE;"

# Restart database with new configuration
docker-compose -f docker/docker-compose.production.yml restart postgresql
```

---

## External API Integration Issues

### Issue: OpenFIGI API Rate Limiting
**Symptoms:**
- `429 Too Many Requests` errors
- Classification failures for securities
- Long delays in security lookups

**Diagnosis:**
```bash
# Check API key configuration
echo "OPENFIGI_API_KEY: ${OPENFIGI_API_KEY:0:10}..."

# Check rate limiting logs
grep -r "rate.limit" /mnt/user/pp-security-prod/logs/
grep -r "429" /mnt/user/pp-security-prod/logs/

# Test API directly
curl -H "X-OPENFIGI-APIKEY: ${OPENFIGI_API_KEY}" \
     -X POST https://api.openfigi.com/v3/mapping \
     -H "Content-Type: application/json" \
     -d '[{"ticker":"AAPL"}]'
```

**Solutions:**
```bash
# Implement exponential backoff
cp templates/external_apis/openfigi_rate_limiter.py src/security_master/classifier/

# Increase cache TTL for classifications
sed -i 's/CLASSIFICATION_CACHE_TTL=3600/CLASSIFICATION_CACHE_TTL=86400/g' .env

# Add request queuing
redis-cli -h redis -a ${REDIS_PASSWORD} config set maxmemory-policy allkeys-lru

# Monitor API usage
./scripts/monitoring/api_usage_monitor.sh
```

### Issue: Alpha Vantage API Failures
**Symptoms:**
- Market data not updating
- `Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute`
- Price history incomplete

**Diagnosis:**
```bash
# Test Alpha Vantage API
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=${ALPHA_VANTAGE_API_KEY}"

# Check API call frequency
grep -c "alphavantage" /mnt/user/pp-security-prod/logs/worker.log

# Check cache hit rates
redis-cli -h redis -a ${REDIS_PASSWORD} info stats | grep cache
```

**Solutions:**
```bash
# Implement API call batching
cp templates/external_apis/alpha_vantage_batch_processor.py src/security_master/classifier/

# Increase cache retention for price data
redis-cli -h redis -a ${REDIS_PASSWORD} config set save "900 1 300 10 60 10000"

# Add fallback data sources
echo "YAHOO_FINANCE_FALLBACK=true" >> .env
echo "QUANDL_API_KEY=${QUANDL_API_KEY}" >> .env
```

### Issue: pp-portfolio-classifier Integration
**Symptoms:**
- Fund classification failures
- Import errors for classifier module
- Inconsistent classification results

**Diagnosis:**
```bash
# Check pp-portfolio-classifier availability
python -c "import pp_portfolio_classifier; print('Available')"
pip list | grep pp-portfolio-classifier

# Test classification directly
python -c "
from pp_portfolio_classifier import classify_fund
result = classify_fund('VTI')
print(result)
"

# Check integration logs
grep -r "pp.portfolio.classifier" /mnt/user/pp-security-prod/logs/
```

**Solutions:**
```bash
# Reinstall pp-portfolio-classifier
poetry remove pp-portfolio-classifier
poetry add git+https://github.com/pp-security/pp-portfolio-classifier.git

# Update integration layer
cp templates/classifiers/pp_classifier_integration.py src/security_master/classifier/fund.py

# Test integration
poetry run python -c "
from src.security_master.classifier.fund import classify_fund_with_pp
result = classify_fund_with_pp('VTI')
print('Integration test:', result)
"
```

---

## Monitoring & Alerting Issues

### Issue: Prometheus Metrics Not Collecting
**Symptoms:**
- Grafana dashboards showing no data
- Prometheus targets showing as down
- Missing business metrics

**Diagnosis:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check metrics endpoints
curl http://localhost:8001/metrics  # API metrics
curl http://localhost:9187/metrics  # PostgreSQL metrics
curl http://localhost:9121/metrics  # Redis metrics

# Check Prometheus configuration
docker exec pp_security_metrics_prod cat /etc/prometheus/prometheus.yml
```

**Solutions:**
```bash
# Restart Prometheus with config reload
curl -X POST http://localhost:9090/-/reload

# Fix metrics endpoint configuration
sed -i 's/8001:8001/8001:8001/g' docker/docker-compose.production.yml

# Update scrape configurations
cp monitoring/prometheus.yml docker/
docker-compose -f docker/docker-compose.production.yml restart prometheus

# Test metrics collection
curl http://localhost:9090/api/v1/query?query=up
```

### Issue: Grafana Dashboards Not Loading
**Symptoms:**
- Empty dashboard panels
- "No data" messages in Grafana
- Dashboard import failures

**Diagnosis:**
```bash
# Check Grafana data source configuration
curl -u admin:${GRAFANA_ADMIN_PASSWORD} http://localhost:3000/api/datasources

# Check dashboard provisioning
docker exec pp_security_dashboards_prod ls -la /etc/grafana/provisioning/dashboards/

# Check Grafana logs
docker logs pp_security_dashboards_prod | grep ERROR
```

**Solutions:**
```bash
# Reimport dashboards
cp monitoring/grafana/dashboards/*.json docker/monitoring/grafana/dashboards/
docker-compose -f docker/docker-compose.production.yml restart grafana

# Fix data source connection
curl -X PUT -u admin:${GRAFANA_ADMIN_PASSWORD} \
     -H "Content-Type: application/json" \
     -d '{"url":"http://prometheus:9090"}' \
     http://localhost:3000/api/datasources/1

# Test dashboard queries
curl -u admin:${GRAFANA_ADMIN_PASSWORD} \
     "http://localhost:3000/api/dashboards/uid/security-master-overview"
```

### Issue: Alert Rules Not Triggering
**Symptoms:**
- No alerts firing despite conditions met
- AlertManager not receiving alerts
- Notification channels not working

**Diagnosis:**
```bash
# Check alert rule status
curl http://localhost:9090/api/v1/rules

# Check AlertManager status
curl http://localhost:9093/api/v1/alerts

# Test alert conditions manually
curl "http://localhost:9090/api/v1/query?query=up{job=\"security-master-api\"} == 0"
```

**Solutions:**
```bash
# Reload alert rules
curl -X POST http://localhost:9090/-/reload

# Fix AlertManager routing
cp monitoring/alertmanager.yml docker/
docker-compose -f docker/docker-compose.production.yml restart alertmanager

# Test alert firing
curl -X POST http://localhost:9093/api/v1/alerts \
     -H "Content-Type: application/json" \
     -d '[{"labels":{"alertname":"test","severity":"warning"}}]'
```

---

## Performance & Scalability Issues

### Issue: Slow Classification Processing
**Symptoms:**
- Long delays in security classification
- Worker queue backlog growing
- Users experiencing timeouts

**Diagnosis:**
```bash
# Check worker status
docker exec pp_security_worker_prod celery inspect active -A src.security_master.worker.celery_app
docker exec pp_security_worker_prod celery inspect registered -A src.security_master.worker.celery_app

# Check queue lengths
redis-cli -h redis -a ${REDIS_PASSWORD} llen "celery"
redis-cli -h redis -a ${REDIS_PASSWORD} llen "classification_queue"

# Check worker performance
docker logs pp_security_worker_prod | grep "Task.*succeeded"
```

**Solutions:**
```bash
# Scale worker instances
docker-compose -f docker/docker-compose.production.yml up -d --scale worker=4

# Optimize classification batch processing
sed -i 's/WORKER_CONCURRENCY=4/WORKER_CONCURRENCY=8/g' docker/docker-compose.production.yml

# Implement classification caching
redis-cli -h redis -a ${REDIS_PASSWORD} config set maxmemory 4gb
redis-cli -h redis -a ${REDIS_PASSWORD} config set maxmemory-policy allkeys-lru

# Monitor improvements
./scripts/monitoring/worker_performance.sh
```

### Issue: Database Query Performance
**Symptoms:**
- Slow portfolio analytics generation
- Long search response times
- Database CPU spikes

**Diagnosis:**
```bash
# Analyze slow queries
psql ${DATABASE_URL} -c "
SELECT query, calls, total_time, mean_time, stddev_time
FROM pg_stat_statements 
WHERE mean_time > 1000 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Check index usage
psql ${DATABASE_URL} -c "
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read 
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;
"
```

**Solutions:**
```bash
# Add missing indexes
psql ${DATABASE_URL} -c "
CREATE INDEX CONCURRENTLY idx_securities_isin ON securities(isin);
CREATE INDEX CONCURRENTLY idx_securities_symbol ON securities(symbol);
CREATE INDEX CONCURRENTLY idx_portfolios_updated ON portfolios(updated_at);
"

# Optimize analytics queries
cp sql/optimizations/portfolio_analytics_optimized.sql sql/
psql ${DATABASE_URL} -f sql/optimizations/portfolio_analytics_optimized.sql

# Update database statistics
psql ${DATABASE_URL} -c "ANALYZE;"
```

### Issue: Memory Usage Problems
**Symptoms:**
- Out of memory errors in containers
- System becoming unresponsive
- Container restarts due to memory limits

**Diagnosis:**
```bash
# Check container memory usage
docker stats --no-stream | grep pp_security

# Check system memory
free -h
df -h

# Check application memory patterns
docker exec pp_security_api_prod ps aux --sort=-%mem | head
```

**Solutions:**
```bash
# Adjust container memory limits
sed -i 's/memory: 4G/memory: 6G/g' docker/docker-compose.production.yml
sed -i 's/memory: 2G/memory: 3G/g' docker/docker-compose.production.yml

# Optimize Python memory usage
echo "PYTHONMALLOC=malloc_debug" >> docker/docker-compose.production.yml

# Implement memory monitoring
./scripts/monitoring/memory_monitor.sh &

# Restart with new limits
docker-compose -f docker/docker-compose.production.yml restart
```

---

## Security & Compliance Issues

### Issue: Security Scan Failures
**Symptoms:**
- Bandit reporting HIGH/CRITICAL security issues
- Safety reporting vulnerable dependencies
- Container security scans failing

**Diagnosis:**
```bash
# Run security scans
poetry run bandit -r src -f json -o bandit-report.json
poetry run safety check --json --output safety-report.json
poetry run pip-audit --format=json --output=audit-report.json

# Check container vulnerabilities
docker run --rm -v $(pwd):/workspace aquasec/trivy fs /workspace
```

**Solutions:**
```bash
# Fix dependency vulnerabilities
poetry update
poetry add "package@^safe.version"

# Address bandit findings
# Review and fix code issues identified in bandit-report.json

# Update base images
sed -i 's/python:3.11-slim/python:3.11.6-slim-bookworm/g' docker/api.Dockerfile

# Regenerate security reports
./security/scans/full_security_assessment.sh
```

### Issue: Data Protection Compliance
**Symptoms:**
- Audit logs missing required fields
- Unencrypted sensitive data in logs
- Inadequate access controls

**Diagnosis:**
```bash
# Check audit log configuration
grep -r "audit" src/security_master/
tail -n 100 /mnt/user/pp-security-prod/logs/audit.log

# Check data encryption status
psql ${DATABASE_URL} -c "SHOW ssl;"
psql ${DATABASE_URL} -c "SELECT * FROM pg_file_settings WHERE name LIKE '%ssl%';"

# Review access controls
psql ${DATABASE_URL} -c "
SELECT username, role, permissions, last_login 
FROM security_master_users 
ORDER BY last_login DESC;
"
```

**Solutions:**
```bash
# Enable comprehensive audit logging
echo "ENABLE_AUDIT_LOGGING=true" >> .env
echo "AUDIT_LOG_LEVEL=INFO" >> .env

# Encrypt sensitive database columns
psql ${DATABASE_URL} -f sql/encryption/encrypt_sensitive_data.sql

# Update access control policies
cp security/policies/rbac_policies.json src/security_master/auth/
docker-compose -f docker/docker-compose.production.yml restart api
```

### Issue: API Security Problems
**Symptoms:**
- API endpoints accessible without authentication
- Rate limiting not working
- Sensitive data exposed in API responses

**Diagnosis:**
```bash
# Test unauthenticated access
curl https://pp-security.your-domain.com/api/securities/
curl https://pp-security.your-domain.com/api/portfolios/

# Check rate limiting
for i in {1..20}; do curl -w "%{http_code}" https://pp-security.your-domain.com/api/health/; done

# Review API response sanitization
curl -H "Cf-Access-Jwt-Assertion: ${TEST_JWT}" https://pp-security.your-domain.com/api/user/
```

**Solutions:**
```bash
# Apply authentication to all endpoints
cp security/middleware/auth_required.py src/security_master/api/

# Configure rate limiting
echo "RATE_LIMIT_PER_MINUTE=60" >> .env
echo "RATE_LIMIT_BURST=120" >> .env

# Sanitize API responses
cp security/middleware/response_sanitizer.py src/security_master/api/

# Restart API with security fixes
docker-compose -f docker/docker-compose.production.yml restart api
```

---

## Data Quality & Import Issues

### Issue: Institution Import Failures
**Symptoms:**
- CSV/XML/PDF imports failing with parsing errors
- Incomplete transaction data extraction
- Data validation failures

**Diagnosis:**
```bash
# Check import logs
tail -f /mnt/user/pp-security-prod/logs/import.log | grep ERROR

# Test individual parsers
poetry run python -c "
from src.security_master.extractor.wells_fargo import WellsFargoCSVExtractor
extractor = WellsFargoCSVExtractor()
result = extractor.extract('sample_data/wells_fargo_sample.csv')
print(result)
"

# Check file format validation
ls -la sample_data/
file sample_data/*.csv
```

**Solutions:**
```bash
# Update parser configurations
cp templates/extractors/enhanced_parsers.py src/security_master/extractor/

# Fix validation rules
sed -i 's/strict_validation=True/strict_validation=False/g' src/security_master/extractor/base.py

# Add fallback parsing
cp templates/extractors/fallback_parser.py src/security_master/extractor/

# Test fixes
poetry run python scripts/test_import.py --file sample_data/test_import.csv
```

### Issue: Data Quality Scoring Problems
**Symptoms:**
- Incorrect quality scores calculated
- Quality trends not updating
- Missing quality metrics

**Diagnosis:**
```bash
# Check quality calculation logic
grep -r "quality_score" src/security_master/
python -c "
from src.security_master.storage.data_quality import calculate_quality_score
score = calculate_quality_score({'isin': 'US1234567890', 'symbol': 'TEST'})
print('Quality score:', score)
"

# Check quality metrics in database
psql ${DATABASE_URL} -c "
SELECT institution, avg(quality_score) as avg_quality 
FROM data_quality_metrics 
GROUP BY institution 
ORDER BY avg_quality DESC;
"
```

**Solutions:**
```bash
# Recalculate all quality scores
poetry run python scripts/recalculate_quality_scores.py

# Update quality scoring algorithm
cp templates/data_quality/enhanced_scoring.py src/security_master/storage/data_quality.py

# Fix quality trend calculation
psql ${DATABASE_URL} -f sql/fixes/quality_trends_fix.sql

# Validate improvements
poetry run pytest tests/test_data_quality.py -v
```

### Issue: Cross-Institution Validation Problems
**Symptoms:**
- Duplicate securities not detected
- Inconsistent classifications across institutions
- Missing cross-validation warnings

**Diagnosis:**
```bash
# Check for duplicate securities
psql ${DATABASE_URL} -c "
SELECT isin, count(*) as count 
FROM securities 
GROUP BY isin 
HAVING count(*) > 1 
ORDER BY count DESC;
"

# Check classification consistency
psql ${DATABASE_URL} -c "
SELECT s.symbol, s.isin, array_agg(DISTINCT c.classification_type) as classifications
FROM securities s
JOIN classifications c ON s.id = c.security_id
GROUP BY s.symbol, s.isin
HAVING count(DISTINCT c.classification_type) > 1;
"
```

**Solutions:**
```bash
# Run deduplication process
poetry run python scripts/deduplicate_securities.py

# Fix classification conflicts
poetry run python scripts/resolve_classification_conflicts.py

# Update validation rules
cp templates/validation/enhanced_cross_validation.py src/security_master/storage/validators.py

# Validate fixes
poetry run python scripts/validate_data_consistency.py
```

---

## Backup & Recovery Issues

### Issue: Backup Failures
**Symptoms:**
- Scheduled backups not running
- Backup files corrupted or incomplete
- Recovery procedures failing

**Diagnosis:**
```bash
# Check backup schedule
crontab -l | grep backup
systemctl status cronie

# Check backup files
ls -la /mnt/user/pp-security-prod/backups/
du -sh /mnt/user/pp-security-prod/backups/*

# Test backup integrity
pg_dump ${DATABASE_URL} --schema-only | head
gpg --list-keys | grep backup
```

**Solutions:**
```bash
# Fix backup script permissions
chmod +x scripts/backup/automated_backup.sh

# Update backup schedule
crontab -e
# Add: 0 2 * * * /path/to/scripts/backup/automated_backup.sh

# Test backup process
./scripts/backup/automated_backup.sh --test

# Verify backup integrity
./scripts/backup/verify_backup.sh /mnt/user/pp-security-prod/backups/latest/
```

### Issue: Recovery Procedures Failing
**Symptoms:**
- Database restore errors
- Incomplete data after recovery
- Configuration not restored properly

**Diagnosis:**
```bash
# Check backup file integrity
gunzip -t /mnt/user/pp-security-prod/backups/latest/database_backup.sql.gz

# Check restore logs
tail -f /mnt/user/pp-security-prod/logs/restore.log

# Validate backup completeness
pg_restore --list /mnt/user/pp-security-prod/backups/latest/database_backup.dump
```

**Solutions:**
```bash
# Perform clean recovery
./scripts/backup/disaster_recovery.sh --backup-date=2024-01-15

# Verify data integrity after recovery
poetry run python scripts/verify_data_integrity.py

# Update recovery documentation
cp templates/procedures/disaster_recovery_updated.md docs/procedures/
```

---

## Development & Testing Issues

### Issue: Test Suite Failures
**Symptoms:**
- pytest failing with import errors
- Coverage reports incomplete
- Integration tests timing out

**Diagnosis:**
```bash
# Run tests with verbose output
poetry run pytest -v --tb=short

# Check test environment
poetry run python -c "
import sys
print('Python path:', sys.path[:3])
import src.security_master
print('Module location:', src.security_master.__file__)
"

# Check test database connectivity
poetry run pytest tests/test_db_connection.py -v
```

**Solutions:**
```bash
# Fix import paths
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
poetry run pytest -v

# Reset test database
dropdb security_master_test
createdb security_master_test
poetry run alembic -x test=true upgrade head

# Update test configuration
cp templates/testing/pytest_enhanced.ini pytest.ini
poetry install --with test

# Run tests with fresh environment
poetry run pytest --cov=src --cov-report=html
```

### Issue: Development Environment Setup
**Symptoms:**
- Poetry installation failing
- IDE integration not working
- Git hooks not executing

**Diagnosis:**
```bash
# Check Poetry installation
poetry --version
poetry config --list

# Check development dependencies
poetry show --tree
poetry check

# Check git configuration
git config --list | grep security-master
ls -la .git/hooks/
```

**Solutions:**
```bash
# Reinstall Poetry environment
poetry env remove python
poetry install --with dev,test

# Setup IDE integration
poetry run python scripts/setup_vscode.py

# Install git hooks
poetry run pre-commit install
poetry run pre-commit run --all-files

# Validate development setup
poetry run python -c "print('Development environment ready')"
```

---

## Deployment Automation Issues

### Issue: Cloudflare Tunnel Configuration
**Symptoms:**
- Tunnel not connecting properly
- SSL certificate errors
- Domain routing failures

**Diagnosis:**
```bash
# Check tunnel status
cloudflared tunnel list
cloudflared tunnel info pp-security-tunnel

# Check DNS configuration
nslookup pp-security.your-domain.com
curl -I https://pp-security.your-domain.com

# Check tunnel configuration
cat ~/.cloudflared/config.yml
```

**Solutions:**
```bash
# Restart tunnel service
sudo systemctl restart cloudflared
cloudflared tunnel run pp-security-tunnel

# Update tunnel configuration
cloudflared tunnel route dns pp-security-tunnel pp-security.your-domain.com

# Test tunnel connectivity
curl -H "CF-RAY: test" https://pp-security.your-domain.com/health
```

### Issue: Production Deployment Script Failures
**Symptoms:**
- Deployment script exiting with errors
- Services not starting after deployment
- Configuration not applied properly

**Diagnosis:**
```bash
# Check deployment script logs
./scripts/phase5/setup_enterprise_production.sh --dry-run

# Check service status after deployment
docker-compose -f docker/docker-compose.production.yml ps
docker-compose -f docker/docker-compose.production.yml logs --tail=50

# Validate deployment configuration
./scripts/validate_production.sh --verbose
```

**Solutions:**
```bash
# Run deployment with debug output
DEBUG=true ./scripts/phase5/setup_enterprise_production.sh

# Fix configuration issues
cp .env.example .env
# Update .env with production values

# Retry deployment with rollback capability
./scripts/phase5/setup_enterprise_production.sh --with-rollback

# Validate successful deployment
./scripts/validate_production.sh --comprehensive
```

---

## Quick Recovery Procedures

### Emergency System Recovery
```bash
#!/bin/bash
# Emergency recovery procedure

echo "=== Security-Master Emergency Recovery ==="

# 1. Stop all services
docker-compose -f docker/docker-compose.production.yml down

# 2. Check system resources
df -h
free -h
docker system df

# 3. Clean up if needed
docker system prune -f
docker volume prune -f

# 4. Restore from backup
./scripts/backup/disaster_recovery.sh --latest

# 5. Start core services first
docker-compose -f docker/docker-compose.production.yml up -d postgresql redis

# 6. Wait for database to be ready
sleep 30

# 7. Start application services
docker-compose -f docker/docker-compose.production.yml up -d api worker

# 8. Start monitoring services
docker-compose -f docker/docker-compose.production.yml up -d prometheus grafana

# 9. Validate recovery
./scripts/validate_production.sh --emergency-check

echo "=== Recovery Complete ==="
```

### Service-Specific Recovery
```bash
# Database recovery
docker-compose -f docker/docker-compose.production.yml stop postgresql
docker volume rm pp_security_pg_data_prod
./scripts/backup/restore_database.sh --latest
docker-compose -f docker/docker-compose.production.yml up -d postgresql

# Authentication recovery
docker-compose -f docker/docker-compose.production.yml restart api
docker exec pp_security_api_prod curl -f http://localhost:8000/auth/health

# Worker recovery
docker-compose -f docker/docker-compose.production.yml restart worker
docker exec pp_security_worker_prod celery inspect ping -A src.security_master.worker.celery_app

# Monitoring recovery
docker-compose -f docker/docker-compose.production.yml restart prometheus grafana
curl -f http://localhost:9090/-/healthy
curl -f http://localhost:3000/api/health
```

### Configuration Reset
```bash
# Reset all configuration to defaults
cp .env.example .env
cp docker/docker-compose.production.yml.template docker/docker-compose.production.yml
cp monitoring/prometheus.yml.template monitoring/prometheus.yml

# Regenerate secrets
export DATABASE_PASSWORD="$(openssl rand -base64 32)"
export JWT_SECRET="$(openssl rand -base64 64)"
export REDIS_PASSWORD="$(openssl rand -base64 32)"

# Update configuration files
sed -i "s/PLACEHOLDER_DB_PASSWORD/${DATABASE_PASSWORD}/g" .env
sed -i "s/PLACEHOLDER_JWT_SECRET/${JWT_SECRET}/g" .env
sed -i "s/PLACEHOLDER_REDIS_PASSWORD/${REDIS_PASSWORD}/g" .env

# Encrypt and save
gpg --symmetric --cipher-algo AES256 .env
rm .env
```

---

## Support Contact Information

### Internal Support
- **Development Team**: security-master-dev@company.com
- **Infrastructure Team**: infra@company.com  
- **Security Team**: security@company.com
- **Database Team**: dba@company.com

### External Support
- **PromptCraft Integration**: https://github.com/pp-security/PromptCraft/issues
- **Portfolio Performance**: https://forum.portfolio-performance.info/
- **OpenFIGI API**: https://www.openfigi.com/support
- **Cloudflare Support**: https://support.cloudflare.com/

### Documentation
- **Security-Master Wiki**: https://wiki.company.com/security-master
- **Runbook**: docs/operations/runbook.md
- **API Documentation**: https://pp-security.your-domain.com/docs
- **Architecture**: docs/adr/

---

**This troubleshooting guide covers the most common issues encountered during Phase 5 enterprise deployment. For issues not covered here, consult the detailed execution guide and validation checklist, or contact the development team.**

*Last updated: 2024-01-15*
*Version: 1.0.0*
*Phase 5 Enterprise Production Guide*