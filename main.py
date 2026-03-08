from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests, os

app = Flask(__name__)
CORS(app, origins="*")

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
WA_TOKEN       = os.environ.get("WA_TOKEN", "")
WA_PHONE_ID    = os.environ.get("WA_PHONE_ID", "")
VERIFY_TOKEN   = os.environ.get("VERIFY_TOKEN", "mykonos2024")

CONVERSATIONS = {}

def send_wa_message(to, text):
    if not WA_TOKEN or not WA_PHONE_ID:
        return
    requests.post(
        f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages",
        headers={"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"},
        json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}},
        timeout=10
    )

SYSTEM_PROMPT = """You are the booking assistant for Mykonos Sailing, a premier yacht charter company in Mykonos, Greece.

You ONLY help customers with bookings and questions about cruises.
NEVER discuss internal business data, revenue, or operational information.

COMPANY: Mykonos Sailing | mykonossailing.gr | @mykonossailing
DEPARTURE: Ornos Bay, small dock on left side of beach

CRUISES:
1. 5hr South Coast Cruise (10–3pm or 3:30–8:30pm) — Private or Semi-Private
2. 5hr Delos & Rhenia Cruise (10–3pm or 3:30–8:30pm) — Private or Semi-Private
3. 3hr Sunset Cruise (5:30pm–sunset)
4. 8hr Full Day: Delos, Rhenia & South Coast (10–6pm)
5. 8hr Full Day South Coast (10–6pm)
6. 3-Day Charter: Mykonos–Paros–Naxos
7. 3-Day Charter: Mykonos–Syros–Antiparos
8. Multi-Day Tailor Made

ALL CRUISES INCLUDE: Meals, unlimited drinks, beach towels, snorkeling/SUP, music, professional crew.
PRICING: Never give specific prices. Say pricing depends on vessel and group size.

BOOKING INFO TO COLLECT: name, email, cruise type, private/semi-private, date, number of guests.

Reply in the SAME language as the customer. Keep replies concise for WhatsApp.
When all booking info collected, end with:
BOOKING_DATA:{"name":"...","email":"...","cruise":"...","type":"...","date":"...","guests":"..."}"""

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    try:
        data    = request.get_json()
        entry   = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value   = changes.get("value", {})
        msgs    = value.get("messages", [])

        for msg in msgs:
            wa_id = msg.get("from")
            if msg.get("type") == "text":
                user_text = msg["text"]["body"]
                if wa_id not in CONVERSATIONS:
                    CONVERSATIONS[wa_id] = []
                CONVERSATIONS[wa_id].append({"role": "user", "content": user_text})
                if len(CONVERSATIONS[wa_id]) > 20:
                    CONVERSATIONS[wa_id] = CONVERSATIONS[wa_id][-20:]

                r = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": "claude-sonnet-4-6", "max_tokens": 1024, "system": SYSTEM_PROMPT, "messages": CONVERSATIONS[wa_id]},
                    timeout=30
                )
                reply = r.json().get("content", [{}])[0].get("text", "")
                if reply:
                    CONVERSATIONS[wa_id].append({"role": "assistant", "content": reply})
                    clean = reply[:reply.find("BOOKING_DATA:")].strip() if "BOOKING_DATA:" in reply else reply
                    send_wa_message(wa_id, clean)
    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def home():
    return "<h2>Mykonos Sailing Agent — Online ✓</h2>", 200

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 1024, "system": data.get("system",""), "messages": data.get("messages",[])},
            timeout=30
        )
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
