import sqlite3

conn = sqlite3.connect("aiproxy.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE api_logs ADD COLUMN mode TEXT DEFAULT 'general'")
    conn.commit()
    print("✅ Column 'mode' added to api_logs")
except sqlite3.OperationalError as e:
    print(f"ℹ️  Already exists or error: {e}")
finally:
    conn.close()