"""
Portfolio Performance XML backup parser.

Parses Portfolio Performance XML backup files and imports data into the security master database.
Handles accounts, portfolios, securities, and all transaction types.
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from defusedxml import ElementTree
from rich.console import Console
from rich.progress import track
from sqlalchemy.orm import Session

from security_master.storage.database import get_db_session
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

console = Console()


class PPXMLImporter:
    """Import Portfolio Performance XML backup files into the database."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the importer.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.stats: dict[str, int] = {
            "accounts": 0,
            "portfolios": 0,
            "securities": 0,
            "account_transactions": 0,
            "portfolio_transactions": 0,
            "security_prices": 0,
            "settings": 0,
            "bookmarks": 0,
        }

        # UUID mappings to preserve cross-references
        self.account_uuid_map: dict[str, int] = {}
        self.portfolio_uuid_map: dict[str, int] = {}
        self.security_uuid_map: dict[str, int] = {}

    def import_file(self, file_path: str, dry_run: bool = False) -> dict[str, Any]:
        """Import a Portfolio Performance XML backup file.

        Args:
            file_path: Path to the PP XML file
            dry_run: Parse without writing to database

        Returns:
            dict: Import statistics

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the XML is invalid
        """
        xml_path = Path(file_path)
        if not xml_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if self.verbose:
            console.print(f"\n[dim]Parsing XML file: {xml_path}[/dim]")

        # Parse XML safely using defusedxml
        try:
            tree = ElementTree.parse(xml_path)
            root = tree.getroot()
        except Exception as e:
            raise ValueError(f"Invalid XML file: {e}") from e

        if root.tag != "client":
            raise ValueError(
                f"Invalid PP XML: root element is '{root.tag}', expected 'client'"
            )

        if dry_run:
            console.print("\n[yellow]DRY RUN mode - no database changes[/yellow]")
            # Parse but don't write
            self._parse_xml_structure(root, dry_run=True)
            return self.stats

        # Import into database with transaction
        with get_db_session() as session:
            self._import_to_database(session, root)

        return self.stats

    def _import_to_database(self, session: Session, root: Any) -> None:
        """Import parsed XML data into database.

        Args:
            session: Database session
            root: XML root element
        """
        # Import in dependency order
        if self.verbose:
            console.print("\n[dim]Importing client configuration...[/dim]")
        self._import_client_config(session, root)

        if self.verbose:
            console.print("[dim]Importing accounts...[/dim]")
        self._import_accounts(session, root)

        if self.verbose:
            console.print("[dim]Importing portfolios...[/dim]")
        self._import_portfolios(session, root)

        if self.verbose:
            console.print("[dim]Importing securities...[/dim]")
        self._import_securities(session, root)

        if self.verbose:
            console.print("[dim]Importing account transactions...[/dim]")
        self._import_account_transactions(session, root)

        if self.verbose:
            console.print("[dim]Importing portfolio transactions...[/dim]")
        self._import_portfolio_transactions(session, root)

        if self.verbose:
            console.print("[dim]Importing security prices...[/dim]")
        self._import_security_prices(session, root)

        if self.verbose:
            console.print("[dim]Importing settings and bookmarks...[/dim]")
        self._import_settings(session, root)
        self._import_bookmarks(session, root)

        session.commit()

    def _parse_xml_structure(self, root: Any, dry_run: bool = False) -> None:
        """Parse XML structure (dry-run mode)."""
        # Count elements for dry-run
        self.stats["accounts"] = len(root.findall(".//accounts/account"))
        self.stats["portfolios"] = len(root.findall(".//portfolios/portfolio"))
        self.stats["securities"] = len(root.findall(".//securities/security"))
        self.stats["account_transactions"] = len(
            root.findall(".//account-transactions/account-transaction")
        )
        self.stats["portfolio_transactions"] = len(
            root.findall(".//portfolio-transactions/portfolio-transaction")
        )

    def _import_client_config(self, session: Session, root: Any) -> None:
        """Import client configuration."""
        version = int(root.get("version", 66))
        base_currency = root.get("baseCurrency", "USD")

        config = PPClientConfig(
            version=version,
            base_currency=base_currency,
            config_name="default",
            is_active=True,
        )
        session.add(config)
        session.flush()

    def _import_accounts(self, session: Session, root: Any) -> None:
        """Import PP accounts."""
        accounts_elem = root.find("accounts")
        if accounts_elem is None:
            return

        account_elems = accounts_elem.findall("account")
        for account_elem in track(
            account_elems, description="Importing accounts", disable=not self.verbose
        ):
            uuid_str = account_elem.get("uuid")
            if not uuid_str:
                continue

            account = PPAccount(
                uuid=UUID(uuid_str),
                name=account_elem.findtext("name", "Unnamed Account"),
                currency_code=account_elem.findtext("currencyCode", "USD"),
                is_retired=account_elem.findtext("isRetired", "false") == "true",
                attributes=account_elem.findtext("attributes"),
            )

            session.add(account)
            session.flush()

            # Store UUID mapping
            self.account_uuid_map[uuid_str] = account.id
            self.stats["accounts"] += 1

    def _import_portfolios(self, session: Session, root: Any) -> None:
        """Import PP portfolios."""
        portfolios_elem = root.find("portfolios")
        if portfolios_elem is None:
            return

        portfolio_elems = portfolios_elem.findall("portfolio")
        for portfolio_elem in track(
            portfolio_elems, description="Importing portfolios", disable=not self.verbose
        ):
            uuid_str = portfolio_elem.get("uuid")
            if not uuid_str:
                continue

            # Get reference account if present
            ref_account_uuid = portfolio_elem.findtext("referenceAccount")
            ref_account_id = None
            if ref_account_uuid:
                ref_account_id = self.account_uuid_map.get(ref_account_uuid)

            portfolio = PPPortfolio(
                uuid=UUID(uuid_str),
                name=portfolio_elem.findtext("name", "Unnamed Portfolio"),
                is_retired=portfolio_elem.findtext("isRetired", "false") == "true",
                reference_account_id=ref_account_id,
                attributes=portfolio_elem.findtext("attributes"),
            )

            session.add(portfolio)
            session.flush()

            # Store UUID mapping
            self.portfolio_uuid_map[uuid_str] = portfolio.id
            self.stats["portfolios"] += 1

    def _import_securities(self, session: Session, root: Any) -> None:
        """Import PP securities."""
        securities_elem = root.find("securities")
        if securities_elem is None:
            return

        # Note: This creates entries in pp_securities table
        # In a full implementation, we would also create/update securities_master entries
        security_elems = securities_elem.findall("security")
        for security_elem in track(
            security_elems, description="Importing securities", disable=not self.verbose
        ):
            uuid_str = security_elem.get("uuid")
            if not uuid_str:
                continue

            from security_master.storage.pp_models import PPSecurity

            security = PPSecurity(
                uuid=UUID(uuid_str),
                name=security_elem.findtext("name", "Unnamed Security"),
                isin=security_elem.findtext("isin"),
                symbol=security_elem.findtext("tickerSymbol"),
                wkn=security_elem.findtext("wkn"),
                currency_code=security_elem.findtext("currencyCode", "USD"),
                note=security_elem.findtext("note"),
                is_retired=security_elem.findtext("isRetired", "false") == "true",
            )

            session.add(security)
            session.flush()

            # Store UUID mapping
            self.security_uuid_map[uuid_str] = security.id
            self.stats["securities"] += 1

    def _import_account_transactions(self, session: Session, root: Any) -> None:
        """Import PP account transactions."""
        transactions_elem = root.find("account-transactions")
        if transactions_elem is None:
            return

        transaction_elems = transactions_elem.findall("account-transaction")
        for txn_elem in track(
            transaction_elems,
            description="Importing account transactions",
            disable=not self.verbose,
        ):
            uuid_str = txn_elem.get("uuid")
            if not uuid_str:
                continue

            # Get account reference
            account_uuid = txn_elem.findtext("account")
            if not account_uuid or account_uuid not in self.account_uuid_map:
                continue

            account_id = self.account_uuid_map[account_uuid]

            # Parse date
            date_str = txn_elem.findtext("date")
            txn_date = (
                datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
            )

            # Parse amount
            amount_str = txn_elem.findtext("amount")
            amount = Decimal(amount_str) if amount_str else Decimal(0)

            transaction = PPAccountTransaction(
                uuid=UUID(uuid_str),
                date=txn_date,
                type=txn_elem.findtext("type", "DEPOSIT"),
                amount=amount,
                currency_code=txn_elem.findtext("currencyCode", "USD"),
                note=txn_elem.findtext("note"),
                account_id=account_id,
            )

            session.add(transaction)
            self.stats["account_transactions"] += 1

    def _import_portfolio_transactions(self, session: Session, root: Any) -> None:
        """Import PP portfolio transactions."""
        transactions_elem = root.find("portfolio-transactions")
        if transactions_elem is None:
            return

        transaction_elems = transactions_elem.findall("portfolio-transaction")
        for txn_elem in track(
            transaction_elems,
            description="Importing portfolio transactions",
            disable=not self.verbose,
        ):
            uuid_str = txn_elem.get("uuid")
            if not uuid_str:
                continue

            # Get portfolio and security references
            portfolio_uuid = txn_elem.findtext("portfolio")
            security_uuid = txn_elem.findtext("security")

            if not portfolio_uuid or portfolio_uuid not in self.portfolio_uuid_map:
                continue
            if not security_uuid:
                continue

            portfolio_id = self.portfolio_uuid_map[portfolio_uuid]

            # Parse date
            date_str = txn_elem.findtext("date")
            txn_date = (
                datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
            )

            # Parse numeric values
            shares_str = txn_elem.findtext("shares")
            shares = Decimal(shares_str) if shares_str else Decimal(0)

            amount_str = txn_elem.findtext("amount")
            amount = Decimal(amount_str) if amount_str else Decimal(0)

            transaction = PPPortfolioTransaction(
                uuid=UUID(uuid_str),
                date=txn_date,
                type=txn_elem.findtext("type", "BUY"),
                shares=shares,
                amount=amount,
                currency_code=txn_elem.findtext("currencyCode", "USD"),
                note=txn_elem.findtext("note"),
                portfolio_id=portfolio_id,
                security_uuid=UUID(security_uuid),
            )

            session.add(transaction)
            self.stats["portfolio_transactions"] += 1

    def _import_security_prices(self, session: Session, root: Any) -> None:
        """Import security price history."""
        securities_elem = root.find("securities")
        if securities_elem is None:
            return

        for security_elem in securities_elem.findall("security"):
            uuid_str = security_elem.get("uuid")
            if not uuid_str or uuid_str not in self.security_uuid_map:
                continue

            security_id = self.security_uuid_map[uuid_str]

            # Import prices
            prices_elem = security_elem.find("prices")
            if prices_elem is not None:
                for price_elem in prices_elem.findall("price"):
                    date_str = price_elem.get("date")
                    value_str = price_elem.get("value")

                    if date_str and value_str:
                        price_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        price_value = Decimal(value_str) / Decimal(100000000)  # PP uses int scaled format

                        price = PPSecurityPrice(
                            security_id=security_id,
                            date=price_date,
                            value=price_value,
                        )
                        session.add(price)
                        self.stats["security_prices"] += 1

    def _import_settings(self, session: Session, root: Any) -> None:
        """Import PP settings."""
        settings_elem = root.find("settings")
        if settings_elem is None:
            return

        for setting_elem in settings_elem.findall("setting"):
            key = setting_elem.get("key")
            value = setting_elem.text

            if key:
                setting = PPSetting(key=key, value=value)
                session.add(setting)
                self.stats["settings"] += 1

    def _import_bookmarks(self, session: Session, root: Any) -> None:
        """Import PP bookmarks."""
        bookmarks_elem = root.find("bookmarks")
        if bookmarks_elem is None:
            return

        for bookmark_elem in bookmarks_elem.findall("bookmark"):
            label = bookmark_elem.findtext("label")
            pattern = bookmark_elem.findtext("pattern")

            if label and pattern:
                bookmark = PPBookmark(label=label, pattern=pattern)
                session.add(bookmark)
                self.stats["bookmarks"] += 1
