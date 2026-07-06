"""
Evidence API Endpoints
Handles evidence upload, retrieval, and management
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime
import uuid
import logging

from backend.database.connection import get_db
from backend.database.evidence_models import Evidence, EvidenceTrustFactors, EvidenceLink, EvidenceAuditLog
from backend.utils.evidence_processor import EvidenceProcessor, TrustScoreCalculator
from backend.services.evidence_storage import get_storage_service
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


# Allowed file types and sizes
ALLOWED_PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
ALLOWED_DOCUMENT_TYPES = ['application/pdf']
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/evidence/upload/photo")
async def upload_photo_evidence(
    file: UploadFile = File(...),
    zone: str = Form(...),
    signal_id: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    source_type: Optional[str] = Form("community"),
    db: Session = Depends(get_db)
):
    """
    Upload photo evidence
    
    Zero-PII Compliance:
    - No personal identifiers accepted
    - GPS coordinates filtered to zone level only
    - EXIF data sanitized
    - No facial recognition
    
    Args:
        file: Photo file (JPEG/PNG, max 10MB)
        zone: Zone identifier (required)
        signal_id: Optional signal to link evidence to
        category: Optional category (crop_damage, infrastructure, etc.)
        source_type: Source type (extension_officer, cooperative, community, etc.)
    
    Returns:
        Evidence metadata with trust score
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_PHOTO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_PHOTO_TYPES)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > MAX_PHOTO_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_PHOTO_SIZE / 1024 / 1024}MB"
            )
        
        # Generate evidence ID
        evidence_id = str(uuid.uuid4())
        
        # Calculate file hash for duplicate detection
        file_hash = EvidenceProcessor.calculate_file_hash(file_content)
        
        # Check for duplicates
        existing_evidence = db.query(Evidence).filter(Evidence.file_hash == file_hash).first()
        if existing_evidence:
            logger.warning(f"Duplicate evidence detected: {file_hash}")
            # Return existing evidence instead of creating duplicate
            return {
                "id": existing_evidence.id,
                "status": "duplicate",
                "message": "This evidence already exists in the system",
                "existing_evidence_id": existing_evidence.id
            }
        
        # Extract metadata (PII-filtered)
        metadata = EvidenceProcessor.extract_photo_metadata(file_content, file.filename or "photo.jpg")
        
        # Get existing hashes for duplicate scoring
        existing_hashes = [e.file_hash for e in db.query(Evidence.file_hash).all() if e.file_hash]
        
        # Calculate trust score
        factors, trust_score, classification = TrustScoreCalculator.calculate_trust_score(
            metadata=metadata,
            source_type=source_type,
            file_hash=file_hash,
            existing_hashes=existing_hashes,
            zone=zone,
            evidence_type='photo',
            category=category,
            similar_evidence_count=0  # Future: Query similar evidence
        )
        
        # Save file to storage
        storage_service = get_storage_service()
        file_extension = file.filename.split('.')[-1] if file.filename and '.' in file.filename else 'jpg'
        file_url, storage_path = storage_service.save_file(file_content, evidence_id, file_extension)
        
        # Generate thumbnail
        thumbnail_result = storage_service.generate_thumbnail(file_content, evidence_id)
        thumbnail_url = thumbnail_result[0] if thumbnail_result else None
        
        # Create evidence record
        evidence = Evidence(
            id=evidence_id,
            signal_id=signal_id,
            zone=zone,
            evidence_type='photo',
            category=category,
            file_url=file_url,
            thumbnail_url=thumbnail_url,
            file_size=len(file_content),
            file_hash=file_hash,
            trust_score=trust_score,
            trust_classification=classification,
            metadata=metadata,
            captured_at=datetime.fromisoformat(metadata['captured_at']) if 'captured_at' in metadata else None,
            source_type=source_type,
            status='active'
        )
        
        db.add(evidence)
        
        # Create trust factors record
        trust_factors = EvidenceTrustFactors(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            timestamp_validity=factors['timestamp_validity'],
            source_reputation=factors['source_reputation'],
            duplicate_detection=factors['duplicate_detection'],
            metadata_consistency=factors['metadata_consistency'],
            geographical_consistency=factors['geographical_consistency'],
            visual_relevance=factors['visual_relevance'],
            cross_source_verification=factors['cross_source_verification'],
            composite_score=trust_score / 100.0
        )
        
        db.add(trust_factors)
        
        # Create evidence link if signal_id provided
        if signal_id:
            link = EvidenceLink(
                id=str(uuid.uuid4()),
                evidence_id=evidence_id,
                linked_entity_type='signal',
                linked_entity_id=signal_id,
                link_type='supports'
            )
            db.add(link)
        
        # Create audit log
        audit_log = EvidenceAuditLog(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            action='upload',
            actor_type='api'
        )
        db.add(audit_log)
        
        db.commit()
        
        logger.info(f"Photo evidence uploaded: {evidence_id} (trust: {trust_score})")
        
        return {
            "id": evidence_id,
            "status": "success",
            "evidence_type": "photo",
            "zone": zone,
            "trust_score": trust_score,
            "trust_classification": classification,
            "file_url": file_url,
            "thumbnail_url": thumbnail_url,
            "metadata": {
                "file_size": len(file_content),
                "format": metadata.get('format'),
                "captured_at": metadata.get('captured_at')
            },
            "trust_factors": factors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading photo evidence: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading evidence: {str(e)}")


@router.post("/evidence/upload/document")
async def upload_document_evidence(
    file: UploadFile = File(...),
    zone: str = Form(...),
    signal_id: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    source_type: Optional[str] = Form("extension_officer"),
    db: Session = Depends(get_db)
):
    """
    Upload document evidence (PDF)
    
    Zero-PII Compliance:
    - No personal identifiers accepted
    - Document metadata sanitized
    - Author/creator information filtered
    
    Args:
        file: PDF file (max 5MB)
        zone: Zone identifier (required)
        signal_id: Optional signal to link evidence to
        category: Optional category
        source_type: Source type (extension_officer, cooperative, etc.)
    
    Returns:
        Evidence metadata with trust score
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_DOCUMENT_TYPES)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > MAX_DOCUMENT_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_DOCUMENT_SIZE / 1024 / 1024}MB"
            )
        
        # Generate evidence ID
        evidence_id = str(uuid.uuid4())
        
        # Calculate file hash
        file_hash = EvidenceProcessor.calculate_file_hash(file_content)
        
        # Check for duplicates
        existing_evidence = db.query(Evidence).filter(Evidence.file_hash == file_hash).first()
        if existing_evidence:
            return {
                "id": existing_evidence.id,
                "status": "duplicate",
                "message": "This document already exists in the system",
                "existing_evidence_id": existing_evidence.id
            }
        
        # Extract metadata
        metadata = EvidenceProcessor.extract_pdf_metadata(file_content, file.filename or "document.pdf")
        
        # Get existing hashes
        existing_hashes = [e.file_hash for e in db.query(Evidence.file_hash).all() if e.file_hash]
        
        # Calculate trust score
        factors, trust_score, classification = TrustScoreCalculator.calculate_trust_score(
            metadata=metadata,
            source_type=source_type,
            file_hash=file_hash,
            existing_hashes=existing_hashes,
            zone=zone,
            evidence_type='pdf',
            category=category,
            similar_evidence_count=0
        )
        
        # Save file
        storage_service = get_storage_service()
        file_url, storage_path = storage_service.save_file(file_content, evidence_id, 'pdf')
        
        # Create evidence record
        evidence = Evidence(
            id=evidence_id,
            signal_id=signal_id,
            zone=zone,
            evidence_type='pdf',
            category=category,
            file_url=file_url,
            file_size=len(file_content),
            file_hash=file_hash,
            trust_score=trust_score,
            trust_classification=classification,
            metadata=metadata,
            captured_at=datetime.fromisoformat(metadata['captured_at']) if 'captured_at' in metadata else None,
            source_type=source_type,
            status='active'
        )
        
        db.add(evidence)
        
        # Create trust factors record
        trust_factors = EvidenceTrustFactors(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            timestamp_validity=factors['timestamp_validity'],
            source_reputation=factors['source_reputation'],
            duplicate_detection=factors['duplicate_detection'],
            metadata_consistency=factors['metadata_consistency'],
            geographical_consistency=factors['geographical_consistency'],
            visual_relevance=factors['visual_relevance'],
            cross_source_verification=factors['cross_source_verification'],
            composite_score=trust_score / 100.0
        )
        
        db.add(trust_factors)
        
        # Create evidence link if signal_id provided
        if signal_id:
            link = EvidenceLink(
                id=str(uuid.uuid4()),
                evidence_id=evidence_id,
                linked_entity_type='signal',
                linked_entity_id=signal_id,
                link_type='supports'
            )
            db.add(link)
        
        # Create audit log
        audit_log = EvidenceAuditLog(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            action='upload',
            actor_type='api'
        )
        db.add(audit_log)
        
        db.commit()
        
        logger.info(f"Document evidence uploaded: {evidence_id} (trust: {trust_score})")
        
        return {
            "id": evidence_id,
            "status": "success",
            "evidence_type": "pdf",
            "zone": zone,
            "trust_score": trust_score,
            "trust_classification": classification,
            "file_url": file_url,
            "metadata": {
                "file_size": len(file_content),
                "num_pages": metadata.get('num_pages'),
                "captured_at": metadata.get('captured_at')
            },
            "trust_factors": factors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document evidence: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading evidence: {str(e)}")


@router.get("/evidence/{evidence_id}")
async def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    """
    Get evidence by ID
    
    Returns:
        Evidence details with trust factors
    """
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    # Get trust factors
    trust_factors = db.query(EvidenceTrustFactors).filter(
        EvidenceTrustFactors.evidence_id == evidence_id
    ).first()
    
    # Get links
    links = db.query(EvidenceLink).filter(EvidenceLink.evidence_id == evidence_id).all()
    
    # Create audit log
    audit_log = EvidenceAuditLog(
        id=str(uuid.uuid4()),
        evidence_id=evidence_id,
        action='view',
        actor_type='api'
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "id": evidence.id,
        "zone": evidence.zone,
        "evidence_type": evidence.evidence_type,
        "category": evidence.category,
        "file_url": evidence.file_url,
        "thumbnail_url": evidence.thumbnail_url,
        "file_size": evidence.file_size,
        "trust_score": evidence.trust_score,
        "trust_classification": evidence.trust_classification,
        "metadata": evidence.metadata,
        "source_type": evidence.source_type,
        "captured_at": evidence.captured_at.isoformat() if evidence.captured_at else None,
        "uploaded_at": evidence.uploaded_at.isoformat(),
        "status": evidence.status,
        "trust_factors": {
            "timestamp_validity": trust_factors.timestamp_validity if trust_factors else 0,
            "source_reputation": trust_factors.source_reputation if trust_factors else 0,
            "duplicate_detection": trust_factors.duplicate_detection if trust_factors else 0,
            "metadata_consistency": trust_factors.metadata_consistency if trust_factors else 0,
            "geographical_consistency": trust_factors.geographical_consistency if trust_factors else 0,
            "visual_relevance": trust_factors.visual_relevance if trust_factors else 0,
            "cross_source_verification": trust_factors.cross_source_verification if trust_factors else 0
        } if trust_factors else None,
        "links": [
            {
                "entity_type": link.linked_entity_type,
                "entity_id": link.linked_entity_id,
                "link_type": link.link_type
            }
            for link in links
        ]
    }


@router.get("/evidence/signal/{signal_id}")
async def get_evidence_by_signal(
    signal_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100)
):
    """
    Get all evidence linked to a signal
    
    Returns:
        List of evidence items
    """
    evidence_list = db.query(Evidence).filter(
        Evidence.signal_id == signal_id,
        Evidence.status == 'active'
    ).order_by(Evidence.created_at.desc()).limit(limit).all()
    
    return {
        "signal_id": signal_id,
        "count": len(evidence_list),
        "evidence": [
            {
                "id": e.id,
                "evidence_type": e.evidence_type,
                "category": e.category,
                "trust_score": e.trust_score,
                "trust_classification": e.trust_classification,
                "file_url": e.file_url,
                "thumbnail_url": e.thumbnail_url,
                "source_type": e.source_type,
                "uploaded_at": e.uploaded_at.isoformat()
            }
            for e in evidence_list
        ]
    }


@router.get("/evidence/zone/{zone}")
async def get_evidence_by_zone(
    zone: str,
    db: Session = Depends(get_db),
    evidence_type: Optional[str] = None,
    min_trust_score: int = Query(0, ge=0, le=100),
    limit: int = Query(50, le=100)
):
    """
    Get evidence for a zone
    
    Args:
        zone: Zone identifier
        evidence_type: Optional filter by type (photo, pdf, etc.)
        min_trust_score: Minimum trust score filter
        limit: Maximum results
    
    Returns:
        List of evidence items
    """
    query = db.query(Evidence).filter(
        Evidence.zone == zone,
        Evidence.status == 'active',
        Evidence.trust_score >= min_trust_score
    )
    
    if evidence_type:
        query = query.filter(Evidence.evidence_type == evidence_type)
    
    evidence_list = query.order_by(Evidence.created_at.desc()).limit(limit).all()
    
    # Calculate summary statistics
    total_count = len(evidence_list)
    avg_trust = sum(e.trust_score for e in evidence_list) / total_count if total_count > 0 else 0
    
    type_counts = {}
    for e in evidence_list:
        type_counts[e.evidence_type] = type_counts.get(e.evidence_type, 0) + 1
    
    return {
        "zone": zone,
        "summary": {
            "total_count": total_count,
            "average_trust_score": round(avg_trust, 1),
            "by_type": type_counts
        },
        "evidence": [
            {
                "id": e.id,
                "evidence_type": e.evidence_type,
                "category": e.category,
                "trust_score": e.trust_score,
                "trust_classification": e.trust_classification,
                "file_url": e.file_url,
                "thumbnail_url": e.thumbnail_url,
                "source_type": e.source_type,
                "uploaded_at": e.uploaded_at.isoformat()
            }
            for e in evidence_list
        ]
    }


@router.delete("/evidence/{evidence_id}")
async def delete_evidence(evidence_id: str, db: Session = Depends(get_db)):
    """
    Delete evidence (soft delete - marks as deleted)
    
    Returns:
        Deletion confirmation
    """
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    # Soft delete
    evidence.status = 'deleted'
    
    # Create audit log
    audit_log = EvidenceAuditLog(
        id=str(uuid.uuid4()),
        evidence_id=evidence_id,
        action='delete',
        actor_type='api'
    )
    db.add(audit_log)
    
    db.commit()
    
    logger.info(f"Evidence deleted: {evidence_id}")
    
    return {
        "id": evidence_id,
        "status": "deleted",
        "message": "Evidence marked as deleted"
    }

# Made with Bob
