"""
Prospectus endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from datetime import datetime
from typing import Optional
import uuid
import logging
import os
from pathlib import Path
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal, Prospectus
from core.prospectus.prospectus_generator import ProspectusGenerator
from backend.utils.pattern_utils import generate_basic_patterns, get_productive_activities
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Ensure prospectus directory exists
PROSPECTUS_DIR = Path("prospectuses")
os.makedirs(PROSPECTUS_DIR, exist_ok=True)


class ProspectusRequest(BaseModel):
    """Pydantic model for prospectus generation validation"""
    zone: str = Field(..., min_length=1, description="Zone identifier")
    user_id: Optional[str] = Field(None, description="User identifier")


@router.post("/generate-prospectus")
async def generate_prospectus(request: ProspectusRequest, db: Session = Depends(get_db)):
    """
    Trigger PDF generation for a zone.
    
    Request body:
    {
      "zone": "MZUZU",
      "user_id": "user_123"
    }
    
    Response:
    {
      "status": "success",
      "data": {
        "prospectus_id": "pros_abc123",
        "pdf_url": "/api/v1/download/prospectus_mzuzu_2026-05-20.pdf",
        "json_url": "/api/v1/download/prospectus_mzuzu_2026-05-20.json",
        "generated_at": "2026-05-20T10:00:00Z"
      }
    }
    """
    try:
        zone = request.zone.upper()
        user_id = request.user_id or "anonymous"
        
        logger.info(f"Generating prospectus for zone: {zone}")
        
        # Generate prospectus ID
        prospectus_id = f"pros_{uuid.uuid4().hex[:12]}"
        
        # Generate timestamp for filename
        timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        zone_key = zone.upper()
        
        # Generate filename
        pdf_filename = f"prospectus_{zone_key}_{timestamp}.pdf"
        json_filename = f"prospectus_{zone_key}_{timestamp}.json"
        
        pdf_path = PROSPECTUS_DIR / pdf_filename
        json_path = PROSPECTUS_DIR / json_filename
        
        # Fetch signals from database
        signals = db.query(Signal).filter(Signal.zone == zone_key).all()
        logger.info(f"Found {len(signals)} signals for zone {zone}")
        
        # Generate patterns using core engines
        if not signals:
            logger.warning(f"No signals found for zone {zone}")
            return {
                "status": "error",
                "data": {
                    "error": f"No signals found for zone {zone}. Cannot generate prospectus without data."
                }
            }
        
        signal_data = []
        for signal in signals:
            signal_data.append({
                "zone": signal.zone,
                "activity_type": signal.activity_type,
                "time_window": signal.time_window,
                "timestamp": signal.timestamp.isoformat(),
                "source": signal.source,
                "user_id": signal.user_id
            })
        
        # Add cycle_index to each signal
        for i, signal in enumerate(signal_data):
            signal["cycle_index"] = i
        
        # Generate basic patterns using aggregation
        logger.info("Generating basic patterns...")
        patterns = generate_basic_patterns(signal_data)
        logger.info(f"Generated {len(patterns)} patterns")
        
        if not patterns:
            logger.warning(f"No activity data available for zone {zone}")
            raise HTTPException(status_code=404, detail="No activity data available")
        
        # Generate prospectus using basic patterns
        logger.info("Generating prospectus from basic patterns...")
        gen = ProspectusGenerator()
        metadata = {
            "region": zone_key,
            "period": "7-cycle window (1 week)",
            "is_sample": False
        }
        
        # Create simple confidence results for prospectus generation
        confidence_results = []
        for pattern in patterns:
            confidence_results.append({
                "activity_type": pattern["activity_type"],
                "time_window": pattern["time_window"],
                "zone": pattern["zone"],
                "confidence_class": "high",
                "confidence_score": 0.9,
                "demand_class": "moderate",
                "infrastructure_implication": "Consider infrastructure investment",
                "trust": {
                    "trust_score": 0.9,
                    "trust_level": "high"
                }
            })
        
        # Use basic planning reserve
        planning_reserve = {"total_reserve": len(patterns) * 100}
        
        # Create basic lundai analysis
        lundai_analysis = {
            "settlement_density": "moderate",
            "infrastructure_coverage": "partial",
            "demand_concentration": patterns
        }
        
        prospectus = gen.generate_prospectus(
            confidence_results,
            lundai_analysis=lundai_analysis,
            metadata=metadata,
            planning_reserve=planning_reserve,
        )
        
        # Save PDF
        gen.generate_pdf(prospectus, str(pdf_path))
        logger.info(f"PDF saved to: {pdf_path}")
        
        # Save JSON
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(prospectus, f, indent=2)
        logger.info(f"JSON saved to: {json_path}")
        
        # Store prospectus in database
        db_prospectus = Prospectus(
            id=prospectus_id,
            zone=zone_key,
            user_id=user_id,
            pdf_url=f"/api/v1/download/{pdf_filename}",
            json_url=f"/api/v1/download/{json_filename}",
            meta_data=json.dumps(metadata),
        )
        db.add(db_prospectus)
        db.commit()
        
        logger.info(f"Prospectus stored in database: {prospectus_id}")
        
        return {
            "status": "success",
            "data": {
                "prospectus_id": prospectus_id,
                "pdf_url": f"/api/v1/download/{pdf_filename}",
                "json_url": f"/api/v1/download/{json_filename}",
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating prospectus: {str(e)}")
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }


@router.get("/prospectus/{prospectus_id}")
async def get_prospectus(prospectus_id: str, db: Session = Depends(get_db)):
    """
    Get prospectus details by ID.
    """
    try:
        prospectus = db.query(Prospectus).filter(Prospectus.id == prospectus_id).first()
        if not prospectus:
            logger.warning(f"Prospectus not found: {prospectus_id}")
            return {
                "status": "error",
                "data": {
                    "error": "Prospectus not found"
                }
            }
        
        return {
            "status": "success",
            "data": {
                "prospectus_id": prospectus_id,
                "zone": prospectus.zone,
                "user_id": prospectus.user_id,
                "pdf_url": prospectus.pdf_url,
                "json_url": prospectus.json_url,
                "created_at": prospectus.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching prospectus: {str(e)}")
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download prospectus file (PDF or JSON).
    
    Returns the file from the prospectuses directory.
    """
    try:
        file_path = PROSPECTUS_DIR / filename
        
        if not file_path.exists():
            logger.warning(f"File not found: {filename}")
            return {
                "status": "error",
                "data": {
                    "error": "File not found"
                }
            }
        
        logger.info(f"Serving file: {file_path}")
        
        # Determine media type based on file extension
        if filename.endswith('.pdf'):
            media_type = 'application/pdf'
        elif filename.endswith('.json'):
            media_type = 'application/json'
        else:
            media_type = 'application/octet-stream'
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }
