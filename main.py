import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Active models list (Fallback System)
CANDIDATE_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]

@app.route("/", methods=["GET"])
def home():
    return "Jarvis is Online and Active!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        reply_text = None
        last_error = ""

        # Loop through available models until one works
        for model_name in CANDIDATE_MODELS:
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": user_text}]
            }
            try:
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers).json()
                if "choices" in res and len(res["choices"]) > 0:
                    reply_text = res["choices"][0]["message"]["content"]
                    break
                elif "error" in res:
                    last_error = res["error"].get("message", "Unknown error")
            except Exception as e:
                last_error = str(e)

        if not reply_text:
            reply_text = f"Groq Error: {last_error}"

        # Send response to Telegram
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": chat_id, "text": reply_text})

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
