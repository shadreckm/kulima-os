# Kulima OS Architecture Summary

## Overview
Kulima OS has been restored as a true coordination intelligence system with the full pipeline: signals → normalization → LUMOZA → LUNDAI → ZENTARI → summary → prospectus.

## Pipeline Architecture

### 1. Signal Ingestion
- **Frontend Form**: Manual signal submission via web interface
- **Twilio Webhook**: WhatsApp message processing with natural language normalization
- **Signal Normalization**: Maps natural language to structured signals (e.g., "watering crops" → irrigation)

### 2. Signal Normalization (`backend/utils/signal_normalizer.py`)
- Maps common Malawian farming/trading terms to standardized activity types
- Activity mappings: irrigation, milling, cold storage, welding, trading
- Time window mappings: morning, afternoon, evening
- Zone mappings: MZUZU, LILONGWE, BLANTYRE, ZOMBA

### 3. LUMOZA Engine (`core/lumoza/lumoza_engine.py`)
- **Purpose**: Detect coordination patterns across 7-cycle windows
- **Input**: Raw signals with cycle_index
- **Output**: Coordination patterns with demand rhythms and stability scores
- **Key Features**:
  - 7-cycle logic (stable if ≥5 of 7 cycles)
  - Noise filtering (<3 cycles excluded)
  - Cross-validation with telemetry
  - Service priority classification (essential vs productive)

### 4. LUNDAI Engine (`core/lundai/lundai_engine.py`)
- **Purpose**: Evaluate signal integrity and settlement context
- **Input**: Coordination patterns from LUMOZA
- **Output**: Integrity scores, settlement analysis, infrastructure gap evaluation
- **Key Features**:
  - Signal integrity scoring (user diversity, time spread, burst detection)
  - Settlement context inference (rural, peri-urban, market-node)
  - Infrastructure gap detection (critical, severe, moderate, minimal)
  - Planning reserve enforcement

### 5. ZENTARI Engine (`core/zentari/zentari_engine.py`)
- **Purpose**: Evaluate coordination confidence and trust
- **Input**: Coordination patterns with integrity scores
- **Output**: Confidence scores, trust levels, bankability notes
- **Key Features**:
  - Coordination confidence calculation (stability × validation multiplier)
  - Trust scoring (integrity, time span, user diversity, alignment)
  - Demand classification (latent, emerging, active, deployable)
  - Action refusal when trust below threshold

### 6. Summary API (`backend/api/summaries.py`)
- **Endpoint**: `GET /api/v1/summary/{zone}`
- **Pipeline**: Fetch signals → LUMOZA → LUNDAI → ZENTARI → aggregate metrics
- **Output**: Total patterns, confidence breakdown, activities detected, pipeline output

### 7. Prospectus Generation (`backend/api/prospectus.py`)
- **Endpoint**: `POST /api/v1/generate-prospectus`
- **Pipeline**: Fetch signals → LUMOZA → LUNDAI → ZENTARI → generate PDF/JSON
- **Output**: Prospectus ID, PDF URL, JSON URL

### 8. Twilio Integration (`backend/api/twilio.py`)
- **Webhook Endpoint**: `POST /api/v1/webhook/twilio`
- **Test Endpoint**: `POST /api/v1/webhook/test`
- **Flow**: WhatsApp message → normalize → store in database → enter pipeline

## Frontend Integration (`frontend/app/page.jsx`)
- Simple, clean UI with hero, problem, solution, and how-it-works sections
- Activity summary display with confidence breakdown
- Signal form for manual submission
- Prospectus generation with download links
- Inline API calls to backend

## Invariant Compliance
- **Zero-PII**: No individual identifiers in outputs
- **Temporal Moat**: Cycle-level aggregation (no precise timestamps)
- **Coordination > Identity**: Patterns represent collective activity
- **Semantic Guard**: No credit scoring or individual profiling

## Testing
End-to-end test script (`test_end_to_end.py`) validates:
1. Signal submission
2. Summary retrieval
3. Prospectus generation
4. Twilio webhook processing

## Files Modified/Created
- `backend/api/summaries.py` - Updated to use full engine pipeline
- `backend/api/prospectus.py` - Updated to use full engine pipeline
- `backend/api/twilio.py` - Created Twilio webhook integration
- `backend/utils/signal_normalizer.py` - Created signal normalization logic
- `backend/main.py` - Registered Twilio router
- `frontend/app/page.jsx` - Updated to display confidence breakdown
- `test_end_to_end.py` - Created end-to-end test script
