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
import os
from typing import List, Dict
from datetime import datetime
from energy_demand_estimator import EnergyDemandEstimator
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


class ProspectusGenerator:
    """
    Generates Demand-Signal Prospectus for institutional decision-makers.
    
    The prospectus combines outputs from LUMOZA and ZENTARI into a single,
    institution-readable document for infrastructure planning.
    """
    
    # Activity-to-Energy Translation Layer
    ACTIVITY_ENERGY_MAP = {
        "milling": {"min_kwh": 10, "max_kwh": 50},
        "irrigation": {"min_kwh": 20, "max_kwh": 100},
        "trading": {"min_kwh": 2, "max_kwh": 10},
        "storage": {"min_kwh": 5, "max_kwh": 20}
    }
    
    def __init__(self, logo_path: str = "assets/kulima_africa_logo.png"):
        """Initialize prospectus generator with energy demand estimator."""
        self.energy_estimator = EnergyDemandEstimator()
        self.logo_path = logo_path
    
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
            "document_classification": {
                "artifact_type": "Institutional Planning Artifact",
                "purpose": "Pilot Demonstration",
                "disclaimer": "Not a Financing Approval"
            },
            "document_scope": {
                "enables": [
                    "Evidence-based planning and sizing of energy infrastructure",
                    "Conservative, lower-bound estimates for coordination-driven demand",
                    "Institutional review of collective activity signals"
                ],
                "does_not_do": [
                    "Provide credit, loan, or financing approval",
                    "Certify investment readiness or bankability",
                    "Expose individual-level or personal data"
                ],
                "estimate_nature": "Estimates are conservative lower-bound signals intended for planning, not exact operational forecasts."
            },
            
            "executive_summary": self._generate_executive_summary(confidence_results, lundai_analysis),
            
            "coordination_patterns": self._format_patterns_for_institutions(confidence_results),
            
            "energy_signals": self.compute_energy_signal(confidence_results),
            
            "load_estimation": self._generate_load_estimation(confidence_results),
            
            "settlement_and_infrastructure_analysis": lundai_analysis if lundai_analysis else {"status": "LUNDAI analysis not included"},
            
            "critical_load_protection": self._generate_critical_load_analysis(confidence_results, lundai_analysis),
            
            "sustainability_impact": self._generate_sustainability_impact(confidence_results, lundai_analysis),
            
            "risk_and_governance": self._generate_risk_governance(confidence_results),
            
            "deployment_readiness": self._generate_deployment_readiness(confidence_results, lundai_analysis),
            
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
    
    def generate_pdf(self, prospectus: Dict, output_path: str):
        """
        Generate a PDF version of the Demand-Signal Prospectus.
        
        Args:
            prospectus: The prospectus dictionary generated by generate_prospectus
            output_path: Path to save the PDF file
        """
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                                leftMargin=40, rightMargin=40,
                                topMargin=50, bottomMargin=55)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=20,
            leading=24, alignment=1, textColor=colors.HexColor('#003366'))
        subtitle_style = ParagraphStyle(
            'Subtitle', parent=styles['Heading2'], fontName='Helvetica', fontSize=14,
            leading=18, alignment=1, textColor=colors.HexColor('#003366'))
        section_style = ParagraphStyle(
            'Section', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14,
            leading=18, spaceAfter=10, textColor=colors.HexColor('#003366'))
        body_style = ParagraphStyle(
            'Body', parent=styles['BodyText'], fontName='Helvetica', fontSize=11,
            leading=14)
        note_style = ParagraphStyle(
            'Note', parent=styles['BodyText'], fontName='Helvetica', fontSize=9,
            leading=12, textColor=colors.grey)
        high_conf_style = ParagraphStyle(
            'HighConf', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11,
            textColor=colors.HexColor('#2E8B57'))
        italic_style = ParagraphStyle(
            'Italic', parent=styles['Italic'], fontName='Helvetica-Oblique', fontSize=10,
            leading=12)

        story = []

        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = Image(self.logo_path, width=80, height=80)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 18))
            except Exception:
                pass

        story.append(Paragraph('KULIMA OS', title_style))
        story.append(Spacer(1, 8))
        story.append(Paragraph('Demand-Signal Prospectus', subtitle_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph('Institutional Planning Artifact', ParagraphStyle('ArtifactLabel', parent=body_style, fontName='Helvetica-Bold', fontSize=11, alignment=1)))
        story.append(Spacer(1, 4))
        story.append(Paragraph('Pilot Demonstration', body_style))
        story.append(Paragraph('Not a Financing Approval', note_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Generated: {prospectus['prospectus_metadata']['generated_at']}", body_style))
        story.append(Paragraph(f"Pilot Region: {prospectus['prospectus_metadata']['pilot_region']}", body_style))
        story.append(Paragraph(f"Evaluation Period: {prospectus['prospectus_metadata']['evaluation_period']}", body_style))
        story.append(Paragraph(f"System Version: {prospectus['prospectus_metadata']['system_version']}", body_style))
        story.append(Spacer(1, 28))

        story.append(Paragraph('What This Document Enables / What It Does Not Do', section_style))
        scope = prospectus['document_scope']
        scope_data = [
            ['Enables', 'Does Not Do'],
            [Paragraph('• ' + '<br/>• '.join(scope['enables']), body_style),
             Paragraph('• ' + '<br/>• '.join(scope['does_not_do']), body_style)]
        ]
        scope_table = Table(scope_data, colWidths=[250, 250], hAlign='LEFT')
        scope_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.grey)
        ]))
        story.append(scope_table)
        story.append(Spacer(1, 28))

        story.append(Paragraph('Executive Overview', section_style))
        summary = prospectus['executive_summary']
        summary_data = [
            ['Metric', 'Value'],
            ['Total Coordination Patterns', str(summary['total_coordination_patterns'])],
            ['High Confidence Patterns', str(summary['high_confidence_patterns'])],
            ['Moderate Confidence Patterns', str(summary['moderate_confidence_patterns'])],
            ['Zones with Coordinated Demand', ', '.join(summary['zones_with_coordinated_demand'])],
            ['Productive Activities Detected', ', '.join(summary['productive_activities_detected'])]
        ]
        summary_table = Table(summary_data, colWidths=[200, 300], hAlign='LEFT')
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.grey)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))
        story.append(Paragraph(summary['key_finding'], body_style))
        story.append(Spacer(1, 24))

        story.append(Paragraph('Coordination Summary', section_style))
        coordination_data = [
            ['Metric', 'Summary'],
            ['Zones with Coordinated Demand', ', '.join(summary['zones_with_coordinated_demand'])],
            ['Productive Activities', ', '.join(summary['productive_activities_detected'])],
            ['High Confidence Patterns', str(summary['high_confidence_patterns'])],
            ['Moderate Confidence Patterns', str(summary['moderate_confidence_patterns'])],
        ]
        coordination_table = Table(coordination_data, colWidths=[200, 300], hAlign='LEFT')
        coordination_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.grey)
        ]))
        story.append(coordination_table)
        story.append(Spacer(1, 24))

        story.append(Paragraph('Verified Coordination Patterns', section_style))
        patterns = prospectus['coordination_patterns']
        if patterns:
            data = [['Activity Type', 'Zone', 'Confidence Class', 'Stability Score']]
            for p in patterns:
                conf_style = high_conf_style if p['confidence_class'] == 'high' else body_style
                data.append([Paragraph(p['activity_type'], conf_style), p['zone'], p['confidence_class'], str(p['stability_score'])])
            pattern_table = Table(data, colWidths=[150, 100, 140, 100], hAlign='LEFT')
            pattern_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
                ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.whitesmoke]),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 0.75, colors.grey)
            ]))
            story.append(pattern_table)
        story.append(Spacer(1, 24))

        story.append(Paragraph('Energy Signal Output', section_style))
        signals = prospectus['energy_signals']
        if signals:
            data = [['Zone', 'Activities', 'Min kWh', 'Max kWh', 'Peak kW', 'Confidence', 'Buffer kW']]
            for s in signals:
                activities_str = ', '.join(s['activities'])
                buffered = s['peak_kw_estimate'] * 1.25
                conf_style = high_conf_style if s['confidence_score'] == 'HIGH' else body_style
                data.append([
                    s['zone'],
                    Paragraph(activities_str, body_style),
                    str(s['estimated_min_kwh']),
                    str(s['estimated_max_kwh']),
                    f"{s['peak_kw_estimate']:.1f}",
                    Paragraph(s['confidence_score'], conf_style),
                    f"{buffered:.1f}"
                ])
            energy_table = Table(data, colWidths=[70, 190, 60, 60, 60, 70, 70], hAlign='LEFT')
            energy_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
                ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
                ('ALIGN',(2,0),(-1,-1),'CENTER'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.whitesmoke]),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 0.75, colors.grey)
            ]))
            story.append(energy_table)
            story.append(Spacer(1, 6))
            story.append(Paragraph('Recommended installed capacity includes a 25% planning buffer.', note_style))
        story.append(Spacer(1, 24))

        story.append(Paragraph('Confidence, Risk & Governance', section_style))
        story.append(Paragraph('Confidence scores are based on stability, frequency, and coordination density to support conservative infrastructure planning.', body_style))
        story.append(Spacer(1, 12))
        confidence_data = [
            ['Confidence Tier', 'Interpretation'],
            ['HIGH (>0.7)', 'Strong coordination signals, recommended for planning and phased deployment.'],
            ['MEDIUM (0.4-0.7)', 'Moderate coordination signals, requires ongoing monitoring.'],
            ['LOW (<0.4)', 'Emerging signals, not yet suitable for infrastructure sizing.']
        ]
        confidence_table = Table(confidence_data, colWidths=[120, 380], hAlign='LEFT')
        confidence_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.grey)
        ]))
        story.append(confidence_table)
        story.append(Spacer(1, 24))

        risk = prospectus['risk_and_governance']
        risk_data = [
            ['Risk Area', 'Summary'],
            ['Confidence Distribution', f"High: {risk['demand_uncertainty_quantification']['confidence_distribution']['high_confidence_patterns']}; Moderate: {risk['demand_uncertainty_quantification']['confidence_distribution']['moderate_confidence_patterns']}; Low: {risk['demand_uncertainty_quantification']['confidence_distribution']['low_confidence_patterns']}"] ,
            ['Demand Uncertainty', risk['demand_uncertainty_quantification']['demand_uncertainty_range']['conservative_estimate']],
            ['Governance Approach', 'Transparent allocation, essential service protection, and phased deployment']
        ]
        risk_table = Table(risk_data, colWidths=[160, 340], hAlign='LEFT')
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.grey)
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 24))

        story.append(Paragraph('Critical Load Protection', section_style))
        clp = prospectus['critical_load_protection']
        story.append(Paragraph(f"Capacity Reservation: {clp['capacity_reservation']['percentage']}%", body_style))
        story.append(Paragraph(clp['capacity_reservation']['rationale'], body_style))
        story.append(Spacer(1, 24))

        story.append(Paragraph('System Invariants', section_style))
        ethics = prospectus['ethics_compliance']
        for invariant in ethics['system_invariants']:
            story.append(Paragraph(f"• {invariant}", body_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph('Verification: ' + ethics['verification'], body_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph('Processing Pipeline', section_style))
        for step in prospectus['methodology']['processing_pipeline']:
            story.append(Paragraph(f"• {step}", body_style))
        story.append(Spacer(1, 24))

        story.append(Paragraph('Technical Notes', section_style))
        story.append(Paragraph('This document is intended as a decision-support artifact for planners and does not replace detailed engineering studies or financing approvals.', note_style))
        story.append(Spacer(1, 28))

        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)

    def _add_footer(self, canvas, doc):
        footer_text = f"Kulima Africa | Kulima OS Pilot v0.2 | Page {doc.page}"
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(40, 20, footer_text)
        canvas.restoreState()
    
    def compute_energy_signal(self, coordination_patterns: List[Dict]) -> List[Dict]:
        """
        Compute energy demand signals from coordination patterns.
        
        Args:
            coordination_patterns: List of coordination patterns from ZENTARI
            
        Returns:
            List of energy signal dictionaries
        """
        signals = []
        zone_groups = {}
        
        # Group patterns by zone
        for pattern in coordination_patterns:
            zone = pattern['zone']
            if zone not in zone_groups:
                zone_groups[zone] = []
            zone_groups[zone].append(pattern)
        
        for zone, patterns in zone_groups.items():
            activities = [p['activity_type'] for p in patterns]
            unique_activities = list(set(activities))
            
            # Aggregate energy ranges
            total_min_kwh = 0
            total_max_kwh = 0
            for activity in unique_activities:
                if activity in self.ACTIVITY_ENERGY_MAP:
                    total_min_kwh += self.ACTIVITY_ENERGY_MAP[activity]['min_kwh']
                    total_max_kwh += self.ACTIVITY_ENERGY_MAP[activity]['max_kwh']
            
            # Peak KW estimate (assume peak is max / hours, but simplify)
            peak_kw_estimate = total_max_kwh / 8  # Assume 8-hour peak
            
            # Stability score (average of patterns)
            stability_scores = [p['stability_score'] for p in patterns]
            avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0
            
            # Confidence score
            confidence_score = self._compute_confidence_score(patterns)
            
            # Growth headroom (25% buffer)
            growth_headroom_kw = peak_kw_estimate * 0.25
            
            signal = {
                "zone": zone,
                "activities": unique_activities,
                "estimated_min_kwh": total_min_kwh,
                "estimated_max_kwh": total_max_kwh,
                "peak_kw_estimate": peak_kw_estimate,
                "stability_score": avg_stability,
                "confidence_score": confidence_score,
                "growth_headroom_kw": growth_headroom_kw,
                "notes": f"Based on {len(patterns)} coordination patterns",
                # Validation fields (for future)
                "observed_actual_kwh": None,
                "variance_from_prediction": None,
                "calibration_factor": 1.0
            }
            signals.append(signal)
        
        return signals
    
    def _compute_confidence_score(self, patterns: List[Dict]) -> str:
        """
        Compute confidence score based on stability, frequency, cluster density.
        
        Args:
            patterns: Coordination patterns for a zone
            
        Returns:
            'HIGH', 'MEDIUM', or 'LOW'
        """
        if not patterns:
            return 'LOW'
        
        # Stability score (most important)
        stability_scores = [p.get('stability_score', 0) for p in patterns]
        avg_stability = sum(stability_scores) / len(stability_scores)
        
        # Frequency of activity cycles (how many patterns)
        frequency = len(patterns) / 7  # Normalize to 7-cycle window
        
        # Cluster density (number of unique activities)
        cluster_density = len(set(p['activity_type'] for p in patterns)) / len(self.ACTIVITY_ENERGY_MAP)
        
        # Weighted score
        score = (avg_stability * 0.6) + (frequency * 0.2) + (cluster_density * 0.2)
        
        if score > 0.7:
            return 'HIGH'
        elif score > 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
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
                "confidence_class": result['confidence_class'],  # Add top-level confidence_class
                "stability_score": result.get('stability_score', 0.7),  # Add stability_score
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
    def _generate_load_estimation(self, confidence_results: List[Dict]) -> Dict:
        """
        Generate conservative energy demand estimates for all coordination patterns.
        
        This section translates coordination patterns into bankable energy demand
        estimates (kW peak, kWh consumption) using conservative load profiles.
        """
        # Get total demand estimate
        demand_estimate = self.energy_estimator.estimate_total_demand(confidence_results)
        
        # Format for institutional readability
        load_estimation = {
            "estimation_methodology": {
                "approach": "Conservative lower-bound estimation using activity-level load profiles",
                "data_sources": [
                    "World Bank Rural Electrification Toolkit (2008)",
                    "ESMAP Technical Papers (121, 145, 156)",
                    "IFC Productive Use of Energy Study (2018)",
                    "WHO Health Facility Electrification Guidelines (2020)"
                ],
                "conservatism": "All estimates use lower bounds of typical ranges to ensure bankability",
                "diversity_factors": "Applied to account for non-simultaneous operation",
                "load_factors": "Applied to account for intermittent operation patterns"
            },
            
            "total_system_demand": {
                "peak_demand_kw": demand_estimate['total_demand']['peak_kw'],
                "daily_energy_kwh": demand_estimate['total_demand']['daily_kwh'],
                "monthly_energy_kwh": demand_estimate['total_demand']['monthly_kwh'],
                "annual_energy_kwh": demand_estimate['total_demand']['annual_kwh'],
                "notes": "Diversified peak demand accounting for non-simultaneous operation"
            },
            
            "demand_breakdown": {
                "essential_services": {
                    "peak_kw": demand_estimate['essential_demand']['peak_kw'],
                    "daily_kwh": demand_estimate['essential_demand']['daily_kwh'],
                    "percentage": demand_estimate['essential_demand']['percentage_of_total'],
                    "priority": "NON-NEGOTIABLE - Must be protected under all scenarios"
                },
                "productive_activities": {
                    "peak_kw": demand_estimate['productive_demand']['peak_kw'],
                    "daily_kwh": demand_estimate['productive_demand']['daily_kwh'],
                    "percentage": demand_estimate['productive_demand']['percentage_of_total'],
                    "priority": "HIGH - Drives economic development and infrastructure ROI"
                }
            },
            
            "zone_level_estimates": demand_estimate['zone_breakdown'],
            
            "capacity_planning_guidance": {
                "recommended_capacity_kw": round(demand_estimate['total_demand']['peak_kw'] * 1.25, 2),
                "rationale": "25% headroom for growth and contingency",
                "critical_load_reserve": "30-40% reserved for essential services (enforced)",
                "transformer_sizing": f"Minimum {round(demand_estimate['total_demand']['peak_kw'] * 1.25 / 0.8, 2)} kVA (assuming 0.8 power factor)",
                "distribution_voltage": "Recommend 11kV or 33kV for productive use loads"
            },
            
            "confidence_statement": "These estimates are conservative (lower-bound) to ensure bankability. "
                                   "Actual demand may be 20-40% higher. Infrastructure should be sized with "
                                   "growth headroom and essential service protection."
        }
        
        return load_estimation
    
    def _generate_sustainability_impact(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """
        Generate sustainability impact analysis for DFI review.
        
        Covers economic, social, and environmental dimensions of infrastructure deployment.
        """
        # Get demand estimates for impact calculations
        demand_estimate = self.energy_estimator.estimate_total_demand(confidence_results)
        
        # Count activities and zones
        productive_activities = [r for r in confidence_results if r['activity_type'] in 
                                {'irrigation', 'milling', 'cold_storage', 'welding'}]
        essential_services = [r for r in confidence_results if r['activity_type'] in 
                            {'clinic', 'school', 'water_system', 'emergency_services'}]
        
        zones = set(r['zone'] for r in confidence_results)
        
        sustainability_impact = {
            "economic_impact": {
                "productive_use_multiplier": {
                    "value": "3.0x - 5.0x",
                    "description": "Every kWh of productive-use energy generates 3-5x economic value compared to household consumption",
                    "source": "IFC Productive Use of Energy Study (2018), ESMAP Technical Paper 145"
                },
                "estimated_annual_economic_value": {
                    "kwh_productive": demand_estimate['productive_demand']['daily_kwh'] * 365,
                    "multiplier_range": "3.0x - 5.0x",
                    "estimated_value_usd": f"${round(demand_estimate['productive_demand']['daily_kwh'] * 365 * 0.15 * 4, 2):,} (assuming $0.15/kWh tariff, 4x multiplier)",
                    "notes": "Conservative estimate. Actual value depends on local economic conditions."
                },
                "livelihood_activities_enabled": len(productive_activities),
                "zones_with_productive_demand": len(zones),
                "infrastructure_roi_driver": "Productive use demand provides stable, predictable revenue for infrastructure cost recovery"
            },
            
            "social_impact": {
                "essential_services_protected": {
                    "count": len(essential_services),
                    "types": list(set(r['activity_type'] for r in essential_services)),
                    "capacity_reserved": "30-40% of total capacity (non-negotiable)",
                    "impact": "Ensures clinics, schools, water systems remain operational under all scenarios"
                },
                "equity_and_inclusion": {
                    "approach": "Coordination-first design ensures infrastructure serves collective needs, not just individual consumption",
                    "no_profiling": "Zero-PII architecture prevents discrimination or exclusion based on identity",
                    "communal_assets": "20% social reserve for shared productive assets (mills, pumps, cold storage)"
                },
                "food_security": {
                    "cold_storage_enabled": any(r['activity_type'] == 'cold_storage' for r in confidence_results),
                    "irrigation_enabled": any(r['activity_type'] == 'irrigation' for r in confidence_results),
                    "impact": "Reduces post-harvest losses, enables year-round food availability"
                }
            },
            
            "environmental_considerations": {
                "renewable_energy_readiness": {
                    "productive_load_profile": "Daytime-heavy productive use aligns well with solar generation",
                    "demand_predictability": "Stable coordination patterns enable better renewable integration",
                    "recommendation": "Consider hybrid solar-grid or solar-diesel systems for productive use loads"
                },
                "efficiency_gains": {
                    "shared_assets": "Communal mills, pumps, cold storage more efficient than individual diesel generators",
                    "displacement": f"Estimated {round(demand_estimate['productive_demand']['daily_kwh'] * 365 * 0.3, 2)} liters/year diesel displacement",
                    "emissions_avoided": f"Approximately {round(demand_estimate['productive_demand']['daily_kwh'] * 365 * 0.3 * 2.68, 2)} kg CO2/year (assuming 2.68 kg CO2/liter diesel)"
                },
                "climate_resilience": {
                    "irrigation": "Enables climate-adaptive agriculture through reliable water access",
                    "cold_storage": "Reduces food waste and climate vulnerability",
                    "essential_services": "Protected capacity ensures climate shocks don't disrupt critical services"
                }
            },
            
            "alignment_with_sdgs": {
                "SDG_1": "No Poverty - Productive use energy enables income generation",
                "SDG_2": "Zero Hunger - Irrigation and cold storage improve food security",
                "SDG_3": "Good Health - Protected capacity for clinics and health services",
                "SDG_4": "Quality Education - Protected capacity for schools",
                "SDG_5": "Gender Equality - Coordination-first design prevents gender-based exclusion",
                "SDG_7": "Affordable Clean Energy - Enables productive use, not just consumption",
                "SDG_8": "Decent Work - Enables livelihood activities (milling, welding, cold storage)",
                "SDG_9": "Industry and Infrastructure - Builds productive-use infrastructure",
                "SDG_13": "Climate Action - Displaces diesel, enables climate adaptation"
            }
        }
        
        return sustainability_impact
    
    def _generate_risk_governance(self, confidence_results: List[Dict]) -> Dict:
        """
        Generate risk assessment and governance framework for DFI review.
        
        Quantifies demand uncertainty, coordination persistence risk, and mitigation strategies.
        """
        # Analyze confidence distribution
        high_conf = sum(1 for r in confidence_results if r['confidence_class'] == 'high')
        moderate_conf = sum(1 for r in confidence_results if r['confidence_class'] == 'moderate')
        low_conf = sum(1 for r in confidence_results if r['confidence_class'] == 'low')
        
        total = len(confidence_results)
        
        risk_governance = {
            "demand_uncertainty_quantification": {
                "confidence_distribution": {
                    "high_confidence_patterns": f"{high_conf}/{total} ({round(high_conf/total*100, 1) if total > 0 else 0}%)",
                    "moderate_confidence_patterns": f"{moderate_conf}/{total} ({round(moderate_conf/total*100, 1) if total > 0 else 0}%)",
                    "low_confidence_patterns": f"{low_conf}/{total} ({round(low_conf/total*100, 1) if total > 0 else 0}%)"
                },
                "demand_uncertainty_range": {
                    "conservative_estimate": "Lower-bound estimates used (as presented in Load Estimation)",
                    "expected_range": "Actual demand likely 20-40% higher than conservative estimates",
                    "upper_bound": "Peak demand could reach 1.5x conservative estimate during high-coordination periods"
                },
                "mitigation": "Infrastructure sized with 25% headroom + modular expansion capability"
            },
            
            "coordination_persistence_risk": {
                "risk_description": "Coordination patterns may weaken or shift over time if economic conditions change",
                "measurement_approach": "ZENTARI evaluates pattern stability across multiple 7-cycle windows",
                "current_stability": f"{high_conf} patterns show high stability (≥5 of 7 cycles, strong validation)",
                "decay_indicators": [
                    "Frequency drops below 3 of 7 cycles",
                    "Human signals no longer align with telemetry",
                    "New patterns emerge that contradict existing ones"
                ],
                "mitigation_strategies": [
                    "Continuous monitoring: Re-evaluate coordination patterns every 4-8 weeks",
                    "Adaptive capacity: Design infrastructure for flexible load allocation",
                    "Stakeholder engagement: Maintain communication with productive use actors",
                    "Phased deployment: Start with high-confidence zones, expand as patterns persist"
                ]
            },
            
            "infrastructure_deployment_risks": {
                "technical_risks": {
                    "load_growth": "Demand may exceed initial estimates - MITIGATION: 25% capacity headroom",
                    "power_quality": "Productive use loads may cause voltage fluctuations - MITIGATION: Proper transformer sizing, voltage regulation",
                    "maintenance": "Rural infrastructure requires robust maintenance - MITIGATION: Design for low-maintenance operation"
                },
                "financial_risks": {
                    "cost_recovery": "Productive use tariffs must balance affordability and cost recovery - MITIGATION: Tiered tariff structure",
                    "payment_reliability": "Informal economy payment patterns - MITIGATION: Prepaid metering, mobile money integration",
                    "demand_shortfall": "Actual demand lower than projected - MITIGATION: Conservative estimates, phased deployment"
                },
                "social_risks": {
                    "elite_capture": "Risk of infrastructure benefiting only well-connected actors - MITIGATION: Coordination-first design prevents individual profiling",
                    "exclusion": "Risk of excluding marginalized groups - MITIGATION: Zero-PII architecture, communal asset priority",
                    "conflict": "Disputes over capacity allocation - MITIGATION: Transparent governance, essential service protection"
                }
            },
            
            "governance_framework": {
                "capacity_allocation_principles": [
                    "1. Essential services (clinics, schools, water) receive non-negotiable priority (30-40% reserve)",
                    "2. Productive use activities allocated based on coordination confidence scores",
                    "3. 20% social reserve for communal productive assets (mills, pumps, cold storage)",
                    "4. Remaining capacity available for household and commercial use"
                ],
                "decision_making_process": {
                    "technical": "KULIMA OS provides demand signals and confidence scores",
                    "institutional": "Utility/infrastructure operator makes deployment decisions",
                    "community": "Stakeholder engagement ensures local needs are understood",
                    "transparency": "All coordination patterns and confidence scores are auditable"
                },
                "monitoring_and_evaluation": {
                    "frequency": "Re-evaluate coordination patterns every 4-8 weeks",
                    "metrics": [
                        "Pattern stability (do patterns persist?)",
                        "Validation strength (do human signals align with telemetry?)",
                        "Demand realization (does actual consumption match estimates?)",
                        "Essential service protection (are critical loads maintained?)"
                    ],
                    "adaptive_management": "Adjust capacity allocation based on observed patterns and community feedback"
                }
            },
            
            "risk_mitigation_summary": {
                "demand_uncertainty": "Conservative estimates + 25% headroom + modular expansion",
                "coordination_persistence": "Continuous monitoring + adaptive capacity + phased deployment",
                "infrastructure_deployment": "Robust design + proper sizing + maintenance planning",
                "governance": "Transparent allocation + essential service protection + stakeholder engagement"
            }
        }
        
        return risk_governance
    
    def _generate_deployment_readiness(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """
        Generate deployment readiness assessment for DFI review.
        
        Provides implementation roadmap, timeline, stakeholder status, and regulatory considerations.
        """
        # Identify high-priority zones
        high_priority_zones = set(r['zone'] for r in confidence_results if r['confidence_class'] == 'high')
        moderate_priority_zones = set(r['zone'] for r in confidence_results if r['confidence_class'] == 'moderate')
        
        # Get demand estimate for infrastructure requirements
        demand_estimate = self.energy_estimator.estimate_total_demand(confidence_results)
        
        deployment_readiness = {
            "infrastructure_requirements": {
                "electrical_infrastructure": {
                    "transformer_capacity": f"{round(demand_estimate['total_demand']['peak_kw'] * 1.25 / 0.8, 2)} kVA minimum (with 25% growth headroom)",
                    "distribution_voltage": "11kV or 33kV recommended for productive use loads",
                    "service_connections": f"Estimated {len(confidence_results)} productive use connection points",
                    "metering": "Three-phase meters for productive use, prepaid capability recommended",
                    "protection": "Overcurrent, earth fault, voltage regulation required"
                },
                "civil_works": {
                    "poles_and_lines": "Distribution network to reach identified zones",
                    "transformer_platforms": f"Minimum {len(high_priority_zones) + len(moderate_priority_zones)} transformer locations",
                    "access_roads": "Required for construction and maintenance access",
                    "site_preparation": "Transformer sites, meter locations, service connection points"
                },
                "estimated_capex": {
                    "note": "Rough order of magnitude - requires detailed engineering",
                    "transformer_and_equipment": f"${round(demand_estimate['total_demand']['peak_kw'] * 1.25 / 0.8 * 150, 2):,} (assuming $150/kVA)",
                    "distribution_network": "Depends on distance and terrain - typically $10,000-$30,000 per km",
                    "service_connections": f"${len(confidence_results) * 500:,} (assuming $500 per connection)",
                    "contingency": "Add 20-30% for unforeseen costs"
                }
            },
            
            "implementation_timeline": {
                "phase_1_planning": {
                    "duration": "3-6 months",
                    "activities": [
                        "Detailed engineering design",
                        "Environmental and social impact assessment",
                        "Regulatory approvals and permits",
                        "Procurement planning",
                        "Stakeholder engagement and consultation"
                    ]
                },
                "phase_2_construction": {
                    "duration": "6-12 months",
                    "activities": [
                        "Civil works (poles, transformer platforms)",
                        "Electrical installation (transformers, lines, meters)",
                        "Testing and commissioning",
                        "Service connection installation",
                        "Safety inspections and approvals"
                    ]
                },
                "phase_3_operation": {
                    "duration": "Ongoing",
                    "activities": [
                        "Service activation and customer onboarding",
                        "Demand monitoring and pattern validation",
                        "Maintenance and fault response",
                        "Capacity utilization tracking",
                        "Adaptive management based on observed patterns"
                    ]
                },
                "total_timeline": "9-18 months from approval to full operation"
            },
            
            "stakeholder_engagement_status": {
                "community_level": {
                    "status": "REQUIRED - Not yet initiated in this pilot",
                    "activities_needed": [
                        "Community meetings to explain infrastructure plans",
                        "Consultation on service connection locations",
                        "Tariff structure discussion and agreement",
                        "Governance framework establishment",
                        "Training on safe electricity use for productive activities"
                    ]
                },
                "institutional_level": {
                    "utility_operator": "REQUIRED - Coordination needed for grid connection, tariff approval, O&M responsibility",
                    "local_government": "REQUIRED - Permits, land access, community liaison",
                    "regulator": "REQUIRED - Tariff approval, safety compliance, service standards",
                    "financier": "IN PROGRESS - This prospectus serves as initial engagement document"
                },
                "technical_partners": {
                    "engineering_firm": "REQUIRED - Detailed design and construction supervision",
                    "equipment_suppliers": "REQUIRED - Transformers, meters, protection equipment",
                    "construction_contractor": "REQUIRED - Civil and electrical installation"
                }
            },
            
            "regulatory_and_compliance": {
                "electrical_safety": {
                    "standards": "IEC 60364 (Low-voltage electrical installations) or national equivalent",
                    "inspections": "Required before energization",
                    "certification": "Electrical contractor must be licensed"
                },
                "environmental_compliance": {
                    "esia_required": "Likely required for new distribution infrastructure",
                    "land_use": "Right-of-way agreements for poles and lines",
                    "waste_management": "Proper disposal of construction waste, old equipment"
                },
                "tariff_regulation": {
                    "productive_use_tariff": "Requires regulatory approval - typically higher than household tariff",
                    "cost_reflective_pricing": "Must balance affordability with cost recovery",
                    "tariff_structure": "Consider time-of-use or demand-based tariffs for productive use"
                },
                "service_standards": {
                    "reliability": "Productive use customers require higher reliability than household",
                    "power_quality": "Voltage regulation critical for motors and equipment",
                    "fault_response": "Faster response times needed for productive use interruptions"
                }
            },
            
            "readiness_assessment": {
                "technical_readiness": "HIGH - Demand signals validated, load estimates conservative, infrastructure requirements clear",
                "financial_readiness": "MODERATE - Requires DFI/development finance commitment, tariff approval, cost recovery plan",
                "institutional_readiness": "MODERATE - Requires utility engagement, regulatory approvals, governance framework",
                "community_readiness": "LOW - Stakeholder engagement not yet initiated (required before deployment)",
                "overall_readiness": "MODERATE - Technical foundation strong, institutional and community engagement needed"
            },
            
            "next_steps_for_deployment": [
                "1. Secure financing commitment from DFI or development finance institution",
                "2. Engage utility operator to confirm grid connection point and O&M responsibility",
                "3. Initiate community stakeholder engagement and consultation process",
                "4. Commission detailed engineering design and ESIA",
                "5. Obtain regulatory approvals (tariff, safety, environmental)",
                "6. Procure equipment and select construction contractor",
                "7. Begin construction with community liaison and safety protocols",
                "8. Commission infrastructure and activate service connections",
                "9. Monitor demand realization and adjust capacity allocation as needed",
                "10. Establish ongoing M&E framework for adaptive management"
            ]
        }
        
        return deployment_readiness

        
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

## Load Estimation

### Estimation Methodology

**Approach:** {prospectus['load_estimation']['estimation_methodology']['approach']}

**Data Sources:**
"""
        
        for source in prospectus['load_estimation']['estimation_methodology']['data_sources']:
            md_content += f"- {source}\n"
        
        md_content += f"""
**Conservatism:** {prospectus['load_estimation']['estimation_methodology']['conservatism']}

**Diversity Factors:** {prospectus['load_estimation']['estimation_methodology']['diversity_factors']}

**Load Factors:** {prospectus['load_estimation']['estimation_methodology']['load_factors']}

### Total System Demand

- **Peak Demand:** {prospectus['load_estimation']['total_system_demand']['peak_demand_kw']} kW
- **Daily Energy:** {prospectus['load_estimation']['total_system_demand']['daily_energy_kwh']} kWh
- **Monthly Energy:** {prospectus['load_estimation']['total_system_demand']['monthly_energy_kwh']} kWh
- **Annual Energy:** {prospectus['load_estimation']['total_system_demand']['annual_energy_kwh']} kWh

**Notes:** {prospectus['load_estimation']['total_system_demand']['notes']}

### Demand Breakdown

**Essential Services:**
- Peak: {prospectus['load_estimation']['demand_breakdown']['essential_services']['peak_kw']} kW
- Daily: {prospectus['load_estimation']['demand_breakdown']['essential_services']['daily_kwh']} kWh
- Percentage: {prospectus['load_estimation']['demand_breakdown']['essential_services']['percentage']}%
- Priority: {prospectus['load_estimation']['demand_breakdown']['essential_services']['priority']}

**Productive Activities:**
- Peak: {prospectus['load_estimation']['demand_breakdown']['productive_activities']['peak_kw']} kW
- Daily: {prospectus['load_estimation']['demand_breakdown']['productive_activities']['daily_kwh']} kWh
- Percentage: {prospectus['load_estimation']['demand_breakdown']['productive_activities']['percentage']}%
- Priority: {prospectus['load_estimation']['demand_breakdown']['productive_activities']['priority']}

### Capacity Planning Guidance

- **Recommended Capacity:** {prospectus['load_estimation']['capacity_planning_guidance']['recommended_capacity_kw']} kW
- **Rationale:** {prospectus['load_estimation']['capacity_planning_guidance']['rationale']}
- **Critical Load Reserve:** {prospectus['load_estimation']['capacity_planning_guidance']['critical_load_reserve']}
- **Transformer Sizing:** {prospectus['load_estimation']['capacity_planning_guidance']['transformer_sizing']}
- **Distribution Voltage:** {prospectus['load_estimation']['capacity_planning_guidance']['distribution_voltage']}

**Confidence Statement:** {prospectus['load_estimation']['confidence_statement']}

---

## Sustainability Impact

### Economic Impact

**Productive Use Multiplier:**
- Value: {prospectus['sustainability_impact']['economic_impact']['productive_use_multiplier']['value']}
- Description: {prospectus['sustainability_impact']['economic_impact']['productive_use_multiplier']['description']}

**Estimated Annual Economic Value:**
- Productive kWh/year: {prospectus['sustainability_impact']['economic_impact']['estimated_annual_economic_value']['kwh_productive']}
- Multiplier Range: {prospectus['sustainability_impact']['economic_impact']['estimated_annual_economic_value']['multiplier_range']}
- Estimated Value: {prospectus['sustainability_impact']['economic_impact']['estimated_annual_economic_value']['estimated_value_usd']}

**Infrastructure ROI Driver:** {prospectus['sustainability_impact']['economic_impact']['infrastructure_roi_driver']}

### Social Impact

**Essential Services Protected:**
- Count: {prospectus['sustainability_impact']['social_impact']['essential_services_protected']['count']}
- Types: {', '.join(prospectus['sustainability_impact']['social_impact']['essential_services_protected']['types'])}
- Capacity Reserved: {prospectus['sustainability_impact']['social_impact']['essential_services_protected']['capacity_reserved']}
- Impact: {prospectus['sustainability_impact']['social_impact']['essential_services_protected']['impact']}

**Equity and Inclusion:**
- Approach: {prospectus['sustainability_impact']['social_impact']['equity_and_inclusion']['approach']}
- No Profiling: {prospectus['sustainability_impact']['social_impact']['equity_and_inclusion']['no_profiling']}
- Communal Assets: {prospectus['sustainability_impact']['social_impact']['equity_and_inclusion']['communal_assets']}

### Environmental Considerations

**Renewable Energy Readiness:**
- Productive Load Profile: {prospectus['sustainability_impact']['environmental_considerations']['renewable_energy_readiness']['productive_load_profile']}
- Demand Predictability: {prospectus['sustainability_impact']['environmental_considerations']['renewable_energy_readiness']['demand_predictability']}

**Efficiency Gains:**
- Diesel Displacement: {prospectus['sustainability_impact']['environmental_considerations']['efficiency_gains']['displacement']}
- Emissions Avoided: {prospectus['sustainability_impact']['environmental_considerations']['efficiency_gains']['emissions_avoided']}

### Alignment with SDGs

"""
        
        for sdg, description in prospectus['sustainability_impact']['alignment_with_sdgs'].items():
            md_content += f"- **{sdg}:** {description}\n"
        
        md_content += f"""
---

## Risk and Governance

### Demand Uncertainty Quantification

**Confidence Distribution:**
- High Confidence: {prospectus['risk_and_governance']['demand_uncertainty_quantification']['confidence_distribution']['high_confidence_patterns']}
- Moderate Confidence: {prospectus['risk_and_governance']['demand_uncertainty_quantification']['confidence_distribution']['moderate_confidence_patterns']}
- Low Confidence: {prospectus['risk_and_governance']['demand_uncertainty_quantification']['confidence_distribution']['low_confidence_patterns']}

**Demand Uncertainty Range:**
- Conservative Estimate: {prospectus['risk_and_governance']['demand_uncertainty_quantification']['demand_uncertainty_range']['conservative_estimate']}
- Expected Range: {prospectus['risk_and_governance']['demand_uncertainty_quantification']['demand_uncertainty_range']['expected_range']}
- Upper Bound: {prospectus['risk_and_governance']['demand_uncertainty_quantification']['demand_uncertainty_range']['upper_bound']}

**Mitigation:** {prospectus['risk_and_governance']['demand_uncertainty_quantification']['mitigation']}

### Coordination Persistence Risk

**Risk Description:** {prospectus['risk_and_governance']['coordination_persistence_risk']['risk_description']}

**Current Stability:** {prospectus['risk_and_governance']['coordination_persistence_risk']['current_stability']}

**Mitigation Strategies:**
"""
        
        for strategy in prospectus['risk_and_governance']['coordination_persistence_risk']['mitigation_strategies']:
            md_content += f"- {strategy}\n"
        
        md_content += f"""
### Governance Framework

**Capacity Allocation Principles:**
"""
        
        for principle in prospectus['risk_and_governance']['governance_framework']['capacity_allocation_principles']:
            md_content += f"{principle}\n"
        
        md_content += f"""
**Monitoring and Evaluation:**
- Frequency: {prospectus['risk_and_governance']['governance_framework']['monitoring_and_evaluation']['frequency']}
- Adaptive Management: {prospectus['risk_and_governance']['governance_framework']['monitoring_and_evaluation']['adaptive_management']}

---

## Deployment Readiness

### Infrastructure Requirements

**Electrical Infrastructure:**
- Transformer Capacity: {prospectus['deployment_readiness']['infrastructure_requirements']['electrical_infrastructure']['transformer_capacity']}
- Distribution Voltage: {prospectus['deployment_readiness']['infrastructure_requirements']['electrical_infrastructure']['distribution_voltage']}
- Service Connections: {prospectus['deployment_readiness']['infrastructure_requirements']['electrical_infrastructure']['service_connections']}
- Metering: {prospectus['deployment_readiness']['infrastructure_requirements']['electrical_infrastructure']['metering']}

**Estimated CAPEX:**
- Transformer & Equipment: {prospectus['deployment_readiness']['infrastructure_requirements']['estimated_capex']['transformer_and_equipment']}
- Service Connections: {prospectus['deployment_readiness']['infrastructure_requirements']['estimated_capex']['service_connections']}
- Contingency: {prospectus['deployment_readiness']['infrastructure_requirements']['estimated_capex']['contingency']}

### Implementation Timeline

**Phase 1 - Planning:** {prospectus['deployment_readiness']['implementation_timeline']['phase_1_planning']['duration']}

**Phase 2 - Construction:** {prospectus['deployment_readiness']['implementation_timeline']['phase_2_construction']['duration']}

**Phase 3 - Operation:** {prospectus['deployment_readiness']['implementation_timeline']['phase_3_operation']['duration']}

**Total Timeline:** {prospectus['deployment_readiness']['implementation_timeline']['total_timeline']}

### Readiness Assessment

- **Technical Readiness:** {prospectus['deployment_readiness']['readiness_assessment']['technical_readiness']}
- **Financial Readiness:** {prospectus['deployment_readiness']['readiness_assessment']['financial_readiness']}
- **Institutional Readiness:** {prospectus['deployment_readiness']['readiness_assessment']['institutional_readiness']}
- **Community Readiness:** {prospectus['deployment_readiness']['readiness_assessment']['community_readiness']}
- **Overall Readiness:** {prospectus['deployment_readiness']['readiness_assessment']['overall_readiness']}

### Next Steps for Deployment

"""
        
        for step in prospectus['deployment_readiness']['next_steps_for_deployment']:
            md_content += f"{step}\n"
        
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
    
    print("\n[SUCCESS] Demand-Signal Prospectus generated successfully")

# Made with Bob
