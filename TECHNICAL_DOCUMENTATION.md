# Kulima OS Intelligence System – Technical Documentation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture Diagram](#3-architecture-diagram)
4. [End-to-End Workflow](#4-end-to-end-workflow)
5. [Backend System (FastAPI)](#5-backend-system-fastapi)
6. [Intelligence Engine Layer](#6-intelligence-engine-layer)
7. [Data Model](#7-data-model)
8. [Frontend Application](#8-frontend-application)
9. [Twilio Integration](#9-twilio-integration)
10. [Prospectus Generation System](#10-prospectus-generation-system)
11. [Error Handling & Stability](#11-error-handling--stability)
12. [Deployment Architecture](#12-deployment-architecture)
13. [Security Considerations](#13-security-considerations)
14. [Future Improvements](#14-future-improvements)
15. [Appendix](#15-appendix)

---

## 1. Executive Summary

### What the System Does

Kulima OS is a coordination-first infrastructure planning system that transforms real-world activity into decision-grade intelligence without relying on identity or assumptions. The system collects identity-free coordination signals from WhatsApp messages and web inputs, processes them through three intelligence engines (LUMOZA, LUNDAI, ZENTARI), and generates verified, bankable demand signals for infrastructure planning.

### Problem It Solves

Many infrastructure investments fail because they are based on assumptions rather than real activity data. Traditional approaches rely on surveys, projections, or individual credit scoring—all of which can be inaccurate, expensive, or ethically problematic. Kulima OS solves this by:

- Using actual observed activity patterns instead of assumptions
- Operating without individual tracking or profiling
- Providing explainable, auditable coordination intelligence
- Enabling data-driven infrastructure investment decisions

### Key Outcomes

- **Verified Demand Signals**: Coordination patterns that prove productive energy demand exists
- **Bankable Intelligence**: Confidence scores that institutional investors can trust
- **Privacy-Preserving**: Zero-PII operation that never tracks individuals
- **Explainable Decisions**: Every recommendation includes clear justification
- **Real-Time Insights**: Live dashboard showing coordination patterns as they emerge

---

## 2. System Overview

### Platform Description

Kulima OS is an Epistemic Digital Public Infrastructure (DPI) designed specifically for infrastructure planning in rural and informal economies. It operates as a full-stack system with:

- **Backend**: FastAPI-based REST API with coordination intelligence engines
- **Frontend**: Next.js web application for signal submission and visualization
- **Integration**: Twilio webhook for WhatsApp message processing
- **Intelligence Layer**: Three specialized engines (LUMOZA, LUNDAI, ZENTARI)
- **Output**: Demand-Signal Prospectus in PDF and JSON formats

### Core Use Case

**WhatsApp → Intelligence → Output**

1. Farmers and traders send WhatsApp messages describing their activities (e.g., "watering crops in Mzuzu this morning")
2. Twilio webhook receives and normalizes messages into structured signals
3. Signals flow through three intelligence engines:
   - LUMOZA: Detects coordination patterns across 7-cycle windows
   - LUNDAI: Analyzes settlement context and infrastructure gaps
   - ZENTARI: Evaluates coordination confidence and trustworthiness
4. System generates summaries, visualizations, and detailed prospectus reports
5. Frontend displays real-time insights and enables report generation

### Key Features

- **Identity-Free Operation**: Never tracks individuals or uses personal data
- **Multi-Channel Input**: WhatsApp, web forms, and API endpoints
- **Real-Time Processing**: Live coordination pattern detection
- **Confidence Scoring**: Bankable trust metrics for each pattern
- **Prospectus Generation**: Professional PDF reports for institutional use
- **Visualization API**: Time-series, flow networks, and pattern evolution charts
- **Auto-Refresh UI**: Frontend automatically updates after signal submission
- **Error Handling**: Comprehensive logging and graceful degradation

---

## 3. Architecture Diagram

### Component Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL INPUTS                              │
├──────────────────────┬──────────────────────┬─────────────────────────┤
│   WhatsApp Messages │      Web Forms       │      API Calls         │
│   (Twilio Webhook)   │   (Frontend UI)      │   (Direct Integration)  │
└──────────┬───────────┴──────────┬───────────┴──────────┬──────────────┘
           │                      │                      │
           ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Port 8000)                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Twilio     │  │   Signals    │  │  Summaries   │              │
│  │   Router     │  │   Router     │  │   Router     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                  │                      │
│         ▼                  ▼                  ▼                      │
│  ┌──────────────────────────────────────────────────────┐           │
│  │              SIGNAL NORMALIZER                       │           │
│  │  (Natural language → Structured signal)              │           │
│  └──────────────────────┬───────────────────────────────┘           │
│                         │                                          │
│                         ▼                                          │
│  ┌──────────────────────────────────────────────────────┐           │
│  │              SQLITE DATABASE                         │           │
│  │  (Signals, Patterns, Prospectus, Users, Zones)       │           │
│  └──────────────────────┬───────────────────────────────┘           │
│                         │                                          │
│                         ▼                                          │
│  ┌──────────────────────────────────────────────────────┐           │
│  │         INTELLIGENCE ENGINE LAYER                    │           │
│  ├──────────────┬──────────────┬──────────────────────┤           │
│  │   LUMOZA     │   LUNDAI     │     ZENTARI          │           │
│  │  (Patterns)  │  (Context)   │   (Confidence)       │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬─────────┘           │
│         │                  │                  │                      │
│         └──────────────────┴──────────────────┘                      │
│                         │                                          │
│                         ▼                                          │
│  ┌──────────────────────────────────────────────────────┐           │
│  │         PROSPECTUS GENERATOR                           │           │
│  │  (PDF + JSON report generation)                       │           │
│  └──────────────────────┬───────────────────────────────┘           │
│                         │                                          │
│                         ▼                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Prospectus   │  │Visualization │  │   System     │              │
│  │   Router     │  │   Router     │  │   Router     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      OUTPUTS                                         │
├──────────────────────┬──────────────────────┬─────────────────────────┤
│   PDF Prospectus     │   JSON Data          │   Frontend Dashboard    │
│   (File Download)    │   (API Response)     │   (Real-time UI)        │
└──────────────────────┴──────────────────────┴─────────────────────────┘
```

### System Components

**Backend (FastAPI)**
- API Gateway with CORS support
- 7 routers: health, signals, summaries, prospectus, twilio, system, visualization
- SQLite database with SQLAlchemy ORM
- Signal normalization utility
- Configuration management with environment variables

**Intelligence Engines**
- LUMOZA: Temporal coordination pattern detection
- LUNDAI: Settlement context and infrastructure gap analysis
- ZENTARI: Coordination confidence and trust evaluation
- Multi-Sector Coordinator: Cross-sector coordination layer
- Cross-Zone Flow Detector: Regional flow analysis
- Long-Horizon Model: Time-series trend analysis

**Frontend (Next.js)**
- React-based single-page application
- Signal submission form
- Real-time summary dashboard
- Report generation interface
- Auto-refresh after signal submission

**External Integrations**
- Twilio: WhatsApp webhook processing
- Render: Backend deployment platform
- Vercel: Frontend deployment platform (optional)

---

## 4. End-to-End Workflow

### Complete Pipeline: WhatsApp → Intelligence → Output

#### Step 1: Signal Input (WhatsApp)

```
User sends WhatsApp message:
"watering crops in Mzuzu this morning"
         │
         ▼
Twilio receives webhook
         │
         ▼
POST /api/v1/webhook/twilio
         │
         ▼
SignalNormalizer extracts:
- activity_type: "irrigation"
- zone: "MZUZU"
- time_window: "morning"
```

#### Step 2: Signal Storage

```
Normalized signal stored in SQLite:
{
  "id": "sig_abc123",
  "zone": "MZUZU",
  "activity_type": "irrigation",
  "sector": "agriculture",
  "time_window": "morning",
  "timestamp": "2026-05-20T10:00:00Z",
  "source": "whatsapp",
  "user_id": "+265883766348"
}
```

#### Step 3: LUMOZA Pattern Detection

```
LUMOZA processes signals through 7-cycle logic:
- Groups by (activity_type, zone, time_window)
- Counts occurrences across cycles
- Applies thresholds:
  * Stable: ≥5 of 7 cycles
  * Noise: <3 cycles
  * Intermediate: 3-4 cycles

Output:
{
  "activity_type": "irrigation",
  "zone": "MZUZU",
  "time_window": "morning",
  "cycle_count": 6,
  "stability_class": "stable",
  "demand_rhythm": "Tuesday-Thursday mornings"
}
```

#### Step 4: LUNDAI Context Analysis

```
LUNDAI analyzes settlement context:
- Zone metadata (population, infrastructure status)
- Infrastructure gap analysis
- Critical load protection
- Flow graph generation

Output:
{
  "zone": "MZUZU",
  "settlement_type": "urban",
  "infrastructure_status": "partial",
  "infrastructure_gaps": ["three-phase power"],
  "flow_graph": {
    "nodes": [...],
    "edges": [...],
    "total_nodes": 5,
    "total_edges": 8
  }
}
```

#### Step 5: ZENTARI Confidence Evaluation

```
ZENTARI evaluates coordination confidence:
- Weighted model: C = (0.5 × Persistence) + (0.3 × Stability) + (0.2 × Flow Strength)
- Applies planning reserve constraints
- Generates explainability fields

Output:
{
  "activity_type": "irrigation",
  "zone": "MZUZU",
  "coordination_confidence": 0.85,
  "confidence_class": "high",
  "action_allowed": true,
  "explanation": {
    "why_accepted": "Pattern shows strong persistence and stability",
    "why_rejected": null,
    "reserve_explanation": "Reserve buffer sufficient for this demand",
    "human_readable": "Irrigation demand in MZUZU is bankable"
  }
}
```

#### Step 6: Summary Generation

```
GET /api/v1/summary/MZUZU

Response:
{
  "zone": "MZUZU",
  "total_patterns": 5,
  "high_confidence_patterns": 3,
  "moderate_confidence_patterns": 2,
  "productive_activities_detected": ["irrigation", "milling"],
  "key_finding": "Strong coordination patterns detected",
  "updated_at": "2026-05-20T10:00:00Z",
  "pipeline_output": {
    "coordination_patterns": [...],
    "lundai_analysis": {...},
    "flow_graph": {...},
    "confidence_results": [...],
    "risk_model": {...}
  }
}
```

#### Step 7: Prospectus Generation

```
POST /api/v1/generate-prospectus
{
  "zone": "MZUZU",
  "user_id": "user_123"
}

Process:
1. Run full pipeline (LUMOZA → LUNDAI → ZENTARI)
2. Generate prospectus structure
3. Create PDF using ReportLab
4. Save JSON data
5. Store in database

Response:
{
  "status": "success",
  "data": {
    "prospectus_id": "pros_abc123",
    "pdf_url": "/api/v1/download/prospectus_MZUZU_2026-05-20-10-00-00.pdf",
    "json_url": "/api/v1/download/prospectus_MZUZU_2026-05-20-10-00-00.json",
    "generated_at": "2026-05-20T10:00:00Z"
  }
}
```

#### Step 8: File Download

```
GET /api/v1/download/prospectus_MZUZU_2026-05-20-10-00-00.pdf

Response:
- File download with correct media type (application/pdf)
- JSON files served as application/json
```

#### Step 9: Frontend Display

```
Frontend automatically refreshes after signal submission:
- Displays updated summary
- Shows confidence breakdown
- Lists productive activities
- Enables report generation
- Provides download links
```

---

## 5. Backend System (FastAPI)

### API Endpoints Overview

The backend is built with FastAPI and provides 7 routers with comprehensive endpoints for signal processing, intelligence analysis, and report generation.

#### Base Configuration

- **Framework**: FastAPI 0.104+
- **API Prefix**: `/api/v1`
- **Database**: SQLite with SQLAlchemy ORM
- **CORS**: Enabled for all origins (configurable)
- **Logging**: INFO level with structured logging

### Endpoint Details

#### 5.1 Health Endpoints

**GET /api/v1/health**

Health check endpoint for monitoring system status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "engines": "operational",
  "timestamp": "2026-05-20T10:00:00Z"
}
```

**Purpose**: Verify backend is operational and database is connected.

---

#### 5.2 Signal Endpoints

**POST /api/v1/signal**

Create a new coordination signal from structured input.

**Request Body:**
```json
{
  "zone": "MZUZU",
  "activity_type": "irrigation",
  "time_window": "morning",
  "timestamp": "2026-05-20T10:00:00Z",
  "source": "manual",
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "signal_id": "sig_abc123",
    "message": "Signal received and processed"
  }
}
```

**Purpose**: Manual signal submission for testing and integration.

**GET /api/v1/signals/{zone}?limit=100**

Retrieve signals for a specific zone.

**Response:**
```json
{
  "status": "success",
  "data": {
    "zone": "MZUZU",
    "signals": [
      {
        "id": "sig_abc123",
        "zone": "MZUZU",
        "activity_type": "irrigation",
        "sector": "agriculture",
        "time_window": "morning",
        "timestamp": "2026-05-20T10:00:00Z",
        "source": "whatsapp",
        "user_id": "+265883766348",
        "created_at": "2026-05-20T10:00:00Z"
      }
    ],
    "total": 1,
    "limit": 100
  }
}
```

**Purpose**: Query historical signals for a zone.

---

#### 5.3 Summary Endpoints

**GET /api/v1/summary/{zone}**

Generate coordination summary for a zone using full pipeline.

**Response:**
```json
{
  "status": "success",
  "data": {
    "zone": "MZUZU",
    "total_patterns": 5,
    "high_confidence_patterns": 3,
    "moderate_confidence_patterns": 2,
    "zones_with_coordinated_demand": ["MZUZU"],
    "productive_activities_detected": ["irrigation", "milling"],
    "key_finding": "Strong coordination patterns detected",
    "updated_at": "2026-05-20T10:00:00Z",
    "pipeline_output": {
      "coordination_patterns": [...],
      "lundai_analysis": {...},
      "flow_graph": {...},
      "confidence_results": [...],
      "risk_model": {...}
    }
  }
}
```

**Purpose**: Real-time coordination intelligence summary with full pipeline output.

**GET /api/v1/flow-graph/{zone}**

Retrieve flow graph for visualization.

**Response:**
```json
{
  "status": "success",
  "data": {
    "zone": "MZUZU",
    "nodes": [
      {
        "id": "irrigation",
        "type": "activity",
        "count": 15
      }
    ],
    "edges": [
      {
        "source": "irrigation",
        "target": "milling",
        "weight": 0.8
      }
    ],
    "total_nodes": 5,
    "total_edges": 8
  }
}
```

**Purpose**: Network graph data for frontend visualization.

**GET /api/v1/zone-scorecard/{zone}**

Retrieve zone scorecard with comprehensive metrics.

**Response:**
```json
{
  "status": "success",
  "data": {
    "zone": "MZUZU",
    "coordination_score": 0.85,
    "infrastructure_readiness": 0.6,
    "investment_priority": "high",
    "key_metrics": {...}
  }
}
```

**Purpose**: Comprehensive zone assessment for planning decisions.

---

#### 5.4 Prospectus Endpoints

**POST /api/v1/generate-prospectus**

Generate a Demand-Signal Prospectus for a zone.

**Request Body:**
```json
{
  "zone": "MZUZU",
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "prospectus_id": "pros_abc123",
    "pdf_url": "/api/v1/download/prospectus_MZUZU_2026-05-20-10-00-00.pdf",
    "json_url": "/api/v1/download/prospectus_MZUZU_2026-05-20-10-00-00.json",
    "generated_at": "2026-05-20T10:00:00Z"
  }
}
```

**Purpose**: Generate professional PDF and JSON prospectus reports.

**GET /api/v1/prospectus/{prospectus_id}**

Retrieve prospectus details by ID.

**Response:**
```json
{
  "status": "success",
  "data": {
    "prospectus_id": "pros_abc123",
    "zone": "MZUZU",
    "user_id": "user_123",
    "pdf_url": "/api/v1/download/prospectus_MZUZU_2026-05-20-10-00-00.pdf",
    "json_url": "/api/v1/download/prospectus_MZUZU_2026-05-20-10-00-00.json",
    "created_at": "2026-05-20T10:00:00Z"
  }
}
```

**Purpose**: Query prospectus metadata.

**GET /api/v1/download/{filename}**

Download prospectus file (PDF or JSON).

**Response:**
- File download with appropriate media type
- PDF: `application/pdf`
- JSON: `application/json`

**Purpose**: File retrieval for prospectus downloads.

---

#### 5.5 Twilio Endpoints

**POST /api/v1/webhook/twilio**

Twilio webhook endpoint for WhatsApp message processing.

**Request Format (Form Data):**
```
From: whatsapp:+265883766348
Body: watering crops in Mzuzu this morning
MessageSid: SMabc123
```

**Response (TwiML XML):**
```xml
<Response>
  <Message>
🚀 Your activity has been successfully recorded in Kulima OS!

🌱 You are contributing to real insights that help communities plan better farming, energy, and infrastructure.

📊 Every signal you send helps turn local activity into powerful knowledge for smarter decisions.

✅ Keep going — you are part of building a system that transforms how we understand and grow our economy.
  </Message>
</Response>
```

**Purpose**: Receive and process WhatsApp messages from Twilio.

**POST /api/v1/webhook/test**

Test webhook for simulating Twilio messages without actual integration.

**Request Body:**
```json
{
  "from": "+265123456789",
  "body": "watering crops in Mzuzu this morning"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Test signal received and stored",
  "signal_id": "sig_abc123",
  "normalized_signal": {
    "activity_type": "irrigation",
    "zone": "MZUZU",
    "time_window": "morning"
  }
}
```

**Purpose**: Testing and development without Twilio account.

---

#### 5.6 System Endpoints

**GET /api/v1/system/info**

Return system identity and metadata.

**Response:**
```json
{
  "status": "success",
  "data": {
    "name": "KULIMA OS",
    "version": "1.0.0",
    "type": "coordination-first infrastructure planning system",
    "description": "A coordination-first infrastructure planning system that transforms real-world activity into decision-grade intelligence without relying on identity or assumptions.",
    "positioning": "Epistemic Digital Public Infrastructure (DPI) for infrastructure planning",
    "architectural_philosophy": "Planning based on observed coordination patterns across time, space, and sectors — not assumptions or individual data.",
    "invariants": {
      "zero_pii": "Operates only on aggregated patterns (never raw signals or individual data)",
      "coordination_over_identity": "Analyzes collective patterns, not individual behaviors",
      "semantic_guard": "Designed for infrastructure planning, not surveillance or profiling",
      "epistemic_reliability": "Truth from repetition, not reporting or assumptions"
    },
    "core_principles": [
      "Identity-free coordination intelligence",
      "Coordination-driven decision making",
      "Temporally grounded analysis",
      "Decision-oriented outputs"
    ],
    "forbidden_operations": [
      "Track individuals",
      "Infer identity",
      "Perform behavioral prediction",
      "Enable surveillance"
    ]
  }
}
```

**Purpose**: Expose system identity and architectural principles.

**GET /api/v1/system/invariants**

Return system invariants and constraints.

**Response:**
```json
{
  "status": "success",
  "data": {
    "invariants": {
      "zero_pii": "Operates only on aggregated patterns (never raw signals or individual data)",
      "coordination_over_identity": "Analyzes collective patterns, not individual behaviors",
      "semantic_guard": "Designed for infrastructure planning, not surveillance or profiling",
      "epistemic_reliability": "Truth from repetition, not reporting or assumptions"
    },
    "forbidden_operations": [
      "Track individuals",
      "Infer identity",
      "Perform behavioral prediction",
      "Enable surveillance"
    ]
  }
}
```

**Purpose**: Transparency about system constraints and ethical boundaries.

---

#### 5.7 Visualization Endpoints

**GET /api/v1/time-series/{zone}?activity_type=irrigation**

Return time-series data for a zone.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "timestamp": "2026-01-01",
      "activity_type": "irrigation",
      "zone": "MZUZU",
      "frequency": 5,
      "persistence": 0.75,
      "stability": 0.68
    }
  ]
}
```

**Purpose**: Time-series data for trend visualization.

**GET /api/v1/regional-flow**

Return regional flow analysis across zones.

**Response:**
```json
{
  "status": "success",
  "data": {
    "dominant_chains": [...],
    "bottlenecks": [...],
    "cross_zone_flows": [...],
    "regional_flow_network": {...}
  }
}
```

**Purpose**: Regional coordination pattern analysis.

---

## 6. Intelligence Engine Layer

### 6.1 LUMOZA — Coordination Pattern Engine

**Purpose**: Detect stable coordination patterns from identity-free signals using 7-cycle logic.

**Inputs**:
- List of identity-free coordination signals
- Each signal: `{zone, activity_type, time_window, timestamp, source}`

**Outputs**:
- Coordination patterns with demand rhythms
- Stability scores (stable/intermediate/noise)
- Persistence metrics across cycles
- Cycle count and occurrence frequency

**Key Features**:
- **7-Cycle Window**: Patterns must repeat across weekly cycles
- **Stable Threshold**: ≥5 of 7 cycles for stable classification
- **Noise Filtering**: <3 cycles excluded as noise
- **Temporal Moat**: Processes pre-batched windows only (no real-time)
- **Zero-PII**: Groups by activity/zone/time (never individuals)

**Algorithm**:
```
1. Group signals by (activity_type, zone, time_window)
2. Track pattern occurrences across cycles
3. Calculate cycle_count and persistence
4. Apply thresholds:
   - cycle_count ≥ 5: stable
   - cycle_count 3-4: intermediate
   - cycle_count < 3: noise (discard)
5. Generate demand rhythm description
6. Return coordination patterns with metadata
```

**Example Output**:
```json
{
  "activity_type": "irrigation",
  "zone": "MZUZU",
  "time_window": "morning",
  "cycle_count": 6,
  "stability_class": "stable",
  "demand_rhythm": "Tuesday-Thursday mornings",
  "persistence": 0.85,
  "signal_count": 15
}
```

---

### 6.2 LUNDAI — Settlement Context Engine

**Purpose**: Analyze settlement context and infrastructure gaps to strengthen coordination intelligence.

**Inputs**:
- Coordination patterns from LUMOZA
- Zone metadata (population, infrastructure status)
- Planning reserve constraints

**Outputs**:
- Settlement context analysis
- Infrastructure gap identification
- Critical load protection assessment
- Flow graph with nodes and edges
- Integrity scores for signal groups

**Key Features**:
- **Zone Metadata**: Population, settlement type, infrastructure status
- **Gap Analysis**: Identifies missing infrastructure (e.g., three-phase power)
- **Integrity Scoring**: Balances user diversity, time spread, and recurrence
- **Flow Graph**: Network representation of activity sequences
- **Reserve-Aware**: Considers planning reserve in recommendations

**Algorithm**:
```
1. Evaluate signal integrity:
   - user_diversity: unique senders / total signals
   - time_spread: signals distributed across days
   - recurrence: pattern repeating across cycles
   - density_factor: signal count relative to baseline
2. Analyze settlement context:
   - Zone metadata lookup
   - Infrastructure status assessment
   - Critical load protection check
3. Generate flow graph:
   - Nodes: activities and zones
   - Edges: sequence connections with weights
4. Identify infrastructure gaps
5. Return analysis with explainability
```

**Example Output**:
```json
{
  "zone": "MZUZU",
  "settlement_type": "urban",
  "infrastructure_status": "partial",
  "infrastructure_gaps": ["three-phase power"],
  "integrity_score": 0.75,
  "flow_graph": {
    "nodes": [
      {"id": "irrigation", "type": "activity", "count": 15},
      {"id": "milling", "type": "activity", "count": 10}
    ],
    "edges": [
      {"source": "irrigation", "target": "milling", "weight": 0.8}
    ],
    "total_nodes": 5,
    "total_edges": 8
  }
}
```

---

### 6.3 ZENTARI — Coordination Confidence Engine

**Purpose**: Evaluate trustworthiness of coordination patterns for infrastructure planning.

**Inputs**:
- Coordination patterns from LUMOZA
- Planning reserve object
- Flow graph from LUNDAI

**Outputs**:
- Coordination confidence scores (0-1)
- Confidence classification (high/moderate/low)
- Action allowed flag
- Explainability fields for every decision

**Key Features**:
- **Weighted Model**: C = (0.5 × Persistence) + (0.3 × Stability) + (0.2 × Flow Strength)
- **Planning Reserve**: Enforces reserve constraints
- **Explainability**: Every decision includes justification
- **No Credit Scoring**: Evaluates patterns, not people
- **Action Guidance**: Informs planning, not access control

**Algorithm**:
```
1. Calculate weighted confidence:
   - Persistence: pattern occurrence across cycles (from LUMOZA)
   - Stability: variance in pattern occurrence
   - Flow Strength: edge weights in flow graph (from LUNDAI)
2. Apply planning reserve constraints:
   - Check if reserve buffer is sufficient
   - Require planning_reserve validation
3. Classify confidence:
   - ≥0.7: high
   - 0.4-0.7: moderate
   - <0.4: low
4. Generate explainability:
   - why_accepted: reason for acceptance
   - why_rejected: reason for rejection
   - reserve_explanation: reserve constraint details
   - human_readable: plain language summary
5. Return confidence results with explanations
```

**Example Output**:
```json
{
  "activity_type": "irrigation",
  "zone": "MZUZU",
  "coordination_confidence": 0.85,
  "confidence_class": "high",
  "action_allowed": true,
  "explanation": {
    "why_accepted": "Pattern shows strong persistence (0.85) and stability (0.68)",
    "why_rejected": null,
    "reserve_explanation": "Reserve buffer of 20% sufficient for this demand level",
    "human_readable": "Irrigation demand in MZUZU is bankable with high confidence"
  }
}
```

---

### 6.4 Engine Integration

**Pipeline Sequence**:
```
Signals → LUMOZA → LUNDAI → ZENTARI → Summary/Prospectus
```

**Data Flow**:
1. **LUMOZA** processes raw signals → coordination patterns
2. **LUNDAI** adds context → patterns with infrastructure analysis
3. **ZENTARI** evaluates trust → patterns with confidence scores
4. **Summary** aggregates → zone-level intelligence
5. **Prospectus** formats → institutional-grade reports

**Combined Output**:
```json
{
  "coordination_patterns": [...],
  "lundai_analysis": {
    "infrastructure_gaps": [...],
    "flow_graph": {...}
  },
  "confidence_results": [
    {
      "coordination_confidence": 0.85,
      "confidence_class": "high",
      "explanation": {...}
    }
  ],
  "risk_model": {...}
}
```

---

## 7. Data Model

### Database Structure

The system uses SQLite with SQLAlchemy ORM for data persistence. The database contains 5 main tables.

### 7.1 Signal Table

**Purpose**: Store raw coordination signals from all input channels.

**Schema**:
```python
class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(String, primary_key)
    zone = Column(String, nullable=False, index=True)
    activity_type = Column(String, nullable=False)
    sector = Column(String, nullable=False, index=True)
    time_window = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String, nullable=False)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Indexes**:
- `zone`: Fast zone-based queries
- `sector`: Multi-sector analysis
- `timestamp`: Time-based filtering
- `user_id`: Signal source tracking

**Data Lifecycle**:
- **Created**: When signal received from WhatsApp/web/API
- **Processed**: Through LUMOZA engine
- **Retained**: For historical analysis and pattern detection
- **Never Deleted**: Signals are permanent records

---

### 7.2 Pattern Table

**Purpose**: Store coordination patterns detected by LUMOZA.

**Schema**:
```python
class Pattern(Base):
    __tablename__ = "patterns"
    
    id = Column(String, primary_key)
    zone = Column(String, nullable=False, index=True)
    activity_type = Column(String, nullable=False)
    confidence_class = Column(String, nullable=False, index=True)
    stability_score = Column(Float, nullable=False)
    demand_rhythm = Column(Text, nullable=False)  # JSON string
    evaluation_window = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Indexes**:
- `zone`: Zone-based pattern queries
- `confidence_class`: Filter by confidence level

**Data Lifecycle**:
- **Created**: When LUMOZA detects stable pattern
- **Updated**: When pattern re-evaluated
- **Retained**: For trend analysis and persistence tracking

---

### 7.3 Prospectus Table

**Purpose**: Store generated prospectus metadata and file URLs.

**Schema**:
```python
class Prospectus(Base):
    __tablename__ = "prospectuses"
    
    id = Column(String, primary_key)
    zone = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    pdf_url = Column(String, nullable=False)
    json_url = Column(String, nullable=False)
    meta_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Indexes**:
- `zone`: Zone-based prospectus queries
- `user_id`: User-specific prospectus history

**Data Lifecycle**:
- **Created**: When prospectus generated
- **Retained**: For audit trail and download access
- **Files**: PDF and JSON stored in `prospectuses/` directory

---

### 7.4 User Table

**Purpose**: Multi-user support for system access.

**Schema**:
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key)
    phone_number = Column(String, unique=True, nullable=True)
    email = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    role = Column(String, default='user')
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Roles**:
- `user`: Standard access
- `admin`: Administrative access (future)

---

### 7.5 Zone Table

**Purpose**: Store zone metadata for context analysis.

**Schema**:
```python
class Zone(Base):
    __tablename__ = "zones"
    
    id = Column(String, primary_key)
    name = Column(String, nullable=False)
    region = Column(String, nullable=False)
    settlement_type = Column(String, nullable=True)
    infrastructure_status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Settlement Types**:
- `urban`: Urban settlements
- `rural`: Rural settlements
- `peri-urban`: Peri-urban areas

**Infrastructure Status**:
- `full`: Complete infrastructure
- `partial`: Partial infrastructure
- `minimal`: Minimal infrastructure

---

### 7.6 Relationships

**Signal → Pattern**: One-to-many (signals aggregate into patterns)
**Pattern → Prospectus**: One-to-many (patterns included in prospectus)
**User → Signal**: One-to-many (user submits multiple signals)
**User → Prospectus**: One-to-many (user generates multiple prospectus)
**Zone → Signal**: One-to-many (zone contains multiple signals)
**Zone → Pattern**: One-to-many (zone has multiple patterns)

---

## 8. Frontend Application

### Framework and Architecture

**Framework**: Next.js 14.1.0 with React 18.2.0

**Architecture**:
- Client-side rendering (CSR)
- Single-page application (SPA)
- State management with React hooks
- API communication via fetch

### Key Pages

#### 8.1 Main Page (page.jsx)

**Purpose**: Primary user interface for signal submission and intelligence viewing.

**Components**:
- Hero section with system description
- Problem and solution explanation
- How-it-works section (3-step process)
- Interactive demo section:
  - Signal submission form
  - Activity summary dashboard
  - Report generation interface

**State Management**:
```javascript
const [zone, setZone] = useState('MZUZU');
const [summary, setSummary] = useState(null);
const [loading, setLoading] = useState(false);
const [signalLoading, setSignalLoading] = useState(false);
const [reportLoading, setReportLoading] = useState(false);
const [reportData, setReportData] = useState(null);
const [signalForm, setSignalForm] = useState({
  activity_type: '',
  time_window: ''
});
const [message, setMessage] = useState('');
```

---

### 8.2 API Communication

**Base URL Configuration**:
```javascript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
  'https://kulima-os-backend.onrender.com/api/v1';
```

**Environment Variable**: `NEXT_PUBLIC_API_URL`

**API Calls**:

1. **Fetch Summary**:
```javascript
const fetchSummary = async () => {
  setLoading(true);
  try {
    const res = await fetch(`${BASE_URL}/summary/${zone}`);
    const data = await res.json();
    if (data.status === 'success') {
      setSummary(data.data);
    }
  } catch (err) {
    console.error('Error fetching summary:', err);
  } finally {
    setLoading(false);
  }
};
```

2. **Submit Signal**:
```javascript
const handleSignalSubmit = async (e) => {
  e.preventDefault();
  setSignalLoading(true);
  setMessage('');
  try {
    const res = await fetch(`${BASE_URL}/signal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        zone,
        activity_type: signalForm.activity_type,
        time_window: signalForm.time_window,
        source: 'web'
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      setMessage('Activity recorded successfully!');
      setSignalForm({ activity_type: '', time_window: '' });
      // Auto-refresh summary after signal submit
      await fetchSummary();
    } else {
      setMessage('Failed to record activity');
    }
  } catch (err) {
    console.error('Error recording activity:', err);
    setMessage('Error recording activity');
  } finally {
    setSignalLoading(false);
  }
};
```

3. **Generate Report**:
```javascript
const handleGenerateReport = async () => {
  setReportLoading(true);
  setReportData(null);
  setMessage('');
  try {
    const res = await fetch(`${BASE_URL}/generate-prospectus`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ zone })
    });
    
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    
    const data = await res.json();
    
    if (data.status === 'success') {
      setReportData(data.data);
      setMessage('Report generated successfully!');
    } else {
      setMessage('Failed to generate report: ' + (data.data?.error || 'Unknown error'));
    }
  } catch (err) {
    console.error('Error generating report:', err);
    setMessage('Error generating report: ' + err.message);
  } finally {
    setReportLoading(false);
  }
};
```

---

### 8.3 Auto-Refresh Logic

**Implementation**: After successful signal submission, the frontend automatically refreshes the summary data.

**Code**:
```javascript
if (data.status === 'success') {
  setMessage('Activity recorded successfully!');
  setSignalForm({ activity_type: '', time_window: '' });
  // Auto-refresh summary after signal submit
  await fetchSummary();
}
```

**Purpose**: Ensure users see updated coordination patterns immediately after submitting signals.

---

### 8.4 Error Handling

**Frontend Error Handling**:
- HTTP status checking before response parsing
- Detailed error messages with specific error details
- Console.error logging for debugging
- User-friendly error messages in UI

**Example**:
```javascript
if (!res.ok) {
  throw new Error(`HTTP error! status: ${res.status}`);
}

// Later in catch block
setMessage('Error generating report: ' + err.message);
```

---

### 8.5 UI Components

**Signal Submission Form**:
- Zone selector (MZUZU, LILONGWE, BLANTYRE, ZOMBA)
- Activity type dropdown (irrigation, milling, cold storage, welding)
- Time window selector (morning, midday, evening)
- Submit button with loading state

**Activity Summary Dashboard**:
- Insight display (key finding)
- Total activities counter
- Confidence breakdown (high/moderate)
- Activity tags (productive activities detected)

**Report Generation**:
- Generate button with loading state
- Success message with prospectus ID
- Download links for PDF and JSON

---

## 9. Twilio Integration

### Webhook Handling

**Endpoint**: `POST /api/v1/webhook/twilio`

**Purpose**: Receive WhatsApp messages from Twilio and convert them into coordination signals.

### Message Parsing

**Twilio Webhook Format**:
```
From: whatsapp:+265883766348
Body: watering crops in Mzuzu this morning
MessageSid: SMabc123
```

**Parsing Process**:
```python
form_data = await request.form()
from_number = form_data.get('From', '')
message_body = form_data.get('Body', '')
message_sid = form_data.get('MessageSid', '')
```

**Phone Number Extraction**:
```python
phone_number = from_number.replace('whatsapp:', '') if from_number else 'unknown'
```

---

### Signal Normalization

**Process**: Convert natural language text into structured signal.

**Normalizer**: `SignalNormalizer` class in `backend/utils/signal_normalizer.py`

**Activity Type Mapping**:
```python
ACTIVITY_MAPPINGS = {
    'watering': 'irrigation',
    'irrigating': 'irrigation',
    'pumping': 'irrigation',
    'milling': 'milling',
    'grinding': 'milling',
    'cold storage': 'cold storage',
    'refrigeration': 'cold storage',
    'welding': 'welding',
    'metal work': 'welding',
    'selling': 'trading',
    'trading': 'trading',
    # ... more mappings
}
```

**Zone Mapping**:
```python
ZONE_MAPPINGS = {
    'mzuzu': 'MZUZU',
    'lilongwe': 'LILONGWE',
    'blantyre': 'BLANTYRE',
    'zomba': 'ZOMBA',
}
```

**Time Window Mapping**:
```python
TIME_WINDOW_MAPPINGS = {
    'morning': 'morning',
    'am': 'morning',
    'afternoon': 'afternoon',
    'pm': 'afternoon',
    'evening': 'evening',
    'night': 'evening',
}
```

**Example**:
```
Input: "watering crops in Mzuzu this morning"
Output: {
  "activity_type": "irrigation",
  "zone": "MZUZU",
  "time_window": "morning"
}
```

---

### XML (TwiML) Response

**Requirement**: Twilio expects XML response to reply to WhatsApp messages.

**Implementation**:
```python
return Response(
    content="""
<Response>
  <Message>
🚀 Your activity has been successfully recorded in Kulima OS!

🌱 You are contributing to real insights that help communities plan better farming, energy, and infrastructure.

📊 Every signal you send helps turn local activity into powerful knowledge for smarter decisions.

✅ Keep going — you are part of building a system that transforms how we understand and grow our economy.
  </Message>
</Response>
""",
    media_type="application/xml"
)
```

**Purpose**: Provide user feedback via WhatsApp message.

---

### Data Flow: WhatsApp → Signal

```
WhatsApp Message
        │
        ▼
Twilio Webhook (POST /api/v1/webhook/twilio)
        │
        ▼
Parse Form Data (From, Body, MessageSid)
        │
        ▼
Normalize Signal Text
        │
        ▼
Extract: activity_type, zone, time_window
        │
        ▼
Create Signal Record
        │
        ▼
Store in Database (SQLite)
        │
        ▼
Return TwiML XML Response
        │
        ▼
User receives confirmation message
```

---

### Test Webhook

**Endpoint**: `POST /api/v1/webhook/test`

**Purpose**: Simulate Twilio webhook without actual Twilio account.

**Request**:
```json
{
  "from": "+265123456789",
  "body": "watering crops in Mzuzu this morning"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Test signal received and stored",
  "signal_id": "sig_abc123",
  "normalized_signal": {
    "activity_type": "irrigation",
    "zone": "MZUZU",
    "time_window": "morning"
  }
}
```

**Use Case**: Development and testing without Twilio credentials.

---

## 10. Prospectus Generation System

### Report Generation Process

**Endpoint**: `POST /api/v1/generate-prospectus`

**Purpose**: Generate professional Demand-Signal Prospectus for institutional decision-makers.

### Pipeline Steps

```
1. Fetch signals from database
2. Run LUMOZA → LUNDAI → ZENTARI pipeline
3. Generate prospectus structure
4. Create PDF using ReportLab
5. Save JSON data
6. Store metadata in database
7. Return file URLs
```

---

### PDF Generation

**Library**: ReportLab 4.0.7

**Components**:
- Title page with logo
- Executive summary
- Coordination patterns table
- Infrastructure gap analysis
- Confidence scores
- Recommendations
- Appendices

**PDF Structure**:
```python
prospectus = {
  "prospectus_metadata": {
    "title": "KULIMA OS Demand-Signal Prospectus",
    "subtitle": "Verified Coordination Patterns for Infrastructure Planning",
    "generated_at": "2026-05-20T10:00:00Z",
    "pilot_region": "MZUZU",
    "evaluation_period": "7-cycle window (1 week)",
    "system_version": "KULIMA OS Pilot v0.2"
  },
  "document_classification": {
    "document_type": "Demand-Signal Prospectus",
    "classification": "Coordination Intelligence",
    "audience": "Infrastructure Planners",
    "sensitivity": "Public"
  },
  "executive_summary": {...},
  "coordination_patterns": [...],
  "infrastructure_analysis": {...},
  "confidence_assessment": {...},
  "recommendations": [...]
}
```

---

### JSON Output

**Purpose**: Machine-readable prospectus data for API integration.

**Structure**:
```json
{
  "prospectus_metadata": {...},
  "document_classification": {...},
  "executive_summary": {
    "key_findings": [...],
    "total_patterns": 5,
    "high_confidence_patterns": 3,
    "investment_priority": "high"
  },
  "coordination_patterns": [
    {
      "activity_type": "irrigation",
      "zone": "MZUZU",
      "coordination_confidence": 0.85,
      "confidence_class": "high",
      "demand_rhythm": "Tuesday-Thursday mornings",
      "explanation": {...}
    }
  ],
  "infrastructure_analysis": {
    "infrastructure_gaps": ["three-phase power"],
    "critical_load_protection": {...},
    "flow_graph": {...}
  },
  "confidence_assessment": {...},
  "recommendations": [...]
}
```

---

### File Storage

**Directory**: `prospectuses/`

**Naming Convention**:
- PDF: `prospectus_{ZONE}_{TIMESTAMP}.pdf`
- JSON: `prospectus_{ZONE}_{TIMESTAMP}.json`

**Example**:
- `prospectus_MZUZU_2026-05-20-10-00-00.pdf`
- `prospectus_MZUZU_2026-05-20-10-00-00.json`

---

### Retrieval and Download

**Metadata Query**:
```
GET /api/v1/prospectus/{prospectus_id}
```

**File Download**:
```
GET /api/v1/download/{filename}
```

**Media Types**:
- PDF: `application/pdf`
- JSON: `application/json`

---

### Audience-Specific Sections

**Policy Makers**:
- Executive summary with key findings
- Investment priority rankings
- Risk assessment
- Policy recommendations

**Investors**:
- Confidence scores and bankability metrics
- Demand projections
- ROI considerations
- Risk factors

**Infrastructure Planners**:
- Detailed infrastructure gap analysis
- Load distribution estimates
- Phased rollout plans
- Technical specifications

---

## 11. Error Handling & Stability

### Backend Error Handling

**Logging Configuration**:
```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**Error Handling Pattern**:
```python
try:
    # Process request
    pass
except Exception as e:
    logger.error(f"Error: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
    return {
        "status": "error",
        "data": {
            "error": str(e)
        }
    }
```

**Database Error Handling**:
```python
try:
    db.add(signal)
    db.commit()
except Exception as e:
    db.rollback()
    logger.error(f"Database error: {str(e)}")
    raise HTTPException(status_code=500, detail="Database error")
```

---

### API Validation

**Pydantic Models**:
```python
class SignalCreate(BaseModel):
    zone: str = Field(..., min_length=1)
    activity_type: str = Field(..., min_length=1)
    time_window: str = Field(..., min_length=1)
    timestamp: Optional[str] = Field(None)
    source: str = Field(default="manual")
    user_id: Optional[str] = Field(default="anonymous")
```

**Validation**:
- Required fields enforced
- Type checking
- Length constraints
- Default values

---

### Frontend Error Handling

**HTTP Status Checking**:
```javascript
if (!res.ok) {
  throw new Error(`HTTP error! status: ${res.status}`);
}
```

**Error Logging**:
```javascript
catch (err) {
  console.error('Error generating report:', err);
  setMessage('Error generating report: ' + err.message);
}
```

**User Feedback**:
- Loading states for async operations
- Error messages displayed in UI
- Success confirmations
- Graceful degradation

---

### Stability Features

**Database Transactions**:
- Automatic rollback on errors
- Session management
- Connection pooling

**Graceful Degradation**:
- Empty data returns valid structure
- Missing engines return partial results
- File not found returns error message

**Retry Logic**:
- Database connection retry
- API timeout handling
- File operation retry

---

## 12. Deployment Architecture

### Backend Deployment (Render)

**Platform**: Render

**Configuration**:
- **Runtime**: Python 3.14
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port 10000`
- **Environment Variables**:
  - `DATABASE_URL`: SQLite database path
  - `CORS_ORIGINS`: Frontend URL
  - `SECRET_KEY`: Application secret

**Procfile**:
```
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**Dockerfile** (optional):
```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
```

---

### Frontend Deployment (Vercel)

**Platform**: Vercel (optional)

**Configuration**:
- **Framework**: Next.js 14.1.0
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: Backend API URL

**next.config.js**:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {}

module.exports = nextConfig
```

---

### Environment Variables

**Backend (.env)**:
```env
DATABASE_URL=sqlite:///./kulima_os.db
DEBUG=False
CORS_ORIGINS=*
SECRET_KEY=your-secret-key-change-in-production
API_KEY=optional-api-key
LOG_LEVEL=INFO
```

**Frontend (.env.local)**:
```env
NEXT_PUBLIC_API_URL=https://kulima-os-backend.onrender.com/api/v1
```

---

### Production Setup

**Database**:
- SQLite for simplicity (can migrate to PostgreSQL)
- Automatic table creation on startup
- Backup strategy: File-based backup

**File Storage**:
- Prospectus files stored in `prospectuses/` directory
- Served via FastAPI FileResponse
- Can migrate to S3 for scalability

**Monitoring**:
- Health check endpoint: `/api/v1/health`
- Logging to console (can integrate with external logging)
- Error tracking (can integrate with Sentry)

---

## 13. Security Considerations

### API Safety

**CORS Configuration**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Recommendations**:
- Restrict `CORS_ORIGINS` to specific domains in production
- Use HTTPS in production
- Implement rate limiting
- Add API key authentication for sensitive endpoints

---

### Input Validation

**Pydantic Models**:
- Type checking
- Length constraints
- Required field validation
- Default values

**SQL Injection Prevention**:
- SQLAlchemy ORM (parameterized queries)
- No raw SQL execution
- Input sanitization

---

### Secrets Handling

**Environment Variables**:
- Never commit secrets to git
- Use `.env` file (gitignored)
- Use platform-specific secret management (Render, Vercel)

**Sensitive Data**:
- Database credentials
- API keys
- Secret keys
- Twilio credentials

---

### Zero-PII Enforcement

**System Invariants**:
- Operates only on aggregated patterns
- Never stores raw individual data
- No behavioral tracking
- No surveillance capabilities

**Implementation**:
- Signals grouped by activity/zone/time (not individuals)
- User IDs only for source tracking (not profiling)
- No personal data in outputs
- Explainability without exposing individuals

---

## 14. Future Improvements

### AI Enhancements

**Natural Language Processing**:
- Advanced signal normalization using NLP
- Multi-language support
- Context understanding
- Intent detection

**Pattern Recognition**:
- Machine learning for pattern detection
- Anomaly detection
- Predictive modeling
- Adaptive thresholds

---

### Scalability Improvements

**Database Migration**:
- SQLite → PostgreSQL
- Connection pooling
- Read replicas
- Database sharding

**File Storage**:
- Local files → S3/Cloud Storage
- CDN integration
- Caching layer
- Backup automation

**API Scaling**:
- Load balancing
- Horizontal scaling
- Caching (Redis)
- Queue system (Celery)

---

### Monitoring

**Application Monitoring**:
- APM integration (Datadog, New Relic)
- Performance metrics
- Error tracking (Sentry)
- Uptime monitoring

**Business Metrics**:
- Signal volume tracking
- Pattern detection rates
- User engagement
- Prospectus generation statistics

---

### Analytics Dashboards

**Real-Time Dashboard**:
- Signal ingestion rate
- Pattern detection timeline
- Zone-level coordination scores
- Infrastructure gap tracking

**Historical Analysis**:
- Trend visualization
- Seasonal patterns
- Long-term coordination evolution
- Investment impact tracking

---

### Additional Features

**Multi-Channel Input**:
- SMS integration
- Email processing
- Mobile app
- IoT device integration

**Advanced Visualization**:
- Interactive flow graphs
- Geographic mapping
- Time-series animations
- 3D network visualization

**Collaboration Features**:
- Multi-user workspaces
- Comment threads
- Approval workflows
- Audit trails

---

## 15. Appendix

### Tech Stack Summary

**Backend**:
- FastAPI 0.104+ (Web Framework)
- SQLAlchemy 2.0+ (ORM)
- SQLite (Database)
- Uvicorn (ASGI Server)
- ReportLab 4.0.7 (PDF Generation)
- Pydantic 2.5+ (Validation)

**Frontend**:
- Next.js 14.1.0 (Framework)
- React 18.2.0 (UI Library)
- D3.js 7.9.0 (Visualization)

**Intelligence Engines**:
- LUMOZA (Coordination Pattern Detection)
- LUNDAI (Settlement Context Analysis)
- ZENTARI (Coordination Confidence Evaluation)
- Multi-Sector Coordinator (Cross-Sector Coordination)
- Cross-Zone Flow Detector (Regional Flow Analysis)
- Long-Horizon Model (Time-Series Analysis)

**Integrations**:
- Twilio (WhatsApp)
- Render (Backend Deployment)
- Vercel (Frontend Deployment - Optional)

---

### Folder Structure Tree

```
kulima-os-hackathon/
├── backend/
│   ├── api/
│   │   ├── health.py
│   │   ├── signals.py
│   │   ├── summaries.py
│   │   ├── prospectus.py
│   │   ├── twilio.py
│   │   ├── system.py
│   │   └── visualization.py
│   ├── config.py
│   ├── database/
│   │   ├── connection.py
│   │   └── models.py
│   ├── utils/
│   │   └── signal_normalizer.py
│   └── main.py
├── core/
│   ├── lumoza/
│   │   └── lumoza_engine.py
│   ├── lundai/
│   │   └── lundai_engine.py
│   ├── zentari/
│   │   └── zentari_engine.py
│   ├── prospectus/
│   │   └── prospectus_generator.py
│   ├── coordination/
│   │   └── multi_sector_coordinator.py
│   ├── flow/
│   │   └── cross_zone_flow_detector.py
│   ├── temporal/
│   │   └── long_horizon_model.py
│   ├── decision/
│   │   └── decision_engine.py
│   ├── infrastructure/
│   │   └── infrastructure_design.py
│   ├── scenario/
│   │   └── scenario_model.py
│   └── learning/
│       └── learning_layer.py
├── frontend/
│   ├── app/
│   │   ├── page.jsx
│   │   └── layout.jsx
│   ├── components/
│   │   ├── CoordinationMap.jsx
│   │   └── SystemIdentity.jsx
│   ├── package.json
│   └── next.config.js
├── prospectuses/
├── requirements.txt
├── README.md
├── AGENTS.md
├── ARCHITECTURE.md
├── COORDINATION_INTELLIGENCE.md
└── TECHNICAL_DOCUMENTATION.md
```

---

### Key Dependencies

**Backend (requirements.txt)**:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
reportlab>=4.0.7
aiosqlite>=0.19.0
```

**Frontend (package.json)**:
```json
{
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "d3": "^7.9.0"
  }
}
```

---

### API Endpoint Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/v1/health | Health check |
| POST | /api/v1/signal | Create signal |
| GET | /api/v1/signals/{zone} | Get signals |
| GET | /api/v1/summary/{zone} | Get summary |
| GET | /api/v1/flow-graph/{zone} | Get flow graph |
| GET | /api/v1/zone-scorecard/{zone} | Get scorecard |
| POST | /api/v1/generate-prospectus | Generate prospectus |
| GET | /api/v1/prospectus/{id} | Get prospectus |
| GET | /api/v1/download/{filename} | Download file |
| POST | /api/v1/webhook/twilio | Twilio webhook |
| POST | /api/v1/webhook/test | Test webhook |
| GET | /api/v1/system/info | System info |
| GET | /api/v1/system/invariants | System invariants |
| GET | /api/v1/time-series/{zone} | Time-series data |
| GET | /api/v1/regional-flow | Regional flow |

---

### System Invariants

**Zero-PII**: Operates only on aggregated patterns (never raw signals or individual data)

**Coordination > Identity**: Analyzes collective patterns, not individual behaviors

**Semantic Guard**: Designed for infrastructure planning, not surveillance or profiling

**Epistemic Reliability**: Truth from repetition, not reporting or assumptions

---

### Core Principles

- Identity-free coordination intelligence
- Coordination-driven decision making
- Temporally grounded analysis
- Decision-oriented outputs

---

### Forbidden Operations

- Track individuals
- Infer identity
- Perform behavioral prediction
- Enable surveillance

---

## Document Information

**Title**: Kulima OS Intelligence System – Technical Documentation

**Version**: 1.0.0

**Date**: May 23, 2026

**Author**: Kulima OS Development Team

**Purpose**: Comprehensive technical documentation for developers, technical partners, and stakeholders.

---

*End of Document*
