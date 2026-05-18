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

    st.title("Kulima OS – Demand Signal Interface")
    st.subheader("Coordination-based infrastructure intelligence")
    st.write(
        "A focused interface for infrastructure planners, funders, and development partners to review verified demand signals."
    )

    with st.expander("How this works"):
        st.write(
            "This system translates daily community activity into coordination-based demand signals to support infrastructure planning."
        )

    st.divider()

    st.markdown("## Overview")
    st.write(
        "Select a pilot zone and review the current coordination state, demand prospectus access, and institutional notes."
    )
    zone = st.radio(
        "Select pilot zone",
        options=PILOT_ZONES,
        horizontal=True,
        label_visibility="collapsed",
    )

    summary = build_coordination_summary(zone)

    st.divider()
    st.markdown("## Coordination Status")

    if summary["total_signals"] == 0:
        st.warning("No coordination signals are recorded yet in this zone.")
        st.write(
            "The interface is ready to receive and aggregate signals once they are submitted through the pilot reporting channels."
        )
    else:
        col1, col2, col3 = st.columns([2, 2, 2])
        col1.metric("Coordination trend", summary["coordination_trend"])
        col2.metric("Signals in current window", summary["signal_count"])
        col3.metric("Stable patterns detected", summary["pattern_count"])

        st.markdown(f"**Interpretation:** {interpret_coordination_trend(summary['coordination_trend'])}")
        st.caption(
            f"Zone {summary['zone']} · {summary['total_signals']} total signals on record · "
            f"rolling {summary['window_days']}-day coordination window"
        )

    st.divider()
    st.markdown("## Prospectus Access")

    pdf_path = latest_pdf_path(zone)

    if pdf_path and pdf_path.is_file():
        st.caption(f"Latest prospectus generated from folder: `{pdf_path.parent.name}`")
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
        st.info("No prospectus available yet for this zone.")

    if st.button(
        "Generate Prospectus",
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

    st.divider()
    st.markdown("## Notes")
    st.markdown("""
- Signals are derived from 7-cycle coordination windows  
- Outputs represent conservative lower-bound demand estimates  
- No personal or individual data is collected
""")

    st.divider()
    st.caption(
        """
Kulima Africa | Kulima OS Pilot v0.2  
Coordination-based Digital Public Infrastructure
"""
    )


if __name__ == "__main__":
    main()
