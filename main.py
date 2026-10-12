import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

CANDIDATE_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]

# File to store permanent chat history
HISTORY_FILE = "chat_history.json"

def load_histories():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_histories(histories):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(histories, f)
    except Exception as e:
        print(f"Error saving history: {e}")

SYSTEM_PROMPT = (
    "You are AK JARVIS, an elite, highly intelligent, and loyal personal AI assistant "
    "created and powered by AK MEDIA. Your creator and boss is Ankush (CEO). "
    "You speak with ultimate confidence, professional yet friendly tone, mixing Hindi (in Latin script/Hinglish) and English naturally. "
    "You must carefully remember previous context and user details (like favorite colors, startup info, names) mentioned earlier in the chat, address your user respectfully, and execute tasks with supreme efficiency."
)

@app.route("/", methods=["GET"])
def home():
    return "AK JARVIS Permanent Memory Core is Online!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = str(data["message"]["chat"]["id"])
        user_text = data["message"].get("text", "")
        
        chat_histories = load_histories()
        
        if chat_id not in chat_histories:
            chat_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Append user message
        chat_histories[chat_id].append({"role": "user", "content": user_text})
        
        # Keep manageable length
        if len(chat_histories[chat_id]) > 15:
            chat_histories[chat_id] = [chat_histories[chat_id][0]] + chat_histories[chat_id][-14:]

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        reply_text = None
        last_error = ""

        for model_name in CANDIDATE_MODELS:
            payload = {
                "model": model_name,
                "messages": chat_histories[chat_id]
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
        else:
            # Append assistant reply and save to file
            chat_histories[chat_id].append({"role": "assistant", "content": reply_text})
            save_histories(chat_histories)

        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": chat_id, "text": reply_text})

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
