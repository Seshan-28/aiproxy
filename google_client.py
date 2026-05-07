# google_client.py
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

def call_google(user_message: str, system_prompt: str = "You are a helpful assistant.") -> dict:
    """
    Google AI Studio client using gemini-2.5-flash-lite.
    Returns same keys as mock_claude_client — app.py needs zero changes besides import.
    """
    start_time = time.time()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }

    body = {
        "systemInstruction": {
            "parts": [
                {"text": system_prompt}
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": user_message}
                ]
            }
        ]
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=body,
            timeout=60
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)
        data = response.json()

        # Print full response for debugging
        print(f"[Google AI] Status: {response.status_code}")
        # Uncomment the line below to view full response
        # print(f"[Google AI] Response: {data}")

        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            return {
                "reply":      f"API Error: {error_msg}",
                "tokens":     0,
                "cost":       0.0,
                "latency_ms": latency_ms,
            }

        reply      = data["candidates"][0]["content"]["parts"][0]["text"]
        usage      = data.get("usageMetadata", {})
        input_tok  = usage.get("promptTokenCount", 0)
        output_tok = usage.get("candidatesTokenCount", 0)
        total_tok  = usage.get("totalTokenCount", input_tok + output_tok)
        cost       = 0.0  # adjust if needed

        print(f"""
--- AIPROXY LOG (Gemini 2.5 Flash Lite via Google AI) ---
Input tok  : {input_tok}
Output tok : {output_tok}
Total tok  : {total_tok}
Latency    : {latency_ms}ms
------------------------------------------------""")

        return {
            "reply":      reply,
            "tokens":     total_tok,
            "cost":       cost,
            "latency_ms": latency_ms,
        }

    except requests.exceptions.Timeout:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "reply":      "Request timed out — try again.",
            "tokens":     0,
            "cost":       0.0,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        print(f"[Google AI Exception] {e}")
        return {
            "reply":      f"Connection error: {str(e)}",
            "tokens":     0,
            "cost":       0.0,
            "latency_ms": latency_ms,
        }
