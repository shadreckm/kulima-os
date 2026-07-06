"""
Evidence Storage Service
Handles file storage for evidence (local or S3-compatible)
"""
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EvidenceStorageService:
    """
    Storage service for evidence files
    Supports local filesystem and S3-compatible storage
    """
    
    def __init__(self, storage_type: str = "local", base_path: str = "./evidence_storage"):
        """
        Initialize storage service
        
        Args:
            storage_type: "local" or "s3"
            base_path: Base directory for local storage or S3 bucket name
        """
        self.storage_type = storage_type
        self.base_path = base_path
        
        if storage_type == "local":
            # Create local storage directory
            Path(base_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Evidence storage initialized: {base_path}")
        elif storage_type == "s3":
            # Future: Initialize S3 client
            logger.info(f"S3 storage initialized: {base_path}")
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
    
    def generate_storage_path(self, evidence_id: str, file_extension: str) -> str:
        """
        Generate storage path for evidence file
        
        Format: /{year}/{month}/{evidence_id}.{ext}
        
        Args:
            evidence_id: Unique evidence identifier
            file_extension: File extension (jpg, pdf, etc.)
            
        Returns:
            Storage path string
        """
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        filename = f"{evidence_id}.{file_extension}"
        return f"{year}/{month}/{filename}"
    
    def save_file(
        self,
        file_content: bytes,
        evidence_id: str,
        file_extension: str
    ) -> Tuple[str, str]:
        """
        Save evidence file to storage
        
        Args:
            file_content: Raw file bytes
            evidence_id: Unique evidence identifier
            file_extension: File extension
            
        Returns:
            Tuple of (file_url, storage_path)
        """
        storage_path = self.generate_storage_path(evidence_id, file_extension)
        
        if self.storage_type == "local":
            return self._save_local(file_content, storage_path)
        elif self.storage_type == "s3":
            return self._save_s3(file_content, storage_path)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def _save_local(self, file_content: bytes, storage_path: str) -> Tuple[str, str]:
        """Save file to local filesystem"""
        full_path = Path(self.base_path) / storage_path
        
        # Create directory if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(full_path, 'wb') as f:
            f.write(file_content)
        
        # Generate URL (relative path for local storage)
        file_url = f"/evidence/{storage_path}"
        
        logger.info(f"Evidence saved locally: {full_path}")
        return file_url, storage_path
    
    def _save_s3(self, file_content: bytes, storage_path: str) -> Tuple[str, str]:
        """Save file to S3-compatible storage"""
        # Future: Implement S3 upload using boto3
        # For MVP, fall back to local storage
        logger.warning("S3 storage not yet implemented, using local storage")
        return self._save_local(file_content, storage_path)
    
    def generate_thumbnail(
        self,
        file_content: bytes,
        evidence_id: str,
        size: Tuple[int, int] = (300, 300)
    ) -> Optional[Tuple[str, str]]:
        """
        Generate thumbnail for image evidence
        
        Args:
            file_content: Raw image bytes
            evidence_id: Unique evidence identifier
            size: Thumbnail size (width, height)
            
        Returns:
            Tuple of (thumbnail_url, storage_path) or None if failed
        """
        try:
            from PIL import Image
            import io
            
            # Open image
            image = Image.open(io.BytesIO(file_content))
            
            # Generate thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail to bytes
            thumb_io = io.BytesIO()
            image.save(thumb_io, format='JPEG', quality=85)
            thumb_content = thumb_io.getvalue()
            
            # Save thumbnail
            thumb_url, thumb_path = self.save_file(
                thumb_content,
                f"{evidence_id}_thumb",
                "jpg"
            )
            
            logger.info(f"Thumbnail generated: {thumb_path}")
            return thumb_url, thumb_path
            
        except ImportError:
            logger.warning("PIL not available, skipping thumbnail generation")
            return None
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None
    
    def delete_file(self, storage_path: str) -> bool:
        """
        Delete evidence file from storage
        
        Args:
            storage_path: Path to file in storage
            
        Returns:
            True if deleted successfully
        """
        if self.storage_type == "local":
            return self._delete_local(storage_path)
        elif self.storage_type == "s3":
            return self._delete_s3(storage_path)
        else:
            return False
    
    def _delete_local(self, storage_path: str) -> bool:
        """Delete file from local filesystem"""
        try:
            full_path = Path(self.base_path) / storage_path
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Evidence deleted: {full_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting evidence: {e}")
            return False
    
    def _delete_s3(self, storage_path: str) -> bool:
        """Delete file from S3-compatible storage"""
        # Future: Implement S3 deletion using boto3
        logger.warning("S3 deletion not yet implemented")
        return False
    
    def get_file_url(self, storage_path: str, signed: bool = False, expiry: int = 3600) -> str:
        """
        Get URL for accessing evidence file
        
        Args:
            storage_path: Path to file in storage
            signed: Whether to generate signed URL (for S3)
            expiry: URL expiry time in seconds (for signed URLs)
            
        Returns:
            File URL
        """
        if self.storage_type == "local":
            return f"/evidence/{storage_path}"
        elif self.storage_type == "s3":
            # Future: Generate signed S3 URL if requested
            return f"https://{self.base_path}.s3.amazonaws.com/{storage_path}"
        else:
            return ""


# Global storage service instance
_storage_service: Optional[EvidenceStorageService] = None


def get_storage_service() -> EvidenceStorageService:
    """Get or create global storage service instance"""
    global _storage_service
    if _storage_service is None:
        # Initialize with environment variables or defaults
        storage_type = os.getenv("EVIDENCE_STORAGE_TYPE", "local")
        base_path = os.getenv("EVIDENCE_STORAGE_PATH", "./evidence_storage")
        _storage_service = EvidenceStorageService(storage_type, base_path)
    return _storage_service

# Made with Bob
