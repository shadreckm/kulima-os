#!/usr/bin/env python3
"""
Test PostgreSQL connection with the current configuration
"""
import os
import sys

# Load .env file
from pathlib import Path
env_path = Path(".env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

print("=" * 60)
print("PostgreSQL Connection Test")
print("=" * 60)

# Check DATABASE_URL
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ DATABASE_URL not found in environment")
    sys.exit(1)

# Mask password for display
masked_url = db_url
if "@" in masked_url:
    parts = masked_url.split("@")
    prefix_parts = parts[0].split(":")
    if len(prefix_parts) >= 3:
        masked_url = f"{prefix_parts[0]}:{prefix_parts[1]}:****@{parts[1]}"

print(f"\n✅ DATABASE_URL loaded: {masked_url}")

# Test psycopg2 import
try:
    import psycopg2
    print("✅ psycopg2 module available")
except ImportError as e:
    print(f"❌ psycopg2 not available: {e}")
    sys.exit(1)

# Test SQLAlchemy connection
try:
    from sqlalchemy import create_engine, text
    
    # Normalize URL
    url = db_url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "sslmode=" not in url:
        url = f"{url}?sslmode=require"
    
    print(f"\n🔄 Creating SQLAlchemy engine...")
    engine = create_engine(url, pool_pre_ping=True)
    
    print("🔄 Testing connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ PostgreSQL connection successful!")
        print(f"✅ Version: {version}")
        
        # Get current database
        result = conn.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        print(f"✅ Database: {db_name}")
        
        # Extract host
        if "@" in str(engine.url):
            host_part = str(engine.url).split("@")[1]
            db_host = host_part.split("/")[0].split(":")[0]
            print(f"✅ Host: {db_host}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - PostgreSQL is ready!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check DATABASE_URL is correct")
    print("2. Verify network connectivity to database host")
    print("3. Confirm database credentials are valid")
    print("4. Check firewall/security group settings")
    sys.exit(1)

# Made with Bob
