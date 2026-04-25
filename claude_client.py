import anthropic
import time
from config import Config

client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

def call_claude(user_message: str, system_prompt: str = "You are a helpful assistant.") -> dict:
    """
    Real Anthropic API wrapper.
    Returns same keys as mock_claude_client so /chat route works identically.
    """
    model = "claude-sonnet-4-20250514"
    start_time = time.time()

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    latency_ms    = round((time.time() - start_time) * 1000)
    input_tokens  = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    input_cost  = (input_tokens  / 1_000_000) * 3.00
    output_cost = (output_tokens / 1_000_000) * 15.00
    total_cost  = round(input_cost + output_cost, 6)
    total_tokens = input_tokens + output_tokens

    print(f"""
--- AIPROXY API LOG ---
Model      : {model}
Input tok  : {input_tokens}
Output tok : {output_tokens}
Total tok  : {total_tokens}
Cost (USD) : ${total_cost}
Latency    : {latency_ms}ms
-----------------------""")

    # ← Same keys as mock_claude_client so /chat needs zero changes
    return {
        "reply":      response.content[0].text,
        "tokens":     total_tokens,
        "cost":       total_cost,
        "latency_ms": latency_ms,
    }