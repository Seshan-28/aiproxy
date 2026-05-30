# ⚡ AIProxy — AI Governance Dashboard

A production-ready AI governance platform for Google Gemini, built to monitor, control, and audit LLM usage across multiple users and departments.

---

## Features

- **Per-user policy enforcement** — Daily token, cost, and call limits with hard blocks.
- **Multi-turn conversation memory** — Context-aware chat sessions.
- **Multi-mode system prompt switcher** — HR Bot, Code Bot, Security Bot, General Assistant — each with a dedicated system prompt.
- **Real-time admin dashboard** — Visual analytics with Chart.js (Donut charts, usage trends).
- **Secure Authentication & RBAC** — Flask-Login based auth with distinct 'admin' and 'user' roles.
- **Alert system** — Automatic tracking of policy breaches.
- **Full Containerization** — Ready for production with Docker and Gunicorn.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, Flask, Gunicorn |
| **Database** | SQLite (persistent via Docker volumes) |
| **AI Client** | Google Gemini (via Google AI Studio API) |
| **Frontend** | Vanilla CSS, Bootstrap 5, Chart.js |
| **DevOps** | Docker, Docker Compose |

---

## Running with Docker (Recommended)

1. **Configure Environment**:
   Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
   Add your `GOOGLE_API_KEY` and `FLASK_SECRET_KEY` to `.env`.

2. **Start the application**:
   ```bash
   docker-compose up -d --build
   ```

3. **Access the dashboard**:
   Open `http://localhost:5000`

---

## Running Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**:
   ```bash
   python app.py
   ```

---

## Project Structure

```
.
├── app.py              # Main Flask application
├── auth.py             # User authentication and RBAC logic
├── config.py           # Configuration management
├── database.py         # Database schema and initialization
├── google_client.py    # Gemini API client
├── policy_engine.py    # Governance and limit enforcement
├── prompt_modes.py     # System prompt definitions
├── Dockerfile          # Container definition
├── docker-compose.yml  # Multi-container orchestration
└── data/               # Persistent database storage
```

---

## Author

Seshan
