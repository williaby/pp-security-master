"""
Portfolio Performance XML export service for complete backup generation.
Generates valid PP XML backup files that can restore a complete PP instance.
"""

from datetime import UTC, datetime
from pathlib import Path

from defusedxml import ElementTree
from defusedxml import ElementTree as safe_ET
from defusedxml import minidom as safe_minidom
from sqlalchemy.orm import Session

from security_master.storage.models import SecurityMaster
from security_master.storage.pp_models import (
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

    def __init__(self, session: Session) -> None:
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
        root = ElementTree.Element("client")

        # Add client metadata
        ElementTree.SubElement(root, "version").text = str(config.version)
        ElementTree.SubElement(root, "baseCurrency").text = config.base_currency

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

    def _add_securities_section(self, parent: ElementTree.Element) -> None:
        """Add securities section with complete price history."""
        securities_elem = ElementTree.SubElement(parent, "securities")

        # Get all securities with their prices
        securities = self.session.query(SecurityMaster).all()

        for security in securities:
            security_elem = ElementTree.SubElement(securities_elem, "security")

            # Security identification
            ElementTree.SubElement(security_elem, "uuid").text = str(
                security.id,
            )  # Use database ID as UUID for now
            ElementTree.SubElement(security_elem, "name").text = security.name
            ElementTree.SubElement(security_elem, "currencyCode").text = (
                security.currency or "USD"
            )

            if security.note:
                ElementTree.SubElement(security_elem, "note").text = security.note
            if security.isin:
                ElementTree.SubElement(security_elem, "isin").text = security.isin
            if security.symbol:
                ElementTree.SubElement(
                    security_elem, "tickerSymbol"
                ).text = security.symbol
            if security.wkn:
                ElementTree.SubElement(security_elem, "wkn").text = security.wkn

            # Quote feed configuration
            ElementTree.SubElement(
                security_elem, "feed"
            ).text = "PP"  # Default to PP feed

            # Add price history
            self._add_price_history(security_elem, security.id)

    def _add_price_history(
        self,
        security_elem: ElementTree.Element,
        security_id: int,
    ) -> None:
        """Add complete price history for a security."""
        prices = (
            self.session.query(PPSecurityPrice)
            .filter_by(security_id=security_id)
            .order_by(PPSecurityPrice.price_date)
            .all()
        )

        if prices:
            prices_elem = ElementTree.SubElement(security_elem, "prices")

            for price in prices:
                price_elem = ElementTree.SubElement(prices_elem, "price")
                price_elem.set("t", price.price_date.strftime("%Y-%m-%d"))
                price_elem.set("v", str(price.price_value))

    def _add_watchlists_section(self, parent: ElementTree.Element) -> None:
        """Add watchlists section (typically empty)."""
        ElementTree.SubElement(parent, "watchlists")

    def _add_accounts_section(self, parent: ElementTree.Element) -> None:
        """Add accounts section with all transactions."""
        accounts_elem = ElementTree.SubElement(parent, "accounts")

        accounts = self.session.query(PPAccount).filter_by(is_retired=False).all()

        for account in accounts:
            account_elem = ElementTree.SubElement(accounts_elem, "account")

            # Account identification
            ElementTree.SubElement(account_elem, "uuid").text = str(account.uuid)
            ElementTree.SubElement(account_elem, "name").text = account.name
            ElementTree.SubElement(
                account_elem, "currencyCode"
            ).text = account.currency_code
            ElementTree.SubElement(account_elem, "isRetired").text = str(
                account.is_retired,
            ).lower()

            # Add account transactions
            self._add_account_transactions(account_elem, account.id)

            # Add account attributes
            if account.attributes:
                attributes_elem = ElementTree.SubElement(account_elem, "attributes")
                ElementTree.SubElement(attributes_elem, "map")  # Empty map for now

            # Add updatedAt timestamp
            ElementTree.SubElement(account_elem, "updatedAt").text = (
                datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
            )

    def _add_account_transactions(
        self,
        account_elem: ElementTree.Element,
        account_id: int,
    ) -> None:
        """Add all transactions for an account."""
        transactions = (
            self.session.query(PPAccountTransaction)
            .filter_by(account_id=account_id)
            .order_by(PPAccountTransaction.transaction_date)
            .all()
        )

        if transactions:
            transactions_elem = ElementTree.SubElement(account_elem, "transactions")

            for transaction in transactions:
                trans_elem = ElementTree.SubElement(
                    transactions_elem,
                    "account-transaction",
                )

                # Transaction core data
                ElementTree.SubElement(trans_elem, "uuid").text = str(transaction.uuid)
                ElementTree.SubElement(
                    trans_elem, "date"
                ).text = transaction.transaction_date.strftime("%Y-%m-%dT00:00")
                ElementTree.SubElement(
                    trans_elem, "currencyCode"
                ).text = transaction.currency_code
                ElementTree.SubElement(trans_elem, "amount").text = str(
                    int(transaction.amount * 100),
                )  # PP uses cents

                # Security reference if present
                if transaction.security_id:
                    security_ref = ElementTree.SubElement(trans_elem, "security")
                    security_ref.set(
                        "reference",
                        f"../../../../../securities/security[{transaction.security_id}]",
                    )

                # Shares (usually 0 for account transactions)
                ElementTree.SubElement(trans_elem, "shares").text = str(
                    int(transaction.shares * 100000000),
                )  # PP format

                # Transaction type
                ElementTree.SubElement(
                    trans_elem, "type"
                ).text = transaction.transaction_type

                # Add transaction units (fees, taxes)
                self._add_transaction_units(trans_elem, transaction.id, "ACCOUNT")

                # Cross-entry for linked portfolio transactions
                if transaction.cross_entry_type:
                    cross_entry = ElementTree.SubElement(trans_elem, "crossEntry")
                    cross_entry.set("class", transaction.cross_entry_type)
                    # Portfolio reference would be added here for linked transactions

    def _add_transaction_units(
        self,
        transaction_elem: ElementTree.Element,
        transaction_id: int,
        transaction_type: str,
    ) -> None:
        """Add fee and tax units for a transaction."""
        units = (
            self.session.query(PPTransactionUnit)
            .filter_by(transaction_id=transaction_id, transaction_type=transaction_type)
            .all()
        )

        for unit in units:
            unit_elem = ElementTree.SubElement(transaction_elem, "unit")
            unit_elem.set("type", unit.unit_type)

            amount_elem = ElementTree.SubElement(unit_elem, "amount")
            amount_elem.set("currency", unit.currency_code)
            amount_elem.text = str(int(unit.amount * 100))  # PP uses cents

    def _add_portfolios_section(self, parent: ElementTree.Element) -> None:
        """Add portfolios section with all portfolio transactions."""
        portfolios_elem = ElementTree.SubElement(parent, "portfolios")

        portfolios = self.session.query(PPPortfolio).filter_by(is_retired=False).all()

        for portfolio in portfolios:
            portfolio_elem = ElementTree.SubElement(portfolios_elem, "portfolio")

            # Portfolio identification
            ElementTree.SubElement(portfolio_elem, "uuid").text = str(portfolio.uuid)
            ElementTree.SubElement(portfolio_elem, "name").text = portfolio.name
            ElementTree.SubElement(portfolio_elem, "isRetired").text = str(
                portfolio.is_retired,
            ).lower()

            # Reference account
            if portfolio.reference_account:
                ref_account_elem = ElementTree.SubElement(
                    portfolio_elem,
                    "referenceAccount",
                )
                ElementTree.SubElement(ref_account_elem, "uuid").text = str(
                    portfolio.reference_account.uuid,
                )
                ElementTree.SubElement(
                    ref_account_elem, "name"
                ).text = portfolio.reference_account.name
                ElementTree.SubElement(
                    ref_account_elem, "currencyCode"
                ).text = portfolio.reference_account.currency_code
                ElementTree.SubElement(ref_account_elem, "isRetired").text = str(
                    portfolio.reference_account.is_retired,
                ).lower()

                # Empty transactions for reference account
                ElementTree.SubElement(ref_account_elem, "transactions")

                # Empty attributes
                attributes_elem = ElementTree.SubElement(ref_account_elem, "attributes")
                ElementTree.SubElement(attributes_elem, "map")

                # Updated timestamp
                ElementTree.SubElement(ref_account_elem, "updatedAt").text = (
                    datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
                )

            # Add portfolio transactions
            self._add_portfolio_transactions(portfolio_elem, portfolio.id)

    def _add_portfolio_transactions(
        self,
        portfolio_elem: ElementTree.Element,
        portfolio_id: int,
    ) -> None:
        """Add all transactions for a portfolio."""
        transactions = (
            self.session.query(PPPortfolioTransaction)
            .filter_by(portfolio_id=portfolio_id)
            .order_by(PPPortfolioTransaction.transaction_date)
            .all()
        )

        if transactions:
            transactions_elem = ElementTree.SubElement(portfolio_elem, "transactions")

            for transaction in transactions:
                trans_elem = ElementTree.SubElement(
                    transactions_elem,
                    "portfolio-transaction",
                )

                # Transaction core data
                ElementTree.SubElement(trans_elem, "uuid").text = str(transaction.uuid)
                ElementTree.SubElement(
                    trans_elem, "date"
                ).text = transaction.transaction_date.strftime("%Y-%m-%dT00:00")
                ElementTree.SubElement(
                    trans_elem, "currencyCode"
                ).text = transaction.currency_code
                ElementTree.SubElement(trans_elem, "amount").text = str(
                    int(transaction.amount * 100),
                )  # PP uses cents

                # Security reference (required for portfolio transactions)
                security_ref = ElementTree.SubElement(trans_elem, "security")
                security_ref.set(
                    "reference",
                    f"../../../../../../../../../securities/security[{transaction.security_id}]",
                )

                # Shares (required for portfolio transactions)
                ElementTree.SubElement(trans_elem, "shares").text = str(
                    int(transaction.shares * 100000000),
                )  # PP format

                # Transaction type
                ElementTree.SubElement(
                    trans_elem, "type"
                ).text = transaction.transaction_type

                # Add transaction units (fees, taxes)
                self._add_transaction_units(trans_elem, transaction.id, "PORTFOLIO")

                # Cross-entry for linked account transaction
                if transaction.linked_account_transaction:
                    cross_entry = ElementTree.SubElement(trans_elem, "crossEntry")
                    cross_entry.set("class", "buysell")  # Most common type

                    # Portfolio reference
                    portfolio_ref = ElementTree.SubElement(cross_entry, "portfolio")
                    portfolio_ref.set("reference", "../../../..")

                    # Portfolio transaction reference
                    portfolio_trans_ref = ElementTree.SubElement(
                        cross_entry,
                        "portfolioTransaction",
                    )
                    portfolio_trans_ref.set("reference", "../..")

                    # Account reference
                    account_ref = ElementTree.SubElement(cross_entry, "account")
                    account_ref.set("reference", "../../../../../../../..")

                    # Account transaction details
                    account_trans = ElementTree.SubElement(
                        cross_entry,
                        "accountTransaction",
                    )
                    linked_trans = transaction.linked_account_transaction

                    ElementTree.SubElement(account_trans, "uuid").text = str(
                        linked_trans.uuid,
                    )
                    ElementTree.SubElement(
                        account_trans, "date"
                    ).text = linked_trans.transaction_date.strftime("%Y-%m-%dT00:00")
                    ElementTree.SubElement(
                        account_trans, "currencyCode"
                    ).text = linked_trans.currency_code
                    ElementTree.SubElement(account_trans, "amount").text = str(
                        int(linked_trans.amount * 100),
                    )

                    if linked_trans.security_id:
                        security_ref = ElementTree.SubElement(account_trans, "security")
                        security_ref.set(
                            "reference",
                            f"../../../../../../../../../../../securities/security[{linked_trans.security_id}]",
                        )

                    # Cross-entry reference back
                    cross_ref = ElementTree.SubElement(account_trans, "crossEntry")
                    cross_ref.set("class", "buysell")
                    cross_ref.set("reference", "../..")

                    ElementTree.SubElement(account_trans, "shares").text = str(
                        int(linked_trans.shares * 100000000),
                    )
                    ElementTree.SubElement(
                        account_trans, "type"
                    ).text = linked_trans.transaction_type

    def _add_dashboards_section(self, parent: ElementTree.Element) -> None:
        """Add dashboards section (typically empty)."""
        ElementTree.SubElement(parent, "dashboards")

    def _add_properties_section(self, parent: ElementTree.Element) -> None:
        """Add properties section from settings."""
        properties_elem = ElementTree.SubElement(parent, "properties")

        # Get properties from settings
        properties = (
            self.session.query(PPSetting).filter_by(setting_category="properties").all()
        )

        for prop in properties:
            entry_elem = ElementTree.SubElement(properties_elem, "entry")
            ElementTree.SubElement(entry_elem, "string").text = prop.setting_key
            ElementTree.SubElement(entry_elem, "string").text = prop.setting_value

    def _add_settings_section(self, parent: ElementTree.Element) -> None:
        """Add settings section with bookmarks."""
        settings_elem = ElementTree.SubElement(parent, "settings")

        # Add bookmarks
        bookmarks_elem = ElementTree.SubElement(settings_elem, "bookmarks")
        bookmarks = self.session.query(PPBookmark).order_by(PPBookmark.sort_order).all()

        for bookmark in bookmarks:
            bookmark_elem = ElementTree.SubElement(bookmarks_elem, "bookmark")
            ElementTree.SubElement(bookmark_elem, "label").text = bookmark.label
            ElementTree.SubElement(bookmark_elem, "pattern").text = bookmark.pattern

    def _prettify_xml(self, elem: ElementTree.Element) -> str:
        """Return a pretty-printed XML string for the Element."""
        rough_string = ElementTree.tostring(elem, "unicode")
        reparsed = safe_minidom.parseString(rough_string)
        return str(reparsed.toprettyxml(indent="  "))

    def export_to_file(self, file_path: str, config_name: str = "default") -> None:
        """Export complete PP XML backup to file."""
        xml_content = self.generate_complete_backup(config_name)

        with Path(file_path).open("w", encoding="utf-8") as f:
            f.write(xml_content)

    def validate_export(self, xml_content: str) -> dict[str, int]:
        """Validate exported XML and return statistics."""
        try:
            # Use defusedxml for safe parsing
            root = safe_ET.fromstring(xml_content)

            return {
                "securities": len(root.findall(".//security")),
                "accounts": len(root.findall(".//accounts/account")),
                "portfolios": len(root.findall(".//portfolios/portfolio")),
                "account_transactions": len(root.findall(".//account-transaction")),
                "portfolio_transactions": len(root.findall(".//portfolio-transaction")),
                "prices": len(root.findall(".//price")),
                "bookmarks": len(root.findall(".//bookmark")),
            }

        except ElementTree.ParseError as e:
            raise ValueError(f"Invalid XML generated: {e}") from e


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
