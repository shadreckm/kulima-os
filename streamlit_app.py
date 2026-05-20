"""
Kulima OS – Institutional Demand Signal Interface (Streamlit)

Live view: community signals → coordination → prospectus.
Run: streamlit run streamlit_app.py
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import streamlit as st

def coordination_strength_color(score: int) -> str:
    if score >= 70:
        return "#2E7D32"   # green
    elif score >= 40:
        return "#F57C00"   # orange
    return "#D32F2F"       # red

from coordination_accumulation import (
    CYCLE_WINDOW_DAYS,
    compute_coordination_trend,
)
from lumoza_integration import integrate_whatsapp_to_lumoza
from pilot_mode import generate_pilot_report
from prospectus_generator import ProspectusGenerator
from signal_storage import Signal, default_storage
from zone_utils import normalize_zone

PILOT_ZONES = ["MZUZU", "EKWENDENI", "KARONGA"]
ARTIFACTS_ROOT = Path(__file__).resolve().parent / "artifacts"


def load_all_signals() -> List[Signal]:
    """Load every signal from the live storage backend."""
    return default_storage.get_all_signals()


def filter_signals_by_zone(signals: List[Signal], zone: str) -> List[Signal]:
    """Keep only signals for the selected pilot zone."""
    zone_key = normalize_zone(zone)
    return [s for s in signals if normalize_zone(s.zone) == zone_key]


def build_zone_signal_timeline(zone: str, days: int = 14) -> List[dict]:
    """Build a recent signal accumulation timeline for the selected zone."""
    zone_key = normalize_zone(zone)
    signals = [s for s in load_all_signals() if normalize_zone(s.zone) == zone_key and s.timestamp]
    counts: Counter = Counter()
    for signal in signals:
        try:
            date_obj = datetime.fromisoformat(signal.timestamp.replace("Z", "+00:00")).date()
            counts[date_obj] += 1
        except Exception:
            continue

    today = datetime.now(timezone.utc).date()
    date_series = [today - timedelta(days=i) for i in reversed(range(days))]
    return [{"date": day.isoformat(), "signals": counts.get(day, 0)} for day in date_series]


def build_coordination_summary(zone: str) -> dict:
    """
    Real coordination state from the validated pipeline.
    Uses the LUMOZA → LUNDAI → ZENTARI integration path so dashboard metrics
    reflect validated, institution-ready outputs only.
    """
    zone_key = normalize_zone(zone)
    summary = integrate_whatsapp_to_lumoza(zone=zone_key)
    patterns = summary.get("patterns", [])
    lundai_overall = summary.get("lundai_analysis", {}).get("overall_assessment", {})

    score = 15
    if patterns:
        confidences = [p.get("coordination_confidence") for p in patterns if isinstance(p.get("coordination_confidence"), (int, float))]
        if confidences:
            score = int(round(min(max(sum(confidences) / len(confidences) * 100, 15), 100)))

    strength_label = "Weak"
    if score >= 70:
        strength_label = "Strong"
    elif score >= 40:
        strength_label = "Emerging"

    return {
        "zone": zone_key,
        "total_signals": summary.get("raw_signal_count", 0),
        "validated_signals": summary.get("validated_signal_count", 0),
        "signal_count": summary.get("validated_signal_count", 0),
        "pattern_count": len(patterns),
        "coordination_trend": summary.get("coordination_trend", "Emerging"),
        "coordination_score": score,
        "coordination_strength_label": strength_label,
        "window_days": summary.get("window_days", CYCLE_WINDOW_DAYS),
        "high_confidence_patterns": sum(1 for p in patterns if p.get("confidence_class") == "high"),
        "lundai_status": lundai_overall.get("overall_infrastructure_status", "Unknown"),
        "planning_reserve": summary.get("planning_reserve", {}).get("usable_signals", 0),
        "pattern_explanations": [
            p.get('explanation', {}).get('human_readable', '')
            if isinstance(p.get('explanation'), dict)
            else p.get('explanation', '')
            for p in patterns
        ],
    }


def patterns_to_confidence_results(patterns: list) -> list:
    """Normalize patterns for prospectus generation."""
    results = []
    for pattern in patterns:
        if pattern.get("confidence_class") and pattern.get("coordination_confidence") is not None:
            results.append(pattern)
            continue

        results.append({
            "activity_type": pattern["activity_type"],
            "zone": pattern["zone"],
            "time_window": pattern["demand_rhythm"]["time_window"],
            "confidence_class": pattern.get("confidence_class", "moderate"),
            "stability_score": pattern.get("coordination_confidence", 0.7),
            "demand_rhythm": {
                "frequency": pattern["demand_rhythm"]["frequency"],
                "stability_class": pattern["demand_rhythm"]["stability_class"],
            },
            "coordination_confidence": pattern.get("coordination_confidence", 0.7),
            "validation_strength": pattern.get("validation_strength", "human_only"),
            "validation_details": pattern.get("validation_details", ""),
            "bankability_note": pattern.get("bankability_note", ""),
        })
    return results


def generate_zone_prospectus(zone: str) -> Tuple[Optional[Path], str]:
    """Generate the PDF/JSON prospectus for a zone."""
    zone_key = normalize_zone(zone)
    summary = integrate_whatsapp_to_lumoza(zone=zone_key)
    patterns = summary.get("patterns", [])
    lundai_analysis = summary.get("lundai_analysis", {})

    if not patterns:
        return None, (
            f"Coordination activity detected, but validated patterns are not yet stable for infrastructure planning in {zone_key}. "
            f"({summary.get('validated_signal_count', 0)} validated signal(s) in the {CYCLE_WINDOW_DAYS}-day window)."
        )

    try:
        gen = ProspectusGenerator()
        metadata = {"region": zone_key, "period": f"{CYCLE_WINDOW_DAYS}-cycle window (1 week)"}
        planning_reserve = summary.get("planning_reserve")
        
        if planning_reserve is None:
            from policy import compute_planning_reserve
            planning_reserve = compute_planning_reserve(len(patterns))
        
        prospectus = gen.generate_prospectus(
            patterns_to_confidence_results(patterns),
            lundai_analysis=lundai_analysis,
            metadata=metadata,
            planning_reserve=planning_reserve,
        )

        timestamp = datetime.utcnow().isoformat().replace(":", "-")
        artifacts_dir = ARTIFACTS_ROOT / zone_key.lower() / timestamp
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = artifacts_dir / f"demand_prospectus_{zone_key.lower()}_{timestamp}.pdf"
        gen.generate_pdf(prospectus, str(pdf_path))

        json_path = artifacts_dir / f"demand_prospectus_{zone_key.lower()}_{timestamp}.json"
        json_path.write_text(json.dumps(prospectus, indent=2), encoding="utf-8")

        return pdf_path, f"Prospectus generated ({len(patterns)} pattern(s))."
    except Exception as e:
        return None, f"Error generating prospectus: {str(e)}"


def build_pilot_insights() -> dict:
    """Build dashboard insights from the pilot evidence log."""
    report = generate_pilot_report()
    daily = report.get("daily_summary", {})
    latest = report.get("recent_log_entries", [])
    return {
        "pilot_mode": report.get("pilot_mode", False),
        "entry_count": daily.get("entry_count", 0),
        "validated_entries": daily.get("validated_entries", 0),
        "rejected_entries": daily.get("rejected_entries", 0),
        "coordination_strength": daily.get("coordination_strength", "Emerging"),
        "activity_counts": daily.get("activity_counts", {}),
        "trust_distribution": daily.get("trust_distribution", {}),
        "top_infrastructure_notes": daily.get("top_infrastructure_notes", []),
        "latest_entries": latest[-5:],
    }


def interpret_coordination_trend(trend: str) -> str:
    normalized = str(trend).strip().lower()
    interpretations = {
        "emerging": "Early activity detected — more signals are needed to confirm demand.",
        "growing": "Increasing coordination suggests a potential demand pattern is forming.",
        "strong": "Consistent coordination pattern — planning-grade signal available.",
    }
    return interpretations.get(normalized, "Stable coordination status based on current signals.")


def main() -> None:
    st.set_page_config(
        page_title="Kulima OS — Coordination Intelligence",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get help': None,
            'Report a bug': None,
            'About': 'Kulima OS is a coordination-first economic substrate designed as Digital Public Infrastructure (DPI) for infrastructure planning.',
        },
    )

    logo_path = Path(__file__).resolve().parent / "assets" / "kulima_africa_logo.png"
    cols = st.columns([1, 4])
    with cols[0]:
        if logo_path.is_file():
            st.image(str(logo_path), width=96)
    with cols[1]:
        st.title("Kulima OS")
        st.subheader("Digital Public Infrastructure (DPI) for Infrastructure Planning")
        st.caption("Verifying collective demand rhythms and coordination patterns to derisk infrastructure deployment without extraction or surveillance.")

    st.divider()

    with st.container():
        st.header("1. System Architecture & Digital Public Infrastructure (DPI)")
        st.write(
            "Kulima OS is a coordination-first economic substrate designed to convert decentralized livelihood activity "
            "into verified, bankable coordination signals for infrastructure planning. By mapping temporal demand rhythms "
            "without extracting or profiling individual behaviors, the platform provides institutional decision-makers "
            "with high-fidelity evidence of productive-use energy demand before capital is deployed."
        )
        
        overview_cols = st.columns(3)
        with overview_cols[0]:
            with st.container():
                st.subheader("LUMOZA Engine")
                st.markdown("**Temporal Coordination**")
                st.caption(
                    "Aggregates identity-free livelihood signals (irrigation, milling, cold storage) into "
                    "7-cycle batched windows to verify collective rhythms and patterns while preserving the temporal moat."
                )
        with overview_cols[1]:
            with st.container():
                st.subheader("LUNDAI Engine")
                st.markdown("**Infrastructure Geometry**")
                st.caption(
                    "Analyzes settlement density patterns, asset distributions, and distance-to-service metrics "
                    "to identify geometric mismatches where coordinated demand exists but infrastructure is absent."
                )
        with overview_cols[2]:
            with st.container():
                st.subheader("ZENTARI Engine")
                st.markdown("**Coordination Confidence**")
                st.caption(
                    "Derives trust from the persistence, repetition, and resilience of coordination patterns over "
                    "multiple observation periods, substituting credit scoring with collective pattern bankability."
                )

    st.divider()

    st.header("2. Livelihood Coordination & Temporal Demand Analysis")
    st.write(
        "Quantitative assessment of temporal coordination stability, planning reserve allocations, "
        "and infrastructure status for the selected observation area."
    )

    if "selected_zone" not in st.session_state:
        st.session_state.selected_zone = PILOT_ZONES[0]

    pill_cols = st.columns(len(PILOT_ZONES))
    for idx, zone_name in enumerate(PILOT_ZONES):
        if pill_cols[idx].button(zone_name, key=f"zone_{zone_name}"):
            st.session_state.selected_zone = zone_name

    selected_zone = st.session_state.selected_zone
    summary = build_coordination_summary(selected_zone)

    # Professional wording upgrade for KPIs
    coordination_score_val = summary.get("coordination_score", 15)
    validated_signals_count = summary.get("validated_signals", 0)
    
    if validated_signals_count == 0:
        validated_signals_val = "0"
        validated_signals_note = "No validated coordination signals detected within the current observation window."
    else:
        validated_signals_val = str(validated_signals_count)
        validated_signals_note = f"{validated_signals_count} validated coordination signal(s) successfully verified within the current 7-cycle window."

    kpi_cards = [
        {
            "label": "Coordination Trend Assessment",
            "value": summary.get("coordination_trend", "Emerging"),
            "note": f"Current coordination pattern classification for the {selected_zone.upper()} observation zone.",
            "score": coordination_score_val,
            "strength_label": summary.get("coordination_strength_label", "Weak"),
            "strength_color": coordination_strength_color(coordination_score_val),
        },
        {
            "label": "Validated Coordination Signals",
            "value": validated_signals_val,
            "note": validated_signals_note,
        },
        {
            "label": "Social Reserve Allocation",
            "value": f"{summary.get('planning_reserve', 0)} Units" if summary.get('planning_reserve') else "0 Units",
            "note": "Non-negotiable energy capacity reserved for critical communal services (clinics, schools, water systems) before productive allocation.",
        },
        {
            "label": "Infrastructure Adequacy Class",
            "value": summary.get("lundai_status", "Unknown"),
            "note": "LUNDAI-derived settlement context and grid adequacy classification.",
        },
    ]

    kpi_cols = st.columns(len(kpi_cards))
    for idx, card in enumerate(kpi_cards):
        with kpi_cols[idx]:
            with st.container():
                st.metric(label=card["label"], value=str(card["value"]))
                if card.get("score") is not None:
                    st.progress(card["score"] / 100.0)
                    st.caption(f"{card['strength_label']} — {card['score']}% coordination strength")
                st.caption(card["note"])

    timeline = build_zone_signal_timeline(selected_zone)
    if timeline:
        with st.container():
            st.subheader("2.1 Signal Accumulation Timeline")
            st.caption("Recent chronological aggregation of raw coordination signals across the active observation window.")
            st.line_chart(
                {"Signals": [point["signals"] for point in timeline]},
                use_container_width=True,
            )

    st.divider()

    st.header("3. Institutional Reporting & Investment Prospectus Generator")
    st.write(
        "Formulate a bankable Demand-Signal Prospectus incorporating temporal coordination rhythms, "
        "LUNDAI infrastructure gap assessments, and social reserve parameters."
    )

    with st.container():
        st.subheader("Generate Verified Demand Signal Prospectus")
        st.write(
            "Deliver an audited Demand-Signal Prospectus packaging coordination patterns, spatial context, "
            "and social reserve requirements into an institutional artifact ready for development finance evaluation."
        )
        if st.button("Generate Verified Demand Signal Prospectus", key="generate_prospectus", help="Create the latest verified planning prospectus", use_container_width=False):
            with st.spinner("Generating verified demand signal prospectus..."):
                new_pdf, message = generate_zone_prospectus(selected_zone)
            if new_pdf and new_pdf.is_file():
                st.success("Verified demand signal prospectus generated successfully.")
                with open(new_pdf, "rb") as pdf_file:
                    st.download_button(
                        label="Download Demand Signal Prospectus",
                        data=pdf_file.read(),
                        file_name="demand_prospectus.pdf",
                        mime="application/pdf",
                        use_container_width=False,
                        key=f"download_new_{summary.get('zone', selected_zone)}",
                    )
            else:
                st.warning(message)

    st.divider()

    st.header("4. Decentralized Signal Acquisition & Onboarding Protocol")
    st.write(
        "Operational procedures to activate decentralized, privacy-preserving livelihood signal telemetry "
        "through standard messaging channels."
    )
    
    with st.container():
        st.subheader("Join the System")
        st.info(
            "**Step 1 (Channel Activation):** Save the Kulima OS WhatsApp gatekeeper number: **+1 415 523 8886**\n\n"
            "**Step 2 (Session Handshake):** Open WhatsApp and transmit the verification token: **join week-saved**\n\n"
            "**Step 3 (Livelihood Telemetry):** Transmit real activity updates using clear, identity-free descriptions, e.g.:\n"
            "- *\"I am irrigating crops\"*\n"
            "- *\"We are milling maize\"*\n"
            "- *\"Selling tomatoes today\"*\n\n"
            "**Step 4 (Coordination Persistence):** Continue transmitting updates consistently. Consistent repetition across weekly cycles confirms coordination confidence."
        )

    st.caption("Kulima Africa — Coordination Intelligence Infrastructure • Public Digital System • [GitHub Repository](https://github.com/shadreckm/kulima-os)")


if __name__ == "__main__":
    main()