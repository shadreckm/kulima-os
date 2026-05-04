"""
PPSG Test Suite
Reference: PPSG_SPECIFICATION.md

Tests for:
- PII rejection
- Extra field rejection
- Volume amplification attack defense
- Synthetic uniform signal attack defense
- Raw data deletion after batch
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from .gateway import app, ephemeral_buffer, rate_limiter
from .pii_filter import detect_pii
from .anti_gaming import apply_volume_dampening, calculate_entropy, detect_suspicious_pattern
from .batch_processor import EphemeralBuffer


client = TestClient(app)


class TestPIIRejection:
    """Test PII detection and rejection (PPSG_SPECIFICATION.md Lines 712-820)"""
    
    def test_reject_phone_number(self):
        """Test rejection of phone number in signal."""
        signal = {
            "activity_type": "irrigation",
            "time_window": "morning",
            "zone_id": "zone_a",
            "signal_source_type": "human",
            "phone": "+254712345678"
        }
        
        response = client.post("/signal/submit", json=signal)
        assert response.status_code == 422  # Pydantic validation error (extra field)
    
    def test_reject_gps_coordinates(self):
        """Test rejection of GPS coordinates."""
        signal = {
            "activity_type": "milling",
            "time_window": "afternoon",
            "zone_id": "zone_b",
            "signal_source_type": "human",
            "location": "-1.286389,36.817223"
        }
        
        response = client.post("/signal/submit", json=signal)
        assert response.status_code == 422  # Pydantic validation error (extra field)
    
    def test_pii_filter_detects_phone(self):
        """Test PII filter detects phone number pattern."""
        signal = {"phone": "+254712345678"}
        error = detect_pii(signal)
        assert error is not None
        assert "phone number" in error.lower()
    
    def test_pii_filter_detects_gps(self):
        """Test PII filter detects GPS coordinates."""
        signal = {"location": "-1.286389,36.817223"}
        error = detect_pii(signal)
        assert error is not None
        assert "gps" in error.lower()
    
    def test_pii_filter_detects_uuid(self):
        """Test PII filter detects UUID pattern."""
        signal = {"device_id": "550e8400-e29b-41d4-a716-446655440000"}
        error = detect_pii(signal)
        assert error is not None
        assert "uuid" in error.lower()


class TestSchemaValidation:
    """Test strict schema validation (PPSG_SPECIFICATION.md Lines 602-640)"""
    
    def test_accept_valid_signal(self):
        """Test acceptance of valid signal."""
        signal = {
            "activity_type": "irrigation",
            "time_window": "morning",
            "zone_id": "zone_a",
            "signal_source_type": "human"
        }
        
        response = client.post("/signal/submit", json=signal)
        assert response.status_code == 202
        assert response.json()["status"] == "queued"
    
    def test_reject_extra_field(self):
        """Test rejection of signal with extra field."""
        signal = {
            "activity_type": "milling",
            "time_window": "afternoon",
            "zone_id": "zone_b",
            "signal_source_type": "human",
            "user_id": "user123"
        }
        
        response = client.post("/signal/submit", json=signal)
        assert response.status_code == 422  # Pydantic forbids extra fields
    
    def test_reject_invalid_activity_type(self):
        """Test rejection of invalid activity_type."""
        signal = {
            "activity_type": "farming",  # Not in allowed list
            "time_window": "morning",
            "zone_id": "zone_a",
            "signal_source_type": "human"
        }
        
        response = client.post("/signal/submit", json=signal)
        assert response.status_code == 422
    
    def test_reject_invalid_zone(self):
        """Test rejection of invalid zone_id."""
        signal = {
            "activity_type": "irrigation",
            "time_window": "morning",
            "zone_id": "zone_xyz",  # Not in whitelist
            "signal_source_type": "human"
        }
        
        response = client.post("/signal/submit", json=signal)
        assert response.status_code == 422
    
    def test_reject_missing_field(self):
        """Test rejection of signal with missing required field."""
        signal = {
            "activity_type": "irrigation",
            "time_window": "morning",
            "zone_id": "zone_a"
            # Missing signal_source_type
        }
        
        response = client.post("/signal/submit", json=signal)
        assert response.status_code == 422


class TestAntiGaming:
    """Test anti-gaming mechanisms (PPSG_SPECIFICATION.md Lines 642-710)"""
    
    def test_volume_dampening(self):
        """Test logarithmic volume dampening."""
        # 1 signal → weight 1.0
        assert abs(apply_volume_dampening(1) - 0.693) < 0.01
        
        # 10 signals → weight ~2.4
        assert abs(apply_volume_dampening(10) - 2.398) < 0.01
        
        # 100 signals → weight ~4.6
        assert abs(apply_volume_dampening(100) - 4.615) < 0.01
        
        # 1000 signals → weight ~6.9
        assert abs(apply_volume_dampening(1000) - 6.908) < 0.01
    
    def test_entropy_detection_uniform(self):
        """Test detection of overly uniform signals (low entropy)."""
        # All identical signals (low entropy)
        uniform_signals = [
            {"activity_type": "irrigation", "time_window": "morning", "zone_id": "zone_a"}
            for _ in range(100)
        ]
        
        entropy = calculate_entropy(uniform_signals)
        assert entropy["activity_entropy"] == 0.0  # All same activity
        assert entropy["time_entropy"] == 0.0  # All same time
        assert entropy["zone_entropy"] == 0.0  # All same zone
        
        # Should be flagged as suspicious
        assert detect_suspicious_pattern(entropy) is True
    
    def test_entropy_detection_varied(self):
        """Test that varied signals have higher entropy."""
        # Varied signals (higher entropy)
        varied_signals = [
            {"activity_type": "irrigation", "time_window": "morning", "zone_id": "zone_a"},
            {"activity_type": "milling", "time_window": "afternoon", "zone_id": "zone_b"},
            {"activity_type": "cold_storage", "time_window": "evening", "zone_id": "zone_c"},
            {"activity_type": "welding", "time_window": "morning", "zone_id": "zone_a"},
        ]
        
        entropy = calculate_entropy(varied_signals)
        assert entropy["activity_entropy"] > 1.5  # Varied activities
        assert entropy["time_entropy"] > 1.0  # Varied times
        assert entropy["zone_entropy"] > 1.0  # Varied zones
        
        # Should NOT be flagged as suspicious
        assert detect_suspicious_pattern(entropy) is False


class TestBatchProcessing:
    """Test batch processing and deletion (PPSG_SPECIFICATION.md Lines 452-520)"""
    
    def test_buffer_adds_signal(self):
        """Test that buffer accepts and stores signals."""
        buffer = EphemeralBuffer()
        signal = {
            "activity_type": "irrigation",
            "time_window": "morning",
            "zone_id": "zone_a",
            "signal_source_type": "human"
        }
        
        buffer.add_signal(signal)
        assert buffer.get_buffer_size() == 1
    
    def test_buffer_cleanup_expired(self):
        """Test that expired signals are removed."""
        buffer = EphemeralBuffer()
        signal = {
            "activity_type": "irrigation",
            "time_window": "morning",
            "zone_id": "zone_a",
            "signal_source_type": "human"
        }
        
        # Add signal
        buffer.add_signal(signal)
        assert buffer.get_buffer_size() == 1
        
        # Manually expire the signal
        buffer.buffer[0] = (
            buffer.buffer[0][0],
            buffer.buffer[0][1],
            datetime.utcnow() - timedelta(hours=3)  # Expired
        )
        
        # Cleanup should remove it
        buffer.cleanup_expired()
        assert buffer.get_buffer_size() == 0
    
    def test_batch_processing_deletes_raw_signals(self):
        """Test that raw signals are deleted after batch processing."""
        buffer = EphemeralBuffer()
        
        # Add multiple signals
        for i in range(10):
            signal = {
                "activity_type": "irrigation",
                "time_window": "morning",
                "zone_id": "zone_a",
                "signal_source_type": "human"
            }
            buffer.add_signal(signal)
        
        assert buffer.get_buffer_size() == 10
        
        # Process batch
        result = buffer.process_batch()
        
        # Raw signals should be deleted
        assert buffer.get_buffer_size() == 0
        assert result["batch_size"] == 10
        assert len(result["aggregated_signals"]) > 0


class TestEndpoints:
    """Test API endpoints (PPSG_SPECIFICATION.md Lines 522-600)"""
    
    def test_health_endpoint(self):
        """Test /health endpoint returns operational metrics."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "buffer_size" in data
        assert "last_batch_handoff" in data
    
    def test_zones_endpoint(self):
        """Test /zones endpoint returns zone whitelist."""
        response = client.get("/zones")
        assert response.status_code == 200
        data = response.json()
        assert "zones" in data
        assert len(data["zones"]) == 3
        assert any(z["id"] == "zone_a" for z in data["zones"])
        assert any(z["id"] == "zone_b" for z in data["zones"])
        assert any(z["id"] == "zone_c" for z in data["zones"])


class TestRateLimiting:
    """Test rate limiting (PPSG_SPECIFICATION.md Lines 438-450)"""
    
    def test_zone_rate_limit(self):
        """Test that zone rate limit is enforced."""
        # This test would require submitting 100+ signals to same zone
        # For reference implementation, we test the rate limiter directly
        limiter = RateLimiter()
        
        # Increment 100 times
        for _ in range(100):
            limiter.increment("zone_a", "human")
        
        # 101st should be blocked
        error = limiter.check_zone_limit("zone_a")
        assert error is not None
        assert "rate limit" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
