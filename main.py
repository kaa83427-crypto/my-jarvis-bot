import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "Jarvis is Online and Active!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")
        
        # Groq API Headers
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Updated Model: llama-3.3-70b-versatile
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": user_text}]
        }
        
        try:
            groq_res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers).json()
            
            # Extract response
            if "choices" in groq_res and len(groq_res["choices"]) > 0:
                reply_text = groq_res["choices"][0]["message"]["content"]
            elif "error" in groq_res:
                reply_text = f"Groq Error: {groq_res['error'].get('message', 'Unknown error')}"
            else:
                reply_text = f"Groq Raw Response: {str(groq_res)}"
                
        except Exception as e:
            reply_text = f"Server Exception: {str(e)}"

        # Send back to Telegram
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": chat_id, "text": reply_text})

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
