# ⚡ AIProxy — AI Governance Dashboard

A production-style API governance layer for Claude (Anthropic), built to monitor, control, and audit LLM usage across multiple users and departments.

> Built as a 12-day internship project at Authify Technologies, inspired by internal tooling requirements for enterprise AI deployment.

---

## What It Does

Most companies plugging LLMs into internal tools have no visibility into who is using the AI, how much it costs, or whether it's being misused. AIProxy sits between your application and the Claude API and solves that.

- **Per-user policy enforcement** — daily token, cost, and call limits with hard blocks and soft warnings at 80%
- **Multi-mode system prompt switcher** — HR Bot, Code Bot, Security Bot, General Assistant — each with a dedicated system prompt, selectable per request
- **Session threading** — conversations grouped by session ID, replayable in admin
- **Real-time admin dashboard** — cost/day charts, calls-per-user doughnut, token usage bar, live request log with mode filtering
- **Alert system** — policy breach events written to DB, resolvable from admin UI
- **CSV export** — full log export, filterable by user or bot mode
- **Swap-ready API client** — mock client for development, real Anthropic SDK for production; one import line to switch

---

## Architecture
Browser
│
▼
Flask App (app.py)
├── Policy Engine      → checks per-user limits before every call
├── Prompt Modes       → injects system prompt based on selected mode
├── Mock/Real Client   → calls Claude API (or simulates it)
└── SQLite DB          → logs every request, stores policies + alerts
Admin UI (/admin)        → charts, log table, conversation replay
Policy Editor (/admin/policies) → set per-user limits
Chat Console (/)         → test interface with mode switcher

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10, Flask |
| Database | SQLite (swap-ready for Postgres) |
| AI Client | Anthropic Claude SDK (mock mode default) |
| Frontend | Bootstrap 5, Chart.js |
| Auth (planned) | Per-user API key via Authify |

---

## Running Locally

```bash
git clone https://github.com/YOUR_USERNAME/aiproxy.git
cd aiproxy

pip install -r requirements.txt

# Copy env template and add your key (optional — mock mode works without it)
cp .env.example .env

python app.py
```

Open `http://localhost:5000`

To use real Claude API responses, add your key to `.env`:

ANTHROPIC_API_KEY=sk-ant-...
Then in `app.py` swap one line:
```python
from claude_client import call_claude      # real
# from mock_claude_client import call_claude  # mock
```

---

## Key Design Decisions

**Why a mock client?** The governance layer is the project — routing, logging, policy enforcement, alerting. These work identically with simulated or real responses. The mock lets the system run in CI or demos without burning API credits.

**Why SQLite?** Appropriate for a single-node internship project. The `get_db()` pattern and schema are designed to migrate to Postgres with minimal changes.

**Why Flask over FastAPI?** Simpler mental model for a 12-day build. The route patterns and DB access would translate directly to FastAPI with async if needed.

---

## Features Roadmap

- [ ] Real Anthropic API key integration + end-to-end test
- [ ] User authentication (JWT or session-based)
- [ ] Conversation memory (multi-turn context per session)
- [ ] Webhook alerts (Slack/email on policy breach)
- [ ] Docker + deployment to Render or Railway

---

## Author

Seshan 