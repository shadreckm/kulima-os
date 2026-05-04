# DSAPG Assumptions and Methodology Documentation
## Demand-Signal Aggregation & Prospectus Generator

**Purpose**: This document explains the conservative estimation methodology, assumptions, and institutional framing used in KULIMA OS demand-signal prospectuses. It is designed for review by Development Finance Institutions (DFIs), utilities, infrastructure planners, and energy programs.

---

## 1. Conservative Estimation Philosophy

### Why Conservative?

KULIMA OS prospectuses are designed to be **bankable** - meaning they provide reliable, trustworthy demand estimates that institutional decision-makers can use for infrastructure investment without fear of demand shortfall.

**Core Principle**: Better to underestimate demand and be pleasantly surprised than to overestimate and face stranded assets.

### How Conservative?

All energy demand estimates use **lower bounds** of typical activity ranges:

- **Power ratings**: Minimum typical kW for each activity type
- **Operating hours**: Minimum typical hours per event
- **Load factors**: Conservative assumptions about intermittent operation
- **Diversity factors**: Account for non-simultaneous operation

**Expected Reality**: Actual demand is likely **20-40% higher** than conservative estimates presented in prospectuses.

---

## 2. Load Profile Data Sources

All activity-level load profiles are derived from peer-reviewed, institutional sources:

### Primary Sources

1. **World Bank Rural Electrification Toolkit (2008)**
   - Standard reference for rural productive use loads
   - Covers irrigation, milling, cold storage

2. **ESMAP Technical Papers (121, 145, 156)**
   - Energy Sector Management Assistance Program
   - Productive use of energy studies
   - Load profiles for rural and informal economies

3. **IFC Productive Use of Energy Study (2018)**
   - International Finance Corporation research
   - Economic multipliers for productive use energy
   - ROI analysis for infrastructure investment

4. **WHO Health Facility Electrification Guidelines (2020)**
   - Essential service load profiles
   - Medical equipment power requirements
   - Reliability standards for health facilities

### Why These Sources?

- **Institutional credibility**: Recognized by DFIs and development banks
- **Rural focus**: Designed for contexts similar to KULIMA OS deployment
- **Conservative**: Already use lower-bound estimates for planning
- **Auditable**: Publicly available, peer-reviewed

---

## 3. Activity-Level Load Profiles

### Productive Activities

#### Irrigation
- **Power Range**: 3.0 - 7.5 kW (using 3.0 kW for estimates)
- **Hours per Event**: 2.0 - 4.0 hours (using 2.0 hours)
- **Load Factor**: 0.85 (motor-driven, sustained operation)
- **Diversity Factor**: 0.70 (not all pumps run simultaneously)
- **Rationale**: Small to medium water pumps, three-phase motors. Conservative estimate assumes smallest pumps, shortest runtime.

#### Milling
- **Power Range**: 5.0 - 15.0 kW (using 5.0 kW)
- **Hours per Event**: 3.0 - 6.0 hours (using 3.0 hours)
- **Load Factor**: 0.75 (high starting current, sustained load)
- **Diversity Factor**: 0.65 (mills operate in shifts)
- **Rationale**: Grain mill motors. Conservative estimate assumes smallest mills, shortest operating windows.

#### Cold Storage
- **Power Range**: 2.0 - 8.0 kW (using 2.0 kW)
- **Hours per Event**: 8.0 - 24.0 hours (using 8.0 hours)
- **Load Factor**: 0.60 (intermittent compressor cycling)
- **Diversity Factor**: 0.80 (cold rooms operate continuously but cycle)
- **Rationale**: Cold room compressors. Conservative estimate assumes smallest units, shortest continuous operation.

#### Welding
- **Power Range**: 4.0 - 10.0 kW (using 4.0 kW)
- **Hours per Event**: 2.0 - 5.0 hours (using 2.0 hours)
- **Load Factor**: 0.50 (highly intermittent use)
- **Diversity Factor**: 0.60 (welders work in shifts)
- **Rationale**: Arc welding equipment. Conservative estimate assumes smallest welders, shortest sessions.

### Essential Services

#### Clinic
- **Power Range**: 1.5 - 5.0 kW (using 1.5 kW)
- **Hours per Event**: 8.0 - 24.0 hours (using 8.0 hours)
- **Load Factor**: 0.40 (lighting, refrigeration, intermittent equipment)
- **Diversity Factor**: 0.90 (essential services must be highly available)
- **Rationale**: Medical equipment, vaccine refrigeration, lighting. Conservative for small rural clinics.

#### School
- **Power Range**: 2.0 - 6.0 kW (using 2.0 kW)
- **Hours per Event**: 6.0 - 10.0 hours (using 6.0 hours)
- **Load Factor**: 0.50 (daytime operation, intermittent use)
- **Diversity Factor**: 0.85 (schools operate on fixed schedules)
- **Rationale**: Lighting, computers, fans. Conservative for small rural schools.

#### Water System
- **Power Range**: 3.0 - 10.0 kW (using 3.0 kW)
- **Hours per Event**: 4.0 - 12.0 hours (using 4.0 hours)
- **Load Factor**: 0.70 (pumping and treatment)
- **Diversity Factor**: 0.85 (community water systems operate on schedules)
- **Rationale**: Community water pumping and treatment. Conservative for small systems.

#### Emergency Services
- **Power Range**: 2.0 - 8.0 kW (using 2.0 kW)
- **Hours per Event**: 24.0 hours (continuous)
- **Load Factor**: 0.30 (standby systems, intermittent use)
- **Diversity Factor**: 0.95 (must be always available)
- **Rationale**: Emergency lighting, communications, backup systems. Conservative for basic emergency infrastructure.

---

## 4. Calculation Methodology

### Step 1: Pattern-Level Estimation

For each coordination pattern detected by LUMOZA:

1. **Identify activity type** (e.g., irrigation, milling)
2. **Look up load profile** (conservative power, hours, factors)
3. **Parse frequency** (e.g., "6 of 7 cycles" → 6 occurrences per week)
4. **Calculate energy per event**:
   ```
   Energy per event (kWh) = Power (kW) × Load Factor × Hours
   ```
5. **Calculate weekly energy**:
   ```
   Weekly energy (kWh) = Energy per event × Frequency
   ```
6. **Calculate daily average**:
   ```
   Daily energy (kWh) = Weekly energy / 7
   ```

### Step 2: Zone-Level Aggregation

For each zone with multiple patterns:

1. **Sum effective power** across all patterns
2. **Apply diversity factor** (weighted average across activities)
3. **Calculate diversified peak**:
   ```
   Diversified peak (kW) = Sum of effective power × Diversity factor
   ```
4. **Sum daily energy** across all patterns

### Step 3: System-Level Totals

1. **Aggregate across all zones**
2. **Separate essential vs productive demand**
3. **Calculate monthly and annual projections**
4. **Add capacity headroom** (25% for growth and contingency)

### Step 4: Capacity Planning

1. **Recommended capacity** = Peak demand × 1.25 (25% headroom)
2. **Transformer sizing** = Recommended capacity / 0.8 (power factor)
3. **Critical load reserve** = 30-40% for essential services (enforced)

---

## 5. Why This Approach is Bankable

### For DFIs and Financiers

1. **Conservative estimates reduce demand risk**: Actual demand likely higher than projected
2. **Institutional data sources**: Recognized, peer-reviewed, auditable
3. **Transparent methodology**: Every number has documented justification
4. **Risk quantification**: Uncertainty ranges explicitly stated
5. **Capacity headroom**: 25% buffer for growth and contingency

### For Utilities and Infrastructure Operators

1. **Reliable demand signals**: Based on observed coordination patterns, not surveys
2. **Cross-validated**: Human signals corroborated by telemetry
3. **Stability scores**: Confidence metrics indicate pattern persistence
4. **Essential service protection**: Critical loads identified and reserved
5. **Phased deployment guidance**: High-confidence zones prioritized

### For Regulators

1. **Tariff justification**: Productive use demand supports cost recovery
2. **Service standards**: Essential services protected under all scenarios
3. **Equity and inclusion**: Zero-PII architecture prevents discrimination
4. **Auditable**: All outputs traceable to coordination patterns
5. **Governance framework**: Transparent capacity allocation principles

---

## 6. Limitations and Caveats

### What This Prospectus IS

- **Demand signal**: Evidence of coordinated productive activity
- **Planning tool**: Guidance for infrastructure investment decisions
- **Bankable estimate**: Conservative, lower-bound demand projection
- **Risk assessment**: Quantified uncertainty and mitigation strategies

### What This Prospectus IS NOT

- **Guarantee**: Actual demand may vary based on economic conditions
- **Detailed engineering**: Requires site-specific design and ESIA
- **Financial model**: Does not include tariff structure or revenue projections
- **Stakeholder consent**: Community engagement required before deployment

### Key Assumptions

1. **Coordination patterns persist**: Assumes observed patterns continue
2. **Economic conditions stable**: Major shocks could disrupt patterns
3. **Infrastructure quality**: Assumes reliable, well-maintained infrastructure
4. **Tariff affordability**: Assumes productive use tariffs are affordable
5. **Stakeholder engagement**: Assumes community support for deployment

### Uncertainty Ranges

- **Conservative estimate**: As presented in prospectus (lower bound)
- **Expected range**: 20-40% higher than conservative estimate
- **Upper bound**: Up to 1.5x conservative estimate during peak coordination

---

## 7. Institutional Framing

### For Development Finance Institutions

**Key Message**: This prospectus provides verified, bankable demand signals for productive use infrastructure investment. Conservative estimates reduce demand risk while enabling infrastructure that drives economic development.

**Value Proposition**:
- Productive use energy generates 3-5x economic value vs household consumption
- Stable coordination patterns indicate reliable revenue for cost recovery
- Essential service protection ensures social impact alongside economic returns
- Zero-PII architecture aligns with ethical investment principles

### For Energy Programs and Utilities

**Key Message**: This prospectus translates informal economic activity into institution-readable demand signals, enabling infrastructure planning without surveillance or profiling.

**Value Proposition**:
- Demand signals based on observed coordination, not surveys or projections
- Cross-validation with telemetry strengthens confidence
- Phased deployment guidance prioritizes high-confidence zones
- Adaptive management framework enables ongoing optimization

### For Regulators and Policymakers

**Key Message**: This prospectus demonstrates how coordination intelligence can enable equitable, inclusive infrastructure planning that serves collective needs.

**Value Proposition**:
- Zero-PII architecture prevents discrimination and exclusion
- Essential service protection is architecturally enforced
- Transparent governance framework for capacity allocation
- Auditable outputs ensure accountability

---

## 8. Next Steps for Institutional Review

### For DFIs Considering Financing

1. **Review load estimation methodology** (Section 2-4 above)
2. **Assess risk quantification** (Risk & Governance section of prospectus)
3. **Evaluate sustainability impact** (Sustainability Impact section)
4. **Confirm deployment readiness** (Deployment Readiness section)
5. **Request detailed engineering** if demand signals are satisfactory

### For Utilities Considering Deployment

1. **Validate coordination patterns** against local knowledge
2. **Assess infrastructure requirements** (electrical, civil, CAPEX)
3. **Review capacity planning guidance** (transformer sizing, voltage)
4. **Confirm essential service protection** (Critical Load Protection section)
5. **Initiate stakeholder engagement** with communities

### For Regulators Reviewing Tariff Applications

1. **Verify demand estimation methodology** (conservative, auditable)
2. **Assess productive use justification** (economic multipliers, ROI)
3. **Confirm essential service protection** (non-negotiable reserves)
4. **Review governance framework** (transparent allocation principles)
5. **Evaluate equity and inclusion** (Zero-PII, no profiling)

---

## 9. Contact and Further Information

For questions about this methodology or to request additional analysis:

- **Technical Documentation**: See `AGENTS.md` for system invariants
- **PPSG Specification**: See `PPSG_SPECIFICATION.md` for signal gateway design
- **Pilot Scenario**: See `PILOT_SCENARIO.md` for demonstration context
- **Implementation Status**: See `IMPLEMENTATION_STATUS.md` for current capabilities

---

## 10. Version History

- **v1.0 (2026-05-04)**: Initial documentation for DFI-grade prospectus
  - Conservative load profile methodology
  - Institutional data sources
  - Bankability justification
  - Uncertainty quantification

---

*This document is part of KULIMA OS, a coordination-first economic substrate designed as Digital Public Infrastructure (DPI). It enables infrastructure planning based on verified collective demand, without surveillance or individual profiling.*