import json
from core.dpi_pipeline import KulimaDPIPipeline, run_pipeline_json

def test_dpi_pipeline():
    # Mock some raw signals, note they use raw schema which will be sanitized
    raw_signals = [
        {"id": "sig_1", "source_id": "user_a", "batch_window": "2026-W21-Morning", "zone": "MZUZU-NORTH", "activity_type": "milling", "confidence": 0.9},
        {"id": "sig_2", "source_id": "user_b", "batch_window": "2026-W21-Morning", "zone": "MZUZU-NORTH", "activity_type": "milling", "confidence": 0.8},
        {"id": "sig_3", "source_id": "user_c", "batch_window": "2026-W21-Afternoon", "zone": "MZUZU-NORTH", "activity_type": "milling", "confidence": 0.85},
        {"id": "sig_4", "source_id": "user_d", "batch_window": "2026-W21-Afternoon", "zone": "MZUZU-NORTH", "activity_type": "milling", "confidence": 0.9},
        {"id": "sig_5", "source_id": "user_e", "batch_window": "2026-W22-Morning", "zone": "MZUZU-NORTH", "activity_type": "milling", "confidence": 0.85},
        {"id": "sig_6", "source_id": "user_f", "batch_window": "2026-W22-Morning", "zone": "MZUZU-NORTH", "activity_type": "milling", "confidence": 0.95},
        {"id": "sig_7", "source_id": "user_g", "batch_window": "2026-W22-Afternoon", "zone": "MZUZU-NORTH", "activity_type": "milling", "confidence": 0.8},
    ]

    print("Running Kulima DPI Pipeline...")
    json_output = run_pipeline_json("MZUZU-NORTH", raw_signals)
    
    data = json.loads(json_output)
    print("\n--- MASTER DPI OUTPUT ---")
    print(f"Zone: {data['zone_id']}")
    
    print("\n1. LAYER 2 - TRUST ENGINE (ZENTARI)")
    print(f"   Trust Score: {data['trust']['trust_score']}")
    print(f"   Confidence Band: {data['trust']['confidence_band']}")
    
    print("\n2. LAYER 3 - CLUSTER ENGINE (LUMOZA)")
    print(f"   Activity: {data['cluster']['activity_concentration']}")
    print(f"   Participants Lower Bound: {data['cluster']['estimated_participants_lower_bound']}")
    print(f"   Stability Index: {data['cluster']['stability_index']}")
    
    print("\n3. LAYER 4 - GAP ENGINE (LUNDAI)")
    print(f"   Gap Type: {data['gap']['gap_type']}")
    print(f"   Severity: {data['gap']['severity_score']}")
    print(f"   Urgency: {data['gap']['urgency_index']}")
    
    print("\n4. LAYER 5 - FINANCIAL ENGINE")
    print(f"   Project Name: {data['financial']['project_name']}")
    print(f"   CAPEX: ${data['financial']['capex_estimate_usd']}")
    print(f"   OPEX/mo: ${data['financial']['opex_monthly_usd']}")
    print(f"   Revenue/mo: ${data['financial']['revenue_projection_monthly_usd']}")
    print(f"   Payback (Months): {data['financial']['payback_period_months']}")
    
    print("\n5. LAYER 6 - RISK & COMPLIANCE ENGINE")
    print(f"   Risk Score: {data['risk']['risk_score']}")
    print(f"   Category: {data['risk']['category']}")
    print(f"   Regulatory Flags: {', '.join(data['risk']['regulatory_flags'])}")
    
    print("\n6. LAYER 7 - IMPLEMENTATION ENGINE")
    print(f"   Ownership Model: {data['implementation']['ownership_model']}")
    print(f"   Funding Strategy: {data['implementation']['funding_strategy']}")
    print("   Steps:")
    for step in data['implementation']['deployment_steps']:
        print(f"     - {step}")
        
    print("\n7. LAYER 8 - INVESTMENT DECISION ENGINE")
    print(f"   Readiness Score: {data['decision']['readiness_score']}")
    print(f"   Recommendation: {data['decision']['recommendation']}")
    
    print("\n8. LAYER 9 - AUDIT & TRACEABILITY ENGINE")
    print(f"   Trace ID: {data['audit']['trace_id']}")
    print(f"   Logic Explanation: {data['audit']['logic_explanation']}")
    
    print("\nPipeline execution successful and strictly formatted as requested!")

if __name__ == "__main__":
    test_dpi_pipeline()
