"""
End-to-end test for Kulima OS pipeline
Tests: signal submission → summary retrieval → prospectus generation
"""
import requests
import json
import sys

# API base URL
API_URL = "http://localhost:8000/api/v1"

def test_signal_submission():
    """Test signal submission via API"""
    print("\n=== Testing Signal Submission ===")
    
    signal_data = {
        "zone": "MZUZU",
        "activity_type": "irrigation",
        "time_window": "morning",
        "source": "manual",
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(f"{API_URL}/signal", json=signal_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_summary_retrieval():
    """Test summary retrieval via API"""
    print("\n=== Testing Summary Retrieval ===")
    
    try:
        response = requests.get(f"{API_URL}/summary/MZUZU")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('status') == 'success':
            summary = data.get('data', {})
            print(f"\nTotal Patterns: {summary.get('total_patterns')}")
            print(f"High Confidence: {summary.get('high_confidence_patterns')}")
            print(f"Moderate Confidence: {summary.get('moderate_confidence_patterns')}")
            print(f"Activities: {summary.get('productive_activities_detected')}")
            return True
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_prospectus_generation():
    """Test prospectus generation via API"""
    print("\n=== Testing Prospectus Generation ===")
    
    prospectus_data = {
        "zone": "MZUZU",
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(f"{API_URL}/generate-prospectus", json=prospectus_data)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('status') == 'success':
            prospectus = data.get('data', {})
            print(f"\nProspectus ID: {prospectus.get('prospectus_id')}")
            print(f"PDF URL: {prospectus.get('pdf_url')}")
            print(f"JSON URL: {prospectus.get('json_url')}")
            return True
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_twilio_webhook():
    """Test Twilio webhook via test endpoint"""
    print("\n=== Testing Twilio Webhook (Test Endpoint) ===")
    
    webhook_data = {
        "from": "+265123456789",
        "body": "watering crops in Mzuzu this morning"
    }
    
    try:
        response = requests.post(f"{API_URL}/webhook/test", json=webhook_data)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('status') == 'success':
            print(f"\nSignal ID: {data.get('signal_id')}")
            print(f"Normalized Signal: {data.get('normalized_signal')}")
            return True
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all end-to-end tests"""
    print("=" * 60)
    print("KULIMA OS END-TO-END TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Signal submission
    results.append(("Signal Submission", test_signal_submission()))
    
    # Test 2: Summary retrieval
    results.append(("Summary Retrieval", test_summary_retrieval()))
    
    # Test 3: Prospectus generation
    results.append(("Prospectus Generation", test_prospectus_generation()))
    
    # Test 4: Twilio webhook
    results.append(("Twilio Webhook", test_twilio_webhook()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n✓ All tests passed! System is working end-to-end.")
        sys.exit(0)
    else:
        print(f"\n✗ {total_tests - total_passed} test(s) failed. Please review errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
