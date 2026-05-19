from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import streamlit as st

from coordination_accumulation import CYCLE_WINDOW_DAYS
from lumoza_integration import integrate_whatsapp_to_lumoza
from prospectus_generator import ProspectusGenerator
from signal_storage import Signal, default_storage
from zone_utils import normalize_zone

PILOT_ZONES = ["MZUZU", "EKWENDENI", "KARONGA"]
ARTIFACTS_ROOT = Path(__file__).resolve().parent / "artifacts"


# ✅ FIXED: GLOBAL FUNCTION (was misplaced before)
def coordination_strength_color(score: int) -> str:
    if score >= 70:
        return "#2E7D32"
    elif score >= 40:
        return "#F57C00"
    return "#D32F2F"


def load_all_signals() -> List[Signal]:
    return default_storage.get_all_signals()


def build_zone_signal_timeline(zone: str, days: int = 14):
    zone_key = normalize_zone(zone)
    signals = [
        s for s in load_all_signals()
        if normalize_zone(s.zone) == zone_key and s.timestamp
    ]

    counts = Counter()
    for s in signals:
        try:
            d = datetime.fromisoformat(s.timestamp.replace("Z", "+00:00")).date()
            counts[d] += 1
        except Exception:
            continue

    today = datetime.now(timezone.utc).date()
    return [
        {"date": (today - timedelta(days=i)), "signals": counts.get(today - timedelta(days=i), 0)}
        for i in reversed(range(days))
    ]


def build_coordination_summary(zone: str) -> dict:
    summary = integrate_whatsapp_to_lumoza(zone=normalize_zone(zone)) or {}

    patterns = summary.get("patterns", [])

    score = 15
    if patterns:
        vals = [p.get("coordination_confidence", 0) for p in patterns]
        if vals:
            score = int(min(max(sum(vals) / len(vals) * 100, 15), 100))

    strength_label = "Weak"
    if score >= 70:
        strength_label = "Strong"
    elif score >= 40:
        strength_label = "Emerging"

    return {
        "coordination_trend": summary.get("coordination_trend", "Emerging"),
        "validated_signals": summary.get("validated_signal_count", 0),
        "planning_reserve": summary.get("planning_reserve", {}).get("usable_signals", 0),
        "lundai_status": summary.get("lundai_analysis", {}).get("overall_assessment", {}).get("overall_infrastructure_status", "Unknown"),
        "coordination_score": score,
        "coordination_strength_label": strength_label,
        "patterns": patterns,
    }


def generate_zone_prospectus(zone: str) -> Tuple[Optional[Path], str]:
    summary = integrate_whatsapp_to_lumoza(zone)
    patterns = summary.get("patterns", [])

    if not patterns:
        return None, "No validated patterns yet."

    gen = ProspectusGenerator()
    prospectus = gen.generate_prospectus(patterns)

    path = ARTIFACTS_ROOT / f"{zone}_prospectus.pdf"
    gen.generate_pdf(prospectus, str(path))

    return path, "Prospectus generated."


# ✅ MAIN APP

def main():
    st.set_page_config(layout="wide")

    # ✅ HERO
    st.markdown("## Kulima OS")
    st.markdown("### Coordination Intelligence System")
    st.markdown("Seeing real demand before infrastructure is built.")
    st.markdown("---")

    # ✅ ZONE SELECTOR
    zone = st.radio("Zone", PILOT_ZONES, horizontal=True)

    summary = build_coordination_summary(zone)

    # ✅ KPI CARDS
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Trend", summary["coordination_trend"])
    col2.metric("Signals", summary["validated_signals"])
    col3.metric("Reserve", summary["planning_reserve"])
    col4.metric("Infrastructure", summary["lundai_status"])

    # ✅ SAFE STRENGTH BAR
    score = summary.get("coordination_score", 0)
    st.progress(score)
    st.caption(f"Coordination Strength: {score}% ({summary.get('coordination_strength_label')})")

    # ✅ CHART
    timeline = build_zone_signal_timeline(zone)
    if timeline:
        st.line_chart([x["signals"] for x in timeline])

    st.markdown("---")

    # ✅ PROSPECTUS
    if st.button("Generate Prospectus"):
        path, msg = generate_zone_prospectus(zone)
        if path:
            st.success(msg)
            with open(path, "rb") as f:
                st.download_button("Download", f.read(), "prospectus.pdf")

    st.markdown("---")
    st.caption("Kulima Africa — Coordination Intelligence Infrastructure")


if __name__ == "__main__":
    main()