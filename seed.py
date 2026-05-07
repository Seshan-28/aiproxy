# seed.py
from database import get_db, init_db
from werkzeug.security import generate_password_hash

def seed_users():
    conn = get_db()
    # Drop and recreate users table to ensure schema is updated
    conn.execute("DROP TABLE IF EXISTS users;")
    conn.commit()
    conn.close()
    
    init_db()
    
    # User list: name + 123 password logic
    user_ids = ["seshan", "testuser", "john", "user_001", "user_002", "users"]
    users_data = [{"user_id": "admin", "password": "admin123", "role": "admin"}]
    
    for uid in user_ids:
        users_data.append({"user_id": uid, "password": uid + "123", "role": "user"})
    
    conn = get_db()
    for u in users_data:
        pwd_hash = generate_password_hash(u["password"])
        conn.execute("""
            INSERT INTO users (user_id, password_hash, role)
            VALUES (?, ?, ?)
        """, (u["user_id"], pwd_hash, u["role"]))
    conn.commit()
    conn.close()
    print(f"Seeded {len(users_data)} users.")

if __name__ == "__main__":
    seed_users()