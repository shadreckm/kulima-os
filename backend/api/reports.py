"""
Report Export & Distribution API for Kulima OS.

Provides endpoints for:
  - PDF export (download)
  - PDF sharing (public URL generation)
  - JSON fallback export

All file paths are sanitized. No PII is exposed.
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import Signal
from core.dpi_pipeline import KulimaDPIPipeline
from core.report_engine import ReportEngine, REPORTS_DIR

logger = logging.getLogger(__name__)

router = APIRouter()

# TODO(security): In production, serve files through a CDN or object store
# with signed URLs instead of directly from the filesystem.


class ExportRequest(BaseModel):
    zone: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    signals: list = Field(default_factory=list)


class ShareResponse(BaseModel):
    public_url: str
    share_ready: bool
    report_id: str
    file_name: str


# Input validation helper
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_\-\.]+$")


def _validate_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Strip path components — only use the basename
    basename = os.path.basename(filename)
    if not _SAFE_FILENAME_RE.match(basename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return basename


# -------------------------------------------------------------------
# SIMPLE REPORT ENDPOINT
# -------------------------------------------------------------------

@router.get("/report")
async def get_report(zone: str = "MZUZU", db: Session = Depends(get_db)):
    """Return a simple structured report for the requested zone using stored signals."""
    zone_upper = (zone or "MZUZU").upper()
    signals = db.query(Signal).filter(Signal.zone == zone_upper).order_by(Signal.timestamp.desc()).all()

    if not signals:
        return {
            "status": "success",
            "data": {
                "zone": zone_upper,
                "summary": {
                    "signal_count": 0,
                    "dominant_activity": "unknown",
                    "confidence_score": 0.0,
                    "message": "No activity yet — submit a signal to activate analysis"
                },
                "signals": [],
                "clusters": [],
                "gaps": ["Irrigation demand monitoring", "Cold storage support", "Community energy access"],
                "generated_at": datetime.utcnow().isoformat(),
            }
        }

    activity_counts = {}
    for signal in signals:
        activity = signal.activity_type or "unknown"
        activity_counts[activity] = activity_counts.get(activity, 0) + 1

    dominant_activity = max(activity_counts.items(), key=lambda item: item[1])[0] if activity_counts else "unknown"
    confidence_score = round(min(0.95, 0.35 + (len(signals) / 40) + (len(activity_counts) / 10)), 2)
    clusters = [
        {
            "name": activity,
            "signal_count": count,
            "gap": "Needs more coverage" if count < 2 else "Demand is active"
        }
        for activity, count in sorted(activity_counts.items(), key=lambda item: item[1], reverse=True)
    ]

    gaps = []
    for activity in ["irrigation", "milling", "cold storage", "welding"]:
        if activity not in activity_counts:
            gaps.append(f"{activity.title()} demand monitoring")

    return {
        "status": "success",
        "data": {
            "zone": zone_upper,
            "summary": {
                "signal_count": len(signals),
                "dominant_activity": dominant_activity,
                "confidence_score": confidence_score,
                "message": "Signals are forming into a clear demand pattern"
            },
            "signals": [
                {
                    "id": signal.id,
                    "activity_type": signal.activity_type,
                    "zone": signal.zone,
                    "time_window": signal.time_window,
                    "timestamp": signal.timestamp.isoformat(),
                    "source": signal.source,
                }
                for signal in signals
            ],
            "clusters": clusters,
            "gaps": gaps or ["Community capacity monitoring"],
            "generated_at": datetime.utcnow().isoformat(),
        }
    }


@router.get("/reports")
async def get_reports(zone: str = "MZUZU", db: Session = Depends(get_db)):
    """Compatibility alias for clients requesting /reports instead of /report."""
    return await get_report(zone=zone, db=db)


# -------------------------------------------------------------------
# STEP 4 — EXPORT FUNCTION
# -------------------------------------------------------------------

@router.post("/reports/export")
async def export_report(request: ExportRequest):
    """
    Generate a PDF prospectus for a zone and return download metadata.

    Request body:
    {
        "zone": "MZUZU-NORTH",
        "signals": [
            {"id": "sig_1", "source_id": "farmer_A", "batch_window": "2026-W24-Morning",
             "zone": "MZUZU-NORTH", "activity_type": "irrigation"},
            ...
        ]
    }

    Returns:
    {
        "file_path": "reports/MZUZU-NORTH_prospectus_20260622-100000.pdf",
        "file_name": "MZUZU-NORTH_prospectus_20260622-100000.pdf",
        "file_size": 45231,
        "report_id": "RPT-A1B2C3D4",
        "download_url": "/api/v1/reports/download/MZUZU-NORTH_prospectus_20260622-100000.pdf"
    }
    """
    try:
        zone = request.zone.upper()

        if not request.signals:
            raise HTTPException(
                status_code=400,
                detail="At least one signal is required to generate a report."
            )

        # Run the DPI pipeline
        pipeline = KulimaDPIPipeline()
        dpi_output = pipeline.process_zone(zone, request.signals)

        # Generate the PDF
        engine = ReportEngine()
        result = engine.generate_prospectus_pdf(dpi_output)

        is_fallback = result.get("fallback", False)
        file_name = result["file_name"]

        return {
            "success": True,
            "status": "success" if not is_fallback else "fallback_json",
            "file_path": result["file_path"],
            "file_name": file_name,
            "file_size": result["file_size"],
            "report_id": result["report_id"],
            "generated_at": result["generated_at"],
            "download_url": f"/api/v1/reports/download/{file_name}",
            "fallback": is_fallback,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Report export failed: {exc}")
        raise HTTPException(status_code=500, detail="Report generation failed. Please try again.")


# -------------------------------------------------------------------
# FILE DOWNLOAD
# -------------------------------------------------------------------

@router.get("/reports/download/{filename}")
async def download_report(filename: str):
    """
    Download a generated report file (PDF or JSON fallback).
    Path traversal is prevented by basename sanitization.
    """
    safe_name = _validate_filename(filename)
    file_path = REPORTS_DIR / safe_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    # Resolve and verify directory boundary to prevent traversal
    resolved = file_path.resolve()
    reports_resolved = REPORTS_DIR.resolve()
    if not str(resolved).startswith(str(reports_resolved) + os.sep):
        raise HTTPException(status_code=403, detail="Access denied")

    if safe_name.endswith(".pdf"):
        media_type = "application/pdf"
    elif safe_name.endswith(".json"):
        media_type = "application/json"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=str(resolved),
        media_type=media_type,
        filename=safe_name,
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_name}\"",
            "X-Content-Type-Options": "nosniff",
        },
    )


# -------------------------------------------------------------------
# STEP 5 — SHARE FUNCTION
# -------------------------------------------------------------------

@router.post("/reports/share")
async def share_report(request: ExportRequest):
    """
    Generate a PDF and return a shareable public URL.

    Returns:
    {
        "public_url": "/api/v1/reports/download/MZUZU-NORTH_prospectus_20260622-100000.pdf",
        "share_ready": true,
        "report_id": "RPT-A1B2C3D4",
        "file_name": "..."
    }

    The public_url can be:
    - Opened in a browser for direct PDF viewing
    - Shared via WhatsApp, email, or any messaging platform
    - Used as an attachment link in communications
    """
    try:
        zone = request.zone.upper()

        if not request.signals:
            raise HTTPException(
                status_code=400,
                detail="At least one signal is required to generate a report."
            )

        pipeline = KulimaDPIPipeline()
        dpi_output = pipeline.process_zone(zone, request.signals)

        engine = ReportEngine()
        result = engine.generate_prospectus_pdf(dpi_output)

        file_name = result["file_name"]
        # TODO(security): In production, generate a signed, time-limited URL
        # via cloud object storage (e.g., S3 presigned URLs) instead of a
        # static file path. This prevents indefinite public access.
        public_url = f"/api/v1/reports/download/{file_name}"

        return ShareResponse(
            public_url=public_url,
            share_ready=True,
            report_id=result["report_id"],
            file_name=file_name,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Report share failed: {exc}")
        raise HTTPException(status_code=500, detail="Report sharing failed. Please try again.")


# -------------------------------------------------------------------
# INLINE PDF VIEW (for browser embedding / WhatsApp preview)
# -------------------------------------------------------------------

@router.get("/reports/view/{filename}")
async def view_report_inline(filename: str):
    """
    Serve a report PDF inline (for browser viewing rather than download).
    """
    safe_name = _validate_filename(filename)
    file_path = REPORTS_DIR / safe_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    resolved = file_path.resolve()
    reports_resolved = REPORTS_DIR.resolve()
    if not str(resolved).startswith(str(reports_resolved) + os.sep):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=str(resolved),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{safe_name}\"",
            "X-Content-Type-Options": "nosniff",
        },
    )
