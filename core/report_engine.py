"""
Kulima OS — Report Generation Engine
Transforms MasterDPIOutput into professionally formatted, investor-grade PDF reports.

Uses ReportLab for PDF generation (no external binary dependencies).
Produces auditable, branded, watermarked documents suitable for
government, DFI, and utility stakeholders.
"""

import os
import json
import uuid
import hashlib
import logging
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas

from core.dpi_schema import MasterDPIOutput

logger = logging.getLogger(__name__)

# ===========================================
# Brand Constants
# ===========================================
BRAND_PRIMARY = HexColor("#0b2a17")
BRAND_ACCENT = HexColor("#00e676")
BRAND_LIGHT_BG = HexColor("#f0faf5")
BRAND_MUTED = HexColor("#666666")
BRAND_WHITE = HexColor("#ffffff")
BRAND_DARK_TEXT = HexColor("#111111")
BRAND_WARNING = HexColor("#e65100")
BRAND_TABLE_HEADER = HexColor("#0b2a17")
BRAND_TABLE_ROW_ALT = HexColor("#f5f5f5")

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


def _build_styles():
    """Build the full set of paragraph styles for the prospectus."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ProspectusTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=28,
        textColor=BRAND_PRIMARY,
        spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        name="ProspectusSubtitle",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=BRAND_MUTED,
        spaceAfter=8 * mm,
        spaceBefore=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=BRAND_PRIMARY,
        spaceBefore=10 * mm,
        spaceAfter=4 * mm,
        borderWidth=0,
    ))
    styles.add(ParagraphStyle(
        name="SubSectionHeading",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=BRAND_PRIMARY,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=BRAND_DARK_TEXT,
        spaceAfter=3 * mm,
        alignment=TA_JUSTIFY,
    ))
    styles.add(ParagraphStyle(
        name="MetricLabel",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=BRAND_MUTED,
    ))
    styles.add(ParagraphStyle(
        name="MetricValue",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=BRAND_PRIMARY,
    ))
    styles.add(ParagraphStyle(
        name="Badge",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=BRAND_ACCENT,
    ))
    styles.add(ParagraphStyle(
        name="WarningText",
        fontName="Helvetica-BoldOblique",
        fontSize=9,
        leading=12,
        textColor=BRAND_WARNING,
        spaceBefore=2 * mm,
        spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name="FooterText",
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=BRAND_MUTED,
        alignment=TA_CENTER,
    ))
    return styles


class _WatermarkCanvas(canvas.Canvas):
    """Custom canvas that draws a watermark and page numbers on every page."""

    def __init__(self, *args, report_id: str = "", **kwargs):
        self._report_id = report_id
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        super().showPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for idx, state in enumerate(self._saved_page_states):
            self.__dict__.update(state)
            self._draw_watermark()
            self._draw_footer(idx + 1, num_pages)
            super().showPage()
        super().save()

    def _draw_watermark(self):
        self.saveState()
        self.setFont("Helvetica-Bold", 40)
        self.setFillColor(HexColor("#e0e0e0"), alpha=0.15)
        self.translate(A4[0] / 2, A4[1] / 2)
        self.rotate(45)
        self.drawCentredString(0, 0, "KULIMA OS — PILOT SYSTEM")
        self.restoreState()

    def _draw_footer(self, page_num, total_pages):
        self.saveState()
        self.setFont("Helvetica", 7)
        self.setFillColor(BRAND_MUTED)
        w, _ = A4
        y = 15 * mm
        self.drawString(20 * mm, y, f"Report ID: {self._report_id}")
        self.drawRightString(w - 20 * mm, y, f"Page {page_num} of {total_pages}")
        self.drawCentredString(w / 2, y, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        # Bottom line
        self.setStrokeColor(BRAND_ACCENT)
        self.setLineWidth(1)
        self.line(20 * mm, y + 4 * mm, w - 20 * mm, y + 4 * mm)
        self.restoreState()


def _make_metric_table(metrics: list, styles) -> Table:
    """Build a compact metrics card row from list of (label, value, badge) tuples."""
    cells = []
    for label, value, badge in metrics:
        cell_content = [
            Paragraph(label, styles["MetricLabel"]),
            Paragraph(str(value), styles["MetricValue"]),
        ]
        if badge:
            cell_content.append(Paragraph(badge, styles["Badge"]))
        cells.append(cell_content)

    # Build a single-row table with one column per metric
    data = [cells]
    col_width = (A4[0] - 40 * mm) / len(cells)
    t = Table(data, colWidths=[col_width] * len(cells))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_ACCENT),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def _make_data_table(headers: list, rows: list) -> Table:
    """Build a nicely formatted data table."""
    data = [headers] + rows
    t = Table(data, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor("#cccccc")),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    # Alternate row backgrounds
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), BRAND_TABLE_ROW_ALT))
    t.setStyle(TableStyle(style_cmds))
    return t


def _fmt_usd(val: float) -> str:
    return f"${val:,.0f}"


def _fmt_pct(val: float) -> str:
    return f"{val:.1f}%"


def _bounded_str(bv, fmt_fn=str) -> str:
    return f"{fmt_fn(bv.central_estimate)} ({fmt_fn(bv.lower_bound)} – {fmt_fn(bv.upper_bound)})"


class ReportEngine:
    """
    Generates investor-grade PDF reports from MasterDPIOutput.

    Usage:
        engine = ReportEngine()
        result = engine.generate_prospectus_pdf(dpi_output)
        # result = {"file_path": "...", "file_name": "...", "file_size": 12345, "report_id": "..."}
    """

    def generate_prospectus_pdf(
        self,
        dpi_output: MasterDPIOutput,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Primary entry point. Generates a PDF from a MasterDPIOutput and saves it.

        Returns:
            dict with file_path, file_name, file_size, report_id
        """
        report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
        zone = dpi_output.zone_id
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        file_name = f"{zone}_prospectus_{timestamp}.pdf"

        target_dir = Path(output_dir) if output_dir else REPORTS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / file_name

        try:
            pdf_bytes = self._build_pdf(dpi_output, report_id)
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)

            file_size = os.path.getsize(file_path)
            logger.info(f"Report generated: {file_path} ({file_size} bytes)")

            return {
                "file_path": str(file_path),
                "file_name": file_name,
                "file_size": file_size,
                "report_id": report_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.error(f"PDF generation failed: {exc}")
            # Step 6 — Fallback to JSON export
            json_name = file_name.replace(".pdf", ".json")
            json_path = target_dir / json_name
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(dpi_output.model_dump_json(indent=2))
            file_size = os.path.getsize(json_path)
            return {
                "file_path": str(json_path),
                "file_name": json_name,
                "file_size": file_size,
                "report_id": report_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "fallback": True,
                "error": str(exc),
            }

    def generate_prospectus_bytes(
        self,
        dpi_output: MasterDPIOutput,
    ) -> bytes:
        """Generate and return raw PDF bytes (for streaming responses)."""
        report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
        return self._build_pdf(dpi_output, report_id)

    # ------------------------------------------------------------------
    # Internal PDF builder
    # ------------------------------------------------------------------

    def _build_pdf(self, output: MasterDPIOutput, report_id: str) -> bytes:
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            topMargin=25 * mm,
            bottomMargin=30 * mm,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            title=f"Kulima OS Demand-Signal Prospectus — {output.zone_id}",
            author="Kulima OS DPI Engine",
        )

        styles = _build_styles()
        story = []

        # ------- COVER / HEADER -------
        story.append(Paragraph("KULIMA OS", styles["ProspectusTitle"]))
        story.append(Paragraph(
            f"Demand-Signal Prospectus — Zone: {output.zone_id}",
            styles["SectionHeading"]
        ))
        story.append(Paragraph(
            f"Report ID: {report_id} &nbsp;|&nbsp; "
            f"Generated: {datetime.now(timezone.utc).strftime('%d %B %Y, %H:%M UTC')} &nbsp;|&nbsp; "
            f"System: Kulima OS DPI v2.0",
            styles["ProspectusSubtitle"]
        ))
        story.append(HRFlowable(
            width="100%", thickness=2, color=BRAND_ACCENT, spaceAfter=6 * mm
        ))

        # ------- DATA SUFFICIENCY STATUS -------
        suff = output.data_sufficiency
        if not suff.is_sufficient:
            story.append(Paragraph("⚠ DATA SUFFICIENCY: INSUFFICIENT", styles["SectionHeading"]))
            story.append(Paragraph(
                f"The system has determined that available data is <b>insufficient</b> to produce "
                f"a defensible prospectus. {suff.reasoning}",
                styles["WarningText"]
            ))
            story.append(Paragraph(
                "No financial modeling, gap analysis, or investment recommendations have been generated. "
                "Additional coordination signals are required before this zone can be assessed.",
                styles["BodyText2"]
            ))
            # Build minimal PDF
            doc.build(story, canvasmaker=lambda *a, **kw: _WatermarkCanvas(*a, report_id=report_id, **kw))
            return buf.getvalue()

        # ------- SECTION 1: EXECUTIVE SUMMARY -------
        story.append(Paragraph("1. Executive Summary", styles["SectionHeading"]))

        trust = output.trust
        decision = output.decision
        financial = output.financial

        # Hero metrics row
        base = financial.scenarios.base_case if financial else None
        hero_metrics = [
            ("TRUST SCORE", f"{trust.trust_score}%", f"ZENTARI — {trust.confidence_band}"),
            ("RECOMMENDATION", decision.recommendation, f"Readiness: {decision.readiness_score}%"),
            ("CAPEX (BASE)", _fmt_usd(base.capex_estimate_usd) if base else "N/A",
             f"Payback: {base.payback_period_months:.0f} mo" if base else ""),
        ]
        story.append(_make_metric_table(hero_metrics, styles))
        story.append(Spacer(1, 4 * mm))

        story.append(Paragraph(
            f"Zone <b>{output.zone_id}</b> was evaluated using {trust.validation_evidence.supporting_sources} "
            f"independent coordination sources across {trust.validation_evidence.repetition_count} temporal cycles. "
            f"The system achieved a trust score of <b>{trust.trust_score}%</b> "
            f"({trust.confidence_band}), with a margin of error of "
            f"±{trust.confidence_bound.margin_of_error}%.",
            styles["BodyText2"]
        ))

        # ------- SECTION 2: DEMAND INTELLIGENCE (LUMOZA) -------
        story.append(Paragraph("2. Demand Intelligence — LUMOZA Cluster Analysis", styles["SectionHeading"]))
        cluster = output.cluster
        story.append(_make_data_table(
            ["Metric", "Central Estimate", "Range (Lower – Upper)", "Margin of Error"],
            [
                ["Estimated Participants", str(cluster.estimated_participants.central_estimate),
                 f"{cluster.estimated_participants.lower_bound} – {cluster.estimated_participants.upper_bound}",
                 _fmt_pct(cluster.estimated_participants.margin_of_error)],
                ["Output Value (USD/yr)", _fmt_usd(cluster.output_value_estimate_usd.central_estimate),
                 f"{_fmt_usd(cluster.output_value_estimate_usd.lower_bound)} – {_fmt_usd(cluster.output_value_estimate_usd.upper_bound)}",
                 _fmt_pct(cluster.output_value_estimate_usd.margin_of_error)],
                ["Stability Index", f"{cluster.stability_index.central_estimate:.2f}",
                 f"{cluster.stability_index.lower_bound:.2f} – {cluster.stability_index.upper_bound:.2f}",
                 _fmt_pct(cluster.stability_index.margin_of_error)],
            ]
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f"Dominant productive activity: <b>{cluster.activity_concentration}</b>. "
            f"Demand frequency: <b>{cluster.demand_frequency}</b>.",
            styles["BodyText2"]
        ))

        # ------- SECTION 3: INFRASTRUCTURE GAPS (LUNDAI) -------
        story.append(Paragraph("3. Infrastructure Gap Analysis — LUNDAI", styles["SectionHeading"]))
        gap = output.gap
        story.append(_make_data_table(
            ["Metric", "Central Estimate", "Range", "MoE"],
            [
                ["Gap Type", gap.gap_type.upper(), "—", "—"],
                ["Severity", f"{gap.severity_score.central_estimate:.1f}/10",
                 f"{gap.severity_score.lower_bound:.1f} – {gap.severity_score.upper_bound:.1f}",
                 _fmt_pct(gap.severity_score.margin_of_error)],
                ["Population Affected", str(gap.population_affected.central_estimate),
                 f"{gap.population_affected.lower_bound} – {gap.population_affected.upper_bound}",
                 _fmt_pct(gap.population_affected.margin_of_error)],
                ["Economic Loss (USD/yr)", _fmt_usd(gap.economic_loss_estimate_usd.central_estimate),
                 f"{_fmt_usd(gap.economic_loss_estimate_usd.lower_bound)} – {_fmt_usd(gap.economic_loss_estimate_usd.upper_bound)}",
                 _fmt_pct(gap.economic_loss_estimate_usd.margin_of_error)],
                ["Urgency", gap.urgency_index.upper(), "—", "—"],
            ]
        ))

        # ------- SECTION 4: TRUST & VALIDATION (ZENTARI) -------
        story.append(Paragraph("4. Trust &amp; Validation — ZENTARI 2.0", styles["SectionHeading"]))
        ev = trust.validation_evidence
        story.append(_make_data_table(
            ["Dimension", "Value"],
            [
                ["Supporting Sources", str(ev.supporting_sources)],
                ["Repetition Cycles", str(ev.repetition_count)],
                ["Geographic Density", f"{ev.geographic_density:.2f}"],
                ["Cross-Checks Passed", str(ev.cross_checks_passed)],
                ["Anomaly Score", _fmt_pct(trust.adversarial_detection.anomaly_score)],
                ["Fraud Risk Flag", "YES" if trust.adversarial_detection.fraud_risk_flag else "NO"],
                ["Trust Penalty Applied", str(trust.adversarial_detection.trust_penalty)],
            ]
        ))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("Explainability:", styles["SubSectionHeading"]))
        for line in trust.explainability:
            story.append(Paragraph(f"• {line}", styles["BodyText2"]))

        # ------- SECTION 5: FINANCIAL MODELING -------
        story.append(Paragraph("5. Financial Modeling — Scenario Analysis", styles["SectionHeading"]))
        scenarios = financial.scenarios
        story.append(_make_data_table(
            ["Metric", "Base Case", "Optimistic", "Pessimistic"],
            [
                ["CAPEX (USD)",
                 _fmt_usd(scenarios.base_case.capex_estimate_usd),
                 _fmt_usd(scenarios.optimistic_case.capex_estimate_usd),
                 _fmt_usd(scenarios.pessimistic_case.capex_estimate_usd)],
                ["OPEX/mo (USD)",
                 _fmt_usd(scenarios.base_case.opex_monthly_usd),
                 _fmt_usd(scenarios.optimistic_case.opex_monthly_usd),
                 _fmt_usd(scenarios.pessimistic_case.opex_monthly_usd)],
                ["Revenue/mo (USD)",
                 _fmt_usd(scenarios.base_case.revenue_projection_monthly_usd),
                 _fmt_usd(scenarios.optimistic_case.revenue_projection_monthly_usd),
                 _fmt_usd(scenarios.pessimistic_case.revenue_projection_monthly_usd)],
                ["Payback (Months)",
                 f"{scenarios.base_case.payback_period_months:.0f}",
                 f"{scenarios.optimistic_case.payback_period_months:.0f}",
                 f"{scenarios.pessimistic_case.payback_period_months:.0f}"],
                ["IRR",
                 _fmt_pct(scenarios.base_case.irr),
                 _fmt_pct(scenarios.optimistic_case.irr),
                 _fmt_pct(scenarios.pessimistic_case.irr)],
            ]
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f"Breakeven users: <b>{_bounded_str(financial.breakeven_users)}</b> "
            f"(±{financial.breakeven_users.margin_of_error:.1f}%). "
            f"Pricing model: <b>{financial.pricing_model}</b>.",
            styles["BodyText2"]
        ))

        # ------- SECTION 6: RISK ASSESSMENT -------
        story.append(Paragraph("6. Risk Assessment", styles["SectionHeading"]))
        risk = output.risk
        story.append(Paragraph(
            f"Risk Score: <b>{risk.risk_score}/100</b> ({risk.category})",
            styles["BodyText2"]
        ))
        story.append(Paragraph(f"Mitigation: {risk.mitigation_plan}", styles["BodyText2"]))
        if risk.regulatory_flags:
            story.append(Paragraph(
                f"Regulatory Flags: {', '.join(risk.regulatory_flags)}",
                styles["BodyText2"]
            ))

        # ------- SECTION 7: INVESTMENT DECISION -------
        story.append(Paragraph("7. Investment Decision", styles["SectionHeading"]))
        dec = output.decision
        story.append(_make_metric_table([
            ("INVESTMENT REQUIRED", _bounded_str(dec.total_investment_required_usd, _fmt_usd), ""),
            ("PROJECTED IRR", _bounded_str(dec.projected_return_irr, _fmt_pct), ""),
            ("RISK PROFILE", dec.risk_profile.upper(), ""),
        ], styles))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            f"<b>Recommendation: {dec.recommendation}</b> (Readiness Score: {dec.readiness_score}%)",
            styles["BodyText2"]
        ))

        # Why Not Analysis
        story.append(Paragraph("Why This May Be Wrong:", styles["SubSectionHeading"]))
        wn = dec.why_not_analysis
        all_items = (
            [(r, "Reason") for r in wn.reasons_this_may_be_wrong]
            + [(d, "Data Limitation") for d in wn.data_limitations]
            + [(u, "Uncertainty") for u in wn.uncertainty_factors]
            + [(b, "Known Bias") for b in wn.known_biases]
        )
        if all_items:
            for item, cat in all_items:
                story.append(Paragraph(f"• [{cat}] {item}", styles["BodyText2"]))
        else:
            story.append(Paragraph("• No significant caveats identified.", styles["BodyText2"]))

        # ------- SECTION 8: IMPLEMENTATION PLAN -------
        story.append(Paragraph("8. Implementation Plan", styles["SectionHeading"]))
        impl = output.implementation
        story.append(Paragraph(
            f"Ownership: <b>{impl.ownership_model}</b> | "
            f"Operator: <b>{impl.operator_type}</b> | "
            f"Funding: <b>{impl.funding_strategy}</b>",
            styles["BodyText2"]
        ))
        for step in impl.deployment_steps:
            story.append(Paragraph(f"→ {step}", styles["BodyText2"]))

        # ------- SECTION 9: SOCIAL RESERVE POLICY -------
        story.append(Paragraph("9. Social Reserve Policy", styles["SectionHeading"]))
        story.append(Paragraph(
            "<b>20% Protected Capacity:</b> Reserved exclusively for critical communal services "
            "(clinics, schools, water systems, emergency infrastructure) to ensure infrastructure "
            "serves the collective economic baseline without extraction. This reserve is "
            "non-negotiable and cannot be overridden by commercial optimization.",
            styles["BodyText2"]
        ))

        # ------- SECTION 10: SYSTEM TRUST DECLARATION -------
        if output.trust_declaration:
            story.append(Paragraph("10. System Trust Declaration", styles["SectionHeading"]))
            td = output.trust_declaration
            story.append(_make_data_table(
                ["Declaration", "Value"],
                [
                    ["Confidence Level", _fmt_pct(td.confidence_level)],
                    ["Data Sufficiency", "PASSED" if td.data_sufficiency_status.is_sufficient else "FAILED"],
                    ["Validation Depth", td.validation_depth],
                    ["Fraud Risk Level", td.fraud_risk_level.upper()],
                    ["Audit Trace Available", "YES" if td.audit_trace_available else "NO"],
                ]
            ))

        # ------- SYSTEM SELF-ASSESSMENT -------
        if output.system_assessment:
            story.append(Paragraph("System Self-Assessment", styles["SubSectionHeading"]))
            sa = output.system_assessment
            story.append(Paragraph(f"System Confidence: <b>{sa.system_confidence_score:.1f}%</b>", styles["BodyText2"]))
            story.append(Paragraph(f"Weakest Layer: {sa.weakest_layer_identified}", styles["BodyText2"]))
            story.append(Paragraph(f"Reliability: {sa.reliability_summary}", styles["BodyText2"]))
            story.append(Paragraph(f"Next Improvement: {sa.recommended_next_improvement}", styles["BodyText2"]))

        # ------- AUDIT TRACE -------
        if output.audit:
            story.append(Paragraph("Audit &amp; Traceability", styles["SubSectionHeading"]))
            story.append(Paragraph(f"Trace ID: <b>{output.audit.trace_id}</b>", styles["BodyText2"]))
            story.append(Paragraph(f"Logic: {output.audit.logic_explanation}", styles["BodyText2"]))
            story.append(Paragraph(f"Inputs Hash: <font size=7>{output.audit.inputs_hashed}</font>", styles["BodyText2"]))

        # ------- LEGAL FOOTER -------
        story.append(Spacer(1, 10 * mm))
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND_MUTED, spaceAfter=4 * mm))
        story.append(Paragraph(
            "This document was generated by Kulima OS, a coordination-first Digital Public Infrastructure system. "
            "All data is identity-free (Zero-PII). Trust scores are derived from collective coordination patterns, "
            "not individual behaviors. This is a pilot-system output and should be reviewed alongside field verification.",
            styles["FooterText"]
        ))
        story.append(Paragraph(
            f"Kulima OS — Digital Public Infrastructure Intelligence &nbsp;|&nbsp; Report {report_id}",
            styles["FooterText"]
        ))

        # Build with watermark canvas
        doc.build(
            story,
            canvasmaker=lambda *a, **kw: _WatermarkCanvas(*a, report_id=report_id, **kw)
        )
        return buf.getvalue()
