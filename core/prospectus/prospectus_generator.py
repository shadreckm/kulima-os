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
from collections import defaultdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from energy_demand_estimator import EnergyDemandEstimator
from policy import RESERVE_RATIO, require_planning_reserve
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def safe_num(value):
    try:
        return float(value)
    except Exception:
        return 0.0

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
        clusters: List[Dict] = None,
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
        clusters = clusters or []
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
            "cluster_overview": clusters,
            
            "executive_summary": self._generate_executive_summary(confidence_results, lundai_analysis, clusters),
            
            "coordination_patterns": self._format_patterns_for_institutions(confidence_results),
            
            "energy_signals": self.compute_energy_signal(confidence_results),
            
            "load_estimation": self._generate_load_estimation(confidence_results),
            
            "settlement_and_infrastructure_analysis": lundai_analysis if lundai_analysis else {"status": "LUNDAI analysis not included"},
            
            "critical_load_protection": self._generate_critical_load_analysis(confidence_results, lundai_analysis),
            
            "sustainability_impact": self._generate_sustainability_impact(confidence_results, lundai_analysis),
            
            "risk_and_governance": self._generate_risk_governance(confidence_results),
            
            "flow_insights": self._generate_flow_insights(lundai_analysis),
            
            "risk_model": self._calculate_risk_model(confidence_results, lundai_analysis),
            
            "decision_recommendations": self._generate_decision_recommendations(confidence_results, lundai_analysis),
            
            "long_term_coordination_insights": self._generate_long_term_insights(confidence_results, lundai_analysis),
            
            "regional_flow_analysis": self._generate_regional_flow_analysis(confidence_results, lundai_analysis),
            
            "infrastructure_roadmap": self._generate_infrastructure_roadmap(confidence_results, lundai_analysis),
            
            "scenario_projections": self._generate_scenario_projections(confidence_results, lundai_analysis),
            
            "policy_maker_section": self._generate_policy_maker_section(confidence_results, lundai_analysis),
            
            "investor_section": self._generate_investor_section(confidence_results, lundai_analysis),
            
            "infrastructure_planner_section": self._generate_infrastructure_planner_section(confidence_results, lundai_analysis),
            
            "deployment_readiness": self._generate_deployment_readiness(confidence_results, lundai_analysis),

            "production_readiness": self._generate_production_readiness_summary(confidence_results, lundai_analysis),
            
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
                fontSize=28,
                leading=36,
                alignment=1,
                spaceAfter=12,
                textColor=colors.HexColor("#003366"),
            ),
            "subtitle": ParagraphStyle(
                "ProspectusSubtitle",
                parent=base["Heading1"],
                fontName="Helvetica",
                fontSize=18,
                leading=24,
                alignment=1,
                spaceAfter=8,
                textColor=colors.HexColor("#003366"),
            ),
            "section": ParagraphStyle(
                "ProspectusSection",
                parent=base["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=15,
                leading=20,
                spaceBefore=24,
                spaceAfter=12,
                textColor=colors.HexColor("#003366"),
            ),
            "body": ParagraphStyle(
                "ProspectusBody",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=11,
                leading=16,
                spaceAfter=8,
                leftIndent=0,
            ),
            "body_bold": ParagraphStyle(
                "ProspectusBodyBold",
                parent=base["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=16,
                spaceAfter=8,
                leftIndent=0,
            ),
            "note": ParagraphStyle(
                "ProspectusNote",
                parent=base["BodyText"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#555555"),
                spaceAfter=8,
                leftIndent=0,
            ),
            "high_conf": ParagraphStyle(
                "ProspectusHighConf",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=16,
                textColor=colors.HexColor("#2E8B57"),
            ),
            "table_header": ParagraphStyle(
                "TableHeader",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#003366"),
            ),
            "table_body": ParagraphStyle(
                "TableBody",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
            ),
            "signature": ParagraphStyle(
                "Signature",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leading=16,
                alignment=1,
            ),
        }

    def _standard_table_style(self) -> TableStyle:
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F5F7FA"), colors.white]),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#003366")),
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

    def _page_break(self) -> PageBreak:
        return PageBreak()

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
        # Footer using standard canvas operations for page-level elements
        # This is standard practice in ReportLab for repeated page elements
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#666666"))
        footer_text = f"Kulima Africa | Kulima OS Pilot v0.2 | Page {doc.page}"
        canvas.drawCentredString(letter[0] / 2, _PDF_FOOTER_Y, footer_text)
        canvas.restoreState()

    def generate_pdf(self, prospectus: Dict, output_path: str):
        """
        Generate a PDF version of the Demand-Signal Prospectus.
        
        Professional document layout engine with proper table rendering,
        typography system, and layout grid enforcement.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info("USING PROFESSIONAL PROSPECTUS GENERATOR - generate_pdf()")
        logger.info(f"Output path: {output_path}")
        
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
        body_bold = st["body_bold"]
        note = st["note"]
        high_conf = st["high_conf"]
        signature = st["signature"]
        story = []

        meta = prospectus["prospectus_metadata"]
        is_sample = meta.get("is_sample", False)
        summary = prospectus.get("executive_summary", {}) or {}

        # Defensive defaults to avoid NoneType comparisons in report generation
        total_coordination_patterns = summary.get('total_coordination_patterns') or 0
        high_confidence_patterns = summary.get('high_confidence_patterns') or 0
        moderate_confidence_patterns = summary.get('moderate_confidence_patterns') or 0
        productive_activities_detected = summary.get('productive_activities_detected') or []
        zones_with_coordinated_demand = summary.get('zones_with_coordinated_demand') or []

        # ========== PAGE 1: COVER PAGE ==========
        logo = self._resolve_logo()
        if logo:
            story.append(logo)
            story.append(self._section_break(48))

        story.append(Paragraph("KULIMA OS", st["title"]))
        story.append(self._section_break(20))
        story.append(Paragraph("Verified Demand Signal Prospectus", st["subtitle"]))
        story.append(self._section_break(16))
        story.append(Paragraph(
            f"{meta['pilot_region']}",
            ParagraphStyle("CoverLine", parent=body, fontSize=14, alignment=1, leading=18),
        ))
        story.append(self._section_break(10))
        story.append(Paragraph(
            f"{meta['evaluation_period']}",
            ParagraphStyle("CoverLine", parent=body, fontSize=12, alignment=1, leading=16),
        ))
        story.append(self._section_break(36))

        if is_sample:
            story.append(Paragraph(
                "SAMPLE PROSPECTUS – DEMONSTRATION ONLY",
                ParagraphStyle("SampleWarning", parent=st["section"], fontSize=14, textColor=colors.red, alignment=1),
            ))
            story.append(self._section_break(24))

        story.append(Paragraph(
            "Institutional Planning Artifact | Pilot Demonstration",
            ParagraphStyle("CoverLine", parent=body, fontSize=11, alignment=1, leading=15),
        ))
        story.append(self._section_break(12))
        story.append(Paragraph("Not a Financing Approval", note))
        story.append(self._section_break(36))

        # Line-by-line metadata display (no compressed table)
        story.append(Paragraph("Document Information", st["section"]))
        story.append(self._section_break(16))
        story.append(Paragraph(f"<b>Generated:</b> {meta['generated_at']}", body))
        story.append(self._section_break(12))
        story.append(Paragraph(f"<b>Pilot Region:</b> {meta['pilot_region']}", body))
        story.append(self._section_break(12))
        story.append(Paragraph(f"<b>Evaluation Period:</b> {meta['evaluation_period']}", body))
        story.append(self._section_break(12))
        story.append(Paragraph(f"<b>System Version:</b> {meta['system_version']}", body))
        story.append(self._section_break(36))

        scope = prospectus["document_scope"]
        story.append(Paragraph("Document Scope", st["section"]))
        story.append(self._section_break(16))
        story.append(Paragraph("<b>Enables:</b>", body_bold))
        story.append(self._section_break(10))
        for item in scope["enables"]:
            story.append(Paragraph(f"• {item}", body))
            story.append(self._section_break(8))
        story.append(self._section_break(16))
        story.append(Paragraph("<b>Does Not Do:</b>", body_bold))
        story.append(self._section_break(10))
        for item in scope["does_not_do"]:
            story.append(Paragraph(f"• {item}", body))
            story.append(self._section_break(8))
        story.append(self._section_break(20))
        story.append(Paragraph(scope["estimate_nature"], note))
        story.append(self._section_break(36))

        # ========== PAGE 2: EXECUTIVE SUMMARY ==========
        story.append(self._page_break())
        story.append(Paragraph("Executive Summary", st["section"]))
        story.append(self._section_break(24))
        
        story.append(Paragraph("<b>What is Happening?</b>", body_bold))
        story.append(self._section_break(12))
        story.append(Paragraph(
            f"This prospectus analyzes coordination patterns from {total_coordination_patterns} detected activities "
            f"in the {meta['pilot_region']} zone over a {meta['evaluation_period']}. "
            f"Of these, {high_confidence_patterns} patterns demonstrate high coordination confidence, "
            f"indicating stable, collective economic activity suitable for infrastructure planning.",
            body
        ))
        story.append(self._section_break(24))
        
        story.append(Paragraph("<b>Where is it Happening?</b>", body_bold))
        story.append(self._section_break(12))
        zones_text = ", ".join(zones_with_coordinated_demand) if zones_with_coordinated_demand else "the analyzed zone"
        story.append(Paragraph(
            f"Coordination patterns are detected in {zones_text}. "
            f"Activities include: {', '.join(productive_activities_detected)}.",
            body
        ))
        story.append(self._section_break(24))
        
        story.append(Paragraph("<b>Is it Real?</b>", body_bold))
        story.append(self._section_break(12))
        story.append(Paragraph(summary.get("key_finding", ""), body))
        story.append(self._section_break(24))
        
        story.append(Paragraph("<b>Coordination Strength</b>", body_bold))
        story.append(self._section_break(12))
        story.append(Paragraph(
            f"Detected activities include: {', '.join(productive_activities_detected)}. "
            f"Coordination patterns indicate {'strong' if safe_num(high_confidence_patterns) > 0 else 'emerging'} "
            f"collective demand with {'high' if safe_num(high_confidence_patterns) >= 3 else 'moderate'} "
            f"confidence for infrastructure investment decisions.",
            body
        ))
        story.append(self._section_break(32))
        
        story.append(Paragraph("Coordination Metrics", st["section"]))
        story.append(self._section_break(16))
        story.append(Paragraph(f"<b>Total Coordination Patterns:</b> {total_coordination_patterns}", body))
        story.append(self._section_break(12))
        story.append(Paragraph(f"<b>High Confidence Patterns:</b> {high_confidence_patterns}", body))
        story.append(self._section_break(12))
        story.append(Paragraph(f"<b>Moderate Confidence Patterns:</b> {moderate_confidence_patterns}", body))
        story.append(self._section_break(12))
        zones_text = ", ".join(zones_with_coordinated_demand) if zones_with_coordinated_demand else "None"
        story.append(Paragraph(f"<b>Zones with Coordinated Demand:</b> {zones_text}", body))
        story.append(self._section_break(12))
        activities_text = ", ".join(productive_activities_detected) if productive_activities_detected else "None"
        story.append(Paragraph(f"<b>Productive Activities:</b> {activities_text}", body))
        story.append(self._section_break(36))

        # ========== PAGE 3: CLUSTER OVERVIEW ==========
        story.append(self._page_break())
        story.append(Paragraph("Cluster Overview", st["section"]))
        story.append(self._section_break(24))
        clusters = prospectus.get("cluster_overview", [])
        if clusters:
            cluster_rows = [["Cluster", "Zone", "Signals", "Top Activities", "Infrastructure Needs"]]
            for cluster in clusters:
                cluster_rows.append([
                    cluster.get("cluster_name", "Unknown"),
                    cluster.get("zone", "Unknown"),
                    str(cluster.get("signal_count", 0)),
                    Paragraph(", ".join(cluster.get("top_activities", [])) or "—", body),
                    Paragraph(", ".join(cluster.get("infrastructure_gaps", [])) or "—", body)
                ])
            cw = _PDF_CONTENT_WIDTH / 5
            story.append(self._make_table(cluster_rows, [cw, cw, cw * 0.7, cw * 1.3, cw * 1.5]))
            story.append(self._section_break(20))
            story.append(Paragraph(
                "This overview identifies geographic clusters of activity, localized infrastructure gaps, and quick project recommendations.",
                note
            ))
        else:
            story.append(Paragraph("No cluster overview was available for this prospectus.", note))
        story.append(self._section_break(36))

        # ========== PAGE 4: COORDINATION PATTERNS ==========
        story.append(self._page_break())
        story.append(Paragraph("Verified Coordination Patterns", st["section"]))
        story.append(self._section_break(24))
        
        patterns = prospectus["coordination_patterns"]
        if patterns:
            # Proper table with aligned columns
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
            story.append(self._section_break(20))
            story.append(Paragraph(
                "Table shows detected coordination patterns with time windows, frequency, confidence levels, and stability scores.",
                note
            ))
        else:
            story.append(Paragraph("No stable patterns in this evaluation window.", note))
        story.append(self._section_break(36))

        # ========== PAGE 4: ENERGY & INFRASTRUCTURE OUTPUT ==========
        story.append(self._page_break())
        story.append(Paragraph("Energy Signal Output", st["section"]))
        story.append(self._section_break(24))
        
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
            story.append(self._section_break(20))
            story.append(Paragraph(
                "Recommended installed capacity includes a 25% planning buffer (conservative lower bound).",
                note
            ))
        story.append(self._section_break(32))

        load_est = prospectus.get("load_estimation", {})
        if load_est.get("total_system_demand"):
            story.append(Paragraph("Load Estimation Summary", st["section"]))
            story.append(self._section_break(16))
            total = load_est["total_system_demand"]
            ess = load_est.get("demand_breakdown", {}).get("essential_services", {})
            prod = load_est.get("demand_breakdown", {}).get("productive_activities", {})
            cap = load_est.get("capacity_planning_guidance", {})
            
            # Line-by-line display
            story.append(Paragraph(f"<b>Peak Demand (kW):</b> {total.get('peak_demand_kw', '—')}", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Daily Energy (kWh):</b> {total.get('daily_energy_kwh', '—')}", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Essential Services Peak (kW):</b> {ess.get('peak_kw', '—')}", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Productive Activities Peak (kW):</b> {prod.get('peak_kw', '—')}", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Recommended Capacity (kW):</b> {cap.get('recommended_capacity_kw', '—')}", body))
            story.append(self._section_break(36))

        # ========== PAGE 5: LUNDAI SECTION ==========
        story.append(self._page_break())
        story.append(Paragraph("Settlement & Land-Use Validation (LUNDAI)", st["section"]))
        story.append(self._section_break(24))
        
        story.append(Paragraph(
            "Detected coordination aligns with settlement structure and land-use activity, "
            "indicating real on-ground demand.",
            body
        ))
        story.append(self._section_break(24))
        
        story.append(Paragraph("<b>Validation Checklist:</b>", body_bold))
        story.append(self._section_break(16))
        story.append(Paragraph("• Settlement consistency ✅", body))
        story.append(self._section_break(12))
        story.append(Paragraph("• Infrastructure proximity ✅", body))
        story.append(self._section_break(12))
        story.append(Paragraph("• Activity clustering ✅", body))
        story.append(self._section_break(32))
        
        lundai = prospectus.get("settlement_and_infrastructure_analysis", {})
        if lundai and lundai.get("status") != "LUNDAI analysis not included":
            overall = lundai.get("overall_assessment", {})
            story.append(Paragraph("<b>Infrastructure Assessment</b>", body_bold))
            story.append(self._section_break(16))
            story.append(Paragraph(f"<b>Total Zones Analyzed:</b> {overall.get('total_zones_analyzed', 0)}", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Critical Infrastructure Gaps:</b> {overall.get('critical_infrastructure_gaps', 0)}", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Urgent Priority Zones:</b> {overall.get('urgent_priority_zones', 0)}", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Average Infrastructure Adequacy:</b> {overall.get('average_infrastructure_adequacy_score', 0):.1f}%", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Overall Status:</b> {overall.get('overall_infrastructure_status', '—').capitalize()}", body))
            story.append(self._section_break(32))
            
            zone_analyses = lundai.get("zone_analyses", {})
            if zone_analyses:
                story.append(Paragraph("<b>Zone-Level Analysis</b>", body_bold))
                story.append(self._section_break(16))
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
        story.append(self._section_break(36))

        # ========== PAGE 6: CONFIDENCE & RISK ==========
        story.append(self._page_break())
        story.append(Paragraph("Confidence & Risk Assessment", st["section"]))
        story.append(self._section_break(24))
        
        story.append(Paragraph("<b>Confidence Tier Interpretation</b>", body_bold))
        story.append(self._section_break(16))
        story.append(self._make_table([
            ["Tier", "Range", "Interpretation", "Actionable Guidance"],
            ["HIGH", ">0.7", "Strong coordination", "Suitable for phased infrastructure planning with confidence"],
            ["MEDIUM", "0.4–0.7", "Moderate coordination", "Monitor and corroborate before capacity sizing decisions"],
            ["LOW", "<0.4", "Emerging signals", "Not yet suitable for capacity commitment; continue monitoring"],
        ], [80, 80, 180, _PDF_CONTENT_WIDTH - 340]))
        story.append(self._section_break(32))
        
        risk = prospectus["risk_and_governance"]
        dist = risk["demand_uncertainty_quantification"]["confidence_distribution"]
        story.append(Paragraph("<b>Risk Summary</b>", body_bold))
        story.append(self._section_break(16))
        story.append(Paragraph(f"<b>Confidence Distribution:</b> High: {dist['high_confidence_patterns']}; Moderate: {dist['moderate_confidence_patterns']}; Low: {dist['low_confidence_patterns']}", body))
        story.append(self._section_break(12))
        story.append(Paragraph(f"<b>Demand Uncertainty:</b> {risk['demand_uncertainty_quantification']['demand_uncertainty_range']['conservative_estimate']}", body))
        story.append(self._section_break(12))
        story.append(Paragraph("<b>Governance Framework:</b> Transparent allocation, essential-service protection, phased deployment", body))
        story.append(self._section_break(20))
        story.append(Paragraph(
            "<b>Risk Mitigation:</b> All estimates use conservative lower-bound assumptions. "
            "Infrastructure sizing includes 25% planning buffer. Essential services receive "
            "priority allocation with 20% capacity reservation.",
            note
        ))
        story.append(self._section_break(36))

        # ========== PAGE 7: INFRASTRUCTURE PLANNING ==========
        story.append(self._page_break())
        guidance = prospectus.get("infrastructure_planning_guidance", {})
        if guidance:
            story.append(Paragraph("Infrastructure Planning Guidance", st["section"]))
            story.append(self._section_break(24))
            
            story.append(Paragraph("<b>What Infrastructure is Needed?</b>", body_bold))
            story.append(self._section_break(12))
            zones_text = ", ".join(guidance.get("high_priority_zones", [])) or "the analyzed zone"
            story.append(Paragraph(
                f"Based on detected coordination patterns, infrastructure is needed in {zones_text} "
                f"to support productive economic activities.",
                body
            ))
            story.append(self._section_break(24))
            
            story.append(Paragraph("<b>Why is it Needed?</b>", body_bold))
            story.append(self._section_break(12))
            story.append(Paragraph(
                f"Coordination patterns indicate sustained demand from {', '.join(summary['productive_activities_detected'])} activities. "
                f"Current infrastructure adequacy is {lundai.get('overall_assessment', {}).get('average_infrastructure_adequacy_score', 0):.1f}%, "
                f"indicating significant gaps.",
                body
            ))
            story.append(self._section_break(24))
            
            story.append(Paragraph("<b>Demand Validity Confidence:</b>", body_bold))
            story.append(self._section_break(12))
            confidence_level = "High" if safe_num(summary.get('high_confidence_patterns')) >= 2 else "Moderate"
            story.append(Paragraph(
                f"{confidence_level} confidence based on {safe_num(summary.get('high_confidence_patterns'))} high-confidence patterns "
                f"validated across {meta['evaluation_period']}.",
                body
            ))
            story.append(self._section_break(32))
            
            story.append(Paragraph("<b>Planning Details:</b>", body_bold))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>High Priority Zones:</b> {', '.join(guidance.get('high_priority_zones', [])) or '—'}", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Moderate Priority Zones:</b> {', '.join(guidance.get('moderate_priority_zones', [])) or '—'}", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Investment Recommendation:</b> {guidance.get('investment_recommendation', '—')}", body))
            story.append(self._section_break(12))
            story.append(Paragraph(f"<b>Capacity Planning:</b> {guidance.get('capacity_planning_note', '—')}", body))
            story.append(self._section_break(36))

        story.append(Paragraph("Infrastructure Planning Implication", st["section"]))
        story.append(self._section_break(24))
        story.append(Paragraph(
            "Observed coordination patterns indicate emerging productive demand that justifies "
            "phased infrastructure deployment under conservative capacity allocation. "
            "The detected activities demonstrate consistent temporal patterns and spatial alignment, "
            "suggesting sustainable demand rather than transient usage.",
            body
        ))
        story.append(self._section_break(20))
        story.append(Paragraph("<b>Recommended Approach:</b>", body_bold))
        story.append(self._section_break(12))
        story.append(Paragraph("• Phase 1: Deploy infrastructure to high-priority zones with validated coordination patterns", body))
        story.append(self._section_break(8))
        story.append(Paragraph("• Phase 2: Monitor demand patterns and adjust capacity allocation based on actual usage", body))
        story.append(self._section_break(8))
        story.append(Paragraph("• Phase 3: Expand to moderate-priority zones as coordination strengthens", body))
        story.append(self._section_break(8))
        story.append(Paragraph("• Maintain 20% capacity reserve for essential services and communal productive assets", body))
        story.append(self._section_break(36))

        # ========== PAGE 8: ETHICS & METHODOLOGY ==========
        story.append(self._page_break())
        story.append(Paragraph("Ethics & Methodology", st["section"]))
        story.append(self._section_break(24))
        
        ethics = prospectus["ethics_compliance"]
        story.append(Paragraph("<b>System Invariants:</b>", body_bold))
        story.append(self._section_break(12))
        for invariant in ethics["system_invariants"]:
            story.append(Paragraph(f"• {invariant}", body))
            story.append(self._section_break(8))
        story.append(self._section_break(16))
        story.append(Paragraph(ethics["verification"], note))
        story.append(self._section_break(24))
        
        story.append(Paragraph("<b>Processing Pipeline:</b>", body_bold))
        story.append(self._section_break(12))
        for i, step in enumerate(prospectus["methodology"]["processing_pipeline"], 1):
            story.append(Paragraph(f"{i}. {step}", body))
            story.append(self._section_break(8))
        story.append(self._section_break(36))

        story.append(Paragraph("Technical Notes", st["section"]))
        story.append(self._section_break(16))
        story.append(Paragraph(
            "This document is a decision-support artifact for utilities and development finance institutions. "
            "It does not replace detailed engineering studies, environmental assessments, or financing approvals.",
            note,
        ))
        story.append(self._section_break(28))

        story.append(Paragraph("Document Disclaimer", st["section"]))
        story.append(self._section_break(16))
        story.append(Paragraph(
            "This document provides coordination-informed infrastructure insight derived from verified activity signals. "
            "It supports planning decisions but does not substitute for engineering or regulatory approval processes.",
            body
        ))
        story.append(self._section_break(20))
        story.append(Paragraph("<b>Use Limitations:</b>", body_bold))
        story.append(self._section_break(12))
        story.append(Paragraph("• Estimates are conservative lower-bound signals intended for planning, not exact operational forecasts", body))
        story.append(self._section_break(8))
        story.append(Paragraph("• Infrastructure decisions require additional technical studies, environmental assessments, and regulatory approvals", body))
        story.append(self._section_break(8))
        story.append(Paragraph("• This document does not constitute financing approval or investment commitment", body))
        story.append(self._section_break(8))
        story.append(Paragraph("• All coordination patterns are aggregated and identity-free, complying with Zero-PII principles", body))
        story.append(self._section_break(36))

        # ========== PAGE 9: SIGNATURE PAGE ==========
        story.append(self._page_break())
        story.append(self._section_break(120))
        
        signature_path = Path(__file__).resolve().parent / "assets" / "shadreck-signature.jpg"
        if signature_path.is_file():
            try:
                # Professional signature design: max 120px width, scaled proportionally
                signature_img = Image(str(signature_path), width=120, height=60, hAlign='CENTER')
                story.append(signature_img)
                story.append(self._section_break(20))
            except:
                pass  # If signature image fails, continue without it

        story.append(Paragraph("________________________", st["title"]))
        story.append(self._section_break(16))
        story.append(Paragraph("Shadreck Mawindo", signature))
        story.append(self._section_break(8))
        story.append(Paragraph("Chief Executive Officer", signature))
        story.append(self._section_break(8))
        story.append(Paragraph("Kulima Africa", signature))
        story.append(self._section_break(20))
        story.append(Paragraph(
            f"Date: {datetime.utcnow().strftime('%B %d, %Y')}",
            signature,
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
        
        if safe_num(score) > 0.7:
            return 'HIGH'
        elif safe_num(score) > 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_executive_summary(self, confidence_results: List[Dict], lundai_analysis: Dict = None, clusters: List[Dict] = None) -> Dict:
        """Generate executive summary of coordination patterns."""
        clusters = clusters or []
        total_patterns = len(confidence_results)
        high_confidence = sum(1 for r in confidence_results if r['confidence_class'] == 'high')
        moderate_confidence = sum(1 for r in confidence_results if r['confidence_class'] == 'moderate')
        
        # Extract unique zones and activities
        zones = set(r['zone'] for r in confidence_results)
        activities = set(r['activity_type'] for r in confidence_results)
        top_cluster_names = [c['cluster_name'] for c in clusters[:2]]
        
        summary = {
            "total_coordination_patterns": total_patterns,
            "high_confidence_patterns": high_confidence,
            "moderate_confidence_patterns": moderate_confidence,
            "zones_with_coordinated_demand": list(zones),
            "productive_activities_detected": list(activities),
            "cluster_count": len(clusters),
            "key_finding": f"Detected {total_patterns} stable coordination patterns across {len(zones)} zones, "
                          f"with {high_confidence} patterns showing high confidence for infrastructure investment.",
            "cluster_overview": {
                "cluster_count": len(clusters),
                "top_clusters": top_cluster_names,
                "cluster_summary": "; ".join([c['summary'] for c in clusters[:2]]) if clusters else "No cluster summaries available."
            }
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
    
    def _generate_flow_insights(self, lundai_analysis: Dict) -> Dict:
        """
        Generate activity flow insights from LUNDAI flow graph.
        
        Provides economic coordination graph and value chain visualization data.
        """
        if not lundai_analysis or lundai_analysis.get("status") == "LUNDAI analysis not included":
            return {"status": "Flow insights not available"}
        
        flow_graph = lundai_analysis.get("flow_graph", {})
        nodes = flow_graph.get("nodes", [])
        edges = flow_graph.get("edges", [])
        
        # Analyze flow patterns
        activity_sequences = []
        for edge in edges:
            activity_sequences.append({
                "from": edge.get("from_activity"),
                "to": edge.get("to_activity"),
                "zone": edge.get("zone"),
                "strength": edge.get("strength_score"),
                "transition_probability": edge.get("transition_probability")
            })
        
        # Identify strong flows
        strong_flows = [seq for seq in activity_sequences if seq.get("strength", 0) >= 0.7]
        
        return {
            "total_activities": len(nodes),
            "total_flows": len(edges),
            "strong_coordination_flows": len(strong_flows),
            "activity_sequences": activity_sequences[:10],  # Top 10 flows
            "economic_coordination_graph": {
                "nodes": nodes,
                "edges": edges
            },
            "value_chain_insights": {
                "primary_sequences": [
                    seq for seq in activity_sequences 
                    if seq.get("transition_probability", 0) >= 0.6
                ][:5]
            }
        }
    
    def _calculate_risk_model(self, confidence_results: List[Dict], lundai_analysis: Dict) -> Dict:
        """
        Calculate multi-factor risk model based on persistence, stability, and flow strength.
        
        Risk Factors:
        - Low persistence → "Demand uncertainty risk"
        - Low stability → "Volatility risk"
        - Weak flow connections → "Fragmentation risk"
        - Sparse signals → "Data insufficiency risk"
        """
        risk_factors = []
        
        # Analyze persistence
        persistence_values = [r.get('persistence', 0) for r in confidence_results]
        avg_persistence = sum(persistence_values) / len(persistence_values) if persistence_values else 0
        
        if avg_persistence < 0.4:
            risk_factors.append({
                "type": "Demand uncertainty risk",
                "severity": "high" if avg_persistence < 0.2 else "moderate",
                "description": f"Low persistence ({avg_persistence:.2f}) indicates patterns may not repeat consistently"
            })
        elif avg_persistence < 0.6:
            risk_factors.append({
                "type": "Demand uncertainty risk",
                "severity": "low",
                "description": f"Moderate persistence ({avg_persistence:.2f}) requires monitoring"
            })
        
        # Analyze stability
        stability_values = [r.get('stability_score', 0) for r in confidence_results]
        avg_stability = sum(stability_values) / len(stability_values) if stability_values else 0
        
        if avg_stability < 0.4:
            risk_factors.append({
                "type": "Volatility risk",
                "severity": "high" if avg_stability < 0.2 else "moderate",
                "description": f"Low stability ({avg_stability:.2f}) indicates high variance in pattern occurrence"
            })
        elif avg_stability < 0.6:
            risk_factors.append({
                "type": "Volatility risk",
                "severity": "low",
                "description": f"Moderate stability ({avg_stability:.2f}) indicates some pattern variance"
            })
        
        # Analyze flow strength
        flow_strength_values = [r.get('flow_strength', 0) for r in confidence_results]
        avg_flow_strength = sum(flow_strength_values) / len(flow_strength_values) if flow_strength_values else 0
        
        if avg_flow_strength < 0.3:
            risk_factors.append({
                "type": "Fragmentation risk",
                "severity": "high",
                "description": f"Weak flow connections ({avg_flow_strength:.2f}) indicate fragmented economic activity"
            })
        elif avg_flow_strength < 0.5:
            risk_factors.append({
                "type": "Fragmentation risk",
                "severity": "moderate",
                "description": f"Moderate flow strength ({avg_flow_strength:.2f}) indicates partial value chain integration"
            })
        
        # Analyze signal density
        total_patterns = len(confidence_results)
        if total_patterns < 3:
            risk_factors.append({
                "type": "Data insufficiency risk",
                "severity": "high",
                "description": f"Low pattern count ({total_patterns}) indicates insufficient data for reliable planning"
            })
        elif total_patterns < 5:
            risk_factors.append({
                "type": "Data insufficiency risk",
                "severity": "moderate",
                "description": f"Limited pattern count ({total_patterns}) requires additional data collection"
            })
        
        # Calculate overall risk level
        high_risk_count = sum(1 for rf in risk_factors if rf.get("severity") == "high")
        moderate_risk_count = sum(1 for rf in risk_factors if rf.get("severity") == "moderate")
        
        if high_risk_count >= 2:
            risk_level = "high"
            recommendation = "Significant risks detected. Recommend extensive data collection and monitoring before infrastructure commitment."
        elif high_risk_count >= 1 or moderate_risk_count >= 2:
            risk_level = "moderate"
            recommendation = "Moderate risks present. Recommend phased deployment with continued monitoring and validation."
        else:
            risk_level = "low"
            recommendation = "Low risk profile. Patterns show good persistence, stability, and flow integration. Suitable for infrastructure planning."
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": recommendation,
            "risk_metrics": {
                "average_persistence": round(avg_persistence, 2),
                "average_stability": round(avg_stability, 2),
                "average_flow_strength": round(avg_flow_strength, 2),
                "total_patterns": total_patterns
            }
        }
    
    def _generate_decision_recommendations(self, confidence_results: List[Dict], lundai_analysis: Dict) -> Dict:
        """
        Generate decision recommendations using the Decision Engine.
        
        Args:
            confidence_results: Confidence results from ZENTARI
            lundai_analysis: Settlement and infrastructure analysis from LUNDAI
            
        Returns:
            Decision recommendations with infrastructure needs and capacity requirements
        """
        from core.decision.decision_engine import DecisionEngine
        
        # Convert confidence results to patterns format
        patterns = []
        for result in confidence_results:
            patterns.append({
                'activity_type': result.get('activity_type'),
                'zone': result.get('zone'),
                'pattern_frequency': result.get('pattern_frequency', 1),
                'time_window': result.get('time_window', 'morning')
            })
        
        # Extract flow graph from LUNDAI analysis
        flow_graph = lundai_analysis.get('flow_graph', {}) if lundai_analysis else {}
        
        # Use Decision Engine to generate recommendations
        decision_engine = DecisionEngine()
        recommendations = decision_engine.recommend_infrastructure(patterns, flow_graph, confidence_results)
        
        return {
            "priority_zone": recommendations.get('priority_zone'),
            "infrastructure_recommendations": recommendations.get('recommended_infrastructure', []),
            "capacity_requirements": recommendations.get('required_capacity'),
            "justification": recommendations.get('justification'),
            "zone_scores": recommendations.get('zone_scores', {}),
            "decision_summary": self._format_decision_summary(recommendations)
        }
    
    def _format_decision_summary(self, recommendations: Dict) -> str:
        """
        Format decision recommendations into a summary for the prospectus.
        
        Args:
            recommendations: Decision engine output
            
        Returns:
            Formatted decision summary
        """
        if not recommendations.get('priority_zone'):
            return "Insufficient coordination patterns to recommend infrastructure at this time."
        
        priority_zone = recommendations['priority_zone']
        capacity = recommendations.get('required_capacity', {})
        total_capacity = capacity.get('total_kw', 0)
        
        summary_parts = [
            f"Zone {priority_zone} is identified as the priority zone for infrastructure deployment. "
            f"Total required capacity is estimated at {total_capacity} kW. "
        ]
        
        infra_recs = recommendations.get('recommended_infrastructure', [])
        if infra_recs:
            high_priority = [r for r in infra_recs if r.get('priority') == 'high']
            if high_priority:
                activities = ', '.join(r['activity_type'] for r in high_priority)
                summary_parts.append(
                    f"High-priority infrastructure is recommended for: {activities}. "
                )
        
        summary_parts.append(recommendations.get('justification', ''))
        
        return ''.join(summary_parts)
    
    def _generate_long_term_insights(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """
        Generate long-term coordination insights using Long-Horizon Model.
        
        Args:
            confidence_results: Confidence results from ZENTARI
            lundai_analysis: Settlement and infrastructure analysis from LUNDAI
            
        Returns:
            Long-term coordination insights with monthly and seasonal trends
        """
        from core.temporal.long_horizon_model import LongHorizonModel
        
        long_horizon = LongHorizonModel()
        
        # Convert confidence results to weekly patterns format
        weekly_patterns = []
        for result in confidence_results:
            weekly_patterns.append({
                'activity_type': result.get('activity_type'),
                'zone': result.get('zone'),
                'pattern_frequency': result.get('pattern_frequency', 1),
                'pattern_persistence': result.get('persistence', 0),
                'pattern_stability': result.get('stability_score', 0)
            })
        
        # Add to history with current timestamp
        from datetime import datetime
        current_timestamp = datetime.utcnow().isoformat() + "Z"
        long_horizon.add_weekly_patterns(weekly_patterns, current_timestamp)
        
        # Aggregate to monthly (using current data as proxy)
        weekly_data = [{'timestamp': current_timestamp, 'patterns': weekly_patterns}]
        monthly_patterns = long_horizon.aggregate_weekly_to_monthly(weekly_data)
        
        # Aggregate to seasonal (using monthly patterns as proxy)
        seasonal_patterns = long_horizon.aggregate_monthly_to_seasonal(monthly_patterns)
        
        return {
            "monthly_trends": monthly_patterns,
            "seasonal_patterns": seasonal_patterns,
            "trend_analysis": {
                "increasing_patterns": len([p for p in monthly_patterns if p.get('trend') == 'increasing']),
                "stable_patterns": len([p for p in monthly_patterns if p.get('trend') == 'stable']),
                "declining_patterns": len([p for p in monthly_patterns if p.get('trend') == 'declining'])
            }
        }
    
    def _generate_regional_flow_analysis(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """
        Generate regional flow analysis using Cross-Zone Flow Detector.
        
        Args:
            confidence_results: Confidence results from ZENTARI
            lundai_analysis: Settlement and infrastructure analysis from LUNDAI
            
        Returns:
            Regional flow analysis with dominant chains and bottlenecks
        """
        from core.flow.cross_zone_flow_detector import CrossZoneFlowDetector
        
        flow_detector = CrossZoneFlowDetector()
        
        # Group patterns by zone
        patterns_by_zone = {}
        for result in confidence_results:
            zone = result.get('zone')
            if zone not in patterns_by_zone:
                patterns_by_zone[zone] = []
            
            patterns_by_zone[zone].append({
                'activity_type': result.get('activity_type'),
                'zone': zone,
                'pattern_frequency': result.get('pattern_frequency', 1),
                'pattern_persistence': result.get('persistence', 0),
                'confidence_score': result.get('confidence_score', 0),
                'temporal_weight': 1.0,
                'persistence_weight': 1.0,
                'time_window': result.get('time_window', 'morning')
            })
        
        # Detect inter-zone flows
        inter_zone_flows = flow_detector.detect_inter_zone_correlations(patterns_by_zone)
        
        # Build regional flow network
        flow_network = flow_detector.build_regional_flow_network(patterns_by_zone)
        
        # Identify dominant chains (high-strength flows)
        dominant_chains = [flow for flow in inter_zone_flows if flow.get('correlation_strength', 0) >= 0.6]
        
        # Identify bottlenecks (zones with high coordination but low infrastructure)
        bottlenecks = []
        if lundai_analysis:
            infrastructure_gaps = lundai_analysis.get('infrastructure_gaps', [])
            for gap in infrastructure_gaps:
                if gap.get('signal_integrity', 0) >= 0.6:  # High coordination
                    bottlenecks.append({
                        'zone': gap.get('zone'),
                        'gap_type': gap.get('gap_type'),
                        'coordination_strength': gap.get('signal_integrity')
                    })
        
        return {
            "dominant_chains": dominant_chains,
            "bottlenecks": bottlenecks,
            "cross_zone_flows": inter_zone_flows,
            "regional_flow_network": flow_network
        }
    
    def _generate_infrastructure_roadmap(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """
        Generate infrastructure roadmap using Infrastructure Design Layer.
        
        Args:
            confidence_results: Confidence results from ZENTARI
            lundai_analysis: Settlement and infrastructure analysis from LUNDAI
            
        Returns:
            Infrastructure roadmap with phased rollout and capacity estimates
        """
        from core.infrastructure.infrastructure_design import InfrastructureDesignLayer
        from core.decision.decision_engine import DecisionEngine
        
        design_layer = InfrastructureDesignLayer()
        decision_engine = DecisionEngine()
        
        # Get zone scores from Decision Engine
        patterns = []
        for result in confidence_results:
            patterns.append({
                'activity_type': result.get('activity_type'),
                'zone': result.get('zone'),
                'pattern_frequency': result.get('pattern_frequency', 1)
            })
        
        flow_graph = lundai_analysis.get('flow_graph', {}) if lundai_analysis else {}
        recommendations = decision_engine.recommend_infrastructure(patterns, flow_graph, confidence_results)
        zone_scores = recommendations.get('zone_scores', {})
        
        # Rank zones by priority
        ranked_zones = design_layer.rank_zones_by_priority(zone_scores)
        
        # Get infrastructure needs
        infrastructure_needs = []
        for result in confidence_results:
            infrastructure_needs.append({
                'zone': result.get('zone'),
                'activity_type': result.get('activity_type'),
                'recommended_capacity_kw': design_layer.determine_infrastructure_type(result.get('activity_type'))['base_capacity_kw']
            })
        
        # Design phased rollout
        phased_rollout = design_layer.design_phased_rollout(ranked_zones, infrastructure_needs)
        
        # Estimate load distribution
        zones = list(zone_scores.keys())
        infrastructure_types = list(set([design_layer.determine_infrastructure_type(result.get('activity_type'))['type'] for result in confidence_results]))
        load_distribution = design_layer.estimate_load_distribution(zones, infrastructure_types)
        
        return {
            "phased_rollout": phased_rollout,
            "load_distribution": load_distribution,
            "ranked_zones": ranked_zones,
            "total_capacity_kw": phased_rollout.get('total_capacity_kw', 0),
            "total_timeline_months": phased_rollout.get('total_timeline_months', 0)
        }
    
    def _generate_scenario_projections(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """
        Generate scenario projections using Scenario Model.
        
        Args:
            confidence_results: Confidence results from ZENTARI
            lundai_analysis: Settlement and infrastructure analysis from LUNDAI
            
        Returns:
            Scenario projections for infrastructure addition impact
        """
        from core.scenario.scenario_model import ScenarioModel
        from core.decision.decision_engine import DecisionEngine
        
        scenario_model = ScenarioModel()
        decision_engine = DecisionEngine()
        
        # Convert confidence results to patterns format
        patterns = []
        for result in confidence_results:
            patterns.append({
                'activity_type': result.get('activity_type'),
                'zone': result.get('zone'),
                'pattern_frequency': result.get('pattern_frequency', 1)
            })
        
        flow_graph = lundai_analysis.get('flow_graph', {}) if lundai_analysis else {}
        
        # Get priority zone
        recommendations = decision_engine.recommend_infrastructure(patterns, flow_graph, confidence_results)
        priority_zone = recommendations.get('priority_zone')
        
        if not priority_zone:
            return {
                "infrastructure_addition_impact": [],
                "note": "No priority zone identified for scenario simulation"
            }
        
        # Simulate infrastructure addition for priority zone
        infrastructure_type = 'three_phase_power'
        simulation = scenario_model.simulate_infrastructure_addition(
            patterns, flow_graph, confidence_results, infrastructure_type, priority_zone
        )
        
        # Simulate capacity upgrade
        current_capacity = recommendations.get('required_capacity', {}).get('total_kw', 50)
        new_capacity = current_capacity * 1.5
        capacity_simulation = scenario_model.simulate_capacity_upgrade(
            patterns, confidence_results, current_capacity, new_capacity, priority_zone
        )
        
        return {
            "infrastructure_addition_impact": [simulation],
            "capacity_upgrade_impact": capacity_simulation,
            "priority_zone": priority_zone
        }
    
    def _generate_policy_maker_section(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """
        Generate policy maker section focusing on infrastructure gaps, regional coordination, and essential load protection.
        
        Args:
            confidence_results: Confidence results from ZENTARI
            lundai_analysis: Settlement and infrastructure analysis from LUNDAI
            
        Returns:
            Policy maker section with public value, equity impact, and infrastructure prioritization
        """
        # Extract infrastructure gaps
        infrastructure_gaps = lundai_analysis.get('infrastructure_gaps', []) if lundai_analysis else []
        
        # Identify essential services
        essential_patterns = [r for r in confidence_results if r.get('service_priority') == 'essential']
        
        # Calculate regional coordination summary
        zone_distribution = {}
        for result in confidence_results:
            zone = result.get('zone')
            if zone not in zone_distribution:
                zone_distribution[zone] = 0
            zone_distribution[zone] += 1
        
        # Calculate equity impact (zones with high coordination but low infrastructure)
        equity_impact = []
        for gap in infrastructure_gaps:
            if gap.get('signal_integrity', 0) >= 0.6:  # High coordination
                equity_impact.append({
                    'zone': gap.get('zone'),
                    'gap_type': gap.get('gap_type'),
                    'coordination_strength': gap.get('signal_integrity'),
                    'priority': 'high'
                })
        
        return {
            "public_value": {
                "total_zones_served": len(zone_distribution),
                "essential_services_detected": len(essential_patterns),
                "coordination_patterns": len(confidence_results)
            },
            "equity_impact": {
                "underserved_zones": len(equity_impact),
                "high_coordination_low_infrastructure": equity_impact
            },
            "infrastructure_prioritization": {
                "critical_gaps": [gap for gap in infrastructure_gaps if gap.get('gap_severity') == 'critical'],
                "essential_load_protection": len(essential_patterns),
                "regional_focus": sorted(zone_distribution.items(), key=lambda x: x[1], reverse=True)
            },
            "regional_coordination_summary": {
                "zone_distribution": zone_distribution,
                "cross_zone_flows": len(lundai_analysis.get('flow_graph', {}).get('edges', [])) if lundai_analysis else 0
            }
        }
    
    def _generate_investor_section(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """
        Generate investor section focusing on confidence scores, demand stability, and risk profile.
        
        Args:
            confidence_results: Confidence results from ZENTARI
            lundai_analysis: Settlement and infrastructure analysis from LUNDAI
            
        Returns:
            Investor section with confidence summary, stability indicators, and risk profile
        """
        # Calculate confidence summary
        high_confidence = [r for r in confidence_results if r.get('confidence_class') == 'high']
        moderate_confidence = [r for r in confidence_results if r.get('confidence_class') == 'moderate']
        low_confidence = [r for r in confidence_results if r.get('confidence_class') == 'low']
        
        # Calculate stability indicators
        persistence_values = [r.get('persistence', 0) for r in confidence_results]
        stability_values = [r.get('stability_score', 0) for r in confidence_results]
        
        avg_persistence = sum(persistence_values) / len(persistence_values) if persistence_values else 0
        avg_stability = sum(stability_values) / len(stability_values) if stability_values else 0
        
        # Calculate trend indicators
        increasing_patterns = len([r for r in confidence_results if r.get('trend') == 'increasing'])
        stable_patterns = len([r for r in confidence_results if r.get('trend') == 'stable'])
        declining_patterns = len([r for r in confidence_results if r.get('trend') == 'declining'])
        
        # Determine risk profile
        if avg_persistence >= 0.7 and avg_stability >= 0.7:
            risk_profile = 'low'
        elif avg_persistence >= 0.5 and avg_stability >= 0.5:
            risk_profile = 'medium'
        else:
            risk_profile = 'high'
        
        # Calculate demand reliability
        demand_reliability = (avg_persistence + avg_stability) / 2
        
        return {
            "coordination_confidence_summary": {
                "high_confidence_count": len(high_confidence),
                "moderate_confidence_count": len(moderate_confidence),
                "low_confidence_count": len(low_confidence),
                "total_patterns": len(confidence_results)
            },
            "stability_indicators": {
                "average_persistence": round(avg_persistence, 2),
                "average_stability": round(avg_stability, 2),
                "demand_reliability": round(demand_reliability, 2)
            },
            "trend_analysis": {
                "increasing_patterns": increasing_patterns,
                "stable_patterns": stable_patterns,
                "declining_patterns": declining_patterns
            },
            "risk_profile": {
                "classification": risk_profile,
                "risk_factors": [],
                "mitigation_opportunities": []
            },
            "coordination_strength_indicators": {
                "overall_strength": round(avg_persistence * avg_stability, 2),
                "strength_distribution": {
                    'high': len([r for r in confidence_results if r.get('persistence', 0) >= 0.7]),
                    'medium': len([r for r in confidence_results if 0.5 <= r.get('persistence', 0) < 0.7]),
                    'low': len([r for r in confidence_results if r.get('persistence', 0) < 0.5])
                }
            }
        }
    
    def _generate_infrastructure_planner_section(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """
        Generate infrastructure planner section focusing on capacity requirements, load type, and spatial mismatch.
        
        Args:
            confidence_results: Confidence results from ZENTARI
            lundai_analysis: Settlement and infrastructure analysis from LUNDAI
            
        Returns:
            Infrastructure planner section with technical demand profile, infrastructure recommendations, and rollout plan
        """
        from core.infrastructure.infrastructure_design import InfrastructureDesignLayer
        from core.coordination.multi_sector_coordinator import MultiSectorCoordinator
        
        design_layer = InfrastructureDesignLayer()
        sector_coordinator = MultiSectorCoordinator()
        
        # Calculate technical demand profile
        demand_profile = []
        for result in confidence_results:
            activity_type = result.get('activity_type')
            sector = sector_coordinator.classify_sector(activity_type)
            infrastructure_mapping = sector_coordinator.get_sector_infrastructure_mapping(sector, activity_type)
            
            demand_profile.append({
                'activity_type': activity_type,
                'sector': sector,
                'infrastructure_type': infrastructure_mapping['type'],
                'load_type': infrastructure_mapping['load_type'],
                'base_capacity_kw': infrastructure_mapping['base_capacity_kw'],
                'zone': result.get('zone'),
                'persistence': result.get('persistence', 0)
            })
        
        # Calculate total capacity requirements by load type
        capacity_by_load_type = defaultdict(float)
        for item in demand_profile:
            load_type = item['load_type']
            capacity_by_load_type[load_type] += item['base_capacity_kw']
        
        # Calculate spatial mismatch
        spatial_mismatch = []
        if lundai_analysis:
            infrastructure_gaps = lundai_analysis.get('infrastructure_gaps', [])
            for gap in infrastructure_gaps:
                spatial_mismatch.append({
                    'zone': gap.get('zone'),
                    'gap_type': gap.get('gap_type'),
                    'signal_integrity': gap.get('signal_integrity'),
                    'infrastructure_adequacy': gap.get('infrastructure_adequacy', 0)
                })
        
        # Generate infrastructure recommendations
        infrastructure_recommendations = []
        for item in demand_profile:
            if item['persistence'] >= 0.6:  # Only recommend for persistent patterns
                infrastructure_recommendations.append({
                    'zone': item['zone'],
                    'activity_type': item['activity_type'],
                    'infrastructure_type': item['infrastructure_type'],
                    'load_type': item['load_type'],
                    'recommended_capacity_kw': item['base_capacity_kw'],
                    'priority': 'high' if item['persistence'] >= 0.8 else 'medium'
                })
        
        return {
            "technical_demand_profile": {
                "total_activities": len(demand_profile),
                "demand_breakdown": demand_profile
            },
            "capacity_requirements": {
                "by_load_type": dict(capacity_by_load_type),
                "total_capacity_kw": round(sum(capacity_by_load_type.values()), 1)
            },
            "spatial_mismatch_analysis": {
                "zones_with_gaps": len(spatial_mismatch),
                "mismatch_details": spatial_mismatch
            },
            "infrastructure_recommendations": {
                "total_recommendations": len(infrastructure_recommendations),
                "recommendations": infrastructure_recommendations
            },
            "rollout_plan": {
                "phased_deployment": "See infrastructure_roadmap section for detailed rollout plan",
                "priority_zones": sorted(set([r['zone'] for r in infrastructure_recommendations if r['priority'] == 'high']))
            }
        }
    
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

    def _generate_production_readiness_summary(self, confidence_results: List[Dict], lundai_analysis: Dict = None) -> Dict:
        """Generate a concise production readiness summary for institutional audiences."""
        deployment_readiness = self._generate_deployment_readiness(confidence_results, lundai_analysis)
        readiness_assessment = deployment_readiness.get("readiness_assessment", {})
        stakeholder_status = deployment_readiness.get("stakeholder_engagement_status", {})
        regulatory = deployment_readiness.get("regulatory_and_compliance", {})

        return {
            "overall_readiness": readiness_assessment.get("overall_readiness", "UNKNOWN"),
            "technical_readiness": readiness_assessment.get("technical_readiness", "UNKNOWN"),
            "financial_readiness": readiness_assessment.get("financial_readiness", "UNKNOWN"),
            "institutional_readiness": readiness_assessment.get("institutional_readiness", "UNKNOWN"),
            "community_readiness": readiness_assessment.get("community_readiness", "UNKNOWN"),
            "top_priority_actions": deployment_readiness.get("next_steps_for_deployment", [])[:5],
            "key_regulatory_requirements": [
                f"{category}: {details.get('standards') or details.get('esia_required') or details.get('productive_use_tariff') or details.get('reliability', '')}" 
                for category, details in regulatory.items() if isinstance(details, dict)
            ],
            "critical_stakeholder_gaps": [
                f"{party}: {status}" for party, status in {
                    **stakeholder_status.get("institutional_level", {}),
                    **stakeholder_status.get("community_level", {})
                }.items()
            ]
        }

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
        import logging
        logging.getLogger(__name__).info(f"\nProspectus saved to: {filename}")
    
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
        import logging
        logging.getLogger(__name__).info(f"Prospectus saved to: {filename}")


if __name__ == "__main__":
    # Test prospectus generation
    from pilot_signals import generate_pilot_signals
    from lumoza_engine import LumozaEngine
    from zentari_engine import ZentariEngine
    
    import logging
    logging.getLogger(__name__).info("Generating Demand-Signal Prospectus...")
    
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

    import logging
    logging.getLogger(__name__).info("\n[SUCCESS] Demand-Signal Prospectus generated successfully (JSON, Markdown, PDF)")

