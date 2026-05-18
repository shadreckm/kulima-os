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
        # Extract message data from Twilio
        incoming_msg = request.form["Body"].strip()
        sender_phone = request.form["From"].strip()
        message_sid = request.form.get("MessageSid", "unknown").strip()

        if not incoming_msg or not sender_phone:
            return twiml_response(
                "Activity recorded (best effort interpretation). "
                "We could not read your message — please try again."
            )

        print(f"[{message_sid}] Incoming message from {sender_phone}: {incoming_msg}")

        success, response_msg = process_message(incoming_msg, sender_phone)
        print(f"[{message_sid}] Response: {response_msg}")

        if not response_msg:
            response_msg = (
                "Activity recorded (best effort interpretation). "
                "Thank you — your update supports local energy planning."
            )

        return twiml_response(response_msg)

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return twiml_response(
            "Activity recorded (best effort interpretation). "
            "A temporary error occurred — please send your update again shortly."
        )


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
    app.run(host="0.0.0.0", port=5000, debug=False)
