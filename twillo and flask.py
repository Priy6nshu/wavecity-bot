from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import logging
from datetime import datetime

from wave_city_assistant_fixed import ConversationManager

app = Flask(__name__)
assistant = ConversationManager()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    sender_id    = request.form.get("From", "")
    sender_name  = request.form.get("ProfileName", "Customer")

    if not incoming_msg:
        return "OK", 200

    log.info(f"📩 [{sender_id}] {sender_name}: {incoming_msg}")

    try:
        response_text = assistant.process_message(sender_id, incoming_msg)
    except Exception as e:
        log.error(f"Bot error: {e}")
        response_text = "Sorry, technical issue. Please try again. 🙏"

    log.info(f"🤖 Priya → [{sender_id}]: {response_text[:80]}")

    try:
        summary = assistant.get_conversation_summary(sender_id)
        if summary["lead_classification"] in ["HOT_BUYER", "WARM_LEAD"]:
            log.info(f"🔥 HOT LEAD: {summary}")
    except:
        pass

    resp = MessagingResponse()
    resp.message(response_text)
    return str(resp), 200, {"Content-Type": "text/xml"}

@app.route("/", methods=["GET"])
def home():
    return {"status": "running", "bot": "Wave City WhatsApp AI Assistant", "time": datetime.now().isoformat()}

@app.route("/leads", methods=["GET"])
def leads():
    all_leads = []
    for user_id in assistant.conversation_history:
        summary = assistant.get_conversation_summary(user_id)
        all_leads.append(summary)
    all_leads.sort(key=lambda x: x["lead_score"], reverse=True)
    return {"total_conversations": len(all_leads), "leads": all_leads}

if __name__ == "__main__":
    print("="*50)
    print("  Wave City WhatsApp Bot — Running!")
    print("  POST /whatsapp  ← Twilio webhook")
    print("  GET  /leads     ← View all leads")
    print("="*50)
    app.run(debug=True, host="0.0.0.0", port=5000)