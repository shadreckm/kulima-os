# PPSG - Privacy-Preserving Signal Gateway

**Reference Implementation v1.0 for KULIMA OS**

---

## What This Is

This is a **reference implementation** of the Privacy-Preserving Signal Gateway (PPSG) as specified in `PPSG_SPECIFICATION.md`. It is a cryptographically and architecturally defensive ingestion gateway that converts decentralized, voluntary activity declarations into coordination-ready signals without identifying, profiling, or tracking any individual.

**Purpose**: Demonstrate that coordination intelligence for infrastructure planning can be built with Zero-PII enforcement, Temporal Moat protection, and anti-gaming defenses—without surveillance or individual tracking.

**Status**: FROZEN. This implementation is complete and audit-ready. Changes require ethics and architecture review.

---

## What This Is NOT

- ❌ NOT an app, product, or service
- ❌ NOT a data collection pipeline or reporting tool
- ❌ NOT a user-facing application
- ❌ NOT a production-scale deployment (reference correctness only)
- ❌ NOT a platform for surveillance, profiling, or tracking
- ❌ NOT a credit scoring or eligibility gating system

**This is infrastructure code designed under adversarial assumptions for audit, review, and pilot preparation.**

---

## System Invariants

The implementation enforces these non-negotiable constraints:

1. **Zero-PII**: No personal identifiers may enter, transit, or persist
2. **No Identity, Ever**: No accounts, authentication, or persistent identifiers
3. **Temporal Moat**: No real-time processing (6-hour batch windows)
4. **Strict Schema**: Only four fields allowed, no extras
5. **Guaranteed Deletion**: Raw signals deleted after batch handoff

## Architecture

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

## Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Install Dependencies

```bash
cd ppsg
pip install -r requirements.txt
```

## Running the Gateway

### Start the Server

```bash
# From the ppsg directory
python -m ppsg.gateway

# Or with custom host/port
python -c "from ppsg.gateway import run_gateway; run_gateway(host='0.0.0.0', port=8000)"
```

The gateway will start on `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. POST /signal/submit

Submit a coordination signal.

**Request Body** (STRICT - only these four fields):
```json
{
  "activity_type": "irrigation",
  "time_window": "morning",
  "zone_id": "zone_a",
  "signal_source_type": "human"
}
```

**Allowed Values**:
- `activity_type`: `irrigation`, `milling`, `cold_storage`, `welding`, `clinic`, `school`, `water_system`, `emergency_services`
- `time_window`: `morning`, `afternoon`, `evening`
- `zone_id`: `zone_a`, `zone_b`, `zone_c`
- `signal_source_type`: `human`, `device`, `proxy`

**Success Response** (202 Accepted):
```json
{
  "status": "queued",
  "batch_window": "2026-05-04T06:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: PII detected, schema violation, or invalid zone
- `429 Too Many Requests`: Rate limit exceeded

### 2. GET /health

Health check endpoint.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "buffer_size": 42,
  "last_batch_handoff": "2026-05-04T06:00:00Z"
}
```

### 3. GET /zones

Get approved zone whitelist.

**Response** (200 OK):
```json
{
  "zones": [
    {"id": "zone_a", "type": "rural_agricultural"},
    {"id": "zone_b", "type": "peri_urban"},
    {"id": "zone_c", "type": "informal_settlement"}
  ]
}
```

## Testing

### Run All Tests

```bash
# From the ppsg directory
pytest test_ppsg.py -v
```

### Test Coverage

The test suite covers:
- ✅ PII rejection (phone numbers, GPS, UUIDs)
- ✅ Extra field rejection
- ✅ Volume amplification attack defense
- ✅ Synthetic uniform signal attack defense
- ✅ Raw data deletion after batch
- ✅ Schema validation
- ✅ Rate limiting
- ✅ Endpoint functionality

## Example Usage

### Valid Signal Submission

```bash
curl -X POST http://localhost:8000/signal/submit \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "irrigation",
    "time_window": "morning",
    "zone_id": "zone_a",
    "signal_source_type": "human"
  }'
```

### Invalid Signal (Extra Field)

```bash
curl -X POST http://localhost:8000/signal/submit \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "irrigation",
    "time_window": "morning",
    "zone_id": "zone_a",
    "signal_source_type": "human",
    "user_id": "user123"
  }'
```

**Response**: `422 Unprocessable Entity` (extra field rejected)

### Invalid Signal (PII)

```bash
curl -X POST http://localhost:8000/signal/submit \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "irrigation",
    "time_window": "morning",
    "zone_id": "-1.286389,36.817223",
    "signal_source_type": "human"
  }'
```

**Response**: `400 Bad Request` (GPS coordinates detected)

## Anti-Gaming Mechanisms

The gateway implements five defense mechanisms:

1. **Temporal Friction**: Requires persistence across 5+ of 7 cycles (weeks)
2. **Volume Dampening**: Logarithmic weighting prevents amplification
   - 1 signal → weight 1.0
   - 100 signals → weight 4.6 (not 100)
   - 1000 signals → weight 6.9 (not 1000)
3. **Pattern Entropy Checks**: Detects overly uniform submissions, down-weights by 50%
4. **Cross-Source Dependence**: Confidence increases when human + device + proxy signals align
5. **Rate Limiting**: 100 signals/hour per zone, 500/hour per source_type (no individual tracking)

## File Structure

```
ppsg/
├── __init__.py              # Package initialization
├── gateway.py               # Main FastAPI gateway (3 endpoints)
├── pii_filter.py            # PII detection and granularity validation
├── anti_gaming.py           # Anti-gaming and manipulation resistance
├── batch_processor.py       # Ephemeral buffer and batch processing
├── test_ppsg.py             # Test suite
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Security Guarantees

This implementation makes it **technically impossible** to:

1. **Track Individuals**: No persistent identifiers accepted or stored
2. **Build Behavioral Profiles**: No individual-level data retained
3. **Reconstruct Individual Activity**: Raw signals deleted after batch handoff
4. **Convert Coordination Signals into Control Signals**: No real-time processing, no individual outputs

## Audit Compliance

The implementation is designed to be defensible under audit:

- All PII rejection logic is explicit and testable
- Raw signal deletion is guaranteed and irreversible
- No durable storage of individual-level data
- Rate limiting is zone-level, not individual-level
- Batch processing enforces Temporal Moat (6-hour windows)

## What This System Refuses to Do

The PPSG is architecturally designed to make the following **technically impossible**:

1. ❌ **Track Individuals**: No persistent identifiers, no session management, no behavioral histories
2. ❌ **Build Profiles**: No individual-level data retained beyond 2-hour TTL
3. ❌ **Reconstruct Activity**: Raw signals deleted irreversibly after batch handoff
4. ❌ **Real-Time Surveillance**: 6-hour batch windows prevent real-time monitoring
5. ❌ **Credit Scoring**: No reputation metrics, no individual trust scores
6. ❌ **Eligibility Gating**: No access control based on signals
7. ❌ **Behavioral Prediction**: No individual forecasting or profiling
8. ❌ **Identity Correlation**: No linking of signals to specific people or devices

**Refusal is architectural, not policy.** These capabilities cannot be added without violating system invariants.

---

## Demonstration Validation

### Expected Behaviors

#### 1. Valid Signal Acceptance
```bash
curl -X POST http://localhost:8000/signal/submit \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "irrigation",
    "time_window": "morning",
    "zone_id": "zone_a",
    "signal_source_type": "human"
  }'
```
**Expected**: `202 Accepted` with batch window timestamp

#### 2. PII Rejection
```bash
curl -X POST http://localhost:8000/signal/submit \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "irrigation",
    "time_window": "morning",
    "zone_id": "-1.286389,36.817223",
    "signal_source_type": "human"
  }'
```
**Expected**: `400 Bad Request` - GPS coordinates detected and rejected

#### 3. Extra Field Rejection
```bash
curl -X POST http://localhost:8000/signal/submit \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "irrigation",
    "time_window": "morning",
    "zone_id": "zone_a",
    "signal_source_type": "human",
    "user_id": "user123"
  }'
```
**Expected**: `422 Unprocessable Entity` - Extra field rejected by Pydantic

#### 4. Volume Amplification Defense
Submit 100 identical signals within batch window:
- **Expected**: Deduplicated to 1 signal with weight ~4.6 (not 100)
- **Mechanism**: Logarithmic dampening prevents volume amplification

#### 5. Batch Processing & Deletion
After 6-hour batch window:
- **Expected**: Raw signals aggregated and deleted from buffer
- **Verification**: Buffer size returns to 0, only aggregated patterns remain
- **Guarantee**: Raw signals cannot be recovered or reconstructed

### Test Suite Validation
```bash
pytest test_ppsg.py -v
```
**Expected**: All tests pass, demonstrating:
- PII rejection (phone, GPS, UUID)
- Schema validation (extra fields, invalid enums)
- Anti-gaming (volume dampening, entropy detection)
- Batch processing (deduplication, deletion)
- Endpoint functionality (health, zones)

---

## Audit Self-Check

### Invariant Verification

✅ **Zero-PII Enforced**:
- PII detection at ingestion (phone, GPS, UUID, MAC, IMEI patterns)
- Immediate rejection of signals containing PII
- No PII stored or transmitted

✅ **No Identity, Ever**:
- No user accounts or authentication
- No persistent identifiers (even pseudonymous)
- No session management or tracking cookies
- Rate limiting by zone/source, not by individual

✅ **Temporal Moat Protected**:
- 6-hour batch windows (no real-time processing)
- No streaming or event-by-event correlation
- Timestamps not preserved beyond batch window

✅ **Strict Schema Enforced**:
- Pydantic model with `extra="forbid"`
- Only four fields allowed, no extras
- All enum values validated against whitelist

✅ **Guaranteed Deletion**:
- Raw signals deleted after batch handoff
- No archival, no backup, no recovery
- Buffer cleared irreversibly

✅ **System Fails CLOSED**:
- Invalid signals rejected by default
- No fallback to permissive mode
- Errors do not expose signal content

✅ **No Cloud Dependencies**:
- Runs locally with in-memory storage
- No external databases or services required
- No telemetry or analytics sent to third parties

### Deployment Independence

This reference implementation:
- ✅ Runs on localhost without internet connection
- ✅ Uses only in-memory storage (no database)
- ✅ Has no external service dependencies
- ✅ Can be audited offline

---

## Production Deployment Notes

**IMPORTANT**: This is a reference implementation for audit and pilot preparation, NOT a production deployment.

For production deployment, consider:
1. **Message Queue Integration**: Replace stub LUMOZA handoff with RabbitMQ/Kafka
2. **Distributed Buffer**: Use Redis for ephemeral buffer across multiple gateway instances
3. **Monitoring**: Add Prometheus metrics (operational only, no signal content)
4. **TLS/HTTPS**: Enforce HTTPS in production
5. **Rate Limiting**: Consider distributed rate limiting (Redis-based)

**MUST NOT Add**:
- User authentication or accounts
- Individual-level logging or tracking
- Persistent storage of raw signals
- Real-time processing or streaming
- Any feature that violates system invariants

---

## Release Status

**Version**: ppsg-reference-v1.0
**Status**: FROZEN
**Date**: 2026-05-04

This implementation is **complete and audit-ready**. It demonstrates that coordination intelligence can be built with Zero-PII enforcement, Temporal Moat protection, and anti-gaming defenses—without surveillance or individual tracking.

**Changes to this implementation require**:
- Ethics review
- Architecture review
- Verification that system invariants are preserved

**This artifact is intended for**:
- Auditors and ethics reviewers
- Institutional partners evaluating KULIMA OS
- Pilot preparation and deployment planning
- Reference correctness validation

**This artifact is NOT intended for**:
- Production-scale deployment (reference only)
- Feature expansion or scope creep
- Convenience-driven compromises

---

## Reference Documentation

- **PPSG_SPECIFICATION.md**: Complete specification (1,089 lines)
- **SPECIFICATION.md**: KULIMA OS canonical specification
- **AGENTS.md**: System invariants and architectural principles
- **RELEASE_NOTES.md**: Frozen status declaration and version history

---

## License

This reference implementation is part of the KULIMA OS project.

**PPSG**: Privacy-Preserving Signal Gateway for KULIMA OS
**Version**: ppsg-reference-v1.0
**Status**: FROZEN - Reference Implementation (Production-Faithful)