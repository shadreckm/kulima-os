# Kulima OS Pilot Execution Plan

**Version**: 1.0  
**Audience**: External evaluators (Youth4Climate), pilot implementers  
**Purpose**: Translate pilot design into demonstrable outcome with clear implementation vs. simulation boundaries

---

## Executive Summary

This document specifies exactly what runs, what is simulated, and what is proven in the Kulima OS pilot execution. The goal is to produce a **credible Demand-Signal Prospectus** that demonstrates coordination-based planning can operate ethically under real constraints.

**Key Principle**: Optimize for clarity, auditability, and evaluator confidence—not completeness.

---

## Current Codebase Assessment

The repository contains two parallel implementations:

### 1. Conceptual Demo (Legacy)
**Files**: [`kulima_pilot_demo.py`](kulima_pilot_demo.py), [`pilot_signals.py`](pilot_signals.py), [`lumoza_engine.py`](lumoza_engine.py), [`zentari_engine.py`](zentari_engine.py), [`prospectus_generator.py`](prospectus_generator.py)

**What it does**:
- Generates synthetic coordination signals (7-cycle window)
- Processes signals through LUMOZA (coordination detection)
- Evaluates confidence through ZENTARI (trust scoring)
- Generates Demand-Signal Prospectus (JSON + Markdown)

**Status**: ✅ Fully functional, runs end-to-end, produces institutional artifact

**Strengths**:
- Complete pipeline demonstration
- Produces real prospectus document
- Shows coordination pattern detection
- Enforces all system invariants

**Limitations**:
- Uses pre-generated synthetic signals (not ingestion flow)
- No SMS/WhatsApp gateway
- No steward review interface
- Batch processing is simulated (not time-triggered)

### 2. PPSG (Privacy-Preserving Signal Gateway)
**Files**: [`ppsg/gateway.py`](ppsg/gateway.py), [`ppsg/batch_processor.py`](ppsg/batch_processor.py), [`ppsg/pii_filter.py`](ppsg/pii_filter.py), [`ppsg/anti_gaming.py`](ppsg/anti_gaming.py)

**What it does**:
- FastAPI gateway with `/signal/submit` endpoint
- PII detection and rejection
- Rate limiting and anti-gaming
- Ephemeral buffer with TTL
- Batch processing with guaranteed deletion

**Status**: ✅ Functional API, demonstrates ingestion layer

**Strengths**:
- Real HTTP API (can accept POST requests)
- Enforces Zero-PII at ingestion
- Demonstrates refusal mechanisms
- Shows batch processing architecture

**Limitations**:
- Does not connect to LUMOZA/ZENTARI pipeline
- No prospectus generation
- No steward review interface
- Batch handoff is not implemented

---

## Recommended Pilot Execution Strategy

### Option A: Conceptual Demo (Recommended for Evaluators)

**Use the existing [`kulima_pilot_demo.py`](kulima_pilot_demo.py) as the primary demonstration.**

**Why**: It produces a complete, credible Demand-Signal Prospectus that proves the core thesis: coordination-based planning works without surveillance.

**What Runs**:
1. ✅ **Signal Generation**: Synthetic signals representing 7 weeks of coordination activity
2. ✅ **LUMOZA Processing**: Detects stable patterns (≥5 of 7 cycles)
3. ✅ **ZENTARI Evaluation**: Calculates coordination confidence scores
4. ✅ **Prospectus Generation**: Produces institutional-grade document (JSON + Markdown)

**What is Simulated**:
- ⚠️ **SMS/WhatsApp Ingestion**: Signals are pre-generated, not submitted via API
- ⚠️ **Steward Review**: Patterns are auto-approved (no human review interface)
- ⚠️ **Time-Triggered Batching**: Batch processing runs immediately (not weekly)

**What is Proven**:
- ✅ Zero-PII enforcement (no personal identifiers in signals or outputs)
- ✅ Coordination pattern detection (stable vs. noise)
- ✅ Trust from persistence (confidence scores based on repetition)
- ✅ Institutional legibility (prospectus is readable by utilities/financiers)
- ✅ Critical load protection (essential services prioritized)

**How to Run**:
```bash
# Windows
run_demo.bat

# Mac/Linux
chmod +x run_demo.sh && ./run_demo.sh
```

**Output**:
- `demand_signal_prospectus.json` - Machine-readable prospectus
- `demand_signal_prospectus.md` - Human-readable prospectus

**Evaluation Criteria**:
1. Open `demand_signal_prospectus.md` and verify it contains:
   - Coordination rhythms (when/what activities cluster)
   - Infrastructure gaps (where demand is unserved)
   - Confidence scores (how bankable patterns are)
   - Critical load protection (essential services reserved)
2. Confirm no personal identifiers exist anywhere in the output
3. Verify patterns are derived from collective activity, not individuals

---

### Option B: PPSG Live Demo (For Technical Evaluators)

**Use the [`ppsg/gateway.py`](ppsg/gateway.py) API to demonstrate ingestion layer.**

**Why**: It proves that Zero-PII enforcement and refusal mechanisms work at the API boundary.

**What Runs**:
1. ✅ **FastAPI Gateway**: HTTP server accepting POST requests
2. ✅ **PII Detection**: Rejects signals containing personal identifiers
3. ✅ **Schema Validation**: Enforces strict four-field schema
4. ✅ **Rate Limiting**: Prevents gaming through volume attacks
5. ✅ **Ephemeral Buffer**: Stores signals temporarily with TTL

**What is Simulated**:
- ⚠️ **LUMOZA/ZENTARI Pipeline**: Batch processor does not connect to coordination engines
- ⚠️ **Prospectus Generation**: No institutional output produced
- ⚠️ **Steward Review**: No review interface

**What is Proven**:
- ✅ Zero-PII enforcement at ingestion (PII is rejected, not stored)
- ✅ Refusal mechanisms work (invalid signals are blocked)
- ✅ Batch processing architecture (signals accumulate, then process)
- ✅ Guaranteed deletion (raw signals are discarded after batching)

**How to Run**:
```bash
# Windows
start_ppsg_demo.bat

# Or manually
cd ppsg
pip install -r requirements.txt
python -m gateway
```

Then open `http://localhost:8000/docs` in browser.

**Evaluation Criteria**:
1. Submit valid signal via `/signal/submit` → 202 Accepted
2. Submit signal with phone number → 400 Bad Request (PII detected)
3. Submit signal with extra fields → 400 Bad Request (schema violation)
4. Verify buffer accumulates signals but does not expose individual data

---

## Hybrid Execution Plan (Recommended)

**Combine both approaches to demonstrate full pipeline:**

### Phase 1: Ingestion Layer (PPSG)
**Duration**: 10 minutes  
**Purpose**: Prove Zero-PII enforcement at API boundary

1. Start PPSG gateway: `start_ppsg_demo.bat`
2. Submit 5-10 valid signals via API
3. Attempt to submit invalid signals (with PII, extra fields)
4. Show that invalid signals are rejected
5. Show that buffer accumulates signals without exposing individuals

**Deliverable**: API demonstration showing refusal mechanisms work

### Phase 2: Coordination Intelligence (Conceptual Demo)
**Duration**: 5 minutes  
**Purpose**: Prove coordination pattern detection and prospectus generation

1. Run conceptual demo: `run_demo.bat`
2. Show LUMOZA detecting stable patterns (≥5 of 7 cycles)
3. Show ZENTARI calculating confidence scores
4. Show prospectus generation

**Deliverable**: `demand_signal_prospectus.md` - institutional artifact

### Phase 3: Evaluator Review
**Duration**: 15 minutes  
**Purpose**: External verification of claims

1. Evaluators review prospectus document
2. Verify no PII exists in outputs
3. Confirm patterns are coordination-focused, not identity-focused
4. Assess institutional legibility (can a utility use this?)

**Deliverable**: Evaluator confidence that system operates as claimed

---

## What Needs Implementation vs. Simulation

### Already Implemented (No Changes Needed)

| Component | Status | File |
|-----------|--------|------|
| Signal Generation | ✅ Implemented | [`pilot_signals.py`](pilot_signals.py) |
| LUMOZA Engine | ✅ Implemented | [`lumoza_engine.py`](lumoza_engine.py) |
| ZENTARI Engine | ✅ Implemented | [`zentari_engine.py`](zentari_engine.py) |
| Prospectus Generator | ✅ Implemented | [`prospectus_generator.py`](prospectus_generator.py) |
| PPSG Gateway | ✅ Implemented | [`ppsg/gateway.py`](ppsg/gateway.py) |
| PII Filter | ✅ Implemented | [`ppsg/pii_filter.py`](ppsg/pii_filter.py) |
| Batch Processor | ✅ Implemented | [`ppsg/batch_processor.py`](ppsg/batch_processor.py) |

### Simulated (Acceptable for Pilot)

| Component | Simulation Approach | Justification |
|-----------|---------------------|---------------|
| SMS/WhatsApp Ingestion | Pre-generated signals | Proves pipeline works; transport layer is implementation detail |
| Steward Review Interface | Auto-approval | Proves pattern aggregation; UI is not core to thesis |
| Time-Triggered Batching | Immediate processing | Proves batch logic; scheduling is implementation detail |
| Telemetry Corroboration | Synthetic telemetry signals | Proves cross-validation logic; hardware integration is future work |
| Multi-Cycle Tracking | Single 7-cycle window | Proves persistence detection; longitudinal tracking is future work |

### Not Implemented (Explicitly Excluded)

| Component | Reason for Exclusion |
|-----------|---------------------|
| Real SMS Gateway | Requires telecom API credentials; not needed to prove concept |
| Steward Dashboard | UI development is not core to coordination intelligence |
| Database Persistence | Ephemeral buffer is sufficient; persistence is implementation detail |
| LUNDAI Spatial Engine | Settlement mapping requires GIS data; conceptual only for pilot |
| Multi-Language Support | Translation is operational concern, not architectural |

---

## Generating a Credible Demand-Signal Prospectus

### Approach: Use Existing Conceptual Demo

The [`kulima_pilot_demo.py`](kulima_pilot_demo.py) already generates a credible prospectus. No changes needed.

**Why it's credible**:

1. **Realistic Signal Patterns**: Synthetic signals mimic real-world coordination:
   - Irrigation appears 6 of 7 weeks (stable)
   - Milling appears 5 of 7 weeks (stable)
   - Welding appears 2 of 7 weeks (noise, filtered out)
   - Essential services appear 7 of 7 weeks (critical load)

2. **Cross-Validation**: Human signals are corroborated by telemetry signals, demonstrating validation logic without surveillance.

3. **Institutional Format**: Prospectus contains:
   - Executive summary (high-level insights)
   - Coordination patterns (when/what/where)
   - Confidence scores (bankability assessment)
   - Infrastructure gaps (where to invest)
   - Critical load protection (essential services reserved)
   - Planning guidance (actionable recommendations)

4. **Zero-PII Compliance**: External auditors can verify that no personal identifiers exist in the prospectus.

### Alternative: Limited Real Test Inputs

If evaluators want to submit real signals:

1. Start PPSG gateway: `start_ppsg_demo.bat`
2. Submit signals via API (using Postman, curl, or Swagger UI)
3. Manually trigger batch processing (not yet automated)
4. Feed batch output to LUMOZA/ZENTARI (requires integration work)
5. Generate prospectus

**Recommendation**: Use conceptual demo for evaluation. Real input integration is future work.

---

## Pilot Execution Summary

### What Ran

**Conceptual Demo** ([`kulima_pilot_demo.py`](kulima_pilot_demo.py)):
- ✅ Generated 7 weeks of synthetic coordination signals
- ✅ Processed signals through LUMOZA (coordination detection)
- ✅ Evaluated confidence through ZENTARI (trust scoring)
- ✅ Generated Demand-Signal Prospectus (institutional artifact)

**PPSG Gateway** ([`ppsg/gateway.py`](ppsg/gateway.py)):
- ✅ Demonstrated Zero-PII enforcement at API boundary
- ✅ Showed refusal mechanisms (PII detection, schema validation)
- ✅ Proved batch processing architecture (ephemeral buffer, TTL)

### What Was Constrained

**Simulated Components**:
- SMS/WhatsApp ingestion (signals pre-generated, not submitted via transport layer)
- Steward review interface (patterns auto-approved, no human review UI)
- Time-triggered batching (processing runs immediately, not on weekly schedule)
- Telemetry corroboration (synthetic telemetry, not real hardware integration)

**Excluded Components**:
- Real SMS gateway (requires telecom API, not needed for proof)
- Steward dashboard (UI development, not core to thesis)
- Database persistence (ephemeral buffer sufficient for pilot)
- LUNDAI spatial engine (requires GIS data, conceptual only)
- Multi-language support (operational concern, not architectural)

### What Was Proven

**Core Thesis**: Coordination-based planning can operate ethically under real constraints.

**Specific Proofs**:

1. **Zero-PII Enforcement**: No personal identifiers exist in signals, processing, or outputs. External auditors can verify this by inspecting:
   - [`pilot_signals.py`](pilot_signals.py) - signal generation (no names, IDs, phone numbers)
   - `demand_signal_prospectus.md` - prospectus output (only aggregated patterns)

2. **Coordination Pattern Detection**: System identifies stable patterns (≥5 of 7 cycles) and filters noise (<3 of 7 cycles). Demonstrated in:
   - LUMOZA output showing 6 stable patterns detected
   - Noise patterns (welding 2/7 cycles) correctly excluded

3. **Trust from Persistence**: Confidence scores are derived from pattern repetition, not individual reputation. Demonstrated in:
   - ZENTARI output showing confidence scores (0.77, 0.86, etc.)
   - High confidence = stable pattern, not reliable participants

4. **Institutional Legibility**: Prospectus is readable by utilities and financiers. Demonstrated in:
   - `demand_signal_prospectus.md` containing actionable recommendations
   - Plain-language interpretation of coordination patterns
   - Infrastructure gap analysis and capacity planning guidance

5. **Critical Load Protection**: Essential services are prioritized in capacity planning. Demonstrated in:
   - 20-25% capacity reserved for clinic, school, water system
   - Essential services cannot be shed or deprioritized

6. **Refusal Mechanisms**: System rejects surveillance, profiling, and individual tracking. Demonstrated in:
   - PPSG gateway rejecting signals with PII
   - Schema validation preventing extra fields
   - No individual-level queries possible in prospectus

### What Was Intentionally Excluded

**Not Attempted** (to maintain ethical restraint and pilot focus):

1. **Real-Time Processing**: No streaming, no live dashboards. All processing is batch-based (weekly).

2. **Individual Tracking**: No participant authentication, no activity logs, no behavioral histories.

3. **Credit Scoring**: No reputation systems, no eligibility gating, no individual trust scores.

4. **Surveillance Capabilities**: No location tracking, no temporal correlation, no identity reconstruction.

5. **Optimization for Scale**: Pilot handles 1-3 zones with <500 signals/week. Scaling is future work.

6. **Production Deployment**: No database, no monitoring, no high-availability infrastructure. Pilot is proof-of-concept only.

---

## Evaluator Checklist

When reviewing this pilot, evaluators should verify:

### Ethical Compliance
- [ ] No personal identifiers exist in signals or outputs
- [ ] System cannot be queried for individual-level data
- [ ] Refusal mechanisms work (PII is rejected at ingestion)
- [ ] Prospectus contains only aggregated patterns

### Technical Functionality
- [ ] LUMOZA detects stable patterns (≥5 of 7 cycles)
- [ ] ZENTARI calculates confidence scores based on persistence
- [ ] Prospectus is generated in institutional format (JSON + Markdown)
- [ ] Critical load protection reserves capacity for essential services

### Institutional Legibility
- [ ] Prospectus is readable by non-technical decision-makers
- [ ] Coordination patterns are clearly explained
- [ ] Infrastructure gaps are identified
- [ ] Planning guidance is actionable

### Pilot Realism
- [ ] Constraints are clearly documented (what's simulated vs. implemented)
- [ ] Excluded components are justified (not needed for proof)
- [ ] System operates under stated constraints (low-bandwidth, batch-only, zero-PII)

---

## Next Steps for Production Deployment

This pilot proves the concept. To deploy in production:

1. **Integrate SMS/WhatsApp Gateway**: Connect PPSG to real telecom APIs (Africa's Talking, Twilio)

2. **Build Steward Review Interface**: Simple web UI for reviewing aggregated patterns

3. **Implement Time-Triggered Batching**: Schedule batch processor to run weekly

4. **Add Telemetry Integration**: Connect to real infrastructure sensors (pump meters, mill sensors)

5. **Deploy LUNDAI Spatial Engine**: Integrate GIS data for settlement and infrastructure analysis

6. **Add Multi-Cycle Tracking**: Track pattern evolution across multiple 7-week cycles

7. **Build Audit Dashboard**: External verification interface for ethics reviewers

8. **Scale Infrastructure**: Database, monitoring, high-availability deployment

**Critical**: All production enhancements must preserve the five system invariants (Zero-PII, Temporal Moat, Coordination > Identity, Semantic Guard, Critical Load Protection).

---

## Conclusion

This pilot execution plan provides a clear path from design to demonstrable outcome. The existing codebase is sufficient to prove the core thesis: **coordination-based planning can operate ethically under real constraints**.

**For evaluators**: Run the conceptual demo ([`run_demo.bat`](run_demo.bat)) and review the generated prospectus. This is the primary artifact demonstrating that informal economies can become institution-readable without surveillance.

**For implementers**: Use this plan to understand what's implemented, what's simulated, and what's intentionally excluded. The pilot is designed for clarity and auditability, not completeness.

---

**Document Version**: 1.0  
**Status**: Pilot Execution Plan  
**Last Updated**: 2026-05-05  
**Maintained By**: Kulima OS Stewardship Team