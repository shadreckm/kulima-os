#!/usr/bin/env python3
"""
Kulima OS End-to-End Verification
Complete system test from database to frontend
"""
import os
import sys
import json
import requests
from urllib.parse import urlparse
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError
import logging
from datetime import datetime
import uuid

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class KulimaE2ETest:
    """End-to-end test suite for Kulima OS"""
    
    def __init__(self):
        self.results = {
            'database': False,
            'backend': False,
            'frontend': False,
            'signal_storage': False,
            'supabase_connection': False,
            'evidence_layer': False
        }
        self.diagnostics = []
        self.test_signal_id = None
        
    def log(self, phase, message, status='INFO'):
        """Log test result"""
        timestamp = datetime.utcnow().isoformat()
        entry = f"[{timestamp}] [{phase}] {status}: {message}"
        self.diagnostics.append(entry)
        if status == 'ERROR':
            logger.error(f"{phase}: {message}")
        elif status == 'SUCCESS':
            logger.info(f"✅ {phase}: {message}")
        else:
            logger.info(f"{phase}: {message}")
    
    # PHASE 1: DATABASE VERIFICATION
    def phase1_database_verification(self):
        """Verify database connectivity and configuration"""
        self.log("PHASE 1", "Starting Database Verification", "INFO")
        
        # Read environment variables
        database_url = os.getenv('DATABASE_URL')
        secret_key = os.getenv('SECRET_KEY')
        cors_origins = os.getenv('CORS_ORIGINS')
        
        self.log("PHASE 1", f"DATABASE_URL: {'SET' if database_url else 'NOT SET'}", "INFO")
        self.log("PHASE 1", f"SECRET_KEY: {'SET' if secret_key else 'NOT SET'}", "INFO")
        self.log("PHASE 1", f"CORS_ORIGINS: {'SET' if cors_origins else 'NOT SET'}", "INFO")
        
        if not database_url:
            self.log("PHASE 1", "DATABASE_URL not set", "ERROR")
            return False
        
        try:
            # Normalize URL
            normalized_url = database_url
            if normalized_url.startswith('postgres://'):
                normalized_url = normalized_url.replace('postgres://', 'postgresql://', 1)
            
            # Parse URL
            parsed = urlparse(normalized_url)
            self.log("PHASE 1", f"Database Host: {parsed.hostname}", "INFO")
            self.log("PHASE 1", f"Database Port: {parsed.port}", "INFO")
            self.log("PHASE 1", f"Database Name: {parsed.path.lstrip('/')}", "INFO")
            
            # Create engine
            engine = create_engine(
                normalized_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 10}
            )
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    self.log("PHASE 1", "SELECT 1 test PASSED", "SUCCESS")
                else:
                    self.log("PHASE 1", "SELECT 1 test FAILED", "ERROR")
                    return False
                
                # Check permissions
                try:
                    conn.execute(text("SELECT current_user, current_database()"))
                    self.log("PHASE 1", "Database permissions OK", "SUCCESS")
                except Exception as e:
                    self.log("PHASE 1", f"Permission check failed: {e}", "ERROR")
                    return False
                
                # List tables
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                self.log("PHASE 1", f"Found {len(tables)} tables", "INFO")
                for table in tables:
                    self.log("PHASE 1", f"  - {table}", "INFO")
            
            self.results['database'] = True
            self.results['supabase_connection'] = True
            self.log("PHASE 1", "Database verification PASSED", "SUCCESS")
            return True
            
        except Exception as e:
            self.log("PHASE 1", f"Database verification FAILED: {e}", "ERROR")
            return False
    
    # PHASE 2: APPLICATION STARTUP
    def phase2_application_startup(self):
        """Verify application can start"""
        self.log("PHASE 2", "Starting Application Startup Verification", "INFO")
        
        try:
            # Check if main.py exists
            if not os.path.exists('backend/main.py'):
                self.log("PHASE 2", "backend/main.py not found", "ERROR")
                return False
            
            # Try to import main components
            sys.path.insert(0, os.getcwd())
            
            # Import database models
            from backend.database import models
            self.log("PHASE 2", "Imported backend.database.models", "SUCCESS")
            
            # Import evidence models
            from backend.database import evidence_models
            self.log("PHASE 2", "Imported backend.database.evidence_models", "SUCCESS")
            
            # Check for metadata conflicts
            from backend.database.evidence_models import Evidence, EvidenceAuditLog
            
            # Verify no 'metadata' column
            if hasattr(Evidence, '__table__'):
                columns = [col.name for col in Evidence.__table__.columns]
                if 'metadata' in columns:
                    self.log("PHASE 2", "Evidence model has 'metadata' column (CONFLICT)", "ERROR")
                    return False
                if 'evidence_metadata' in columns:
                    self.log("PHASE 2", "Evidence model uses 'evidence_metadata' (OK)", "SUCCESS")
            
            if hasattr(EvidenceAuditLog, '__table__'):
                columns = [col.name for col in EvidenceAuditLog.__table__.columns]
                if 'metadata' in columns:
                    self.log("PHASE 2", "EvidenceAuditLog has 'metadata' column (CONFLICT)", "ERROR")
                    return False
                if 'audit_metadata' in columns:
                    self.log("PHASE 2", "EvidenceAuditLog uses 'audit_metadata' (OK)", "SUCCESS")
            
            # Import API modules
            from backend.api import signals, evidence
            self.log("PHASE 2", "Imported API modules", "SUCCESS")
            
            self.results['backend'] = True
            self.log("PHASE 2", "Application startup verification PASSED", "SUCCESS")
            return True
            
        except ImportError as e:
            self.log("PHASE 2", f"Import error: {e}", "ERROR")
            return False
        except Exception as e:
            self.log("PHASE 2", f"Startup verification FAILED: {e}", "ERROR")
            return False
    
    # PHASE 3: API HEALTH
    def phase3_api_health(self, base_url="http://localhost:8000"):
        """Test API health endpoint"""
        self.log("PHASE 3", f"Testing API Health at {base_url}", "INFO")
        
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log("PHASE 3", f"Health response: {json.dumps(data)}", "INFO")
                
                if data.get('status') == 'OK':
                    self.log("PHASE 3", "API status: OK", "SUCCESS")
                else:
                    self.log("PHASE 3", f"API status: {data.get('status')}", "ERROR")
                    return False
                
                if data.get('database') == 'DB_CONNECTED':
                    self.log("PHASE 3", "Database status: CONNECTED", "SUCCESS")
                else:
                    self.log("PHASE 3", f"Database status: {data.get('database')}", "ERROR")
                    return False
                
                self.log("PHASE 3", "API health check PASSED", "SUCCESS")
                return True
            else:
                self.log("PHASE 3", f"Health endpoint returned {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.ConnectionError:
            self.log("PHASE 3", "Cannot connect to API (is it running?)", "ERROR")
            return False
        except Exception as e:
            self.log("PHASE 3", f"Health check FAILED: {e}", "ERROR")
            return False
    
    # PHASE 4: SIGNAL TEST
    def phase4_signal_test(self, base_url="http://localhost:8000"):
        """Submit test signal through API"""
        self.log("PHASE 4", "Testing Signal Submission", "INFO")
        
        try:
            # Create test signal
            test_signal = {
                "text": "stock out NPK fertilizer ekwendeni",
                "source": "test",
                "user_id": "test_user"
            }
            
            self.log("PHASE 4", f"Submitting signal: {test_signal['text']}", "INFO")
            
            response = requests.post(
                f"{base_url}/api/v1/signals",
                json=test_signal,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log("PHASE 4", f"Signal accepted: {json.dumps(data)}", "SUCCESS")
                
                # Extract signal ID
                if 'id' in data:
                    self.test_signal_id = data['id']
                    self.log("PHASE 4", f"Signal ID: {self.test_signal_id}", "INFO")
                
                # Verify normalization
                if 'zone' in data:
                    self.log("PHASE 4", f"EPA detected: {data['zone']}", "SUCCESS")
                
                if 'activity_type' in data:
                    self.log("PHASE 4", f"Activity type: {data['activity_type']}", "SUCCESS")
                
                self.results['signal_storage'] = True
                self.log("PHASE 4", "Signal test PASSED", "SUCCESS")
                return True
            else:
                self.log("PHASE 4", f"Signal submission failed: {response.status_code}", "ERROR")
                self.log("PHASE 4", f"Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log("PHASE 4", f"Signal test FAILED: {e}", "ERROR")
            return False
    
    # PHASE 5: DATABASE PERSISTENCE
    def phase5_database_persistence(self):
        """Verify signal was stored in database"""
        self.log("PHASE 5", "Verifying Database Persistence", "INFO")
        
        if not self.test_signal_id:
            self.log("PHASE 5", "No test signal ID available", "ERROR")
            return False
        
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                self.log("PHASE 5", "DATABASE_URL not set", "ERROR")
                return False
            
            # Normalize URL
            normalized_url = database_url
            if normalized_url.startswith('postgres://'):
                normalized_url = normalized_url.replace('postgres://', 'postgresql://', 1)
            
            engine = create_engine(normalized_url, pool_pre_ping=True)
            
            with engine.connect() as conn:
                # Query for the signal
                result = conn.execute(
                    text("SELECT * FROM signals WHERE id = :signal_id"),
                    {"signal_id": self.test_signal_id}
                )
                
                row = result.fetchone()
                
                if row:
                    self.log("PHASE 5", "Signal found in database", "SUCCESS")
                    self.log("PHASE 5", f"  ID: {row[0]}", "INFO")
                    self.log("PHASE 5", f"  Zone: {row[1]}", "INFO")
                    self.log("PHASE 5", f"  Activity: {row[2]}", "INFO")
                    self.log("PHASE 5", f"  Created: {row[8]}", "INFO")
                    
                    self.log("PHASE 5", "Database persistence PASSED", "SUCCESS")
                    return True
                else:
                    self.log("PHASE 5", "Signal NOT found in database", "ERROR")
                    return False
                    
        except Exception as e:
            self.log("PHASE 5", f"Database persistence check FAILED: {e}", "ERROR")
            return False
    
    # PHASE 6: FRONTEND CONNECTIVITY
    def phase6_frontend_connectivity(self, frontend_url="http://localhost:3000"):
        """Test frontend connectivity"""
        self.log("PHASE 6", f"Testing Frontend Connectivity at {frontend_url}", "INFO")
        
        try:
            response = requests.get(frontend_url, timeout=10)
            
            if response.status_code == 200:
                self.log("PHASE 6", "Frontend is reachable", "SUCCESS")
                self.results['frontend'] = True
                return True
            else:
                self.log("PHASE 6", f"Frontend returned {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.ConnectionError:
            self.log("PHASE 6", "Cannot connect to frontend (is it running?)", "ERROR")
            return False
        except Exception as e:
            self.log("PHASE 6", f"Frontend connectivity FAILED: {e}", "ERROR")
            return False
    
    # PHASE 7: EVIDENCE LAYER
    def phase7_evidence_layer(self, base_url="http://localhost:8000"):
        """Verify Evidence Intelligence Layer"""
        self.log("PHASE 7", "Testing Evidence Intelligence Layer", "INFO")
        
        try:
            # Test evidence API endpoint
            response = requests.get(
                f"{base_url}/api/v1/evidence/zone/test_zone",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("PHASE 7", "Evidence API endpoint accessible", "SUCCESS")
                self.log("PHASE 7", f"Response: {json.dumps(data)}", "INFO")
                
                self.results['evidence_layer'] = True
                self.log("PHASE 7", "Evidence layer PASSED", "SUCCESS")
                return True
            else:
                self.log("PHASE 7", f"Evidence API returned {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log("PHASE 7", f"Evidence layer test FAILED: {e}", "ERROR")
            return False
    
    # PHASE 8: END-TO-END TEST
    def phase8_end_to_end_test(self, base_url="http://localhost:8000"):
        """Complete end-to-end flow test"""
        self.log("PHASE 8", "Running End-to-End Test", "INFO")
        
        try:
            # Submit Chichewa signal
            test_signal = {
                "text": "mbewu palibe rumphi",
                "source": "test_e2e",
                "user_id": "test_user"
            }
            
            self.log("PHASE 8", f"Submitting: {test_signal['text']}", "INFO")
            
            # Step 1: Submit to API
            response = requests.post(
                f"{base_url}/api/v1/signals",
                json=test_signal,
                timeout=10
            )
            
            if response.status_code not in [200, 201]:
                self.log("PHASE 8", f"API submission failed: {response.status_code}", "ERROR")
                return False
            
            data = response.json()
            signal_id = data.get('id')
            self.log("PHASE 8", f"✓ Signal submitted (ID: {signal_id})", "SUCCESS")
            
            # Step 2: Verify in database
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                normalized_url = database_url
                if normalized_url.startswith('postgres://'):
                    normalized_url = normalized_url.replace('postgres://', 'postgresql://', 1)
                
                engine = create_engine(normalized_url, pool_pre_ping=True)
                
                with engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT * FROM signals WHERE id = :signal_id"),
                        {"signal_id": signal_id}
                    )
                    
                    if result.fetchone():
                        self.log("PHASE 8", "✓ Signal stored in database", "SUCCESS")
                    else:
                        self.log("PHASE 8", "✗ Signal NOT in database", "ERROR")
                        return False
            
            # Step 3: Retrieve via API
            response = requests.get(
                f"{base_url}/api/v1/signals/recent?limit=10",
                timeout=10
            )
            
            if response.status_code == 200:
                signals = response.json()
                found = any(s.get('id') == signal_id for s in signals)
                if found:
                    self.log("PHASE 8", "✓ Signal retrievable via API", "SUCCESS")
                else:
                    self.log("PHASE 8", "✗ Signal not in recent signals", "ERROR")
                    return False
            
            self.log("PHASE 8", "End-to-end test PASSED", "SUCCESS")
            return True
            
        except Exception as e:
            self.log("PHASE 8", f"End-to-end test FAILED: {e}", "ERROR")
            return False
    
    # PHASE 9: RENDER DEPLOYMENT
    def phase9_render_deployment(self):
        """Test production deployment"""
        self.log("PHASE 9", "Testing Render Deployment", "INFO")
        
        backend_url = "https://kulima-os-backend.onrender.com"
        frontend_url = "https://kulima-os.vercel.app"
        
        # Test backend
        try:
            response = requests.get(f"{backend_url}/health", timeout=15)
            if response.status_code == 200:
                self.log("PHASE 9", "✓ Backend is live", "SUCCESS")
            else:
                self.log("PHASE 9", f"Backend returned {response.status_code}", "ERROR")
        except Exception as e:
            self.log("PHASE 9", f"Backend unreachable: {e}", "ERROR")
        
        # Test backend docs
        try:
            response = requests.get(f"{backend_url}/docs", timeout=15)
            if response.status_code == 200:
                self.log("PHASE 9", "✓ API docs accessible", "SUCCESS")
        except Exception as e:
            self.log("PHASE 9", f"API docs unreachable: {e}", "ERROR")
        
        # Test frontend
        try:
            response = requests.get(frontend_url, timeout=15)
            if response.status_code == 200:
                self.log("PHASE 9", "✓ Frontend is live", "SUCCESS")
            else:
                self.log("PHASE 9", f"Frontend returned {response.status_code}", "ERROR")
        except Exception as e:
            self.log("PHASE 9", f"Frontend unreachable: {e}", "ERROR")
        
        return True
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "=" * 60)
        print("KULIMA OS END-TO-END TEST REPORT")
        print("=" * 60)
        print()
        
        print("DATABASE STATUS:")
        print(f"  {'✅' if self.results['database'] else '❌'} Database Connection")
        print()
        
        print("BACKEND STATUS:")
        print(f"  {'✅' if self.results['backend'] else '❌'} Application Startup")
        print()
        
        print("FRONTEND STATUS:")
        print(f"  {'✅' if self.results['frontend'] else '❌'} Frontend Connectivity")
        print()
        
        print("SIGNAL STORAGE:")
        print(f"  {'✅' if self.results['signal_storage'] else '❌'} Signal Submission & Storage")
        print()
        
        print("SUPABASE CONNECTION:")
        print(f"  {'✅' if self.results['supabase_connection'] else '❌'} Supabase PostgreSQL")
        print()
        
        print("EVIDENCE LAYER:")
        print(f"  {'✅' if self.results['evidence_layer'] else '❌'} Evidence Intelligence Layer")
        print()
        
        all_passed = all(self.results.values())
        
        print("=" * 60)
        print(f"OVERALL STATUS: {'🟢 GO' if all_passed else '🔴 NO-GO'}")
        print("=" * 60)
        print()
        
        if not all_passed:
            print("FAILED COMPONENTS:")
            for component, status in self.results.items():
                if not status:
                    print(f"  ❌ {component}")
            print()
        
        print("DETAILED DIAGNOSTICS:")
        print("-" * 60)
        for entry in self.diagnostics:
            print(entry)
        print()
        
        return all_passed


def main():
    """Run all tests"""
    tester = KulimaE2ETest()
    
    # Run all phases
    tester.phase1_database_verification()
    tester.phase2_application_startup()
    
    # Check if backend is running
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
    
    if tester.phase3_api_health(backend_url):
        tester.phase4_signal_test(backend_url)
        tester.phase5_database_persistence()
        tester.phase7_evidence_layer(backend_url)
        tester.phase8_end_to_end_test(backend_url)
    
    # Test frontend if URL provided
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    tester.phase6_frontend_connectivity(frontend_url)
    
    # Test production deployment
    tester.phase9_render_deployment()
    
    # Generate report
    all_passed = tester.generate_report()
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

# Made with Bob
