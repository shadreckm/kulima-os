"""
DPI Core Engines (Layers 1-4) for Kulima OS DPI.
Implements the new quantitative trust, clustering, and gap logic with uncertainty propagation.
"""

from typing import List, Dict
import hashlib
from datetime import datetime
import math
from core.dpi_schema import (
    SignalSchema, TrustOutput, ValidationEvidence, AdversarialDetection, 
    CalibrationState, ProvenanceTrace, ConfidenceBound, TrustCertification,
    ClusterOutput, GapOutput, BoundedValue
)

def parse_week_to_int(batch_window: str) -> int:
    """Mock parser to turn '2026-W21-Morning' into an integer for decay calculation."""
    try:
        parts = batch_window.split("-")
        year = int(parts[0])
        week = int(parts[1].replace("W", ""))
        return year * 52 + week
    except:
        return 2026 * 52 + 21 # Default fallback

class DPISignalLayer:
    """Layer 1: Signal Intelligence"""
    def __init__(self, current_batch_window: str = "2026-W24-Morning"):
        self.current_time_val = parse_week_to_int(current_batch_window)
        self.decay_lambda = 0.173 # Approx 4-week half-life: e^(-0.173 * 4) ≈ 0.5
        
    def ingest_signals(self, raw_signals: List[Dict]) -> List[SignalSchema]:
        validated = []
        for raw in raw_signals:
            raw_source = str(raw.get("source_id", "unknown"))
            session_hash = hashlib.md5(raw_source.encode()).hexdigest()
            
            batch_window = raw.get("batch_window", "2026-W24-Morning")
            signal_time_val = parse_week_to_int(batch_window)
            
            # Step 2: Temporal Decay Model
            time_diff = max(0, self.current_time_val - signal_time_val)
            decay_weight = math.exp(-self.decay_lambda * time_diff)
            
            base_confidence = float(raw.get("confidence", 0.5))
            final_confidence = base_confidence * decay_weight
            
            sig = SignalSchema(
                signal_id=raw.get("id", f"sig_{len(validated)}"),
                session_hash=session_hash,
                batch_window=batch_window,
                zone_id=raw.get("zone", "UNKNOWN-ZONE"),
                activity_type=raw.get("activity_type", "unknown"),
                confidence_weight=final_confidence
            )
            validated.append(sig)
        return validated

class ZentariTrustInfrastructure:
    """Layer 2: ZENTARI Calibrated Trust Infrastructure (11 Steps)"""
    
    def __init__(self):
        self.weights = {
            "diversity": 20.0,
            "repetition": 30.0,
            "density": 15.0,
            "cross_validation": 35.0,
        }
        self.calibration_state = CalibrationState(
            calibration_cycle=1,
            error_tracking=0.0,
            weight_adjustment_rules="Adjust weights +-5% based on MSE of predicted vs actual utilization."
        )

    def _detect_adversarial(self, signals: List[SignalSchema]) -> AdversarialDetection:
        """Step 5: Adversarial Detection"""
        if not signals:
            return AdversarialDetection(anomaly_score=0.0, fraud_risk_flag=False, trust_penalty=0.0)
            
        unique_sessions = len(set(s.session_hash for s in signals))
        total_signals = len(signals)
        
        # Detect sybil attack: many signals from one source
        anomaly_score = 0.0
        fraud_risk = False
        penalty = 0.0
        
        if total_signals > 5 and (unique_sessions / total_signals) < 0.2:
            anomaly_score = 85.0
            fraud_risk = True
            penalty = 50.0  # Huge penalty for suspected sybil manipulation
            
        return AdversarialDetection(
            anomaly_score=anomaly_score,
            fraud_risk_flag=fraud_risk,
            trust_penalty=penalty
        )

    def _gather_evidence(self, signals: List[SignalSchema]) -> ValidationEvidence:
        """Step 2: Validation Evidence Layer"""
        unique_sessions = len(set(s.session_hash for s in signals))
        repetition_cycles = len(set(s.batch_window for s in signals))
        
        # Geographic density proxy
        density = min(1.0, unique_sessions / 10.0)
        
        # Cross checks (Step 6 mock)
        cross_checks = 1 if repetition_cycles > 3 else 0
        
        return ValidationEvidence(
            supporting_sources=unique_sessions,
            repetition_count=repetition_cycles,
            time_window_coverage=repetition_cycles,
            geographic_density=density,
            cross_checks_passed=cross_checks
        )

    def evaluate_trust(self, signals: List[SignalSchema]) -> TrustOutput:
        """Calculate quantitative trust score using 11-step methodology."""
        if not signals:
            return TrustOutput(
                trust_score=0.0,
                confidence_band="Unverified",
                validation_evidence=ValidationEvidence(supporting_sources=0, repetition_count=0, time_window_coverage=0, geographic_density=0.0, cross_checks_passed=0),
                adversarial_detection=AdversarialDetection(anomaly_score=0.0, fraud_risk_flag=False, trust_penalty=0.0),
                calibration_state=self.calibration_state,
                provenance_tracking=ProvenanceTrace(original_signal_ids=[], transformations_applied=[], trust_adjustments=[], final_decision_path=""),
                explainability=["No signals provided."],
                confidence_bound=ConfidenceBound(confidence_level=0.0, margin_of_error=100.0, reliability_summary="No data"),
                trust_certification=TrustCertification(system_trust_rating=0.0, readiness_level="experimental")
            )
            
        evidence = self.gather_evidence(signals)
        adversarial = self._detect_adversarial(signals)
        
        # Step 1: Multi-Dimensional Trust Model
        # Decay-weighted diversity
        weighted_diversity = sum(s.confidence_weight for s in signals)
        
        score_diversity = min(self.weights["diversity"], weighted_diversity * 2.0)
        score_repetition = min(self.weights["repetition"], evidence.repetition_count * 5.0)
        score_density = min(self.weights["density"], evidence.geographic_density * self.weights["density"])
        score_cv = min(self.weights["cross_validation"], evidence.cross_checks_passed * 15.0)
        
        raw_trust = score_diversity + score_repetition + score_density + score_cv
        
        trust_score = raw_trust - adversarial.trust_penalty
        trust_score = max(0.0, min(100.0, trust_score))
        
        if trust_score < 30:
            band = "Unverified"
        elif trust_score < 60:
            band = "Emerging"
        elif trust_score < 80:
            band = "Actionable"
        elif trust_score < 95:
            band = "High Confidence"
        else:
            band = "Institutionally Defensible"
            
        sig_ids = [s.signal_id for s in signals]
        provenance = ProvenanceTrace(
            original_signal_ids=sig_ids,
            transformations_applied=["Time-Batching", "Temporal Decay Applied", "Zero-PII Hashing", "Trust Normalization"],
            trust_adjustments=[f"Penalty: -{adversarial.trust_penalty}" if adversarial.trust_penalty > 0 else "No penalties applied"],
            final_decision_path=f"Trust Score {trust_score:.1f} -> {band}"
        )
        
        explainability = [
            f"Trust score is {trust_score:.1f} out of 100.",
            f"Supported by {evidence.supporting_sources} unique sources over {evidence.repetition_count} cycles.",
            f"Decay-weighted signal strength: {weighted_diversity:.1f}"
        ]
        if adversarial.fraud_risk_flag:
            explainability.append(f"WARNING: Fraud risk detected. Anomaly score {adversarial.anomaly_score}. Penalty applied.")
            
        moe = max(1.0, 50.0 - (evidence.supporting_sources * 2) - (evidence.repetition_count * 5))
        if adversarial.fraud_risk_flag:
            moe = 100.0
            
        bounds = ConfidenceBound(
            confidence_level=trust_score,
            margin_of_error=round(moe, 1),
            reliability_summary=f"Score ±{moe:.1f}% based on evidence volume."
        )
        
        if trust_score >= 80 and not adversarial.fraud_risk_flag:
            readiness = "institution-ready"
        elif trust_score >= 60:
            readiness = "pilot-ready"
        else:
            readiness = "experimental"
            
        cert = TrustCertification(
            system_trust_rating=trust_score,
            readiness_level=readiness
        )

        return TrustOutput(
            trust_score=round(trust_score, 1),
            confidence_band=band,
            validation_evidence=evidence,
            adversarial_detection=adversarial,
            calibration_state=self.calibration_state,
            provenance_tracking=provenance,
            explainability=explainability,
            confidence_bound=bounds,
            trust_certification=cert
        )

    def gather_evidence(self, signals):
        return self._gather_evidence(signals)

class DPILumozaEngine:
    """Layer 3: LUMOZA Cluster Engine"""
    def generate_cluster(self, zone_id: str, signals: List[SignalSchema]) -> ClusterOutput:
        """Create economically meaningful clusters with confidence bounds."""
        if not signals:
            return ClusterOutput(
                cluster_id=f"cluster_{zone_id}",
                zone_id=zone_id,
                activity_concentration="none",
                estimated_participants=BoundedValue[int](central_estimate=0, lower_bound=0, upper_bound=0, margin_of_error=0.0),
                output_value_estimate_usd=BoundedValue[float](central_estimate=0.0, lower_bound=0.0, upper_bound=0.0, margin_of_error=0.0),
                demand_frequency="none",
                stability_index=BoundedValue[float](central_estimate=0.0, lower_bound=0.0, upper_bound=0.0, margin_of_error=0.0)
            )
            
        activities = [s.activity_type for s in signals]
        dominant = max(set(activities), key=activities.count)
        
        unique_participants = len(set(s.session_hash for s in signals))
        lower_bound = max(5, unique_participants)
        upper_bound = int(lower_bound * 1.5) # Example variance
        central = int((lower_bound + upper_bound) / 2)
        moe_part = (upper_bound - lower_bound) / (2 * max(1, central)) * 100.0
        
        active_cycles = len(set(s.batch_window for s in signals))
        stability_central = min(1.0, active_cycles / 7.0)
        
        return ClusterOutput(
            cluster_id=f"cluster_{zone_id}_{dominant}",
            zone_id=zone_id,
            activity_concentration=dominant,
            estimated_participants=BoundedValue[int](
                central_estimate=central,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                margin_of_error=moe_part
            ),
            output_value_estimate_usd=BoundedValue[float](
                central_estimate=central * 500.0,
                lower_bound=lower_bound * 500.0,
                upper_bound=upper_bound * 500.0,
                margin_of_error=moe_part
            ),
            demand_frequency="daily-morning",
            stability_index=BoundedValue[float](
                central_estimate=stability_central,
                lower_bound=max(0.0, stability_central - 0.2),
                upper_bound=min(1.0, stability_central + 0.1),
                margin_of_error=20.0
            )
        )

class DPILundaiEngine:
    """Layer 4: LUNDAI Gap Engine"""
    def identify_gaps(self, cluster: ClusterOutput) -> GapOutput:
        if cluster.stability_index.central_estimate < 0.3 or cluster.estimated_participants.central_estimate < 5:
            return GapOutput(
                gap_type="none",
                severity_score=BoundedValue[float](central_estimate=0.0, lower_bound=0.0, upper_bound=0.0, margin_of_error=0.0),
                population_affected=BoundedValue[int](central_estimate=0, lower_bound=0, upper_bound=0, margin_of_error=0.0),
                economic_loss_estimate_usd=BoundedValue[float](central_estimate=0.0, lower_bound=0.0, upper_bound=0.0, margin_of_error=0.0),
                urgency_index="adequate"
            )
            
        gap_map = {
            "milling": "energy",
            "irrigation": "irrigation",
            "welding": "energy",
            "storage": "storage",
            "trading": "energy"
        }
        
        gap_type = gap_map.get(cluster.activity_concentration, "energy")
        
        severity_central = min(10.0, cluster.stability_index.central_estimate * 10.0)
        sev_lb = min(10.0, cluster.stability_index.lower_bound * 10.0)
        sev_ub = min(10.0, cluster.stability_index.upper_bound * 10.0)
        
        if severity_central > 8.0:
            urgency = "critical"
        elif severity_central > 6.0:
            urgency = "high"
        elif severity_central > 4.0:
            urgency = "medium"
        else:
            urgency = "low"
            
        return GapOutput(
            gap_type=gap_type,
            severity_score=BoundedValue[float](
                central_estimate=round(severity_central, 1),
                lower_bound=round(sev_lb, 1),
                upper_bound=round(sev_ub, 1),
                margin_of_error=cluster.stability_index.margin_of_error
            ),
            population_affected=BoundedValue[int](
                central_estimate=cluster.estimated_participants.central_estimate * 5,
                lower_bound=cluster.estimated_participants.lower_bound * 5,
                upper_bound=cluster.estimated_participants.upper_bound * 5,
                margin_of_error=cluster.estimated_participants.margin_of_error
            ),
            economic_loss_estimate_usd=BoundedValue[float](
                central_estimate=cluster.output_value_estimate_usd.central_estimate * 0.3,
                lower_bound=cluster.output_value_estimate_usd.lower_bound * 0.3,
                upper_bound=cluster.output_value_estimate_usd.upper_bound * 0.3,
                margin_of_error=cluster.output_value_estimate_usd.margin_of_error
            ),
            urgency_index=urgency
        )
