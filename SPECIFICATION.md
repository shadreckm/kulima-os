# Kulima OS – Coordination Substrate Specification (Canonical)

**Version**: 1.0  
**Status**: Frozen specification – future changes require institutional ethics review  
**Date**: 2026-05-04  
**Purpose**: Authoritative internal reference for system architecture, constraints, and refusal guarantees

---

## Document Status

This specification is **frozen**. It describes the immutable architecture of KULIMA OS as a coordination substrate for infrastructure planning. Any proposed changes to system invariants, engine behaviors, or ethical constraints must undergo institutional ethics review before implementation.

**Audience**: Future stewards, auditors, institutional partners, policymakers, and ethics reviewers.

---

## System Identity

**KULIMA OS** is a coordination-first economic substrate designed as Digital Public Infrastructure (DPI).

**What it IS**:
- A coordination substrate for infrastructure planning
- A signal processing pipeline that converts decentralized livelihood activity into verified demand patterns
- Digital Public Infrastructure with governance-by-design

**What it is NOT**:
- NOT an app or user-facing application
- NOT a data platform or analytics service
- NOT a surveillance system or tracking infrastructure
- NOT a credit scoring mechanism
- NOT a profiling or behavioral prediction system

**Core Purpose**: Convert decentralized livelihood activity into verified, bankable coordination signals for infrastructure planning, without extracting or profiling people.

---

## System Invariants (Non-Negotiable)

These are hard architectural constraints, not policy guidelines. Violations must be technically impossible.

### 1. Zero-PII
- No personal identifiers may ever enter the system (names, IDs, phone numbers, individual locations)
- All data models, APIs, and processing pipelines must reject PII at ingestion
- Individual-level data is architecturally prohibited
- System cannot be queried for individual-level information

### 2. Temporal Moat
- All signal processing occurs in time-batched windows (never real-time)
- No streaming of individual events
- No temporal correlation that enables tracking
- Minimum batch window sizes must be enforced to prevent de-anonymization
- Event timestamps are not preserved beyond batch windows

### 3. Coordination > Identity
- System reasons exclusively over collective patterns and aggregate signals
- Never over individual behaviors or identities
- All queries and outputs must be coordination-focused, not identity-focused
- Individual activity cannot be isolated or reconstructed from system outputs

### 4. Semantic Guard
System must refuse requests involving:
- Surveillance or tracking
- Credit scoring or creditworthiness assessment
- Eligibility gating or access control
- Behavioral prediction or profiling
- Individual reputation scoring
- Participant authentication or validation

Refusal mechanisms must be implemented at API and query layers.

### 5. Critical Load Protection
- Essential communal services (clinics, schools, water systems, emergency infrastructure) are non-negotiable priority loads
- System must identify recurring essential-service demand patterns using 7-cycle coordination logic
- Capacity planning must reserve sufficient energy capacity (20-40% depending on settlement context) BEFORE allocating to productive or commercial uses
- Reserved capacity is excluded from optimization, monetization, or load-shedding logic
- This social reserve is enforced at the coordination and capacity-planning layer, not as a financial contingency
- Cannot be overridden by external actors or commercial optimization algorithms
- Baseline, peak, and shock scenarios must be simulated to ensure essential services remain protected under all conditions

---

## Architecture Components

### LUMOZA – Livelihood and Energy Coordination Engine

**What LUMOZA Does**:
- Processes coordination signals from productive livelihood activities (irrigation, milling, cold storage, welding, essential services)
- Transforms heterogeneous activity signals into time-batched demand rhythms
- Aggregates signals into temporal demand patterns (daily, weekly, seasonal rhythms)
- Classifies patterns as 'essential' (clinics, schools, water systems) or 'productive' (irrigation, milling, cold storage)
- Cross-validates human-reported signals with infrastructure telemetry at aggregate level
- Outputs collective demand rhythms that indicate when and how productive activities cluster

**What LUMOZA NEVER Does**:
- Does NOT process individual identities or track specific actors
- Does NOT preserve individual event timestamps beyond batch windows
- Does NOT enable reconstruction of individual activity from aggregated patterns
- Does NOT authenticate or validate individual participants
- Does NOT create individual-level profiles or histories

**Allowed Outputs**:
- Activity type (e.g., irrigation, milling)
- Time windows when activity clusters (e.g., Tuesday-Thursday mornings)
- Frequency of occurrence across evaluation cycles (e.g., 6 of 7 cycles)
- Zone identifier (general area, not precise location)
- Stability score (consistency metric)
- Validation score (alignment between human signals and telemetry)
- Service priority classification (essential vs. productive)

**Mandatory Refusals**:
- Individual activity logs or histories
- Participant-level validation status
- Real-time event streams
- Precise location coordinates
- Individual timestamps or sequences

**Scope Boundary**: LUMOZA operates exclusively on activity types and temporal patterns. It sees only the rhythm of collective economic activity—when irrigation happens, when milling peaks, when cold storage demand rises—without knowing who is doing these activities.

---

### LUNDAI – Spatial and Infrastructure Mismatch Engine

**What LUNDAI Does**:
- Analyzes infrastructure geometry and asset distribution (transformers, poles, service points)
- Analyzes settlement density patterns at zone level
- Identifies spatial density of productive activity signals (not population density)
- Identifies mismatches between coordination patterns and infrastructure coverage
- Calculates distance-to-service metrics at settlement scale
- Informs Critical Load Protection capacity adjustments based on infrastructure gap severity
- Outputs zones of unmet but coordinated demand with infrastructure gap analysis

**What LUNDAI NEVER Does**:
- Does NOT map individual households or precise dwelling locations
- Does NOT track behavioral histories or movement patterns
- Does NOT reason about specific actors or participants
- Does NOT create population profiles or demographic analyses
- Does NOT enable individual-level spatial queries

**Allowed Outputs**:
- Zone-level settlement context (e.g., rural_agricultural, peri_urban, informal_settlement)
- Infrastructure asset presence/absence at zone level (e.g., grid connection status)
- Distance-to-service metrics at settlement scale (e.g., 25km from nearest substation)
- Infrastructure gap severity classification (critical, moderate, minimal)
- Capacity reservation adjustment recommendations (e.g., +10% for critical gaps)
- Aggregate activity density patterns (not population density)

**Mandatory Refusals**:
- Individual household locations or addresses
- Precise GPS coordinates of dwellings
- Individual movement or travel patterns
- Household-level infrastructure access status
- Person-level spatial queries

**Scope Boundary**: LUNDAI operates exclusively at settlement and infrastructure scale. All spatial analysis remains at zone-level aggregation. It identifies "here is where coordinated milling demand exists, but no three-phase power" without tracking where specific people live or work.

---

### ZENTARI – Trust and Coordination Confidence Engine

**What ZENTARI Does**:
- Evaluates coordination pattern persistence across multiple time windows
- Measures coordination stability (how consistently patterns repeat)
- Measures coordination alignment (whether multiple activity types coordinate together)
- Measures coordination resilience (whether patterns persist through disruptions)
- Derives trust from repetition, alignment, and resilience of coordination patterns over time
- Outputs coordination confidence scores that indicate bankability of demand signals

**What ZENTARI NEVER Does**:
- Does NOT evaluate individuals, households, or participants
- Does NOT create reputations or credit scores
- Does NOT assess individual reliability or trustworthiness
- Does NOT authenticate or validate participants
- Does NOT enable individual-level trust queries

**Allowed Outputs**:
- Coordination confidence score (0.0 to 1.0 scale)
- Stability metric (pattern consistency across evaluation periods)
- Alignment metric (cross-activity coordination strength)
- Resilience metric (pattern persistence through disruptions)
- Confidence classification (high, medium, low)
- Bankability assessment for institutional decision-makers

**Mandatory Refusals**:
- Individual trust scores or reputation metrics
- Participant-level reliability assessments
- Credit scores or creditworthiness evaluations
- Individual authentication status
- Person-level confidence queries

**Trust Logic**: ZENTARI evaluates *coordination pattern persistence*, not people, households, or identity. It does not create reputations or assess individual reliability. A high confidence score indicates "this collective demand pattern is stable and bankable for infrastructure planning," not "these participants are trustworthy." Trust emerges from sustained, aligned coordination across multiple evaluation periods—it is a property of the pattern, not the participants.

---

### Demand-Signal Prospectus (System Output)

**What the Prospectus Contains**:
- Coordination Rhythms (from LUMOZA): When and what types of productive demand exist
- Infrastructure Gaps (from LUNDAI): Where coordinated demand is unserved by current infrastructure
- Coordination Confidence (from ZENTARI): How stable and bankable these demand patterns are
- Critical Load Protection: Reserved capacity percentages and essential service prioritization
- Settlement Context: Zone-level infrastructure and settlement characteristics
- Planning Guidance: Infrastructure investment recommendations based on verified collective demand

**What the Prospectus NEVER Contains**:
- Individual identities, names, or personal identifiers
- Household-level data or precise locations
- Individual activity logs or histories
- Participant-level trust or reputation scores
- Real-time event data or streaming updates
- Credit scores or eligibility assessments

**Intended Audience**: Institutional decision-makers (utilities, development finance institutions, infrastructure planners, policymakers)

**Purpose**: Enable infrastructure investment decisions based on verified collective demand, not on surveillance, credit scores, or individual profiling.

---

## Data Flow Architecture

### 1. Signal Ingestion

**Valid Coordination Signals**:
- Activity type (irrigation, milling, cold storage, welding, clinic, school, water_system, emergency_services)
- Approximate time window (morning/afternoon/evening)
- General location zone (coarse spatial granularity)
- NO participant identity or metadata

**Identity-Free Acceptance**:
- Ingestion layer actively rejects any input containing PII
- Signals are immediately stripped of any metadata that could enable re-identification
- Consent is embedded in the signal itself (participation implies consent to contribute to collective patterns)

**Minimum Aggregation Thresholds**:
- Signals must meet minimum batch sizes before processing
- Individual events cannot be isolated or queried

### 2. Time-Batching (Temporal Moat)

**Fixed Time Windows**:
- Individual events are grouped into fixed time windows (7-cycle/weekly batches for pilot)
- No immediate processing or streaming
- Minimum batch sizes enforced to prevent de-anonymization

**Tracking Prevention**:
- Batching destroys temporal precision needed for behavioral tracking
- Event timestamps are not preserved beyond batch window
- Sequential patterns within a batch are intentionally obscured through aggregation

### 3. Aggregation & Pattern Formation

**Batch Aggregation**:
- Batched signals are aggregated into coordination patterns that reveal collective rhythms
- One-off events and outliers are discarded as noise
- Only patterns that repeat across multiple batches are retained (5+ of 7 cycles for stability)

**Pattern Formation Without Reconstruction**:
- Aggregation produces statistical summaries (counts, frequencies, distributions)
- Raw signals are never stored or made available for reconstruction
- Patterns are synthetic representations of collective behavior, not traces of individuals

### 4. Engine Interaction

**Inter-Engine Flow**:
- LUMOZA receives batched, aggregated signals → outputs demand rhythms
- LUNDAI receives demand rhythms → overlays infrastructure context → outputs gap analysis
- ZENTARI receives coordination patterns → evaluates persistence → outputs confidence scores
- Engines operate on aggregated outputs from previous stages, never raw signals
- Each engine adds a layer of abstraction, moving further from individual events

**Isolation Guarantee**:
- No engine has access to data that could reconstruct individual activity
- Raw signals are discarded after aggregation (not archived)

### 5. Output Boundary

**Institutional Boundary**:
- Only aggregated, synthetic outputs cross the boundary to institutional decision-makers
- Demand-Signal Prospectus contains only collective patterns, infrastructure gaps, and confidence scores
- No raw signals, individual events, or personally identifiable information

**Export Restrictions**:
- System architecture makes it impossible to export or query individual-level data
- All queries must be coordination-focused, not identity-focused
- API layer enforces Semantic Guard refusals

---

## Architectural Principles

### Think Infrastructure, Not Features
- Prioritize governance, ethics, and system integrity over speed
- Design for long-term stability and trust
- Every component must serve coordination, not extraction

### Emergent Verification
- KULIMA OS does not validate individual inputs or authenticate participants
- Trust emerges from sustained, aligned coordination patterns across time
- Fake or noisy signals decay naturally—they do not reinforce patterns unless backed by real coordination
- Verification is a property of collective persistence, not individual attestation
- This approach prevents gaming: fabricated signals cannot sustain coordination patterns over multiple evaluation periods

### Fail-Soft Design
- Incorrect or noisy signals do not collapse the system
- They do not unlock access or trigger infrastructure deployment
- They fade from the pattern unless reinforced by genuine, repeated coordination
- System degrades gracefully: weak signals reduce confidence scores but do not break the pipeline
- Worst-case outcome is absence of bankable patterns, not exposure of personal data

### Fail-Safe Defaults
When ambiguous, default toward:
- More privacy (not less)
- More aggregation (not less)
- Less granularity (not more)

Never reverse these defaults for convenience.

### Transparency Without Exposure
- Design audit trails that verify adherence to invariants
- Enable external verification without exposing underlying data
- Documentation must make invariants visible to all contributors

---

## Non-Goals (Explicit Exclusions)

KULIMA OS is explicitly designed to NEVER:

1. **Track Individuals**: No surveillance, no behavioral tracking, no individual activity logs
2. **Create Credit Scores**: No creditworthiness assessment, no financial profiling
3. **Build Reputations**: No individual trust scores, no participant reliability metrics
4. **Enable Surveillance**: No real-time monitoring, no location tracking, no identity correlation
5. **Profile Participants**: No demographic analysis, no behavioral prediction, no individual characterization
6. **Gate Access**: No eligibility determination, no service access control, no participant authentication
7. **Predict Behavior**: No individual forecasting, no behavioral modeling, no person-level predictions
8. **Monetize Data**: No data sales, no third-party access to raw signals, no individual-level data exports
9. **Optimize for Individuals**: No personalization, no individual recommendations, no targeted interventions
10. **Authenticate Participants**: No identity verification, no participant validation, no individual attestation

---

## Ethics Locks (Refusal Guarantees)

The following requests MUST be refused at API and query layers:

### Individual-Level Queries
- "Show me activity for participant X"
- "List all participants in zone Y"
- "What is the trust score for household Z?"
- "Track individual A's coordination history"

### Real-Time Requests
- "Stream live coordination events"
- "Show current activity in zone X"
- "Alert when participant Y coordinates"

### Profiling Requests
- "Identify most reliable participants"
- "Rank households by coordination frequency"
- "Predict which participants will coordinate next"
- "Create demographic profile of zone X"

### Surveillance Requests
- "Track movement patterns of participants"
- "Monitor individual activity over time"
- "Correlate coordination with other behaviors"
- "Identify specific actors in coordination patterns"

### Credit/Eligibility Requests
- "Calculate creditworthiness for participant X"
- "Determine eligibility for service access"
- "Assess individual reliability for loan approval"
- "Create reputation score for household Y"

### Granularity Violations
- "Provide precise GPS coordinates of activity"
- "Show exact timestamps of individual events"
- "Export raw signal data for analysis"
- "Reconstruct individual activity from patterns"

**Refusal Response**: "This request violates system invariants. KULIMA OS operates exclusively on collective coordination patterns and cannot provide individual-level, real-time, or identity-linked information."

---

## Implementation Requirements

### For LUMOZA
- Must classify coordination patterns as 'essential' or 'productive' based on activity type
- Must enforce 7-cycle coordination logic with 5-of-7 stability threshold
- Must cross-validate human signals with telemetry at aggregate level only
- Must discard raw signals after aggregation (no archival)
- Must reject any input containing PII at ingestion

### For LUNDAI
- Must operate at settlement and infrastructure scale only
- Must not map individual households or precise locations
- Must calculate infrastructure gap severity for Critical Load Protection
- Must provide zone-level settlement context only
- Must refuse queries for individual-level spatial data

### For ZENTARI
- Must evaluate coordination pattern persistence, not individual reliability
- Must measure stability, alignment, and resilience of collective patterns
- Must not create individual trust scores or reputations
- Must output coordination confidence scores for patterns, not participants
- Must refuse queries for individual-level trust assessments

### For Prospectus Generator
- Must calculate and enforce Critical Load Protection capacity reservations (20-40%)
- Must integrate LUNDAI infrastructure gap analysis
- Must include settlement context and planning guidance
- Must contain only aggregated, synthetic outputs
- Must refuse to include individual-level data or identifiers

---

## Pilot Implementation Status

**Current Version**: v0.2 (Pilot-Ready)

**Implemented Components**:
- ✅ LUMOZA (7-cycle coordination detection with essential service classification)
- ✅ LUNDAI (settlement & infrastructure gap analysis, deterministic)
- ✅ ZENTARI (coordination confidence evaluation)
- ✅ Critical Load Protection (dynamic capacity reservation 20-40%)
- ✅ Demand-Signal Prospectus generation
- ✅ All five system invariants enforced architecturally

**Pilot Characteristics**:
- Uses synthetic coordination signals (see DATASET.md)
- Demonstrates complete signal-to-prospectus pipeline
- Enforces all invariants and refusal guarantees
- Produces institutional-grade outputs
- Cross-platform compatible (Windows, Mac, Linux)

**Pilot-to-Production Path**:
- Same pipeline, same invariants, same refusal guarantees
- Only signal source changes (synthetic → real community coordination signals)
- No architectural changes required
- No relaxation of privacy constraints

---

## Governance Requirements

### For Future Changes

Any proposed changes to the following require institutional ethics review:

1. **System Invariants**: Zero-PII, Temporal Moat, Coordination > Identity, Semantic Guard, Critical Load Protection
2. **Engine Behaviors**: What each engine processes, outputs, or refuses
3. **Data Flow Architecture**: Signal ingestion, batching, aggregation, or output boundaries
4. **Refusal Guarantees**: What the system must refuse to do
5. **Scope Boundaries**: What scale each engine operates at

### Ethics Review Criteria

Proposed changes must demonstrate:
- Preservation of all five system invariants
- No introduction of individual-level data processing
- No weakening of privacy protections
- No expansion of scope toward surveillance or profiling
- Alignment with coordination-first, non-extractive mission
- Institutional audit trail and external verification capability

### Change Rejection Criteria

Proposed changes MUST be rejected if they:
- Enable individual tracking or surveillance
- Create credit scores or reputations
- Introduce real-time processing or streaming
- Allow individual-level queries or exports
- Weaken aggregation or increase granularity
- Violate any system invariant or refusal guarantee

---

## Audit and Verification

### External Audit Requirements

KULIMA OS must enable external auditors to verify:
- No PII enters or exists in the system
- All processing occurs in time-batched windows
- No individual-level data can be reconstructed from outputs
- Refusal mechanisms function correctly at API layer
- Critical Load Protection capacity reservations are enforced
- System cannot be repurposed for surveillance

### Audit Artifacts

The following must be available for audit:
- This specification document (canonical reference)
- Source code with invariant enforcement comments
- Data flow diagrams showing abstraction layers
- Example prospectus outputs (demonstrating aggregation)
- Test suites validating refusal guarantees
- API documentation showing query restrictions

### Verification Methods

Auditors may:
- Review source code for PII handling
- Test API with prohibited queries (must be refused)
- Analyze outputs for individual-level information (must be absent)
- Trace data flow from ingestion to output (must show layered abstraction)
- Verify batch window enforcement (must prevent real-time processing)
- Confirm Critical Load Protection logic (must reserve capacity)

---

## Conclusion

This specification defines the immutable architecture of KULIMA OS as a coordination substrate for infrastructure planning. It is designed to make productive-use energy demand visible and trustworthy BEFORE infrastructure is deployed, without surveillance, profiling, or individual tracking.

**Core Achievement**: KULIMA OS demonstrates that coordination can replace surveillance in Digital Public Infrastructure. It proves that informal economies can become institution-readable without extraction or profiling.

**Governance Commitment**: This specification is frozen. Future changes require institutional ethics review to ensure preservation of system invariants and refusal guarantees.

**For Stewards**: Your responsibility is to maintain the integrity of this architecture. Resist feature creep, scope expansion, and convenience-driven compromises. KULIMA OS is infrastructure for infrastructure planning—not an app, not a platform, not a surveillance system.

---

**Document Version**: 1.0  
**Status**: Frozen – Changes require institutional ethics review  
**Last Updated**: 2026-05-04  
**Maintained By**: KULIMA OS Stewardship Team