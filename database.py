# database.py
import sqlite3
from config import Config

def get_db():
    conn = sqlite3.connect(
        Config.DATABASE,
        timeout=10,              # wait up to 10s if locked, instead of instant crash
        check_same_thread=False  # needed for Flask dev server
    )
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS api_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       TEXT NOT NULL,
            model         TEXT,
            user_message  TEXT,
            response      TEXT,
            input_tokens  INTEGER,
            output_tokens INTEGER,
            cost_usd      REAL,
            latency_ms    INTEGER,
            system_prompt TEXT,
            timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
            prompt        TEXT,
            tokens        INTEGER DEFAULT 0,
            cost          REAL DEFAULT 0,
            mode          TEXT DEFAULT 'general'
        );
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS policies (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        TEXT UNIQUE NOT NULL,
            max_tokens_day INTEGER DEFAULT 10000,
            max_cost_day   REAL DEFAULT 1.00,
            max_calls_day  INTEGER DEFAULT 50,
            is_active      INTEGER DEFAULT 1,
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            message    TEXT NOT NULL,
            value      REAL,
            limit_val  REAL,
            resolved   INTEGER DEFAULT 0,
            timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    print("[AIProxy] Database initialized.")