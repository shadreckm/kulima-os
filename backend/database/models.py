"""
Database models using SQLAlchemy
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Signal(Base):
    """Signal model for storing activity inputs"""
    __tablename__ = "signals"
    
    id = Column(String, primary_key=True)
    zone = Column(String, nullable=False, index=True)
    activity_type = Column(String, nullable=False)
    time_window = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String, nullable=False)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Pattern(Base):
    """Pattern model for storing coordination patterns"""
    __tablename__ = "patterns"
    
    id = Column(String, primary_key=True)
    zone = Column(String, nullable=False, index=True)
    activity_type = Column(String, nullable=False)
    confidence_class = Column(String, nullable=False, index=True)
    stability_score = Column(Float, nullable=False)
    demand_rhythm = Column(Text, nullable=False)  # JSON string
    evaluation_window = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Prospectus(Base):
    """Prospectus model for storing generated prospectuses"""
    __tablename__ = "prospectuses"
    
    id = Column(String, primary_key=True)
    zone = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    pdf_url = Column(String, nullable=False)
    json_url = Column(String, nullable=False)
    meta_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """User model for multi-user support"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    phone_number = Column(String, unique=True, nullable=True)
    email = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    role = Column(String, default='user')
    created_at = Column(DateTime, default=datetime.utcnow)


class Zone(Base):
    """Zone model for storing zone information"""
    __tablename__ = "zones"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    region = Column(String, nullable=False)
    settlement_type = Column(String, nullable=True)
    infrastructure_status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
