# license_server/db.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "licenses.db")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                key         TEXT PRIMARY KEY,
                hw_id       TEXT,
                active      INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL,
                activated_at TEXT,
                note        TEXT
            )
        """)
        c.commit()


def insert_key(key: str, note: str = ""):
    with _conn() as c:
        c.execute(
            "INSERT INTO licenses (key, active, created_at, note) VALUES (?,1,?,?)",
            (key, datetime.utcnow().isoformat(), note)
        )
        c.commit()


def get_key(key: str):
    with _conn() as c:
        row = c.execute("SELECT * FROM licenses WHERE key=?", (key,)).fetchone()
        return dict(row) if row else None


def activate_key(key: str, hw_id: str):
    with _conn() as c:
        c.execute(
            "UPDATE licenses SET hw_id=?, activated_at=? WHERE key=?",
            (hw_id, datetime.utcnow().isoformat(), key)
        )
        c.commit()


def revoke_key(key: str):
    with _conn() as c:
        c.execute("UPDATE licenses SET active=0 WHERE key=?", (key,))
        c.commit()


def list_keys():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM licenses ORDER BY created_at DESC").fetchall()]
