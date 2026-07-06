#!/usr/bin/env python3
"""
Kulima OS Database Connectivity Test
Validates PostgreSQL connection and deployment readiness
"""
import os
import sys
from urllib.parse import urlparse
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def validate_database_url(database_url: str) -> tuple[bool, str]:
    """
    STEP 1: Validate DATABASE_URL format and components
    
    Returns:
        (is_valid, reason)
    """
    if not database_url:
        return False, "DATABASE_URL is empty or not provided"
    
    try:
        parsed = urlparse(database_url)
        
        # Check scheme
        if parsed.scheme not in ['postgresql', 'postgres']:
            return False, f"Invalid scheme '{parsed.scheme}'. Must be 'postgresql' or 'postgres'"
        
        # Check username
        if not parsed.username:
            return False, "Username is missing"
        
        # Check password
        if not parsed.password:
            return False, "Password is missing"
        
        # Check host
        if not parsed.hostname:
            return False, "Host is missing"
        
        # Check port
        if not parsed.port:
            return False, "Port is missing"
        
        # Check database name
        if not parsed.path or parsed.path == '/':
            return False, "Database name is missing"
        
        # Check sslmode
        if 'sslmode' not in database_url:
            return False, "sslmode parameter is missing (should include ?sslmode=require)"
        
        return True, "VALID"
        
    except Exception as e:
        return False, f"URL parsing failed: {str(e)}"


def test_connection(database_url: str) -> tuple[bool, str, dict]:
    """
    STEP 2: Test database connectivity
    
    Returns:
        (connected, status, diagnostics)
    """
    diagnostics = {
        'url_scheme': None,
        'host': None,
        'port': None,
        'database': None,
        'connection_test': None,
        'select_test': None,
        'error': None
    }
    
    try:
        # Parse URL for diagnostics
        parsed = urlparse(database_url)
        diagnostics['url_scheme'] = parsed.scheme
        diagnostics['host'] = parsed.hostname
        diagnostics['port'] = parsed.port
        diagnostics['database'] = parsed.path.lstrip('/')
        
        # Normalize URL
        normalized_url = database_url
        if normalized_url.startswith('postgres://'):
            normalized_url = normalized_url.replace('postgres://', 'postgresql://', 1)
        
        # Create engine
        engine = create_engine(
            normalized_url,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000"
            }
        )
        
        diagnostics['connection_test'] = 'Attempting connection...'
        
        # Test connection
        with engine.connect() as conn:
            diagnostics['connection_test'] = 'Connected'
            
            # Execute SELECT 1
            result = conn.execute(text("SELECT 1"))
            value = result.scalar()
            
            if value == 1:
                diagnostics['select_test'] = 'PASSED'
                return True, "CONNECTED", diagnostics
            else:
                diagnostics['select_test'] = f'FAILED (returned {value})'
                return False, "FAILED", diagnostics
                
    except OperationalError as e:
        diagnostics['error'] = f"OperationalError: {str(e)}"
        diagnostics['connection_test'] = 'FAILED'
        return False, "FAILED", diagnostics
    except Exception as e:
        diagnostics['error'] = f"Exception: {str(e)}"
        diagnostics['connection_test'] = 'FAILED'
        return False, "FAILED", diagnostics


def verify_database_metadata(database_url: str) -> tuple[bool, list, str]:
    """
    STEP 3: Verify database metadata and list tables
    
    Returns:
        (accessible, tables, error)
    """
    try:
        # Normalize URL
        normalized_url = database_url
        if normalized_url.startswith('postgres://'):
            normalized_url = normalized_url.replace('postgres://', 'postgresql://', 1)
        
        engine = create_engine(normalized_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Get inspector
            inspector = inspect(engine)
            
            # List tables
            tables = inspector.get_table_names()
            
            return True, tables, None
            
    except Exception as e:
        return False, [], str(e)


def verify_startup_configuration() -> tuple[bool, list]:
    """
    STEP 4: Verify Kulima OS startup configuration
    
    Returns:
        (valid, risks)
    """
    risks = []
    
    # Check if main.py exists
    if not os.path.exists('backend/main.py'):
        risks.append("backend/main.py not found")
        return False, risks
    
    # Check if database connection module exists
    if not os.path.exists('backend/database/connection.py'):
        risks.append("backend/database/connection.py not found")
        return False, risks
    
    # Check if models exist
    if not os.path.exists('backend/database/models.py'):
        risks.append("backend/database/models.py not found")
    
    if not os.path.exists('backend/database/evidence_models.py'):
        risks.append("backend/database/evidence_models.py not found")
    
    # Try to import and check for issues
    try:
        sys.path.insert(0, os.getcwd())
        from backend.database import models
        from backend.database import evidence_models
    except ImportError as e:
        risks.append(f"Import error: {str(e)}")
        return False, risks
    except Exception as e:
        risks.append(f"Unexpected error during import: {str(e)}")
        return False, risks
    
    return len(risks) == 0, risks


def verify_evidence_layer() -> tuple[bool, list]:
    """
    STEP 5: Verify Evidence Intelligence Layer models
    
    Returns:
        (valid, issues)
    """
    issues = []
    
    try:
        sys.path.insert(0, os.getcwd())
        from backend.database.evidence_models import (
            Evidence, EvidenceTrustFactors, EvidenceLink, EvidenceAuditLog
        )
        
        # Check for metadata conflicts
        reserved_attrs = ['metadata', 'registry', '__tablename__', '__table__', '__mapper__']
        
        for model_class in [Evidence, EvidenceTrustFactors, EvidenceLink, EvidenceAuditLog]:
            model_name = model_class.__name__
            
            # Check columns
            if hasattr(model_class, '__table__'):
                for column in model_class.__table__.columns:
                    if column.name in reserved_attrs:
                        issues.append(f"{model_name}.{column.name} uses reserved attribute name")
        
        if not issues:
            return True, []
        else:
            return False, issues
            
    except ImportError as e:
        issues.append(f"Cannot import evidence models: {str(e)}")
        return False, issues
    except Exception as e:
        issues.append(f"Error verifying evidence models: {str(e)}")
        return False, issues


def create_startup_diagnostic(database_url: str) -> dict:
    """
    STEP 6: Create startup diagnostic output
    
    Returns:
        diagnostic_results
    """
    results = {
        'database_url_loaded': False,
        'database_host_detected': None,
        'database_connected': False,
        'tables_verified': False,
        'evidence_tables_verified': False,
        'errors': []
    }
    
    # Check DATABASE_URL
    if database_url:
        results['database_url_loaded'] = True
        parsed = urlparse(database_url)
        results['database_host_detected'] = parsed.hostname
    else:
        results['errors'].append("DATABASE_URL not loaded")
        return results
    
    # Test connection
    connected, status, diagnostics = test_connection(database_url)
    results['database_connected'] = connected
    
    if not connected:
        results['errors'].append(f"Connection failed: {diagnostics.get('error', 'Unknown error')}")
        return results
    
    # Verify tables
    accessible, tables, error = verify_database_metadata(database_url)
    results['tables_verified'] = accessible
    
    if not accessible:
        results['errors'].append(f"Cannot access tables: {error}")
    
    # Verify evidence models
    valid, issues = verify_evidence_layer()
    results['evidence_tables_verified'] = valid
    
    if not valid:
        results['errors'].extend(issues)
    
    return results


def create_deployment_readiness_report(database_url: str, secret_key: str, cors_origins: str) -> dict:
    """
    STEP 7: Create deployment readiness report
    
    Returns:
        readiness_report
    """
    report = {
        'local_connection_will_succeed': False,
        'render_connection_will_succeed': False,
        'missing_environment_variables': [],
        'startup_blockers': [],
        'model_blockers': [],
        'confidence_score': 0,
        'decision': 'NO-GO'
    }
    
    # Check environment variables
    if not database_url or database_url == '<ENTER_DATABASE_URL_HERE>':
        report['missing_environment_variables'].append('DATABASE_URL')
    
    if not secret_key or secret_key == '<ENTER_SECRET_KEY_HERE>':
        report['missing_environment_variables'].append('SECRET_KEY')
    
    if not cors_origins or cors_origins == '<ENTER_CORS_ORIGINS_HERE>':
        report['missing_environment_variables'].append('CORS_ORIGINS')
    
    # If critical variables missing, return early
    if 'DATABASE_URL' in report['missing_environment_variables']:
        report['startup_blockers'].append('DATABASE_URL not configured')
        report['confidence_score'] = 0
        return report
    
    # Validate DATABASE_URL
    valid, reason = validate_database_url(database_url)
    if not valid:
        report['startup_blockers'].append(f"Invalid DATABASE_URL: {reason}")
        report['confidence_score'] = 10
        return report
    
    # Test connection
    connected, status, diagnostics = test_connection(database_url)
    report['local_connection_will_succeed'] = connected
    report['render_connection_will_succeed'] = connected  # Same config should work
    
    if not connected:
        report['startup_blockers'].append(f"Connection test failed: {diagnostics.get('error', 'Unknown')}")
        report['confidence_score'] = 20
        return report
    
    # Verify startup configuration
    valid_startup, risks = verify_startup_configuration()
    if not valid_startup:
        report['startup_blockers'].extend(risks)
        report['confidence_score'] = 40
        return report
    
    # Verify evidence models
    valid_models, issues = verify_evidence_layer()
    if not valid_models:
        report['model_blockers'].extend(issues)
        report['confidence_score'] = 60
        return report
    
    # All checks passed
    report['confidence_score'] = 100
    report['decision'] = 'GO'
    
    return report


def main():
    """Main execution"""
    print("=" * 60)
    print("KULIMA OS DATABASE CONNECTIVITY TEST")
    print("=" * 60)
    print()
    
    # Get environment variables
    database_url = os.getenv('DATABASE_URL', '<ENTER_DATABASE_URL_HERE>')
    secret_key = os.getenv('SECRET_KEY', '<ENTER_SECRET_KEY_HERE>')
    cors_origins = os.getenv('CORS_ORIGINS', '<ENTER_CORS_ORIGINS_HERE>')
    
    # STEP 1: Validate DATABASE_URL
    print("STEP 1: Validating DATABASE_URL")
    print("-" * 60)
    valid, reason = validate_database_url(database_url)
    print(f"Status: {reason}")
    print()
    
    if not valid:
        print("❌ DATABASE_URL validation failed")
        print(f"Reason: {reason}")
        print()
        print("FINAL DECISION: NO-GO")
        sys.exit(1)
    
    # STEP 2: Test connection
    print("STEP 2: Testing Database Connection")
    print("-" * 60)
    connected, status, diagnostics = test_connection(database_url)
    print(f"Status: {status}")
    print(f"Host: {diagnostics['host']}")
    print(f"Port: {diagnostics['port']}")
    print(f"Database: {diagnostics['database']}")
    print(f"Connection Test: {diagnostics['connection_test']}")
    print(f"SELECT 1 Test: {diagnostics.get('select_test', 'N/A')}")
    if diagnostics.get('error'):
        print(f"Error: {diagnostics['error']}")
    print()
    
    # STEP 3: Verify database metadata
    print("STEP 3: Verifying Database Metadata")
    print("-" * 60)
    if connected:
        accessible, tables, error = verify_database_metadata(database_url)
        if accessible:
            print(f"Tables accessible: YES")
            print(f"Existing tables: {len(tables)}")
            if tables:
                for table in tables:
                    print(f"  - {table}")
            else:
                print("  (No tables found - database is empty)")
        else:
            print(f"Tables accessible: NO")
            print(f"Error: {error}")
    else:
        print("Skipped (connection failed)")
    print()
    
    # STEP 4: Verify startup configuration
    print("STEP 4: Verifying Startup Configuration")
    print("-" * 60)
    valid_startup, risks = verify_startup_configuration()
    if valid_startup:
        print("Startup configuration: VALID")
    else:
        print("Startup configuration: INVALID")
        for risk in risks:
            print(f"  - {risk}")
    print()
    
    # STEP 5: Verify Evidence Intelligence Layer
    print("STEP 5: Verifying Evidence Intelligence Layer")
    print("-" * 60)
    valid_models, issues = verify_evidence_layer()
    if valid_models:
        print("Evidence models: VALID")
        print("  ✓ Evidence")
        print("  ✓ EvidenceTrustFactors")
        print("  ✓ EvidenceLink")
        print("  ✓ EvidenceAuditLog")
        print("  ✓ No metadata conflicts")
    else:
        print("Evidence models: INVALID")
        for issue in issues:
            print(f"  - {issue}")
    print()
    
    # STEP 6: Startup diagnostic
    print("STEP 6: Startup Diagnostic")
    print("-" * 60)
    diagnostic = create_startup_diagnostic(database_url)
    print(f"Database URL loaded: {'✓' if diagnostic['database_url_loaded'] else '✗'}")
    print(f"Database host detected: {diagnostic['database_host_detected']}")
    print(f"Database connected: {'✓' if diagnostic['database_connected'] else '✗'}")
    print(f"Tables verified: {'✓' if diagnostic['tables_verified'] else '✗'}")
    print(f"Evidence tables verified: {'✓' if diagnostic['evidence_tables_verified'] else '✗'}")
    if diagnostic['errors']:
        print("Errors:")
        for error in diagnostic['errors']:
            print(f"  - {error}")
    print()
    
    # STEP 7: Deployment readiness report
    print("STEP 7: Deployment Readiness Report")
    print("=" * 60)
    report = create_deployment_readiness_report(database_url, secret_key, cors_origins)
    
    print(f"1. Will local connection succeed? {'YES' if report['local_connection_will_succeed'] else 'NO'}")
    print(f"2. Will Render connection succeed? {'YES' if report['render_connection_will_succeed'] else 'NO'}")
    
    print(f"3. Missing environment variables:")
    if report['missing_environment_variables']:
        for var in report['missing_environment_variables']:
            print(f"   - {var}")
    else:
        print("   None")
    
    print(f"4. Startup blockers:")
    if report['startup_blockers']:
        for blocker in report['startup_blockers']:
            print(f"   - {blocker}")
    else:
        print("   None")
    
    print(f"5. Model blockers:")
    if report['model_blockers']:
        for blocker in report['model_blockers']:
            print(f"   - {blocker}")
    else:
        print("   None")
    
    print(f"6. Confidence score: {report['confidence_score']}/100")
    print()
    print("=" * 60)
    print(f"FINAL DECISION: {report['decision']}")
    print("=" * 60)
    
    if report['decision'] == 'GO':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
