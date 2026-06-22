"""
Risk & Compliance Engine (Layer 6) for Kulima OS DPI.
Evaluates risk across multiple dimensions for the generated financial models.
"""

from core.dpi_schema import FinancialModelOutput, RiskOutput, ClusterOutput

class RiskEngine:
    def evaluate_risk(self, financial: FinancialModelOutput, cluster: ClusterOutput) -> RiskOutput:
        """Evaluate the risk profile of a proposed financial model."""
        
        base_scenario = financial.scenarios.base_case
        
        # Base risk starts at 50, modified by various factors
        risk_score = 50.0
        regulatory_flags = []
        mitigation_plan = ""
        category = "operational"
        
        if base_scenario.capex_estimate_usd == 0:
            return RiskOutput(
                risk_score=0.0,
                category="operational",
                mitigation_plan="N/A - No investment required",
                regulatory_flags=[]
            )

        # 1. Financial Risk modifiers
        if base_scenario.payback_period_months > 60:
            risk_score += 20
            category = "financial"
            mitigation_plan = "Seek concessional/grant funding to offset capex and reduce payback period."
        elif base_scenario.payback_period_months < 24:
            risk_score -= 15
            
        # 2. Operational/Cluster Risk modifiers
        if cluster.stability_index.central_estimate < 0.6:
            risk_score += 25
            category = "operational"
            mitigation_plan = "Stagger deployment; start with smaller capacity to test demand before scaling."
        elif cluster.stability_index.central_estimate >= 0.85:
            risk_score -= 10
            
        # 3. Regulatory flags based on capex size (proxy for project scale)
        if base_scenario.capex_estimate_usd > 100000:
            regulatory_flags.append("requires_mini_grid_license")
            regulatory_flags.append("environmental_impact_assessment_needed")
        elif base_scenario.capex_estimate_usd > 20000:
            regulatory_flags.append("requires_local_council_approval")
            
        if "energy" in financial.project_name.lower():
            regulatory_flags.append("energy_regulator_notification")
            
        if not mitigation_plan:
            mitigation_plan = "Standard operational monitoring and preventative maintenance schedule."

        # Cap risk score between 0 and 100
        risk_score = max(0.0, min(100.0, risk_score))
        
        return RiskOutput(
            risk_score=round(risk_score, 1),
            category=category,
            mitigation_plan=mitigation_plan,
            regulatory_flags=regulatory_flags
        )
