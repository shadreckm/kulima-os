# KULIMA OS - Demonstration Guide

**For Hackathon Judges, Reviewers, and Auditors**

---

## Demo Hierarchy

KULIMA OS provides **two demonstration modes**. Judges and reviewers should prioritize the **PPSG Live Demo** as the canonical proof of system claims.

### 🔴 PRIMARY: PPSG Live Demo (Canonical)

**Status**: Authoritative demonstration for reviewers and judges  
**Purpose**: Prove architectural refusal of PII, Zero-PII enforcement, and Temporal Moat protection  
**What it demonstrates**: What the system **refuses to do**, not just what it can do

**This is the demo that validates the system's core claims.**

### 🔵 SECONDARY: Legacy Pilot Demo (Conceptual)

**Status**: Retained for narrative completeness  
**Purpose**: Storytelling and explaining the original hackathon concept  
**What it demonstrates**: Coordination intelligence pipeline (conceptual)

**This demo is for context only. It does not prove privacy guarantees.**

---

## 🔴 PPSG Live Demo (RECOMMENDED FOR JUDGES)

### What This Demo Proves

The PPSG Live Demo demonstrates that KULIMA OS:

1. ✅ **Accepts coordination signals without identity**
   - No accounts, no authentication, no persistent identifiers

2. ✅ **Architecturally refuses PII**
   - Phone numbers, GPS coordinates, device IDs are rejected at ingestion
   - Rejection is automatic, not policy-based

3. ✅ **Enforces Temporal Moat**
   - 6-hour batch windows prevent real-time surveillance
   - No streaming, no event-by-event correlation

4. ✅ **Applies anti-gaming defenses**
   - Volume dampening (logarithmic weighting)
   - Pattern entropy detection
   - Cross-source validation

5. ✅ **Guarantees raw signal deletion**
   - Signals deleted after batch handoff
   - No archival, no recovery, no reconstruction

**This demo proves refusal, not just capability.**

---

## Running the PPSG Live Demo

### Option 1: One-Click Launcher (Windows)

**Easiest method for demonstrations:**

1. Double-click `start_ppsg_demo.bat` in the repository root
2. Wait for the gateway to start
3. Open your browser to `http://localhost:8000/docs`
4. Follow the on-screen instructions

The launcher will:
- Check dependencies and install if needed
- Start the PPSG gateway
- Display clear demo instructions
- Provide example signals to test

### Option 2: Manual Start (All Platforms)

```bash
# Navigate to ppsg directory
cd ppsg

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the gateway
python -m gateway
```

Then open `http://localhost:8000/docs` in your browser.

---

## Demo Scenarios

### Scenario A: Valid Signal Acceptance

**Purpose**: Prove the system accepts coordination signals without identity.

**Action**: Submit this signal via Swagger UI (`POST /signal/submit`):

```json
{
  "activity_type": "irrigation",
  "time_window": "morning",
  "zone_id": "zone_a",
  "signal_source_type": "human"
}
```

**Expected Result**: `202 Accepted` with batch window timestamp

**What this proves**:
- No authentication required
- No user ID or account needed
- Signal queued for batch processing

---

### Scenario B: PII Rejection (GPS Coordinates)

**Purpose**: Prove the system architecturally refuses PII.

**Action**: Submit this signal with GPS coordinates:

```json
{
  "activity_type": "irrigation",
  "time_window": "morning",
  "zone_id": "-1.286389,36.817223",
  "signal_source_type": "human"
}
```

**Expected Result**: `400 Bad Request` - GPS coordinates detected and rejected

**What this proves**:
- PII detection is automatic
- Rejection happens at ingestion
- No PII can enter the system

---

### Scenario C: Extra Field Rejection

**Purpose**: Prove strict schema enforcement (only four fields allowed).

**Action**: Submit this signal with an extra field:

```json
{
  "activity_type": "irrigation",
  "time_window": "morning",
  "zone_id": "zone_a",
  "signal_source_type": "human",
  "user_id": "user123"
}
```

**Expected Result**: `422 Unprocessable Entity` - Extra field rejected

**What this proves**:
- Schema is strict (no additional fields)
- No identity fields can be added
- System fails CLOSED (rejects by default)

---

### Scenario D: Volume Amplification Defense

**Purpose**: Prove anti-gaming mechanisms work without identity tracking.

**Action**: Submit 100 identical signals rapidly (use a script or Swagger UI "Try it out" repeatedly).

**Expected Behavior**:
- Signals are deduplicated within batch window
- Logarithmic dampening applied: 100 signals → weight ~4.6 (not 100)
- No individual tracking occurs

**What this proves**:
- Volume amplification attacks are resisted
- Anti-gaming works without identity
- System cannot be gamed by repetition

---

### Scenario E: Health Check (No Sensitive Data)

**Purpose**: Prove operational metrics contain no sensitive data.

**Action**: Call `GET /health`

**Expected Result**:
```json
{
  "status": "healthy",
  "buffer_size": 42,
  "last_batch_handoff": "2026-05-04T06:00:00Z"
}
```

**What this proves**:
- Only operational metrics exposed
- No signal content
- No individual identifiers
- No behavioral data

---

### Scenario F: Zone Whitelist (Public Information)

**Purpose**: Prove zone information is public and coarse.

**Action**: Call `GET /zones`

**Expected Result**:
```json
{
  "zones": [
    {"id": "zone_a", "type": "rural_agricultural"},
    {"id": "zone_b", "type": "peri_urban"},
    {"id": "zone_c", "type": "informal_settlement"}
  ]
}
```

**What this proves**:
- Zone IDs are coarse (not precise locations)
- Information is public (no privacy concerns)
- No individual geography exposed

---

## What the Demo Does NOT Show

The PPSG Live Demo intentionally does NOT demonstrate:

❌ **Individual tracking** (architecturally impossible)  
❌ **Real-time processing** (6-hour batch windows)  
❌ **Credit scoring** (no reputation metrics)  
❌ **Behavioral prediction** (no individual forecasting)  
❌ **Identity correlation** (no persistent identifiers)  

**These capabilities are architecturally impossible, not just disabled.**

---

## 🔵 Legacy Pilot Demo (Conceptual)

### Purpose

The legacy pilot demo (`run_demo.bat` / `run_demo.sh`) demonstrates the original hackathon concept: a coordination intelligence pipeline that processes signals through LUMOZA, LUNDAI, and ZENTARI engines to generate a Demand-Signal Prospectus.

**This demo is retained for narrative completeness but is NOT the authoritative proof of privacy guarantees.**

### Running the Legacy Demo

```bash
# Windows
run_demo.bat

# Mac/Linux
chmod +x run_demo.sh && ./run_demo.sh
```

### What It Demonstrates

- Coordination signal processing (7-cycle logic)
- Demand rhythm detection
- Infrastructure gap analysis
- Trust evaluation without reputation
- Prospectus generation

### Limitations

The legacy demo:
- Uses synthetic data (not live ingestion)
- Does not demonstrate PII rejection in real-time
- Does not prove anti-gaming defenses
- Is a script-based simulation, not a live gateway

**For proof of privacy guarantees, use the PPSG Live Demo.**

---

## For Hackathon Judges

### Evaluation Criteria

When evaluating KULIMA OS, prioritize the **PPSG Live Demo** because it demonstrates:

1. **Technical Achievement**: Coordination intelligence without surveillance
2. **Architectural Integrity**: Privacy enforced by design, not policy
3. **Audit-Readiness**: System can be verified externally
4. **Ethical Rigor**: Refusal is technically impossible to bypass
5. **Infrastructure-Grade**: Production-faithful reference implementation

### Key Questions the Demo Answers

✅ **Can coordination be visible without making people visible?**  
Yes. The PPSG accepts signals without identity.

✅ **Is privacy enforced architecturally or just by policy?**  
Architecturally. PII rejection is automatic and cannot be bypassed.

✅ **Can the system be gamed or manipulated?**  
No. Anti-gaming defenses work without identity tracking.

✅ **Is this surveillance infrastructure in disguise?**  
No. Real-time processing is architecturally impossible (6-hour batch windows).

✅ **Can this be audited externally?**  
Yes. All code is open, all invariants are testable.

---

## Technical Details

### System Invariants Enforced

The PPSG Live Demo enforces these non-negotiable constraints:

1. **Zero-PII**: No personal identifiers accepted or stored
2. **No Identity, Ever**: No accounts, authentication, or persistent IDs
3. **Temporal Moat**: 6-hour batch windows, no real-time processing
4. **Strict Schema**: Only four fields allowed, no extras
5. **Guaranteed Deletion**: Raw signals deleted after batch handoff

### Architecture

```
[Signal Sources]
    ↓
[Gateway API] → [PII Filter] → [Schema Validator] → [Zone Obfuscator]
    ↓
[Ephemeral Buffer] (TTL: 2 hours)
    ↓
[Anti-Gaming Layer] → [Batch Processor] → [LUMOZA Handoff]
    ↓
[Raw Signal Deletion] (guaranteed, irreversible)
```

### Reference Documentation

- **PPSG_SPECIFICATION.md**: Complete specification (1,089 lines)
- **ppsg/README.md**: Implementation documentation
- **ppsg/RELEASE_NOTES.md**: Frozen status declaration
- **SPECIFICATION.md**: KULIMA OS canonical specification

---

## Conclusion

**For hackathon judges and reviewers**: Use the **PPSG Live Demo** as the authoritative demonstration of KULIMA OS capabilities and constraints.

**For narrative context**: The legacy pilot demo provides storytelling value but does not prove privacy guarantees.

**This demo proves what the system refuses to do, not just what it can do.**

---

**KULIMA OS**: Coordination-first infrastructure for the informal economy  
**PPSG Version**: ppsg-reference-v1.0 (FROZEN)  
**Demo Status**: Audit-Ready, Reviewer-Friendly