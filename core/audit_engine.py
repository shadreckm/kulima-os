"""
Audit & Traceability Engine (Layer 9) for Kulima OS DPI.
Provides immutable, explainable trace from decisions to raw aggregates.
"""

from core.dpi_schema import DecisionOutput, FinancialModelOutput, ClusterOutput, GapOutput, AuditTrace
import hashlib
from datetime import datetime
import json

class AuditEngine:
    def generate_trace(self, decision: DecisionOutput, financial: FinancialModelOutput, cluster: ClusterOutput, gap: GapOutput) -> AuditTrace:
        """Generate an explainable audit trace for the final decision."""
        
        base_scenario = financial.scenarios.base_case
        
        # Hash inputs to create an immutable link
        inputs_str = f"{cluster.cluster_id}_{gap.severity_score.central_estimate}_{base_scenario.capex_estimate_usd}"
        inputs_hashed = hashlib.sha256(inputs_str.encode()).hexdigest()
        
        trace_id = f"TRC-{hashlib.md5(inputs_hashed.encode()).hexdigest()[:8].upper()}"
        
        explanation = (
            f"Decision [{decision.recommendation}] reached with readiness score {decision.readiness_score}. "
            f"Based on cluster {cluster.cluster_id} showing {cluster.activity_concentration} demand. "
            f"Financial model requires ${base_scenario.capex_estimate_usd} Capex with an estimated "
            f"payback of {base_scenario.payback_period_months} months."
        )
        
        return AuditTrace(
            decision_timestamp=datetime.utcnow().isoformat() + "Z",
            trace_id=trace_id,
            logic_explanation=explanation,
            inputs_hashed=inputs_hashed
        )
