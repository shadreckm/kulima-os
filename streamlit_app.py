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
            f"Coordination activity detected, but patterns are not yet stable for infrastructure planning in {zone_key}. "
            f"({summary.get('signals_in_window', 0)} signal(s) in the {CYCLE_WINDOW_DAYS}-day window)."
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
            padding: 2rem 2rem 3rem;
            max-width: 1180px;
            margin: auto;
            background: #F8FAFC;
        }
        div[data-testid="stImage"] {
            display: flex;
            justify-content: center;
        }
        div[data-testid="stImage"] img {
            border-radius: 16px;
            box-shadow: 0 18px 35px rgba(46, 125, 50, 0.12);
        }
        .hero-block {
            text-align: center;
            padding: 2rem 1.5rem 1.75rem;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 28px;
            box-shadow: 0 26px 70px rgba(15, 23, 42, 0.08);
            margin-bottom: 1.75rem;
        }
        .hero-block h1 {
            margin: 0;
            color: #263238;
            font-size: 3.35rem;
            letter-spacing: -0.04em;
        }
        .hero-block h2 {
            margin: 0.75rem 0 0;
            color: #263238;
            font-size: 1.45rem;
            font-weight: 600;
        }
        .hero-block p {
            margin: 1rem auto 0;
            color: #616161;
            font-size: 1rem;
            line-height: 1.75;
            max-width: 740px;
        }
        .section-heading {
            color: #263238;
            margin: 0;
            font-size: 1.45rem;
            font-weight: 700;
        }
        .section-copy {
            color: #616161;
            margin-top: 0.75rem;
            margin-bottom: 1.25rem;
            line-height: 1.75;
            max-width: 820px;
        }
        .section-divider {
            height: 1px;
            background: #E2E8F0;
            margin: 1.75rem 0 2rem;
            border: none;
        }
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1rem;
            margin-top: 1.75rem;
        }
        .card {
            background: white;
            border-radius: 22px;
            padding: 1.7rem 1.7rem;
            box-shadow: 0 24px 45px rgba(15, 23, 42, 0.08);
            min-height: 190px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
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
            margin: 0.9rem 0 0;
            color: #263238;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.05;
        }
        .card-primary .card-value {
            font-size: 2.4rem;
        }
        .card-note {
            margin: 0.65rem 0 0;
            color: #616161;
            font-size: 0.95rem;
            font-weight: 600;
        }
        .footer-text {
            color: #9E9E9E;
            font-size: 0.92rem;
            line-height: 1.8;
            text-align: center;
            margin-top: 3rem;
        }
        button {
            background: #F57C00 !important;
            color: #ffffff !important;
            border-radius: 999px !important;
            border: none !important;
            padding: 0.95rem 1.25rem !important;
            font-weight: 700 !important;
            box-shadow: 0 18px 40px rgba(245, 124, 0, 0.18) !important;
            transition: background 0.18s ease, transform 0.18s ease !important;
        }
        button:hover {
            background: #dd6d03 !important;
            transform: translateY(-1px) !important;
        }
        button:focus {
            outline: none !important;
            box-shadow: 0 0 0 4px rgba(245, 124, 0, 0.18) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.image("assets/kulima_africa_logo.png", width=130)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='hero-block'>
            <h1>Kulima OS</h1>
            <h2>Demand Signal Interface</h2>
            <p>Seeing real demand before infrastructure is built.</p>
            <p>A coordination-first digital public infrastructure for real-world demand sensing.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-heading'>Live System</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Core infrastructure signals are flowing through the platform in real time.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class='info-card-grid'>
            <div class='info-card'>✅ System operational</div>
            <div class='info-card'>✅ Signals being collected in real time</div>
            <div class='info-card'>✅ Backend live</div>
            <div class='info-card'>✅ WhatsApp input active</div>
        </div>
        <p class='section-copy'><strong>Live Pilot:</strong> Mzuzu · Ekwendeni · Karonga</p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
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
    st.markdown("<br>", unsafe_allow_html=True)

    summary = build_coordination_summary(zone)

    st.markdown("<hr class='section-divider' />", unsafe_allow_html=True)
    st.markdown("<h2 class='section-heading'>Dashboard</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Live coordination indicators for the selected pilot zone.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class='dashboard-grid'>
            <div class='card card-primary'>
                <p class='card-title'>Coordination Trend</p>
                <p class='card-value'>{summary['coordination_trend']}</p>
                <p class='card-note'>{interpret_coordination_trend(summary['coordination_trend'])}</p>
            </div>
            <div class='card'>
                <p class='card-title'>Signals Count</p>
                <p class='card-value'>{summary['signal_count']}</p>
                <p class='card-note'>Signals in the current {summary['window_days']}-day coordination window.</p>
            </div>
            <div class='card'>
                <p class='card-title'>Detected Patterns</p>
                <p class='card-value'>{summary['pattern_count']}</p>
                <p class='card-note'>Stable patterns currently available for planning review.</p>
            </div>
            <div class='card'>
                <p class='card-title'>Zone Activity State</p>
                <p class='card-value'>{summary['zone']}</p>
                <p class='card-note'>{('Active signals detected' if summary['total_signals'] > 0 else 'Awaiting pilot coordination inputs')}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr class='section-divider' />", unsafe_allow_html=True)
    st.markdown("<h2 class='section-heading'>Prospectus</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Generate demand intelligence for infrastructure planning.</p>",
        unsafe_allow_html=True,
    )

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
        st.info("Coordination activity detected, but patterns are not yet stable for infrastructure planning.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(
        "Generate Demand Prospectus",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("Generating demand signal prospectus..."):
            new_pdf, message = generate_zone_prospectus(zone)

        if new_pdf and new_pdf.is_file():
            st.success("Prospectus generated and ready for download.")
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

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-heading'>Join the System</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Help the pilot grow by sharing real-time activity updates through WhatsApp.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class='join-card'>
            <p class='join-step'><strong>1.</strong> Save number: +1 415 523 8886</p>
            <p class='join-step'><strong>2.</strong> Send: <em>join week-saved</em></p>
            <p class='join-step'><strong>3.</strong> Start sending updates like:</p>
            <p class='join-step'>• I am irrigating crops</p>
            <p class='join-step'>• We are milling maize</p>
            <p class='join-step'>• Selling tomatoes</p>
        </div>
        <p class='section-copy'>Just send what you are doing — no app required.</p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='footer-text'>Kulima Africa<br>Kulima OS v0.2<br>Coordination-based Digital Public Infrastructure<br>Live Dashboard: https://kulima-os.streamlit.app/</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
