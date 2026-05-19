from __future__ import annotationsfrom __future__") as f:
                st.download_button("Download Prospectus", f, "prospectus.pdf")
        else:
            st.warning(msg)

    st.markdown("---")

    # ✅ ONBOARDING
    st.markdown("### Join the System")
    st.markdown("""
    1. Save WhatsApp number  
    2. Send join code  
    3. Submit activities  

    Example:
    - I am irrigating crops  
    - We are milling maize  
    """)

    st.markdown("---")
    st.caption("Kulima Africa • Coordination Intelligence Infrastructure")


if __name__ == "__main__":
    main()


from pathlib import Path
import streamlit as st

from lumoza_integration import integrate_whatsapp_to_lumoza
from prospectus_generator import ProspectusGenerator
from zone_utils import normalize_zone

PILOT_ZONES = ["MZUZU", "EKWENDENI", "KARONGA"]


def build_summary(zone: str):
    summary = integrate_whatsapp_to_lumoza(zone) or {}
    patterns = summary.get("patterns", [])

    score = 0
    if patterns:
        vals = [p.get("coordination_confidence", 0) for p in patterns]
        score = int(min(max(sum(vals) / len(vals) * 100, 0), 100))

    return {
        "trend": summary.get("coordination_trend", "Emerging"),
        "signals": summary.get("validated_signal_count", 0),
        "reserve": summary.get("planning_reserve", {}).get("usable_signals", 0),
        "infrastructure": summary.get("lundai_analysis", {}).get("overall_assessment", {}).get("overall_infrastructure_status", "Unknown"),
        "score": score,
    }


def generate_prospectus(zone):
    summary = integrate_whatsapp_to_lumoza(zone)
    patterns = summary.get("patterns", [])
    
    if not patterns:
        return None, "No patterns yet."

    gen = ProspectusGenerator()
    pdf = f"{zone}_prospectus.pdf"
    gen.generate_pdf(gen.generate_prospectus(patterns), pdf)

    return pdf, "Generated"


def main():
    st.set_page_config(layout="wide")

    # 🔥 HERO
    st.markdown("# Kulima OS")
    st.markdown("## Coordination Intelligence for Infrastructure Planning")
    st.markdown("Seeing real demand before infrastructure is built.")
    st.markdown("---")

    # ✅ ZONE
    zone = st.radio("Select Zone", PILOT_ZONES, horizontal=True)

    summary = build_summary(zone)

    # ✅ KPI GRID
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Coordination Trend", summary["trend"])
    col2.metric("Validated Signals", summary["signals"])
    col3.metric("Planning Reserve", summary["reserve"])
    col4.metric("Infrastructure Status", summary["infrastructure"])

    # ✅ STRENGTH
    st.progress(summary["score"])
    st.caption(f"Coordination Strength: {summary['score']}%")

    st.markdown("---")

    # ✅ PROSPECTUS
    st.markdown("### Prospectus")

    if st.button("Generate Demand Prospectus"):
        pdf, msg = generate_prospectus(zone)

        if pdf:
