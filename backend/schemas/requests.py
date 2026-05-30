"""
Request validation schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class ZoneValidator(str):
    """Validator for zone codes"""
    
    VALID_ZONES = {"MZUZU", "LILONGWE", "BLANTYRE", "ZOMBA"}
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        zone_upper = v.upper()
        if zone_upper not in cls.VALID_ZONES:
            raise ValueError(f"Invalid zone. Must be one of: {', '.join(sorted(cls.VALID_ZONES))}")
        return zone_upper


class ActivityTypeValidator(str):
    """Validator for activity types"""
    
    VALID_ACTIVITIES = {
        "irrigation", "milling", "cold storage", "welding", 
        "trading", "storage", "unknown"
    }
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        activity_lower = v.lower().strip()
        if activity_lower not in cls.VALID_ACTIVITIES:
            raise ValueError(
                f"Invalid activity type. Must be one of: {', '.join(sorted(cls.VALID_ACTIVITIES))}"
            )
        return activity_lower


class TimeWindowValidator(str):
    """Validator for time windows"""
    
    VALID_WINDOWS = {"morning", "afternoon", "evening", "midday", "unknown"}
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        window_lower = v.lower().strip()
        if window_lower not in cls.VALID_WINDOWS:
            raise ValueError(
                f"Invalid time window. Must be one of: {', '.join(sorted(cls.VALID_WINDOWS))}"
            )
        return window_lower


class SignalRequest(BaseModel):
    """Schema for signal request - flexible input with optional structured fields"""
    activity_type: Optional[str] = Field(None, description="Activity type (optional if raw_text provided)")
    zone: Optional[str] = Field(None, description="Zone identifier (optional if raw_text provided)")
    time_window: Optional[str] = Field(None, description="Time window (optional if raw_text provided)")
    raw_text: Optional[str] = Field(None, description="Raw text input for normalization")
    timestamp: Optional[str] = Field(None, description="ISO format timestamp")
    source: str = Field(default="web", description="Signal source (whatsapp, web, manual)")
    user_id: Optional[str] = Field(default="anonymous", description="User identifier")
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v is None:
            return v
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("Invalid timestamp format. Use ISO format (e.g., 2026-05-20T10:00:00Z)")


class SignalCreate(BaseModel):
    """Schema for signal creation"""
    zone: str = Field(..., min_length=1, description="Zone identifier (MZUZU, LILONGWE, BLANTYRE, ZOMBA)")
    activity_type: str = Field(..., min_length=1, description="Activity type (irrigation, milling, cold storage, welding, trading)")
    time_window: str = Field(..., min_length=1, description="Time window (morning, afternoon, evening, midday)")
    timestamp: Optional[str] = Field(None, description="ISO format timestamp")
    source: str = Field(default="manual", description="Signal source (whatsapp, web, manual)")
    user_id: Optional[str] = Field(default="anonymous", description="User identifier")
    
    @validator('zone')
    def validate_zone(cls, v):
        return ZoneValidator.validate(v)
    
    @validator('activity_type')
    def validate_activity_type(cls, v):
        return ActivityTypeValidator.validate(v)
    
    @validator('time_window')
    def validate_time_window(cls, v):
        return TimeWindowValidator.validate(v)
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v is None:
            return v
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("Invalid timestamp format. Use ISO format (e.g., 2026-05-20T10:00:00Z)")


class ProspectusRequest(BaseModel):
    """Schema for prospectus generation"""
    zone: str = Field(..., min_length=1, description="Zone identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    
    @validator('zone')
    def validate_zone(cls, v):
        return ZoneValidator.validate(v)


class SignalsQuery(BaseModel):
    """Schema for signals query parameters"""
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    activity_type: Optional[str] = Field(None, description="Filter by activity type")
    date_from: Optional[str] = Field(None, description="Filter from date (ISO format)")
    date_to: Optional[str] = Field(None, description="Filter to date (ISO format)")
    
    @validator('activity_type')
    def validate_activity_type(cls, v):
        if v is None:
            return v
        return ActivityTypeValidator.validate(v)
    
    @validator('date_from', 'date_to')
    def validate_date(cls, v):
        if v is None:
            return v
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("Invalid date format. Use ISO format (e.g., 2026-05-20)")
