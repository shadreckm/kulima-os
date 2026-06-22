"""
Investment Decision Engine (Layer 8) for Kulima OS DPI.
Generates final decisive verdict on projects, now protected by rigorous
'Why Not' analysis and uncertainty propagation.
"""

from core.dpi_schema import FinancialModelOutput, RiskOutput, TrustOutput, DecisionOutput, WhyNotAnalysis, BoundedValue

class DecisionEngine:
    def make_decision(self, financial: FinancialModelOutput, risk: RiskOutput, trust: TrustOutput) -> DecisionOutput:
        """Generate final investment decision based on financials, risk, and trust."""
        
        # Pull from base scenario for core decision logic
        base_scenario = financial.scenarios.base_case
        pessimistic_scenario = financial.scenarios.pessimistic_case
        optimistic_scenario = financial.scenarios.optimistic_case
        
        financial_score = 0.0
        if base_scenario.payback_period_months <= 36:
            financial_score = 100.0
        elif base_scenario.payback_period_months <= 60:
            financial_score = 75.0
        elif base_scenario.payback_period_months <= 84:
            financial_score = 40.0
        else:
            financial_score = 10.0
            
        inverse_risk = 100.0 - risk.risk_score
        
        readiness_score = (trust.trust_score * 0.4) + (inverse_risk * 0.3) + (financial_score * 0.3)
        
        # Determine risk profile string
        if risk.risk_score > 75:
            risk_profile = "critical"
        elif risk.risk_score > 50:
            risk_profile = "high"
        elif risk.risk_score > 25:
            risk_profile = "moderate"
        else:
            risk_profile = "low"
            
        # Recommendation Logic
        if readiness_score >= 80 and trust.confidence_band in ["High Confidence", "Institutionally Defensible"]:
            recommendation = "INVEST"
        elif readiness_score >= 50 and trust.confidence_band != "Unverified":
            recommendation = "PILOT"
        else:
            recommendation = "COLLECT MORE DATA"
            
        if base_scenario.capex_estimate_usd == 0:
            readiness_score = 100.0
            recommendation = "MAINTAIN"
            
        # Compile "Why Not" Analysis (Step 7)
        why_not = WhyNotAnalysis(
            reasons_this_may_be_wrong=[],
            data_limitations=[],
            uncertainty_factors=[],
            known_biases=[]
        )
        
        if recommendation in ["INVEST", "PILOT"]:
            why_not.reasons_this_may_be_wrong.append(
                f"Pessimistic scenario shows payback could stretch to {pessimistic_scenario.payback_period_months} months."
            )
            why_not.uncertainty_factors.append(
                f"Margin of error on trust score is {trust.confidence_bound.margin_of_error}%. True demand could be lower."
            )
            
        if trust.validation_evidence.cross_checks_passed == 0:
            why_not.data_limitations.append("0 cross-checks passed. Entire model relies on self-reported signaling.")
            why_not.known_biases.append("Selection bias: Only those actively seeking infrastructure are signaling.")
            
        if financial.breakeven_users.margin_of_error > 20.0:
            why_not.uncertainty_factors.append("High variance in required breakeven participants.")
            
        # Create Bounded Outputs
        capex_bound = BoundedValue[float](
            central_estimate=base_scenario.capex_estimate_usd,
            lower_bound=optimistic_scenario.capex_estimate_usd,  # Optimistic = lower cost
            upper_bound=pessimistic_scenario.capex_estimate_usd, # Pessimistic = higher cost
            margin_of_error=abs(pessimistic_scenario.capex_estimate_usd - base_scenario.capex_estimate_usd) / max(1.0, base_scenario.capex_estimate_usd) * 100.0
        )
        
        irr_bound = BoundedValue[float](
            central_estimate=base_scenario.irr,
            lower_bound=pessimistic_scenario.irr,
            upper_bound=optimistic_scenario.irr,
            margin_of_error=abs(optimistic_scenario.irr - base_scenario.irr)
        )

        return DecisionOutput(
            total_investment_required_usd=capex_bound,
            projected_return_irr=irr_bound,
            risk_profile=risk_profile,
            readiness_score=round(readiness_score, 1),
            recommendation=recommendation,
            why_not_analysis=why_not
        )
