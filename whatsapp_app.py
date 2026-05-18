"""
LUMOZA WhatsApp Flask Server

Simple, fast MVP server that receives WhatsApp messages via Twilio webhook
and routes them through the signal pipeline.

Startup:
    python whatsapp_app.py

Then configure Twilio webhook to point to:
    http://your-server/webhook
"""

from flask import Flask, request, jsonify, Response
import os
import xml.sax.saxutils
from whatsapp_handler import process_message
from signal_storage import get_unprocessed_signals
from twilio.twiml.messaging_response import MessagingResponse
from threading import Thread

app = Flask(__name__)


def twiml_response(message: str) -> Response:
    """Build a valid Twilio TwiML XML response (UTF-8, escaped body)."""
    safe_body = xml.sax.saxutils.escape(message or "")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe_body}</Message>
</Response>"""
    return Response(twiml, mimetype="application/xml")

# Environment variables (set these in production)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "test-account")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "test-token")
TWILIO_PHONE = os.getenv("TWILIO_PHONE", "+1234567890")


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Twilio WhatsApp webhook endpoint.
    
    Receives incoming messages and processes them through LUMOZA.
    """
    try:
        # Extract message data from Twilio (lightweight parsing only)
        incoming_msg = request.form.get("Body", "").strip()
        sender_phone = request.form.get("From", "").strip()
        message_sid = request.form.get("MessageSid", "unknown").strip()

        # Build quick Twilio MessagingResponse acknowledgment
        resp = MessagingResponse()

        if not incoming_msg or not sender_phone:
            print("Incoming message: <missing or empty>")
            resp.message(
                "Activity recorded (best effort interpretation). We could not read your message — please try again."
            )
            print("Response:", resp)
            print("Webhook latency-safe response sent")
            return str(resp)

        print("Incoming message:", incoming_msg)
        print(f"Message SID: {message_sid} From: {sender_phone}")

        # Immediate, fast acknowledgement to avoid Twilio timeouts
        resp.message("✅ Activity recorded. Processing signal...")

        # Background processing so the webhook can return immediately
        def _background_process(msg, phone, sid):
            try:
                print(f"Background processing started for SID {sid}")
                success, response_msg = process_message(msg, phone)
                print(f"Background processing complete for SID {sid}: success={success}")
            except Exception as e:
                print("Background processing ERROR:", str(e))

        thread = Thread(target=_background_process, args=(incoming_msg, sender_phone, message_sid), daemon=True)
        thread.start()

        print("Webhook latency-safe response sent")
        return str(resp)

    except Exception as e:
        print("ERROR:", str(e))
        resp = MessagingResponse()
        resp.message("System error occurred. Please try again.")
        return str(resp)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route("/signals", methods=["GET"])
def get_signals():
    """
    Debug endpoint: retrieve all stored signals.
    
    Optional query param: ?zone=ZONE_A
    """
    zone = request.args.get("zone")
    
    # Get unprocessed signals (default)
    signals = get_unprocessed_signals(zone=zone)
    
    return jsonify({
        "count": len(signals),
        "signals": [s.to_dict() for s in signals]
    }), 200


@app.route("/status", methods=["GET"])
def status():
    """Get system status."""
    unprocessed = get_unprocessed_signals()
    
    zones = set(s.zone for s in unprocessed)
    activities = set(s.activity_type for s in unprocessed)
    
    return jsonify({
        "system": "LUMOZA WhatsApp Interface",
        "status": "running",
        "unprocessed_signals": len(unprocessed),
        "zones": list(zones),
        "activities": list(activities)
    }), 200


@app.route("/", methods=["GET"])
def index():
    """Welcome message."""
    return jsonify({
        "service": "LUMOZA WhatsApp Interface (MVP)",
        "status": "active",
        "endpoints": {
            "webhook": "POST /webhook (Twilio integration)",
            "health": "GET /health",
            "signals": "GET /signals (debug)",
            "status": "GET /status"
        }
    }), 200


if __name__ == "__main__":
    # Run Flask server
    # In production, use gunicorn or similar
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
