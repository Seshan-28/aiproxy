# app.py
from flask import Flask, request, jsonify, render_template, Response, redirect, url_for, flash, abort
from config import Config
from google_client import call_google
from database import init_db, get_db
from prompt_modes import get_system_prompt, all_modes
from policy_engine import check_policy, fire_alert, get_today_usage, get_policy
from auth import User, get_user_by_id, get_user_by_username, admin_required
import csv, io, time
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_db_id):
    return get_user_by_id(user_db_id)

with app.app_context():
    init_db()

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/admin")
@admin_required
def admin():
    return render_template("admin.html")

@app.route("/admin/policies")
@admin_required
def policies_page():
    return render_template("policies.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        login_type = request.form.get("login_type") # 'user' or 'admin'

        user_row = get_user_by_username(username)
        if user_row and check_password_hash(user_row["password_hash"], password):
            if user_row["role"] != login_type:
                flash(f"Access Denied: You are not registered as {login_type}.", "danger")
            else:
                user_obj = User(id=user_row["id"], user_id=user_row["user_id"], role=user_row["role"])
                login_user(user_obj)
                return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "danger")
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

def fetch_session_history(session_id, limit=5):
    if not session_id:
        return ""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT prompt, response FROM api_logs
            WHERE session_id = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (session_id, limit)).fetchall()
        
        # Reverse to get chronological order
        rows.reverse()
        
        history_str = ""
        for r in rows:
            history_str += f"User: {r['prompt']}\nAI: {r['response']}\n"
        return history_str
    finally:
        db.close()

# ── Chat ──────────────────────────────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()
    user_id    = current_user.user_id
    message    = data.get("message", "")
    mode       = data.get("mode", "general")
    session_id = data.get("session_id", "")

    if not message:
        return jsonify({"error": "message is required"}), 400

    allowed, reason, _, _ = check_policy(user_id)
    if not allowed:
        # HARD BLOCK: Must refuse to call AI if limit reached
        return jsonify({"error": "Policy Breach: Your daily limit is reached. Contact your Admin.", "blocked": True}), 429

    system_prompt = get_system_prompt(mode)
    history = fetch_session_history(session_id)
    
    combined_prompt = message
    if history:
        combined_prompt = f"Context of previous conversation:\n{history}\n\nCurrent Prompt: {message}"

    start    = time.time()
    response = call_google(combined_prompt, system_prompt=system_prompt)
    latency  = round((time.time() - start) * 1000, 2)

    tokens = response.get("tokens", 0)
    cost   = response.get("cost", 0.0)
    reply  = response.get("reply", "")

    db = get_db()
    try:
        db.execute(
            """INSERT INTO api_logs
               (user_id, prompt, response, tokens, cost, latency_ms, mode, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, message, reply, tokens, cost, latency, mode, session_id)
        )
        db.commit()
    finally:
        db.close()

    return jsonify({
        "reply": reply, "tokens": tokens,
        "cost": cost, "latency_ms": latency,
        "mode": mode, "session_id": session_id
    })

# ── Modes ─────────────────────────────────────────────────────────────────────
@app.route("/api/modes")
@login_required
def api_modes():
    return jsonify(all_modes())

# ── Logs ──────────────────────────────────────────────────────────────────────
@app.route("/api/logs")
@login_required
def get_logs():
    db = get_db()
    try:
        if current_user.role == 'admin':
            logs = db.execute("""
                SELECT id, user_id,
                       COALESCE(prompt, user_message, '') as prompt,
                       response,
                       COALESCE(tokens, input_tokens + output_tokens, 0) as tokens,
                       COALESCE(cost, cost_usd, 0) as cost,
                       latency_ms, timestamp, mode
                FROM api_logs
                ORDER BY timestamp DESC LIMIT 100
            """).fetchall()
        else:
            logs = db.execute("""
                SELECT id, user_id,
                       COALESCE(prompt, user_message, '') as prompt,
                       response,
                       COALESCE(tokens, input_tokens + output_tokens, 0) as tokens,
                       COALESCE(cost, cost_usd, 0) as cost,
                       latency_ms, timestamp, mode
                FROM api_logs
                WHERE user_id = ?
                ORDER BY timestamp DESC LIMIT 100
            """, (current_user.user_id,)).fetchall()
    finally:
        db.close()
    return jsonify([dict(r) for r in logs])

# ── Stats ─────────────────────────────────────────────────────────────────────
@app.route("/api/stats")
@login_required
def get_stats():
    db = get_db()
    try:
        if current_user.role == 'admin':
            total = db.execute("""
                SELECT COUNT(*) as calls,
                       SUM(COALESCE(tokens, input_tokens+output_tokens, 0)) as total_tokens,
                       ROUND(SUM(COALESCE(cost, cost_usd, 0)), 4) as total_cost
                FROM api_logs
            """).fetchone()

            per_user = db.execute("""
                SELECT user_id, COUNT(*) as calls,
                       SUM(COALESCE(tokens, input_tokens+output_tokens, 0)) as tokens,
                       ROUND(SUM(COALESCE(cost, cost_usd, 0)), 4) as cost
                FROM api_logs
                GROUP BY user_id ORDER BY cost DESC
            """).fetchall()

            per_day = db.execute("""
                SELECT DATE(timestamp) as day, COUNT(*) as calls,
                       ROUND(SUM(COALESCE(cost, cost_usd, 0)), 4) as cost
                FROM api_logs
                GROUP BY DATE(timestamp)
                ORDER BY day DESC LIMIT 7
            """).fetchall()
        else:
            total = db.execute("""
                SELECT COUNT(*) as calls,
                       SUM(COALESCE(tokens, input_tokens+output_tokens, 0)) as total_tokens,
                       ROUND(SUM(COALESCE(cost, cost_usd, 0)), 4) as total_cost
                FROM api_logs
                WHERE user_id = ?
            """, (current_user.user_id,)).fetchone()
            per_user = []
            per_day = []
    finally:
        db.close()

    return jsonify({
        "totals":   dict(total) if total else {"calls":0, "total_tokens":0, "total_cost":0},
        "per_user": [dict(r) for r in per_user],
        "per_day":  [dict(r) for r in per_day]
    })

# ── Policies ──────────────────────────────────────────────────────────────────
@app.route("/api/policies", methods=["GET"])
@admin_required
def get_policies():
    db = get_db()
    try:
        rows = db.execute("SELECT * FROM policies ORDER BY created_at DESC").fetchall()
    finally:
        db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/policies", methods=["POST"])
@admin_required
def save_policy():
    data = request.get_json()
    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM policies WHERE user_id = ?", (data["user_id"],)
        ).fetchone()
        if existing:
            db.execute("""
                UPDATE policies SET
                    max_tokens_day = ?, max_cost_day = ?,
                    max_calls_day  = ?, is_active    = 1
                WHERE user_id = ?
            """, (data["max_tokens_day"], data["max_cost_day"],
                  data["max_calls_day"], data["user_id"]))
        else:
            db.execute("""
                INSERT INTO policies (user_id, max_tokens_day, max_cost_day, max_calls_day)
                VALUES (?, ?, ?, ?)
            """, (data["user_id"], data["max_tokens_day"],
                  data["max_cost_day"], data["max_calls_day"]))
        db.commit()
    finally:
        db.close()
    return jsonify({"status": "saved"})

@app.route("/api/policies/<user_id>", methods=["DELETE"])
@admin_required
def delete_policy(user_id):
    db = get_db()
    try:
        db.execute("UPDATE policies SET is_active = 0 WHERE user_id = ?", (user_id,))
        db.commit()
    finally:
        db.close()
    return jsonify({"status": "deactivated"})

# ── Alerts ────────────────────────────────────────────────────────────────────
@app.route("/api/alerts")
@admin_required
def get_alerts():
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 50"
        ).fetchall()
    finally:
        db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/alerts/<int:alert_id>/resolve", methods=["POST"])
@admin_required
def resolve_alert(alert_id):
    db = get_db()
    try:
        db.execute("UPDATE alerts SET resolved = 1 WHERE id = ?", (alert_id,))
        db.commit()
    finally:
        db.close()
    return jsonify({"status": "resolved"})

# ── Usage ─────────────────────────────────────────────────────────────────────
@app.route("/api/usage/<user_id>")
@login_required
def get_user_usage(user_id):
    if current_user.role != 'admin' and current_user.user_id != user_id:
        abort(403)
    usage  = get_today_usage(user_id)
    policy = get_policy(user_id)
    return jsonify({"usage": usage, "policy": policy})

# ── Export ────────────────────────────────────────────────────────────────────
@app.route("/admin/export")
@admin_required
def export_csv():
    user_filter = request.args.get("user_id")
    mode_filter = request.args.get("mode")

    query  = "SELECT * FROM api_logs WHERE 1=1"
    params = []
    if user_filter:
        query += " AND user_id = ?"
        params.append(user_filter)
    if mode_filter:
        query += " AND mode = ?"
        params.append(mode_filter)
    query += " ORDER BY timestamp DESC"

    db = get_db()
    try:
        rows = db.execute(query, params).fetchall()
    finally:
        db.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "timestamp", "user_id", "mode",
                     "tokens", "cost", "latency_ms", "prompt", "response"])
    for row in rows:
        writer.writerow([
            row["id"], row["timestamp"], row["user_id"],
            row["mode"] if "mode" in row.keys() else "general",
            row["tokens"] if "tokens" in row.keys() else 0,
            row["cost"]   if "cost"   in row.keys() else 0,
            row["latency_ms"], row["prompt"] if "prompt" in row.keys() else "",
            row["response"],
        ])

    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=aiproxy_logs.csv"})

# ── Sessions ─────────────────────────────────────────────────────────────────────
@app.route("/api/sessions/<user_id>")
@login_required
def get_sessions(user_id):
    if current_user.role != 'admin' and current_user.user_id != user_id:
        abort(403)
    db = get_db()
    try:
        rows = db.execute("""
            SELECT session_id,
                   COUNT(*) as message_count,
                   MIN(timestamp) as started_at,
                   MAX(timestamp) as last_at,
                   SUM(COALESCE(tokens,0)) as total_tokens
            FROM api_logs
            WHERE user_id = ? AND session_id IS NOT NULL AND session_id != ''
            GROUP BY session_id
            ORDER BY last_at DESC
        """, (user_id,)).fetchall()
    finally:
        db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/sessions/<user_id>/<session_id>")
@login_required
def get_session_messages(user_id, session_id):
    if current_user.role != 'admin' and current_user.user_id != user_id:
        abort(403)
    db = get_db()
    try:
        rows = db.execute("""
            SELECT id, prompt, response, tokens, cost,
                   latency_ms, mode, timestamp
            FROM api_logs
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp ASC
        """, (user_id, session_id)).fetchall()
    finally:
        db.close()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)