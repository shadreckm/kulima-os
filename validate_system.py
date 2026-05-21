"""
End-to-end system validation script
"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def test_signal_submission():
    """Test signal submission"""
    print("Testing signal submission...")
    
    signals = [
        {"zone": "MZUZU", "activity_type": "irrigation", "time_window": "morning"},
        {"zone": "MZUZU", "activity_type": "milling", "time_window": "afternoon"},
        {"zone": "MZUZU", "activity_type": "irrigation", "time_window": "morning"},
    ]
    
    for signal in signals:
        response = requests.post(f"{API_BASE}/signal", json=signal)
        print(f"Signal submitted: {response.status_code}")
        print(f"Response: {response.json()}")
    
    print("Signal submission complete.\n")

def test_summary():
    """Test summary endpoint"""
    print("Testing summary endpoint...")
    
    response = requests.get(f"{API_BASE}/summary/MZUZU")
    print(f"Summary status: {response.status_code}")
    data = response.json()
    print(f"Summary response: {json.dumps(data, indent=2)}")
    
    if data.get("status") == "success":
        total_patterns = data["data"]["total_patterns"]
        print(f"Total patterns: {total_patterns}")
        if total_patterns > 0:
            print("SUCCESS: Patterns generated!")
        else:
            print("FAILURE: No patterns generated")
    else:
        print("FAILURE: Summary returned error")
    
    print()

def test_prospectus_generation():
    """Test prospectus generation"""
    print("Testing prospectus generation...")
    
    response = requests.post(f"{API_BASE}/generate-prospectus", json={"zone": "MZUZU"})
    print(f"Prospectus status: {response.status_code}")
    data = response.json()
    print(f"Prospectus response: {json.dumps(data, indent=2)}")
    
    if data.get("status") == "success":
        print("SUCCESS: Prospectus generated!")
        return data["data"]
    else:
        print("FAILURE: Prospectus generation failed")
        return None

def test_file_download(prospectus_data):
    """Test file download"""
    print("Testing file download...")
    
    if not prospectus_data:
        print("Skipping file download (no prospectus data)")
        return
    
    pdf_url = prospectus_data["pdf_url"]
    response = requests.get(f"http://localhost:8000{pdf_url}")
    print(f"Download status: {response.status_code}")
    
    if response.status_code == 200:
        print("SUCCESS: File downloaded!")
        print(f"File size: {len(response.content)} bytes")
    else:
        print("FAILURE: File download failed")
    
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("KULIMA OS END-TO-END VALIDATION")
    print("=" * 50)
    print()
    
    try:
        test_signal_submission()
        test_summary()
        prospectus_data = test_prospectus_generation()
        test_file_download(prospectus_data)
        
        print("=" * 50)
        print("VALIDATION COMPLETE")
        print("=" * 50)
    except Exception as e:
        print(f"ERROR: {str(e)}")
