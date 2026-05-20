"""
Test script to verify summary pipeline works end-to-end
"""
import requests
import time

# API base URL
API_URL = "http://localhost:8000/api/v1"

print("Testing Summary Pipeline")
print("=" * 50)

# Step 1: Initialize database
print("\n1. Initializing database...")
from backend.database.connection import init_db
init_db()
print("Database initialized")

# Step 2: Send test signals
print("\n2. Sending test signals...")
test_signals = [
    {
        "zone": "MZUZU",
        "activity_type": "irrigation",
        "time_window": "morning",
        "timestamp": "2026-05-20T06:00:00Z",
        "source": "manual",
        "user_id": "test_user_1"
    },
    {
        "zone": "MZUZU",
        "activity_type": "irrigation",
        "time_window": "morning",
        "timestamp": "2026-05-21T06:00:00Z",
        "source": "manual",
        "user_id": "test_user_1"
    },
    {
        "zone": "MZUZU",
        "activity_type": "irrigation",
        "time_window": "morning",
        "timestamp": "2026-05-22T06:00:00Z",
        "source": "manual",
        "user_id": "test_user_2"
    },
    {
        "zone": "MZUZU",
        "activity_type": "milling",
        "time_window": "afternoon",
        "timestamp": "2026-05-20T14:00:00Z",
        "source": "manual",
        "user_id": "test_user_1"
    },
    {
        "zone": "MZUZU",
        "activity_type": "milling",
        "time_window": "afternoon",
        "timestamp": "2026-05-21T14:00:00Z",
        "source": "manual",
        "user_id": "test_user_2"
    }
]

signal_ids = []
for signal in test_signals:
    try:
        response = requests.post(f"{API_URL}/signal", json=signal)
        if response.status_code == 200:
            result = response.json()
            signal_ids.append(result.get("signal_id"))
            print(f"  Signal sent: {signal['activity_type']} in {signal['zone']}")
        else:
            print(f"  Failed to send signal: {response.status_code}")
    except Exception as e:
        print(f"  Error sending signal: {e}")

print(f"\n  Total signals sent: {len(signal_ids)}")

# Step 3: Get summary
print("\n3. Getting summary for MZUZU...")
try:
    response = requests.get(f"{API_URL}/summary/MZUZU")
    if response.status_code == 200:
        summary = response.json()
        print(f"  Zone: {summary['zone']}")
        print(f"  Total Patterns: {summary['total_patterns']}")
        print(f"  High Confidence: {summary['high_confidence_patterns']}")
        print(f"  Moderate Confidence: {summary['moderate_confidence_patterns']}")
        print(f"  Productive Activities: {summary['productive_activities_detected']}")
        print(f"  Key Finding: {summary['key_finding']}")
        print(f"  Updated At: {summary['updated_at']}")
    else:
        print(f"  Failed to get summary: {response.status_code}")
except Exception as e:
    print(f"  Error getting summary: {e}")

print("\n" + "=" * 50)
print("Test complete")
