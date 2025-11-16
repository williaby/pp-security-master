import os
import sys
import urllib.parse
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# Add the src directory to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))

# Import all models to ensure they are registered with Base
from security_master.storage.models import (  # noqa: E402, F401
    Base,
    HoldingComparison,
    KuberaHolding,
    KuberaSection,
    KuberaSheet,
    SecurityMaster,
)
from security_master.storage.pp_models import (  # noqa: E402, F401
    PPAccount,
    PPAccountTransaction,
    PPBookmark,
    PPClientConfig,
    PPPortfolio,
    PPPortfolioTransaction,
    PPSecurity,
    PPSecurityPrice,
    PPSetting,
    PPTransactionUnit,
)
from security_master.storage.transaction_models import (  # noqa: E402, F401
    AltoIRATransaction,
    ConsolidatedTransaction,
    ImportBatch,
    InteractiveBrokersTransaction,
    KuberaTransaction,
    WellsFargoTransaction,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load environment variables from .env file
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Configure database URL from environment variables
def get_database_url() -> str:
    """Get database URL from environment variables."""
    # Try DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Build from individual components
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_user = os.getenv("POSTGRES_USER", "pp_user")
    postgres_db = os.getenv("POSTGRES_DB", "pp_master")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")

    # URL-encode credentials to handle special characters
    user_enc = urllib.parse.quote_plus(postgres_user)
    pw_enc = urllib.parse.quote_plus(postgres_password)

    return f"postgresql://{user_enc}:{pw_enc}@{postgres_host}:{postgres_port}/{postgres_db}"


# Override sqlalchemy.url in config
config.set_main_option("sqlalchemy.url", get_database_url())

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"connect_timeout": 5},  # Add timeout to fail fast
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()
    except Exception as e:
        # If connection fails, provide helpful error message
        import sys

        print(
            f"\n❌ Database connection failed: {e}",
            file=sys.stderr,
        )
        print(
            "\n💡 To create migrations, ensure PostgreSQL is running and .env is configured:",
            file=sys.stderr,
        )
        print("   - POSTGRES_HOST=<your-server-ip>", file=sys.stderr)
        print("   - POSTGRES_PORT=5432", file=sys.stderr)
        print("   - POSTGRES_USER=<your-user>", file=sys.stderr)
        print("   - POSTGRES_PASSWORD=<your-password>", file=sys.stderr)
        print("   - POSTGRES_DB=pp_master", file=sys.stderr)
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
