"""
broadcast_route.py

Periodically checks Airtable for leads that have an AI-generated follow-up
message but haven't been messaged on WhatsApp yet, sends them via Twilio,
and marks them as sent.

How to wire this into your existing Flask app (app.py or main.py):

    from broadcast_route import broadcast_bp, start_scheduler

    app.register_blueprint(broadcast_bp)
    start_scheduler()   # starts the background job that runs every N minutes

Required Railway environment variables (you already have these):
    TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN
    TWILIO_WHATSAPP_FROM      e.g. whatsapp:+14155238886
    TWILIO_TEMPLATE_SID       e.g. HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    AIRTABLE_API_KEY
    AIRTABLE_BASE_ID
"""

import os
import time
import logging
import threading

import requests
from flask import Blueprint, jsonify
from twilio.rest import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("broadcast")

# ---------- Config (pulled from Railway env vars) ----------
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM")  # whatsapp:+14155238886
TWILIO_TEMPLATE_SID = os.environ.get("TWILIO_TEMPLATE_SID")    # HX...

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.environ.get("AIRTABLE_TABLE_NAME", "Leads")

# How often the background job checks Airtable for new leads to message
BROADCAST_INTERVAL_SECONDS = int(os.environ.get("BROADCAST_INTERVAL_SECONDS", 300))  # default 5 min

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

broadcast_bp = Blueprint("broadcast", __name__)

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def fetch_unsent_leads():
    """
    Fetch records from Airtable where:
      - AI Message field is not empty
      - WhatsApp Sent checkbox is not checked
    """
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

    # Airtable formula: only rows with a message AND not yet sent
    formula = "AND({AI Message} != '', NOT({WhatsApp Sent}))"
    params = {"filterByFormula": formula}

    response = requests.get(AIRTABLE_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json().get("records", [])


def mark_as_sent(record_id):
    """Set WhatsApp Sent = True for a given Airtable record."""
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{AIRTABLE_URL}/{record_id}"
    payload = {"fields": {"WhatsApp Sent": True}}

    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()


def send_whatsapp_message(to_number, name, property_type):
    """
    Send a WhatsApp template message via Twilio.
    to_number should be in E.164 format, e.g. +919876543210
    """
    if not to_number.startswith("+"):
        to_number = "+" + to_number.lstrip("0")

    message = twilio_client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=f"whatsapp:{to_number}",
        content_sid=TWILIO_TEMPLATE_SID,
        content_variables=f'{{"1":"{name}","2":"{property_type}"}}',
    )
    return message.sid


def run_broadcast():
    """Main job: fetch unsent leads, message each one, mark as sent."""
    logger.info("Checking Airtable for unsent leads...")
    try:
        leads = fetch_unsent_leads()
    except Exception as e:
        logger.error(f"Failed to fetch leads from Airtable: {e}")
        return

    if not leads:
        logger.info("No unsent leads found.")
        return

    logger.info(f"Found {len(leads)} unsent lead(s).")

    for record in leads:
        record_id = record["id"]
        fields = record.get("fields", {})

        name = fields.get("Name", "there")
        phone = fields.get("Phone")
        property_type = fields.get("Property", "your requirement")

        if not phone:
            logger.warning(f"Skipping record {record_id} — no phone number.")
            continue

        try:
            sid = send_whatsapp_message(phone, name, property_type)
            logger.info(f"Sent message to {name} ({phone}) — SID: {sid}")
            mark_as_sent(record_id)
        except Exception as e:
            logger.error(f"Failed to send message to {name} ({phone}): {e}")


def _scheduler_loop():
    while True:
        run_broadcast()
        time.sleep(BROADCAST_INTERVAL_SECONDS)


def start_scheduler():
    """Starts the background thread that runs the broadcast job periodically."""
    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()
    logger.info(f"Broadcast scheduler started — runs every {BROADCAST_INTERVAL_SECONDS} seconds.")


# ---------- Manual trigger route (optional, for testing) ----------
@broadcast_bp.route("/broadcast/run-now", methods=["GET", "POST"])
def trigger_broadcast_now():
    """Manually trigger a broadcast run via HTTP — useful for testing."""
    run_broadcast()
    return jsonify({"status": "broadcast run triggered"})