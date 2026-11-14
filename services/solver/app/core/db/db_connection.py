"""Open psycopg connections to the shared Postgres database."""

import psycopg
from psycopg.rows import dict_row


def connect(database_url: str, autocommit: bool = False) -> psycopg.Connection:
    """Return a dict-row connection with a short connect timeout."""
    return psycopg.connect(
        database_url, autocommit=autocommit, row_factory=dict_row, connect_timeout=3
    )


def ping(database_url: str) -> bool:
    """Return True when the database answers a trivial query."""
    if not database_url:
        return False
    try:
        with connect(database_url, autocommit=True) as conn:
            conn.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False
