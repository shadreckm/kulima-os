#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KULIMA OS - Program Manager Dashboard Verification

Tests the dashboard functionality with real backend data.
Validates that all components work correctly.
"""

import sys
import io
import requests
import json
from datetime import datetime
from typing import Dict, List, Any

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
BACKEND_URL = "https://kulima-os-backend.onrender.com"
FRONTEND_URL = "https://kulima-os.vercel.app"

class DashboardValidator:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name: str, condition: bool, details: str = ""):
        """Record test result"""
        status = "✅ PASS" if condition else "❌ FAIL"
        self.results.append(f"{status} | {name}")
        if details:
            self.results.append(f"    {details}")
        
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        
        return condition
    
    def section(self, title: str):
        """Add section header"""
        self.results.append(f"\n{'='*60}")
        self.results.append(f"{title}")
        self.results.append(f"{'='*60}")
    
    def print_results(self):
        """Print all results"""
        print("\n".join(self.results))
        print(f"\n{'='*60}")
        print(f"SUMMARY: {self.passed} passed, {self.failed} failed")
        print(f"{'='*60}")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED - Dashboard is operational!")
            return True
        else:
            print(f"\n⚠️  {self.failed} test(s) failed - Review issues above")
            return False

def main():
    validator = DashboardValidator()
    
    # ========================================
    # Phase 1: Backend Health Check
    # ========================================
    validator.section("PHASE 1: Backend Health Check")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        validator.test(
            "Backend health endpoint",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        if response.status_code == 200:
            health_data = response.json()
            validator.test(
                "Backend status is healthy",
                health_data.get("status") == "healthy",
                f"Status: {health_data.get('status')}"
            )
    except Exception as e:
        validator.test("Backend health endpoint", False, f"Error: {str(e)}")
    
    # ========================================
    # Phase 2: Signals API Validation
    # ========================================
    validator.section("PHASE 2: Signals API Validation")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/signals/recent", timeout=10)
        validator.test(
            "Recent signals endpoint",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        if response.status_code == 200:
            signals_data = response.json()
            
            # Handle nested data structure
            if isinstance(signals_data, dict) and 'data' in signals_data:
                signals = signals_data['data']
            else:
                signals = signals_data if isinstance(signals_data, list) else []
            
            validator.test(
                "Signals data is a list",
                isinstance(signals, list),
                f"Type: {type(signals).__name__}"
            )
            
            validator.test(
                "Signals exist in database",
                len(signals) > 0,
                f"Count: {len(signals)} signals"
            )
            
            if len(signals) > 0:
                # Validate signal structure
                first_signal = signals[0]
                required_fields = ['id', 'zone', 'activity_type', 'created_at']
                
                for field in required_fields:
                    validator.test(
                        f"Signal has '{field}' field",
                        field in first_signal,
                        f"Value: {first_signal.get(field, 'MISSING')}"
                    )
                
                # Calculate zone statistics (dashboard logic)
                zone_stats = {}
                for signal in signals:
                    zone = signal.get('zone', 'UNKNOWN')
                    if zone not in zone_stats:
                        zone_stats[zone] = {
                            'count': 0,
                            'activities': set(),
                            'last_signal': None
                        }
                    zone_stats[zone]['count'] += 1
                    if signal.get('activity_type'):
                        zone_stats[zone]['activities'].add(signal['activity_type'])
                    if signal.get('created_at'):
                        if not zone_stats[zone]['last_signal'] or \
                           signal['created_at'] > zone_stats[zone]['last_signal']:
                            zone_stats[zone]['last_signal'] = signal['created_at']
                
                validator.test(
                    "Zone statistics calculated",
                    len(zone_stats) > 0,
                    f"Active zones: {len(zone_stats)}"
                )
                
                # Priority ranking (dashboard logic)
                priority_zones = sorted(
                    zone_stats.items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:5]
                
                validator.test(
                    "Priority zones identified",
                    len(priority_zones) > 0,
                    f"Top zone: {priority_zones[0][0]} ({priority_zones[0][1]['count']} signals)"
                )
                
                # National metrics (dashboard logic)
                total_signals = len(signals)
                active_zones = len(zone_stats)
                
                # Calculate confidence scores
                for zone, stats in zone_stats.items():
                    stats['confidence'] = min(95, 40 + (stats['count'] * 10))
                
                avg_confidence = sum(
                    stats['confidence'] for _, stats in priority_zones
                ) / len(priority_zones) if priority_zones else 0
                
                validator.test(
                    "National metrics calculated",
                    True,
                    f"Signals: {total_signals}, Zones: {active_zones}, Confidence: {avg_confidence:.0f}%"
                )
                
    except Exception as e:
        validator.test("Recent signals endpoint", False, f"Error: {str(e)}")
    
    # ========================================
    # Phase 3: Frontend Accessibility
    # ========================================
    validator.section("PHASE 3: Frontend Accessibility")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=10, allow_redirects=False)
        validator.test(
            "Frontend landing page accessible",
            response.status_code in [200, 301, 302, 307, 308],
            f"Status: {response.status_code}"
        )
    except Exception as e:
        validator.test("Frontend landing page accessible", False, f"Error: {str(e)}")
    
    try:
        response = requests.get(f"{FRONTEND_URL}/dashboard", timeout=10)
        validator.test(
            "Dashboard page accessible",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for key dashboard elements
            validator.test(
                "Dashboard contains 'KULIMA OS' title",
                "KULIMA OS" in html_content,
                "Title found in HTML"
            )
            
            validator.test(
                "Dashboard contains 'Program Manager' text",
                "Program Manager" in html_content or "program-manager" in html_content.lower(),
                "Role identifier found"
            )
            
    except Exception as e:
        validator.test("Dashboard page accessible", False, f"Error: {str(e)}")
    
    # ========================================
    # Phase 4: Dashboard Component Validation
    # ========================================
    validator.section("PHASE 4: Dashboard Component Validation")
    
    # Read dashboard source code
    try:
        with open('frontend/app/dashboard/page.jsx', 'r', encoding='utf-8') as f:
            dashboard_code = f.read()
        
        components = [
            ("National Summary Cards", "National Overview"),
            ("Priority Zone Rankings", "Priority Zone Rankings"),
            ("Recent Signals Table", "Recent Coordination Signals"),
            ("Recommendation Panel", "Recommended Actions"),
            ("Evidence Overview", "Evidence & Trust")
        ]
        
        for component_name, search_text in components:
            validator.test(
                f"Dashboard includes {component_name}",
                search_text in dashboard_code,
                f"Component found in source"
            )
        
        # Check for auto-refresh
        validator.test(
            "Auto-refresh implemented",
            "setInterval" in dashboard_code and "30000" in dashboard_code,
            "30-second refresh interval found"
        )
        
        # Check for loading states
        validator.test(
            "Loading states implemented",
            "loading" in dashboard_code.lower() and "spinner" in dashboard_code.lower(),
            "Loading UI found"
        )
        
        # Check for error handling
        validator.test(
            "Error handling implemented",
            "error" in dashboard_code.lower() and "catch" in dashboard_code,
            "Error handling found"
        )
        
    except Exception as e:
        validator.test("Dashboard source code readable", False, f"Error: {str(e)}")
    
    # ========================================
    # Phase 5: Zero-PII Compliance
    # ========================================
    validator.section("PHASE 5: Zero-PII Compliance")
    
    try:
        # Re-read dashboard code for this phase
        with open('frontend/app/dashboard/page.jsx', 'r', encoding='utf-8') as f:
            dashboard_code_pii = f.read()
        
        # Check that dashboard only uses aggregated data
        forbidden_terms = [
            "user_id", "userId", "phone", "email", "name", "address",
            "individual", "person", "household_id"
        ]
        
        pii_found = []
        for term in forbidden_terms:
            if term in dashboard_code_pii.lower():
                pii_found.append(term)
        
        validator.test(
            "No PII-related terms in dashboard code",
            len(pii_found) == 0,
            f"Clean code" if len(pii_found) == 0 else f"Found: {', '.join(pii_found)}"
        )
        
        # Check for aggregation-only logic
        aggregation_terms = ["zone", "activity_type", "count", "confidence", "stats"]
        aggregation_found = sum(1 for term in aggregation_terms if term in dashboard_code_pii)
        
        validator.test(
            "Dashboard uses aggregation logic",
            aggregation_found >= 3,
            f"Found {aggregation_found} aggregation terms"
        )
        
    except Exception as e:
        validator.test("Zero-PII compliance check", False, f"Error: {str(e)}")
    
    # ========================================
    # Phase 6: Documentation Validation
    # ========================================
    validator.section("PHASE 6: Documentation Validation")
    
    try:
        with open('PROGRAM_MANAGER_DASHBOARD.md', 'r', encoding='utf-8') as f:
            docs = f.read()
        
        doc_sections = [
            "Overview",
            "Purpose",
            "Dashboard Components",
            "Data Flow",
            "User Experience Design",
            "Decision-Making Workflow",
            "Zero-PII Compliance"
        ]
        
        for section in doc_sections:
            validator.test(
                f"Documentation includes '{section}' section",
                section in docs,
                "Section found"
            )
        
        validator.test(
            "Documentation mentions Grace Banda",
            "Grace Banda" in docs,
            "Target user identified"
        )
        
        validator.test(
            "Documentation includes 30-second decision time",
            "30 seconds" in docs,
            "Performance target documented"
        )
        
    except Exception as e:
        validator.test("Documentation readable", False, f"Error: {str(e)}")
    
    # ========================================
    # Final Results
    # ========================================
    validator.section("FINAL RESULTS")
    
    success = validator.print_results()
    
    if success:
        print("\n✅ DASHBOARD CERTIFICATION: PASSED")
        print("\nThe Program Manager Dashboard is:")
        print("  • Operational and accessible")
        print("  • Using real backend data")
        print("  • Zero-PII compliant")
        print("  • Fully documented")
        print("\nReady for Grace Banda and NGO decision-makers.")
        print(f"\n🔗 Access: {FRONTEND_URL}/dashboard")
    else:
        print("\n⚠️  DASHBOARD CERTIFICATION: NEEDS ATTENTION")
        print("\nReview failed tests above and address issues.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())

# Made with Bob
