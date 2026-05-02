# KULIMA OS - Pilot Implementation

**Coordination-First Economic Substrate for Infrastructure Planning**

KULIMA OS is Digital Public Infrastructure (DPI) that converts decentralized livelihood activity into verified, bankable coordination signals for infrastructure planning—without surveillance or individual profiling.

## 🎯 Purpose

Make productive-use energy demand visible and trustworthy **BEFORE** infrastructure is deployed, enabling evidence-based investment in rural and informal economies.

## 🛡️ System Invariants

KULIMA OS is built on four non-negotiable architectural constraints:

1. **Zero-PII**: No personal identifiers may ever enter the system
2. **Temporal Moat**: All processing in time-batched windows (no real-time tracking)
3. **Coordination > Identity**: System reasons over collective patterns, never individuals
4. **Semantic Guard**: No surveillance, credit scoring, eligibility gating, or behavioral prediction

## 🏗️ Architecture

### The Three Engines

#### LUMOZA - Livelihood and Energy Coordination Engine
Processes identity-free coordination signals (irrigation, milling, cold storage, welding) into time-batched demand rhythms using 7-cycle logic.

#### LUNDAI - Spatial and Infrastructure Mismatch Engine
*(Conceptual in pilot)* Analyzes infrastructure geometry to identify zones where coordinated demand exists but infrastructure does not.

#### ZENTARI - Trust and Coordination Confidence Engine
Derives trust from coordination pattern stability and validation strength. Trust is a property of coordination, not individuals.

### Output: Demand-Signal Prospectus

A verified, bankable document for institutional decision-makers (utilities, development finance institutions, infrastructure planners) containing:
- Coordination rhythms (when and what types of productive demand exist)
- Infrastructure gaps (where coordinated demand is unserved)
- Coordination confidence (how stable and bankable patterns are)

## 📁 Project Structure

```
kulima-os-hackathon/
├── AGENTS.md                      # System invariants and architectural principles
├── README.md                      # This file
├── pilot_signals.py               # Synthetic coordination signal generation
├── lumoza_engine.py               # LUMOZA coordination engine
├── zentari_engine.py              # ZENTARI trust engine
├── prospectus_generator.py        # Demand-Signal Prospectus generator
├── kulima_pilot_demo.py           # End-to-end demonstration script
└── bob_sessions/                  # IBM Bob session data
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- No external dependencies required (uses only Python standard library)

### Running the Demo

```bash
# Run the complete pilot demonstration
python kulima_pilot_demo.py
```

The demo will:
1. Generate synthetic coordination signals (identity-free)
2. Process signals through LUMOZA (7-cycle coordination logic)
3. Evaluate coordination confidence through ZENTARI
4. Generate a Demand-Signal Prospectus for infrastructure planners

### Generated Outputs

After running the demo, you'll find:
- `demand_signal_prospectus.json` - Machine-readable prospectus
- `demand_signal_prospectus.md` - Human-readable prospectus

## 🔍 Understanding the Pilot

### 7-Cycle Coordination Logic

The pilot uses a 7-cycle (weekly) window that reflects natural livelihood rhythms:
- Agricultural activities follow weekly market cycles
- Milling and processing align with harvest patterns
- Irrigation schedules repeat on weekly intervals
- Cold storage use clusters around market days

**Stable Pattern**: Activity appears in ≥5 of 7 cycles  
**Noise**: Activity appears in <3 of 7 cycles (filtered out)

### Signal Types

1. **Human-Reported Coordination Signals**
   - Activity type (irrigation, milling, cold storage, welding)
   - Approximate time window (morning/afternoon/evening)
   - General zone (coarse spatial granularity)
   - No participant identity or metadata

2. **Infrastructure Telemetry Signals**
   - Shared asset activity (pump runtime, mill usage, cold room power)
   - Aggregated at asset level (not individual connections)
   - Treated as corroboration, not surveillance

### Cross-Signal Validation

LUMOZA cross-validates human signals with infrastructure telemetry:
- Human signals establish coordination patterns
- Telemetry corroborates that energy use occurred
- Alignment increases pattern confidence
- Discrepancies reduce confidence but don't penalize participants

## 📊 Example Output

```
Pattern: zone_a_irrigation_morning
- Frequency: 6 of 7 cycles
- Stability: stable (score: 0.86)
- Validation: strong (6 of 6 cycles corroborated)
- Coordination Confidence: 0.86 (high)
- Infrastructure Implication: Requires reliable morning power for water pumping
```

## 🎓 Key Concepts

### Trust-as-a-Service

ZENTARI replaces credit scoring without creating reputations:
- **High trust** = "this demand pattern is stable and bankable"
- **NOT** = "these people are reliable"

Trust grows when coordination persists. Trust decays when coordination breaks down.

### Social Reserve Policy

20% of infrastructure capacity is reserved for communal productive assets, ensuring infrastructure serves collective economic activity, not just individual consumption.

### Coordination > Surveillance

KULIMA OS demonstrates that:
- Coordination can replace surveillance
- Trust can exist without reputations
- Infrastructure planning can proceed without profiling
- Informal activity can become institution-readable without extraction

## 🔐 Privacy & Ethics

### What KULIMA OS Does NOT Do

- ❌ Track individuals
- ❌ Create credit scores
- ❌ Build reputations
- ❌ Enable surveillance
- ❌ Profile participants
- ❌ Gate access to services
- ❌ Predict individual behavior

### What KULIMA OS DOES Do

- ✅ Process collective coordination patterns
- ✅ Validate demand signals with infrastructure telemetry
- ✅ Generate bankable prospectuses for infrastructure planning
- ✅ Maintain strict privacy through architectural constraints
- ✅ Enable evidence-based investment in informal economies

## 📚 Documentation

- **AGENTS.md**: Complete system invariants, domain context, and architectural principles
- **Source Code**: All modules are heavily commented with invariant enforcement explanations

## 🤝 IBM Bob Dev Day Hackathon

This pilot demonstrates how IBM Bob accelerates complex system design by:
- Maintaining strict adherence to ethical constraints
- Enabling rapid iteration on coordination logic
- Generating comprehensive documentation
- Producing audit-ready code with invariant enforcement

## 🌍 Real-World Impact

KULIMA OS enables:
- **Utilities**: Deploy infrastructure where coordinated demand exists
- **Development Finance**: Invest based on verified collective demand
- **Rural Communities**: Make productive activity visible without surveillance
- **Policy Makers**: Plan infrastructure using evidence, not assumptions

## 📖 Further Reading

For detailed technical documentation, see:
- `AGENTS.md` - System invariants and architectural principles
- Source code comments - Invariant enforcement explanations
- Generated prospectus files - Example institutional outputs

## 🚧 Pilot Status

This is a proof-of-concept implementation for the IBM Bob Dev Day Hackathon. It demonstrates:
- ✅ End-to-end coordination intelligence pipeline
- ✅ Strict invariant compliance
- ✅ Institutional-grade outputs
- ✅ Audit-ready architecture

**Not included in pilot**: LUNDAI spatial engine (conceptual only), real-world data integration, production deployment infrastructure.

## 📄 License

This pilot implementation is created for the IBM Bob Dev Day Hackathon.

---

**KULIMA OS**: Coordination-first infrastructure for the informal economy.  
**Built with**: IBM Bob, Python, and a commitment to ethical Digital Public Infrastructure.