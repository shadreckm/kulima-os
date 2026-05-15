"""
Signal Storage Layer for LUMOZA WhatsApp Interface

Stores incoming activity signals for processing by LUMOZA.
Supports both JSON file and SQLite backends.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Signal:
    """Activity signal from WhatsApp user."""
    signal_id: str
    activity_type: str
    zone: str
    frequency: str
    actors: Optional[int] = None
    raw_message: str = ""
    confidence: float = 0.8
    timestamp: str = ""
    user_phone: str = ""
    processed: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class SignalStorage:
    """Base class for signal storage."""
    
    def add_signal(self, signal: Signal) -> bool:
        raise NotImplementedError
    
    def get_signals(self, zone: Optional[str] = None, processed: bool = False) -> List[Signal]:
        raise NotImplementedError
    
    def mark_processed(self, signal_id: str) -> bool:
        raise NotImplementedError


class JsonSignalStorage(SignalStorage):
    """Store signals in JSON file (MVP-ready)."""
    
    def __init__(self, filepath: str = "signals.json"):
        self.filepath = Path(filepath)
        self._ensure_file()
    
    def _ensure_file(self):
        """Ensure signals.json exists."""
        if not self.filepath.exists():
            self.filepath.write_text(json.dumps([]))
    
    def add_signal(self, signal: Signal) -> bool:
        """Add a signal to storage."""
        try:
            signals = self._read_signals()
            signals.append(signal.to_dict())
            self.filepath.write_text(json.dumps(signals, indent=2))
            return True
        except Exception as e:
            print(f"Error adding signal: {e}")
            return False
    
    def get_signals(self, zone: Optional[str] = None, processed: bool = False) -> List[Signal]:
        """Retrieve signals from storage."""
        try:
            signals_data = self._read_signals()
            signals = [Signal(**s) for s in signals_data]
            
            # Filter by zone if specified
            if zone:
                signals = [s for s in signals if s.zone == zone.upper().replace(" ", "_")]
            
            # Filter by processed status
            signals = [s for s in signals if s.processed == processed]
            
            return signals
        except Exception as e:
            print(f"Error retrieving signals: {e}")
            return []
    
    def mark_processed(self, signal_id: str) -> bool:
        """Mark a signal as processed."""
        try:
            signals = self._read_signals()
            for signal in signals:
                if signal.get('signal_id') == signal_id:
                    signal['processed'] = True
                    break
            self.filepath.write_text(json.dumps(signals, indent=2))
            return True
        except Exception as e:
            print(f"Error marking signal processed: {e}")
            return False
    
    def _read_signals(self) -> List[Dict]:
        """Read signals from file."""
        try:
            return json.loads(self.filepath.read_text())
        except:
            return []


class SqliteSignalStorage(SignalStorage):
    """Store signals in SQLite database."""
    
    def __init__(self, db_path: str = "signals.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY,
                    activity_type TEXT,
                    zone TEXT,
                    frequency TEXT,
                    actors INTEGER,
                    raw_message TEXT,
                    confidence REAL,
                    timestamp TEXT,
                    user_phone TEXT,
                    processed BOOLEAN DEFAULT 0
                )
            """)
            conn.commit()
    
    def add_signal(self, signal: Signal) -> bool:
        """Add a signal to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO signals 
                    (signal_id, activity_type, zone, frequency, actors, raw_message, confidence, timestamp, user_phone, processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal.signal_id, signal.activity_type, signal.zone, signal.frequency,
                    signal.actors, signal.raw_message, signal.confidence, signal.timestamp,
                    signal.user_phone, signal.processed
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding signal: {e}")
            return False
    
    def get_signals(self, zone: Optional[str] = None, processed: bool = False) -> List[Signal]:
        """Retrieve signals from database."""
        try:
            query = "SELECT * FROM signals WHERE processed = ?"
            params = [processed]
            
            if zone:
                query += " AND zone = ?"
                params.append(zone.upper().replace(" ", "_"))
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                signals = []
                for row in rows:
                    signal_dict = dict(zip(columns, row))
                    signals.append(Signal(**signal_dict))
                
                return signals
        except Exception as e:
            print(f"Error retrieving signals: {e}")
            return []
    
    def mark_processed(self, signal_id: str) -> bool:
        """Mark a signal as processed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE signals SET processed = 1 WHERE signal_id = ?", (signal_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error marking signal processed: {e}")
            return False


# Default storage instance (JSON for MVP speed)
default_storage = JsonSignalStorage("lumoza_signals.json")


def store_signal(activity_type: str, zone: str, frequency: str, actors: Optional[int] = None, 
                 raw_message: str = "", user_phone: str = "") -> str:
    """
    Convenience function to store a signal.
    
    Args:
        activity_type: Type of activity
        zone: Zone identifier
        frequency: Activity frequency
        actors: Number of actors (optional)
        raw_message: Original user message
        user_phone: WhatsApp phone number
        
    Returns:
        Signal ID if successful
    """
    signal_id = f"{zone}_{activity_type}_{datetime.utcnow().isoformat()}"
    
    signal = Signal(
        signal_id=signal_id,
        activity_type=activity_type,
        zone=zone,
        frequency=frequency,
        actors=actors,
        raw_message=raw_message,
        confidence=0.8,
        timestamp=datetime.utcnow().isoformat(),
        user_phone=user_phone,
        processed=False
    )
    
    if default_storage.add_signal(signal):
        return signal_id
    return None


def get_unprocessed_signals(zone: Optional[str] = None) -> List[Signal]:
    """Get unprocessed signals for LUMOZA processing."""
    return default_storage.get_signals(zone=zone, processed=False)
