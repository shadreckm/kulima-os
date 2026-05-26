"""
Twilio webhook endpoint for WhatsApp message processing
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import uuid
from fastapi.responses import Response

from backend.database.connection import get_db
from backend.database.models import Signal
from backend.utils.signal_normalizer import normalize_signal_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
@router.post("/webhook/twilio")
async def twilio_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Twilio webhook endpoint for receiving WhatsApp messages.
    
    Expected Twilio webhook format:
    - From: WhatsApp number (e.g., whatsapp:+265123456789)
    - Body: Message text (e.g., "watering crops in Mzuzu this morning")
    - MessageSid: Unique message ID
    
    Pipeline:
    1. Receive WhatsApp message
    2. Parse text to extract activity, zone, time window
    3. Normalize to structured signal
    4. Store in database
    5. Signal enters coordination pipeline automatically
    """
    try:
        # Parse form data from Twilio webhook
        form_data = await request.form()
        
        # Extract Twilio webhook fields
        from_number = form_data.get('From', '')
        message_body = form_data.get('Body', '')
        message_sid = form_data.get('MessageSid', '')
        
        logger.info(f"Received WhatsApp message from {from_number}: {message_body}")
        
        # Validate message
        if not message_body or not message_body.strip():
            logger.warning("Empty message received from Twilio webhook")
            raise HTTPException(status_code=400, detail="Empty message body")

        # Normalize the message text to structured signal
        normalized_signal = normalize_signal_text(message_body)
        
        logger.info(f"Normalized signal: {normalized_signal}")
        
        # Extract phone number (remove 'whatsapp:' prefix)
        phone_number = from_number.replace('whatsapp:', '') if from_number else 'unknown'
        phone_number = phone_number or 'anonymous'

        # Determine whether this sender is new to the WhatsApp flow
        first_time_sender = db.query(Signal).filter(Signal.user_id == phone_number, Signal.source == 'whatsapp').count() == 0
        
        # Create new signal record (store original_text)
        new_signal = Signal(
            id=f"sig_{uuid.uuid4().hex[:12]}",
            zone=normalized_signal.get('zone', 'MZUZU'),
            activity_type=normalized_signal.get('activity_type', 'unknown'),
            sector=normalized_signal.get('sector') or 'general',
            time_window=normalized_signal.get('time_window', 'unknown'),
            source='whatsapp',
            user_id=phone_number,
            timestamp=datetime.utcnow(),
            original_text=normalized_signal.get('original_text', message_body)
        )
        
        # Store in database synchronously
        db.add(new_signal)
        db.commit()
        db.refresh(new_signal)
        
        logger.info(f"Signal stored in database with ID: {new_signal.id}")

        if first_time_sender:
            twiml_message = (
                "Welcome to Kulima OS 👋\n"
                "Send a message like:\n"
                "'irrigation mzuzu morning'\n"
                "and we will analyze your area."
            )
        else:
            twiml_message = (
                "✅ Activity recorded.\n"
                "Kulima OS is analyzing patterns in your area.\n"
                "Keep sending activities to improve insights."
            )

        response_content = f"<Response><Message>{twiml_message}</Message></Response>"
        return Response(content=response_content, media_type='application/xml')
        
    except Exception as e:
        logger.error(f"Error processing Twilio webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error processing message")


@router.post("/webhook/test")
async def test_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Test webhook endpoint for simulating Twilio messages without actual Twilio integration.
    
    Body format:
    {
        "from": "+265123456789",
        "body": "watering crops in Mzuzu this morning"
    }
    """
    try:
        try:
            body_data = await request.json()
        except Exception:
            logger.warning("Invalid JSON received at test webhook")
            return {"status": "error", "message": "Invalid JSON payload"}
        
        from_number = body_data.get('from', '')
        message_body = body_data.get('body', '')
        
        logger.info(f"Test webhook - Received message from {from_number}: {message_body}")
        
        if not message_body or not str(message_body).strip():
            return {"status": "error", "message": "Empty message"}
        
        # Normalize the message text
        normalized_signal = normalize_signal_text(message_body)
        
        logger.info(f"Normalized signal: {normalized_signal}")
        
        # Create new signal record (store original_text)
        new_signal = Signal(
            id=f"sig_{uuid.uuid4().hex[:12]}",
            zone=normalized_signal.get('zone', 'UNKNOWN'),
            activity_type=normalized_signal.get('activity_type', 'unknown'),
            sector=normalized_signal.get('sector') or 'general',
            time_window=normalized_signal.get('time_window', 'unknown'),
            source='test',
            user_id=from_number or 'anonymous',
            timestamp=datetime.utcnow(),
            original_text=normalized_signal.get('original_text', message_body)
        )
        
        # Store in database
        db.add(new_signal)
        db.commit()
        db.refresh(new_signal)
        
        logger.info(f"Test signal stored in database with ID: {new_signal.id}")
        
        return {
            "status": "success",
            "message": "Test signal received and stored",
            "signal_id": new_signal.id,
            "normalized_signal": normalized_signal
        }
    except Exception as e:
        logger.error(f"Error in test webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}