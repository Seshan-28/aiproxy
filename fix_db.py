# run once: python fix_db.py
from database import get_db

conn = get_db()
conn.execute("DROP TABLE IF EXISTS policies")
conn.execute("DROP TABLE IF EXISTS alerts")
conn.execute("""
    CREATE TABLE policies (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        TEXT UNIQUE NOT NULL,
        max_tokens_day INTEGER DEFAULT 10000,
        max_cost_day   REAL DEFAULT 1.00,
        max_calls_day  INTEGER DEFAULT 50,
        is_active      INTEGER DEFAULT 1,
        created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.execute("""
    CREATE TABLE alerts (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    TEXT NOT NULL,
        alert_type TEXT NOT NULL,
        message    TEXT NOT NULL,
        value      REAL,
        limit_val  REAL,
        resolved   INTEGER DEFAULT 0,
        timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()
conn.close()
print("Done — policies and alerts tables recreated.")