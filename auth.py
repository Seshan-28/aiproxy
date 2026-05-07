# auth.py
from flask_login import UserMixin
from functools import wraps
from flask import abort, render_template
from flask_login import current_user
from database import get_db

class User(UserMixin):
    def __init__(self, id, user_id, role):
        self.id = id
        self.user_id = user_id
        self.role = role

def get_user_by_id(user_db_id):
    db = get_db()
    row = db.execute("SELECT id, user_id, role FROM users WHERE id = ?", (user_db_id,)).fetchone()
    db.close()
    if row:
        return User(id=row["id"], user_id=row["user_id"], role=row["role"])
    return None

def get_user_by_username(username):
    db = get_db()
    row = db.execute("SELECT id, user_id, role, password_hash FROM users WHERE user_id = ?", (username,)).fetchone()
    db.close()
    return row

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            # Instead of just abort(403), we can render a custom page or return JSON if it's an API
            # For this dashboard, 403 Forbidden is requested.
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
