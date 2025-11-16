"""
Security Master CLI - Command-line interface for Portfolio Performance Security Master.

Entry point for all security master operations:
- Import/export Portfolio Performance XML backups
- Import institution transaction files (Wells Fargo, IBKR, AltoIRA)
- Manage security classifications
- Run database migrations
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Initialize Rich console for beautiful output
console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="pp-security-master")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Portfolio Performance Security Master CLI.

    Centralized asset classification and taxonomy management for Portfolio Performance.
    """
    # Load environment variables from .env
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        console.print(
            "[yellow]⚠️  No .env file found. Database operations may fail.[/yellow]"
        )
        console.print(
            "[yellow]   Run 'pp-master init' to create a default .env file.[/yellow]\n"
        )

    # Store context for subcommands
    ctx.ensure_object(dict)


# ============================================================================
# Portfolio Performance XML Commands
# ============================================================================


@cli.command("import-xml")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--dry-run",
    is_flag=True,
    help="Parse XML without writing to database (validation only)",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed progress information"
)
def import_xml(file_path: str, dry_run: bool, verbose: bool) -> None:
    """Import Portfolio Performance XML backup into database.

    FILE_PATH: Path to the PP XML backup file to import

    Examples:
        pp-master import-xml sample_data/BruceandSueWilliams_sample.xml
        pp-master import-xml backup.xml --dry-run --verbose
    """
    from security_master.extractor.pp_xml_parser import PPXMLImporter

    console.print(f"\n[bold blue]Importing PP XML backup:[/bold blue] {file_path}\n")

    if dry_run:
        console.print("[yellow]Running in DRY-RUN mode (no database writes)[/yellow]\n")

    try:
        importer = PPXMLImporter(verbose=verbose)
        result = importer.import_file(file_path, dry_run=dry_run)

        # Display import summary
        table = Table(title="Import Summary", show_header=True, header_style="bold cyan")
        table.add_column("Category", style="dim", width=30)
        table.add_column("Count", justify="right")

        table.add_row("Accounts", str(result.get("accounts", 0)))
        table.add_row("Portfolios", str(result.get("portfolios", 0)))
        table.add_row("Securities", str(result.get("securities", 0)))
        table.add_row("Account Transactions", str(result.get("account_transactions", 0)))
        table.add_row(
            "Portfolio Transactions", str(result.get("portfolio_transactions", 0))
        )

        console.print(table)
        console.print("\n[bold green]✓ Import completed successfully[/bold green]\n")

    except FileNotFoundError:
        console.print(f"[bold red]✗ Error:[/bold red] File not found: {file_path}\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ Import failed:[/bold red] {e}\n")
        if verbose:
            import traceback

            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


@cli.command("export-xml")
@click.argument("output_path", type=click.Path(dir_okay=False))
@click.option(
    "--config-name",
    default="default",
    help="PP configuration name to export (default: 'default')",
)
@click.option("--pretty", is_flag=True, help="Format XML with indentation")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed progress information"
)
def export_xml(
    output_path: str, config_name: str, pretty: bool, verbose: bool
) -> None:
    """Export database to Portfolio Performance XML backup.

    OUTPUT_PATH: Path where the PP XML backup file should be saved

    Examples:
        pp-master export-xml backup.xml
        pp-master export-xml backup.xml --pretty --verbose
    """
    console.print(
        f"\n[bold blue]Exporting PP XML backup:[/bold blue] {output_path}\n"
    )

    try:
        from security_master.patch.pp_xml_export import PPXMLExportService
        from security_master.storage.database import get_session

        with get_session() as session:
            exporter = PPXMLExportService(session)
            xml_content = exporter.generate_complete_backup(config_name=config_name)

            # Write to file
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)

            if pretty:
                from defusedxml import minidom

                dom = minidom.parseString(xml_content)
                xml_content = dom.toprettyxml(indent="  ")

            output.write_text(xml_content, encoding="utf-8")

        console.print("[bold green]✓ Export completed successfully[/bold green]\n")

    except Exception as e:
        console.print(f"[bold red]✗ Export failed:[/bold red] {e}\n")
        if verbose:
            import traceback

            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


# ============================================================================
# Institution Data Import Commands
# ============================================================================


@cli.command("import-wells-csv")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--account-mapping",
    help="JSON file mapping Wells Fargo accounts to PP groups/accounts",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed progress information"
)
def import_wells_csv(
    file_path: str, account_mapping: Optional[str], verbose: bool
) -> None:
    """Import Wells Fargo CSV transaction file.

    FILE_PATH: Path to the Wells Fargo CSV export file

    Examples:
        pp-master import-wells-csv transactions.csv
        pp-master import-wells-csv transactions.csv --account-mapping mapping.json
    """
    console.print(f"\n[bold blue]Importing Wells Fargo CSV:[/bold blue] {file_path}\n")
    console.print(
        "[yellow]⚠️  Wells Fargo CSV parser not yet implemented[/yellow]\n"
    )
    sys.exit(1)


@cli.command("import-ibkr-csv")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed progress information"
)
def import_ibkr_csv(file_path: str, verbose: bool) -> None:
    """Import Interactive Brokers CSV transaction file.

    FILE_PATH: Path to the IBKR CSV export file

    Examples:
        pp-master import-ibkr-csv flex_query.csv
    """
    console.print(f"\n[bold blue]Importing IBKR CSV:[/bold blue] {file_path}\n")
    console.print("[yellow]⚠️  IBKR CSV parser not yet implemented[/yellow]\n")
    sys.exit(1)


# ============================================================================
# Database Management Commands
# ============================================================================


@cli.command("db-init")
@click.option(
    "--force", is_flag=True, help="Drop existing tables before creating new ones"
)
def db_init(force: bool) -> None:
    """Initialize database schema (run Alembic migrations).

    This creates all tables defined in the database models.

    Examples:
        pp-master db-init
        pp-master db-init --force
    """
    console.print("\n[bold blue]Initializing database schema...[/bold blue]\n")

    try:
        if force:
            console.print("[yellow]⚠️  Force mode: Dropping existing tables[/yellow]\n")
            # TODO: Implement drop tables

        # Run Alembic upgrade
        import subprocess

        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            console.print("[bold green]✓ Database initialized successfully[/bold green]\n")
            console.print(result.stdout)
        else:
            console.print(f"[bold red]✗ Database initialization failed[/bold red]\n")
            console.print(result.stderr)
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}\n")
        sys.exit(1)


@cli.command("db-status")
def db_status() -> None:
    """Show database connection status and current migration version.

    Examples:
        pp-master db-status
    """
    console.print("\n[bold blue]Database Status[/bold blue]\n")

    try:
        from security_master.storage.database import test_connection

        # Test connection
        db_info = test_connection()

        table = Table(title="Connection Info", show_header=True)
        table.add_column("Property", style="dim")
        table.add_column("Value")

        table.add_row("Host", db_info.get("host", "N/A"))
        table.add_row("Port", str(db_info.get("port", "N/A")))
        table.add_row("Database", db_info.get("database", "N/A"))
        table.add_row("User", db_info.get("user", "N/A"))
        table.add_row("Version", db_info.get("version", "N/A"))

        console.print(table)
        console.print("\n[bold green]✓ Database connection successful[/bold green]\n")

    except Exception as e:
        console.print(f"[bold red]✗ Connection failed:[/bold red] {e}\n")
        sys.exit(1)


@cli.command("init")
def init_project() -> None:
    """Initialize project configuration (create .env file).

    Examples:
        pp-master init
    """
    console.print("\n[bold blue]Initializing project configuration...[/bold blue]\n")

    env_path = Path(".env")
    if env_path.exists():
        console.print("[yellow]⚠️  .env file already exists. Skipping.[/yellow]\n")
        return

    # Copy .env.example to .env
    example_path = Path(".env.example")
    if example_path.exists():
        import shutil

        shutil.copy(example_path, env_path)
        console.print("[green]✓ Created .env from .env.example[/green]")
        console.print(
            "\n[yellow]⚠️  Edit .env with your PostgreSQL connection details:[/yellow]"
        )
        console.print("   - POSTGRES_HOST")
        console.print("   - POSTGRES_PORT")
        console.print("   - POSTGRES_USER")
        console.print("   - POSTGRES_PASSWORD")
        console.print("   - POSTGRES_DB\n")
    else:
        console.print("[red]✗ .env.example not found[/red]\n")
        sys.exit(1)


# ============================================================================
# Main Entry Point
# ============================================================================


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]\n")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]✗ Unexpected error:[/bold red] {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
