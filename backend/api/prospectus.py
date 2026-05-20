"""
Prospectus endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from datetime import datetime
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal, Prospectus
from core.prospectus.prospectus_generator import ProspectusGenerator
from core.lumoza.lumoza_integration import integrate_whatsapp_to_lumoza
from streamlit_app import generate_sample_patterns
from policy import compute_planning_reserve
from patterns_to_confidence_results import patterns_to_confidence_results

router = APIRouter()

PROSPECTUS_DIR = Path("prospectuses")
PROSPECTUS_DIR.mkdir(exist_ok=True)


@router.post("/generate-prospectus")
async def generate_prospectus(request: dict, db: Session = Depends(get_db)):
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
      "prospectus_id": "pros_abc123",
      "pdf_url": "/api/v1/download/prospectus_mzuzu_2026-05-20.pdf",
      "json_url": "/api/v1/download/prospectus_mzuzu_2026-05-20.json",
      "generated_at": "2026-05-20T10:00:00Z"
    }
    """
    try:
        zone = request.get("zone")
        user_id = request.get("user_id")
        
        if not zone:
            raise HTTPException(status_code=400, detail="Zone is required")
        
        print(f"Generating prospectus for zone: {zone}")
        
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
        print(f"Found {len(signals)} signals for zone {zone}")
        
        # Generate patterns using core engines
        if signals:
            signal_data = []
            for signal in signals:
                signal_data.append({
                    "zone": signal.zone,
                    "activity_type": signal.activity_type,
                    "time_window": signal.time_window,
                    "timestamp": signal.timestamp.isoformat(),
                    "source": signal.source
                })
            
            from core.lumoza.lumoza_engine import LumozaEngine
            from core.lundai.lundai_engine import LundaiEngine
            from core.zentari.zentari_engine import ZentariEngine
            
            lumoza = LumozaEngine()
            patterns = lumoza.process_signals(signal_data)
            print(f"LUMOZA generated {len(patterns)} patterns")
            
            lundai = LundaiEngine()
            planning_reserve = compute_planning_reserve(len(patterns))
            lundai_analysis = lundai.analyze_settlement_context(patterns, planning_reserve=planning_reserve)
            
            zentari = ZentariEngine()
            confidence_results = zentari.evaluate_coordination_confidence(patterns, planning_reserve=planning_reserve)
        else:
            # Use sample patterns if no signals
            patterns = generate_sample_patterns(zone_key)
            lundai_analysis = {
                "overall_assessment": {
                    "total_zones_analyzed": 1,
                    "critical_infrastructure_gaps": 1,
                    "urgent_priority_zones": 1,
                    "average_infrastructure_adequacy_score": 45,
                    "overall_infrastructure_status": "underserved"
                },
                "zone_analyses": {
                    zone_key: {
                        "settlement_type": "rural_agricultural",
                        "infrastructure_status": "underserved",
                        "essential_services_count": 2,
                        "productive_activity_count": 3,
                        "grid_edge_exposure": True
                    }
                }
            }
            confidence_results = patterns_to_confidence_results(patterns)
            planning_reserve = compute_planning_reserve(len(patterns))
        
        # Generate prospectus using ProspectusGenerator
        gen = ProspectusGenerator()
        metadata = {
            "region": zone_key,
            "period": "7-cycle window (1 week)",
            "is_sample": len(signals) == 0
        }
        
        prospectus = gen.generate_prospectus(
            confidence_results,
            lundai_analysis=lundai_analysis,
            metadata=metadata,
            planning_reserve=planning_reserve,
        )
        
        # Save PDF
        gen.generate_pdf(prospectus, str(pdf_path))
        print(f"PDF saved to: {pdf_path}")
        
        # Save JSON
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(prospectus, f, indent=2)
        print(f"JSON saved to: {json_path}")
        
        # Store prospectus in database
        db_prospectus = Prospectus(
            id=prospectus_id,
            zone=zone_key,
            user_id=user_id or "unknown",
            pdf_url=f"/api/v1/download/{pdf_filename}",
            json_url=f"/api/v1/download/{json_filename}",
            meta_data=json.dumps(metadata),
        )
        db.add(db_prospectus)
        db.commit()
        
        print(f"Prospectus stored in database: {prospectus_id}")
        
        return {
            "status": "success",
            "prospectus_id": prospectus_id,
            "pdf_url": f"/api/v1/download/{pdf_filename}",
            "json_url": f"/api/v1/download/{json_filename}",
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        db.rollback()
        print(f"Error generating prospectus: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prospectus/{prospectus_id}")
async def get_prospectus(prospectus_id: str, db: Session = Depends(get_db)):
    """
    Get prospectus details by ID.
    """
    try:
        prospectus = db.query(Prospectus).filter(Prospectus.id == prospectus_id).first()
        if not prospectus:
            raise HTTPException(status_code=404, detail="Prospectus not found")
        
        return {
            "prospectus_id": prospectus_id,
            "status": "found",
            "zone": prospectus.zone,
            "user_id": prospectus.user_id,
            "pdf_url": prospectus.pdf_url,
            "json_url": prospectus.json_url,
            "created_at": prospectus.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download prospectus file (PDF or JSON).
    
    Returns the file from the prospectuses directory.
    """
    try:
        file_path = PROSPECTUS_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        print(f"Serving file: {file_path}")
        
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
