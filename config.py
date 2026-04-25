import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback-secret")
    DATABASE = "aiproxy.db"