"""Mock company data in SQLite (fake users + tickets). Run: python -m app.db"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "helpdesk.db"

USERS = [  # email, name, department, account_status, mfa_enabled
    ("anna.schmidt@example.com", "Anna Schmidt", "Sales", "active", 1),
    ("ben.mueller@example.com", "Ben Mueller", "Warehouse", "locked", 0),
    ("clara.weber@example.com", "Clara Weber", "Accounting", "active", 1),
    ("david.fischer@example.com", "David Fischer", "Sales", "disabled", 0),
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db() -> None:
    """Create tables and fill them with fake users (safe to run again)."""
    with connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, name TEXT, department TEXT,
                account_status TEXT, mfa_enabled INTEGER);
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT,
                summary TEXT, category TEXT, priority TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        conn.executemany("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", USERS)


if __name__ == "__main__":
    init_db()
    with connect() as conn:
        for row in conn.execute("SELECT email, account_status FROM users"):
            print(dict(row))
