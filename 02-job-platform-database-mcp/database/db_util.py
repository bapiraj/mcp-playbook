import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "job-platform.db"


def get_connection():
    """Return a SQLite connection to job-platform.db.
    Results come back as dict-like objects thanks to row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql, params=()):
    """Execute a SELECT query and return all results as a list of dicts."""
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def query_one(sql, params=()):
    """Execute a SELECT query and return a single result as a dict, or None."""
    with get_connection() as conn:
        row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def execute(sql, params=()):
    """Execute an INSERT, UPDATE, or DELETE query. Returns the lastrowid."""
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
    return cursor.lastrowid
