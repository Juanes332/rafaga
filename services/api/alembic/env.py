"""Alembic environment: the URL comes from the application settings."""

from alembic import context
from sqlalchemy import create_engine

from app.configs.config import get_settings


def run_migrations() -> None:
    """Apply pending migrations on a synchronous connection."""
    engine = create_engine(get_settings().database_url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations()
