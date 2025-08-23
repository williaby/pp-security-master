"""
Portfolio Performance XML export service for complete backup generation.
Generates valid PP XML backup files that can restore a complete PP instance.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom

from sqlalchemy.orm import Session

from ..storage.models import SecurityMaster
from ..storage.pp_models import (
    PPAccount,
    PPAccountTransaction,
    PPBookmark,
    PPClientConfig,
    PPPortfolio,
    PPPortfolioTransaction,
    PPSecurityPrice,
    PPSetting,
    PPTransactionUnit,
)


class PPXMLExportService:
    """Generate complete Portfolio Performance XML backup from database."""

    def __init__(self, session: Session):
        self.session = session

    def generate_complete_backup(self, config_name: str = "default") -> str:
        """Generate complete PP XML backup file."""

        # Get client configuration
        config = (
            self.session.query(PPClientConfig)
            .filter_by(config_name=config_name, is_active=True)
            .first()
        )

        if not config:
            raise ValueError(f"No active PP configuration found for '{config_name}'")

        # Create root client element
        root = ET.Element("client")

        # Add client metadata
        ET.SubElement(root, "version").text = str(config.version)
        ET.SubElement(root, "baseCurrency").text = config.base_currency

        # Add main sections
        self._add_securities_section(root)
        self._add_watchlists_section(root)
        self._add_accounts_section(root)
        self._add_portfolios_section(root)
        self._add_dashboards_section(root)
        self._add_properties_section(root)
        self._add_settings_section(root)

        # Convert to pretty-printed XML string
        return self._prettify_xml(root)

    def _add_securities_section(self, parent: ET.Element) -> None:
        """Add securities section with complete price history."""
        securities_elem = ET.SubElement(parent, "securities")

        # Get all securities with their prices
        securities = self.session.query(SecurityMaster).all()

        for security in securities:
            security_elem = ET.SubElement(securities_elem, "security")

            # Security identification
            ET.SubElement(security_elem, "uuid").text = str(
                security.id,
            )  # Use database ID as UUID for now
            ET.SubElement(security_elem, "name").text = security.name
            ET.SubElement(security_elem, "currencyCode").text = (
                security.currency or "USD"
            )

            if security.note:
                ET.SubElement(security_elem, "note").text = security.note
            if security.isin:
                ET.SubElement(security_elem, "isin").text = security.isin
            if security.symbol:
                ET.SubElement(security_elem, "tickerSymbol").text = security.symbol
            if security.wkn:
                ET.SubElement(security_elem, "wkn").text = security.wkn

            # Quote feed configuration
            ET.SubElement(security_elem, "feed").text = "PP"  # Default to PP feed

            # Add price history
            self._add_price_history(security_elem, security.id)

    def _add_price_history(self, security_elem: ET.Element, security_id: int) -> None:
        """Add complete price history for a security."""
        prices = (
            self.session.query(PPSecurityPrice)
            .filter_by(security_id=security_id)
            .order_by(PPSecurityPrice.price_date)
            .all()
        )

        if prices:
            prices_elem = ET.SubElement(security_elem, "prices")

            for price in prices:
                price_elem = ET.SubElement(prices_elem, "price")
                price_elem.set("t", price.price_date.strftime("%Y-%m-%d"))
                price_elem.set("v", str(price.price_value))

    def _add_watchlists_section(self, parent: ET.Element) -> None:
        """Add watchlists section (typically empty)."""
        ET.SubElement(parent, "watchlists")

    def _add_accounts_section(self, parent: ET.Element) -> None:
        """Add accounts section with all transactions."""
        accounts_elem = ET.SubElement(parent, "accounts")

        accounts = self.session.query(PPAccount).filter_by(is_retired=False).all()

        for account in accounts:
            account_elem = ET.SubElement(accounts_elem, "account")

            # Account identification
            ET.SubElement(account_elem, "uuid").text = str(account.uuid)
            ET.SubElement(account_elem, "name").text = account.name
            ET.SubElement(account_elem, "currencyCode").text = account.currency_code
            ET.SubElement(account_elem, "isRetired").text = str(
                account.is_retired,
            ).lower()

            # Add account transactions
            self._add_account_transactions(account_elem, account.id)

            # Add account attributes
            if account.attributes:
                attributes_elem = ET.SubElement(account_elem, "attributes")
                ET.SubElement(attributes_elem, "map")  # Empty map for now

            # Add updatedAt timestamp
            ET.SubElement(account_elem, "updatedAt").text = (
                datetime.utcnow().isoformat() + "Z"
            )

    def _add_account_transactions(
        self, account_elem: ET.Element, account_id: int,
    ) -> None:
        """Add all transactions for an account."""
        transactions = (
            self.session.query(PPAccountTransaction)
            .filter_by(account_id=account_id)
            .order_by(PPAccountTransaction.transaction_date)
            .all()
        )

        if transactions:
            transactions_elem = ET.SubElement(account_elem, "transactions")

            for transaction in transactions:
                trans_elem = ET.SubElement(transactions_elem, "account-transaction")

                # Transaction core data
                ET.SubElement(trans_elem, "uuid").text = str(transaction.uuid)
                ET.SubElement(trans_elem, "date").text = (
                    transaction.transaction_date.strftime("%Y-%m-%dT00:00")
                )
                ET.SubElement(trans_elem, "currencyCode").text = (
                    transaction.currency_code
                )
                ET.SubElement(trans_elem, "amount").text = str(
                    int(transaction.amount * 100),
                )  # PP uses cents

                # Security reference if present
                if transaction.security_id:
                    security_ref = ET.SubElement(trans_elem, "security")
                    security_ref.set(
                        "reference",
                        f"../../../../../securities/security[{transaction.security_id}]",
                    )

                # Shares (usually 0 for account transactions)
                ET.SubElement(trans_elem, "shares").text = str(
                    int(transaction.shares * 100000000),
                )  # PP format

                # Transaction type
                ET.SubElement(trans_elem, "type").text = transaction.transaction_type

                # Add transaction units (fees, taxes)
                self._add_transaction_units(trans_elem, transaction.id, "ACCOUNT")

                # Cross-entry for linked portfolio transactions
                if transaction.cross_entry_type:
                    cross_entry = ET.SubElement(trans_elem, "crossEntry")
                    cross_entry.set("class", transaction.cross_entry_type)
                    # Portfolio reference would be added here for linked transactions

    def _add_transaction_units(
        self, transaction_elem: ET.Element, transaction_id: int, transaction_type: str,
    ) -> None:
        """Add fee and tax units for a transaction."""
        units = (
            self.session.query(PPTransactionUnit)
            .filter_by(transaction_id=transaction_id, transaction_type=transaction_type)
            .all()
        )

        for unit in units:
            unit_elem = ET.SubElement(transaction_elem, "unit")
            unit_elem.set("type", unit.unit_type)

            amount_elem = ET.SubElement(unit_elem, "amount")
            amount_elem.set("currency", unit.currency_code)
            amount_elem.text = str(int(unit.amount * 100))  # PP uses cents

    def _add_portfolios_section(self, parent: ET.Element) -> None:
        """Add portfolios section with all portfolio transactions."""
        portfolios_elem = ET.SubElement(parent, "portfolios")

        portfolios = self.session.query(PPPortfolio).filter_by(is_retired=False).all()

        for portfolio in portfolios:
            portfolio_elem = ET.SubElement(portfolios_elem, "portfolio")

            # Portfolio identification
            ET.SubElement(portfolio_elem, "uuid").text = str(portfolio.uuid)
            ET.SubElement(portfolio_elem, "name").text = portfolio.name
            ET.SubElement(portfolio_elem, "isRetired").text = str(
                portfolio.is_retired,
            ).lower()

            # Reference account
            if portfolio.reference_account:
                ref_account_elem = ET.SubElement(portfolio_elem, "referenceAccount")
                ET.SubElement(ref_account_elem, "uuid").text = str(
                    portfolio.reference_account.uuid,
                )
                ET.SubElement(ref_account_elem, "name").text = (
                    portfolio.reference_account.name
                )
                ET.SubElement(ref_account_elem, "currencyCode").text = (
                    portfolio.reference_account.currency_code
                )
                ET.SubElement(ref_account_elem, "isRetired").text = str(
                    portfolio.reference_account.is_retired,
                ).lower()

                # Empty transactions for reference account
                ET.SubElement(ref_account_elem, "transactions")

                # Empty attributes
                attributes_elem = ET.SubElement(ref_account_elem, "attributes")
                ET.SubElement(attributes_elem, "map")

                # Updated timestamp
                ET.SubElement(ref_account_elem, "updatedAt").text = (
                    datetime.utcnow().isoformat() + "Z"
                )

            # Add portfolio transactions
            self._add_portfolio_transactions(portfolio_elem, portfolio.id)

    def _add_portfolio_transactions(
        self, portfolio_elem: ET.Element, portfolio_id: int,
    ) -> None:
        """Add all transactions for a portfolio."""
        transactions = (
            self.session.query(PPPortfolioTransaction)
            .filter_by(portfolio_id=portfolio_id)
            .order_by(PPPortfolioTransaction.transaction_date)
            .all()
        )

        if transactions:
            transactions_elem = ET.SubElement(portfolio_elem, "transactions")

            for transaction in transactions:
                trans_elem = ET.SubElement(transactions_elem, "portfolio-transaction")

                # Transaction core data
                ET.SubElement(trans_elem, "uuid").text = str(transaction.uuid)
                ET.SubElement(trans_elem, "date").text = (
                    transaction.transaction_date.strftime("%Y-%m-%dT00:00")
                )
                ET.SubElement(trans_elem, "currencyCode").text = (
                    transaction.currency_code
                )
                ET.SubElement(trans_elem, "amount").text = str(
                    int(transaction.amount * 100),
                )  # PP uses cents

                # Security reference (required for portfolio transactions)
                security_ref = ET.SubElement(trans_elem, "security")
                security_ref.set(
                    "reference",
                    f"../../../../../../../../../securities/security[{transaction.security_id}]",
                )

                # Shares (required for portfolio transactions)
                ET.SubElement(trans_elem, "shares").text = str(
                    int(transaction.shares * 100000000),
                )  # PP format

                # Transaction type
                ET.SubElement(trans_elem, "type").text = transaction.transaction_type

                # Add transaction units (fees, taxes)
                self._add_transaction_units(trans_elem, transaction.id, "PORTFOLIO")

                # Cross-entry for linked account transaction
                if transaction.linked_account_transaction:
                    cross_entry = ET.SubElement(trans_elem, "crossEntry")
                    cross_entry.set("class", "buysell")  # Most common type

                    # Portfolio reference
                    portfolio_ref = ET.SubElement(cross_entry, "portfolio")
                    portfolio_ref.set("reference", "../../../..")

                    # Portfolio transaction reference
                    portfolio_trans_ref = ET.SubElement(
                        cross_entry, "portfolioTransaction",
                    )
                    portfolio_trans_ref.set("reference", "../..")

                    # Account reference
                    account_ref = ET.SubElement(cross_entry, "account")
                    account_ref.set("reference", "../../../../../../../..")

                    # Account transaction details
                    account_trans = ET.SubElement(cross_entry, "accountTransaction")
                    linked_trans = transaction.linked_account_transaction

                    ET.SubElement(account_trans, "uuid").text = str(linked_trans.uuid)
                    ET.SubElement(account_trans, "date").text = (
                        linked_trans.transaction_date.strftime("%Y-%m-%dT00:00")
                    )
                    ET.SubElement(account_trans, "currencyCode").text = (
                        linked_trans.currency_code
                    )
                    ET.SubElement(account_trans, "amount").text = str(
                        int(linked_trans.amount * 100),
                    )

                    if linked_trans.security_id:
                        security_ref = ET.SubElement(account_trans, "security")
                        security_ref.set(
                            "reference",
                            f"../../../../../../../../../../../securities/security[{linked_trans.security_id}]",
                        )

                    # Cross-entry reference back
                    cross_ref = ET.SubElement(account_trans, "crossEntry")
                    cross_ref.set("class", "buysell")
                    cross_ref.set("reference", "../..")

                    ET.SubElement(account_trans, "shares").text = str(
                        int(linked_trans.shares * 100000000),
                    )
                    ET.SubElement(account_trans, "type").text = (
                        linked_trans.transaction_type
                    )

    def _add_dashboards_section(self, parent: ET.Element) -> None:
        """Add dashboards section (typically empty)."""
        ET.SubElement(parent, "dashboards")

    def _add_properties_section(self, parent: ET.Element) -> None:
        """Add properties section from settings."""
        properties_elem = ET.SubElement(parent, "properties")

        # Get properties from settings
        properties = (
            self.session.query(PPSetting).filter_by(setting_category="properties").all()
        )

        for prop in properties:
            entry_elem = ET.SubElement(properties_elem, "entry")
            ET.SubElement(entry_elem, "string").text = prop.setting_key
            ET.SubElement(entry_elem, "string").text = prop.setting_value

    def _add_settings_section(self, parent: ET.Element) -> None:
        """Add settings section with bookmarks."""
        settings_elem = ET.SubElement(parent, "settings")

        # Add bookmarks
        bookmarks_elem = ET.SubElement(settings_elem, "bookmarks")
        bookmarks = self.session.query(PPBookmark).order_by(PPBookmark.sort_order).all()

        for bookmark in bookmarks:
            bookmark_elem = ET.SubElement(bookmarks_elem, "bookmark")
            ET.SubElement(bookmark_elem, "label").text = bookmark.label
            ET.SubElement(bookmark_elem, "pattern").text = bookmark.pattern

    def _prettify_xml(self, elem: ET.Element) -> str:
        """Return a pretty-printed XML string for the Element."""
        rough_string = ET.tostring(elem, "unicode")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def export_to_file(self, file_path: str, config_name: str = "default") -> None:
        """Export complete PP XML backup to file."""
        xml_content = self.generate_complete_backup(config_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_content)

    def validate_export(self, xml_content: str) -> dict[str, int]:
        """Validate exported XML and return statistics."""
        try:
            root = ET.fromstring(xml_content)

            stats = {
                "securities": len(root.findall(".//security")),
                "accounts": len(root.findall(".//accounts/account")),
                "portfolios": len(root.findall(".//portfolios/portfolio")),
                "account_transactions": len(root.findall(".//account-transaction")),
                "portfolio_transactions": len(root.findall(".//portfolio-transaction")),
                "prices": len(root.findall(".//price")),
                "bookmarks": len(root.findall(".//bookmark")),
            }

            return stats

        except ET.ParseError as e:
            raise ValueError(f"Invalid XML generated: {e}")


# Utility functions for PP data conversion
def pp_amount_to_decimal(pp_amount: int) -> float:
    """Convert PP integer amount (cents) to decimal."""
    return pp_amount / 100.0


def decimal_to_pp_amount(amount: float) -> int:
    """Convert decimal amount to PP integer (cents)."""
    return int(amount * 100)


def pp_shares_to_decimal(pp_shares: int) -> float:
    """Convert PP integer shares to decimal."""
    return pp_shares / 100000000.0


def decimal_to_pp_shares(shares: float) -> int:
    """Convert decimal shares to PP integer format."""
    return int(shares * 100000000)
