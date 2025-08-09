"""Alembic migration environment setup."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from config import Settings

# Alembic Config object, provides access to .ini values.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No models' metadata is available; migrations use imperative syntax.
target_metadata = None


def get_url() -> str:
    """Return the database URL from environment settings."""

    settings = Settings()
    if settings.database_url:
        return settings.database_url
    db_path = settings.data_dir / "workspace.db"
    return f"sqlite:///{db_path}"


def run_migrations_offline() -> None:
    """Run migrations without a SQL connection."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        {"url": get_url()}, prefix="", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
