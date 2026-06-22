"""
Kulima OS - National DPI System Architecture Schemas

Defines the structured schema for the 10-layer architecture, ensuring DPI compliance,
Zero-PII invariants, and type safety for investment-grade outputs.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal, Generic, TypeVar

T = TypeVar('T')

class BoundedValue(BaseModel, Generic[T]):
    central_estimate: T
    lower_bound: T
    upper_bound: T
    margin_of_error: float

# ==========================================
# LAYER 1: SIGNAL INTELLIGENCE
# ==========================================
class SignalSchema(BaseModel):
    signal_id: str = Field(..., description="Unique identifier for the signal")
    session_hash: str = Field(..., description="Ephemeral hash replacing source_id for Zero-PII")
    batch_window: str = Field(..., description="Time window (e.g. 2026-W21-Morning) replacing exact timestamp")
    zone_id: str = Field(..., description="Coarse location replacing precise geo")
    activity_type: str = Field(..., description="Type of productive activity (e.g. milling, irrigation)")
    confidence_weight: float = Field(..., ge=0.0, le=1.0)
    
    @validator("session_hash")
    def validate_no_pii_in_hash(cls, v):
        if "@" in v or "-" in v and len(v) < 16:  # simplistic check to avoid plain emails/phones
            raise ValueError("session_hash must not contain PII.")
        return v

# ==========================================
# LAYER 2: ZENTARI TRUST ENGINE (TRUST INFRASTRUCTURE)
# ==========================================
class ValidationEvidence(BaseModel):
    supporting_sources: int
    repetition_count: int
    time_window_coverage: int
    geographic_density: float
    cross_checks_passed: int

class AdversarialDetection(BaseModel):
    anomaly_score: float = Field(..., ge=0.0, le=100.0)
    fraud_risk_flag: bool
    trust_penalty: float

class CalibrationState(BaseModel):
    calibration_cycle: int
    error_tracking: float
    weight_adjustment_rules: str

class ProvenanceTrace(BaseModel):
    original_signal_ids: List[str]
    transformations_applied: List[str]
    trust_adjustments: List[str]
    final_decision_path: str

class ConfidenceBound(BaseModel):
    confidence_level: float = Field(..., ge=0.0, le=100.0)
    margin_of_error: float
    reliability_summary: str

class TrustCertification(BaseModel):
    system_trust_rating: float = Field(..., ge=0.0, le=100.0)
    readiness_level: Literal["experimental", "pilot-ready", "institution-ready"]

class TrustOutput(BaseModel):
    trust_score: float = Field(..., ge=0.0, le=100.0)
    confidence_band: Literal["Unverified", "Emerging", "Actionable", "High Confidence", "Institutionally Defensible"]
    validation_evidence: ValidationEvidence
    adversarial_detection: AdversarialDetection
    calibration_state: CalibrationState
    provenance_tracking: ProvenanceTrace
    explainability: List[str]
    confidence_bound: ConfidenceBound
    trust_certification: TrustCertification

# ==========================================
# LAYER 3: LUMOZA CLUSTER ENGINE
# ==========================================
class ClusterOutput(BaseModel):
    cluster_id: str
    zone_id: str
    activity_concentration: str
    estimated_participants: BoundedValue[int]
    output_value_estimate_usd: BoundedValue[float]
    demand_frequency: str
    stability_index: BoundedValue[float]

# ==========================================
# LAYER 4: LUNDAI GAP ENGINE
# ==========================================
class GapOutput(BaseModel):
    gap_type: Literal["energy", "irrigation", "storage", "logistics", "none"]
    severity_score: BoundedValue[float]
    population_affected: BoundedValue[int]
    economic_loss_estimate_usd: BoundedValue[float]
    urgency_index: Literal["low", "medium", "high", "critical", "adequate"]

# ==========================================
# LAYER 5: FINANCIAL ENGINE
# ==========================================
class FinancialModelScenario(BaseModel):
    capex_estimate_usd: float
    opex_monthly_usd: float
    revenue_projection_monthly_usd: float
    payback_period_months: float
    irr: float

class ScenarioAnalysis(BaseModel):
    base_case: FinancialModelScenario
    optimistic_case: FinancialModelScenario
    pessimistic_case: FinancialModelScenario

class FinancialModelOutput(BaseModel):
    project_name: str
    pricing_model: str
    breakeven_users: BoundedValue[int]
    scenarios: ScenarioAnalysis

# ==========================================
# LAYER 6: RISK & COMPLIANCE ENGINE
# ==========================================
class RiskOutput(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=100.0)
    category: Literal["operational", "financial", "environmental", "governance"]
    mitigation_plan: str
    regulatory_flags: List[str]

# ==========================================
# LAYER 7: IMPLEMENTATION ENGINE
# ==========================================
class ImplementationOutput(BaseModel):
    ownership_model: Literal["public", "private", "PPP", "cooperative"]
    operator_type: str
    funding_strategy: Literal["grant", "debt", "equity", "blended"]
    deployment_steps: List[str]

# ==========================================
# LAYER 8: INVESTMENT DECISION ENGINE
# ==========================================
class WhyNotAnalysis(BaseModel):
    reasons_this_may_be_wrong: List[str]
    data_limitations: List[str]
    uncertainty_factors: List[str]
    known_biases: List[str]

class DecisionOutput(BaseModel):
    total_investment_required_usd: BoundedValue[float]
    projected_return_irr: BoundedValue[float]
    risk_profile: Literal["low", "moderate", "high", "critical"]
    readiness_score: float = Field(..., ge=0.0, le=100.0)
    recommendation: Literal["INVEST", "PILOT", "COLLECT MORE DATA", "MAINTAIN"]
    why_not_analysis: WhyNotAnalysis

# ==========================================
# LAYER 9: AUDIT & TRACEABILITY
# ==========================================
class AuditTrace(BaseModel):
    decision_timestamp: str
    trace_id: str
    logic_explanation: str
    inputs_hashed: str

# ==========================================
# LAYER 10 / SYSTEM: DECLARATIONS & ASSESSMENTS
# ==========================================
class DataSufficiencyStatus(BaseModel):
    is_sufficient: bool
    minimum_signal_threshold_met: bool
    diversity_threshold_met: bool
    time_coverage_threshold_met: bool
    reasoning: str

class TrustDeclarationBlock(BaseModel):
    confidence_level: float
    data_sufficiency_status: DataSufficiencyStatus
    validation_depth: str
    fraud_risk_level: Literal["low", "medium", "high", "critical"]
    audit_trace_available: bool = True

class SystemSelfAssessment(BaseModel):
    system_confidence_score: float
    weakest_layer_identified: str
    reliability_summary: str
    recommended_next_improvement: str

# ==========================================
# MASTER SCHEMA
# ==========================================
class MasterDPIOutput(BaseModel):
    zone_id: str
    data_sufficiency: DataSufficiencyStatus
    cluster: Optional[ClusterOutput] = None
    trust: Optional[TrustOutput] = None
    gap: Optional[GapOutput] = None
    financial: Optional[FinancialModelOutput] = None
    risk: Optional[RiskOutput] = None
    implementation: Optional[ImplementationOutput] = None
    decision: Optional[DecisionOutput] = None
    audit: Optional[AuditTrace] = None
    trust_declaration: Optional[TrustDeclarationBlock] = None
    system_assessment: Optional[SystemSelfAssessment] = None
