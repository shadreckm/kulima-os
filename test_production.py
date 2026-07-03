#!/usr/bin/env python3
"""
Production Verification Test Suite for Kulima OS
"""
import requests
import json
import time
from datetime import datetime

BACKEND_URL = "https://kulima-os-backend.onrender.com"
FRONTEND_URL = "https://kulima-os.vercel.app"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def test_backend_health():
    print_section("TEST 1: BACKEND HEALTH")
    
    try:
        # Test root health endpoint
        r = requests.get(f"{BACKEND_URL}/health", timeout=10)
        print(f"GET /health")
        print(f"Status: {r.status_code}")
        print(f"Response: {json.dumps(r.json(), indent=2)}")
        
        if r.status_code == 200:
            print("✅ Root health endpoint: PASS")
        else:
            print("❌ Root health endpoint: FAIL")
        
        print()
        
        # Test enhanced health endpoint
        r = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=10)
        print(f"GET /api/v1/health")
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check database type
        db_type = data.get('database_type', 'unknown')
        db_host = data.get('database_host', 'unknown')
        warning = data.get('warning')
        
        print(f"\n📊 Database Analysis:")
        print(f"  Type: {db_type}")
        print(f"  Host: {db_host}")
        
        if db_type == 'postgresql':
            print("  ✅ PostgreSQL ACTIVE")
            if 'supabase' in db_host:
                print("  ✅ Supabase host DETECTED")
            return True
        elif db_type == 'sqlite':
            print("  ❌ SQLite FALLBACK ACTIVE")
            if warning:
                print(f"  ⚠️  Warning: {warning}")
            print("  🚨 CRITICAL: DATABASE_URL not configured in Render!")
            return False
        else:
            print(f"  ❌ Unknown database type: {db_type}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_api_endpoints():
    print_section("TEST 2: API ENDPOINTS")
    
    endpoints = [
        ("GET", "/api/v1/health", None),
        ("POST", "/api/v1/signal", {
            "zone": "MZUZU",
            "activity_type": "irrigation",
            "time_window": "morning",
            "original_text": "Production verification test signal"
        }),
        ("GET", "/api/v1/signals?limit=5", None),
        ("GET", "/api/v1/summary/MZUZU", None),
    ]
    
    results = []
    
    for method, path, payload in endpoints:
        try:
            url = f"{BACKEND_URL}{path}"
            print(f"{method} {path}")
            
            if method == "GET":
                r = requests.get(url, timeout=30)
            else:
                r = requests.post(url, json=payload, timeout=30)
            
            print(f"  Status: {r.status_code}")
            
            if r.status_code == 200:
                print(f"  ✅ PASS")
                results.append(True)
            else:
                print(f"  ❌ FAIL")
                print(f"  Response: {r.text[:200]}")
                results.append(False)
            
            print()
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append(False)
            print()
    
    return all(results)

def test_frontend():
    print_section("TEST 4: FRONTEND LOAD TEST")
    
    try:
        r = requests.get(FRONTEND_URL, timeout=10)
        print(f"GET {FRONTEND_URL}")
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            print("✅ Frontend loads")
            
            # Check for key content
            html = r.text
            checks = [
                ("Kulima" in html, "Kulima branding present"),
                ("<!DOCTYPE html>" in html or "<html" in html, "Valid HTML"),
                ("script" in html.lower(), "JavaScript present"),
            ]
            
            for check, desc in checks:
                if check:
                    print(f"  ✅ {desc}")
                else:
                    print(f"  ❌ {desc}")
            
            return True
        else:
            print("❌ Frontend failed to load")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def generate_report():
    print_section("PRODUCTION VERIFICATION REPORT")
    print(f"Generated: {datetime.utcnow().isoformat()}Z\n")
    
    # Run all tests
    test1 = test_backend_health()
    test2 = test_api_endpoints()
    test4 = test_frontend()
    
    # Summary
    print_section("OVERALL STATUS")
    
    if test1 and test2 and test4:
        print("🟢 PRODUCTION READY")
        print("\nAll systems operational.")
    elif test2 and test4 and not test1:
        print("🟡 PARTIALLY WORKING")
        print("\n⚠️  Backend is using SQLite fallback instead of PostgreSQL")
        print("⚠️  DATABASE_URL environment variable not configured in Render")
    else:
        print("🔴 CRITICAL ISSUES PRESENT")
        print("\nMultiple systems failing.")
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"✅ Backend Online: {'PASS' if test2 else 'FAIL'}")
    print(f"{'✅' if test1 else '❌'} PostgreSQL Active: {'PASS' if test1 else 'FAIL - Using SQLite'}")
    print(f"✅ API Endpoints: {'PASS' if test2 else 'FAIL'}")
    print(f"✅ Frontend Load: {'PASS' if test4 else 'FAIL'}")
    
    if not test1:
        print("\n" + "=" * 60)
        print("🚨 CRITICAL FIX REQUIRED")
        print("=" * 60)
        print("\n1. Go to Render Dashboard")
        print("2. Select 'kulima-os-backend' service")
        print("3. Go to 'Environment' tab")
        print("4. Add environment variable:")
        print("\n   Key: DATABASE_URL")
        print("   Value: postgresql://postgres:Jolly@143!windows@db.tygpjeuifqzihmmpduzt.supabase.co:5432/postgres?sslmode=require")
        print("\n5. Save and wait for redeploy")
        print("6. Verify health endpoint shows 'database_type': 'postgresql'")

if __name__ == "__main__":
    generate_report()

# Made with Bob
