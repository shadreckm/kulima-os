"""
End-to-end system validation script
"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def test_signal_submission():
    """Test signal submission"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Testing signal submission...")
    
    signals = [
        {"zone": "MZUZU", "activity_type": "irrigation", "time_window": "morning"},
        {"zone": "MZUZU", "activity_type": "milling", "time_window": "afternoon"},
        {"zone": "MZUZU", "activity_type": "irrigation", "time_window": "morning"},
    ]
    
    for signal in signals:
        response = requests.post(f"{API_BASE}/signal", json=signal)
        logger.info("Signal submitted: %s", response.status_code)
        logger.info("Response: %s", response.json())
    
    logger.info("Signal submission complete.\n")

def test_summary():
    """Test summary endpoint"""
    logger = logging.getLogger(__name__)
    logger.info("Testing summary endpoint...")

    response = requests.get(f"{API_BASE}/summary/MZUZU")
    logger.info("Summary status: %s", response.status_code)
    data = response.json()
    logger.info("Summary response: %s", json.dumps(data, indent=2))
    
    if data.get("status") == "success":
        total_patterns = data["data"]["total_patterns"]
        logger.info("Total patterns: %s", total_patterns)
        if total_patterns > 0:
            logger.info("SUCCESS: Patterns generated!")
        else:
            logger.info("FAILURE: No patterns generated")
    else:
        logger.info("FAILURE: Summary returned error")
    
    logger.info("")

def test_prospectus_generation():
    """Test prospectus generation"""
    logger = logging.getLogger(__name__)
    logger.info("Testing prospectus generation...")

    response = requests.post(f"{API_BASE}/generate-prospectus", json={"zone": "MZUZU"})
    logger.info("Prospectus status: %s", response.status_code)
    data = response.json()
    logger.info("Prospectus response: %s", json.dumps(data, indent=2))
    
    if data.get("status") == "success":
        logger.info("SUCCESS: Prospectus generated!")
        return data["data"]
    else:
        logger.info("FAILURE: Prospectus generation failed")
        return None

def test_file_download(prospectus_data):
    """Test file download"""
    logger = logging.getLogger(__name__)
    logger.info("Testing file download...")

    if not prospectus_data:
        logger.info("Skipping file download (no prospectus data)")
        return

    pdf_url = prospectus_data["pdf_url"]
    response = requests.get(f"http://localhost:8000{pdf_url}")
    logger.info("Download status: %s", response.status_code)

    if response.status_code == 200:
        logger.info("SUCCESS: File downloaded!")
        logger.info("File size: %s bytes", len(response.content))
    else:
        logger.info("FAILURE: File download failed")

    logger.info()

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("KULIMA OS END-TO-END VALIDATION")
    logger.info("=" * 50)
    logger.info()

    try:
        test_signal_submission()
        test_summary()
        prospectus_data = test_prospectus_generation()
        test_file_download(prospectus_data)

        logger.info("=" * 50)
        logger.info("VALIDATION COMPLETE")
        logger.info("=" * 50)
    except Exception as e:
        logger.exception("ERROR: %s", str(e))
