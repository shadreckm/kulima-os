# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Identity

**KULIMA OS** is a coordination-first economic substrate designed as Digital Public Infrastructure (DPI). It is NOT an app, NOT a data platform, and NOT a surveillance system.

**Purpose**: Convert decentralized livelihood activity into verified, bankable coordination signals for infrastructure planning, without extracting or profiling people.

## Domain Context

KULIMA OS operates in the context of energy and infrastructure planning for rural and informal economies. Its purpose is to make productive-use energy demand visible and trustworthy BEFORE infrastructure is deployed.

### The Three Engines

#### 1. LUMOZA — Livelihood and Energy Coordination Engine

LUMOZA processes coordination signals from productive livelihood activities such as irrigation, milling, cold storage, welding, and other energy-dependent economic activities. It transforms heterogeneous activity signals into time-batched demand rhythms that reveal collective patterns of productive energy use.

**Key Characteristics**:
- Processes activity types (irrigation, milling, cold storage), not individual actors
- Aggregates signals into temporal demand patterns (daily, weekly, seasonal rhythms)
- Operates exclusively on coordination patterns, never individual behaviors
- Outputs: Collective demand rhythms that indicate when and how productive activities cluster

**Invariant Alignment**: LUMOZA never reasons about individuals. It sees only the rhythm of collective economic activity—when irrigation happens, when milling peaks, when cold storage demand rises—without knowing who is doing these activities.

##### LUMOZA Pilot Specialization: 7-Cycle Coordination Logic

For the pilot implementation, LUMOZA uses a 7-cycle coordination window aligned with weekly livelihood rhythms in rural and informal economies.

**1. The 7-Cycle Window**

The 7-cycle (weekly) window reflects natural livelihood rhythms:
- Agricultural activities follow weekly market cycles
- Milling and processing align with harvest and sale patterns
- Irrigation schedules repeat on weekly intervals
- Cold storage use clusters around market days

A **stable coordination pattern** emerges when an activity type repeats consistently across at least 5 of 7 cycles within the same time window (e.g., irrigation every Tuesday-Thursday morning). One-off or noisy activities that appear in fewer than 3 cycles are excluded as non-coordinated events.

**2. Signal Types for the Pilot**

LUMOZA accepts two signal types, both identity-free:

**Human-Reported Coordination Signals**:
- Activity type (irrigation, milling, cold storage, welding)
- Approximate time window (morning/afternoon/evening)
- General zone (not precise location)
- No participant identity or metadata

**Infrastructure Telemetry Signals**:
- Shared asset activity (pump on/off, mill runtime, cold room power draw)
- Aggregated at asset level (not individual connections)
- Treated as corroboration, not surveillance
- Cannot be linked back to specific users

**Telemetry as Corroboration**: Infrastructure telemetry validates that reported coordination signals correspond to actual energy use patterns. This strengthens trust in the demand signal without tracking individuals. For example, if human signals report milling activity on Tuesday mornings, telemetry showing mill runtime during those windows corroborates the pattern without revealing who used the mill.

**3. Cross-Signal Validation**

LUMOZA cross-validates human signals with infrastructure telemetry to strengthen coordination confidence:

**Validation Logic**:
- Human signals establish the claimed coordination pattern
- Telemetry corroborates that energy use occurred during claimed windows
- Alignment between signals increases pattern confidence
- Discrepancies reduce confidence but do not penalize participants

**Handling Discrepancies**:
- If human signals report coordination but telemetry shows no activity: pattern confidence decreases, but no individual is flagged
- If telemetry shows activity but no human signals: activity is noted but not counted as coordinated demand (may be individual, non-coordinated use)
- Validation operates at aggregate level across all signals in a zone, never at individual level

**Strengthening Trust Without Exposure**:
- Validation increases the bankability of demand signals for institutional decision-makers
- Cross-validation proves that coordination is real, not fabricated
- No individual identities are exposed or tracked in the validation process
- Discrepancies are treated as noise in the collective pattern, not as individual failures

**4. Output to ZENTARI**

After 7 cycles, LUMOZA outputs coordination metrics for each activity type and zone:

**Demand Rhythm**:
- Activity type (e.g., irrigation, milling)
- Time windows when activity clusters (e.g., Tuesday-Thursday mornings)
- Frequency of occurrence across 7 cycles (e.g., 6 out of 7 cycles)
- Zone identifier (general area, not precise location)

**Stability Score**:
- Consistency metric: how reliably does the pattern repeat?
- Validation metric: how well do human signals align with telemetry?
- Noise ratio: what percentage of signals were excluded as one-offs?

**Feed to ZENTARI**:
- ZENTARI receives only these aggregated outputs, never raw signals
- ZENTARI evaluates stability scores over multiple 7-cycle windows to measure coordination resilience
- Trust grows when patterns persist across multiple evaluation periods
- Trust decays when patterns become erratic or disappear

**Pilot-Ready for Real-World Energy Planning**

This 7-cycle specialization makes LUMOZA pilot-ready because:

1. **Aligned with Livelihood Rhythms**: Weekly cycles match how rural economies actually operate, making patterns meaningful for infrastructure planning.

2. **Validation Without Surveillance**: Cross-validation with telemetry proves demand is real without tracking individuals, satisfying both institutional trust requirements and ethical constraints.

3. **Noise Filtering**: The 5-of-7 threshold ensures only genuine coordination patterns are counted, preventing one-off events from distorting demand signals.

4. **Bankable Outputs**: Stability scores and demand rhythms provide utilities and financiers with the confidence metrics they need to invest in infrastructure.

5. **Invariant Compliance**: Every stage maintains Zero-PII, Temporal Moat, and Coordination > Identity principles, ensuring the pilot cannot drift toward surveillance.

#### 2. LUNDAI — Spatial and Infrastructure Mismatch Engine

LUNDAI reasons over infrastructure geometry, not people geography. It analyzes settlement density patterns, asset distribution (transformers, poles, service points), and distance-to-service metrics to identify zones where coordinated demand exists but infrastructure does not.

**Key Characteristics**:
- Operates on infrastructure topology: where assets are, where gaps exist
- Analyzes spatial density of productive activity signals (not population density)
- Identifies mismatches between coordination patterns and infrastructure coverage
- Outputs: Zones of unmet but coordinated demand, infrastructure gap analysis

**Scope Boundary**: LUNDAI operates exclusively at settlement and infrastructure scale. It does not map individual households, track behavioral histories, or reason about specific actors. All spatial analysis remains at zone-level aggregation, preserving the Zero-PII invariant.

**Invariant Alignment**: LUNDAI sees infrastructure geometry and aggregate activity density. It identifies "here is where coordinated milling demand exists, but no three-phase power" without tracking where specific people live or work.

#### 3. ZENTARI — Trust and Coordination Confidence Engine

ZENTARI derives trust from repetition, alignment, and resilience of coordination patterns over time. Trust is not a property of individuals but of coordination itself. Trust grows when collective patterns persist and align across time windows. Trust decays when coordination breaks down or becomes erratic.

**Key Characteristics**:
- Measures coordination stability: how consistently do patterns repeat?
- Measures coordination alignment: do multiple activity types coordinate together?
- Measures coordination resilience: do patterns persist through disruptions?
- Outputs: Coordination confidence scores that indicate bankability of demand signals

**Trust Logic Clarification**: ZENTARI evaluates *coordination pattern persistence*, not people, households, or identity. It does not create reputations or assess individual reliability. A high confidence score indicates "this collective demand pattern is stable and bankable for infrastructure planning," not "these participants are trustworthy." Trust emerges from sustained, aligned coordination across multiple evaluation periods—it is a property of the pattern, not the participants.

**Invariant Alignment**: ZENTARI replaces credit scoring without creating reputations. It evaluates the trustworthiness of coordination patterns, not the creditworthiness of people. A high trust score means "this demand pattern is stable and bankable," not "these people are reliable."

### Demand-Signal Prospectus

The outputs from LUMOZA, LUNDAI, and ZENTARI combine into a **Demand-Signal Prospectus**—a verified, bankable document for institutional decision-makers (utilities, development finance institutions, infrastructure planners).

The prospectus contains:
- **Coordination Rhythms** (from LUMOZA): When and what types of productive demand exist
- **Infrastructure Gaps** (from LUNDAI): Where coordinated demand is unserved by current infrastructure
- **Coordination Confidence** (from ZENTARI): How stable and bankable these demand patterns are

This prospectus enables infrastructure investment decisions based on verified collective demand, not on surveillance, credit scores, or individual profiling. It answers: "Where should we build? What capacity is needed? How confident can we be in the demand?"

## Data Flow Architecture

The data flow architecture enforces the Temporal Moat and Zero-PII invariants at every stage, ensuring signals move through the system without enabling surveillance or individual tracking.

### 1. Signal Ingestion

**Valid Coordination Signals**: A coordination signal represents a productive livelihood activity type (irrigation event, milling activity, cold storage use, welding session) with temporal and spatial context but no identity.

**Identity-Free Acceptance**:
- Signals contain only: activity type, approximate time window, general location zone (not precise coordinates)
- No names, IDs, phone numbers, or individual identifiers are accepted
- Ingestion layer actively rejects any input containing PII
- Consent is embedded in the signal itself (participation implies consent to contribute to collective patterns)

**Scope Enforcement**:
- Signals are scoped to activity types and zones, never to individuals
- Each signal is immediately stripped of any metadata that could enable re-identification
- Ingestion validates that signals meet minimum aggregation thresholds before acceptance

### 2. Time-Batching (Temporal Moat)

**Fixed Time Windows**: Individual events are grouped into fixed time windows (e.g., daily, weekly batches) before any processing occurs.

**No Real-Time Processing**:
- Signals accumulate in batches; no immediate processing or streaming
- Minimum batch sizes are enforced to prevent de-anonymization
- Time windows are large enough that individual events cannot be isolated or correlated

**Tracking Prevention**:
- Batching destroys temporal precision needed for behavioral tracking
- No event timestamps are preserved beyond the batch window
- Sequential patterns within a batch are intentionally obscured through aggregation

### 3. Aggregation & Pattern Formation

**Batch Aggregation**: Batched signals are aggregated into coordination patterns that reveal collective rhythms, not individual behaviors.

**Noise Filtering**:
- One-off events and outliers are discarded as noise
- Only patterns that repeat across multiple batches are retained
- Minimum occurrence thresholds ensure patterns represent collective activity

**Pattern Formation Without Reconstruction**:
- Aggregation produces statistical summaries (counts, frequencies, distributions)
- Raw signals are never stored or made available for reconstruction
- Patterns are synthetic representations of collective behavior, not traces of individuals

### 4. Engine Interaction

**LUMOZA Processing**: Receives batched, aggregated signals and transforms them into demand rhythms (daily peaks, weekly cycles, seasonal patterns) by activity type.

**LUNDAI Overlay**: Takes demand rhythms from LUMOZA and overlays spatial/infrastructure context (where transformers exist, where gaps are, distance-to-service metrics) to identify mismatches.

**ZENTARI Evaluation**: Analyzes coordination patterns over multiple time windows to measure stability, alignment, and resilience, producing coordination confidence scores.

**Inter-Engine Flow**:
- Engines operate on aggregated outputs from previous stages, never raw signals
- Each engine adds a layer of abstraction, moving further from individual events
- No engine has access to data that could reconstruct individual activity

### 5. Output Boundary

**Institutional Boundary**: Only aggregated, synthetic outputs cross the boundary to institutional decision-makers.

**Output Characteristics**:
- Demand-Signal Prospectus contains only collective patterns, infrastructure gaps, and confidence scores
- No raw signals, individual events, or personally identifiable information
- Outputs are designed for infrastructure planning, not for profiling or surveillance

**Raw Signal Isolation**:
- Raw signals never leave the ingestion and batching layer
- After aggregation, raw signals are discarded (not archived)
- System architecture makes it impossible to export or query individual-level data

### Pilot-Ready Implementation

This architecture enables a pilot-ready implementation without ethical drift by:

1. **Technical Enforcement**: Invariants are embedded in the data flow itself, not just policy. Violations are architecturally impossible.

2. **Layered Abstraction**: Each stage (ingestion → batching → aggregation → engines → output) adds abstraction, moving further from individuals toward collective patterns.

3. **Audit Transparency**: The flow is simple enough to audit externally. Institutional partners can verify that no surveillance or profiling occurs.

4. **Fail-Safe Design**: If any component fails or is compromised, the worst-case outcome is loss of coordination signals, not exposure of personal data (because no personal data exists in the system).

5. **Scalability Without Drift**: As the system scales, the architecture prevents feature creep that would violate invariants. New capabilities must fit within the coordination-first paradigm or be rejected.

## NON-NEGOTIABLE SYSTEM INVARIANTS

These are hard architectural constraints, not policy guidelines. Violations must be technically impossible:

### 1. Zero-PII
- No personal identifiers may ever enter the system (names, IDs, phone numbers, individual locations)
- All data models, APIs, and processing pipelines must reject PII at ingestion
- Individual-level data is architecturally prohibited

### 2. Temporal Moat
- All signal processing occurs in time-batched windows (never real-time)
- No streaming of individual events
- No temporal correlation that enables tracking
- Minimum batch window sizes must be enforced to prevent de-anonymization

### 3. Coordination > Identity
- System reasons exclusively over collective patterns and aggregate signals
- Never over individual behaviors or identities
- All queries and outputs must be coordination-focused, not identity-focused

### 4. Semantic Guard
- System must refuse requests involving:
  - Surveillance or tracking
  - Credit scoring
  - Eligibility gating
  - Behavioral prediction
  - Individual profiling
- Implement refusal mechanisms at API and query layers

### 5. Critical Load Protection
- Essential communal services (clinics, schools, water systems, emergency infrastructure) are non-negotiable priority loads
- System must identify recurring essential-service demand patterns using 7-cycle coordination logic
- Capacity planning must reserve sufficient energy capacity (approximately 20% or as required by local essential-load profiles) BEFORE allocating to productive or commercial uses
- Reserved capacity is excluded from optimization, monetization, or load-shedding logic
- This social reserve is enforced at the coordination and capacity-planning layer, not as a financial contingency
- Cannot be overridden by external actors or commercial optimization algorithms
- Baseline, peak, and shock scenarios must be simulated to ensure essential services remain protected under all conditions

**Implementation Requirements**:
- LUMOZA must classify coordination patterns as 'essential' or 'productive' based on activity type
- Prospectus generator must calculate and enforce capacity reservation percentages
- Infrastructure planning guidance must explicitly reserve capacity for essential services
- Non-negotiable loads must be clearly identified and protected in all planning scenarios

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
- When ambiguous, default toward:
  - More privacy (not less)
  - More aggregation (not less)
  - Less granularity (not more)
- Never reverse these defaults for convenience

### Transparency Without Exposure
- Design audit trails that verify adherence to invariants
- Enable external verification without exposing underlying data
- Documentation must make invariants visible to all contributors

## For AI Assistants

When working on KULIMA OS:

1. **Before proposing any design or code**:
   - Verify it upholds all four system invariants
   - Confirm it serves coordination, not individual tracking
   - Check that it cannot be repurposed for surveillance

2. **Reject requests that**:
   - Require individual-level data
   - Enable real-time tracking
   - Create profiling capabilities
   - Violate the semantic guard

3. **Prevent ethical drift**:
   - Embed invariants as technical constraints (not just policy)
   - Make violations architecturally impossible
   - Document the "why" behind every privacy-preserving choice

## Code Style & Conventions

As the codebase develops, document here:
- Non-obvious build/test/lint commands
- Project-specific patterns discovered by reading code
- Custom utilities for privacy-preserving operations
- Critical gotchas that would violate system invariants

**Note**: Only include non-obvious, project-specific information. Standard practices should not be documented here.