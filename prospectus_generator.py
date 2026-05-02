"""
KULIMA OS Pilot - Demand-Signal Prospectus Generator
====================================================

Generates a Demand-Signal Prospectus for institutional decision-makers.

INVARIANT ENFORCEMENT:
- Zero-PII: Prospectus contains only aggregated patterns (no individual data)
- Coordination > Identity: All outputs are coordination-focused
- Semantic Guard: Designed for infrastructure planning, not surveillance or profiling

The prospectus is a verified, bankable document that enables infrastructure investment
decisions based on collective demand patterns, not individual profiling.
"""

import json
from typing import List, Dict
from datetime import datetime


class ProspectusGenerator:
    """
    Generates Demand-Signal Prospectus for institutional decision-makers.
    
    The prospectus combines outputs from LUMOZA and ZENTARI into a single,
    institution-readable document for infrastructure planning.
    """
    
    def __init__(self):
        """Initialize prospectus generator."""
        pass
    
    def generate_prospectus(
        self,
        confidence_results: List[Dict],
        lundai_analysis: Dict = None,
        metadata: Dict = None
    ) -> Dict:
        """
        Generate a Demand-Signal Prospectus.
        
        ZERO-PII ENFORCEMENT:
        - Prospectus contains only aggregated coordination patterns
        - No raw signals, no individual events, no personal data
        
        Args:
            confidence_results: Coordination patterns with confidence scores from ZENTARI
            lundai_analysis: Settlement and infrastructure gap analysis from LUNDAI (optional)
            metadata: Optional metadata about the pilot (region, time period, etc.)
            
        Returns:
            Demand-Signal Prospectus as a dictionary
        """
        
        if metadata is None:
            metadata = {}
        
        # Build prospectus structure
        prospectus = {
            "prospectus_metadata": {
                "title": "KULIMA OS Demand-Signal Prospectus",
                "subtitle": "Verified Coordination Patterns for Infrastructure Planning",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "pilot_region": metadata.get("region", "Pilot Region"),
                "evaluation_period": metadata.get("period", "7-cycle window (1 week)"),
                "system_version": "KULIMA OS Pilot v0.2 (LUMOZA + LUNDAI + Critical Load Protection)"
            },
            
            "executive_summary": self._generate_executive_summary(confidence_results, lundai_analysis),
            
            "coordination_patterns": self._format_patterns_for_institutions(confidence_results),
            
            "settlement_and_infrastructure_analysis": lundai_analysis if lundai_analysis else {"status": "LUNDAI analysis not included"},
            
            "critical_load_protection": self._generate_critical_load_analysis(confidence_results, lundai_analysis),
            
            "infrastructure_planning_guidance": self._generate_planning_guidance(confidence_results, lundai_analysis),
            
            "social_reserve_policy": {
                "description": "20% capacity reserved for communal productive assets",
                "rationale": "Ensures infrastructure serves collective economic activity, not just individual consumption",
                "implementation": "Infrastructure design must include capacity for shared assets (mills, pumps, cold storage)"
            },
            
            "ethics_compliance": {
                "system_invariants": [
                    "Zero-PII: No personal identifiers in any data or outputs",
                    "Temporal Moat: All processing in time-batched windows (no real-time tracking)",
                    "Coordination > Identity: System reasons over collective patterns only",
                    "Semantic Guard: No surveillance, credit scoring, or individual profiling"
                ],
                "verification": "All outputs are auditable against AGENTS.md system invariants",
                "data_governance": "Raw signals are never stored or exported. Only aggregated patterns cross institutional boundary."
            },
            
            "methodology": {
                "signal_sources": [
                    "Human-reported coordination signals (identity-free)",
                    "Infrastructure telemetry (shared assets only, aggregated)"
                ],
                "processing_pipeline": [
                    "1. Signal ingestion (identity-free, scope-enforced)",
                    "2. Time-batching (7-cycle windows, no real-time)",
                    "3. Aggregation (collective patterns, noise filtering)",
                    "4. LUMOZA processing (demand rhythms, stability scores)",
                    "5. ZENTARI evaluation (coordination confidence)",
                    "6. Prospectus generation (institutional outputs only)"
                ],
                "coordination_thresholds": {
                    "stable_pattern": ">=5 of 7 cycles",
                    "noise_threshold": "<3 of 7 cycles",
                    "validation": "Human signals cross-validated with telemetry"
                }
            }
        }
        
        return prospectus
    
    def _generate_executive_summary(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """Generate executive summary of coordination patterns."""
        
        total_patterns = len(confidence_results)
        high_confidence = sum(1 for r in confidence_results if r['confidence_class'] == 'high')
        moderate_confidence = sum(1 for r in confidence_results if r['confidence_class'] == 'moderate')
        
        # Extract unique zones and activities
        zones = set(r['zone'] for r in confidence_results)
        activities = set(r['activity_type'] for r in confidence_results)
        
        summary = {
            "total_coordination_patterns": total_patterns,
            "high_confidence_patterns": high_confidence,
            "moderate_confidence_patterns": moderate_confidence,
            "zones_with_coordinated_demand": list(zones),
            "productive_activities_detected": list(activities),
            "key_finding": f"Detected {total_patterns} stable coordination patterns across {len(zones)} zones, "
                          f"with {high_confidence} patterns showing high confidence for infrastructure investment."
        }
        
        # Add LUNDAI insights if available
        if lundai_analysis and 'overall_assessment' in lundai_analysis:
            overall = lundai_analysis['overall_assessment']
            summary["infrastructure_status"] = overall.get('overall_infrastructure_status', 'Unknown')
            summary["critical_infrastructure_gaps"] = overall.get('critical_infrastructure_gaps', 0)
            summary["urgent_priority_zones"] = overall.get('urgent_priority_zones', 0)
        
        return summary
    
    def _generate_critical_load_analysis(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """
        Generate Critical Load Protection analysis for essential services.
        
        SYSTEM CONSTRAINT: CRITICAL LOAD PROTECTION + LUNDAI INTEGRATION
        Essential communal services (clinics, schools, water systems, emergency infrastructure)
        are non-negotiable priority loads that must be protected in capacity planning.
        
        This analysis:
        1. Identifies recurring essential-service demand patterns (LUMOZA)
        2. Assesses settlement context and infrastructure gaps (LUNDAI)
        3. Simulates baseline, peak, and shock scenarios
        4. Calculates required capacity reservation with LUNDAI-informed adjustments
        5. Ensures this capacity is excluded from optimization/monetization logic
        """
        # Separate essential and productive patterns
        essential_patterns = [p for p in confidence_results if p.get('service_priority') == 'essential']
        productive_patterns = [p for p in confidence_results if p.get('service_priority') == 'productive']
        
        # Calculate essential service load profile
        essential_zones = set(p['zone'] for p in essential_patterns)
        essential_activities = set(p['activity_type'] for p in essential_patterns)
        
        # Determine capacity reservation percentage with LUNDAI-informed adjustments
        # Base: 20%, adjusted based on essential service density AND infrastructure gaps
        base_reservation = 20
        
        if len(essential_patterns) == 0:
            reservation_percentage = 0
            reservation_note = "No essential services detected. Standard capacity planning applies."
        elif len(essential_patterns) >= len(productive_patterns):
            reservation_percentage = 30
            reservation_note = "High essential service density. 30% capacity reserved for critical loads."
        else:
            reservation_percentage = base_reservation
            reservation_note = f"Standard essential service protection. {base_reservation}% capacity reserved for critical loads."
        
        # LUNDAI-informed adjustment: increase reservation for critical infrastructure gaps
        if lundai_analysis and 'zone_analyses' in lundai_analysis:
            critical_gap_zones = [
                zone for zone, analysis in lundai_analysis['zone_analyses'].items()
                if analysis.get('gap_severity') in ['critical', 'severe'] and zone in essential_zones
            ]
            
            if critical_gap_zones:
                # Increase reservation by 10% for zones with critical gaps and essential services
                reservation_percentage = min(reservation_percentage + 10, 40)
                reservation_note += f" Increased by 10% due to critical infrastructure gaps in {len(critical_gap_zones)} zone(s) with essential services."
        
        # Scenario analysis
        scenarios = {
            "baseline": {
                "description": "Normal operation with all essential services active",
                "essential_load_percentage": reservation_percentage,
                "available_for_productive_use": 100 - reservation_percentage
            },
            "peak": {
                "description": "Peak demand when all services operate simultaneously",
                "essential_load_percentage": min(reservation_percentage * 1.5, 40),
                "available_for_productive_use": max(100 - (reservation_percentage * 1.5), 60)
            },
            "shock": {
                "description": "Emergency scenario requiring maximum essential service capacity",
                "essential_load_percentage": min(reservation_percentage * 2, 50),
                "available_for_productive_use": max(100 - (reservation_percentage * 2), 50)
            }
        }
        
        return {
            "enforcement_status": "ACTIVE - Architecturally enforced, cannot be overridden",
            "essential_service_count": len(essential_patterns),
            "productive_activity_count": len(productive_patterns),
            "zones_with_essential_services": sorted(list(essential_zones)),
            "essential_service_types": sorted(list(essential_activities)),
            "capacity_reservation": {
                "percentage": reservation_percentage,
                "rationale": reservation_note,
                "enforcement": "Reserved capacity is excluded from optimization, monetization, and load-shedding logic"
            },
            "scenario_analysis": scenarios,
            "planning_requirements": [
                f"Infrastructure MUST reserve {reservation_percentage}% capacity for essential services",
                "Essential service loads cannot be shed during peak demand periods",
                "Productive use optimization must operate within remaining capacity only",
                "Emergency scenarios require ability to scale essential capacity to 50%"
            ],
            "non_negotiable_loads": [
                {
                    "activity": p['activity_type'],
                    "zone": p['zone'],
                    "time_window": p['time_window'],
                    "stability": p['demand_rhythm']['stability_class'],
                    "priority": "CRITICAL - Cannot be interrupted"
                }
                for p in essential_patterns
            ]
        }
    
    def _format_patterns_for_institutions(self, confidence_results: List[Dict]) -> List[Dict]:
        """Format coordination patterns for institutional decision-makers."""
        
        formatted_patterns = []
        
        for result in confidence_results:
            pattern = {
                "pattern_id": f"{result['zone']}_{result['activity_type']}_{result['time_window']}",
                "activity_type": result['activity_type'],
                "zone": result['zone'],
                "demand_rhythm": {
                    "time_window": result['time_window'],
                    "frequency": result['demand_rhythm']['frequency'],
                    "stability_class": result['demand_rhythm']['stability_class']
                },
                "coordination_confidence": {
                    "score": result['coordination_confidence'],
                    "class": result['confidence_class'],
                    "bankability": result['bankability_note']
                },
                "validation": {
                    "strength": result['validation_strength'],
                    "details": result['validation_details']
                },
                "infrastructure_implication": self._get_infrastructure_implication(result)
            }
            
            formatted_patterns.append(pattern)
        
        return formatted_patterns
    
    def _get_infrastructure_implication(self, result: Dict) -> str:
        """Derive infrastructure planning implications from coordination pattern."""
        
        activity = result['activity_type']
        confidence = result['confidence_class']
        time_window = result['time_window']
        
        implications = {
            'irrigation': f"Requires reliable {time_window} power for water pumping. Consider three-phase capacity.",
            'milling': f"Requires high-power {time_window} capacity for grain processing. Peak demand periods.",
            'cold_storage': f"Requires continuous {time_window} power for cold chain. Critical for food security.",
            'welding': f"Requires high-power {time_window} capacity for metalwork. Industrial load profile."
        }
        
        base_implication = implications.get(activity, f"Productive use demand in {time_window} window.")
        
        if confidence == 'high':
            return f"{base_implication} HIGH PRIORITY for infrastructure investment."
        elif confidence == 'moderate':
            return f"{base_implication} MODERATE PRIORITY. Monitor for stability."
        else:
            return f"{base_implication} LOW PRIORITY. Requires further validation."
    
    def _generate_planning_guidance(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """Generate infrastructure planning guidance with LUNDAI integration."""
        
        high_priority_zones = set()
        moderate_priority_zones = set()
        
        for result in confidence_results:
            if result['confidence_class'] == 'high':
                high_priority_zones.add(result['zone'])
            elif result['confidence_class'] == 'moderate':
                moderate_priority_zones.add(result['zone'])
        
        guidance = {
            "high_priority_zones": list(high_priority_zones),
            "moderate_priority_zones": list(moderate_priority_zones),
            "investment_recommendation": self._get_investment_recommendation(
                len(high_priority_zones),
                len(moderate_priority_zones)
            ),
            "capacity_planning_note": "Infrastructure capacity must account for productive-use demand patterns, "
                                     "not just household consumption. Social reserve enforced for essential services."
        }
        
        # Add LUNDAI-informed zone prioritization
        if lundai_analysis and 'zone_analyses' in lundai_analysis:
            urgent_zones = [
                zone for zone, analysis in lundai_analysis['zone_analyses'].items()
                if analysis.get('priority_classification') == 'urgent'
            ]
            
            if urgent_zones:
                guidance["urgent_infrastructure_zones"] = urgent_zones
                guidance["lundai_recommendation"] = f"URGENT: {len(urgent_zones)} zone(s) require immediate infrastructure intervention due to critical gaps and essential service presence."
        
        return guidance
    
    def _get_investment_recommendation(self, high_priority_count: int, moderate_priority_count: int) -> str:
        """Generate investment recommendation based on priority zones."""
        
        if high_priority_count > 0:
            return f"RECOMMENDED: Prioritize infrastructure deployment in {high_priority_count} high-confidence zone(s). " \
                   f"Coordination patterns are stable and validated, indicating bankable demand."
        elif moderate_priority_count > 0:
            return f"CONDITIONAL: {moderate_priority_count} zone(s) show moderate coordination. " \
                   f"Consider phased deployment with continued monitoring."
        else:
            return "INSUFFICIENT: No high-confidence patterns detected. Continue signal collection and validation."
    
    def save_prospectus_json(self, prospectus: Dict, filename: str = "demand_signal_prospectus.json") -> None:
        """Save prospectus as JSON file."""
        with open(filename, 'w') as f:
            json.dump(prospectus, f, indent=2)
        print(f"\nProspectus saved to: {filename}")
    
    def save_prospectus_markdown(self, prospectus: Dict, filename: str = "demand_signal_prospectus.md") -> None:
        """
        Save prospectus as Markdown file for human readability.
        
        Note: Uses UTF-8 encoding to ensure cross-platform compatibility (Windows fix).
        """
        
        md_content = f"""# {prospectus['prospectus_metadata']['title']}

## {prospectus['prospectus_metadata']['subtitle']}

**Generated:** {prospectus['prospectus_metadata']['generated_at']}  
**Region:** {prospectus['prospectus_metadata']['pilot_region']}  
**Period:** {prospectus['prospectus_metadata']['evaluation_period']}  
**System:** {prospectus['prospectus_metadata']['system_version']}

---

## Executive Summary

{prospectus['executive_summary']['key_finding']}

- **Total Coordination Patterns:** {prospectus['executive_summary']['total_coordination_patterns']}
- **High Confidence Patterns:** {prospectus['executive_summary']['high_confidence_patterns']}
- **Moderate Confidence Patterns:** {prospectus['executive_summary']['moderate_confidence_patterns']}
- **Zones with Coordinated Demand:** {', '.join(prospectus['executive_summary']['zones_with_coordinated_demand'])}
- **Productive Activities Detected:** {', '.join(prospectus['executive_summary']['productive_activities_detected'])}

---

## Coordination Patterns

"""
        
        for i, pattern in enumerate(prospectus['coordination_patterns'], 1):
            md_content += f"""
### Pattern {i}: {pattern['pattern_id']}

- **Activity:** {pattern['activity_type']}
- **Zone:** {pattern['zone']}
- **Time Window:** {pattern['demand_rhythm']['time_window']}
- **Frequency:** {pattern['demand_rhythm']['frequency']}
- **Stability:** {pattern['demand_rhythm']['stability_class']}
- **Coordination Confidence:** {pattern['coordination_confidence']['score']} ({pattern['coordination_confidence']['class']})
- **Validation:** {pattern['validation']['strength']} - {pattern['validation']['details']}
- **Infrastructure Implication:** {pattern['infrastructure_implication']}

"""
        
        md_content += f"""
---

## Critical Load Protection

**Enforcement Status:** {prospectus['critical_load_protection']['enforcement_status']}

**Essential Services Detected:** {prospectus['critical_load_protection']['essential_service_count']}
**Productive Activities Detected:** {prospectus['critical_load_protection']['productive_activity_count']}

**Zones with Essential Services:** {', '.join(prospectus['critical_load_protection']['zones_with_essential_services']) if prospectus['critical_load_protection']['zones_with_essential_services'] else 'None'}

**Essential Service Types:** {', '.join(prospectus['critical_load_protection']['essential_service_types']) if prospectus['critical_load_protection']['essential_service_types'] else 'None'}

### Capacity Reservation

**Reserved Capacity:** {prospectus['critical_load_protection']['capacity_reservation']['percentage']}%

**Rationale:** {prospectus['critical_load_protection']['capacity_reservation']['rationale']}

**Enforcement:** {prospectus['critical_load_protection']['capacity_reservation']['enforcement']}

### Scenario Analysis

"""
        
        for scenario_name, scenario_data in prospectus['critical_load_protection']['scenario_analysis'].items():
            md_content += f"""
**{scenario_name.upper()} Scenario:**
- Description: {scenario_data['description']}
- Essential Load: {scenario_data['essential_load_percentage']}%
- Available for Productive Use: {scenario_data['available_for_productive_use']}%
"""
        
        md_content += "\n### Planning Requirements\n\n"
        for req in prospectus['critical_load_protection']['planning_requirements']:
            md_content += f"- {req}\n"
        
        if prospectus['critical_load_protection']['non_negotiable_loads']:
            md_content += "\n### Non-Negotiable Loads\n\n"
            for load in prospectus['critical_load_protection']['non_negotiable_loads']:
                md_content += f"""
**{load['activity']}** ({load['zone']})
- Time Window: {load['time_window']}
- Stability: {load['stability']}
- Priority: {load['priority']}
"""
        
        md_content += f"""
---

## Infrastructure Planning Guidance

**High Priority Zones:** {', '.join(prospectus['infrastructure_planning_guidance']['high_priority_zones']) if prospectus['infrastructure_planning_guidance']['high_priority_zones'] else 'None'}

**Moderate Priority Zones:** {', '.join(prospectus['infrastructure_planning_guidance']['moderate_priority_zones']) if prospectus['infrastructure_planning_guidance']['moderate_priority_zones'] else 'None'}

**Investment Recommendation:**  
{prospectus['infrastructure_planning_guidance']['investment_recommendation']}

**Capacity Planning Note:**  
{prospectus['infrastructure_planning_guidance']['capacity_planning_note']}

---

## Social Reserve Policy

**Description:** {prospectus['social_reserve_policy']['description']}

**Rationale:** {prospectus['social_reserve_policy']['rationale']}

**Implementation:** {prospectus['social_reserve_policy']['implementation']}

---

## Ethics Compliance

### System Invariants

"""
        
        for invariant in prospectus['ethics_compliance']['system_invariants']:
            md_content += f"- {invariant}\n"
        
        md_content += f"""
**Verification:** {prospectus['ethics_compliance']['verification']}

**Data Governance:** {prospectus['ethics_compliance']['data_governance']}

---

## Methodology

### Signal Sources

"""
        
        for source in prospectus['methodology']['signal_sources']:
            md_content += f"- {source}\n"
        
        md_content += "\n### Processing Pipeline\n\n"
        
        for step in prospectus['methodology']['processing_pipeline']:
            md_content += f"{step}\n"
        
        md_content += f"""
### Coordination Thresholds

- **Stable Pattern:** {prospectus['methodology']['coordination_thresholds']['stable_pattern']}
- **Noise Threshold:** {prospectus['methodology']['coordination_thresholds']['noise_threshold']}
- **Validation:** {prospectus['methodology']['coordination_thresholds']['validation']}

---

*This prospectus is generated by KULIMA OS, a coordination-first economic substrate designed as Digital Public Infrastructure (DPI). It enables infrastructure planning based on verified collective demand, without surveillance or individual profiling.*
"""
        
        # Use UTF-8 encoding explicitly for cross-platform compatibility (fixes Windows UnicodeEncodeError)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"Prospectus saved to: {filename}")


if __name__ == "__main__":
    # Test prospectus generation
    from pilot_signals import generate_pilot_signals
    from lumoza_engine import LumozaEngine
    from zentari_engine import ZentariEngine
    
    print("Generating Demand-Signal Prospectus...")
    
    # Process signals through engines
    signals = generate_pilot_signals()
    lumoza = LumozaEngine()
    patterns = lumoza.process_signals(signals)
    
    zentari = ZentariEngine()
    confidence_results = zentari.evaluate_coordination_confidence(patterns)
    
    # Generate prospectus
    generator = ProspectusGenerator()
    prospectus = generator.generate_prospectus(
        confidence_results,
        metadata={
            "region": "Pilot Region - Rural Energy Planning",
            "period": "7-cycle window (Week 1)"
        }
    )
    
    # Save in both formats
    generator.save_prospectus_json(prospectus)
    generator.save_prospectus_markdown(prospectus)
    
    print("\n✓ Demand-Signal Prospectus generated successfully")

# Made with Bob
