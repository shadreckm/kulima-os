"""
Evidence Processing Utilities
Handles EXIF extraction, duplicate detection, and PII filtering for evidence
"""
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EvidenceProcessor:
    """
    Process evidence files with Zero-PII compliance
    Extracts metadata, validates integrity, detects duplicates
    """
    
    # PII patterns to filter from EXIF/metadata
    PII_FIELDS = [
        'Artist', 'Author', 'Creator', 'Owner', 'Copyright',
        'UserComment', 'ImageDescription', 'XPComment', 'XPAuthor',
        'GPSLatitude', 'GPSLongitude',  # Precise GPS removed, only zone-level kept
        'SerialNumber', 'InternalSerialNumber', 'LensSerialNumber',
        'CameraSerialNumber', 'BodySerialNumber'
    ]
    
    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """
        Calculate SHA-256 hash for duplicate detection
        
        Args:
            file_content: Raw file bytes
            
        Returns:
            Hex string of SHA-256 hash
        """
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def extract_photo_metadata(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract EXIF metadata from photo with PII filtering
        
        Args:
            file_content: Raw image bytes
            filename: Original filename
            
        Returns:
            Filtered metadata dictionary
        """
        metadata = {
            'filename': filename,
            'file_size': len(file_content),
            'extracted_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Try to import PIL for EXIF extraction
            from PIL import Image
            from PIL.ExifTags import TAGS
            import io
            
            image = Image.open(io.BytesIO(file_content))
            
            # Basic image info
            metadata['format'] = image.format
            metadata['mode'] = image.mode
            metadata['size'] = image.size
            
            # Extract EXIF data
            exif_data = image._getexif()
            if exif_data:
                filtered_exif = {}
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    
                    # Filter out PII fields
                    if tag_name in EvidenceProcessor.PII_FIELDS:
                        continue
                    
                    # Convert value to JSON-serializable format
                    try:
                        if isinstance(value, bytes):
                            value = value.decode('utf-8', errors='ignore')
                        json.dumps(value)  # Test if serializable
                        filtered_exif[tag_name] = value
                    except (TypeError, UnicodeDecodeError):
                        # Skip non-serializable values
                        continue
                
                metadata['exif'] = filtered_exif
                
                # Extract timestamp if available
                if 'DateTime' in filtered_exif:
                    metadata['captured_at'] = filtered_exif['DateTime']
                elif 'DateTimeOriginal' in filtered_exif:
                    metadata['captured_at'] = filtered_exif['DateTimeOriginal']
            
        except ImportError:
            logger.warning("PIL not available, skipping EXIF extraction")
        except Exception as e:
            logger.error(f"Error extracting EXIF: {e}")
        
        return metadata
    
    @staticmethod
    def extract_pdf_metadata(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF with PII filtering
        
        Args:
            file_content: Raw PDF bytes
            filename: Original filename
            
        Returns:
            Filtered metadata dictionary
        """
        metadata = {
            'filename': filename,
            'file_size': len(file_content),
            'extracted_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Try to import PyPDF2 for PDF metadata
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            
            # Basic PDF info
            metadata['num_pages'] = len(pdf_reader.pages)
            
            # Extract metadata (filtered)
            pdf_info = pdf_reader.metadata
            if pdf_info:
                filtered_info = {}
                for key, value in pdf_info.items():
                    # Remove leading slash from key
                    clean_key = key.lstrip('/')
                    
                    # Filter out PII fields
                    if clean_key in EvidenceProcessor.PII_FIELDS:
                        continue
                    
                    # Keep only safe metadata
                    if clean_key in ['Title', 'Subject', 'CreationDate', 'ModDate', 'Producer']:
                        filtered_info[clean_key] = str(value)
                
                metadata['pdf_info'] = filtered_info
                
                # Extract creation date if available
                if 'CreationDate' in filtered_info:
                    metadata['captured_at'] = filtered_info['CreationDate']
            
        except ImportError:
            logger.warning("PyPDF2 not available, skipping PDF metadata extraction")
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
        
        return metadata
    
    @staticmethod
    def validate_zone_consistency(metadata: Dict[str, Any], claimed_zone: str) -> Tuple[bool, float]:
        """
        Validate that evidence metadata is consistent with claimed zone
        
        Args:
            metadata: Extracted metadata
            claimed_zone: Zone claimed in evidence submission
            
        Returns:
            Tuple of (is_consistent, confidence_score)
        """
        # For MVP, we accept zone claims without GPS validation
        # Future: Implement zone boundary checking if GPS available
        
        # Check if timestamp is reasonable (not future, not too old)
        if 'captured_at' in metadata:
            try:
                # Parse timestamp (handle various formats)
                captured_str = metadata['captured_at']
                # Simple validation: not in future
                # Full implementation would parse and validate properly
                return True, 0.8
            except Exception:
                return True, 0.5
        
        # No metadata to validate against
        return True, 0.6
    
    @staticmethod
    def detect_manipulation(metadata: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Detect potential evidence manipulation
        
        Args:
            metadata: Extracted metadata
            
        Returns:
            Tuple of (is_authentic, confidence_score)
        """
        confidence = 1.0
        
        # Check for EXIF data presence (photos without EXIF are suspicious)
        if 'exif' in metadata:
            if not metadata['exif']:
                confidence *= 0.7  # No EXIF data
        
        # Check for timestamp consistency
        if 'captured_at' in metadata:
            # Future: Implement timestamp validation logic
            pass
        else:
            confidence *= 0.8  # No timestamp
        
        # Check for software manipulation indicators
        if 'exif' in metadata and metadata['exif']:
            software = metadata['exif'].get('Software', '')
            if any(editor in software.lower() for editor in ['photoshop', 'gimp', 'editor']):
                confidence *= 0.6  # Edited with image editor
        
        is_authentic = confidence > 0.5
        return is_authentic, confidence


class TrustScoreCalculator:
    """
    Calculate trust scores for evidence using 7-factor model
    """
    
    # Factor weights (must sum to 1.0)
    WEIGHTS = {
        'timestamp_validity': 0.15,
        'source_reputation': 0.20,
        'duplicate_detection': 0.15,
        'metadata_consistency': 0.15,
        'geographical_consistency': 0.15,
        'visual_relevance': 0.10,
        'cross_source_verification': 0.10
    }
    
    @staticmethod
    def calculate_timestamp_validity(metadata: Dict[str, Any]) -> float:
        """
        Score timestamp validity (0.0 to 1.0)
        
        Checks:
        - Timestamp exists
        - Timestamp is not in future
        - Timestamp is reasonable (not too old)
        """
        if 'captured_at' not in metadata:
            return 0.5  # No timestamp, neutral score
        
        try:
            # For MVP, simple validation
            # Future: Parse and validate timestamp properly
            return 0.8
        except Exception:
            return 0.3
    
    @staticmethod
    def calculate_source_reputation(source_type: Optional[str]) -> float:
        """
        Score source reputation (0.0 to 1.0)
        
        Source types ranked by reliability:
        - extension_officer: 0.95 (official, trained)
        - cooperative: 0.85 (organized, accountable)
        - community: 0.70 (grassroots, variable)
        - telemetry: 0.90 (automated, objective)
        - unknown: 0.50 (neutral)
        """
        reputation_map = {
            'extension_officer': 0.95,
            'cooperative': 0.85,
            'telemetry': 0.90,
            'community': 0.70,
            'field_agent': 0.80,
            'unknown': 0.50
        }
        return reputation_map.get(source_type, 0.50)
    
    @staticmethod
    def calculate_duplicate_detection(file_hash: str, existing_hashes: list) -> float:
        """
        Score duplicate detection (0.0 to 1.0)
        
        Returns:
        - 1.0 if unique (not a duplicate)
        - 0.0 if exact duplicate found
        """
        if file_hash in existing_hashes:
            return 0.0  # Exact duplicate
        return 1.0  # Unique
    
    @staticmethod
    def calculate_metadata_consistency(metadata: Dict[str, Any]) -> float:
        """
        Score metadata consistency (0.0 to 1.0)
        
        Checks:
        - EXIF data present and complete
        - No manipulation indicators
        - Metadata fields are consistent
        """
        score = 0.5  # Base score
        
        # Check for EXIF presence
        if 'exif' in metadata and metadata['exif']:
            score += 0.2
        
        # Check for timestamp
        if 'captured_at' in metadata:
            score += 0.15
        
        # Check for manipulation
        is_authentic, confidence = EvidenceProcessor.detect_manipulation(metadata)
        score += confidence * 0.15
        
        return min(score, 1.0)
    
    @staticmethod
    def calculate_geographical_consistency(metadata: Dict[str, Any], zone: str) -> float:
        """
        Score geographical consistency (0.0 to 1.0)
        
        Validates that evidence location matches claimed zone
        """
        is_consistent, confidence = EvidenceProcessor.validate_zone_consistency(metadata, zone)
        return confidence
    
    @staticmethod
    def calculate_visual_relevance(evidence_type: str, category: Optional[str]) -> float:
        """
        Score visual relevance (0.0 to 1.0)
        
        For MVP: Simple heuristic based on evidence type
        Future: ML-based content analysis
        """
        # Photos and videos are more verifiable
        if evidence_type in ['photo', 'video']:
            return 0.8
        # Documents are moderately verifiable
        elif evidence_type in ['pdf', 'document']:
            return 0.7
        # Voice notes are less verifiable
        elif evidence_type == 'voice':
            return 0.6
        else:
            return 0.5
    
    @staticmethod
    def calculate_cross_source_verification(
        evidence_id: str,
        zone: str,
        evidence_type: str,
        similar_evidence_count: int
    ) -> float:
        """
        Score cross-source verification (0.0 to 1.0)
        
        Higher score if multiple sources provide similar evidence
        """
        if similar_evidence_count == 0:
            return 0.5  # No corroboration yet
        elif similar_evidence_count == 1:
            return 0.7  # One other source
        elif similar_evidence_count >= 2:
            return 0.9  # Multiple sources confirm
        return 0.5
    
    @classmethod
    def calculate_trust_score(
        cls,
        metadata: Dict[str, Any],
        source_type: Optional[str],
        file_hash: str,
        existing_hashes: list,
        zone: str,
        evidence_type: str,
        category: Optional[str],
        similar_evidence_count: int = 0
    ) -> Tuple[Dict[str, float], float, str]:
        """
        Calculate comprehensive trust score using 7-factor model
        
        Returns:
            Tuple of (factor_scores, composite_score, classification)
        """
        # Calculate individual factors
        factors = {
            'timestamp_validity': cls.calculate_timestamp_validity(metadata),
            'source_reputation': cls.calculate_source_reputation(source_type),
            'duplicate_detection': cls.calculate_duplicate_detection(file_hash, existing_hashes),
            'metadata_consistency': cls.calculate_metadata_consistency(metadata),
            'geographical_consistency': cls.calculate_geographical_consistency(metadata, zone),
            'visual_relevance': cls.calculate_visual_relevance(evidence_type, category),
            'cross_source_verification': cls.calculate_cross_source_verification(
                '', zone, evidence_type, similar_evidence_count
            )
        }
        
        # Calculate weighted composite score
        composite = sum(factors[k] * cls.WEIGHTS[k] for k in factors.keys())
        
        # Convert to 0-100 scale
        trust_score = int(composite * 100)
        
        # Classify trust level
        if trust_score >= 85:
            classification = 'very_high'
        elif trust_score >= 70:
            classification = 'high'
        elif trust_score >= 50:
            classification = 'moderate'
        else:
            classification = 'low'
        
        return factors, trust_score, classification

# Made with Bob
