import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback-secret")
    # In Docker, we store data in /data. Locally, use the current dir.
    # We check for writability to avoid permission errors on some systems.
    _db_path = "/data/aiproxy.db"
    if not os.path.exists("/data") or not os.access("/data", os.W_OK):
        _db_path = "aiproxy.db"
    
    DATABASE = _db_path