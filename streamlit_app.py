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
    Real coordination state from stored signals and LUMOZA 7-cycle logic.
    Reuses coordination_accumulation (no duplicate logic).
    """
    zone_key = normalize_zone(zone)
    all_zone_signals = filter_signals_by_zone(load_all_signals(), zone_key)
    window_signals = get_zone_window_signals(zone_key)
    patterns = compute_coordination_patterns(zone_key)

    return {
        "zone": zone_key,
        "total_signals": len(all_zone_signals),
        "signal_count": len(window_signals),
        "pattern_count": len(patterns),
        "coordination_trend": compute_coordination_trend(zone_key),
        "window_days": CYCLE_WINDOW_DAYS,
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
    """Map LUMOZA integration patterns to prospectus generator input."""
    results = []
    for pattern in patterns:
        results.append({
            "activity_type": pattern["activity_type"],
            "zone": pattern["zone"],
            "time_window": pattern["demand_rhythm"]["time_window"],
            "confidence_class": pattern["confidence_class"],
            "stability_score": pattern.get("coordination_confidence", 0.7),
            "demand_rhythm": {
                "frequency": pattern["demand_rhythm"]["frequency"],
                "stability_class": pattern["demand_rhythm"]["stability_class"],
            },
            "coordination_confidence": pattern["coordination_confidence"],
            "validation_strength": pattern["validation_strength"],
            "validation_details": pattern["validation_details"],
            "bankability_note": pattern["bankability_note"],
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

    if not patterns:
        return None, (
            f"No stable coordination patterns for {zone_key} yet "
            f"({summary.get('signals_in_window', 0)} signal(s) in the "
            f"{CYCLE_WINDOW_DAYS}-day window)."
        )

    gen = ProspectusGenerator()
    metadata = {"region": zone_key, "period": f"{CYCLE_WINDOW_DAYS}-cycle window (1 week)"}
    prospectus = gen.generate_prospectus(
        patterns_to_confidence_results(patterns),
        metadata=metadata,
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
            padding: 1.75rem 2rem 3rem;
            max-width: 1180px;
            margin: auto;
            background: #F8FAFC;
        }
        .title-block {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1.5rem 1.5rem 1rem;
            background: rgba(255, 255, 255, 0.92);
            border-radius: 24px;
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
            margin-bottom: 1.25rem;
        }
        .title-block img {
            border-radius: 18px;
            box-shadow: 0 18px 35px rgba(46, 125, 50, 0.12);
        }
        .title-block h1 {
            margin: 0;
            color: #263238;
            font-size: 3rem;
            letter-spacing: -0.04em;
        }
        .title-block h2 {
            margin: 0.2rem 0 0;
            color: #263238;
            font-size: 1.4rem;
            font-weight: 500;
        }
        .title-block p {
            margin: 0.75rem 0 0;
            color: #4B5563;
            font-size: 1rem;
            line-height: 1.6;
        }
        .section-heading {
            color: #263238;
            margin: 0;
            font-size: 1.45rem;
            font-weight: 700;
        }
        .section-copy {
            color: #4B5563;
            margin-top: 0.5rem;
            margin-bottom: 1rem;
            line-height: 1.75;
            max-width: 820px;
        }
        .section-divider {
            height: 1px;
            background: #E2E8F0;
            margin: 1.5rem 0 2rem;
            border: none;
        }
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-top: 1.25rem;
        }
        .card {
            background: white;
            border-radius: 20px;
            padding: 1.4rem 1.5rem;
            box-shadow: 0 24px 45px rgba(15, 23, 42, 0.08);
            min-height: 150px;
        }
        .card-title {
            margin: 0;
            color: #263238;
            font-size: 0.85rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            opacity: 0.75;
        }
        .card-value {
            margin: 0.8rem 0 0;
            color: #263238;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.05;
        }
        .card-note {
            margin: 0.65rem 0 0;
            color: #2E7D32;
            font-size: 0.95rem;
            font-weight: 600;
        }
        .footer-text {
            color: #64748B;
            font-size: 0.94rem;
            line-height: 1.7;
            text-align: center;
            margin-top: 2.5rem;
        }
        button {
            background: #F57C00 !important;
            color: #ffffff !important;
            border-radius: 999px !important;
            border: none !important;
            padding: 0.95rem 1.25rem !important;
            font-weight: 700 !important;
            box-shadow: 0 18px 40px rgba(245, 124, 0, 0.22) !important;
        }
        button:hover {
            background: #dd6d03 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.image("assets/kulima_africa_logo.png", width=130)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='title-block'>
            <div>
                <h1>Kulima OS</h1>
                <h2>Demand Signal Interface</h2>
                <p>Coordination-based infrastructure intelligence</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<p class='section-copy'>A high-integrity interface for infrastructure planners, development partners, and institutional decision-makers.</p>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider' />", unsafe_allow_html=True)
    st.markdown("<h2 class='section-heading'>Overview</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Select a pilot zone to review live coordination state, demand intelligence, and prospectus delivery.</p>",
        unsafe_allow_html=True,
    )
    zone = st.radio(
        "Select pilot zone",
        options=PILOT_ZONES,
        horizontal=True,
        label_visibility="collapsed",
    )

    summary = build_coordination_summary(zone)

    st.markdown("<hr class='section-divider' />", unsafe_allow_html=True)
    st.markdown("<h2 class='section-heading'>Coordination Status</h2>", unsafe_allow_html=True)

    if summary["total_signals"] == 0:
        st.warning("No validated coordination patterns detected in this zone.")
        st.markdown(
            "<p class='section-copy'>No coordination signals are recorded yet. The platform is ready to aggregate pilot data once it is submitted.</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class='card-grid'>
                <div class='card'>
                    <p class='card-title'>Coordination trend</p>
                    <p class='card-value'>{summary['coordination_trend']}</p>
                    <p class='card-note'>{interpret_coordination_trend(summary['coordination_trend'])}</p>
                </div>
                <div class='card'>
                    <p class='card-title'>Signals in current window</p>
                    <p class='card-value'>{summary['signal_count']}</p>
                    <p class='card-note'>Live 7-cycle data powering decision-grade signals</p>
                </div>
                <div class='card'>
                    <p class='card-title'>Stable patterns detected</p>
                    <p class='card-value'>{summary['pattern_count']}</p>
                    <p class='card-note'>Conservative coordination patterns available for prospectus generation</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<p class='section-copy'><strong>Interpretation:</strong> {interpret_coordination_trend(summary['coordination_trend'])}</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p class='section-copy'>Zone {summary['zone']} · {summary['total_signals']} total signals on record · rolling {summary['window_days']}-day coordination window</p>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='section-divider' />", unsafe_allow_html=True)
    st.markdown("<h2 class='section-heading'>Prospectus</h2>", unsafe_allow_html=True)

    pdf_path = latest_pdf_path(zone)

    if pdf_path and pdf_path.is_file():
        st.markdown(
            f"<p class='section-copy'>Latest prospectus generated from folder: <strong>{pdf_path.parent.name}</strong></p>",
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
        st.info("No validated coordination patterns detected in this zone.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(
        "Generate Demand Prospectus",
        type="primary",
        use_container_width=True,
    ):
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
            st.experimental_rerun()
        else:
            st.warning(message)

    st.markdown("<hr class='section-divider' />", unsafe_allow_html=True)
    st.markdown("<h2 class='section-heading'>Notes</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Signals are derived from 7-cycle coordination windows, outputs represent conservative lower-bound demand estimates, and no personal or individual data is collected.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='footer-text'>Kulima Africa | Kulima OS Pilot v0.2<br>Coordination-based Digital Public Infrastructure</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
