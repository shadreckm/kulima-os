# Kulima OS Pilot Reference Implementation

**Version**: 0.1 (Minimal Viable Pilot)  
**Audience**: External evaluators (Youth4Climate, institutional partners, ethics reviewers)  
**Purpose**: Proof that coordination-based planning can operate ethically under real constraints

---

## Design Philosophy

This pilot is designed for **ethical restraint, auditability, and feasibility**—not completeness, scale, or optimization.

**Core Principle**: If a feature could enable surveillance, profiling, or individual tracking, it is excluded by design, not by policy.

---

## System Overview

The pilot consists of four components that operate in strict sequence:

1. **Signal Ingestion** (SMS/WhatsApp) → accepts only coordination signals, rejects everything else
2. **Weekly Batch Processor** → detects persistence patterns, discards noise
3. **Steward Review Loop** → exposes only aggregates, never individual inputs
4. **Prospectus Generator** → produces institutional-grade demand signals

**Data Flow**: Signals → Batches → Patterns → Prospectus  
**No Backflow**: Individual signals cannot be reconstructed from any downstream component.

---

## Component 1: Signal Ingestion (SMS/WhatsApp)

### What It Accepts

A valid coordination signal contains exactly four fields:

1. **Activity Type**: One of: `irrigation`, `milling`, `cold_storage`, `welding`, `clinic`, `school`, `water_system`
2. **Time Window**: One of: `morning`, `afternoon`, `evening`
3. **Zone**: General area identifier (e.g., `kasungu_west`, `zone_a`, `district_3`)
4. **Week Number**: Current week number (e.g., `week_1`, `week_2`, ... `week_7`)

**Example Valid Signal** (SMS format):
```
irrigation morning kasungu_west week_3
```

**Example Valid Signal** (WhatsApp format):
```
Activity: milling
Time: afternoon
Zone: zone_b
Week: week_5
```

### What It Rejects

The ingestion layer **immediately rejects and discards** any input containing:

- Phone numbers or device identifiers
- Names or personal identifiers
- GPS coordinates or precise locations
- Timestamps (beyond week number)
- Participant counts or individual references
- Any metadata not explicitly listed above

**Rejection is silent**: No error messages are sent back. Invalid inputs are discarded at the transport layer and never enter the system.

### How It Works

**Step 1: Transport Layer Stripping**

When a message arrives via SMS or WhatsApp:
- The system extracts only the four valid fields
- All transport metadata (sender ID, timestamp, device info) is discarded immediately
- No logs are kept of who sent what or when (beyond week number)

**Step 2: Validation**

The extracted fields are validated:
- Activity type must match allowed list
- Time window must be morning/afternoon/evening
- Zone must be a registered general area (not a precise location)
- Week number must be current evaluation period (1-7)

**Step 3: Anonymization**

Valid signals are written to a weekly batch file as:
```json
{
  "activity": "irrigation",
  "time_window": "morning",
  "zone": "kasungu_west",
  "week": 3
}
```

**No other data is stored.** The signal is now completely anonymous and cannot be traced back to any individual.

### Implementation Notes

**SMS Gateway**: Use a simple SMS API (e.g., Africa's Talking, Twilio) that accepts incoming messages and forwards only the message body to the ingestion script. Configure the gateway to NOT store sender information.

**WhatsApp**: Use WhatsApp Business API with a webhook that extracts message content only. Do not store chat history or sender metadata.

**Paper Facilitation**: Community facilitators can collect signals on paper forms and batch-enter them weekly. The form contains only the four fields. No names or identifiers are recorded.

**Bandwidth**: A single coordination signal is ~50 bytes. A week's worth of signals from 100 participants is ~5KB—easily transmitted over 2G or SMS.

---

## Component 2: Weekly Batch Processor

### What It Does

At the end of each week, the batch processor:

1. Groups all signals by `(activity, time_window, zone)`
2. Counts how many weeks each pattern has appeared (out of 7 weeks)
3. Calculates a persistence score
4. Discards one-off or noisy patterns
5. Outputs only stable coordination patterns

### Persistence Detection

A coordination pattern is considered **stable** if it appears in **5 or more of the 7 weeks**.

**Example**:
- Week 1: `irrigation morning kasungu_west` (3 signals)
- Week 2: `irrigation morning kasungu_west` (5 signals)
- Week 3: `irrigation morning kasungu_west` (4 signals)
- Week 4: `irrigation morning kasungu_west` (6 signals)
- Week 5: `irrigation morning kasungu_west` (0 signals) ← absent
- Week 6: `irrigation morning kasungu_west` (5 signals)
- Week 7: `irrigation morning kasungu_west` (4 signals)

**Result**: Pattern appeared in 6 of 7 weeks → **Stable** (persistence score: 0.86)

### Noise Filtering

Patterns that appear in **fewer than 3 weeks** are automatically discarded as noise. They do not appear in any output.

**Example**:
- `welding evening zone_b` appears in weeks 2 and 5 only → **Discarded** (noise)

### Coordination Confidence Score

For stable patterns, the processor calculates a confidence score:

```
confidence = (weeks_present / 7) × (avg_signals_per_week / 10)
```

**Interpretation**:
- **0.7 - 1.0**: High confidence (bankable for infrastructure planning)
- **0.5 - 0.69**: Medium confidence (monitor for another cycle)
- **Below 0.5**: Low confidence (not yet actionable)

### Output Format

The batch processor outputs a JSON file containing only aggregated patterns:

```json
{
  "evaluation_period": "2026-W01 to 2026-W07",
  "patterns": [
    {
      "pattern_id": "kasungu_west_irrigation_morning",
      "activity": "irrigation",
      "time_window": "morning",
      "zone": "kasungu_west",
      "weeks_present": 6,
      "total_weeks": 7,
      "avg_signals_per_week": 4.5,
      "persistence_score": 0.86,
      "confidence": 0.77,
      "classification": "stable"
    },
    {
      "pattern_id": "zone_b_milling_afternoon",
      "activity": "milling",
      "time_window": "afternoon",
      "zone": "zone_b",
      "weeks_present": 5,
      "total_weeks": 7,
      "avg_signals_per_week": 3.2,
      "persistence_score": 0.71,
      "confidence": 0.45,
      "classification": "stable"
    }
  ]
}
```

**Critical**: Individual signals are never included in this output. Only aggregated patterns.

### Implementation Notes

**Processing Schedule**: Run the batch processor once per week, on a fixed day (e.g., every Sunday at midnight).

**Storage**: Weekly batch files are kept for the current 7-week evaluation period only. After a new cycle begins, old batch files are archived (not deleted, for audit purposes) but never re-processed.

**No Real-Time**: The processor does not run continuously. It runs once per week, in batch mode.

---

## Component 3: Steward Review Loop

### Purpose

Before patterns are used to generate a prospectus, a human steward reviews the aggregated patterns to ensure:

1. Patterns make sense for the zone (e.g., irrigation in an agricultural area)
2. No anomalies suggest gaming or fabricated signals
3. Essential services (clinic, school, water system) are correctly classified

### What Stewards See

Stewards are shown only the aggregated pattern output from the batch processor (see JSON above). They **never** see:

- Individual signals
- Who sent signals or when
- Raw batch files
- Any data that could identify participants

### Review Interface

A simple web interface or spreadsheet displays:

| Pattern ID | Activity | Time | Zone | Weeks Present | Confidence | Status |
|------------|----------|------|------|---------------|------------|--------|
| kasungu_west_irrigation_morning | irrigation | morning | kasungu_west | 6/7 | 0.77 | Pending |
| zone_b_milling_afternoon | milling | afternoon | zone_b | 5/7 | 0.45 | Pending |

Stewards can:
- **Approve**: Pattern is valid and should be included in prospectus
- **Reject**: Pattern seems anomalous or fabricated (e.g., irrigation in a non-agricultural zone)
- **Flag for Next Cycle**: Pattern is borderline; monitor for another 7 weeks

### Rejection Criteria

Stewards reject patterns if:
- Activity type doesn't match known zone characteristics (e.g., irrigation in urban zone)
- Confidence score is suspiciously high with very few signals (possible gaming)
- Pattern contradicts known infrastructure constraints (e.g., cold storage where no electricity exists)

**Important**: Rejection does not penalize participants. It simply excludes the pattern from the current prospectus. If the pattern persists in the next cycle, it can be re-evaluated.

### Implementation Notes

**Steward Training**: Stewards must understand that they are reviewing patterns, not people. They should be trained to recognize anomalies without making assumptions about individual behavior.

**Audit Trail**: All steward decisions (approve/reject/flag) are logged with a timestamp and reason. This creates an audit trail for external reviewers.

**No Override**: Stewards cannot modify patterns or add data. They can only approve or reject what the batch processor outputs.

---

## Component 4: Demand-Signal Prospectus Generator (v0)

### Purpose

Generate a plain-language document that institutional decision-makers (utilities, financiers, policymakers) can use to plan infrastructure investment.

### Input

The prospectus generator receives only:
- Approved patterns from the steward review loop
- Zone metadata (settlement type, infrastructure status, distance to grid)
- Essential service classification (clinic, school, water system)

### Output Structure

The prospectus is a Markdown or PDF document containing:

#### 1. Executive Summary
- Number of stable coordination patterns detected
- Zones with highest coordination confidence
- Recommended infrastructure investments

#### 2. Coordination Rhythms
For each approved pattern:
- Activity type and time window
- Persistence score (how reliably it repeats)
- Confidence score (how bankable it is)
- Plain-language interpretation

**Example**:
```
Pattern: Irrigation (Morning) - Kasungu West
- Appeared in 6 of 7 weeks
- Average 4-5 coordination signals per week
- Confidence: 0.77 (High)
- Interpretation: Stable morning irrigation demand exists in Kasungu West. 
  Infrastructure should provide reliable power during morning hours (6am-10am) 
  for water pumping. Estimated capacity: 15-20kW.
```

#### 3. Infrastructure Gaps
For each zone with stable patterns:
- Current infrastructure status (grid-connected, off-grid, no power)
- Distance to nearest substation or transformer
- Gap severity (critical, moderate, minimal)

**Example**:
```
Zone: Kasungu West
- Current Status: Off-grid (diesel generators)
- Distance to Grid: 12km from nearest substation
- Gap Severity: Critical
- Recommendation: Extend distribution line to serve coordinated irrigation demand
```

#### 4. Critical Load Protection
For zones with essential services:
- Percentage of capacity reserved for clinic, school, water system
- Justification based on detected essential service patterns

**Example**:
```
Zone: Kasungu West
- Essential Services Detected: Clinic (morning), School (morning/afternoon), Water System (all day)
- Reserved Capacity: 25% (minimum 10kW)
- Justification: Essential services show stable coordination patterns and must be 
  protected from load-shedding or commercial optimization.
```

#### 5. Coordination Confidence Summary
- Overall confidence score for the zone
- Bankability assessment (high/medium/low)
- Recommendation for institutional action

**Example**:
```
Zone: Kasungu West
- Overall Confidence: 0.75 (High)
- Bankability: High - Patterns are stable, validated, and persistent
- Recommendation: Proceed with infrastructure investment. Demand signal is 
  trustworthy and sufficient for financial planning.
```

### Implementation Notes

**Template-Based**: Use a Markdown template with placeholders for pattern data. This makes the prospectus easy to generate and audit.

**Plain Language**: Avoid technical jargon. Write for utility managers and financiers who may not understand coordination theory.

**No Individual Data**: The prospectus contains only aggregated patterns and zone-level analysis. It is impossible to reconstruct individual signals from the prospectus.

**Version Control**: Each prospectus is versioned and timestamped. If patterns change in the next evaluation cycle, a new prospectus is generated. Old versions are archived for audit.

---

## What This Pilot Does NOT Solve

This minimal pilot intentionally excludes:

1. **Real-Time Processing**: No streaming, no live dashboards, no instant updates. Everything is batch-processed weekly.

2. **Telemetry Validation**: No cross-validation with infrastructure telemetry (pump meters, mill sensors). This would require hardware integration and is deferred to future versions.

3. **Spatial Analysis (LUNDAI)**: No settlement mapping, no infrastructure topology analysis. Zone metadata is manually entered, not computed.

4. **Multi-Cycle Trust Evolution (ZENTARI)**: No tracking of how patterns evolve across multiple 7-week cycles. Each cycle is evaluated independently.

5. **Automated Capacity Planning**: No algorithmic calculation of required kW capacity. Capacity estimates are provided as guidance, not precise engineering specs.

6. **Fraud Detection**: No sophisticated anti-gaming mechanisms beyond steward review. Trust is derived from persistence, not from cryptographic proofs.

7. **Multi-Language Support**: Pilot assumes English or a single local language. Translation is manual.

8. **Mobile App**: No smartphone app. Signals are submitted via SMS, WhatsApp, or paper forms.

9. **API Integration**: No REST API for external systems. Prospectus is generated as a static document.

10. **Scalability**: Pilot is designed for 1-3 zones with <500 signals per week. Scaling to hundreds of zones requires architectural changes.

---

## What Future Versions Could Add

Without designing them now, future versions could explore:

1. **Telemetry Corroboration**: Cross-validate human signals with infrastructure telemetry to strengthen confidence scores.

2. **Multi-Cycle Tracking**: Track how patterns evolve across multiple 7-week cycles to measure coordination resilience.

3. **Spatial Intelligence (LUNDAI)**: Integrate settlement mapping and infrastructure topology analysis to identify gaps automatically.

4. **Automated Capacity Planning**: Use historical energy use data to calculate precise kW requirements for each pattern.

5. **Anti-Gaming Mechanisms**: Implement statistical anomaly detection to flag suspicious patterns without tracking individuals.

6. **Multi-Zone Coordination**: Detect when patterns coordinate across multiple zones (e.g., regional market days).

7. **Seasonal Patterns**: Extend evaluation periods to detect seasonal rhythms (planting, harvest, dry season).

8. **API for Institutional Systems**: Provide a read-only API for utilities and financiers to query prospectus data.

9. **Mobile App for Facilitators**: Build a simple app for community facilitators to batch-enter signals more efficiently.

10. **Audit Dashboard**: Create a web interface for external auditors to verify that no PII exists in the system.

---

## Ethical Constraints (Non-Negotiable)

These constraints apply to this pilot and all future versions:

1. **Zero PII**: No personal identifiers may ever enter the system. This is architecturally enforced, not policy-based.

2. **Batch-Only Processing**: No real-time processing. All signals are batched weekly.

3. **Trust from Persistence**: Trust is derived from coordination patterns repeating over time, never from identity, reputation, or authentication.

4. **No Reconstruction**: Individual signals cannot be reconstructed from any downstream component (patterns, prospectus, audit logs).

5. **Steward Oversight**: Human stewards review aggregated patterns before they are used for institutional decision-making.

6. **Audit Transparency**: External auditors can verify that no PII exists and that patterns are derived from genuine coordination, not fabricated data.

---

## Implementation Checklist

To deploy this pilot, you need:

### Infrastructure
- [ ] SMS gateway (Africa's Talking, Twilio) or WhatsApp Business API
- [ ] Simple server (can be a laptop or Raspberry Pi) to run batch processor
- [ ] Spreadsheet or basic web interface for steward review
- [ ] Markdown-to-PDF converter for prospectus generation

### Data
- [ ] List of valid activity types (irrigation, milling, etc.)
- [ ] List of valid zones (kasungu_west, zone_a, etc.)
- [ ] Zone metadata (settlement type, infrastructure status)

### People
- [ ] 1-2 trained stewards who understand coordination patterns
- [ ] Community facilitators (optional, for paper-based signal collection)
- [ ] Institutional partner (utility or development finance institution) to receive prospectus

### Timeline
- **Week 0**: Set up SMS gateway, configure batch processor
- **Weeks 1-7**: Collect coordination signals
- **Week 8**: Run batch processor, steward review, generate prospectus
- **Week 9**: Deliver prospectus to institutional partner, gather feedback

---

## Success Criteria

This pilot is successful if:

1. **Zero PII**: External auditors confirm that no personal identifiers exist in the system.

2. **Stable Patterns Detected**: At least 2-3 stable coordination patterns are identified across 7 weeks.

3. **Steward Confidence**: Stewards can review patterns and make approve/reject decisions without seeing individual signals.

4. **Institutional Legibility**: Utility or financier can read the prospectus and understand what infrastructure is needed, where, and why.

5. **Ethical Restraint**: No feature creep toward surveillance, profiling, or individual tracking.

---

## Conclusion

This pilot is designed to prove one thing: **Coordination-based planning can operate ethically under real constraints.**

It is not complete. It is not scalable. It is not optimized. But it is **auditable, feasible, and ethically restrained**.

If this pilot succeeds, it demonstrates that informal economies can become institution-readable without extraction, surveillance, or profiling. That is the only goal.

---

**Document Version**: 0.1  
**Status**: Pilot Reference Design  
**Last Updated**: 2026-05-05  
**Maintained By**: Kulima OS Stewardship Team