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
        metadata: Dict = None
    ) -> Dict:
        """
        Generate a Demand-Signal Prospectus.
        
        ZERO-PII ENFORCEMENT:
        - Prospectus contains only aggregated coordination patterns
        - No raw signals, no individual events, no personal data
        
        Args:
            confidence_results: Coordination patterns with confidence scores from ZENTARI
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
                "system_version": "KULIMA OS Pilot v0.1"
            },
            
            "executive_summary": self._generate_executive_summary(confidence_results),
            
            "coordination_patterns": self._format_patterns_for_institutions(confidence_results),
            
            "infrastructure_planning_guidance": self._generate_planning_guidance(confidence_results),
            
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
    
    def _generate_executive_summary(self, confidence_results: List[Dict]) -> Dict:
        """Generate executive summary of coordination patterns."""
        
        total_patterns = len(confidence_results)
        high_confidence = sum(1 for r in confidence_results if r['confidence_class'] == 'high')
        moderate_confidence = sum(1 for r in confidence_results if r['confidence_class'] == 'moderate')
        
        # Extract unique zones and activities
        zones = set(r['zone'] for r in confidence_results)
        activities = set(r['activity_type'] for r in confidence_results)
        
        return {
            "total_coordination_patterns": total_patterns,
            "high_confidence_patterns": high_confidence,
            "moderate_confidence_patterns": moderate_confidence,
            "zones_with_coordinated_demand": list(zones),
            "productive_activities_detected": list(activities),
            "key_finding": f"Detected {total_patterns} stable coordination patterns across {len(zones)} zones, "
                          f"with {high_confidence} patterns showing high confidence for infrastructure investment."
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
    
    def _generate_planning_guidance(self, confidence_results: List[Dict]) -> Dict:
        """Generate infrastructure planning guidance."""
        
        high_priority_zones = set()
        moderate_priority_zones = set()
        
        for result in confidence_results:
            if result['confidence_class'] == 'high':
                high_priority_zones.add(result['zone'])
            elif result['confidence_class'] == 'moderate':
                moderate_priority_zones.add(result['zone'])
        
        return {
            "high_priority_zones": list(high_priority_zones),
            "moderate_priority_zones": list(moderate_priority_zones),
            "investment_recommendation": self._get_investment_recommendation(
                len(high_priority_zones),
                len(moderate_priority_zones)
            ),
            "capacity_planning_note": "Infrastructure capacity must account for productive-use demand patterns, "
                                     "not just household consumption. Include 20% social reserve for communal assets."
        }
    
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
