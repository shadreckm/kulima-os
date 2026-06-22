"""
Financial Engine (Layer 5) for Kulima OS DPI.
Translates infrastructure gaps into bankable financial models with Base, Optimistic, and Pessimistic scenarios.
"""

from typing import Dict, List, Optional
from core.dpi_schema import GapOutput, ClusterOutput, FinancialModelOutput, ScenarioAnalysis, FinancialModelScenario, BoundedValue

class FinancialEngine:
    def __init__(self):
        # Base assumptions for different gap types
        self.assumptions = {
            "energy": {
                "capex_per_kw": 1200,  # USD per kW installed
                "opex_percent_capex": 0.05,  # 5% annual opex
                "revenue_per_user_monthly": 15.0,
                "pricing_model": "pay-as-you-go_tariff",
            },
            "irrigation": {
                "capex_per_kw": 800,
                "opex_percent_capex": 0.03,
                "revenue_per_user_monthly": 25.0,
                "pricing_model": "water_as_a_service",
            },
            "storage": {
                "capex_per_kw": 1500,
                "opex_percent_capex": 0.04,
                "revenue_per_user_monthly": 40.0,
                "pricing_model": "space_rental",
            },
            "milling": {
                "capex_per_kw": 900,
                "opex_percent_capex": 0.06,
                "revenue_per_user_monthly": 30.0,
                "pricing_model": "fee_per_kg",
            }
        }

    def _estimate_capacity_kw(self, participants: int) -> float:
        """Estimate the required capacity in kW based on participants and activity."""
        return max(10.0, participants * 1.5)

    def _calculate_scenario(self, capacity_kw: float, users: int, capex_modifier: float, revenue_modifier: float, assumptions: Dict) -> FinancialModelScenario:
        capex = capacity_kw * assumptions["capex_per_kw"] * capex_modifier
        annual_opex = capex * assumptions["opex_percent_capex"]
        monthly_opex = annual_opex / 12.0
        
        monthly_revenue = users * assumptions["revenue_per_user_monthly"] * revenue_modifier
        
        net_monthly = monthly_revenue - monthly_opex
        if net_monthly > 0:
            payback_months = capex / net_monthly
        else:
            payback_months = 999.0 # Never pays back
            
        # Simplified IRR
        if payback_months < 24:
            irr = 25.0
        elif payback_months < 48:
            irr = 15.0
        elif payback_months < 84:
            irr = 10.0
        else:
            irr = 3.0
            
        return FinancialModelScenario(
            capex_estimate_usd=round(capex, 2),
            opex_monthly_usd=round(monthly_opex, 2),
            revenue_projection_monthly_usd=round(monthly_revenue, 2),
            payback_period_months=round(payback_months, 1),
            irr=irr
        )

    def generate_model(self, cluster: ClusterOutput, gap: GapOutput) -> FinancialModelOutput:
        """Generates a financial model based on the cluster and gap data."""
        
        # If no gap, no financial model needed or zeroed out
        if gap.gap_type == "none" or gap.urgency_index == "adequate":
            zero_scenario = FinancialModelScenario(capex_estimate_usd=0.0, opex_monthly_usd=0.0, revenue_projection_monthly_usd=0.0, payback_period_months=0.0, irr=0.0)
            return FinancialModelOutput(
                project_name="Adequate Infrastructure - No Investment Required",
                pricing_model="N/A",
                breakeven_users=BoundedValue[int](central_estimate=0, lower_bound=0, upper_bound=0, margin_of_error=0.0),
                scenarios=ScenarioAnalysis(
                    base_case=zero_scenario,
                    optimistic_case=zero_scenario,
                    pessimistic_case=zero_scenario
                )
            )

        asset_type = gap.gap_type
        if asset_type not in self.assumptions:
            asset_type = "energy"

        assumptions = self.assumptions[asset_type]
        
        # Extract bounded values from cluster
        users_central = cluster.estimated_participants.central_estimate
        users_lb = cluster.estimated_participants.lower_bound
        users_ub = cluster.estimated_participants.upper_bound
        
        # Calculate scenarios
        base_scenario = self._calculate_scenario(
            self._estimate_capacity_kw(users_central), users_central, 1.0, 1.0, assumptions)
            
        # Optimistic: lower capex (-10%), higher users (upper bound), better revenue (+10%)
        optimistic_scenario = self._calculate_scenario(
            self._estimate_capacity_kw(users_ub), users_ub, 0.9, 1.1, assumptions)
            
        # Pessimistic: higher capex (+20%), lower users (lower bound), worse revenue (-20%)
        pessimistic_scenario = self._calculate_scenario(
            self._estimate_capacity_kw(users_lb), users_lb, 1.2, 0.8, assumptions)

        # Breakeven calculation based on central scenario
        target_payback = 60 # 5 years
        required_monthly = base_scenario.opex_monthly_usd + (base_scenario.capex_estimate_usd / target_payback)
        breakeven_central = int(required_monthly / assumptions["revenue_per_user_monthly"]) + 1
        
        # Breakeven bounds
        req_mo_pessimistic = pessimistic_scenario.opex_monthly_usd + (pessimistic_scenario.capex_estimate_usd / target_payback)
        breakeven_lb = int(req_mo_pessimistic / (assumptions["revenue_per_user_monthly"] * 0.8)) + 1
        
        req_mo_optimistic = optimistic_scenario.opex_monthly_usd + (optimistic_scenario.capex_estimate_usd / target_payback)
        breakeven_ub = int(req_mo_optimistic / (assumptions["revenue_per_user_monthly"] * 1.1)) + 1

        project_name = f"{cluster.zone_id} {asset_type.capitalize()} Infrastructure"
        
        return FinancialModelOutput(
            project_name=project_name,
            pricing_model=assumptions["pricing_model"],
            breakeven_users=BoundedValue[int](
                central_estimate=breakeven_central,
                lower_bound=min(breakeven_lb, breakeven_ub),
                upper_bound=max(breakeven_lb, breakeven_ub),
                margin_of_error=((max(breakeven_lb, breakeven_ub) - min(breakeven_lb, breakeven_ub)) / (2*max(1, breakeven_central))) * 100.0
            ),
            scenarios=ScenarioAnalysis(
                base_case=base_scenario,
                optimistic_case=optimistic_scenario,
                pessimistic_case=pessimistic_scenario
            )
        )
