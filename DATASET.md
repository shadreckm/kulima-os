# DATASET.md - Synthetic Data Approach

## Overview

All data used in the KULIMA OS pilot demonstration is **internally generated synthetic coordination data**. No real-world personal data, location data, or activity logs are used.

## Why Synthetic Data?

### 1. Privacy & Ethics Compliance

KULIMA OS is built on strict system invariants:
- **Zero-PII**: No personal identifiers may ever enter the system
- **Temporal Moat**: All processing in time-batched windows (no real-time tracking)
- **Coordination > Identity**: System reasons over collective patterns, never individuals
- **Semantic Guard**: No surveillance, credit scoring, or behavioral prediction

Using synthetic data for the pilot demonstration ensures:
- No risk of exposing real individuals or communities
- No ethical concerns about consent or data collection
- Full compliance with privacy-by-design principles
- Transparent, auditable demonstration of system capabilities

### 2. Pilot Readiness Without Real-World Deployment

Synthetic data allows us to demonstrate the **complete end-to-end pipeline** without requiring:
- Real-world infrastructure telemetry integration
- Community engagement and consent processes
- Regulatory approvals for data collection
- Physical deployment of monitoring systems

This makes the pilot **immediately demonstrable** while maintaining full ethical compliance.

### 3. Reproducibility & Auditability

Synthetic data ensures:
- Anyone can run the demo and see identical results
- Judges can verify system behavior without privacy concerns
- The demonstration is fully transparent and auditable
- No hidden data dependencies or external APIs

## What the Synthetic Data Represents

The synthetic dataset in `pilot_signals.py` simulates:

### Signal Types

1. **Human-Reported Coordination Signals**
   - Activity type (irrigation, milling, cold storage, welding)
   - Approximate time window (morning, afternoon, evening)
   - General zone (zone_a, zone_b, zone_c)
   - No participant identity or metadata

2. **Infrastructure Telemetry Signals**
   - Shared asset activity (pump runtime, mill usage, cold room power draw)
   - Aggregated at asset level (not individual connections)
   - Treated as corroboration, not surveillance

### Coordination Patterns

The synthetic data includes:
- **Stable patterns**: Activities appearing in 5-7 of 7 cycles (e.g., irrigation in zone_a)
- **Intermediate patterns**: Activities appearing in 4 of 7 cycles (borderline coordination)
- **Noise patterns**: Activities appearing in <3 of 7 cycles (filtered out as one-offs)
- **Validation scenarios**: Human signals with/without telemetry corroboration
- **Discrepancy examples**: Claimed coordination without infrastructure evidence

## How Real-World Data Would Work

### Signal Sources in Production

In a real-world pilot, coordination signals would come from:

1. **Community Reporting**
   - SMS-based coordination reporting (identity-free)
   - Community coordinators reporting collective activity
   - Shared asset usage logs (aggregated, not individual)

2. **Infrastructure Telemetry**
   - Smart meter data from shared assets (pumps, mills, cold storage)
   - Aggregated at asset level, not individual connections
   - Time-batched to prevent real-time tracking

### Data Flow Remains Identical

The **exact same pipeline** would process real-world data:

1. **Signal Ingestion**: Accept identity-free coordination signals
2. **Time-Batching**: Group signals into 7-cycle windows
3. **Aggregation**: Form collective patterns, filter noise
4. **LUMOZA Processing**: Detect demand rhythms, cross-validate
5. **ZENTARI Evaluation**: Compute coordination confidence
6. **Prospectus Generation**: Output institutional-grade documents

**Only the signal source changes. The coordination logic, privacy enforcement, and output format remain identical.**

## Synthetic Data Generation Logic

The synthetic data in `pilot_signals.py` is generated using:

```python
def generate_pilot_signals() -> List[Dict]:
    """
    Generate synthetic coordination signals for a 7-cycle (weekly) window.
    
    PRIVACY DESIGN:
    - No individual identifiers
    - Coarse spatial granularity (zones, not coordinates)
    - Coarse temporal granularity (time windows, not timestamps)
    - Signals represent activity types, not people
    """
```

Each signal contains only:
- `activity_type`: Type of productive activity (irrigation, milling, etc.)
- `cycle_index`: Which cycle in the 7-cycle window (1-7)
- `time_window`: Coarse time period (morning, afternoon, evening)
- `zone`: General area identifier (zone_a, zone_b, zone_c)
- `signal_source`: Whether human-reported or telemetry

**No names. No IDs. No precise locations. No timestamps. No individual identifiers.**

## Verification

To verify that the system operates only on synthetic data:

1. **Inspect `pilot_signals.py`**: All data is generated in-memory
2. **Run the demo**: No external data sources or APIs are accessed
3. **Check outputs**: Prospectus contains only aggregated patterns
4. **Review AGENTS.md**: System invariants prevent individual-level data

## Transition to Real-World Data

When transitioning to a real-world pilot:

1. **Replace signal source**: Swap `generate_pilot_signals()` with real data ingestion
2. **Maintain invariants**: All privacy constraints remain enforced
3. **Same pipeline**: LUMOZA, ZENTARI, and prospectus generation unchanged
4. **Audit compliance**: External verification that no PII enters the system

The synthetic data approach proves that **coordination intelligence works without surveillance**—and that the same system can operate on real-world data while maintaining strict ethical constraints.

---

**Key Takeaway**: Synthetic data enables a fully functional, auditable demonstration while maintaining absolute privacy compliance. The transition to real-world data requires only changing the signal source—the coordination logic and privacy enforcement remain identical.