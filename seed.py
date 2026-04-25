# run this once: python seed.py
from database import get_db, init_db
import random, datetime

init_db()

users = ["seshan", "admin", "analyst", "testuser"]
messages = [
    "Explain zero-day vulnerabilities",
    "What is SIEM?",
    "Summarize OWASP Top 10",
    "How does PKI work?",
    "What is threat modeling?"
]
responses = [
    "Mock response about security concepts.",
    "AIProxy governance layer processed this request.",
    "This is a simulated AI response for testing.",
]

conn = get_db()
for i in range(40):
    days_ago = random.randint(0, 6)
    ts = datetime.datetime.now() - datetime.timedelta(days=days_ago, hours=random.randint(0,23))
    conn.execute("""
        INSERT INTO api_logs 
        (user_id, model, user_message, response, input_tokens, output_tokens, cost_usd, latency_ms, system_prompt, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        random.choice(users),
        "claude-sonnet-4-mock",
        random.choice(messages),
        random.choice(responses),
        random.randint(50, 400),
        random.randint(80, 500),
        round(random.uniform(0.0001, 0.005), 6),
        random.randint(150, 900),
        "You are a helpful assistant.",
        ts.strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (random.choice(users),))

conn.commit()
conn.close()
print("Seeded 40 records across 4 users and 7 days.")