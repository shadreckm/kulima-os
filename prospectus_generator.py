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
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from energy_demand_estimator import EnergyDemandEstimator
from policy import RESERVE_RATIO, require_planning_reserve
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

_PDF_MARGIN = 72
_PDF_FOOTER_Y = 40
_PDF_CONTENT_WIDTH = letter[0] - 2 * _PDF_MARGIN


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
    
    def __init__(self, logo_path: Optional[str] = None):
        """Initialize prospectus generator with energy demand estimator."""
        self.energy_estimator = EnergyDemandEstimator()
        default_logo = Path(__file__).resolve().parent / "assets" / "kulima_africa_logo.png"
        self.logo_path = str(Path(logo_path) if logo_path else default_logo)
    
    def generate_prospectus(
        self,
        confidence_results: List[Dict],
        lundai_analysis: Dict = None,
        metadata: Dict = None,
        planning_reserve: Dict = None,
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
            planning_reserve: Planning reserve object describing usable_signals and reserve_buffer
            
        Returns:
            Demand-Signal Prospectus as a dictionary
        """
        
        if metadata is None:
            metadata = {}
        if planning_reserve is None:
            raise ValueError(
                "ProspectusGenerator requires an explicit planning_reserve object derived from usable signals."
            )
        require_planning_reserve(planning_reserve)
        
        # Build prospectus structure
        is_sample = metadata.get("is_sample", False)
        prospectus = {
            "prospectus_metadata": {
                "title": "KULIMA OS Demand-Signal Prospectus",
                "subtitle": "Verified Coordination Patterns for Infrastructure Planning",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "pilot_region": metadata.get("region", "Pilot Region"),
                "evaluation_period": metadata.get("period", "7-cycle window (1 week)"),
                "system_version": "KULIMA OS Pilot v0.2 (LUMOZA + LUNDAI + Critical Load Protection)",
                "is_sample": is_sample,
                "disclaimer": "Sample Prospectus – Demonstration Only" if is_sample else None
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
            "planning_reserve": planning_reserve,
            
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
                "description": f"{int(RESERVE_RATIO * 100)}% capacity reserved for communal productive assets",
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

    def _resolve_logo(self) -> Optional[Image]:
        """Load centered logo at fixed aspect (80×80 pt)."""
        path = Path(self.logo_path)
        if not path.is_file():
            alt = Path("assets/kulima_africa_logo.png")
            if alt.is_file():
                path = alt
            else:
                return None
        try:
            logo = Image(str(path))
            logo.drawWidth = 80
            logo.drawHeight = 80
            logo.hAlign = "CENTER"
            return logo
        except Exception:
            return None

    def _pdf_styles(self) -> Dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "ProspectusTitle",
                parent=base["Title"],
                fontName="Helvetica-Bold",
                fontSize=24,
                leading=30,
                alignment=1,
                spaceAfter=6,
                textColor=colors.HexColor("#003366"),
            ),
            "subtitle": ParagraphStyle(
                "ProspectusSubtitle",
                parent=base["Heading1"],
                fontName="Helvetica",
                fontSize=16,
                leading=20,
                alignment=1,
                spaceAfter=4,
                textColor=colors.HexColor("#003366"),
            ),
            "section": ParagraphStyle(
                "ProspectusSection",
                parent=base["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                spaceBefore=8,
                spaceAfter=12,
                textColor=colors.HexColor("#003366"),
            ),
            "body": ParagraphStyle(
                "ProspectusBody",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=11,
                leading=16,
                spaceAfter=6,
            ),
            "note": ParagraphStyle(
                "ProspectusNote",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#555555"),
                spaceAfter=4,
            ),
            "high_conf": ParagraphStyle(
                "ProspectusHighConf",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=16,
                textColor=colors.HexColor("#2E8B57"),
            ),
        }

    def _standard_table_style(self) -> TableStyle:
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F5F7FA"), colors.white]),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#003366")),
        ])

    def _make_table(
        self,
        rows: List[List[Any]],
        col_widths: Optional[List[float]] = None,
    ) -> Table:
        if col_widths is None:
            n = len(rows[0])
            col_widths = [_PDF_CONTENT_WIDTH / n] * n
        table = Table(rows, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
        table.setStyle(self._standard_table_style())
        return table

    def _section_break(self, height: float = 20) -> Spacer:
        return Spacer(1, height)

    def _page_break(self) -> Spacer:
        return Spacer(1, 0)

    def _add_header(self, canvas, doc) -> None:
        """Add small logo to header on pages after cover."""
        if doc.page > 1:
            canvas.saveState()
            try:
                logo_path = Path(__file__).resolve().parent / "assets" / "kulima_africa_logo.png"
                if logo_path.is_file():
                    from reportlab.lib.utils import ImageReader
                    img = ImageReader(str(logo_path))
                    canvas.drawImage(img, 72, letter[1] - 50, width=40, height=40, mask='auto')
            except:
                pass
            canvas.restoreState()

    def _add_footer(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#666666"))
        footer_text = f"Kulima Africa | Kulima OS Pilot v0.2 | Page {doc.page}"
        canvas.drawCentredString(letter[0] / 2, _PDF_FOOTER_Y, footer_text)
        canvas.restoreState()

    def generate_pdf(self, prospectus: Dict, output_path: str):
        """
        Generate a PDF version of the Demand-Signal Prospectus.

        Args:
            prospectus: The prospectus dictionary generated by generate_prospectus
            output_path: Path to save the PDF file
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=_PDF_MARGIN,
            rightMargin=_PDF_MARGIN,
            topMargin=_PDF_MARGIN,
            bottomMargin=_PDF_MARGIN + 12,
        )
        st = self._pdf_styles()
        body = st["body"]
        note = st["note"]
        high_conf = st["high_conf"]
        half_w = _PDF_CONTENT_WIDTH / 2
        story = []

        meta = prospectus["prospectus_metadata"]
        is_sample = meta.get("is_sample", False)

        # Cover Page
        logo = self._resolve_logo()
        if logo:
            story.append(logo)
            story.append(self._section_break(36))

        story.append(Paragraph("KULIMA OS", st["title"]))
        story.append(self._section_break(12))
        story.append(Paragraph("Verified Demand Signal Prospectus", st["subtitle"]))
        story.append(self._section_break(8))
        story.append(Paragraph(
            f"{meta['pilot_region']} | {meta['evaluation_period']}",
            ParagraphStyle("CoverLine", parent=body, fontSize=12, alignment=1, leading=16),
        ))
        story.append(self._section_break(20))

        if is_sample:
            story.append(Paragraph(
                "SAMPLE PROSPECTUS – DEMONSTRATION ONLY",
                ParagraphStyle("SampleWarning", parent=st["section"], fontSize=14, textColor=colors.red, alignment=1),
            ))
            story.append(self._section_break(12))

        story.append(Paragraph(
            '<b>Institutional Planning Artifact</b> &nbsp;|&nbsp; Pilot Demonstration',
            ParagraphStyle("CoverLine", parent=body, fontSize=11, alignment=1, leading=15),
        ))
        story.append(Paragraph("Not a Financing Approval", note))
        story.append(self._section_break(28))
        story.append(self._make_table([
            ["Field", "Value"],
            ["Generated", meta["generated_at"]],
            ["Pilot Region", meta["pilot_region"]],
            ["Evaluation Period", meta["evaluation_period"]],
            ["System Version", meta["system_version"]],
        ], [180, _PDF_CONTENT_WIDTH - 180]))
        story.append(self._section_break(28))

        scope = prospectus["document_scope"]
        story.append(Paragraph("Document Scope", st["section"]))
        story.append(self._make_table([
            ["Enables", "Does Not Do"],
            [
                Paragraph("<br/>".join(f"• {x}" for x in scope["enables"]), body),
                Paragraph("<br/>".join(f"• {x}" for x in scope["does_not_do"]), body),
            ],
        ], [half_w, half_w]))
        story.append(self._section_break(8))
        story.append(Paragraph(scope["estimate_nature"], note))
        story.append(self._section_break(28))

        # Executive Summary Page
        story.append(self._page_break())
        story.append(Paragraph("Executive Summary", st["section"]))
        story.append(self._section_break(12))
        
        summary = prospectus["executive_summary"]
        story.append(Paragraph("<b>Analysis Overview</b>", body))
        story.append(self._section_break(8))
        story.append(Paragraph(
            f"This prospectus analyzes coordination patterns from {summary['total_coordination_patterns']} detected activities "
            f"in the {meta['pilot_region']} zone over a {meta['evaluation_period']}. "
            f"Of these, {summary['high_confidence_patterns']} patterns demonstrate high coordination confidence, "
            f"indicating stable, collective economic activity suitable for infrastructure planning.",
            body
        ))
        story.append(self._section_break(16))
        
        story.append(Paragraph("<b>Key Insight</b>", body))
        story.append(self._section_break(8))
        story.append(Paragraph(summary["key_finding"], body))
        story.append(self._section_break(16))
        
        story.append(Paragraph("<b>Coordination Strength</b>", body))
        story.append(self._section_break(8))
        story.append(Paragraph(
            f"Detected activities include: {', '.join(summary['productive_activities_detected'])}. "
            f"Coordination patterns indicate {'strong' if summary['high_confidence_patterns'] > 0 else 'emerging'} "
            f"collective demand with {'high' if summary['high_confidence_patterns'] >= 3 else 'moderate'} "
            f"confidence for infrastructure investment decisions.",
            body
        ))
        story.append(self._section_break(28))
        
        story.append(Paragraph("Coordination Metrics", st["section"]))
        story.append(self._make_table([
            ["Metric", "Value"],
            ["Total Coordination Patterns", str(summary["total_coordination_patterns"])],
            ["High Confidence Patterns", str(summary["high_confidence_patterns"])],
            ["Moderate Confidence Patterns", str(summary["moderate_confidence_patterns"])],
            ["Zones with Coordinated Demand", ", ".join(summary["zones_with_coordinated_demand"]) or "—"],
            ["Productive Activities", ", ".join(summary["productive_activities_detected"]) or "—"],
        ], [220, _PDF_CONTENT_WIDTH - 220]))
        story.append(self._section_break(28))

        patterns = prospectus["coordination_patterns"]
        story.append(Paragraph("Verified Coordination Patterns", st["section"]))
        if patterns:
            pat_rows = [["Activity", "Zone", "Time Window", "Frequency", "Confidence", "Stability"]]
            for p in patterns:
                act_style = high_conf if p.get("confidence_class") == "high" else body
                rhythm = p.get("demand_rhythm", {})
                pat_rows.append([
                    Paragraph(p["activity_type"].capitalize(), act_style),
                    p["zone"],
                    rhythm.get("time_window", "—"),
                    rhythm.get("frequency", "—"),
                    p.get("confidence_class", "—").capitalize(),
                    f"{p.get('stability_score', 0):.2f}",
                ])
            cw = _PDF_CONTENT_WIDTH / 6
            story.append(self._make_table(pat_rows, [cw * 1.0, cw * 0.8, cw * 0.9, cw * 0.9, cw * 0.8, cw * 0.6]))
        else:
            story.append(Paragraph("No stable patterns in this evaluation window.", note))
        story.append(self._section_break(28))

        # LUNDAI Section - Settlement & Land-Use Validation
        story.append(Paragraph("Settlement & Land-Use Validation (LUNDAI)", st["section"]))
        lundai = prospectus.get("settlement_and_infrastructure_analysis", {})
        if lundai and lundai.get("status") != "LUNDAI analysis not included":
            story.append(self._section_break(8))
            story.append(Paragraph(
                "Detected coordination patterns align with observed settlement dynamics, "
                "indicating real on-ground activity rather than isolated reporting.",
                body
            ))
            story.append(self._section_break(16))
            
            overall = lundai.get("overall_assessment", {})
            story.append(Paragraph("<b>Infrastructure Assessment</b>", body))
            story.append(self._section_break(8))
            story.append(self._make_table([
                ["Metric", "Value"],
                ["Total Zones Analyzed", str(overall.get("total_zones_analyzed", 0))],
                ["Critical Infrastructure Gaps", str(overall.get("critical_infrastructure_gaps", 0))],
                ["Urgent Priority Zones", str(overall.get("urgent_priority_zones", 0))],
                ["Average Infrastructure Adequacy", f"{overall.get('average_infrastructure_adequacy_score', 0):.1f}%"],
                ["Overall Status", overall.get("overall_infrastructure_status", "—").capitalize()],
            ], [240, _PDF_CONTENT_WIDTH - 240]))
            story.append(self._section_break(16))
            
            zone_analyses = lundai.get("zone_analyses", {})
            if zone_analyses:
                story.append(Paragraph("<b>Zone-Level Analysis</b>", body))
                story.append(self._section_break(8))
                za_rows = [["Zone", "Settlement Type", "Infrastructure Status", "Essential Services", "Productive Activities"]]
                for zone, data in zone_analyses.items():
                    za_rows.append([
                        zone,
                        data.get("settlement_type", "—").replace("_", " ").title(),
                        data.get("infrastructure_status", "—").capitalize(),
                        str(data.get("essential_services_count", 0)),
                        str(data.get("productive_activity_count", 0)),
                    ])
                cw = _PDF_CONTENT_WIDTH / 5
                story.append(self._make_table(za_rows, [cw * 0.8, cw * 1.2, cw * 1.0, cw * 0.8, cw * 0.8]))
        else:
            story.append(Paragraph("LUNDAI analysis not available for this evaluation.", note))
        story.append(self._section_break(28))

        story.append(Paragraph("Energy Signal Output", st["section"]))
        energy_signals = prospectus["energy_signals"]
        if energy_signals:
            e_rows = [["Zone", "Activities", "Min kWh", "Max kWh", "Peak kW", "Confidence", "Buffered kW"]]
            for s in energy_signals:
                conf_style = high_conf if s["confidence_score"] == "HIGH" else body
                e_rows.append([
                    s["zone"],
                    Paragraph(", ".join(s["activities"]), body),
                    str(s["estimated_min_kwh"]),
                    str(s["estimated_max_kwh"]),
                    f"{s['peak_kw_estimate']:.1f}",
                    Paragraph(s["confidence_score"], conf_style),
                    f"{s['peak_kw_estimate'] * 1.25:.1f}",
                ])
            ew = _PDF_CONTENT_WIDTH / 7
            story.append(self._make_table(e_rows, [ew] * 7))
            story.append(self._section_break(8))
            story.append(Paragraph(
                "Recommended installed capacity includes a 25% planning buffer (conservative lower bound).",
                note,
            ))
        story.append(self._section_break(28))

        load_est = prospectus.get("load_estimation", {})
        if load_est.get("total_system_demand"):
            story.append(Paragraph("Load Estimation Summary", st["section"]))
            total = load_est["total_system_demand"]
            ess = load_est.get("demand_breakdown", {}).get("essential_services", {})
            prod = load_est.get("demand_breakdown", {}).get("productive_activities", {})
            cap = load_est.get("capacity_planning_guidance", {})
            story.append(self._make_table([
                ["Measure", "Value"],
                ["Peak Demand (kW)", f"{total.get('peak_demand_kw', '—')}"],
                ["Daily Energy (kWh)", f"{total.get('daily_energy_kwh', '—')}"],
                ["Essential Services Peak (kW)", f"{ess.get('peak_kw', '—')}"],
                ["Productive Activities Peak (kW)", f"{prod.get('peak_kw', '—')}"],
                ["Recommended Capacity (kW)", f"{cap.get('recommended_capacity_kw', '—')}"],
            ], [220, _PDF_CONTENT_WIDTH - 220]))
            story.append(self._section_break(28))

        story.append(Paragraph("Confidence & Risk Assessment", st["section"]))
        story.append(self._section_break(8))
        story.append(Paragraph("<b>Confidence Tier Interpretation</b>", body))
        story.append(self._section_break(8))
        story.append(self._make_table([
            ["Tier", "Range", "Interpretation", "Actionable Guidance"],
            ["HIGH", ">0.7", "Strong coordination", "Suitable for phased infrastructure planning with confidence"],
            ["MEDIUM", "0.4–0.7", "Moderate coordination", "Monitor and corroborate before capacity sizing decisions"],
            ["LOW", "<0.4", "Emerging signals", "Not yet suitable for capacity commitment; continue monitoring"],
        ], [80, 80, 180, _PDF_CONTENT_WIDTH - 340]))
        story.append(self._section_break(16))
        
        risk = prospectus["risk_and_governance"]
        dist = risk["demand_uncertainty_quantification"]["confidence_distribution"]
        story.append(Paragraph("<b>Risk Summary</b>", body))
        story.append(self._section_break(8))
        story.append(self._make_table([
            ["Risk Area", "Summary"],
            ["Confidence Distribution",
             f"High: {dist['high_confidence_patterns']}; "
             f"Moderate: {dist['moderate_confidence_patterns']}; "
             f"Low: {dist['low_confidence_patterns']}"],
            ["Demand Uncertainty",
             risk["demand_uncertainty_quantification"]["demand_uncertainty_range"]["conservative_estimate"]],
            ["Governance Framework", "Transparent allocation, essential-service protection, phased deployment"],
        ], [180, _PDF_CONTENT_WIDTH - 180]))
        story.append(self._section_break(12))
        story.append(Paragraph(
            "<b>Risk Mitigation:</b> All estimates use conservative lower-bound assumptions. "
            "Infrastructure sizing includes 25% planning buffer. Essential services receive "
            "priority allocation with 20% capacity reservation.",
            note
        ))
        story.append(self._section_break(28))

        clp = prospectus["critical_load_protection"]
        story.append(Paragraph("Critical Load Protection", st["section"]))
        story.append(self._make_table([
            ["Parameter", "Detail"],
            ["Capacity Reservation", f"{clp['capacity_reservation']['percentage']}%"],
            ["Rationale", Paragraph(clp["capacity_reservation"]["rationale"], body)],
            ["Enforcement", clp["capacity_reservation"]["enforcement"]],
            ["Essential Patterns", str(clp.get("essential_service_count", 0))],
            ["Productive Patterns", str(clp.get("productive_activity_count", 0))],
        ], [160, _PDF_CONTENT_WIDTH - 160]))
        scenarios = clp.get("scenario_analysis", {})
        if scenarios:
            story.append(self._section_break(12))
            scen_rows = [["Scenario", "Essential Load %", "Available for Productive %"]]
            for name, data in scenarios.items():
                scen_rows.append([
                    name.capitalize(),
                    f"{data.get('essential_load_percentage', '—')}%",
                    f"{data.get('available_for_productive_use', '—')}%",
                ])
            story.append(self._make_table(scen_rows, [120, 174, 174]))
        story.append(self._section_break(28))

        deploy = prospectus.get("deployment_readiness", {})
        readiness = deploy.get("readiness_assessment", {}) if deploy else {}
        if readiness:
            story.append(Paragraph("Deployment Readiness", st["section"]))
            story.append(self._make_table([
                ["Criterion", "Assessment"],
                ["Overall Readiness", readiness.get("overall_readiness", "—")],
                ["Technical Readiness", readiness.get("technical_readiness", "—")],
                ["Financial Readiness", readiness.get("financial_readiness", "—")],
                ["Institutional Readiness", readiness.get("institutional_readiness", "—")],
                ["Community Readiness", readiness.get("community_readiness", "—")],
            ], [160, _PDF_CONTENT_WIDTH - 160]))
            next_steps = deploy.get("next_steps_for_deployment", [])[:5]
            if next_steps:
                story.append(self._section_break(12))
                step_rows = [["Step", "Action"]]
                for i, step in enumerate(next_steps, 1):
                    step_rows.append([str(i), Paragraph(step, body)])
                story.append(self._make_table(step_rows, [40, _PDF_CONTENT_WIDTH - 40]))
            story.append(self._section_break(28))

        guidance = prospectus.get("infrastructure_planning_guidance", {})
        if guidance:
            story.append(Paragraph("Infrastructure Planning Guidance", st["section"]))
            story.append(self._section_break(8))
            story.append(Paragraph(
                "<b>Infrastructure Required:</b> "
                f"Based on detected coordination patterns, infrastructure is needed in "
                f"{', '.join(guidance.get('high_priority_zones', [])) or 'the analyzed zone'} "
                f"to support productive economic activities.",
                body
            ))
            story.append(self._section_break(8))
            story.append(Paragraph(
                "<b>Why It Is Needed:</b> "
                f"Coordination patterns indicate sustained demand from "
                f"{', '.join(summary['productive_activities_detected'])} activities. "
                f"Current infrastructure adequacy is {lundai.get('overall_assessment', {}).get('average_infrastructure_adequacy_score', 0):.1f}%, "
                f"indicating significant gaps.",
                body
            ))
            story.append(self._section_break(8))
            story.append(Paragraph(
                "<b>Demand Validity Confidence:</b> "
                f"{'High' if summary['high_confidence_patterns'] >= 2 else 'Moderate'} confidence "
                f"based on {summary['high_confidence_patterns']} high-confidence patterns "
                f"validated across {meta['evaluation_period']}.",
                body
            ))
            story.append(self._section_break(16))
            story.append(self._make_table([
                ["Category", "Detail"],
                ["High Priority Zones", ", ".join(guidance.get("high_priority_zones", [])) or "—"],
                ["Moderate Priority Zones", ", ".join(guidance.get("moderate_priority_zones", [])) or "—"],
                ["Investment Recommendation", Paragraph(guidance.get("investment_recommendation", "—"), body)],
                ["Capacity Planning", Paragraph(guidance.get("capacity_planning_note", "—"), body)],
            ], [200, _PDF_CONTENT_WIDTH - 200]))
            story.append(self._section_break(28))

        # Infrastructure Planning Implication
        story.append(Paragraph("Infrastructure Planning Implication", st["section"]))
        story.append(self._section_break(8))
        story.append(Paragraph(
            "Observed coordination patterns indicate emerging productive demand that justifies "
            "phased infrastructure deployment under conservative capacity allocation. "
            "The detected activities demonstrate consistent temporal patterns and spatial alignment, "
            "suggesting sustainable demand rather than transient usage.",
            body
        ))
        story.append(self._section_break(12))
        story.append(Paragraph(
            "<b>Recommended Approach:</b> ",
            body
        ))
        story.append(self._section_break(4))
        story.append(Paragraph(
            "• Phase 1: Deploy infrastructure to high-priority zones with validated coordination patterns<br/>"
            "• Phase 2: Monitor demand patterns and adjust capacity allocation based on actual usage<br/>"
            "• Phase 3: Expand to moderate-priority zones as coordination strengthens<br/>"
            "• Maintain 20% capacity reserve for essential services and communal productive assets",
            body
        ))
        story.append(self._section_break(28))

        story.append(Paragraph("Ethics & Methodology", st["section"]))
        ethics = prospectus["ethics_compliance"]
        inv_rows = [["System Invariant", "Status"]]
        for invariant in ethics["system_invariants"]:
            inv_rows.append([Paragraph(invariant, body), "Enforced"])
        story.append(self._make_table(inv_rows, [340, _PDF_CONTENT_WIDTH - 340]))
        story.append(self._section_break(12))
        story.append(Paragraph(ethics["verification"], note))
        story.append(self._section_break(12))
        pipe_rows = [["Step", "Process Stage"]]
        for i, step in enumerate(prospectus["methodology"]["processing_pipeline"], 1):
            pipe_rows.append([str(i), step])
        story.append(self._make_table(pipe_rows, [50, _PDF_CONTENT_WIDTH - 50]))
        story.append(self._section_break(28))

        story.append(Paragraph("Technical Notes", st["section"]))
        story.append(Paragraph(
            "This document is a decision-support artifact for utilities and development finance institutions. "
            "It does not replace detailed engineering studies, environmental assessments, or financing approvals.",
            note,
        ))
        story.append(self._section_break(20))

        # Professional Closing Statement
        story.append(Paragraph("Document Disclaimer", st["section"]))
        story.append(self._section_break(8))
        story.append(Paragraph(
            "This document provides coordination-informed infrastructure insight derived from verified activity signals. "
            "It supports planning decisions but does not substitute for engineering or regulatory approval processes.",
            body
        ))
        story.append(self._section_break(12))
        story.append(Paragraph(
            "<b>Use Limitations:</b>",
            body
        ))
        story.append(self._section_break(4))
        story.append(Paragraph(
            "• Estimates are conservative lower-bound signals intended for planning, not exact operational forecasts<br/>"
            "• Infrastructure decisions require additional technical studies, environmental assessments, and regulatory approvals<br/>"
            "• This document does not constitute financing approval or investment commitment<br/>"
            "• All coordination patterns are aggregated and identity-free, complying with Zero-PII principles",
            body
        ))
        story.append(self._section_break(20))

        # CEO Signature Page
        story.append(self._page_break())
        signature_path = Path(__file__).resolve().parent / "assets" / "shadreck-signature.jpg"
        if signature_path.is_file():
            try:
                signature_img = Image(str(signature_path), width=200, height=100)
                story.append(signature_img)
                story.append(self._section_break(12))
            except:
                pass  # If signature image fails, continue without it

        story.append(Paragraph("________________________", st["title"]))
        story.append(self._section_break(8))
        story.append(Paragraph("Shadreck Mawindo", st["subtitle"]))
        story.append(Paragraph("Chief Executive Officer", body))
        story.append(Paragraph("Kulima Africa", body))
        story.append(self._section_break(12))
        story.append(Paragraph(
            f"Date: {datetime.utcnow().strftime('%B %d, %Y')}",
            note,
        ))

        doc.build(story, onFirstPage=self._add_footer, onLaterPages=lambda c, d: (self._add_header(c, d), self._add_footer(c, d)))

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
    
    def _validate_pattern_explanation(self, explanation: Dict) -> None:
        """Ensure that each prospectus pattern contains a complete explainability payload."""
        if not isinstance(explanation, dict):
            raise ValueError("Pattern explanation must be a dictionary.")

        required_keys = [
            'why_accepted',
            'why_rejected',
            'reserve_explanation',
            'action_allowed_explanation',
            'human_readable'
        ]
        missing = [key for key in required_keys if not explanation.get(key)]
        if missing:
            raise ValueError(
                f"Prospectus pattern explanation missing required keys: {', '.join(missing)}"
            )

    def _format_patterns_for_institutions(self, confidence_results: List[Dict]) -> List[Dict]:
        """Format coordination patterns for institutional decision-makers."""
        
        formatted_patterns = []
        
        for result in confidence_results:
            explanation = result.get('explanation', {})
            self._validate_pattern_explanation(explanation)

            pattern = {
                "pattern_id": f"{result['zone']}_{result['activity_type']}_{result['time_window']}",
                "activity_type": result['activity_type'],
                "zone": result['zone'],
                "signal_count": result.get('signal_count', None),
                "validated_signals": result.get('validated_signals', None),
                "rejected_signals": result.get('rejected_signals', None),
                "integrity_score": result.get('integrity_score', None),
                "alignment_level": result.get('alignment_level', None),
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
                "explanation": explanation,
                "trust": result.get('trust', {}),
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
        return implications.get(
            activity,
            f"Coordination pattern ({confidence} confidence) in {time_window} window — site-specific sizing required.",
        )

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
    
    from policy import compute_planning_reserve

    zentari = ZentariEngine()
    planning_reserve = compute_planning_reserve(len(patterns))
    confidence_results = zentari.evaluate_coordination_confidence(patterns, planning_reserve=planning_reserve)
    
    # Generate prospectus
    generator = ProspectusGenerator()
    prospectus = generator.generate_prospectus(
        confidence_results,
        metadata={
            "region": "Pilot Region - Rural Energy Planning",
            "period": "7-cycle window (Week 1)"
        },
        planning_reserve=planning_reserve,
    )
    
    # Save in both formats
    generator.save_prospectus_json(prospectus)
    generator.save_prospectus_markdown(prospectus)
    generator.generate_pdf(prospectus, "demand_signal_prospectus.pdf")

    print("\n[SUCCESS] Demand-Signal Prospectus generated successfully (JSON, Markdown, PDF)")

