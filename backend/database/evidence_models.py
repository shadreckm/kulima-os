"""
Evidence Intelligence Layer - Database Models
Zero-PII compliant evidence storage for KULIMA OS
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.models import Base


class Evidence(Base):
    """
    Evidence model for storing verifiable evidence linked to signals/recommendations
    
    ZERO-PII COMPLIANCE:
    - No personal identifiers stored
    - GPS coordinates limited to EPA/zone level (not precise locations)
    - No facial recognition or individual tracking
    - Evidence can be anonymized
    """
    __tablename__ = "evidence"
    
    id = Column(String, primary_key=True)
    
    # Linking (to signals or recommendations, not individuals)
    signal_id = Column(String, ForeignKey("signals.id"), nullable=True, index=True)
    zone = Column(String, nullable=False, index=True)
    
    # Evidence classification
    evidence_type = Column(String, nullable=False, index=True)  # photo, pdf, voice, video, etc.
    category = Column(String, nullable=True)  # crop_damage, infrastructure, meeting, etc.
    
    # Storage
    file_url = Column(Text, nullable=False)  # S3 or local storage URL
    thumbnail_url = Column(Text, nullable=True)  # For photos/videos
    file_size = Column(Integer, nullable=True)  # In bytes
    file_hash = Column(String, nullable=True, index=True)  # SHA-256 for duplicate detection
    
    # Trust scoring (0-100)
    trust_score = Column(Integer, nullable=False, default=0)
    trust_classification = Column(String, nullable=True)  # very_high, high, moderate, low
    
    # Metadata (JSON) - EXIF, timestamps, etc. (PII-filtered)
    evidence_metadata = Column(JSON, nullable=True)
    
    # Temporal context (batched, not precise)
    captured_at = Column(DateTime, nullable=True)  # When evidence was captured (if available)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Source context (not individual identity)
    source_type = Column(String, nullable=True)  # extension_officer, cooperative, community, telemetry
    
    # Status
    status = Column(String, nullable=False, default="active")  # active, archived, deleted
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_evidence_zone_type', 'zone', 'evidence_type'),
        Index('idx_evidence_trust', 'trust_score'),
        Index('idx_evidence_created', 'created_at'),
    )


class EvidenceTrustFactors(Base):
    """
    Trust factors for evidence scoring (7-factor model)
    Stores individual factor scores for transparency and auditability
    """
    __tablename__ = "evidence_trust_factors"
    
    id = Column(String, primary_key=True)
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=False, index=True)
    
    # 7 Trust Factors (0.0 to 1.0 scale)
    timestamp_validity = Column(Float, nullable=False, default=0.0)  # EXIF timestamp consistency
    source_reputation = Column(Float, nullable=False, default=0.0)  # Source type reliability
    duplicate_detection = Column(Float, nullable=False, default=1.0)  # Not a duplicate
    metadata_consistency = Column(Float, nullable=False, default=0.0)  # EXIF/metadata integrity
    geographical_consistency = Column(Float, nullable=False, default=0.0)  # GPS matches zone
    visual_relevance = Column(Float, nullable=False, default=0.0)  # Content relevance (future: ML)
    cross_source_verification = Column(Float, nullable=False, default=0.0)  # Multiple sources confirm
    
    # Composite score (weighted average)
    composite_score = Column(Float, nullable=False, default=0.0)
    
    # Calculation metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculation_version = Column(String, nullable=False, default="1.0")  # For model versioning
    
    created_at = Column(DateTime, default=datetime.utcnow)


class EvidenceLink(Base):
    """
    Links between evidence and other entities (signals, patterns, recommendations)
    Enables evidence chains and cross-validation
    """
    __tablename__ = "evidence_links"
    
    id = Column(String, primary_key=True)
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=False, index=True)
    
    # Link target
    linked_entity_type = Column(String, nullable=False)  # signal, pattern, recommendation, prospectus
    linked_entity_id = Column(String, nullable=False, index=True)
    
    # Link metadata
    link_type = Column(String, nullable=True)  # supports, contradicts, corroborates
    confidence = Column(Float, nullable=True)  # How strong is this link?
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_evidence_link_entity', 'linked_entity_type', 'linked_entity_id'),
    )


class EvidenceAuditLog(Base):
    """
    Audit log for evidence operations
    Tracks access, modifications, and deletions for accountability
    """
    __tablename__ = "evidence_audit_log"
    
    id = Column(String, primary_key=True)
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=False, index=True)
    
    # Action
    action = Column(String, nullable=False)  # upload, view, update, delete, archive
    actor_type = Column(String, nullable=True)  # system, api, user_role (not individual)
    
    # Context
    ip_range = Column(String, nullable=True)  # IP range, not specific IP (privacy)
    user_agent = Column(String, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# Made with Bob
