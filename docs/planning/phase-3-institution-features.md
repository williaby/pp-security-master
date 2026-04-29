---
title: "Phase 3: Institution-Specific Features & Multi-Institution Support"
version: "1.0"
status: "active"
component: "Planning"
tags: ["multi_institution", "data_adapters", "validation"]
source: "PP Security-Master Project"
purpose: "Multi-institution support with complete data pipeline validation."
---

# Phase 3: Institution-Specific Features & Multi-Institution Support

**Duration**: 4 weeks (Weeks 11-14)  
**Team Size**: 2-4 developers  
**Success Metric**: All four institutions importing data with cross-validation operational  

---

## Phase Overview

### Objective

Implement complete multi-institution support with specialized data adapters for Interactive Brokers, AltoIRA, and Kubera, plus advanced cross-institution validation and data quality frameworks.

### Success Criteria

- [ ] All four institutions (Wells Fargo, IBKR, AltoIRA, Kubera) importing successfully
- [ ] Cross-institution validation identifies discrepancies with >95% accuracy  
- [ ] Batch processing handles 50,000+ transactions across all institutions
- [ ] Manual review workflow reduces manual effort by >80%
- [ ] Data quality scores show consistent improvement across all institutions

### Key Deliverables

- Interactive Brokers Flex Query XML parser with derivatives support
- AltoIRA PDF parsing with OCR confidence scoring
- Kubera JSON API integration for validation and reconciliation
- Advanced cross-institution data quality validation
- Comprehensive batch processing and manual review workflows

---

## Detailed Issues

### Issue P3-001: Interactive Brokers Flex Query Parser

**Branch**: `feature/ibkr-flex-parser`  
**Estimated Time**: 4 hours  
**Priority**: High  
**Week**: 11  

#### Description

Implement IBKR Flex Query XML parser supporting complex derivatives, options, and international securities.

#### Implementation Steps

#### Step 1: IBKR XML Parser Structure Setup

```bash
# Create IBKR extractor module
mkdir -p src/security_master/extractor/interactive_brokers
cat > src/security_master/extractor/interactive_brokers/__init__.py << 'EOF'
"""Interactive Brokers Flex Query XML parser."""
EOF

cat > src/security_master/extractor/interactive_brokers/models.py << 'EOF'
"""IBKR transaction and position models."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class IBKRTransactionType(Enum):
    """IBKR transaction types from Flex Query."""
    TRADE = "Trade"
    FOREX = "ForexTradeP&L"
    CORPORATE_ACTION = "CorporateAction"
    CASH = "CashTransaction"
    DIVIDEND = "Dividend"
    WITHHOLDING_TAX = "WithholdingTax"
    INTEREST = "InterestAccrualsCurrency"

class IBKRAssetCategory(Enum):
    """IBKR asset categories."""
    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    CASH = "CASH"
    FOREX = "FOREX"
    BOND = "BOND"
    ETF = "ETF"
    INDEX = "IND"

class IBKRTransaction(BaseModel):
    """IBKR Flex Query transaction model."""
    
    # Core transaction fields
    account_id: str = Field(..., description="IBKR account identifier")
    trade_id: Optional[str] = Field(None, description="Unique trade ID for audit trail")
    order_id: Optional[str] = Field(None, description="Order reference ID")
    execution_id: Optional[str] = Field(None, description="Execution ID")
    
    # Transaction details
    transaction_type: IBKRTransactionType
    transaction_date: date
    settlement_date: Optional[date] = None
    
    # Security identification
    symbol: Optional[str] = None
    description: Optional[str] = None
    conid: Optional[str] = Field(None, description="IBKR contract ID")
    isin: Optional[str] = None
    cusip: Optional[str] = None
    underlying_symbol: Optional[str] = Field(None, description="For derivatives")
    asset_category: Optional[IBKRAssetCategory] = None
    
    # Derivatives-specific fields
    strike: Optional[Decimal] = Field(None, description="Strike price for options")
    expiry_date: Optional[date] = Field(None, description="Expiration date for derivatives")
    put_call: Optional[str] = Field(None, description="P for Put, C for Call")
    multiplier: Optional[Decimal] = Field(Decimal('1'), description="Contract multiplier")
    
    # Transaction amounts
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    proceeds: Optional[Decimal] = None
    
    # Multi-currency support
    currency: str = Field(default="USD")
    fx_rate_to_base: Optional[Decimal] = Field(Decimal('1'), description="FX rate to base currency")
    
    # IBKR-specific fees
    commission: Optional[Decimal] = None
    regulatory_fees: Optional[Decimal] = None
    exchange_fees: Optional[Decimal] = None
    other_fees: Optional[Decimal] = None
    total_fees: Optional[Decimal] = None
    
    # Data quality and processing
    data_quality_score: Optional[Decimal] = Field(None, ge=0, le=1)
    raw_xml_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    processing_notes: Optional[str] = None
    
    @validator('data_quality_score', always=True)
    def calculate_quality_score(cls, v, values):
        """Calculate data quality score based on field completeness."""
        if v is not None:
            return v
            
        required_fields = ['account_id', 'transaction_type', 'transaction_date']
        important_fields = ['symbol', 'quantity', 'price', 'currency']
        
        score = 0.5  # Base score
        
        # Check required fields
        required_score = sum(1 for field in required_fields if values.get(field) is not None)
        score += (required_score / len(required_fields)) * 0.3
        
        # Check important fields
        important_score = sum(1 for field in important_fields if values.get(field) is not None)
        score += (important_score / len(important_fields)) * 0.2
        
        return min(Decimal(str(score)), Decimal('1.0'))
EOF

# Install XML parsing dependencies
poetry add lxml xmltodict
```

## Step 2: IBKR XML Parser Implementation

```bash
cat > src/security_master/extractor/interactive_brokers/parser.py << 'EOF'
"""IBKR Flex Query XML parser implementation."""
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Iterator, Any
from decimal import Decimal, InvalidOperation
from uuid import UUID

from .models import IBKRTransaction, IBKRTransactionType, IBKRAssetCategory
from ...batch.service import BatchManager
from ...batch.models import Institution, BatchStatus

logger = logging.getLogger(__name__)

class IBKRFlexQueryParser:
    """Parser for IBKR Flex Query XML reports."""
    
    def __init__(self, batch_manager: BatchManager = None):
        self.batch_manager = batch_manager or BatchManager()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # XML namespace mappings for different IBKR report versions
        self.namespaces = {
            'v1': 'http://www.interactivebrokers.com/schemas/IBFlexStatementSchema/FlexQueryResponse',
            'v2': 'http://www.interactivebrokers.com/schemas/FlexStatement'
        }
    
    def parse_file(self, xml_path: Path, created_by: str = "system") -> Dict[str, Any]:
        """Parse IBKR Flex Query XML file."""
        
        # Create import batch
        batch = self.batch_manager.create_batch(
            institution=Institution.INTERACTIVE_BROKERS,
            file_path=xml_path,
            created_by=created_by
        )
        
        try:
            self.batch_manager.start_processing(batch.id)
            
            # Parse XML structure
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Detect XML schema version and namespace
            namespace = self._detect_namespace(root)
            
            # Extract transactions from different report sections
            transactions = []
            
            # Parse Trades section
            trades = self._parse_trades(root, namespace)
            transactions.extend(trades)
            
            # Parse Corporate Actions
            corporate_actions = self._parse_corporate_actions(root, namespace)
            transactions.extend(corporate_actions)
            
            # Parse Cash Transactions
            cash_transactions = self._parse_cash_transactions(root, namespace)
            transactions.extend(cash_transactions)
            
            # Parse Forex transactions
            forex_transactions = self._parse_forex_transactions(root, namespace)
            transactions.extend(forex_transactions)
            
            # Validate and clean transactions
            valid_transactions = self._validate_transactions(transactions)
            
            # Calculate statistics
            statistics = {
                'total_records': len(transactions),
                'valid_records': len(valid_transactions),
                'invalid_records': len(transactions) - len(valid_transactions),
                'duplicate_records': 0,  # Will implement duplicate detection
                'skipped_records': 0
            }
            
            # Calculate average quality score
            if valid_transactions:
                quality_scores = [float(t.data_quality_score) for t in valid_transactions]
                avg_quality_score = sum(quality_scores) / len(quality_scores)
            else:
                avg_quality_score = 0.0
            
            self.batch_manager.complete_batch(
                batch.id,
                statistics,
                data_quality_score=avg_quality_score
            )
            
            return {
                'batch_id': batch.id,
                'transactions': valid_transactions,
                'statistics': statistics,
                'namespace_version': namespace
            }
            
        except Exception as e:
            self.logger.error(f"IBKR XML parsing failed for {xml_path}: {e}")
            self.batch_manager.fail_batch(batch.id, str(e))
            raise
    
    def _detect_namespace(self, root: ET.Element) -> Optional[str]:
        """Detect XML namespace version."""
        for version, namespace_uri in self.namespaces.items():
            if namespace_uri in root.tag or root.get('xmlns') == namespace_uri:
                return namespace_uri
        return None
    
    def _parse_trades(self, root: ET.Element, namespace: Optional[str]) -> List[IBKRTransaction]:
        """Parse trades section from XML."""
        transactions = []
        
        # Find Trades section - try different possible paths
        trade_elements = []
        
        # Common IBKR XML structures
        possible_paths = [
            './/Trade',
            './/Trades/Trade',
            './/FlexStatement/Trades/Trade',
            './/FlexQueryResponse/FlexStatements/FlexStatement/Trades/Trade'
        ]
        
        for path in possible_paths:
            elements = root.findall(path)
            if elements:
                trade_elements = elements
                break
        
        for trade_elem in trade_elements:
            try:
                transaction = self._parse_trade_element(trade_elem)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                self.logger.warning(f"Failed to parse trade element: {e}")
                continue
        
        return transactions
    
    def _parse_trade_element(self, elem: ET.Element) -> Optional[IBKRTransaction]:
        """Parse individual trade element."""
        
        def get_text_or_none(tag_name: str) -> Optional[str]:
            value = elem.get(tag_name) or elem.findtext(tag_name)
            return value.strip() if value else None
        
        def get_decimal_or_none(tag_name: str) -> Optional[Decimal]:
            value = get_text_or_none(tag_name)
            if value:
                try:
                    return Decimal(value)
                except (InvalidOperation, ValueError):
                    return None
            return None
        
        def get_date_or_none(tag_name: str) -> Optional[date]:
            value = get_text_or_none(tag_name)
            if value:
                try:
                    # IBKR date formats: YYYY-MM-DD or YYYYMMDD
                    if '-' in value:
                        return datetime.strptime(value, '%Y-%m-%d').date()
                    else:
                        return datetime.strptime(value, '%Y%m%d').date()
                except ValueError:
                    return None
            return None
        
        # Extract core fields
        account_id = get_text_or_none('accountId') or get_text_or_none('account')
        if not account_id:
            return None
        
        # Determine transaction type
        transaction_type = IBKRTransactionType.TRADE
        
        # Parse asset category
        asset_cat_str = get_text_or_none('assetCategory')
        asset_category = None
        if asset_cat_str:
            try:
                asset_category = IBKRAssetCategory(asset_cat_str)
            except ValueError:
                asset_category = None
        
        # Extract all transaction data
        transaction_data = {
            'account_id': account_id,
            'trade_id': get_text_or_none('tradeID'),
            'order_id': get_text_or_none('orderID'),
            'execution_id': get_text_or_none('execID'),
            'transaction_type': transaction_type,
            'transaction_date': get_date_or_none('tradeDate') or get_date_or_none('dateTime'),
            'settlement_date': get_date_or_none('settleDateTarget'),
            'symbol': get_text_or_none('symbol'),
            'description': get_text_or_none('description'),
            'conid': get_text_or_none('conid'),
            'isin': get_text_or_none('isin'),
            'cusip': get_text_or_none('cusip'),
            'underlying_symbol': get_text_or_none('underlyingSymbol'),
            'asset_category': asset_category,
            'strike': get_decimal_or_none('strike'),
            'expiry_date': get_date_or_none('expiry'),
            'put_call': get_text_or_none('putCall'),
            'multiplier': get_decimal_or_none('multiplier'),
            'quantity': get_decimal_or_none('quantity'),
            'price': get_decimal_or_none('tradePrice'),
            'proceeds': get_decimal_or_none('proceeds'),
            'currency': get_text_or_none('currency') or 'USD',
            'fx_rate_to_base': get_decimal_or_none('fxRateToBase'),
            'commission': get_decimal_or_none('ibCommission'),
            'regulatory_fees': get_decimal_or_none('regulatoryFees'),
            'exchange_fees': get_decimal_or_none('exchangeFees'),
            'other_fees': get_decimal_or_none('otherFees'),
            'total_fees': get_decimal_or_none('totalFees'),
            'raw_xml_data': dict(elem.attrib)
        }
        
        return IBKRTransaction(**transaction_data)
    
    def _parse_corporate_actions(self, root: ET.Element, namespace: Optional[str]) -> List[IBKRTransaction]:
        """Parse corporate actions section."""
        # Implementation similar to _parse_trades but for corporate actions
        return []
    
    def _parse_cash_transactions(self, root: ET.Element, namespace: Optional[str]) -> List[IBKRTransaction]:
        """Parse cash transactions section."""
        # Implementation for dividends, interest, fees, etc.
        return []
    
    def _parse_forex_transactions(self, root: ET.Element, namespace: Optional[str]) -> List[IBKRTransaction]:
        """Parse forex transactions section."""
        # Implementation for forex trades
        return []
    
    def _validate_transactions(self, transactions: List[IBKRTransaction]) -> List[IBKRTransaction]:
        """Validate and filter transactions."""
        valid_transactions = []
        
        for transaction in transactions:
            validation_errors = []
            
            # Required field validation
            if not transaction.account_id:
                validation_errors.append("Missing account ID")
            
            if not transaction.transaction_date:
                validation_errors.append("Missing transaction date")
            
            # Derivatives validation
            if transaction.asset_category == IBKRAssetCategory.OPTION:
                if not transaction.strike:
                    validation_errors.append("Options missing strike price")
                if not transaction.expiry_date:
                    validation_errors.append("Options missing expiry date")
                if not transaction.put_call:
                    validation_errors.append("Options missing put/call designation")
            
            # Currency validation
            if transaction.fx_rate_to_base and transaction.fx_rate_to_base <= 0:
                validation_errors.append("Invalid FX rate")
            
            if validation_errors:
                self.logger.warning(f"Transaction validation failed: {'; '.join(validation_errors)}")
                # Optionally add to invalid transactions list
            else:
                valid_transactions.append(transaction)
        
        return valid_transactions
EOF
```

## Step 3: Integration Testing

```bash
# Create IBKR parser tests
cat > tests/unit/test_ibkr_parser.py << 'EOF'
"""Tests for IBKR Flex Query parser."""
import pytest
from pathlib import Path
from decimal import Decimal
from datetime import date
import xml.etree.ElementTree as ET

from security_master.extractor.interactive_brokers.parser import IBKRFlexQueryParser
from security_master.extractor.interactive_brokers.models import IBKRTransaction, IBKRAssetCategory

@pytest.fixture
def sample_ibkr_xml():
    """Sample IBKR XML for testing."""
    return '''
    <?xml version="1.0" encoding="UTF-8"?>
    <FlexQueryResponse>
        <FlexStatements count="1">
            <FlexStatement accountId="U12345" fromDate="2024-01-01" toDate="2024-01-31">
                <Trades>
                    <Trade accountId="U12345" 
                           tradeID="123456789"
                           tradeDate="2024-01-15"
                           symbol="AAPL"
                           assetCategory="STK"
                           quantity="100"
                           tradePrice="150.25"
                           proceeds="-15025.00"
                           currency="USD"
                           ibCommission="-1.00"/>
                </Trades>
            </FlexStatement>
        </FlexStatements>
    </FlexQueryResponse>
    '''

def test_ibkr_parser_initialization():
    """Test IBKR parser initialization."""
    parser = IBKRFlexQueryParser()
    assert parser is not None
    assert parser.batch_manager is not None

def test_parse_trade_element(sample_ibkr_xml):
    """Test parsing individual trade element."""
    parser = IBKRFlexQueryParser()
    
    root = ET.fromstring(sample_ibkr_xml)
    trade_elem = root.find('.//Trade')
    
    transaction = parser._parse_trade_element(trade_elem)
    
    assert transaction is not None
    assert transaction.account_id == "U12345"
    assert transaction.trade_id == "123456789"
    assert transaction.symbol == "AAPL"
    assert transaction.asset_category == IBKRAssetCategory.STOCK
    assert transaction.quantity == Decimal('100')
    assert transaction.price == Decimal('150.25')
EOF

# Create sample IBKR XML data for testing
mkdir -p sample_data/interactive_brokers
cat > sample_data/interactive_brokers/sample_flex_query.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<FlexQueryResponse queryName="Security Master Test" type="AF">
    <FlexStatements count="1">
        <FlexStatement accountId="U12345" fromDate="2024-01-01" toDate="2024-01-31" 
                      whenGenerated="2024-02-01 09:30:00">
            <Trades>
                <Trade accountId="U12345" 
                       tradeID="123456789"
                       orderID="987654321"
                       tradeDate="2024-01-15"
                       settleDateTarget="2024-01-17"
                       symbol="AAPL"
                       description="APPLE INC"
                       assetCategory="STK"
                       quantity="100"
                       tradePrice="150.25"
                       proceeds="-15025.00"
                       currency="USD"
                       ibCommission="-1.00"
                       regulatoryFees="-0.02"
                       exchangeFees="-0.01"/>
                <Trade accountId="U12345" 
                       tradeID="123456790"
                       tradeDate="2024-01-16"
                       symbol="SPY"
                       description="SPDR S&P 500 ETF TRUST"
                       assetCategory="ETF"
                       quantity="50"
                       tradePrice="420.50"
                       proceeds="-21025.00"
                       currency="USD"
                       ibCommission="-1.00"/>
            </Trades>
        </FlexStatement>
    </FlexStatements>
</FlexQueryResponse>
EOF
```

## Validation Commands (1)

```bash
# Test IBKR parser import
python -c "
from security_master.extractor.interactive_brokers.parser import IBKRFlexQueryParser
from security_master.extractor.interactive_brokers.models import IBKRTransaction
print('IBKR parser imports successful')
"

# Test XML parsing
python -c "
import sys
sys.path.insert(0, 'src')
from pathlib import Path
from security_master.extractor.interactive_brokers.parser import IBKRFlexQueryParser
parser = IBKRFlexQueryParser()
result = parser.parse_file(Path('sample_data/interactive_brokers/sample_flex_query.xml'))
print(f'Parsed {len(result[\"transactions\"])} transactions')
"

# Run unit tests
poetry run pytest tests/unit/test_ibkr_parser.py -v
```

### Acceptance Criteria

- [ ] XML parser handling IBKR Flex Query format variations
- [ ] Complex derivatives support (options, futures, strikes, expiry dates)
- [ ] Multi-currency transaction handling
- [ ] IBKR-specific fee breakdown (commission, regulatory, exchange)
- [ ] Trade ID preservation for audit trails
- [ ] Performance optimization for large XML files
- [ ] Integration with batch processing system

---

### Issue P3-002: AltoIRA PDF Parser with OCR

**Branch**: `feature/altoira-pdf-parser`  
**Estimated Time**: 4 hours  
**Priority**: Medium  
**Week**: 11  

#### Description

Implement AltoIRA PDF statement parser with OCR capabilities and manual review workflow for low-confidence extractions.

#### Implementation Steps

#### Step 1: PDF Processing Dependencies Setup

```bash
# Install PDF and OCR dependencies
poetry add PyPDF2 pdfplumber pytesseract Pillow pdf2image

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils

# For macOS
# brew install tesseract poppler
```

## Step 2: AltoIRA PDF Parser Implementation

```bash
# Create AltoIRA extractor module
mkdir -p src/security_master/extractor/altoira
cat > src/security_master/extractor/altoira/__init__.py << 'EOF'
"""AltoIRA PDF statement parser."""
EOF

cat > src/security_master/extractor/altoira/models.py << 'EOF'
"""AltoIRA transaction and PDF extraction models."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum

class AltoIRATransactionType(Enum):
    """AltoIRA transaction types."""
    BUY = "Buy"
    SELL = "Sell"
    DIVIDEND = "Dividend"
    INTEREST = "Interest"
    FEE = "Fee"
    CONTRIBUTION = "Contribution"
    DISTRIBUTION = "Distribution"
    TRANSFER = "Transfer"

class OCRConfidenceLevel(Enum):
    """OCR confidence levels."""
    HIGH = "high"        # >90% confidence
    MEDIUM = "medium"    # 70-90% confidence
    LOW = "low"          # 50-70% confidence
    VERY_LOW = "very_low" # <50% confidence

class PDFExtractionResult(BaseModel):
    """Result of PDF text extraction."""
    page_number: int
    extraction_method: str = Field(..., description="'text' or 'ocr'")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    raw_text: str
    bounding_boxes: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    processing_time_ms: float
    errors: List[str] = Field(default_factory=list)

class AltoIRATransaction(BaseModel):
    """AltoIRA PDF-extracted transaction model."""
    
    # PDF extraction metadata
    source_pdf: str = Field(..., description="Source PDF filename")
    page_number: int = Field(..., description="Page number in PDF")
    extraction_confidence: OCRConfidenceLevel
    ocr_confidence_score: float = Field(..., ge=0.0, le=1.0)
    
    # Transaction details
    account_number: str
    transaction_type: AltoIRATransactionType
    transaction_date: date
    settlement_date: Optional[date] = None
    
    # Security identification
    symbol: Optional[str] = None
    security_description: Optional[str] = None
    cusip: Optional[str] = None
    
    # Transaction amounts
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    principal_amount: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    
    # Manual review flags
    requires_manual_review: bool = False
    manual_review_reason: Optional[str] = None
    manual_review_priority: int = Field(default=3, ge=1, le=5)  # 1=highest, 5=lowest
    
    # Data quality and audit
    data_quality_score: Optional[Decimal] = Field(None, ge=0, le=1)
    processing_notes: Optional[str] = None
    raw_extracted_text: Optional[str] = None
    
    @validator('data_quality_score', always=True)
    def calculate_quality_score(cls, v, values):
        """Calculate data quality score based on OCR confidence and field completeness."""
        if v is not None:
            return v
        
        # Base score from OCR confidence
        ocr_score = values.get('ocr_confidence_score', 0.0)
        score = ocr_score * 0.6  # OCR confidence weight
        
        # Field completeness score
        required_fields = ['account_number', 'transaction_type', 'transaction_date']
        important_fields = ['symbol', 'quantity', 'price', 'principal_amount']
        
        required_completeness = sum(1 for field in required_fields if values.get(field))
        important_completeness = sum(1 for field in important_fields if values.get(field))
        
        score += (required_completeness / len(required_fields)) * 0.3
        score += (important_completeness / len(important_fields)) * 0.1
        
        return min(Decimal(str(score)), Decimal('1.0'))
    
    @validator('requires_manual_review', always=True)
    def set_manual_review_flag(cls, v, values):
        """Automatically flag for manual review based on confidence."""
        if v:  # Already set to True
            return v
        
        # Flag for manual review if confidence is low
        confidence = values.get('ocr_confidence_score', 1.0)
        if confidence < 0.7:  # Below 70% confidence
            values['manual_review_reason'] = f"Low OCR confidence: {confidence:.1%}"
            return True
        
        # Flag if key fields are missing
        if not values.get('symbol') and values.get('transaction_type') in ['BUY', 'SELL']:
            values['manual_review_reason'] = "Buy/Sell transaction missing symbol"
            return True
        
        return False
EOF

cat > src/security_master/extractor/altoira/parser.py << 'EOF'
"""AltoIRA PDF statement parser with OCR capabilities."""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, InvalidOperation
from uuid import UUID

# PDF processing imports
import PyPDF2
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

from .models import (
    AltoIRATransaction, AltoIRATransactionType, 
    OCRConfidenceLevel, PDFExtractionResult
)
from ...batch.service import BatchManager
from ...batch.models import Institution, BatchStatus

logger = logging.getLogger(__name__)

class AltoIRAPDFParser:
    """AltoIRA PDF statement parser with OCR fallback."""
    
    def __init__(self, batch_manager: BatchManager = None):
        self.batch_manager = batch_manager or BatchManager()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Transaction detection patterns
        self.transaction_patterns = {
            'buy_sell': re.compile(r'(BUY|SELL)\s+(\d+(?:\.\d+)?)\s+(.+?)\s+\$([\d,]+\.\d{2})', re.IGNORECASE),
            'dividend': re.compile(r'DIVIDEND\s+(.+?)\s+\$([\d,]+\.\d{2})', re.IGNORECASE),
            'fee': re.compile(r'FEE\s+(.+?)\s+\$([\d,]+\.\d{2})', re.IGNORECASE),
            'date': re.compile(r'(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})'),
            'account': re.compile(r'Account\s*:?\s*([\w\d-]+)', re.IGNORECASE)
        }
    
    def parse_file(self, pdf_path: Path, created_by: str = "system") -> Dict[str, Any]:
        """Parse AltoIRA PDF statement."""
        
        # Create import batch
        batch = self.batch_manager.create_batch(
            institution=Institution.ALTOIRA,
            file_path=pdf_path,
            created_by=created_by
        )
        
        try:
            self.batch_manager.start_processing(batch.id)
            
            # Extract text from PDF using multiple methods
            extraction_results = self._extract_pdf_content(pdf_path)
            
            # Parse transactions from extracted text
            all_transactions = []
            
            for page_result in extraction_results:
                page_transactions = self._parse_page_transactions(
                    page_result, pdf_path.name
                )
                all_transactions.extend(page_transactions)
            
            # Validate and clean transactions
            valid_transactions = self._validate_transactions(all_transactions)
            
            # Separate manual review items
            auto_processed = [t for t in valid_transactions if not t.requires_manual_review]
            manual_review = [t for t in valid_transactions if t.requires_manual_review]
            
            # Calculate statistics
            statistics = {
                'total_records': len(all_transactions),
                'valid_records': len(valid_transactions),
                'invalid_records': len(all_transactions) - len(valid_transactions),
                'auto_processed': len(auto_processed),
                'manual_review_required': len(manual_review),
                'pages_processed': len(extraction_results)
            }
            
            # Calculate average quality score
            if valid_transactions:
                quality_scores = [float(t.data_quality_score) for t in valid_transactions]
                avg_quality_score = sum(quality_scores) / len(quality_scores)
            else:
                avg_quality_score = 0.0
            
            self.batch_manager.complete_batch(
                batch.id,
                statistics,
                data_quality_score=avg_quality_score
            )
            
            return {
                'batch_id': batch.id,
                'transactions': valid_transactions,
                'auto_processed': auto_processed,
                'manual_review': manual_review,
                'extraction_results': extraction_results,
                'statistics': statistics
            }
            
        except Exception as e:
            self.logger.error(f"AltoIRA PDF parsing failed for {pdf_path}: {e}")
            self.batch_manager.fail_batch(batch.id, str(e))
            raise
    
    def _extract_pdf_content(self, pdf_path: Path) -> List[PDFExtractionResult]:
        """Extract content from PDF using text extraction and OCR fallback."""
        results = []
        
        try:
            # Method 1: Try text extraction first (faster)
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    start_time = datetime.now()
                    
                    try:
                        text = page.extract_text()
                        processing_time = (datetime.now() - start_time).total_seconds() * 1000
                        
                        if text.strip():
                            # Estimate confidence based on text quality
                            confidence = self._estimate_text_confidence(text)
                            
                            result = PDFExtractionResult(
                                page_number=page_num,
                                extraction_method='text',
                                confidence_score=confidence,
                                raw_text=text,
                                processing_time_ms=processing_time
                            )
                            
                            # If text confidence is high enough, use it
                            if confidence >= 0.8:
                                results.append(result)
                                continue
                    
                    except Exception as e:
                        self.logger.warning(f"Text extraction failed for page {page_num}: {e}")
                    
                    # Method 2: OCR fallback for low confidence or failed text extraction
                    ocr_result = self._ocr_extract_page(pdf_path, page_num)
                    if ocr_result:
                        results.append(ocr_result)
            
        except Exception as e:
            self.logger.error(f"PDF extraction failed: {e}")
            # Try pdfplumber as final fallback
            try:
                results = self._pdfplumber_extract(pdf_path)
            except Exception as e2:
                self.logger.error(f"pdfplumber fallback failed: {e2}")
                raise
        
        return results
    
    def _ocr_extract_page(self, pdf_path: Path, page_num: int) -> Optional[PDFExtractionResult]:
        """Extract page content using OCR."""
        start_time = datetime.now()
        
        try:
            # Convert PDF page to image
            images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=300)
            
            if not images:
                return None
            
            image = images[0]
            
            # Perform OCR with confidence data
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(image)
            
            # Calculate confidence score
            confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            confidence_score = avg_confidence / 100.0  # Convert to 0-1 range
            
            # Extract bounding boxes for high-confidence text
            bounding_boxes = []
            for i, conf in enumerate(ocr_data['conf']):
                if int(conf) > 50:  # Only include reasonable confidence text
                    bounding_boxes.append({
                        'text': ocr_data['text'][i],
                        'confidence': int(conf),
                        'x': ocr_data['left'][i],
                        'y': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i]
                    })
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return PDFExtractionResult(
                page_number=page_num,
                extraction_method='ocr',
                confidence_score=confidence_score,
                raw_text=text,
                bounding_boxes=bounding_boxes,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed for page {page_num}: {e}")
            return PDFExtractionResult(
                page_number=page_num,
                extraction_method='ocr',
                confidence_score=0.0,
                raw_text='',
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                errors=[str(e)]
            )
    
    def _estimate_text_confidence(self, text: str) -> float:
        """Estimate confidence of extracted text based on content quality."""
        if not text.strip():
            return 0.0
        
        score = 0.7  # Base score for successful text extraction
        
        # Look for expected AltoIRA patterns
        if 'AltoIRA' in text or 'ALTO IRA' in text:
            score += 0.1
        
        # Check for transaction-like patterns
        if any(pattern.search(text) for pattern in self.transaction_patterns.values()):
            score += 0.1
        
        # Penalize if too much garbled text
        words = text.split()
        if words:
            garbled_ratio = sum(1 for word in words if len(word) > 20 or not word.isascii()) / len(words)
            score -= garbled_ratio * 0.2
        
        return max(0.0, min(1.0, score))
    
    def _pdfplumber_extract(self, pdf_path: Path) -> List[PDFExtractionResult]:
        """Fallback extraction using pdfplumber."""
        results = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                start_time = datetime.now()
                
                try:
                    text = page.extract_text() or ''
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    confidence = self._estimate_text_confidence(text)
                    
                    result = PDFExtractionResult(
                        page_number=page_num,
                        extraction_method='pdfplumber',
                        confidence_score=confidence,
                        raw_text=text,
                        processing_time_ms=processing_time
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    self.logger.warning(f"pdfplumber extraction failed for page {page_num}: {e}")
        
        return results
    
    def _parse_page_transactions(self, 
                               extraction_result: PDFExtractionResult, 
                               pdf_filename: str) -> List[AltoIRATransaction]:
        """Parse transactions from extracted page text."""
        transactions = []
        text = extraction_result.raw_text
        
        # Extract account number (usually at top of statement)
        account_match = self.transaction_patterns['account'].search(text)
        account_number = account_match.group(1) if account_match else 'UNKNOWN'
        
        # Find transaction patterns
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Try different transaction pattern matches
            transaction = None
            
            # Buy/Sell transactions
            buy_sell_match = self.transaction_patterns['buy_sell'].search(line)
            if buy_sell_match:
                transaction_type = AltoIRATransactionType.BUY if buy_sell_match.group(1).upper() == 'BUY' else AltoIRATransactionType.SELL
                quantity = Decimal(buy_sell_match.group(2))
                security_desc = buy_sell_match.group(3).strip()
                amount = Decimal(buy_sell_match.group(4).replace(',', ''))
                
                # Look for date in surrounding lines
                transaction_date = self._find_date_near_line(lines, line_num)
                
                transaction = AltoIRATransaction(
                    source_pdf=pdf_filename,
                    page_number=extraction_result.page_number,
                    extraction_confidence=self._get_confidence_level(extraction_result.confidence_score),
                    ocr_confidence_score=extraction_result.confidence_score,
                    account_number=account_number,
                    transaction_type=transaction_type,
                    transaction_date=transaction_date or datetime.now().date(),
                    security_description=security_desc,
                    quantity=quantity,
                    principal_amount=amount,
                    raw_extracted_text=line
                )
            
            # Dividend transactions
            elif 'dividend' in line.lower():
                dividend_match = self.transaction_patterns['dividend'].search(line)
                if dividend_match:
                    security_desc = dividend_match.group(1).strip()
                    amount = Decimal(dividend_match.group(2).replace(',', ''))
                    transaction_date = self._find_date_near_line(lines, line_num)
                    
                    transaction = AltoIRATransaction(
                        source_pdf=pdf_filename,
                        page_number=extraction_result.page_number,
                        extraction_confidence=self._get_confidence_level(extraction_result.confidence_score),
                        ocr_confidence_score=extraction_result.confidence_score,
                        account_number=account_number,
                        transaction_type=AltoIRATransactionType.DIVIDEND,
                        transaction_date=transaction_date or datetime.now().date(),
                        security_description=security_desc,
                        principal_amount=amount,
                        raw_extracted_text=line
                    )
            
            if transaction:
                transactions.append(transaction)
        
        return transactions
    
    def _find_date_near_line(self, lines: List[str], line_num: int) -> Optional[date]:
        """Find date in lines near the given line number."""
        # Search in current line and few lines above/below
        search_range = range(max(0, line_num - 2), min(len(lines), line_num + 3))
        
        for i in search_range:
            date_match = self.transaction_patterns['date'].search(lines[i])
            if date_match:
                date_str = date_match.group(1)
                try:
                    if '/' in date_str:
                        return datetime.strptime(date_str, '%m/%d/%Y').date()
                    else:
                        return datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    continue
        
        return None
    
    def _get_confidence_level(self, score: float) -> OCRConfidenceLevel:
        """Convert numeric confidence to level enum."""
        if score >= 0.9:
            return OCRConfidenceLevel.HIGH
        elif score >= 0.7:
            return OCRConfidenceLevel.MEDIUM
        elif score >= 0.5:
            return OCRConfidenceLevel.LOW
        else:
            return OCRConfidenceLevel.VERY_LOW
    
    def _validate_transactions(self, transactions: List[AltoIRATransaction]) -> List[AltoIRATransaction]:
        """Validate parsed transactions and set quality scores."""
        valid_transactions = []
        
        for transaction in transactions:
            validation_errors = []
            
            # Required field validation
            if not transaction.account_number or transaction.account_number == 'UNKNOWN':
                validation_errors.append("Missing or unknown account number")
            
            if not transaction.transaction_date:
                validation_errors.append("Missing transaction date")
            
            # Business rule validation
            if transaction.transaction_type in [AltoIRATransactionType.BUY, AltoIRATransactionType.SELL]:
                if not transaction.security_description:
                    validation_errors.append("Buy/Sell transaction missing security description")
                if not transaction.quantity:
                    validation_errors.append("Buy/Sell transaction missing quantity")
            
            if validation_errors:
                self.logger.warning(f"Transaction validation failed: {'; '.join(validation_errors)}")
                transaction.requires_manual_review = True
                transaction.manual_review_reason = '; '.join(validation_errors)
            
            valid_transactions.append(transaction)
        
        return valid_transactions
EOF
```

## Step 3: Manual Review Workflow Components

```bash
# Create manual review models
cat > src/security_master/workflow/manual_review.py << 'EOF'
"""Manual review workflow for low-confidence extractions."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum

class ReviewStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"

class ReviewItem(BaseModel):
    """Item requiring manual review."""
    id: str
    transaction_id: Optional[str] = None
    review_type: str  # "ocr_confidence", "validation_error", "discrepancy"
    priority: int  # 1=highest, 5=lowest
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    
    # Original data
    original_data: Dict[str, Any]
    confidence_score: float
    
    # Review context
    review_reason: str
    suggested_corrections: Optional[Dict[str, Any]] = None
    
    # Resolution
    resolution: Optional[Dict[str, Any]] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

class ManualReviewQueue:
    """Queue for managing manual review items."""
    
    def __init__(self):
        self.items: List[ReviewItem] = []
    
    def add_item(self, item: ReviewItem):
        """Add item to review queue."""
        self.items.append(item)
        # Sort by priority and creation date
        self.items.sort(key=lambda x: (x.priority, x.created_at))
    
    def get_pending_items(self, limit: int = 10) -> List[ReviewItem]:
        """Get pending review items."""
        return [item for item in self.items if item.status == ReviewStatus.PENDING][:limit]
    
    def get_item_by_id(self, item_id: str) -> Optional[ReviewItem]:
        """Get specific review item."""
        return next((item for item in self.items if item.id == item_id), None)
    
    def resolve_item(self, item_id: str, resolution: Dict[str, Any], resolved_by: str, notes: str = None):
        """Resolve a review item."""
        item = self.get_item_by_id(item_id)
        if item:
            item.status = ReviewStatus.COMPLETED
            item.resolution = resolution
            item.resolved_by = resolved_by
            item.resolved_at = datetime.now()
            item.resolution_notes = notes
EOF
```

## Validation Commands (2)

```bash
# Test AltoIRA parser import
python -c "
from security_master.extractor.altoira.parser import AltoIRAPDFParser
from security_master.extractor.altoira.models import AltoIRATransaction
print('AltoIRA parser imports successful')
"

# Create sample PDF for testing (would need actual AltoIRA PDF)
# mkdir -p sample_data/altoira
# echo "Sample AltoIRA statement would go here" > sample_data/altoira/sample_statement.pdf

# Test OCR dependencies
python -c "
import pytesseract
import PIL
from pdf2image import convert_from_path
print('OCR dependencies available')
"
```

### Acceptance Criteria

- [ ] PDF text extraction with OCR fallback
- [ ] Confidence scoring for extracted data
- [ ] Manual review workflow for low-confidence extractions
- [ ] Page-level transaction extraction with audit trail
- [ ] Support for multiple PDF statement formats
- [ ] Integration with validation framework

---

### Issue P3-003: Kubera API Integration

**Branch**: `feature/kubera-integration`  
**Estimated Time**: 3 hours  
**Priority**: Medium  
**Week**: 12  

#### Description

Integrate Kubera JSON API for real-time portfolio data validation and cross-institution reconciliation.

#### Acceptance Criteria

- [ ] Kubera JSON API client with authentication
- [ ] Sheet/section hierarchy preservation
- [ ] Real-time data sync for validation purposes
- [ ] Provider connection tracking (Finicity, Yodlee, manual)
- [ ] Cross-validation with other institution data
- [ ] Performance optimization for frequent updates

---

### Issue P3-004: Cross-Institution Data Validation Framework

**Branch**: `feature/cross-institution-validation`  
**Estimated Time**: 4 hours  
**Priority**: High  
**Week**: 12  

#### Description

Implement sophisticated cross-institution validation to identify discrepancies and improve data quality.

#### Acceptance Criteria

- [ ] Position reconciliation across institutions
- [ ] Discrepancy detection and reporting
- [ ] Data quality scoring improvements through cross-validation
- [ ] Automatic conflict resolution where possible
- [ ] Manual review workflow for unresolved discrepancies
- [ ] Comprehensive reporting and analytics

---

### Issue P3-005: Advanced Batch Processing Optimization

**Branch**: `feature/batch-processing-optimization`  
**Estimated Time**: 3 hours  
**Priority**: Medium  
**Week**: 13  

#### Description

Optimize batch processing for handling large datasets across multiple institutions efficiently.

#### Acceptance Criteria

- [ ] Parallel processing for multiple institution files
- [ ] Memory optimization for large datasets
- [ ] Progress tracking and status reporting
- [ ] Incremental processing for changed data only
- [ ] Error recovery and partial batch processing
- [ ] Performance monitoring and optimization

---

### Issue P3-006: Manual Review Workflow Implementation

**Branch**: `feature/manual-review-workflow`  
**Estimated Time**: 3 hours  
**Priority**: Medium  
**Week**: 13  

#### Description

Implement comprehensive manual review workflow for exceptions, low-confidence data, and discrepancies.

#### Acceptance Criteria

- [ ] Review queue management system
- [ ] Prioritization based on data quality scores
- [ ] User interface for review and correction
- [ ] Audit trail for all manual interventions
- [ ] Performance metrics for review efficiency
- [ ] Integration with classification system

---

### Issue P3-007: Data Lineage and Audit Enhancement

**Branch**: `feature/enhanced-data-lineage`  
**Estimated Time**: 3 hours  
**Priority**: Medium  
**Week**: 14  

#### Description

Enhance data lineage tracking to support complex multi-institution data flows and regulatory compliance.

#### Acceptance Criteria

- [ ] Complete data lineage from source to final classification
- [ ] Regulatory compliance reporting capabilities
- [ ] Change tracking and version control for all data modifications
- [ ] Performance optimization for lineage queries
- [ ] Export capabilities for audit purposes

---

### Issue P3-008: Phase 3 Integration Testing and Validation

**Branch**: `feature/phase3-integration`  
**Estimated Time**: 4 hours  
**Priority**: High  
**Week**: 14  

#### Description

Comprehensive testing of all Phase 3 functionality with realistic multi-institution datasets.

#### Acceptance Criteria

- [ ] End-to-end testing with all four institutions
- [ ] Performance testing with 50,000+ transaction datasets
- [ ] Data quality validation across institution boundaries
- [ ] Error handling and recovery testing
- [ ] Load testing for concurrent institution processing
- [ ] Documentation updates and Phase 4 preparation

---

## Phase 3 Success Criteria

### Technical Validation

- [ ] All institution parsers handle their respective data formats with >99% accuracy
- [ ] Cross-institution validation identifies known discrepancies in test datasets  
- [ ] System processes 50,000+ transactions across all institutions within 15 minutes
- [ ] Manual review workflow shows >80% efficiency improvement over manual processes
- [ ] Data quality scores improve by measurable percentage over Phase 2 baseline

### Performance Benchmarks

- [ ] IBKR XML processing: 10,000+ transactions per minute
- [ ] PDF processing: 100+ pages per minute with >95% OCR confidence
- [ ] Kubera API sync: <30 seconds for complete portfolio refresh
- [ ] Cross-validation: 10,000+ position comparisons within 2 minutes
- [ ] Batch processing: All institutions processed concurrently without resource conflicts

### Business Validation

- [ ] Complete institutional data coverage with minimal manual intervention
- [ ] Data discrepancy detection enables portfolio accuracy validation
- [ ] System scalability demonstrated for production transaction volumes
- [ ] Foundation established for advanced analytics and Portfolio Performance integration

---

**Phase 3 Target Completion**: End of Week 14  
**Next Phase**: Phase 4 - Analytics & Portfolio Performance Integration  
**Key Milestone**: Multi-institution data pipeline fully operational with quality validation
