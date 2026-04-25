# policy_engine.py
from database import get_db
from datetime import date

def get_policy(user_id):
    """Fetch policy for user. Returns default if none set."""
    conn = get_db()
    policy = conn.execute("""
        SELECT * FROM policies WHERE user_id = ? AND is_active = 1
    """, (user_id,)).fetchone()
    conn.close()

    if policy:
        return dict(policy)

    # Default policy for users with no custom rule
    return {
        "user_id": user_id,
        "max_tokens_day": 10000,
        "max_cost_day": 1.00,
        "max_calls_day": 50,
        "is_active": 1
    }

def get_today_usage(user_id):
    conn = get_db()
    usage = conn.execute("""
        SELECT
            COUNT(*) as calls,
            COALESCE(SUM(input_tokens + output_tokens + COALESCE(tokens,0)), 0) as tokens,
            COALESCE(ROUND(SUM(COALESCE(cost_usd,0) + COALESCE(cost,0)), 6), 0) as cost
        FROM api_logs
        WHERE user_id = ? AND DATE(timestamp) = DATE('now')
    """, (user_id,)).fetchone()
    conn.close()
    return dict(usage)

def fire_alert(user_id, alert_type, message, value, limit_val):
    """Write an alert to the database."""
    conn = get_db()
    conn.execute("""
        INSERT INTO alerts (user_id, alert_type, message, value, limit_val)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, alert_type, message, value, limit_val))
    conn.commit()
    conn.close()
    print(f"[AIProxy ALERT] {alert_type} — {user_id}: {message}")

def check_policy(user_id):
    """
    Main enforcement function.
    Returns: (allowed: bool, reason: str, usage: dict, policy: dict)
    """
    policy = get_policy(user_id)
    usage  = get_today_usage(user_id)

    # Check calls limit
    if usage["calls"] >= policy["max_calls_day"]:
        msg = f"Daily call limit reached: {usage['calls']}/{policy['max_calls_day']}"
        fire_alert(user_id, "CALL_LIMIT", msg, usage["calls"], policy["max_calls_day"])
        return False, msg, usage, policy

    # Check token limit
    if usage["tokens"] >= policy["max_tokens_day"]:
        msg = f"Daily token limit reached: {usage['tokens']}/{policy['max_tokens_day']}"
        fire_alert(user_id, "TOKEN_LIMIT", msg, usage["tokens"], policy["max_tokens_day"])
        return False, msg, usage, policy

    # Check cost limit
    if usage["cost"] >= policy["max_cost_day"]:
        msg = f"Daily cost limit reached: ${usage['cost']}/${policy['max_cost_day']}"
        fire_alert(user_id, "COST_LIMIT", msg, usage["cost"], policy["max_cost_day"])
        return False, msg, usage, policy

    # Soft warnings at 80%
    if usage["tokens"] >= policy["max_tokens_day"] * 0.8:
        msg = f"Token usage at 80%: {usage['tokens']}/{policy['max_tokens_day']}"
        fire_alert(user_id, "TOKEN_WARNING", msg, usage["tokens"], policy["max_tokens_day"])

    if usage["cost"] >= policy["max_cost_day"] * 0.8:
        msg = f"Cost usage at 80%: ${usage['cost']}/${policy['max_cost_day']}"
        fire_alert(user_id, "COST_WARNING", msg, usage["cost"], policy["max_cost_day"])

    return True, "OK", usage, policy