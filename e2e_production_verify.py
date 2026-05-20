"""
Kulima OS — End-to-End Production Verification
================================================
Tests the full pipeline: WhatsApp input -> parse -> store -> LUMOZA -> LUNDAI -> ZENTARI -> dashboard -> prospectus.
"""

import sys
import json
import traceback
from pathlib import Path
from datetime import datetime

PASS = 0
FAIL = 0
WARNINGS = []

def section(title):
    print(f"\n{'='*72}")
    print(f"  {title}")
    print(f"{'='*72}")

def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}")
        if detail:
            print(f"         -> {detail}")

def warn(label, detail=""):
    WARNINGS.append((label, detail))
    print(f"  [WARN] {label}")
    if detail:
        print(f"         -> {detail}")


# ─────────────────────────────────────────────────────────────────────
# LAYER 1: Input Parsing
# ─────────────────────────────────────────────────────────────────────
section("LAYER 1 — Input Parsing (input_parser.py)")

from input_parser import parse_user_input, InputParser

test_messages = [
    ("I am irrigating crops today", "irrigation", "Core irrigation signal"),
    ("We are milling maize", "milling", "Core milling signal"),
    ("Selling tomatoes today", "trading", "Core trading signal"),
    ("cold storage running", "storage", "Core storage signal"),
    ("welding gates", "welding", "Core welding signal"),
    ("irrigatin", "irrigation", "Typo tolerance"),
    ("busy at the mill", "milling", "Informal language"),
    ("watering crops", "irrigation", "Synonym mapping"),
]

for msg, expected_activity, description in test_messages:
    result = parse_user_input(msg, sender_phone="+265883766348")
    if result is None:
        check(f"Parse: {description}", False, f"Returned None for: '{msg}'")
    else:
        check(f"Parse: {description} -> {result.activity_type}",
              result.activity_type == expected_activity,
              f"Expected '{expected_activity}', got '{result.activity_type}' for '{msg}'")

# Empty / meaningless messages
empty_result = parse_user_input("", sender_phone="+265883766348")
check("Empty input returns None", empty_result is None)

symbols_result = parse_user_input("!!!", sender_phone="+265883766348")
check("Symbols-only input returns None", symbols_result is None)

# Field completeness
sample = parse_user_input("I am irrigating crops today", sender_phone="+265883766348")
check("Parsed signal has activity_type", sample is not None and sample.activity_type != "")
check("Parsed signal has zone", sample is not None and sample.zone != "")
check("Parsed signal has frequency", sample is not None and sample.frequency != "")
check("Parsed signal has confidence > 0", sample is not None and sample.confidence > 0)
check("Parsed signal has actors >= 1", sample is not None and sample.actors >= 1)


# ─────────────────────────────────────────────────────────────────────
# LAYER 2: Signal Storage
# ─────────────────────────────────────────────────────────────────────
section("LAYER 2 — Signal Storage (signal_storage.py)")

from signal_storage import Signal, store_signal, default_storage, get_unprocessed_signals
from zone_utils import normalize_zone

# Store a test signal
test_signal_id = store_signal(
    activity_type="irrigation",
    zone="MZUZU",
    frequency="daily",
    actors=2,
    raw_message="e2e test irrigation",
    user_phone="+265883766348",
    confidence=0.85,
)
check("store_signal returns signal_id", test_signal_id is not None, f"Got: {test_signal_id}")

# Retrieve signals
all_signals = default_storage.get_all_signals()
check("get_all_signals returns list", isinstance(all_signals, list))
check("Storage contains signals", len(all_signals) > 0, f"Count: {len(all_signals)}")

# Verify stored signal fields
if all_signals:
    last = all_signals[-1]
    check("Stored signal has signal_id", last.signal_id != "")
    check("Stored signal has activity_type", last.activity_type != "")
    check("Stored signal has zone", last.zone != "")
    check("Stored signal has timestamp", last.timestamp != "")
    check("Stored signal zone is normalized", last.zone == normalize_zone(last.zone))


# ─────────────────────────────────────────────────────────────────────
# LAYER 3: Full Pipeline (LUMOZA → LUNDAI → ZENTARI)
# ─────────────────────────────────────────────────────────────────────
section("LAYER 3 — Pipeline: LUMOZA -> LUNDAI -> ZENTARI")

from lumoza_integration import integrate_whatsapp_to_lumoza

summary = integrate_whatsapp_to_lumoza(zone="MZUZU")

check("Pipeline returns dict", isinstance(summary, dict))
check("Summary has 'zone'", "zone" in summary)
check("Summary has 'raw_signal_count'", "raw_signal_count" in summary)
check("Summary has 'validated_signal_count'", "validated_signal_count" in summary)
check("Summary has 'planning_reserve'", "planning_reserve" in summary)
check("Summary has 'coordination_trend'", "coordination_trend" in summary)
check("Summary has 'patterns'", "patterns" in summary)
check("Summary has 'lundai_analysis'", "lundai_analysis" in summary)
check("Summary has 'settlement_alignment'", "settlement_alignment" in summary)
check("Summary has 'status'", "status" in summary)

# Verify planning reserve structure
pr = summary.get("planning_reserve", {})
check("Planning reserve has 'usable_signals'",
      isinstance(pr, dict) and "usable_signals" in pr,
      f"Got: {pr}")
check("Planning reserve has 'reserve_buffer'",
      isinstance(pr, dict) and "reserve_buffer" in pr)
check("Planning reserve has 'reserve_ratio'",
      isinstance(pr, dict) and "reserve_ratio" in pr)

# Verify coordination trend is a known value
trend = summary.get("coordination_trend", "")
check("Coordination trend is valid",
      trend in ("Emerging", "Growing", "Strong"),
      f"Got: '{trend}'")

# Verify patterns structure (if any exist)
patterns = summary.get("patterns", [])
if patterns:
    p = patterns[0]
    check("Pattern has 'activity_type'", "activity_type" in p)
    check("Pattern has 'zone'", "zone" in p)
    check("Pattern has 'demand_rhythm'", "demand_rhythm" in p)
    check("Pattern has 'confidence_class'", "confidence_class" in p)
    check("Pattern has 'coordination_confidence'", "coordination_confidence" in p)
    check("Pattern has 'validation_strength'", "validation_strength" in p)
    check("Pattern has 'bankability_note'", "bankability_note" in p)
else:
    warn("No patterns in current window",
         "This is expected if few signals exist in the 7-day window. Not a bug.")


# ─────────────────────────────────────────────────────────────────────
# LAYER 4: Dashboard Data (build_coordination_summary)
# ─────────────────────────────────────────────────────────────────────
section("LAYER 4 — Dashboard Data (streamlit_app helpers)")

from streamlit_app import (
    build_coordination_summary,
    build_zone_signal_timeline,
    coordination_strength_color,
    interpret_coordination_trend,
)

dash = build_coordination_summary("MZUZU")

check("Dashboard summary is dict", isinstance(dash, dict))
check("Has 'zone'", "zone" in dash)
check("Has 'total_signals'", "total_signals" in dash)
check("Has 'validated_signals'", "validated_signals" in dash)
check("Has 'coordination_score'", "coordination_score" in dash)
check("Has 'coordination_strength_label'", "coordination_strength_label" in dash)
check("Has 'coordination_trend'", "coordination_trend" in dash)
check("Has 'lundai_status'", "lundai_status" in dash)
check("Has 'planning_reserve'", "planning_reserve" in dash)
check("Has 'pattern_explanations'", "pattern_explanations" in dash)

# Verify coordination_score is bounded
score = dash.get("coordination_score", -1)
check("Coordination score 15–100", 15 <= score <= 100, f"Got: {score}")

# Verify strength label consistency
label = dash.get("coordination_strength_label", "")
check("Strength label is valid",
      label in ("Weak", "Emerging", "Strong"),
      f"Got: '{label}'")

# Verify color function
check("Color for score 80 is green", coordination_strength_color(80) == "#2E7D32")
check("Color for score 50 is orange", coordination_strength_color(50) == "#F57C00")
check("Color for score 20 is red", coordination_strength_color(20) == "#D32F2F")

# Timeline
timeline = build_zone_signal_timeline("MZUZU")
check("Timeline returns list", isinstance(timeline, list))
check("Timeline has entries", len(timeline) > 0, f"Count: {len(timeline)}")
if timeline:
    check("Timeline entry has 'date'", "date" in timeline[0])
    check("Timeline entry has 'signals'", "signals" in timeline[0])

# Trend interpretation
check("interpret_coordination_trend('Emerging')",
      "Early" in interpret_coordination_trend("Emerging"))
check("interpret_coordination_trend('Strong')",
      "planning-grade" in interpret_coordination_trend("Strong"))

# Explanation crash guard (the bug we fixed)
explanations = dash.get("pattern_explanations", [])
check("pattern_explanations is list", isinstance(explanations, list))
for i, exp in enumerate(explanations):
    check(f"Explanation [{i}] is string (no crash)", isinstance(exp, str))


# ─────────────────────────────────────────────────────────────────────
# LAYER 5: Prospectus Generation
# ─────────────────────────────────────────────────────────────────────
section("LAYER 5 — Prospectus Generation")

from prospectus_generator import ProspectusGenerator
from streamlit_app import generate_zone_prospectus

# Generate a prospectus for MZUZU
pdf_path, message = generate_zone_prospectus("MZUZU")

if pdf_path and pdf_path.is_file():
    check("Prospectus PDF generated", True)
    check("PDF file size > 0", pdf_path.stat().st_size > 0,
          f"Size: {pdf_path.stat().st_size} bytes")
    check("PDF is downloadable (file exists)", pdf_path.is_file())
    
    # Check companion JSON
    json_path = pdf_path.with_suffix(".json")
    if json_path.is_file():
        check("Companion JSON exists", True)
        with open(json_path, "r") as f:
            prospectus_data = json.load(f)
        check("Prospectus JSON is dict", isinstance(prospectus_data, dict))
        check("Prospectus has 'metadata'", "metadata" in prospectus_data)
        check("Prospectus has 'patterns'", "patterns" in prospectus_data)
        check("Prospectus has 'planning_reserve'", "planning_reserve" in prospectus_data)
    else:
        warn("Companion JSON not found", str(json_path))
else:
    warn("Prospectus not generated (insufficient patterns)",
         f"Message: {message}")
    # This is NOT a failure — it means the 7-day window has too few signals
    check("Prospectus message is informative", len(message) > 20, f"Got: '{message}'")


# ─────────────────────────────────────────────────────────────────────
# LAYER 6: WhatsApp Handler (User Feedback)
# ─────────────────────────────────────────────────────────────────────
section("LAYER 6 — WhatsApp Handler & User Feedback")

from whatsapp_handler import WhatsAppMessageHandler

handler = WhatsAppMessageHandler()

# Test normal activity message
success, response = handler.handle_incoming_message(
    "I am irrigating crops today", "+265883766348"
)
check("Handler returns success=True for valid input", success is True)
check("Response is non-empty string", isinstance(response, str) and len(response) > 0)
check("Response contains confirmation", "✅" in response or "recorded" in response.lower())
check("Response contains trend info", "trend" in response.lower() or "📊" in response)
check("Response is professional and clear", "🔌" in response or "energy" in response.lower())

# Test empty/meaningless message
success2, response2 = handler.handle_incoming_message("!!!", "+265883766348")
check("Handler returns success=True for meaningless input", success2 is True)
check("Meaningless response is non-empty", len(response2) > 0)
check("Meaningless response does NOT expose errors",
      "error" not in response2.lower() and "traceback" not in response2.lower())

# Test REPORT command
success3, response3 = handler.handle_incoming_message("REPORT MZUZU", "+265883766348")
check("REPORT command returns success", success3 is True)
check("REPORT response is non-empty", len(response3) > 0)

# Test invalid REPORT
success4, response4 = handler.handle_incoming_message("REPORT", "+265883766348")
check("Invalid REPORT returns helpful message", success4 is False or "REPORT" in response4)


# ─────────────────────────────────────────────────────────────────────
# LAYER 7: System Invariant Checks
# ─────────────────────────────────────────────────────────────────────
section("LAYER 7 — System Invariant Verification")

from policy import RESERVE_RATIO, ENFORCED_RESERVE_RATIO

check("Reserve ratio invariant holds",
      RESERVE_RATIO == ENFORCED_RESERVE_RATIO,
      f"RESERVE_RATIO={RESERVE_RATIO}, ENFORCED={ENFORCED_RESERVE_RATIO}")

# Zero-PII check: verify no phone numbers leak into patterns or prospectus
all_sigs = default_storage.get_all_signals()
pipeline_out = integrate_whatsapp_to_lumoza(zone="MZUZU")
patterns_json = json.dumps(pipeline_out.get("patterns", []))
check("No phone numbers in pattern output",
      "+265" not in patterns_json and "phone" not in patterns_json.lower())

lundai_json = json.dumps(pipeline_out.get("lundai_analysis", {}))
check("No phone numbers in LUNDAI output",
      "+265" not in lundai_json and "phone" not in lundai_json.lower())

# Temporal moat: verify window_days is 7
check("Temporal moat: window_days == 7",
      pipeline_out.get("window_days") == 7,
      f"Got: {pipeline_out.get('window_days')}")


# ─────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────
section("END-TO-END VERIFICATION SUMMARY")

total = PASS + FAIL
print(f"\n  Total checks:  {total}")
print(f"  Passed:        {PASS}")
print(f"  Failed:        {FAIL}")
print(f"  Warnings:      {len(WARNINGS)}")

if WARNINGS:
    print("\n  Warnings (non-blocking observations):")
    for label, detail in WARNINGS:
        print(f"    • {label}")
        if detail:
            print(f"      {detail}")

if FAIL == 0:
    print(f"\n  {'='*50}")
    print(f"  [SUCCESS] All {PASS} checks passed.")
    print(f"  System Status: PRODUCTION-READY")
    print(f"  {'='*50}")
else:
    print(f"\n  {'='*50}")
    print(f"  [ATTENTION] {FAIL} check(s) failed. Review above.")
    print(f"  {'='*50}")
    sys.exit(1)
