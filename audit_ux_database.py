"""
KULIMA OS - UX & DATABASE AUDIT
================================

Audit what data exists vs what is displayed
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def audit_database():
    """Audit database content"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("="*80)
    print("DATABASE CONTENT AUDIT")
    print("="*80)
    
    # Recent signals
    print("\n=== RECENT SIGNALS (Last 10) ===")
    cur.execute("""
        SELECT id, zone, created_at, source, raw_text 
        FROM signals 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    signals = cur.fetchall()
    
    for s in signals:
        print(f"ID: {s['id'][:20]}")
        print(f"  Zone: {s['zone']}")
        print(f"  Created: {s['created_at']}")
        print(f"  Source: {s['source']}")
        print(f"  Text: {s.get('raw_text', 'N/A')[:50]}")
        print()
    
    # Signals by zone
    print("\n=== SIGNALS BY ZONE ===")
    cur.execute("""
        SELECT COUNT(*) as total, zone 
        FROM signals 
        GROUP BY zone 
        ORDER BY total DESC
    """)
    zones = cur.fetchall()
    
    for z in zones:
        print(f"{z['zone']:15} : {z['total']} signals")
    
    # Signals by source
    print("\n=== SIGNALS BY SOURCE ===")
    cur.execute("""
        SELECT COUNT(*) as total, source 
        FROM signals 
        GROUP BY source 
        ORDER BY total DESC
    """)
    sources = cur.fetchall()
    
    for s in sources:
        print(f"{s['source']:30} : {s['total']} signals")
    
    # Check for patterns
    print("\n=== PATTERNS TABLE ===")
    cur.execute("SELECT COUNT(*) as total FROM patterns")
    pattern_count = cur.fetchone()
    print(f"Total patterns: {pattern_count['total']}")
    
    # Check for prospectuses
    print("\n=== PROSPECTUSES TABLE ===")
    cur.execute("SELECT COUNT(*) as total FROM prospectuses")
    prospectus_count = cur.fetchone()
    print(f"Total prospectuses: {prospectus_count['total']}")
    
    # Check for evidence
    print("\n=== EVIDENCE TABLE ===")
    cur.execute("SELECT COUNT(*) as total FROM evidence")
    evidence_count = cur.fetchone()
    print(f"Total evidence: {evidence_count['total']}")
    
    cur.close()
    conn.close()
    
    return {
        'total_signals': len(signals),
        'zones': len(zones),
        'sources': len(sources),
        'patterns': pattern_count['total'],
        'prospectuses': prospectus_count['total'],
        'evidence': evidence_count['total']
    }

if __name__ == '__main__':
    stats = audit_database()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total signals in DB: {stats['total_signals']}")
    print(f"Zones with data: {stats['zones']}")
    print(f"Signal sources: {stats['sources']}")
    print(f"Patterns: {stats['patterns']}")
    print(f"Prospectuses: {stats['prospectuses']}")
    print(f"Evidence: {stats['evidence']}")

# Made with Bob
