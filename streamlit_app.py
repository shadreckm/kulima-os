"""
Kulima OS – Institutional Demand Signal Interface (Streamlit)

Live view: community signals → coordination → prospectus.
Run: streamlit run streamlit_app.py
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import streamlit as st
...

def coordination_strength_color(score: int) -> str:
    ...
def coordination_strength_color(score: int) -> str:
    if score >= 70:
        return "#2E7D32"   # green
    elif score >= 40:
        return "#F57C00"   # orange
    return "#D32F2F"       # red
from coordination_accumulation import (
    CYCLE_WINDOW_DAYS,
    compute_coordination_patterns,
    compute_coordination_trend,
    get_zone_window_signals,
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



    def coordination_strength_color(score: int) -> str:
        if score >= 70:
            return "#2E7D32"
        if score >= 40:
            return "#F57C00"
        return "#D32F2F"

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
            'About': 'Kulima OS is a coordination intelligence platform for infrastructure planning.',
        },
    )

    st.markdown(
        """
        <style>
        body, html, .stApp, .main {
            background: #F5F7FA !important;
            color: #263238 !important;
        }
        #MainMenu, header, footer, .css-1lsmgbg, .viewerBadge_link, [data-testid="stToolbar"], [data-testid="collapsedControl"], [aria-label="Main menu"] {
            visibility: hidden !important;
            height: 0 !important;
            width: 0 !important;
            overflow: hidden !important;
        }
        .css-1v0mbdj, .css-1lsmgbg, .css-1d391kg, .css-14xtw13 {
            display: none !important;
        }
        div.block-container {
            padding: 1rem 1.5rem 1.5rem !important;
            max-width: 1200px;
            margin: 0 auto;
            background: transparent;
        }
        .stApp {
            background: linear-gradient(180deg, #F5F7FA 0%, #FFFFFF 100%) !important;
        }
        main {
            padding-top: 0 !important;
        }
        .hero-panel {
            display: grid;
            grid-template-columns: 120px minmax(320px, 1fr);
            gap: 2rem;
            align-items: center;
            padding: 2rem 2rem 2.5rem;
            background: linear-gradient(160deg, #E8F5E9 0%, #F5F7FA 100%);
            border-radius: 28px;
            box-shadow: 0 28px 70px rgba(38, 50, 56, 0.08);
            margin-bottom: 2rem;
        }
        .hero-panel img {
            width: 88px;
            border-radius: 24px;
            background: #FFFFFF;
            padding: 0.75rem;
            box-shadow: 0 16px 40px rgba(46, 125, 50, 0.08);
        }
        .hero-copy {
            display: grid;
            gap: 0.4rem;
        }
        .hero-copy h1 {
            margin: 0;
            color: #263238;
            font-size: 3.2rem;
            letter-spacing: -0.04em;
        }
        .hero-copy h2 {
            margin: 0;
            color: #2E7D32;
            font-size: 1.45rem;
            font-weight: 700;
        }
        .hero-copy p {
            margin: 0.8rem 0 0;
            color: #455A64;
            font-size: 1rem;
            line-height: 1.8;
            max-width: 720px;
        }
        .section-heading {
            color: #263238;
            margin: 0;
            font-size: 1.55rem;
            font-weight: 700;
        }
        .section-copy {
            color: #455A64;
            margin: 0.75rem 0 0;
            line-height: 1.75;
            max-width: 820px;
        }
        .section-separator {
            height: 1px;
            background: rgba(38, 50, 56, 0.12);
            margin: 2rem 0;
        }
        .kpi-grid, .overview-grid, .pilot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .section-card, .action-card, .onboard-card {
            background: #FFFFFF;
            border-radius: 24px;
            padding: 1.75rem;
            box-shadow: 0 18px 40px rgba(38, 50, 56, 0.06);
        }
        .kpi-card {
            border-left: 4px solid #2E7D32;
            padding-left: 1.25rem;
        }
        .kpi-label {
            margin: 0;
            color: #455A64;
            font-size: 0.85rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .kpi-value {
            margin: 0.85rem 0 0;
            color: #263238;
            font-size: 2.4rem;
            font-weight: 800;
            line-height: 1;
        }
        .kpi-note {
            margin: 0.9rem 0 0;
            color: #607D8B;
            font-size: 0.95rem;
            line-height: 1.6;
        }
        .strength-meter {
            position: relative;
            width: 100%;
            height: 12px;
            border-radius: 999px;
            background: rgba(38, 50, 56, 0.08);
            margin: 1rem 0 0.55rem;
            overflow: hidden;
        }
        .strength-fill {
            height: 100%;
            border-radius: 999px;
            transition: width 0.35s ease;
        }
        .strength-label {
            margin: 0;
            color: #455A64;
            font-size: 0.95rem;
            font-weight: 700;
        }
        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-top: 1rem;
        }
        .pill {
            border-radius: 999px;
            background: #FFFFFF;
            color: #263238;
            border: 1px solid rgba(38, 50, 56, 0.12);
            padding: 0.8rem 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .pill.selected {
            background: #2E7D32;
            color: #FFFFFF;
            border-color: transparent;
            box-shadow: 0 18px 30px rgba(46, 125, 50, 0.16);
        }
        .action-card {
            text-align: center;
        }
        .action-card h3 {
            margin: 0;
            font-size: 1.45rem;
            color: #263238;
        }
        .action-card p {
            margin: 1rem auto 1.5rem;
            color: #455A64;
            max-width: 720px;
            line-height: 1.75;
        }
        .action-button {
            background: #F57C00 !important;
            color: #FFFFFF !important;
            border-radius: 999px !important;
            padding: 1rem 1.6rem !important;
            font-size: 1rem !important;
            font-weight: 800 !important;
            border: none !important;
        }
        .action-button:hover {
            background: #EF6C00 !important;
        }
        .onboard-card h3 {
            margin: 0;
            font-size: 1.35rem;
            color: #263238;
        }
        .onboard-card ul {
            margin: 1rem 0 0;
            padding-left: 1.2rem;
            color: #455A64;
            line-height: 1.8;
        }
        .onboard-card li {
            margin-bottom: 0.8rem;
        }
        .dashboard-footer {
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(38, 50, 56, 0.12);
            color: #546E7A;
            text-align: center;
            font-size: 0.95rem;
            line-height: 1.8;
        }
        .dashboard-footer a {
            color: #2E7D32;
            text-decoration: none;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    logo_path = Path(__file__).resolve().parent / "assets" / "kulima_africa_logo.png"
    cols = st.columns([1, 4])
    with cols[0]:
        if logo_path.is_file():
            st.image(str(logo_path), width=96)
    with cols[1]:
        st.markdown(
            """
            <div class='hero-copy'>
                <h1>Kulima OS</h1>
                <h2>Coordination Intelligence System</h2>
                <p>Seeing real demand before infrastructure is built.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div class='section-separator'></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-heading'>System Overview</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Kulima OS converts verified, identity-free coordination signals into institution-grade infrastructure intelligence for critical planning decisions.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class='overview-grid'>
            <div class='card'><p class='card-title'>Temporal Coordination</p><p class='card-note'>Process signals in 7-cycle windows to protect the temporal moat and preserve collective context.</p></div>
            <div class='card'><p class='card-title'>Infrastructure Context</p><p class='card-note'>Apply settlement and gap analysis so planning reflects real infrastructure readiness.</p></div>
            <div class='card'><p class='card-title'>Traceable Evidence</p><p class='card-note'>Capture structured pilot evidence and decision intelligence for governance review.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-separator'></div>", unsafe_allow_html=True)

    st.markdown("<h2 class='section-heading'>Live Coordination Dashboard</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Review validated demand signal performance and infrastructure readiness for the selected pilot zone.</p>",
        unsafe_allow_html=True,
    )

    if "selected_zone" not in st.session_state:
        st.session_state.selected_zone = PILOT_ZONES[0]

    pill_cols = st.columns(len(PILOT_ZONES))
    for idx, zone_name in enumerate(PILOT_ZONES):
        if pill_cols[idx].button(zone_name, key=f"zone_{zone_name}"):
            st.session_state.selected_zone = zone_name

    selected_zone = st.session_state.selected_zone
    summary = build_coordination_summary(selected_zone)

kpi_cards = [
    {
        "label": "Coordination Trend",
        "value": summary["coordination_trend"],
        "note": "Current intelligence classification for this zone.",
        "score": summary["coordination_score"],
        "strength_label": summary["coordination_strength_label"],
        "strength_color": coordination_strength_color(summary["coordination_score"]),
    },
    {
        "label": "Validated Signals",
        "value": summary["validated_signals"],
        "note": "Signals that passed integrity and reserve filtering.",
    },
    {
        "label": "Planning Reserve",
        "value": summary["planning_reserve"],
        "note": "Conservative capacity reserved for shared productive loads.",
    },
    {
        "label": "Infrastructure Readiness",
        "value": summary["lundai_status"],
        "note": "Assessment from the LUNDAI infrastructure layer.",
    },
]

# ✅ FIXED KPI GRID (ONLY CHANGE: HTML + SAFE STRENGTH)
st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
for card in kpi_cards:

    strength_html = ""
    if card.get("score") is not None:
        strength_html = f"""
        <div class='strength-meter'>
            <div class='strength-fill' style='width: {card['score']}%; background: {card['strength_color']};'></div>
        </div>
        <p class='strength-label'>{card['strength_label']} — {card['score']}% coordination strength</p>
        """

    st.markdown(
        f"""
        <div class='card kpi-card'>
            <p class='kpi-label'>{card['label']}</p>
            <p class='kpi-value'>{card['value']}</p>
            {strength_html}
            <p class='kpi-note'>{card['note']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

# ✅ NO CHANGE BELOW — ONLY FIX HTML TAGS
timeline = build_zone_signal_timeline(selected_zone)
if timeline:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-heading'>Signal Accumulation</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Recent daily signal volume for the selected pilot zone.</p>",
        unsafe_allow_html=True,
    )
    st.line_chart(
        {"Signals": [point["signals"] for point in timeline]},
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='section-separator'></div>", unsafe_allow_html=True)

st.markdown("<h2 class='section-heading'>Prospectus / Reporting</h2>", unsafe_allow_html=True)
st.markdown(
    "<p class='section-copy'>Create a verified demand signal prospectus for institutional review and infrastructure investment planning.</p>",
    unsafe_allow_html=True,
)

st.markdown("<div class='action-card'>", unsafe_allow_html=True)
st.markdown("<h3>Generate Verified Demand Signal Prospectus</h3>", unsafe_allow_html=True)
st.markdown(
    "<p>Deliver a prospectus that packages audited coordination patterns, infrastructure context, and social reserve guidance into an institutional artifact.</p>",
    unsafe_allow_html=True,
)

if st.button("Generate Verified Demand Signal Prospectus", key="generate_prospectus", help="Create the latest verified planning prospectus", use_container_width=False):
    with st.spinner("Generating verified demand prospectus..."):
        new_pdf, message = generate_zone_prospectus(selected_zone)
    if new_pdf and new_pdf.is_file():
        st.success("Verified demand prospectus generated.")
        with open(new_pdf, "rb") as pdf_file:
            st.download_button(
                label="Download Demand Prospectus",
                data=pdf_file.read(),
                file_name="demand_prospectus.pdf",
                mime="application/pdf",
                use_container_width=False,
                key=f"download_new_{summary['zone']}",
            )
    else:
        st.warning(message)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='section-separator'></div>", unsafe_allow_html=True)

st.markdown("<h2 class='section-heading'>Join System</h2>", unsafe_allow_html=True)
st.markdown(
    "<p class='section-copy'>Activate local participation through the operational WhatsApp channel and contribute real coordination signals for infrastructure planning.</p>",
    unsafe_allow_html=True,
)

st.markdown("<div class='onboard-card'>", unsafe_allow_html=True)
st.markdown("<h3>Join the System</h3>", unsafe_allow_html=True)

# ✅ ONLY IMPROVED ONBOARDING (CLARITY FIX)
st.markdown(
"""
<ul>
    <li><strong>Step 1:</strong> Save the Kulima OS WhatsApp number:<br>
    <strong>+1 415 523 8886</strong></li>

    <li><strong>Step 2:</strong> Open WhatsApp and send:<br>
    <strong>join week-saved</strong></li>

    <li><strong>Step 3:</strong> Send real activity updates such as:<br>
    "I am irrigating crops"<br>
    "We are milling maize"<br>
    "Selling tomatoes today"</li>

    <li><strong>Step 4:</strong> Continue sending updates consistently.<br>
    Stable repetition strengthens coordination signals.</li>
</ul>
""",
unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<div class='dashboard-footer'>Kulima Africa — Coordination Intelligence Infrastructure • Public Digital System • <a href='https://github.com/shadreckm/kulima-os' target='_blank'>GitHub</a> • <a href='#'>Dashboard</a></div>",
    unsafe_allow_html=True,
)

if __name__ == "__main__":
    main()
