"""
Red Team Simulation for ZENTARI 2.0
Tests the Calibrated Trust Infrastructure against various scenarios.
"""

from core.dpi_pipeline import KulimaDPIPipeline
import json

def run_simulation(scenario_name: str, signals: list):
    print(f"\n==============================================")
    print(f"SCENARIO: {scenario_name}")
    print(f"==============================================")
    
    pipeline = KulimaDPIPipeline()
    result = pipeline.process_zone("TEST-ZONE", signals)
    
    trust = result.trust
    
    print(f"Trust Score: {trust.trust_score}")
    print(f"Confidence Band: {trust.confidence_band}")
    print(f"System Trust Rating: {trust.trust_certification.system_trust_rating} ({trust.trust_certification.readiness_level})")
    
    print("\n[EVIDENCE LAYER]")
    print(f"Sources: {trust.validation_evidence.supporting_sources}, Cycles: {trust.validation_evidence.repetition_count}")
    
    print("\n[ADVERSARIAL DETECTION]")
    print(f"Fraud Risk Flag: {trust.adversarial_detection.fraud_risk_flag}")
    print(f"Anomaly Score: {trust.adversarial_detection.anomaly_score}")
    print(f"Penalty Applied: {trust.adversarial_detection.trust_penalty}")
    
    print("\n[CONFIDENCE BOUNDS]")
    print(f"Margin of Error: ±{trust.confidence_bound.margin_of_error}%")
    print(f"Reliability: {trust.confidence_bound.reliability_summary}")
    
    print("\n[EXPLAINABILITY LAYER]")
    for e in trust.explainability:
        print(f" - {e}")
        
    print("\n[PROVENANCE TRACE]")
    for t in trust.provenance_tracking.trust_adjustments:
        print(f" - {t}")
    print(f" Final Path: {trust.provenance_tracking.final_decision_path}")


def main():
    # Scenario 1: Clean Data
    clean_signals = [
        {"id": "sig_1", "source_id": "farmer_A", "batch_window": "2026-W21-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_2", "source_id": "farmer_B", "batch_window": "2026-W21-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_3", "source_id": "farmer_C", "batch_window": "2026-W21-Afternoon", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_4", "source_id": "farmer_D", "batch_window": "2026-W22-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_5", "source_id": "farmer_E", "batch_window": "2026-W22-Afternoon", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_6", "source_id": "farmer_F", "batch_window": "2026-W23-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_7", "source_id": "farmer_G", "batch_window": "2026-W23-Afternoon", "zone": "TEST-ZONE", "activity_type": "irrigation"},
        {"id": "sig_8", "source_id": "farmer_H", "batch_window": "2026-W24-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
    ]
    
    # Scenario 2: Sybil Attack (Bad Data)
    # One user sending many signals rapidly
    bad_signals = []
    for i in range(20):
        bad_signals.append({
            "id": f"bad_sig_{i}", 
            "source_id": "malicious_bot", 
            "batch_window": "2026-W21-Morning", 
            "zone": "TEST-ZONE", 
            "activity_type": "irrigation"
        })
        
    # Scenario 3: Missing Data / Weak Signal
    weak_signals = [
        {"id": "sig_w1", "source_id": "farmer_A", "batch_window": "2026-W21-Morning", "zone": "TEST-ZONE", "activity_type": "irrigation"},
    ]

    run_simulation("Clean Distributed Data", clean_signals)
    run_simulation("Sybil Attack (1 Source, 20 Signals)", bad_signals)
    run_simulation("Weak Sporadic Signal (1 Source, 1 Signal)", weak_signals)

if __name__ == "__main__":
    main()
