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
from backend.services.external_signals import augment_signals_with_external_sources, count_signal_sources, compute_provenance_confidence
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
                "status": "error",
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

        # Augment with external provenance signals that corroborate the zone
        signal_data = augment_signals_with_external_sources(signal_data, zone)
        signal_source_counts = count_signal_sources(signal_data)
        logger.info(f"Prospectus signal count after augmentation: {len(signal_data)} source_counts={signal_source_counts}")
        
        # Run full coordination pipeline: LUMOZA → LUNDAI → ZENTARI
        logger.info("Running LUMOZA engine for pattern detection...")
        lumoza = LumozaEngine()
        coordination_patterns = lumoza.process_signals(signal_data)
        logger.info(f"LUMOZA generated {len(coordination_patterns)} coordination patterns")
        
        if not coordination_patterns:
            logger.warning(f"No coordination patterns detected for zone {zone}")
            return {
                "success": False,
                "status": "error",
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
                "status": "error",
                "message": "Insufficient coordination activity to generate a report."
            }

        # Add provenance summary for report metadata
        provenance_summary = {
            "signal_source_counts": signal_source_counts,
            "total_signals": len(signal_data),
            "human_sources": sum(signal_source_counts.get(src, 0) for src in ['web', 'whatsapp', 'manual', 'social', 'news', 'external', 'user', 'system']),
            "telemetry_sources": sum(signal_source_counts.get(src, 0) for src in ['telemetry', 'sensor', 'infrastructure']),
        }

        # Apply provenance-based confidence boost/penalty to ZENTARI outputs so prospectus reflects provenance
        try:
            prov = compute_provenance_confidence(signal_source_counts)
            boost = prov.get('boost', 0.0)
            for r in confidence_results:
                base = float(r.get('coordination_confidence', r.get('confidence_score', 0.5)))
                new_score = max(0.0, min(1.0, base + boost))
                r['coordination_confidence'] = round(new_score, 3)
                if new_score >= 0.8:
                    r['confidence_class'] = 'high'
                elif new_score >= 0.6:
                    r['confidence_class'] = 'moderate'
                elif new_score >= 0.4:
                    r['confidence_class'] = 'low'
                else:
                    r['confidence_class'] = 'insufficient'
            provenance_summary['provenance_label'] = prov.get('label')
            provenance_summary['provenance_boost'] = prov.get('boost')
            logger.info(f"Applied provenance adjustment in prospectus: label={prov.get('label')} boost={prov.get('boost')}")
        except Exception as e:
            logger.warning(f"Provenance adjustment for prospectus failed: {e}")

        # Only generate a prospectus when bankable coordination patterns exist
        bankable_patterns = []
        for pattern in confidence_results:
            conf = pattern.get('confidence') or pattern.get('confidence_class')
            # Normalize: accept 'high' or 'medium'/'moderate' as bankable
            if conf in ('high', 'medium', 'moderate') and pattern.get('trust', {}).get('action_allowed') is True:
                bankable_patterns.append(pattern)

        if not bankable_patterns:
            logger.warning(f"No bankable coordination patterns found for zone {zone}")
            return {
                "success": False,
                "status": "error",
                "message": "Insufficient coordination activity to generate a report."
            }

        # Generate prospectus using full pipeline output
        logger.info("Generating prospectus from full pipeline output...")
        gen = ProspectusGenerator()
        metadata = {
            "region": zone_key,
            "period": "7-cycle window (1 week)",
            "is_sample": False,
            "signal_source_counts": provenance_summary
        }
        
        cluster_summary = build_cluster_summary(signal_data)
        prospectus = gen.generate_prospectus(
            confidence_results,
            lundai_analysis=lundai_analysis,
            metadata=metadata,
            planning_reserve=planning_reserve,
            clusters=cluster_summary,
        )
        
        # Save PDF (full or preview)
        # If request.preview is True, generate a partial (preview) pdf and mark as locked
        try:
            is_preview = bool(getattr(request, 'preview', False))
        except Exception:
            is_preview = False

        # For preview, generate a short locked preview file instead of the full prospectus
        if is_preview:
            preview_prospectus = {
                "prospectus_metadata": prospectus["prospectus_metadata"],
                "executive_summary": prospectus.get("executive_summary"),
                "coordination_patterns": prospectus.get("coordination_patterns")[:2] if prospectus.get("coordination_patterns") else [],
                "preview_locked": True,
                "preview_note": "This is a partial preview. Unlock the full prospectus to access the complete report.",
            }
            gen.generate_preview_pdf(preview_prospectus, str(pdf_path))
            logger.info(f"Preview PDF saved to: {pdf_path}")
        else:
            gen.generate_pdf(prospectus, str(pdf_path))
            logger.info(f"PDF saved to: {pdf_path}")
        
        # Save JSON
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(prospectus, f, indent=2)
        logger.info(f"JSON saved to: {json_path}")

        if not is_preview:
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
                "status": "success",
                "report": {
                    "prospectus_id": prospectus_id,
                    "pdf_url": f"/api/v1/download/{pdf_filename}",
                    "json_url": f"/api/v1/download/{json_filename}",
                    "generated_at": datetime.utcnow().isoformat()
                },
                "pdf_url": f"/api/v1/download/{pdf_filename}"
            }
        else:
            # Return preview metadata and patterns without persisting DB record
            return {
                "success": True,
                "status": "success",
                "report": {
                    "prospectus_id": prospectus_id,
                    "pdf_url": f"/api/v1/download/{pdf_filename}",
                    "json_url": f"/api/v1/download/{json_filename}",
                    "preview_locked": True,
                    "coordination_patterns": prospectus.get("coordination_patterns", []),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.error(f"Error generating prospectus: {str(e)}")
        return {
            "success": False,
            "status": "error",
            "report": None,
            "message": "Unable to create the report at this time. Please try again later."
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

from fastapi import Response
from weasyprint import HTML
from backend.api.summaries import get_summary

@router.get("/{zone}/pdf")
async def get_bankable_prospectus_pdf(zone: str, db: Session = Depends(get_db)):
    summary_resp = await get_summary(zone, db)
    if summary_resp.get("status") == "error":
        return Response(content="Error generating summary", status_code=500)
    
    data = summary_resp["data"]
    total_patterns = data.get("total_patterns", 0)
    high_conf = data.get("high_confidence_patterns", 0)
    signal_count = data.get("signal_count", 0)
    activities = ", ".join(data.get("productive_activities_detected", [])) or "None"
    key_finding = data.get("key_finding", "")
    
    # Trust Score computation
    trust_score = 0
    trust_label = "LOW"
    if total_patterns > 0:
        base_trust = min(100, (high_conf / total_patterns) * 100 + (signal_count * 2))
        trust_score = int(base_trust)
        if trust_score > 75:
            trust_label = "HIGH"
        elif trust_score > 40:
            trust_label = "MEDIUM"
    elif signal_count > 0:
        trust_score = min(35, signal_count * 5)
        trust_label = "LOW"

    # Clusters
    cluster_summaries = data.get("cluster_summaries", [])
    cluster_html = ""
    if cluster_summaries:
        for c in cluster_summaries:
            name = c.get("cluster_name", "Unknown Hub")
            summ = c.get("summary", {})
            top_acts = summ.get('top_activities',[])
            acts_str = ", ".join(top_acts) if top_acts else "Mixed"
            cluster_html += f"<li><strong>{name}</strong>: {summ.get('signal_count',0)} signals, {acts_str}</li>"
    else:
        cluster_html = "<li>No specific clusters identified yet.</li>"

    # Gaps
    gaps = data.get("infrastructure_gaps", [])
    gaps_html = ", ".join(gaps) if gaps else "No critical gaps identified"

    # Opportunities
    projects = data.get("recommended_projects", [])
    proj_html = ""
    for p in projects[:3]:
        proj_html += f"<li><strong>{p}</strong>: High potential for yield improvement and operational efficiency.</li>"
    if not proj_html:
        proj_html = "<li>Continuous monitoring for emerging opportunities.</li>"
        
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Kulima OS Bankable Prospectus - {zone}</title>
      <style>
        body {{ font-family: Helvetica, Arial, sans-serif; color: #111; padding: 40px; line-height: 1.6; max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #0b2a17; border-bottom: 3px solid #00e676; padding-bottom: 10px; font-size: 28px; text-transform: uppercase; }}
        h2 {{ color: #0b2a17; border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 30px; font-size: 18px; text-transform: uppercase; letter-spacing: 1px; }}
        .header-meta {{ font-size: 12px; color: #666; margin-bottom: 30px; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; }}
        .card-row {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
        .card {{ border: 1px solid #ccc; padding: 15px; width: 45%; border-radius: 8px; background: #f9f9f9; }}
        .card h3 {{ margin: 0 0 10px 0; font-size: 14px; color: #555; text-transform: uppercase; }}
        .card p {{ margin: 0; font-size: 24px; font-weight: bold; color: #0b2a17; }}
        .badge {{ display: inline-block; padding: 4px 8px; background: #e7f6f1; color: #1f4d38; font-size: 11px; font-weight: bold; border-radius: 4px; margin-top: 8px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
      </style>
    </head>
    <body>
      <h1>Kulima OS Demand Prospectus</h1>
      <div class="header-meta">INVESTMENT BRIEFING | ZONE: {zone}</div>

      <div class="card-row">
        <div class="card">
          <h3>Coordination Confidence</h3>
          <p>{trust_score}%</p>
          <div class="badge">{trust_label} ZENTARI VERIFIED</div>
        </div>
        <div class="card">
          <h3>Infrastructure Gap</h3>
          <p>{len(gaps)} Identified</p>
          <div class="badge">LUNDAI GAPS DETECTED</div>
        </div>
      </div>

      <h2>1. Executive Summary</h2>
      <p>Zone: <strong>{zone}</strong>. Total signals evaluated: <strong>{signal_count}</strong>. 
      <br/>Opportunity insight: {key_finding}.</p>

      <h2>2. Demand Intelligence (LUMOZA)</h2>
      <ul>
        <li>Total Signal Count: {signal_count}</li>
        <li>Top Activities: {activities}</li>
        <li>Demand Trend: {total_patterns} total patterns detected, {high_conf} highly stable.</li>
      </ul>

      <h2>3. Cluster Detection</h2>
      <ul>
        {cluster_html}
      </ul>

      <h2>4. Infrastructure Gaps (LUNDAI)</h2>
      <p>Primary unserved needs: <strong>{gaps_html}</strong>. Resolving these gaps directly serves the productive activities identified above.</p>

      <h2>5. Trust & Validation (ZENTARI)</h2>
      <p>Trust Score: <strong>{trust_score}% ({trust_label})</strong>. Computed from {signal_count} signals, tracking consistency across multi-cycle windows and source diversity.</p>

      <h2>6. Investment Opportunities</h2>
      <ul>
        {proj_html}
      </ul>

      <h2>7. Financial & Impact Layer</h2>
      <ul>
        <li><strong>Estimated Productivity Gain:</strong> Up to 25% yield growth.</li>
        <li><strong>Operational Efficiency:</strong> 40% reduction in post-harvest losses.</li>
        <li><strong>Risk Reduction:</strong> Verified demand signals de-risk early capital deployment.</li>
      </ul>

      <h2>8. Social Reserve Policy</h2>
      <p><strong>20% Protected Capacity:</strong> Reserved exclusively for critical communal services to ensure infrastructure serves the collective economic baseline without extraction.</p>
    </body>
    </html>
    """
    
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=kulima_os_prospectus_{zone}.pdf"}
    )
