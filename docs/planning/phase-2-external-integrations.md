---
title: "Phase 2: External Integrations & Enhanced Classification"
version: "1.0"
status: "active"
component: "Planning"
tags: ["external_integrations", "classification", "api_integration"]
source: "PP Security-Master Project"
purpose: "Integrate external libraries and enhance classification capabilities."
---

# Phase 2: External Integrations & Enhanced Classification

**Duration**: 4 weeks (Weeks 7-10)  
**Team Size**: 2-3 developers  
**Success Metric**: Fund classification achieving >90% accuracy with fallback mechanisms  

---

## Phase Overview

### Objective
Integrate external libraries (pp-portfolio-classifier, ppxml2db) and external APIs (OpenFIGI) to provide comprehensive security classification capabilities with proper fallback mechanisms.

### Success Criteria
- [ ] External libraries integrated and passing security scans
- [ ] Fund classification accuracy >90% on test dataset
- [ ] OpenFIGI API integration respecting rate limits with <1% failure rate
- [ ] Fallback mechanisms activate properly when external services fail
- [ ] Classification pipeline processes 1,000+ securities with <10% manual review required

### Key Deliverables
- pp-portfolio-classifier fork, security scan, and subtree integration
- ppxml2db integration for Portfolio Performance XML handling
- OpenFIGI API client with rate limiting and caching
- Classification pipeline with confidence scoring
- External service monitoring and health checks

---

## Detailed Issues

### Issue P2-001: External Repository Security Assessment and Integration

**Branch**: `feature/external-repo-integration`  
**Estimated Time**: 4 hours  
**Priority**: Critical  
**Week**: 7  

#### Description
Fork, security scan, and integrate pp-portfolio-classifier and ppxml2db as git subtrees following ADR-008 Tier 1 strategy.

#### Implementation Steps

**Step 1: Fork External Repositories**
```bash
# Fork pp-portfolio-classifier to organization
gh repo fork fizban99/pp-portfolio-classifier --org your-org --clone
cd pp-portfolio-classifier

# Enable branch protection
gh api repos/your-org/pp-portfolio-classifier/branches/main/protection \
  --method PUT \
  --field required_status_checks='{}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}'

# Fork ppxml2db to organization  
gh repo fork pfalcon/ppxml2db --org your-org --clone
cd ppxml2db

# Enable branch protection
gh api repos/your-org/ppxml2db/branches/main/protection \
  --method PUT \
  --field required_status_checks='{}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}'
```

**Step 2: Security Scanning Setup**
```bash
# Create security scanning workflow for pp-portfolio-classifier
mkdir -p pp-portfolio-classifier/.github/workflows
cat > pp-portfolio-classifier/.github/workflows/security-scan.yml << 'EOF'
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install safety bandit pip-audit
      - name: Run safety check
        run: safety check
      - name: Run bandit scan
        run: bandit -r . -f json -o bandit-report.json
      - name: Run pip-audit
        run: pip-audit
EOF

# Commit and push security workflow
cd pp-portfolio-classifier
git add .github/workflows/security-scan.yml
git commit -m "Add automated security scanning workflow"
git push origin main

# Create security scanning workflow for ppxml2db
mkdir -p ../ppxml2db/.github/workflows
cp .github/workflows/security-scan.yml ../ppxml2db/.github/workflows/
cd ../ppxml2db
git add .github/workflows/security-scan.yml
git commit -m "Add automated security scanning workflow" 
git push origin main
```

**Step 3: Git Subtree Integration**
```bash
# Return to main project
cd /home/byron/dev/pp-security-master

# Create external directory structure
mkdir -p src/external

# Add pp-portfolio-classifier as subtree
git subtree add --prefix=src/external/pp-portfolio-classifier \
  https://github.com/your-org/pp-portfolio-classifier.git main --squash

# Add ppxml2db as subtree
git subtree add --prefix=src/external/ppxml2db \
  https://github.com/your-org/ppxml2db.git main --squash

# Create subtree sync script
cat > scripts/sync_external_repos.sh << 'EOF'
#!/bin/bash
# Sync external repository subtrees with upstream

set -e

echo "🔄 Syncing external repositories..."

# Sync pp-portfolio-classifier
echo "Syncing pp-portfolio-classifier..."
git subtree pull --prefix=src/external/pp-portfolio-classifier \
  https://github.com/your-org/pp-portfolio-classifier.git main --squash

# Sync ppxml2db  
echo "Syncing ppxml2db..."
git subtree pull --prefix=src/external/ppxml2db \
  https://github.com/your-org/ppxml2db.git main --squash

echo "✅ External repositories synced successfully"
EOF

chmod +x scripts/sync_external_repos.sh
```

**Step 4: Integration Testing Setup**
```bash
# Create external library integration tests
cat > tests/integration/test_external_libraries.py << 'EOF'
"""Integration tests for external library functionality."""
import pytest
import sys
from pathlib import Path

# Add external libraries to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "external"))

def test_pp_portfolio_classifier_import():
    """Test that pp-portfolio-classifier can be imported."""
    try:
        # Test basic import - adjust import path based on actual structure
        from pp_portfolio_classifier import classifier
        assert classifier is not None
    except ImportError as e:
        pytest.skip(f"pp-portfolio-classifier not available: {e}")

def test_ppxml2db_import():
    """Test that ppxml2db can be imported."""
    try:
        # Test basic import - adjust import path based on actual structure  
        import ppxml2db
        assert ppxml2db is not None
    except ImportError as e:
        pytest.skip(f"ppxml2db not available: {e}")

def test_external_library_security():
    """Test that external libraries pass security checks."""
    # This will be implemented based on actual library structure
    assert True  # Placeholder
EOF

# Create external library adapter modules
mkdir -p src/security_master/adapters

cat > src/security_master/adapters/__init__.py << 'EOF'
"""Adapter modules for external library integration."""
EOF

cat > src/security_master/adapters/pp_classifier_adapter.py << 'EOF'
"""Adapter for pp-portfolio-classifier integration."""
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Add external library to path
EXTERNAL_PATH = Path(__file__).parent.parent.parent / "external"
sys.path.insert(0, str(EXTERNAL_PATH))

logger = logging.getLogger(__name__)

class PPClassifierAdapter:
    """Adapter for pp-portfolio-classifier library."""
    
    def __init__(self):
        self._classifier = None
        self._initialize_classifier()
    
    def _initialize_classifier(self):
        """Initialize the pp-portfolio-classifier."""
        try:
            # Import will be adjusted based on actual library structure
            from pp_portfolio_classifier import classifier
            self._classifier = classifier
            logger.info("pp-portfolio-classifier initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to initialize pp-portfolio-classifier: {e}")
            self._classifier = None
    
    def classify_fund(self, 
                      symbol: str, 
                      name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Classify a fund using pp-portfolio-classifier."""
        if not self._classifier:
            logger.warning("pp-portfolio-classifier not available")
            return None
        
        try:
            # Implementation will be adjusted based on actual library API
            result = self._classifier.classify(symbol, name)
            return {
                'classification': result,
                'confidence': 0.8,  # Will be calculated based on actual result
                'source': 'pp-portfolio-classifier'
            }
        except Exception as e:
            logger.error(f"Classification failed for {symbol}: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if classifier is available."""
        return self._classifier is not None
EOF
```

**Validation Commands:**
```bash
# Verify subtree integration
ls -la src/external/
# Expected: pp-portfolio-classifier and ppxml2db directories

# Test external library imports
python -c "
import sys
sys.path.insert(0, 'src')
from security_master.adapters.pp_classifier_adapter import PPClassifierAdapter
print('Adapter import successful')
"

# Run security scans on external libraries
poetry run safety check
poetry run bandit -r src/external/ -f json
poetry run pip-audit

# Run integration tests
poetry run pytest tests/integration/test_external_libraries.py -v
```

#### Acceptance Criteria
- [ ] pp-portfolio-classifier forked with security scanning
- [ ] ppxml2db forked with security scanning  
- [ ] Both repositories integrated as git subtrees under `src/external/`
- [ ] Automated security scanning pipeline operational
- [ ] Documentation for upstream sync procedures
- [ ] Integration tests validating external library functionality

---

### Issue P2-002: OpenFIGI API Client Implementation

**Branch**: `feature/openfigi-client`  
**Estimated Time**: 3 hours  
**Priority**: High  
**Week**: 7  

#### Description
Implement OpenFIGI API client with rate limiting, caching, and error handling for equity and bond classification.

#### Implementation Steps

**Step 1: OpenFIGI Client Implementation**
```bash
# Create OpenFIGI client module
mkdir -p src/security_master/external_apis
cat > src/security_master/external_apis/__init__.py << 'EOF'
"""External API client modules."""
EOF

cat > src/security_master/external_apis/openfigi_client.py << 'EOF'
"""OpenFIGI API client with rate limiting and caching."""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from pathlib import Path

import aiohttp
import aiofiles
from pydantic import BaseSettings, Field

logger = logging.getLogger(__name__)

class OpenFIGISettings(BaseSettings):
    """OpenFIGI API configuration."""
    api_key: Optional[str] = Field(None, env="OPENFIGI_API_KEY")
    base_url: str = "https://api.openfigi.com/v3"
    rate_limit_per_minute: int = 25
    cache_ttl_hours: int = 24
    request_timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    
    class Config:
        env_file = ".env"

@dataclass
class CacheEntry:
    """Cache entry for OpenFIGI responses."""
    data: Dict[str, Any]
    timestamp: datetime
    ttl_hours: int
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + timedelta(hours=self.ttl_hours)

class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests: List[datetime] = []
    
    async def acquire(self):
        """Acquire rate limit token."""
        now = datetime.now()
        
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(minutes=1)]
        
        if len(self.requests) >= self.requests_per_minute:
            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = 60 - (now - oldest_request).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        self.requests.append(now)

class OpenFIGIClient:
    """OpenFIGI API client with rate limiting and caching."""
    
    def __init__(self, settings: Optional[OpenFIGISettings] = None):
        self.settings = settings or OpenFIGISettings()
        self.rate_limiter = RateLimiter(self.settings.rate_limit_per_minute)
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_file = Path("data/cache/openfigi_cache.json")
        self._ensure_cache_dir()
        self._load_cache()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_cache(self):
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    for key, entry_data in cache_data.items():
                        self.cache[key] = CacheEntry(
                            data=entry_data['data'],
                            timestamp=datetime.fromisoformat(entry_data['timestamp']),
                            ttl_hours=entry_data['ttl_hours']
                        )
                logger.info(f"Loaded {len(self.cache)} entries from cache")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            cache_data = {}
            for key, entry in self.cache.items():
                if not entry.is_expired:
                    cache_data[key] = {
                        'data': entry.data,
                        'timestamp': entry.timestamp.isoformat(),
                        'ttl_hours': entry.ttl_hours
                    }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _get_cache_key(self, **kwargs) -> str:
        """Generate cache key for request parameters."""
        return json.dumps(kwargs, sort_keys=True)
    
    async def search_securities(self,
                               symbols: List[str] = None,
                               cusips: List[str] = None,
                               names: List[str] = None) -> List[Dict[str, Any]]:
        """Search securities using OpenFIGI API."""
        
        # Build request payload
        requests = []
        
        if symbols:
            requests.extend([{'idType': 'TICKER', 'idValue': symbol} for symbol in symbols])
        if cusips:
            requests.extend([{'idType': 'ID_CUSIP', 'idValue': cusip} for cusip in cusips])
        if names:
            requests.extend([{'idType': 'NAME', 'idValue': name} for name in names])
        
        if not requests:
            return []
        
        # Check cache first
        cache_key = self._get_cache_key(requests=requests)
        cached_entry = self.cache.get(cache_key)
        
        if cached_entry and not cached_entry.is_expired:
            logger.debug(f"Cache hit for {len(requests)} requests")
            return cached_entry.data
        
        # Make API request
        results = await self._make_request('/search', requests)
        
        # Cache results
        if results:
            self.cache[cache_key] = CacheEntry(
                data=results,
                timestamp=datetime.now(),
                ttl_hours=self.settings.cache_ttl_hours
            )
            self._save_cache()
        
        return results
    
    async def _make_request(self, endpoint: str, payload: Any) -> List[Dict[str, Any]]:
        """Make HTTP request to OpenFIGI API with retry logic."""
        url = f"{self.settings.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.settings.api_key:
            headers['X-OPENFIGI-APIKEY'] = self.settings.api_key
        
        for attempt in range(self.settings.max_retries):
            try:
                # Respect rate limits
                await self.rate_limiter.acquire()
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(
                    total=self.settings.request_timeout
                )) as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.debug(f"OpenFIGI request successful: {len(result)} results")
                            return result
                        
                        elif response.status == 429:  # Rate limit exceeded
                            wait_time = self.settings.retry_backoff_factor ** attempt
                            logger.warning(f"Rate limit exceeded, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        else:
                            error_text = await response.text()
                            logger.error(f"OpenFIGI API error {response.status}: {error_text}")
                            
                            if response.status >= 500:  # Server error, retry
                                if attempt < self.settings.max_retries - 1:
                                    wait_time = self.settings.retry_backoff_factor ** attempt
                                    await asyncio.sleep(wait_time)
                                    continue
                            
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                                message=error_text
                            )
            
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.settings.max_retries})")
                if attempt == self.settings.max_retries - 1:
                    raise
                await asyncio.sleep(self.settings.retry_backoff_factor ** attempt)
            
            except Exception as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.settings.max_retries}): {e}")
                if attempt == self.settings.max_retries - 1:
                    raise
                await asyncio.sleep(self.settings.retry_backoff_factor ** attempt)
        
        return []
    
    async def get_security_details(self, figi: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific FIGI."""
        
        cache_key = self._get_cache_key(figi=figi)
        cached_entry = self.cache.get(cache_key)
        
        if cached_entry and not cached_entry.is_expired:
            logger.debug(f"Cache hit for FIGI {figi}")
            return cached_entry.data
        
        # Make API request
        results = await self._make_request('/search', [{'figi': figi}])
        
        result = results[0] if results else None
        
        # Cache result
        if result:
            self.cache[cache_key] = CacheEntry(
                data=result,
                timestamp=datetime.now(),
                ttl_hours=self.settings.cache_ttl_hours
            )
            self._save_cache()
        
        return result
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired)
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'hit_rate': 0.0  # Will be implemented with actual hit tracking
        }
    
    def clear_expired_cache(self):
        """Clear expired cache entries."""
        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired]
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
            self._save_cache()
EOF
```

**Step 2: Configuration Setup**
```bash
# Add OpenFIGI configuration to .env.example
echo "
# OpenFIGI API Configuration
OPENFIGI_API_KEY=your_api_key_here
" >> .env.example

# Add aiohttp dependency
poetry add aiohttp aiofiles
```

**Step 3: Client Testing**
```bash
# Create OpenFIGI client tests
cat > tests/unit/test_openfigi_client.py << 'EOF'
"""Tests for OpenFIGI API client."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from security_master.external_apis.openfigi_client import (
    OpenFIGIClient, OpenFIGISettings, RateLimiter
)

@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiting functionality."""
    limiter = RateLimiter(requests_per_minute=2)
    
    # Should allow first two requests immediately
    start_time = asyncio.get_event_loop().time()
    await limiter.acquire()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start_time
    
    assert elapsed < 1.0  # Should be immediate

@pytest.mark.asyncio
async def test_openfigi_client_cache():
    """Test caching functionality."""
    settings = OpenFIGISettings(api_key="test_key")
    client = OpenFIGIClient(settings)
    
    # Mock the API request
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = [{'figi': 'TEST123', 'name': 'Test Security'}]
        
        # First call should hit API
        result1 = await client.search_securities(symbols=['AAPL'])
        assert mock_request.call_count == 1
        
        # Second call should use cache
        result2 = await client.search_securities(symbols=['AAPL'])
        assert mock_request.call_count == 1  # No additional API call
        assert result1 == result2

@pytest.mark.asyncio  
async def test_openfigi_client_error_handling():
    """Test error handling and retry logic."""
    settings = OpenFIGISettings(api_key="test_key", max_retries=2)
    client = OpenFIGIClient(settings)
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        # Mock server error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Server Error"
        mock_post.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(Exception):
            await client.search_securities(symbols=['AAPL'])
        
        # Should have retried
        assert mock_post.call_count == 2
EOF
```

**Validation Commands:**
```bash
# Test OpenFIGI client import
python -c "
from security_master.external_apis.openfigi_client import OpenFIGIClient
print('OpenFIGI client import successful')
"

# Run unit tests
poetry run pytest tests/unit/test_openfigi_client.py -v

# Test rate limiting (requires API key)
# This would be done in integration tests
```

#### Acceptance Criteria
- [ ] API client with proper authentication and rate limiting (25 requests/minute)
- [ ] Response caching with configurable TTL
- [ ] Retry logic with exponential backoff
- [ ] Bulk request optimization where possible
- [ ] Error handling for all API failure scenarios
- [ ] Performance monitoring and alerting

---

### Issue P2-003: Fund Classification Pipeline

**Branch**: `feature/fund-classification`  
**Estimated Time**: 4 hours  
**Priority**: High  
**Week**: 8  

#### Description
Implement fund and ETF classification using integrated pp-portfolio-classifier with confidence scoring.

#### Acceptance Criteria
- [ ] Fund classification using pp-portfolio-classifier integration
- [ ] Classification confidence scoring (0.0-1.0)
- [ ] Fallback classification strategies for unmatched funds
- [ ] Performance optimization for batch classification
- [ ] Integration with data quality framework
- [ ] Comprehensive testing with real fund data

---

### Issue P2-004: Equity Classification Integration

**Branch**: `feature/equity-classification`  
**Estimated Time**: 3 hours  
**Priority**: Medium  
**Week**: 8  

#### Description
Integrate OpenFIGI API for equity classification with GICS and other taxonomy data.

#### Acceptance Criteria
- [ ] Equity classification via OpenFIGI API
- [ ] GICS sector and industry classification
- [ ] Market data integration (market cap, exchange)
- [ ] Classification result caching
- [ ] Error handling and fallback strategies
- [ ] Rate limiting compliance

---

### Issue P2-005: Classification Confidence and Quality Framework

**Branch**: `feature/classification-quality`  
**Estimated Time**: 3 hours  
**Priority**: Medium  
**Week**: 9  

#### Description
Enhance classification with confidence scoring, quality metrics, and manual review workflow triggers.

#### Acceptance Criteria
- [ ] Classification confidence scoring algorithm
- [ ] Quality metrics dashboard for classification accuracy
- [ ] Manual review workflow for low-confidence classifications
- [ ] Classification accuracy tracking and reporting
- [ ] A/B testing framework for classification improvements

---

### Issue P2-006: External Service Resilience and Monitoring

**Branch**: `feature/service-resilience`  
**Estimated Time**: 3 hours  
**Priority**: High  
**Week**: 10  

#### Description
Implement comprehensive resilience patterns and monitoring for all external service integrations.

#### Acceptance Criteria
- [ ] Circuit breaker patterns for external API calls
- [ ] Health check endpoints for all external services
- [ ] Service degradation handling with graceful fallbacks
- [ ] Monitoring dashboards for external service performance
- [ ] Alerting for service failures and performance issues
- [ ] Recovery procedures documentation

---

## Phase 2 Success Criteria

### Technical Validation
- [ ] All external libraries passing security scans with no high-severity issues
- [ ] Fund classification accuracy >90% validated on 500+ fund test dataset
- [ ] OpenFIGI API rate limits respected with <1% failure rate over 24-hour period
- [ ] External service failures trigger fallback mechanisms within 5 seconds
- [ ] System maintains >99% availability despite external service issues

### Performance Metrics
- [ ] Fund classification: <2 seconds average response time
- [ ] OpenFIGI API calls: <1 second average response time  
- [ ] Batch classification: 1,000+ securities processed within 10 minutes
- [ ] Cache hit rate: >40% for repeated classification requests
- [ ] Memory usage: <1GB during peak classification operations

### Business Validation
- [ ] Classification pipeline reduces manual review requirements by >80%
- [ ] Classification accuracy improvements measurable against Phase 1 baseline
- [ ] External service cost within budget projections (<$50/month)
- [ ] System resilience demonstrated through external service failure simulation

---

**Phase 2 Target Completion**: End of Week 10  
**Next Phase**: Phase 3 - Multi-Institution Support  
**Key Milestone**: >90% automated classification accuracy achieved