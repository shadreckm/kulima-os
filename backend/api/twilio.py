"""
Twilio webhook endpoint for WhatsApp message processing
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import logging

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
        
        # Normalize the message text to structured signal
        normalized_signal = normalize_signal_text(message_body)
        
        logger.info(f"Normalized signal: {normalized_signal}")
        
        # Extract phone number (remove 'whatsapp:' prefix)
        phone_number = from_number.replace('whatsapp:', '') if from_number else 'unknown'
        
        # Create new signal record
        new_signal = Signal(
            zone=normalized_signal['zone'],
            activity_type=normalized_signal['activity_type'],
            time_window=normalized_signal['time_window'],
            source='whatsapp',
            user_id=phone_number,
            timestamp=datetime.utcnow()
        )
        
        # Store in database
        db.add(new_signal)
        db.commit()
        db.refresh(new_signal)
        
        logger.info(f"Signal stored in database with ID: {new_signal.id}")
        
        # Return Twilio-compatible response (TwiML)
        # For now, just return a simple acknowledgment
        return {
            "status": "success",
            "message": "Signal received and stored",
            "signal_id": new_signal.id
        }
        
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
        body_data = await request.json()
        
        from_number = body_data.get('from', '')
        message_body = body_data.get('body', '')
        
        logger.info(f"Test webhook - Received message from {from_number}: {message_body}")
        
        # Normalize the message text
        normalized_signal = normalize_signal_text(message_body)
        
        logger.info(f"Normalized signal: {normalized_signal}")
        
        # Create new signal record
        new_signal = Signal(
            zone=normalized_signal['zone'],
            activity_type=normalized_signal['activity_type'],
            time_window=normalized_signal['time_window'],
            source='test',
            user_id=from_number,
            timestamp=datetime.utcnow()
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
        raise HTTPException(status_code=500, detail="Error processing test message")
