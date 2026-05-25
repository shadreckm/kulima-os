"""
Background task processing service
Uses FastAPI BackgroundTasks for async processing (no Redis/Celery required)
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.connection import SessionLocal, get_db
from backend.database.models import Signal, Prospectus
from core.lumoza.lumoza_engine import LumozaEngine
from core.lundai.lundai_engine import LundaiEngine, evaluate_signal_integrity
from core.zentari.zentari_engine import ZentariEngine
from core.prospectus.prospectus_generator import ProspectusGenerator
from policy import compute_planning_reserve
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# In-memory task status tracking
task_status: Dict[str, Dict[str, Any]] = {}


class BackgroundTaskService:
    """
    Service for managing background tasks using FastAPI BackgroundTasks.
    """
    
    @staticmethod
    def generate_prospectus_async(
        task_id: str,
        zone: str,
        user_id: str,
        db: Session
    ) -> None:
        """
        Generate prospectus in background task.
        
        Args:
            task_id: Unique task identifier
            zone: Zone identifier
            user_id: User identifier
            db: Database session
        """
        try:
            # Update task status
            task_status[task_id] = {
                "status": "processing",
                "progress": 0,
                "message": "Starting prospectus generation...",
                "started_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Background task {task_id}: Starting prospectus generation for zone {zone}")
            
            # Step 1: Fetch signals
            task_status[task_id]["progress"] = 10
            task_status[task_id]["message"] = "Fetching signals..."
            signals = db.query(Signal).filter(Signal.zone == zone.upper()).all()
            
            if not signals:
                task_status[task_id] = {
                    "status": "failed",
                    "error": f"No signals found for zone {zone}",
                    "completed_at": datetime.utcnow().isoformat()
                }
                logger.error(f"Background task {task_id}: No signals found")
                return
            
            logger.info(f"Background task {task_id}: Found {len(signals)} signals")
            
            # Step 2: Convert to engine format
            task_status[task_id]["progress"] = 20
            task_status[task_id]["message"] = "Processing signals..."
            signal_data = []
            for signal in signals:
                signal_data.append({
                    "zone": signal.zone,
                    "activity_type": signal.activity_type,
                    "time_window": signal.time_window,
                    "timestamp": signal.timestamp.isoformat(),
                    "signal_source": signal.source,
                    "user_phone": signal.user_id,
                    "service_priority": "productive"
                })
            
            for i, signal in enumerate(signal_data):
                signal["cycle_index"] = i
            
            # Step 3: Run LUMOZA
            task_status[task_id]["progress"] = 40
            task_status[task_id]["message"] = "Detecting coordination patterns..."
            lumoza = LumozaEngine()
            coordination_patterns = lumoza.process_signals(signal_data)
            
            if not coordination_patterns:
                task_status[task_id] = {
                    "status": "failed",
                    "error": "No coordination patterns detected",
                    "completed_at": datetime.utcnow().isoformat()
                }
                logger.error(f"Background task {task_id}: No patterns detected")
                return
            
            # Step 4: Run LUNDAI
            task_status[task_id]["progress"] = 60
            task_status[task_id]["message"] = "Analyzing settlement context..."
            planning_reserve = compute_planning_reserve(len(coordination_patterns))
            lundai = LundaiEngine()
            lundai_analysis = lundai.analyze_settlement_context(
                coordination_patterns, 
                planning_reserve
            )
            
            # Step 5: Run ZENTARI
            task_status[task_id]["progress"] = 70
            task_status[task_id]["message"] = "Evaluating coordination confidence..."
            zentari = ZentariEngine()
            confidence_results = zentari.evaluate_coordination_confidence(
                coordination_patterns,
                planning_reserve,
                flow_graph=lundai_analysis.get('flow_graph', {})
            )
            
            # Step 6: Generate prospectus
            task_status[task_id]["progress"] = 80
            task_status[task_id]["message"] = "Generating prospectus documents..."
            generator = ProspectusGenerator()
            prospectus_data = generator.generate_prospectus(
                confidence_results=confidence_results,
                lundai_analysis=lundai_analysis,
                metadata={
                    "region": zone,
                    "period": "7-cycle window (1 week)",
                    "is_sample": False
                },
                planning_reserve=planning_reserve
            )
            
            # Step 7: Save files
            task_status[task_id]["progress"] = 90
            task_status[task_id]["message"] = "Saving prospectus files..."
            timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
            zone_key = zone.upper()
            
            pdf_filename = f"prospectus_{zone_key}_{timestamp}.pdf"
            json_filename = f"prospectus_{zone_key}_{timestamp}.json"
            
            prospectus_dir = Path("prospectuses")
            prospectus_dir.mkdir(exist_ok=True)
            
            pdf_path = prospectus_dir / pdf_filename
            json_path = prospectus_dir / json_filename
            
            # Save JSON
            import json
            with open(json_path, 'w') as f:
                json.dump(prospectus_data, f, indent=2, default=str)
            
            # Generate PDF
            generator.generate_pdf(prospectus_data, str(pdf_path))
            
            # Step 8: Store in database
            task_status[task_id]["progress"] = 95
            task_status[task_id]["message"] = "Saving to database..."
            prospectus_id = f"pros_{task_id}"
            
            prospectus = Prospectus(
                id=prospectus_id,
                zone=zone_key,
                user_id=user_id,
                pdf_url=f"/api/v1/download/{pdf_filename}",
                json_url=f"/api/v1/download/{json_filename}",
                meta_data=json.dumps(prospectus_data, default=str)
            )
            db.add(prospectus)
            db.commit()
            
            # Complete
            task_status[task_id] = {
                "status": "completed",
                "progress": 100,
                "message": "Prospectus generation complete",
                "prospectus_id": prospectus_id,
                "pdf_url": f"/api/v1/download/{pdf_filename}",
                "json_url": f"/api/v1/download/{json_filename}",
                "completed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Background task {task_id}: Prospectus generation complete")
            
        except Exception as e:
            logger.error(f"Background task {task_id}: Error - {str(e)}")
            task_status[task_id] = {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a background task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status dict or None if not found
        """
        return task_status.get(task_id)
    
    @staticmethod
    def cleanup_old_tasks(max_age_hours: int = 24) -> None:
        """
        Clean up old task status entries.
        
        Args:
            max_age_hours: Maximum age in hours to keep
        """
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        to_delete = []
        
        for task_id, status in task_status.items():
            if "completed_at" in status:
                completed_at = datetime.fromisoformat(status["completed_at"]).timestamp()
                if completed_at < cutoff:
                    to_delete.append(task_id)
        
        for task_id in to_delete:
            del task_status[task_id]
        
        logger.info(f"Cleaned up {len(to_delete)} old task status entries")
