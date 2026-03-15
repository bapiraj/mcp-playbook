import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "job-platform.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init():
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print("Database and Tables created")


if __name__ == "__main__":
    init()
