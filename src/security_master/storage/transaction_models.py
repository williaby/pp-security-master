from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .models import Base


class TransactionBase(Base):
    """Base class for all institution transaction tables."""
    __abstract__ = True
    
    # Common fields across all institutions
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Transaction identification
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    settlement_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Security identification
    security_name: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    isin: Mapped[Optional[str]] = mapped_column(String(12), index=True)
    cusip: Mapped[Optional[str]] = mapped_column(String(9), index=True)
    
    # Transaction details
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # BUY, SELL, DIV, etc.
    quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8))
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    # Fees and charges
    commission: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    fees: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Account mapping
    account_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    account_number: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    
    # Import metadata
    import_batch_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    import_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source_file: Mapped[Optional[str]] = mapped_column(String(255))
    source_line_number: Mapped[Optional[int]] = mapped_column()
    
    # Data quality flags
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    has_errors: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WellsFargoTransaction(TransactionBase):
    """Wells Fargo specific transaction imports from CSV files."""
    __tablename__ = "transactions_wells_fargo"
    
    # Wells Fargo specific fields
    investment_objective: Mapped[Optional[str]] = mapped_column(String(100))
    account_type: Mapped[Optional[str]] = mapped_column(String(50))  # IRA, TAXABLE, etc.
    sub_account: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Additional Wells Fargo fields from CSV
    description: Mapped[Optional[str]] = mapped_column(Text)
    investment_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    def __repr__(self) -> str:
        return f"<WellsFargoTransaction(id={self.id}, date={self.transaction_date}, type='{self.transaction_type}', security='{self.security_name}', amount={self.amount})>"


class InteractiveBrokersTransaction(TransactionBase):
    """Interactive Brokers Flex Query transaction imports."""
    __tablename__ = "transactions_interactive_brokers"
    
    # IBKR specific fields
    trade_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(50))
    execution_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    # IBKR market data
    exchange: Mapped[Optional[str]] = mapped_column(String(20))
    multiplier: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), default=1)
    asset_class: Mapped[Optional[str]] = mapped_column(String(20))  # STK, OPT, FUT, etc.
    sec_type: Mapped[Optional[str]] = mapped_column(String(20))  # Stock, Option, etc.
    
    # Options/Derivatives specific
    strike: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    expiry: Mapped[Optional[date]] = mapped_column(Date)
    put_call: Mapped[Optional[str]] = mapped_column(String(1))  # P, C
    underlying_symbol: Mapped[Optional[str]] = mapped_column(String(20))
    
    # IBKR fees breakdown
    ib_commission: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    regulatory_fees: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    exchange_fees: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    def __repr__(self) -> str:
        return f"<InteractiveBrokersTransaction(id={self.id}, trade_id='{self.trade_id}', date={self.transaction_date}, type='{self.transaction_type}', security='{self.security_name}')>"


class AltoIRATransaction(TransactionBase):
    """AltoIRA transaction imports from PDF statements."""
    __tablename__ = "transactions_altoira"
    
    # AltoIRA specific fields
    statement_date: Mapped[Optional[date]] = mapped_column(Date)
    page_number: Mapped[Optional[int]] = mapped_column()
    parsed_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))  # PDF parsing confidence 0.00-1.00
    
    # Manual review flags
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    manually_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100))
    review_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    review_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # PDF extraction metadata
    pdf_text_raw: Mapped[Optional[str]] = mapped_column(Text)
    ocr_engine: Mapped[Optional[str]] = mapped_column(String(50))  # tesseract, etc.
    
    def __repr__(self) -> str:
        return f"<AltoIRATransaction(id={self.id}, date={self.transaction_date}, type='{self.transaction_type}', confidence={self.parsed_confidence}, manual_review={self.requires_manual_review})>"


class KuberaTransaction(TransactionBase):
    """Kubera aggregated transaction data for comparison and validation."""
    __tablename__ = "transactions_kubera"
    
    # Kubera specific fields
    kubera_asset_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    kubera_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    
    # Kubera hierarchical data
    sheet_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # IRA, Crypto, etc.
    section_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # Wells Fargo, IBKR, etc.
    
    # Data connection info
    aggregator: Mapped[Optional[str]] = mapped_column(String(50))  # finicity, yodlee, manual
    provider_name: Mapped[Optional[str]] = mapped_column(String(100))
    provider_account_id: Mapped[Optional[str]] = mapped_column(String(50))
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Validation flags
    is_validation_source: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    matched_to_institution: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    variance_flag: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    def __repr__(self) -> str:
        return f"<KuberaTransaction(id={self.id}, asset_id='{self.kubera_asset_id}', sheet='{self.sheet_name}', section='{self.section_name}')>"


class ConsolidatedTransaction(Base):
    """Consolidated view of all transactions normalized for Portfolio Performance export."""
    __tablename__ = "transactions_consolidated"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Source tracking
    source_institution: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # wells_fargo, ibkr, altoira
    source_transaction_id: Mapped[int] = mapped_column(nullable=False)
    source_table: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Normalized transaction data
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    settlement_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Security reference (linked to securities_master)
    security_master_id: Mapped[Optional[int]] = mapped_column(ForeignKey("securities_master.id"))
    security_name: Mapped[str] = mapped_column(String(255), nullable=False)
    isin: Mapped[Optional[str]] = mapped_column(String(12), index=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    
    # Portfolio Performance mapping
    pp_group: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    pp_account: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Standardized transaction data
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8))
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    fees_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    net_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    # Data quality
    quality_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=1.00)  # 0.00-1.00
    has_validation_issues: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    validation_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Processing status
    exported_to_pp: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    export_batch_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    export_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ConsolidatedTransaction(id={self.id}, source='{self.source_institution}', date={self.transaction_date}, pp_account='{self.pp_account}', amount={self.net_amount})>"


class ImportBatch(Base):
    """Tracks data import batches for audit and rollback capabilities."""
    __tablename__ = "import_batches"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Import metadata
    institution: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    import_type: Mapped[str] = mapped_column(String(50), nullable=False)  # csv, xml, pdf, api
    source_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column()
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA-256
    
    # Processing statistics
    records_imported: Mapped[int] = mapped_column(default=0)
    records_processed: Mapped[int] = mapped_column(default=0)
    records_errors: Mapped[int] = mapped_column(default=0)
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Import configuration
    import_config: Mapped[Optional[str]] = mapped_column(Text)  # JSON config used for import
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ImportBatch(id='{self.batch_id}', institution='{self.institution}', status='{self.status}', records={self.records_imported})>"