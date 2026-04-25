# # mock_claude_client.py
# import time
# import random
# from database import get_db
# from policy_engine import check_policy

# MOCK_RESPONSES = [
#     "This is a mock response from AIProxy. The system is functioning correctly.",
#     "Mock mode active. In production this would call Claude via Anthropic API.",
#     "AIProxy governance layer intercepted this request successfully.",
# ]

# def call_claude(user_message, system_prompt="You are a helpful assistant.", user_id="anonymous"):

#     # Policy enforcement — runs before every call
#     allowed, reason, usage, policy = check_policy(user_id)
#     if not allowed:
#         return {
#             "content": f"[AIProxy BLOCKED] {reason}",
#             "model": "blocked",
#             "input_tokens": 0,
#             "output_tokens": 0,
#             "cost_usd": 0,
#             "latency_ms": 0,
#             "user_id": user_id,
#             "blocked": True,
#             "reason": reason
#         }

#     time.sleep(0.3)

#     input_tokens  = random.randint(50, 300)
#     output_tokens = random.randint(80, 400)
#     input_cost    = (input_tokens / 1_000_000) * 3.00
#     output_cost   = (output_tokens / 1_000_000) * 15.00
#     total_cost    = round(input_cost + output_cost, 6)
#     latency_ms    = random.randint(200, 900)
#     response_text = random.choice(MOCK_RESPONSES)

#     conn = get_db()
#     conn.execute("""
#         INSERT INTO api_logs 
#         (user_id, model, user_message, response, input_tokens, output_tokens, cost_usd, latency_ms, system_prompt)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """, (user_id, "claude-sonnet-4-mock", user_message, response_text,
#           input_tokens, output_tokens, total_cost, latency_ms, system_prompt))
#     conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
#     conn.commit()
#     conn.close()

#     print(f"""
# --- AIPROXY API LOG ---
# User       : {user_id}
# Model      : claude-sonnet-4-mock
# Input tok  : {input_tokens}
# Output tok : {output_tokens}
# Cost (USD) : ${total_cost}
# Latency    : {latency_ms}ms
# -----------------------
#     """)

#     return {
#         "content": response_text,
#         "model": "claude-sonnet-4-mock",
#         "input_tokens": input_tokens,
#         "output_tokens": output_tokens,
#         "cost_usd": total_cost,
#         "latency_ms": latency_ms,
#         "user_id": user_id,
#         "blocked": False
#     }

# mock_claude_client.py  (updated signature only)

import random, time

def call_claude(prompt: str, system_prompt: str = None) -> dict:
    """Simulates a Claude API call. system_prompt accepted but not used in mock."""
    time.sleep(random.uniform(0.1, 0.4))
    words = len(prompt.split())
    tokens = random.randint(words * 3, words * 6 + 80)
    cost = round(tokens * 0.000002, 6)
    reply = (
        f"[MOCK] Responding to: '{prompt[:60]}{'...' if len(prompt)>60 else ''}' "
        f"— {tokens} tokens used."
    )
    return {"reply": reply, "tokens": tokens, "cost": cost}