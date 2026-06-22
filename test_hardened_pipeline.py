"""
Red Team Continuous Mode for Kulima OS Hardened Pipeline
Simulates edge cases: Decayed Data, Insufficient Data, and Clean Data.
"""

from core.dpi_pipeline import KulimaDPIPipeline
from datetime import datetime
import json

def run_simulation(scenario_name: str, signals: list):
    print(f"\n==============================================")
    print(f"SCENARIO: {scenario_name}")
    print(f"==============================================")
    
    pipeline = KulimaDPIPipeline()
    result = pipeline.process_zone("TEST-ZONE", signals)
    
    suff = result.data_sufficiency
    print(f"Data Sufficiency Gate Passed: {suff.is_sufficient}")
    print(f"Reason: {suff.reasoning}")
    
    if not suff.is_sufficient:
        print("PIPELINE STOPPED AT GATE.")
        return

    print(f"\n[SYSTEM DECLARATION]")
    print(f"Confidence Level: {result.trust_declaration.confidence_level}")
    print(f"Fraud Risk Level: {result.trust_declaration.fraud_risk_level}")
    print(f"Weakest Layer: {result.system_assessment.weakest_layer_identified}")
    
    print("\n[FINANCIAL BOUNDS]")
    base = result.financial.scenarios.base_case
    opt = result.financial.scenarios.optimistic_case
    pess = result.financial.scenarios.pessimistic_case
    print(f"Base CAPEX: ${base.capex_estimate_usd}")
    print(f"Optimistic CAPEX: ${opt.capex_estimate_usd}")
    print(f"Pessimistic CAPEX: ${pess.capex_estimate_usd}")
    print(f"Breakeven Users: {result.financial.breakeven_users.lower_bound} - {result.financial.breakeven_users.upper_bound} (MoE: ±{result.financial.breakeven_users.margin_of_error:.1f}%)")
    
    print("\n[DECISION LAYER]")
    print(f"Recommendation: {result.decision.recommendation}")
    print(f"Readiness Score: {result.decision.readiness_score}")
    
    print("\n[WHY NOT ANALYSIS]")
    for r in result.decision.why_not_analysis.reasons_this_may_be_wrong:
        print(f" - {r}")
    for u in result.decision.why_not_analysis.uncertainty_factors:
        print(f" - {u}")
    for b in result.decision.why_not_analysis.known_biases:
        print(f" - {b}")

def main():
    # Scenario 1: Clean Data (Current time is set to 2026-W24 internally)
    clean_signals = [
        {"id": "sig_1", "source_id": "farmer_A", "batch_window": "2026-W24-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_2", "source_id": "farmer_B", "batch_window": "2026-W24-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_3", "source_id": "farmer_C", "batch_window": "2026-W23-Afternoon", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_4", "source_id": "farmer_D", "batch_window": "2026-W23-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_5", "source_id": "farmer_E", "batch_window": "2026-W22-Afternoon", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_6", "source_id": "farmer_F", "batch_window": "2026-W22-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
    ]
    
    # Scenario 2: Insufficient Data (Fails Gate)
    weak_signals = [
        {"id": "sig_w1", "source_id": "farmer_A", "batch_window": "2026-W24-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_w2", "source_id": "farmer_B", "batch_window": "2026-W24-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
    ]
    
    # Scenario 3: Heavily Decayed Data
    # 20 weeks old data. Will have extremely low weights.
    decayed_signals = [
        {"id": "sig_d1", "source_id": "farmer_A", "batch_window": "2026-W04-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_d2", "source_id": "farmer_B", "batch_window": "2026-W04-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_d3", "source_id": "farmer_C", "batch_window": "2026-W03-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_d4", "source_id": "farmer_D", "batch_window": "2026-W03-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
    ]

    run_simulation("Clean Distributed Data", clean_signals)
    run_simulation("Insufficient Data (Fails Gate)", weak_signals)
    run_simulation("Decayed Old Data", decayed_signals)

if __name__ == "__main__":
    main()
