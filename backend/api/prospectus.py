"""
Prospectus endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
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
from backend.schemas.requests import ProspectusRequest
from backend.utils.signal_normalizer import normalize_signal_text
from backend.utils.cluster_utils import build_cluster_summary
from core.prospectus.prospectus_generator import ProspectusGenerator
from core.lumoza.lumoza_engine import LumozaEngine
from core.lundai.lundai_engine import LundaiEngine, evaluate_signal_integrity
from core.zentari.zentari_engine import ZentariEngine
from policy import compute_planning_reserve

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Ensure prospectus directory exists
PROSPECTUS_DIR = Path("prospectuses")
os.makedirs(PROSPECTUS_DIR, exist_ok=True)


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
                "success": False,
                "message": "Insufficient coordination activity to generate a report."
            }
        
        signal_data = []
        for signal in signals:
            normalized = normalize_signal_text(signal.original_text)
            signal_data.append({
                "zone": normalized.get('zone', signal.zone),
                "activity_type": normalized.get('activity_type') or signal.activity_type,
                "time_window": normalized.get('time_window') or signal.time_window,
                "location": normalized.get('location', 'Local area'),
                "crop": normalized.get('crop', ''),
                "cluster_id": normalized.get('cluster_id'),
                "timestamp": signal.timestamp.isoformat(),
                "signal_source": signal.source,
                "user_phone": signal.user_id,
                "service_priority": "productive",
                "original_text": signal.original_text or ''
            })
        
        # Add cycle_index to each signal
        for i, signal in enumerate(signal_data):
            signal["cycle_index"] = i
        
        # Run full coordination pipeline: LUMOZA → LUNDAI → ZENTARI
        logger.info("Running LUMOZA engine for pattern detection...")
        lumoza = LumozaEngine()
        coordination_patterns = lumoza.process_signals(signal_data)
        logger.info(f"LUMOZA generated {len(coordination_patterns)} coordination patterns")
        
        if not coordination_patterns:
            logger.warning(f"No coordination patterns detected for zone {zone}")
            return {
                "success": False,
                "message": "Insufficient coordination activity to generate a report."
            }
        
        # Run LUNDAI engine for integrity evaluation
        logger.info("Running LUNDAI engine for integrity evaluation...")
        integrity_results = evaluate_signal_integrity(signal_data, integrity_threshold=0.4)
        logger.info(f"LUNDAI evaluated {len(integrity_results)} activity-zone groups")
        
        # Merge integrity scores into coordination patterns using activity-zone matching
        patterns_by_group = {}
        for pattern in coordination_patterns:
            group_key = (pattern['activity_type'], pattern['zone'])
            patterns_by_group.setdefault(group_key, []).append(pattern)

        for integrity_result in integrity_results:
            group_key = (integrity_result.get('activity'), integrity_result.get('zone'))
            for pattern in patterns_by_group.get(group_key, []):
                # Coerce numeric fields to safe types
                try:
                    integrity_score = float(integrity_result.get('integrity_score') or 0.0)
                except Exception:
                    integrity_score = 0.0

                try:
                    signal_count = int(integrity_result.get('signal_count') or 0)
                except Exception:
                    signal_count = 0

                try:
                    unique_days = int(integrity_result.get('unique_days') or 0)
                except Exception:
                    unique_days = 0

                try:
                    unique_senders = int(integrity_result.get('unique_senders') or 0)
                except Exception:
                    unique_senders = 0

                pattern['integrity_score'] = integrity_score
                pattern['alignment_level'] = integrity_result.get('classification')
                pattern['signal_count'] = signal_count
                pattern['validated_signals'] = signal_count
                pattern['unique_days'] = unique_days
                pattern['unique_senders'] = unique_senders
                # burst_ratio may be fractional
                try:
                    pattern['burst_ratio'] = float(integrity_result.get('burst_ratio')) if integrity_result.get('burst_ratio') is not None else None
                except Exception:
                    pattern['burst_ratio'] = None
                pattern['anomaly_flag'] = bool(integrity_result.get('anomaly_flag'))
        
        # Run LUNDAI engine for settlement context analysis
        logger.info("Running LUNDAI engine for settlement context...")
        lundai = LundaiEngine()
        planning_reserve = compute_planning_reserve(len(coordination_patterns))
        lundai_analysis = lundai.analyze_settlement_context(coordination_patterns, planning_reserve)
        logger.info(f"LUNDAI completed settlement context analysis")
        
        # Extract flow graph from LUNDAI analysis
        flow_graph = lundai_analysis.get('flow_graph', {})
        logger.info(f"Flow graph contains {flow_graph.get('total_nodes', 0)} nodes and {flow_graph.get('total_edges', 0)} edges")
        
        # Run ZENTARI engine for coordination confidence evaluation
        logger.info("Running ZENTARI engine for coordination confidence...")
        zentari = ZentariEngine()
        confidence_results = zentari.evaluate_coordination_confidence(coordination_patterns, planning_reserve, flow_graph=flow_graph)
        logger.info(f"ZENTARI evaluated {len(confidence_results)} patterns for coordination confidence")

        if not confidence_results:
            logger.warning(f"ZENTARI produced no confidence results for zone {zone}")
            return {
                "success": False,
                "message": "Insufficient coordination activity to generate a report."
            }

        # Only generate a prospectus when bankable coordination patterns exist
        bankable_patterns = [
            pattern for pattern in confidence_results
            if pattern.get("confidence_class") in ("high", "moderate")
            and pattern.get("trust", {}).get("action_allowed") is True
        ]

        if not bankable_patterns:
            logger.warning(f"No bankable coordination patterns found for zone {zone}")
            return {
                "success": False,
                "message": "Insufficient coordination activity to generate a report."
            }

        # Generate prospectus using full pipeline output
        logger.info("Generating prospectus from full pipeline output...")
        gen = ProspectusGenerator()
        metadata = {
            "region": zone_key,
            "period": "7-cycle window (1 week)",
            "is_sample": False
        }
        
        cluster_summary = build_cluster_summary(signal_data)
        prospectus = gen.generate_prospectus(
            confidence_results,
            lundai_analysis=lundai_analysis,
            metadata=metadata,
            planning_reserve=planning_reserve,
            clusters=cluster_summary,
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
            "success": True,
            "report": {
                "prospectus_id": prospectus_id,
                "pdf_url": f"/api/v1/download/{pdf_filename}",
                "json_url": f"/api/v1/download/{json_filename}",
                "generated_at": datetime.utcnow().isoformat()
            },
            "pdf_url": f"/api/v1/download/{pdf_filename}"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating prospectus: {str(e)}")
        return {
            "success": False,
            "message": str(e)
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
                "success": False,
                "status": "error",
                "data": {
                    "error": "Prospectus not found"
                }
            }
        
        return {
            "success": True,
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
            "success": False,
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
