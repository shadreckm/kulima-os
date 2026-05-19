"""
Kulima OS – Institutional Demand Signal Interface (Streamlit)

Live view: community signals → coordination → prospectus.
Run: streamlit run streamlit_app.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import streamlit as st

from coordination_accumulation import (
    CYCLE_WINDOW_DAYS,
    compute_coordination_patterns,
    compute_coordination_trend,
    get_zone_window_signals,
)
from lumoza_integration import integrate_whatsapp_to_lumoza
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

    return {
        "zone": zone_key,
        "total_signals": summary.get("raw_signal_count", 0),
        "validated_signals": summary.get("validated_signal_count", 0),
        "signal_count": summary.get("validated_signal_count", 0),
        "pattern_count": len(patterns),
        "coordination_trend": summary.get("coordination_trend", "Emerging"),
        "window_days": summary.get("window_days", CYCLE_WINDOW_DAYS),
        "high_confidence_patterns": sum(1 for p in patterns if p.get("confidence_class") == "high"),
        "lundai_status": lundai_overall.get("overall_infrastructure_status", "Unknown"),
        "planning_reserve": summary.get("planning_reserve", {}).get("usable_signals", 0),
        "pattern_explanations": [p.get('explanation', {}).get('human_readable', '') for p in patterns],
    }


def latest_pdf_path(zone: str) -> Optional[Path]:
    """Scan artifacts/<zone>/ for the newest timestamp folder and its PDF."""
    zone_dir = ARTIFACTS_ROOT / normalize_zone(zone).lower()
    if not zone_dir.is_dir():
        return None

    subdirs = sorted(
        (d for d in zone_dir.iterdir() if d.is_dir()),
        key=lambda p: p.name,
        reverse=True,
    )
    for folder in subdirs:
        pdfs = list(folder.glob("*.pdf"))
        if pdfs:
            return max(pdfs, key=lambda p: p.stat().st_mtime)
    return None


def patterns_to_confidence_results(patterns: list) -> list:
    """Normalize patterns for prospectus generation.

    If the pipeline has already produced ZENTARI outputs, keep them intact.
    """
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
    """
    1. integrate_whatsapp_to_lumoza(zone)
    2. ProspectusGenerator.generate_prospectus + generate_pdf
    3. Save under artifacts/<zone>/<timestamp>/
    """
    zone_key = normalize_zone(zone)
    summary = integrate_whatsapp_to_lumoza(zone=zone_key)
    patterns = summary.get("patterns", [])
    lundai_analysis = summary.get("lundai_analysis", {})

    if not patterns:
        return None, (
            f"Coordination activity detected, but validated patterns are not yet stable for infrastructure planning in {zone_key}. "
            f"({summary.get('validated_signal_count', 0)} validated signal(s) in the {CYCLE_WINDOW_DAYS}-day window)."
        )

    gen = ProspectusGenerator()
    metadata = {"region": zone_key, "period": f"{CYCLE_WINDOW_DAYS}-cycle window (1 week)"}
    prospectus = gen.generate_prospectus(
        patterns_to_confidence_results(patterns),
        lundai_analysis=lundai_analysis,
        metadata=metadata,
        planning_reserve=summary.get("planning_reserve"),
    )

    timestamp = datetime.utcnow().isoformat().replace(":", "-")
    artifacts_dir = ARTIFACTS_ROOT / zone_key.lower() / timestamp
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = artifacts_dir / f"demand_prospectus_{zone_key.lower()}_{timestamp}.pdf"
    gen.generate_pdf(prospectus, str(pdf_path))

    json_path = artifacts_dir / f"demand_prospectus_{zone_key.lower()}_{timestamp}.json"
    json_path.write_text(json.dumps(prospectus, indent=2), encoding="utf-8")

    return pdf_path, f"Prospectus generated ({len(patterns)} pattern(s))."


def interpret_coordination_trend(trend: str) -> str:
    normalized = str(trend).strip().lower()
    interpretations = {
        "emerging": "Early activity detected — more signals are needed to confirm demand.",
        "growing": "Increasing coordination suggests a potential demand pattern is forming.",
        "strong": "Consistent coordination pattern — planning-grade signal available.",
    }
    return interpretations.get(normalized, "Stable coordination status based on current signals.")


def main() -> None:
    st.set_page_config(page_title="Kulima OS — Demand Signal Interface", layout="wide")

    st.markdown(
        """
        <style>
        div.block-container {
            padding: 2.5rem 2.5rem 3rem;
            max-width: 1180px;
            margin: auto;
            background: #F8FAFC;
        }
        .hero-block {
            text-align: left;
            padding: 2rem 2rem 2.25rem;
            background: #FFFFFF;
            border-radius: 24px;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
            margin-bottom: 2rem;
        }
        .hero-block h1 {
            margin: 0;
            color: #102A43;
            font-size: 2.75rem;
            letter-spacing: -0.04em;
        }
        .hero-block h2 {
            margin: 0.8rem 0 0;
            color: #102A43;
            font-size: 1.35rem;
            font-weight: 600;
        }
        .hero-block p {
            margin: 1.15rem 0 0;
            color: #334E68;
            font-size: 1rem;
            line-height: 1.8;
            max-width: 780px;
        }
        .section-heading {
            color: #102A43;
            margin: 0;
            font-size: 1.6rem;
            font-weight: 700;
        }
        .section-copy {
            color: #334E68;
            margin: 0.75rem 0 1.5rem;
            line-height: 1.75;
            max-width: 780px;
        }
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .card {
            background: #FFFFFF;
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 18px 35px rgba(15, 23, 42, 0.06);
            min-height: 180px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .card-title {
            margin: 0;
            color: #102A43;
            font-size: 0.85rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            opacity: 0.75;
        }
        .card-value {
            margin: 1rem 0 0;
            color: #102A43;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.05;
        }
        .card-note {
            margin: 0.75rem 0 0;
            color: #334E68;
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.6;
        }
        .footer-text {
            color: #627D98;
            font-size: 0.95rem;
            line-height: 1.8;
            text-align: center;
            margin-top: 3rem;
        }
        button {
            background: #0F766E !important;
            color: #ffffff !important;
            border-radius: 999px !important;
            border: none !important;
            padding: 0.95rem 1.25rem !important;
            font-weight: 700 !important;
        }
        button:hover {
            background: #115E59 !important;
        }
        button:focus {
            outline: none !important;
            box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.2) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='hero-block'>
            <h1>Kulima OS — Demand Signal Interface</h1>
            <h2>Coordination-based infrastructure intelligence</h2>
            <p>This interface presents conservative, coordination-driven demand insights for planners, energy developers, and funders.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("How this works"):
        st.write(
            "This system translates daily community activity into coordination-based demand signals to support infrastructure planning."
        )

    st.divider()
    st.markdown("<h2 class='section-heading'>Overview</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Select a pilot zone to review the latest coordination state, demand signal readiness, and prospectus access.</p>",
        unsafe_allow_html=True,
    )

    zone = st.radio(
        "Select pilot zone",
        options=PILOT_ZONES,
        horizontal=True,
        label_visibility="collapsed",
    )

    summary = build_coordination_summary(zone)
    st.markdown("<div class='card-grid'>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='card'>
            <p class='card-title'>Selected Zone</p>
            <p class='card-value'>{summary['zone']}</p>
            <p class='card-note'>{'Pilot area under review'}</p>
        </div>
        <div class='card'>
            <p class='card-title'>Validated Signals</p>
            <p class='card-value'>{summary['validated_signals']}</p>
            <p class='card-note'>Signals that passed integrity filtering before planning.</p>
        </div>
        <div class='card'>
            <p class='card-title'>Stable Patterns</p>
            <p class='card-value'>{summary['pattern_count']}</p>
            <p class='card-note'>Verified coordination patterns available for planning review.</p>
        </div>
        <div class='card'>
            <p class='card-title'>Infrastructure Status</p>
            <p class='card-value'>{summary['lundai_status']}</p>
            <p class='card-note'>Zone-level assessment from the LUNDAI context layer.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<h2 class='section-heading'>Coordination Status</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>The current signal trend indicates whether the zone is moving toward planning-grade demand intelligence.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class='card-grid'>
            <div class='card card-primary'>
                <p class='card-title'>Coordination Trend</p>
                <p class='card-value'>{summary['coordination_trend']}</p>
                <p class='card-note'>{interpret_coordination_trend(summary['coordination_trend'])}</p>
            </div>
            <div class='card'>
                <p class='card-title'>Planning Reserve</p>
                <p class='card-value'>{summary['planning_reserve']}</p>
                <p class='card-note'>Usable signal capacity after a 25% conservative reserve.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("<h2 class='section-heading'>Prospectus Access</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Generate or download the latest demand prospectus for this pilot zone.</p>",
        unsafe_allow_html=True,
    )

    pdf_path = latest_pdf_path(zone)
    if pdf_path and pdf_path.is_file():
        st.markdown(
            f"<p class='section-copy'>Latest prospectus: <strong>{pdf_path.parent.name}</strong></p>",
            unsafe_allow_html=True,
        )
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Download Latest Demand Prospectus",
                data=pdf_file.read(),
                file_name="demand_prospectus.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"download_{summary['zone']}",
            )
    else:
        st.info("Coordination activity is present, but planning-grade patterns are still forming.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Generate Prospectus", type="primary", use_container_width=True):
        with st.spinner("Generating demand prospectus..."):
            new_pdf, message = generate_zone_prospectus(zone)

        if new_pdf and new_pdf.is_file():
            st.success("Prospectus generated successfully.")
            with open(new_pdf, "rb") as pdf_file:
                st.download_button(
                    label="Download Demand Prospectus",
                    data=pdf_file.read(),
                    file_name="demand_prospectus.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"download_new_{summary['zone']}",
                )
        else:
            st.warning(message)

    st.divider()
    st.markdown("<h2 class='section-heading'>Notes</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        <p class='section-copy'>The platform is designed for institutional review and conservative planning.</p>
        <ul style='color: #334E68; margin-top: 0.75rem; line-height: 1.8;'>
            <li>Signals are derived from 7-cycle coordination windows.</li>
            <li>Outputs represent conservative lower-bound demand estimates.</li>
            <li>No personal or individual data is collected.</li>
        </ul>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='footer-text'>Kulima Africa | Kulima OS Pilot v0.2<br>Coordination-based Digital Public Infrastructure</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
