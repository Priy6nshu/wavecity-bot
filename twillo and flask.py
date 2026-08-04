"""
Wave City WhatsApp Bot - Meta WhatsApp Cloud API Version
Replaces Twilio with Meta's FREE WhatsApp Cloud API
"""

import os
import json
import requests
from flask import Flask, request, jsonify
from wave_city_assistant_fixed import ConversationManager

app = Flask(__name__)

# ============================================================
# META WHATSAPP CLOUD API CONFIGURATION
# ============================================================
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "EAAOjbNmrttQBSDe4ByVxDXMBQqMjMlVGR5a2dZAduRGxa8oz1Huq48pYGAuCeZB6V58JNbSpxSBfA8gxmZC2vjzY6RdfLZCQbqy6xtsuCi9jAXZBThRULJcnFVslhZA62w2sZC0NXvUhorjKtAoX1LSH3QZBaILpofodBne3uFEBb54esspwkU1O2ds10JtGo1ZC7NaWQfNyxTDmiPKoqEMd62rB1bVn12Sdn1qTqGfHjDVhjvPKTgW5ntFa3ZBNhZBk4ZBMwZCH1jEkaPYMXUjsy9ezx4BzNQu918PtHHgZDZD")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "1285463671309876")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "2293611864811543")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "wavecity_verify_token_2024")

# Initialize the Wave City Assistant
assistant = ConversationManager()


def send_whatsapp_message(to_number: str, message: str):
    """Send message via Meta WhatsApp Cloud API"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print(f"Message sent successfully to {to_number}")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")
    
    return response


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Meta webhook verification - required first step"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return challenge, 200
    else:
        print(f"Webhook verification failed. Token: {token}")
        return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    """Receive and process incoming WhatsApp messages"""
    try:
        data = request.get_json()
        print(f"Incoming webhook: {json.dumps(data, indent=2)}")
        
        # Parse the message from Meta's webhook format
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return jsonify({"status": "no messages"}), 200
        
        message = messages[0]
        
        # Extract message details
        from_number = message.get("from")  # sender's WhatsApp number
        message_type = message.get("type")
        
        # Only process text messages
        if message_type != "text":
            send_whatsapp_message(
                from_number,
                "I can only process text messages at the moment. Please type your inquiry."
            )
            return jsonify({"status": "non-text message"}), 200
        
        user_message = message.get("text", {}).get("body", "")
        
        if not user_message:
            return jsonify({"status": "empty message"}), 200
        
        print(f"Message from {from_number}: {user_message}")
        
        # Process with Wave City Assistant
        response = assistant.process_message(from_number, user_message)
        
        # Send reply back
        send_whatsapp_message(from_number, response)
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        print(f"Error processing message: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Wave City WhatsApp Bot is running!",
        "version": "4.1 - Meta WhatsApp Cloud API",
        "agent": "Priyanshu",
        "agency": "Wave City",
        "phone": "+91 87438 29884"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Wave City Bot on port {port}")
    print(f"Webhook URL: https://wavecity-bot-production.up.railway.app/webhook")
    print(f"Verify Token: {VERIFY_TOKEN}")
    app.run(host="0.0.0.0", port=port, debug=False)