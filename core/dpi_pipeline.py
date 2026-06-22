"""
Master DPI Pipeline for Kulima OS.
Integrates all 10 layers into a single execution flow, enforcing
strict Data Sufficiency gates and Institutional Trust Declarations.
"""

from typing import List, Dict
import json
from core.dpi_schema import MasterDPIOutput, DataSufficiencyStatus, TrustDeclarationBlock, SystemSelfAssessment
from core.dpi_core_engines import DPISignalLayer, ZentariTrustInfrastructure, DPILumozaEngine, DPILundaiEngine
from core.financial_engine import FinancialEngine
from core.risk_engine import RiskEngine
from core.implementation_engine import ImplementationEngine
from core.decision_engine import DecisionEngine
from core.audit_engine import AuditEngine

class KulimaDPIPipeline:
    def __init__(self):
        self.signal_layer = DPISignalLayer()
        self.zentari = ZentariTrustInfrastructure()
        self.lumoza = DPILumozaEngine()
        self.lundai = DPILundaiEngine()
        self.financial = FinancialEngine()
        self.risk = RiskEngine()
        self.implementation = ImplementationEngine()
        self.decision = DecisionEngine()
        self.audit = AuditEngine()
        
    def process_zone(self, zone_id: str, raw_signals: List[Dict]) -> MasterDPIOutput:
        """Process a batch of raw signals for a zone through all 10 layers."""
        
        # Layer 1: Signal Intelligence (Ingestion & Zero-PII sanitization & Temporal Decay)
        signals = self.signal_layer.ingest_signals(raw_signals)
        
        # Layer 2: Trust Engine (ZENTARI)
        trust_output = self.zentari.evaluate_trust(signals)
        
        # --- DATA SUFFICIENCY GATE (Step 4) ---
        evidence = trust_output.validation_evidence
        min_sources = 3
        min_cycles = 2
        
        has_sources = evidence.supporting_sources >= min_sources
        has_cycles = evidence.repetition_count >= min_cycles
        is_sufficient = has_sources and has_cycles
        
        suff_status = DataSufficiencyStatus(
            is_sufficient=is_sufficient,
            minimum_signal_threshold_met=has_sources,
            diversity_threshold_met=has_sources,
            time_coverage_threshold_met=has_cycles,
            reasoning=f"Requires {min_sources} sources and {min_cycles} cycles. Got {evidence.supporting_sources} and {evidence.repetition_count}."
        )
        
        # If data is insufficient, stop pipeline and return immediately.
        if not is_sufficient:
            return MasterDPIOutput(
                zone_id=zone_id,
                data_sufficiency=suff_status,
                trust=trust_output
            )
        
        # Layer 3: Cluster Engine (LUMOZA)
        cluster_output = self.lumoza.generate_cluster(zone_id, signals)
        
        # Layer 4: Gap Engine (LUNDAI)
        gap_output = self.lundai.identify_gaps(cluster_output)
        
        # Layer 5: Financial Engine
        financial_output = self.financial.generate_model(cluster_output, gap_output)
        
        # Layer 6: Risk & Compliance Engine
        # NOTE: Risk engine needs adjustment to read bounded values but we'll adapt slightly here
        risk_output = self.risk.evaluate_risk(financial_output, cluster_output)
        
        # Layer 7: Implementation Engine
        impl_output = self.implementation.structure_execution(financial_output, risk_output)
        
        # Layer 8: Investment Decision Engine (Includes "Why Not" analysis)
        decision_output = self.decision.make_decision(financial_output, risk_output, trust_output)
        
        # Layer 9: Audit & Traceability
        audit_output = self.audit.generate_trace(decision_output, financial_output, cluster_output, gap_output)
        
        # --- Layer 10: System Self-Assessment & Trust Declaration (Steps 6 & 9) ---
        
        fraud_risk_level = "critical" if trust_output.adversarial_detection.fraud_risk_flag else "low"
        
        trust_dec = TrustDeclarationBlock(
            confidence_level=trust_output.trust_score,
            data_sufficiency_status=suff_status,
            validation_depth=f"{evidence.supporting_sources} sources over {evidence.repetition_count} cycles",
            fraud_risk_level=fraud_risk_level,
            audit_trace_available=True
        )
        
        # Simple heuristic to identify weakest layer
        weakest = "Trust Layer"
        if trust_output.confidence_bound.margin_of_error > 20.0:
            weakest = "Trust Layer: High margin of error on signals."
        elif financial_output.breakeven_users.margin_of_error > 20.0:
            weakest = "Financial Layer: High variance in breakeven calculation."
        elif gap_output.severity_score.margin_of_error > 20.0:
            weakest = "Gap Layer: Wide bounds on gap severity."
            
        sys_assess = SystemSelfAssessment(
            system_confidence_score=trust_output.trust_score * 0.8, # More conservative
            weakest_layer_identified=weakest,
            reliability_summary=f"System generated decision with {trust_output.confidence_bound.margin_of_error}% MoE on base inputs.",
            recommended_next_improvement="Deploy ground-truth telemetry sensors to tighten confidence bounds."
        )
        
        return MasterDPIOutput(
            zone_id=zone_id,
            data_sufficiency=suff_status,
            cluster=cluster_output,
            trust=trust_output,
            gap=gap_output,
            financial=financial_output,
            risk=risk_output,
            implementation=impl_output,
            decision=decision_output,
            audit=audit_output,
            trust_declaration=trust_dec,
            system_assessment=sys_assess
        )

def run_pipeline_json(zone_id: str, raw_signals: List[Dict]) -> str:
    """Convenience function to run the pipeline and return DPI compliant JSON."""
    pipeline = KulimaDPIPipeline()
    result = pipeline.process_zone(zone_id, raw_signals)
    return result.model_dump_json(indent=2)
