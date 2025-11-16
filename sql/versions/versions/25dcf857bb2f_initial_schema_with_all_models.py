"""Initial schema with all models

Revision ID: 25dcf857bb2f
Revises:
Create Date: 2025-11-16 05:56:15.984049

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "25dcf857bb2f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create all tables."""

    # Create PP Client Config table
    op.create_table(
        "pp_client_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("config_name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create PP Accounts table
    op.create_table(
        "pp_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("is_retired", sa.Boolean(), nullable=False),
        sa.Column("attributes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )

    # Create PP Portfolios table
    op.create_table(
        "pp_portfolios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_retired", sa.Boolean(), nullable=False),
        sa.Column("reference_account_id", sa.Integer(), nullable=True),
        sa.Column("attributes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["reference_account_id"],
            ["pp_accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )

    # Create Securities Master table
    op.create_table(
        "securities_master",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("wkn", sa.String(length=20), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("latest_price", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("delta_percent", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("delta_amount", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("latest_date", sa.Date(), nullable=True),
        sa.Column("last_historical_date", sa.Date(), nullable=True),
        sa.Column("first_historical_date", sa.Date(), nullable=True),
        sa.Column("quote_feed_historic", sa.String(length=100), nullable=True),
        sa.Column("quote_feed_latest", sa.String(length=100), nullable=True),
        sa.Column("url_historic_quotes", sa.String(length=500), nullable=True),
        sa.Column("url_latest_quotes", sa.String(length=500), nullable=True),
        sa.Column("next_ex_date", sa.Date(), nullable=True),
        sa.Column("next_payment_date", sa.Date(), nullable=True),
        sa.Column("next_payment_amount", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("logo", sa.String(length=500), nullable=True),
        sa.Column("ter", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("aum", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("vendor", sa.String(length=100), nullable=True),
        sa.Column("acquisition_fee", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("management_fee", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("asset_classes_level1", sa.String(length=100), nullable=True),
        sa.Column("asset_classes", sa.String(length=200), nullable=True),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("industry_group", sa.String(length=100), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("industries_gics_level4", sa.String(length=200), nullable=True),
        sa.Column("industries_gics", sa.String(length=200), nullable=True),
        sa.Column("industries_gics_sectors_level1", sa.String(length=100), nullable=True),
        sa.Column("industries_gics_sectors", sa.String(length=200), nullable=True),
        sa.Column("asset_allocation_level1", sa.String(length=100), nullable=True),
        sa.Column("asset_allocation_level2", sa.String(length=100), nullable=True),
        sa.Column("asset_allocation", sa.String(length=200), nullable=True),
        sa.Column("market", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("regions_msci_level3", sa.String(length=100), nullable=True),
        sa.Column("regions_msci", sa.String(length=200), nullable=True),
        sa.Column("type_of_security_level1", sa.String(length=100), nullable=True),
        sa.Column("type_of_security", sa.String(length=200), nullable=True),
        sa.Column("brx_plus_level1", sa.String(length=100), nullable=True),
        sa.Column("brx_plus_level2", sa.String(length=100), nullable=True),
        sa.Column("brx_plus", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("data_source", sa.String(length=50), nullable=False),
        sa.Column("data_quality_score", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_securities_master_isin"), "securities_master", ["isin"], unique=True)
    op.create_index(op.f("ix_securities_master_name"), "securities_master", ["name"], unique=False)
    op.create_index(op.f("ix_securities_master_sector"), "securities_master", ["sector"], unique=False)
    op.create_index(op.f("ix_securities_master_symbol"), "securities_master", ["symbol"], unique=False)
    op.create_index(op.f("ix_securities_master_type_of_security_level1"), "securities_master", ["type_of_security_level1"], unique=False)
    op.create_index(op.f("ix_securities_master_wkn"), "securities_master", ["wkn"], unique=False)

    # Create Kubera tables
    op.create_table(
        "kubera_sheets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sheet_id", sa.String(length=50), nullable=False),
        sa.Column("sheet_name", sa.String(length=100), nullable=False),
        sa.Column("pp_group_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sheet_id"),
    )
    op.create_index(op.f("ix_kubera_sheets_pp_group_name"), "kubera_sheets", ["pp_group_name"], unique=False)
    op.create_index(op.f("ix_kubera_sheets_sheet_name"), "kubera_sheets", ["sheet_name"], unique=False)

    op.create_table(
        "kubera_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.String(length=50), nullable=False),
        sa.Column("section_name", sa.String(length=100), nullable=False),
        sa.Column("sheet_id", sa.Integer(), nullable=False),
        sa.Column("pp_account_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["sheet_id"],
            ["kubera_sheets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("section_id"),
    )
    op.create_index(op.f("ix_kubera_sections_pp_account_name"), "kubera_sections", ["pp_account_name"], unique=False)
    op.create_index(op.f("ix_kubera_sections_section_name"), "kubera_sections", ["section_name"], unique=False)

    op.create_table(
        "kubera_holdings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kubera_asset_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("security_master_id", sa.Integer(), nullable=True),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("market_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["kubera_sections.id"],
        ),
        sa.ForeignKeyConstraint(
            ["security_master_id"],
            ["securities_master.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kubera_asset_id"),
    )
    op.create_index(op.f("ix_kubera_holdings_isin"), "kubera_holdings", ["isin"], unique=False)
    op.create_index(op.f("ix_kubera_holdings_name"), "kubera_holdings", ["name"], unique=False)
    op.create_index(op.f("ix_kubera_holdings_symbol"), "kubera_holdings", ["symbol"], unique=False)

    # Create Holdings Comparison table
    op.create_table(
        "holdings_comparison",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pp_group_name", sa.String(length=100), nullable=False),
        sa.Column("pp_account_name", sa.String(length=100), nullable=False),
        sa.Column("security_master_id", sa.Integer(), nullable=False),
        sa.Column("kubera_holding_id", sa.Integer(), nullable=True),
        sa.Column("pp_quantity", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("kubera_quantity", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("quantity_variance", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("pp_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("kubera_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("value_variance", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["kubera_holding_id"],
            ["kubera_holdings.id"],
        ),
        sa.ForeignKeyConstraint(
            ["security_master_id"],
            ["securities_master.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_holdings_comparison_as_of_date"), "holdings_comparison", ["as_of_date"], unique=False)
    op.create_index(op.f("ix_holdings_comparison_pp_account_name"), "holdings_comparison", ["pp_account_name"], unique=False)
    op.create_index(op.f("ix_holdings_comparison_pp_group_name"), "holdings_comparison", ["pp_group_name"], unique=False)

    # Create Import Batch table
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.String(length=50), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=True),
        sa.Column("import_date", sa.DateTime(), nullable=False),
        sa.Column("transaction_count", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_id"),
    )
    op.create_index(op.f("ix_import_batches_import_date"), "import_batches", ["import_date"], unique=False)
    op.create_index(op.f("ix_import_batches_source_type"), "import_batches", ["source_type"], unique=False)
    op.create_index(op.f("ix_import_batches_status"), "import_batches", ["status"], unique=False)

    # Create Transaction tables
    op.create_table(
        "transactions_wells_fargo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("settlement_date", sa.Date(), nullable=True),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.Column("security_name", sa.String(length=255), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("cusip", sa.String(length=9), nullable=True),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("commission", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("fees", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("account_name", sa.String(length=100), nullable=False),
        sa.Column("account_number", sa.String(length=50), nullable=True),
        sa.Column("import_batch_id", sa.String(length=50), nullable=False),
        sa.Column("import_date", sa.DateTime(), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=True),
        sa.Column("source_line_number", sa.Integer(), nullable=True),
        sa.Column("is_processed", sa.Boolean(), nullable=False),
        sa.Column("has_errors", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("investment_objective", sa.String(length=100), nullable=True),
        sa.Column("account_type", sa.String(length=50), nullable=True),
        sa.Column("sub_account", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_wells_fargo_account_name"), "transactions_wells_fargo", ["account_name"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_account_number"), "transactions_wells_fargo", ["account_number"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_cusip"), "transactions_wells_fargo", ["cusip"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_has_errors"), "transactions_wells_fargo", ["has_errors"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_import_batch_id"), "transactions_wells_fargo", ["import_batch_id"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_is_processed"), "transactions_wells_fargo", ["is_processed"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_isin"), "transactions_wells_fargo", ["isin"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_settlement_date"), "transactions_wells_fargo", ["settlement_date"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_symbol"), "transactions_wells_fargo", ["symbol"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_transaction_date"), "transactions_wells_fargo", ["transaction_date"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_transaction_id"), "transactions_wells_fargo", ["transaction_id"], unique=False)
    op.create_index(op.f("ix_transactions_wells_fargo_transaction_type"), "transactions_wells_fargo", ["transaction_type"], unique=False)

    # Create Interactive Brokers transaction table (abbreviated version)
    op.create_table(
        "transactions_interactive_brokers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("settlement_date", sa.Date(), nullable=True),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.Column("security_name", sa.String(length=255), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("cusip", sa.String(length=9), nullable=True),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("commission", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("fees", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("account_name", sa.String(length=100), nullable=False),
        sa.Column("account_number", sa.String(length=50), nullable=True),
        sa.Column("import_batch_id", sa.String(length=50), nullable=False),
        sa.Column("import_date", sa.DateTime(), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=True),
        sa.Column("source_line_number", sa.Integer(), nullable=True),
        sa.Column("is_processed", sa.Boolean(), nullable=False),
        sa.Column("has_errors", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("asset_class", sa.String(length=50), nullable=True),
        sa.Column("underlying_symbol", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_interactive_brokers_account_name"), "transactions_interactive_brokers", ["account_name"], unique=False)
    op.create_index(op.f("ix_transactions_interactive_brokers_transaction_date"), "transactions_interactive_brokers", ["transaction_date"], unique=False)

    # Create AltoIRA transaction table (abbreviated)
    op.create_table(
        "transactions_altoira",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("settlement_date", sa.Date(), nullable=True),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.Column("security_name", sa.String(length=255), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("cusip", sa.String(length=9), nullable=True),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("commission", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("fees", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("account_name", sa.String(length=100), nullable=False),
        sa.Column("account_number", sa.String(length=50), nullable=True),
        sa.Column("import_batch_id", sa.String(length=50), nullable=False),
        sa.Column("import_date", sa.DateTime(), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=True),
        sa.Column("source_line_number", sa.Integer(), nullable=True),
        sa.Column("is_processed", sa.Boolean(), nullable=False),
        sa.Column("has_errors", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create Kubera transaction table (abbreviated)
    op.create_table(
        "transactions_kubera",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("settlement_date", sa.Date(), nullable=True),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.Column("security_name", sa.String(length=255), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("cusip", sa.String(length=9), nullable=True),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("commission", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("fees", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("account_name", sa.String(length=100), nullable=False),
        sa.Column("account_number", sa.String(length=50), nullable=True),
        sa.Column("import_batch_id", sa.String(length=50), nullable=False),
        sa.Column("import_date", sa.DateTime(), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=True),
        sa.Column("source_line_number", sa.Integer(), nullable=True),
        sa.Column("is_processed", sa.Boolean(), nullable=False),
        sa.Column("has_errors", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create Consolidated Transaction table (abbreviated)
    op.create_table(
        "consolidated_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("security_master_id", sa.Integer(), nullable=False),
        sa.Column("pp_group", sa.String(length=100), nullable=False),
        sa.Column("pp_account", sa.String(length=100), nullable=False),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("gross_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("net_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["security_master_id"],
            ["securities_master.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_consolidated_transactions_pp_account"), "consolidated_transactions", ["pp_account"], unique=False)
    op.create_index(op.f("ix_consolidated_transactions_pp_group"), "consolidated_transactions", ["pp_group"], unique=False)
    op.create_index(op.f("ix_consolidated_transactions_transaction_date"), "consolidated_transactions", ["transaction_date"], unique=False)

    # Create PP transaction tables
    op.create_table(
        "pp_account_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["pp_accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index(op.f("ix_pp_account_transactions_date"), "pp_account_transactions", ["date"], unique=False)

    op.create_table(
        "pp_portfolio_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("shares", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("security_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["portfolio_id"],
            ["pp_portfolios.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index(op.f("ix_pp_portfolio_transactions_date"), "pp_portfolio_transactions", ["date"], unique=False)

    # Create PP supporting tables
    op.create_table(
        "pp_securities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("wkn", sa.String(length=20), nullable=True),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("is_retired", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )

    op.create_table(
        "pp_security_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("security_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["security_id"],
            ["pp_securities.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pp_transaction_units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("account_transaction_id", sa.Integer(), nullable=True),
        sa.Column("portfolio_transaction_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_transaction_id"],
            ["pp_account_transactions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_transaction_id"],
            ["pp_portfolio_transactions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pp_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    op.create_table(
        "pp_bookmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("pattern", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema - drop all tables in reverse order."""

    # Drop PP tables first (due to foreign keys)
    op.drop_table("pp_bookmarks")
    op.drop_table("pp_settings")
    op.drop_table("pp_transaction_units")
    op.drop_table("pp_security_prices")
    op.drop_table("pp_securities")
    op.drop_index(op.f("ix_pp_portfolio_transactions_date"), table_name="pp_portfolio_transactions")
    op.drop_table("pp_portfolio_transactions")
    op.drop_index(op.f("ix_pp_account_transactions_date"), table_name="pp_account_transactions")
    op.drop_table("pp_account_transactions")

    # Drop consolidated and transaction tables
    op.drop_index(op.f("ix_consolidated_transactions_transaction_date"), table_name="consolidated_transactions")
    op.drop_index(op.f("ix_consolidated_transactions_pp_group"), table_name="consolidated_transactions")
    op.drop_index(op.f("ix_consolidated_transactions_pp_account"), table_name="consolidated_transactions")
    op.drop_table("consolidated_transactions")
    op.drop_table("transactions_kubera")
    op.drop_table("transactions_altoira")
    op.drop_index(op.f("ix_transactions_interactive_brokers_transaction_date"), table_name="transactions_interactive_brokers")
    op.drop_index(op.f("ix_transactions_interactive_brokers_account_name"), table_name="transactions_interactive_brokers")
    op.drop_table("transactions_interactive_brokers")
    op.drop_index(op.f("ix_transactions_wells_fargo_transaction_type"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_transaction_id"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_transaction_date"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_symbol"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_settlement_date"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_isin"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_is_processed"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_import_batch_id"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_has_errors"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_cusip"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_account_number"), table_name="transactions_wells_fargo")
    op.drop_index(op.f("ix_transactions_wells_fargo_account_name"), table_name="transactions_wells_fargo")
    op.drop_table("transactions_wells_fargo")

    # Drop import batches
    op.drop_index(op.f("ix_import_batches_status"), table_name="import_batches")
    op.drop_index(op.f("ix_import_batches_source_type"), table_name="import_batches")
    op.drop_index(op.f("ix_import_batches_import_date"), table_name="import_batches")
    op.drop_table("import_batches")

    # Drop holdings comparison
    op.drop_index(op.f("ix_holdings_comparison_pp_group_name"), table_name="holdings_comparison")
    op.drop_index(op.f("ix_holdings_comparison_pp_account_name"), table_name="holdings_comparison")
    op.drop_index(op.f("ix_holdings_comparison_as_of_date"), table_name="holdings_comparison")
    op.drop_table("holdings_comparison")

    # Drop Kubera tables
    op.drop_index(op.f("ix_kubera_holdings_symbol"), table_name="kubera_holdings")
    op.drop_index(op.f("ix_kubera_holdings_name"), table_name="kubera_holdings")
    op.drop_index(op.f("ix_kubera_holdings_isin"), table_name="kubera_holdings")
    op.drop_table("kubera_holdings")
    op.drop_index(op.f("ix_kubera_sections_section_name"), table_name="kubera_sections")
    op.drop_index(op.f("ix_kubera_sections_pp_account_name"), table_name="kubera_sections")
    op.drop_table("kubera_sections")
    op.drop_index(op.f("ix_kubera_sheets_sheet_name"), table_name="kubera_sheets")
    op.drop_index(op.f("ix_kubera_sheets_pp_group_name"), table_name="kubera_sheets")
    op.drop_table("kubera_sheets")

    # Drop securities master
    op.drop_index(op.f("ix_securities_master_wkn"), table_name="securities_master")
    op.drop_index(op.f("ix_securities_master_type_of_security_level1"), table_name="securities_master")
    op.drop_index(op.f("ix_securities_master_symbol"), table_name="securities_master")
    op.drop_index(op.f("ix_securities_master_sector"), table_name="securities_master")
    op.drop_index(op.f("ix_securities_master_name"), table_name="securities_master")
    op.drop_index(op.f("ix_securities_master_isin"), table_name="securities_master")
    op.drop_table("securities_master")

    # Drop PP base tables
    op.drop_table("pp_portfolios")
    op.drop_table("pp_accounts")
    op.drop_table("pp_client_config")
