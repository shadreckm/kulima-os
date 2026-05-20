"""
WhatsApp webhook handler
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Optional

router = APIRouter()


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Receive WhatsApp messages via webhook.
    
    This endpoint receives messages from WhatsApp Business API
    and processes them as coordination signals.
    """
    try:
        # Parse webhook payload
        data = await request.json()
        
        # Extract message data
        # TODO: Implement WhatsApp message parsing
        # TODO: Extract activity type, zone, time window
        # TODO: Call signal creation endpoint
        
        return {"status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook/whatsapp/verify")
async def whatsapp_webhook_verify(
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None
):
    """
    Verify WhatsApp webhook.
    
    This endpoint is used by WhatsApp to verify the webhook URL.
    """
    from backend.config import settings
    
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return hub_challenge
    else:
        raise HTTPException(status_code=403, detail="Verification failed")
