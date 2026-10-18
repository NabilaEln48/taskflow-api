"""Alembic migration environment.

Two customizations vs. the generated default:

1. `target_metadata = Base.metadata` — Alembic compares this against the
   live database to AUTO-GENERATE migrations (`alembic revision
   --autogenerate`). Importing the models package is what registers the
   tables with Base; forget the import and autogenerate sees zero tables.
2. The DB URL comes from `app.config.settings` (env var DATABASE_URL),
   not from alembic.ini. One source of truth for connection config —
   alembic.ini's sqlalchemy.url is left blank on purpose.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.config import settings
from app.database import Base

# Import models so their tables register on Base.metadata.
# (Unused imports are intentional — flake8 would flag them; that's fine.)
import app.models.task  # noqa: F401
import app.models.user  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override whatever is in alembic.ini with the app's configured URL.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting ("--sql" mode)."""
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
