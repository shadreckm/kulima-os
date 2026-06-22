"""
Implementation Engine (Layer 7) for Kulima OS DPI.
Structures the execution strategy based on financial and risk outputs.
"""

from core.dpi_schema import FinancialModelOutput, RiskOutput, ImplementationOutput

class ImplementationEngine:
    def structure_execution(self, financial: FinancialModelOutput, risk: RiskOutput) -> ImplementationOutput:
        """Structure the execution strategy based on financial parameters and risk profile."""
        
        base_scenario = financial.scenarios.base_case
        
        if base_scenario.capex_estimate_usd == 0:
            return ImplementationOutput(
                ownership_model="public",
                operator_type="local_government",
                funding_strategy="grant",
                deployment_steps=["Monitor existing infrastructure for continued adequacy"]
            )

        # Determine funding strategy
        if risk.risk_score > 70 or base_scenario.payback_period_months > 60:
            funding_strategy = "grant"
            ownership_model = "public"
            operator_type = "community_cooperative"
        elif risk.risk_score > 40:
            funding_strategy = "blended"
            ownership_model = "PPP"
            operator_type = "private_operator_with_public_oversight"
        else:
            funding_strategy = "debt"
            ownership_model = "private"
            operator_type = "private_utility"
            
        # Determine deployment steps
        deployment_steps = [
            "1. Stakeholder alignment and community consent",
            f"2. Secure {funding_strategy} funding covering ${base_scenario.capex_estimate_usd}",
        ]
        
        if "requires_mini_grid_license" in risk.regulatory_flags:
            deployment_steps.append("3. Submit regulatory filings and obtain mini-grid license")
            deployment_steps.append("4. Procurement and vendor selection")
            deployment_steps.append("5. Asset installation and commissioning")
        else:
            deployment_steps.append("3. Procurement and vendor selection")
            deployment_steps.append("4. Asset installation and commissioning")
            
        deployment_steps.append("6. Operator onboarding and tariff collection setup")
        
        return ImplementationOutput(
            ownership_model=ownership_model,
            operator_type=operator_type,
            funding_strategy=funding_strategy,
            deployment_steps=deployment_steps
        )
