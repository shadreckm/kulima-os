# Privacy-Preserving Signal Gateway (PPSG) – Production Architecture

**Version**: 1.0  
**Status**: Production-Grade Design Specification  
**Date**: 2026-05-04  
**Purpose**: Cryptographically and architecturally defensive ingestion gateway for KULIMA OS

---

## Document Status

This specification defines a production-grade Privacy-Preserving Signal Gateway (PPSG) designed under adversarial assumptions. It converts decentralized, voluntary activity declarations into coordination-ready signals without identifying, profiling, or tracking any individual.

**Design Philosophy**: Defensive by default. Assume misuse attempts. Make surveillance architecturally impossible.

---

## Foundational Principles (Non-Negotiable)

### 1. Authenticity ≠ Truth

The system does NOT verify the truth of any single signal. The system ONLY resists manipulation at scale.

**Authenticity Definition**: "Difficulty of sustained, coordinated falsification over time"

- Individual signals may be false, noisy, or fabricated
- System strength emerges from cross-signal alignment and temporal persistence
- Fake signals that cannot sustain coordination patterns across multiple batches decay naturally
- No individual signal is trusted; only collective patterns are evaluated

### 2. Zero-PII Enforcement

No personal identifiers may enter, transit, or persist in the system.

**Prohibited Data**:
- Names, phone numbers, SIM IDs
- Device fingerprints, MAC addresses, IMEI numbers
- Precise GPS coordinates or street addresses
- Stable identifiers (even pseudonymous or hashed)
- Free-text fields that could contain identifying information
- IP addresses, session tokens, or tracking cookies

**Enforcement**: Any signal containing PII-like patterns MUST be rejected immediately at ingestion.

### 3. No Identity, Ever

- No user accounts or authentication tied to people
- No persistent identifiers (even pseudonymous)
- No login systems or session management
- Repeat signals handled statistically, never personally
- No "reputation" or "trust score" for individuals

### 4. Temporal Moat

- No real-time processing or streaming
- No event-by-event correlation
- No precise timestamps retained beyond batch window
- Minimum batch window: 6 hours (configurable, never less than 4 hours)
- All signals grouped into fixed time windows before processing

---

## System Architecture

### High-Level Flow

```
[Signal Sources] 
    ↓
[Gateway Interface] → [PII Filter] → [Schema Validator] → [Zone Obfuscator]
    ↓
[Ephemeral Intake Buffer] (TTL: 2 hours)
    ↓
[Anti-Gaming Layer] → [Normalization] → [Time-Batch Queue]
    ↓
[Handoff to LUMOZA] (batched, aggregated, identity-free)
    ↓
[Raw Signal Deletion] (guaranteed, irreversible)
```

### Component Descriptions

#### 1. Signal Gateway Interface

**Purpose**: Accept signals from multiple sources while remaining stateless.

**Supported Input Channels**:
- USSD/SMS (via telecom gateway, no caller ID stored)
- Offline field agents (via secure upload, no agent identity retained)
- IoT/meter aggregations (device-level only, no individual connections)
- Web API (no authentication, rate-limited by IP range, not individual)

**Interface Characteristics**:
- Stateless: No session management
- Idempotent: Duplicate submissions within batch window are deduplicated statistically
- Rate-limited: By source type and zone, not by individual
- Low-bandwidth: Minimal payload size (<200 bytes)
- Offline-capable: Accepts batch uploads from intermittent connections

**API Endpoint**:
```
POST /signal/submit
Content-Type: application/json

{
  "activity_type": "irrigation",
  "time_window": "morning",
  "zone_id": "zone_a",
  "signal_source_type": "human"
}
```

**Response**:
```
HTTP 202 Accepted
{
  "status": "queued",
  "batch_window": "2026-05-04T06:00:00Z"
}
```

No unique submission ID is returned. No tracking of individual submissions.

---

#### 2. PII & Granularity Filter

**Purpose**: Detect and reject signals containing PII or overly precise data.

**Detection Rules**:

1. **Phone Number Patterns**:
   - Reject any field matching: `^\+?[0-9]{7,15}$`
   - Reject any field containing: country codes, area codes, or phone-like sequences

2. **GPS Coordinates**:
   - Reject any field matching: `^-?\d+\.\d+,-?\d+\.\d+$`
   - Reject latitude/longitude pairs
   - Reject any precision beyond zone-level (>1km resolution)

3. **Device IDs**:
   - Reject any field matching: UUID patterns, MAC addresses, IMEI patterns
   - Reject any stable identifier longer than 8 characters

4. **Names & Free-Text**:
   - Reject any field containing: alphabetic strings >20 characters
   - Reject any field not in predefined ENUM sets
   - No free-text fields allowed

5. **Temporal Precision**:
   - Reject any timestamp more precise than 1-hour windows
   - Reject any date more precise than current day
   - Convert all times to coarse windows (morning/afternoon/evening)

**Rejection Response**:
```
HTTP 400 Bad Request
{
  "error": "PII_DETECTED",
  "message": "Signal contains prohibited personal identifiers",
  "detail": "Field 'location' contains GPS coordinates"
}
```

**Logging**: Violation events are logged WITHOUT storing payload data. Only metadata: timestamp, source_type, violation_type.

---

#### 3. Zone Obfuscation System

**Purpose**: Map any location hints to pre-approved coarse zones without storing raw coordinates.

**Zone Definition**:
- Zones are predefined, coarse spatial areas (minimum 5km² for rural, 2km² for urban)
- Zone IDs are opaque strings (e.g., "zone_a", "zone_b"), not geographic coordinates
- Zone boundaries are public knowledge, not secret
- No reverse inference of dwellings or routes possible from zone IDs

**Obfuscation Process**:
1. If signal contains location hint (e.g., "near market"), map to predefined zone
2. Discard original location hint immediately
3. Validate zone_id against whitelist of approved zones
4. Reject if zone_id is not in whitelist or is too precise

**Zone Whitelist Example**:
```json
{
  "zone_a": {"type": "rural_agricultural", "area_km2": 12},
  "zone_b": {"type": "peri_urban", "area_km2": 8},
  "zone_c": {"type": "informal_settlement", "area_km2": 5}
}
```

**Rejection for Invalid Zone**:
```
HTTP 400 Bad Request
{
  "error": "INVALID_ZONE",
  "message": "Zone ID not in approved whitelist",
  "detail": "zone_id 'zone_xyz' is not recognized"
}
```

---

#### 4. Schema Validator

**Purpose**: Enforce strict signal schema. Reject any additional fields.

**Allowed Schema (STRICT)**:
```json
{
  "activity_type": "ENUM",
  "time_window": "ENUM",
  "zone_id": "STRING",
  "signal_source_type": "ENUM"
}
```

**Allowed Values**:

- **activity_type**: 
  - Productive: `irrigation`, `milling`, `cold_storage`, `welding`
  - Essential: `clinic`, `school`, `water_system`, `emergency_services`

- **time_window**: 
  - `morning` (06:00-12:00)
  - `afternoon` (12:00-18:00)
  - `evening` (18:00-24:00)

- **zone_id**: 
  - Must match predefined zone whitelist (e.g., `zone_a`, `zone_b`, `zone_c`)

- **signal_source_type**: 
  - `human` (human-reported via USSD/SMS/agent)
  - `device` (IoT/meter aggregation)
  - `proxy` (field agent on behalf of community, no individual identity)

**Validation Rules**:
1. All four fields are REQUIRED
2. No additional fields allowed (reject if present)
3. All values must match ENUM or whitelist
4. Field types must be correct (string, not number or object)
5. No nested objects or arrays allowed

**Rejection for Schema Violation**:
```
HTTP 400 Bad Request
{
  "error": "SCHEMA_VIOLATION",
  "message": "Signal contains invalid or additional fields",
  "detail": "Field 'user_id' is not allowed"
}
```

---

#### 5. Ephemeral Intake Buffer

**Purpose**: Hold raw signals only long enough to normalize, validate, and enqueue into time-batching.

**Buffer Characteristics**:
- **TTL**: 2 hours (configurable, never more than 4 hours)
- **Storage**: In-memory or ephemeral disk (no durable database)
- **Guaranteed Deletion**: After handoff to time-batch queue, raw signals are irreversibly deleted
- **No Archival**: No backup, no recovery, no audit trail of raw signals
- **No Ordering**: Signals are not stored in submission order

**Buffer Operations**:
1. **Enqueue**: Validated signal enters buffer with TTL timestamp
2. **Normalize**: Convert to canonical format (lowercase, trim whitespace)
3. **Deduplicate**: Within batch window, identical signals are counted, not stored repeatedly
4. **Handoff**: When batch window closes, signals are aggregated and passed to time-batch queue
5. **Delete**: Raw signals are deleted from buffer immediately after handoff

**Deduplication Logic**:
- Signals with identical (activity_type, time_window, zone_id, signal_source_type) within same batch window are counted as one signal with weight = count
- No tracking of which specific submissions were duplicates
- Deduplication prevents volume amplification attacks

**Buffer Monitoring**:
- Track: buffer size, TTL violations, handoff success rate
- Do NOT track: individual signal content, submission sources, or temporal patterns

---

## Anti-Gaming & Manipulation Resistance

### Attack Assumption Model

The system must resist:

1. **Single Attacker**: One person submitting many fake signals
2. **Small Coordinated Group**: 5-10 people coordinating to fabricate patterns
3. **Automated Bot Injection**: Scripts submitting synthetic signals at scale
4. **Volume Amplification**: Repeated identical signals to inflate demand
5. **Temporal Gaming**: Submitting signals only during specific windows to fake patterns

### Defense Mechanisms

#### A. Temporal Friction

**Principle**: Ignore isolated or burst-only signals. Require persistence across multiple batches.

**Implementation**:
- Signals are not immediately trusted or acted upon
- LUMOZA requires 5+ of 7 cycles for pattern stability
- One-off signals or burst submissions are filtered as noise
- Coordination confidence grows only with sustained repetition

**Effect**: Attackers must sustain fabrication over weeks, not hours, making attacks costly and detectable.

#### B. Volume Dampening

**Principle**: Diminishing returns for repeated identical signals. Prevent volume amplification.

**Implementation**:
- Within a batch window, identical signals are deduplicated
- Signal weight increases logarithmically, not linearly: `weight = log(1 + count)`
- After deduplication, 100 identical signals have weight ~4.6, not 100
- Prevents attackers from overwhelming system with volume

**Example**:
```
1 signal → weight 1.0
10 signals → weight 2.4
100 signals → weight 4.6
1000 signals → weight 6.9
```

**Effect**: Attackers cannot amplify fake demand through volume alone.

#### C. Pattern Entropy Checks

**Principle**: Detect overly uniform or synthetic-looking submissions. Penalize deterministic repetition.

**Implementation**:
- Calculate entropy of signal distribution within batch window
- Real coordination has natural variance (different time windows, zones, activity types)
- Synthetic signals often have low entropy (same values repeated)
- Signals with entropy below threshold are flagged and down-weighted

**Entropy Calculation**:
```
H = -Σ(p_i * log(p_i))
where p_i = proportion of signals with value i
```

**Threshold**: If entropy < 1.5 bits for any dimension (activity_type, time_window, zone_id), flag batch as suspicious.

**Effect**: Attackers must introduce variance to avoid detection, making coordination harder.

#### D. Cross-Source Dependence

**Principle**: Strength increases only when multiple signal sources align.

**Implementation**:
- Human-only signals have lower initial confidence
- Device-only signals have lower initial confidence
- Confidence increases when human signals align with device/proxy signals
- LUMOZA cross-validates human signals with telemetry at aggregate level

**Confidence Boost**:
```
base_confidence = 0.5 (human-only or device-only)
aligned_confidence = 0.8 (human + device alignment)
strong_confidence = 0.9 (human + device + proxy alignment)
```

**Effect**: Attackers must compromise multiple signal sources to fabricate high-confidence patterns.

#### E. Rate Limiting (Zone-Level, Not Individual)

**Principle**: Limit signal submission rate by zone and source type, not by individual.

**Implementation**:
- Rate limit: 100 signals per zone per hour (configurable)
- Rate limit: 500 signals per source_type per hour (configurable)
- No rate limit per individual (no identity to rate-limit against)
- Excess signals are queued or rejected with backoff

**Effect**: Prevents single-zone flooding attacks while allowing legitimate high-activity zones.

---

## Signal Lifecycle

### Stage 1: Ingestion (0-5 seconds)

1. Signal arrives at Gateway Interface
2. PII Filter scans for prohibited patterns → REJECT if found
3. Schema Validator checks structure → REJECT if invalid
4. Zone Obfuscator maps location to approved zone → REJECT if invalid
5. Signal enters Ephemeral Intake Buffer with TTL

**Outcome**: Signal is queued for batch processing OR rejected with error.

### Stage 2: Normalization (within buffer, <2 hours)

1. Convert to canonical format (lowercase, trim)
2. Deduplicate identical signals within batch window
3. Apply volume dampening (logarithmic weighting)
4. Calculate pattern entropy for batch
5. Flag suspicious batches (low entropy, high volume)

**Outcome**: Normalized, weighted signals ready for batch handoff.

### Stage 3: Batch Handoff (every 6 hours)

1. Batch window closes (e.g., 00:00-06:00)
2. Signals are aggregated by (activity_type, time_window, zone_id, signal_source_type)
3. Aggregated signals passed to time-batch queue for LUMOZA
4. Raw signals deleted from buffer (irreversible)

**Outcome**: Identity-free, aggregated signals enter LUMOZA pipeline. Raw data no longer exists.

### Stage 4: LUMOZA Processing (7-cycle evaluation)

1. LUMOZA receives aggregated signals
2. Applies 7-cycle coordination logic (5+ of 7 for stability)
3. Cross-validates human signals with device signals
4. Outputs demand rhythms and stability scores

**Outcome**: Coordination patterns emerge from sustained, aligned signals. Fake signals decay.

### Stage 5: Deletion Guarantee

1. After batch handoff, raw signals are deleted from buffer
2. No archival, no backup, no recovery
3. Only aggregated patterns persist
4. Individual submissions cannot be reconstructed

**Outcome**: System cannot be used for surveillance or tracking, even if compromised.

---

## API Endpoint Definitions

### 1. Submit Signal

**Endpoint**: `POST /signal/submit`

**Request**:
```json
{
  "activity_type": "irrigation",
  "time_window": "morning",
  "zone_id": "zone_a",
  "signal_source_type": "human"
}
```

**Success Response**:
```
HTTP 202 Accepted
{
  "status": "queued",
  "batch_window": "2026-05-04T06:00:00Z"
}
```

**Error Responses**:

- **PII Detected**:
```
HTTP 400 Bad Request
{
  "error": "PII_DETECTED",
  "message": "Signal contains prohibited personal identifiers"
}
```

- **Schema Violation**:
```
HTTP 400 Bad Request
{
  "error": "SCHEMA_VIOLATION",
  "message": "Signal contains invalid or additional fields"
}
```

- **Invalid Zone**:
```
HTTP 400 Bad Request
{
  "error": "INVALID_ZONE",
  "message": "Zone ID not in approved whitelist"
}
```

- **Rate Limit Exceeded**:
```
HTTP 429 Too Many Requests
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Zone rate limit exceeded",
  "retry_after": 3600
}
```

### 2. Health Check

**Endpoint**: `GET /health`

**Response**:
```
HTTP 200 OK
{
  "status": "healthy",
  "buffer_size": 1247,
  "last_batch_handoff": "2026-05-04T06:00:00Z"
}
```

No sensitive data exposed. Only operational metrics.

### 3. Zone Whitelist (Public)

**Endpoint**: `GET /zones`

**Response**:
```
HTTP 200 OK
{
  "zones": [
    {"id": "zone_a", "type": "rural_agricultural"},
    {"id": "zone_b", "type": "peri_urban"},
    {"id": "zone_c", "type": "informal_settlement"}
  ]
}
```

Public information. No privacy concerns.

---

## Validation & Rejection Rules

### Validation Rules (MUST PASS)

1. **Schema Completeness**: All four required fields present
2. **Schema Strictness**: No additional fields beyond the four allowed
3. **Enum Validity**: All enum values match allowed sets
4. **Zone Whitelist**: zone_id exists in approved whitelist
5. **PII Absence**: No phone numbers, GPS coordinates, device IDs, or names
6. **Temporal Coarseness**: time_window is coarse (morning/afternoon/evening), not precise
7. **Type Correctness**: All fields are strings, not numbers or objects

### Rejection Rules (MUST REJECT)

1. **PII Present**: Any field contains phone number, GPS, device ID, or name pattern
2. **Extra Fields**: Signal contains fields beyond the four allowed
3. **Invalid Enum**: activity_type, time_window, or signal_source_type not in allowed set
4. **Invalid Zone**: zone_id not in approved whitelist
5. **Overly Precise**: Timestamp more precise than 1-hour window, location more precise than zone
6. **Malformed JSON**: Invalid JSON syntax or structure
7. **Rate Limit**: Zone or source_type rate limit exceeded

---

## Anti-Gaming Logic Examples

### Example 1: Volume Amplification Attack

**Attack**: Attacker submits 1000 identical signals for "irrigation" in "zone_a" during "morning".

**Defense**:
1. Deduplication: 1000 signals → 1 signal with count=1000
2. Volume Dampening: weight = log(1 + 1000) = 6.9
3. Pattern Entropy: Low entropy detected (all identical)
4. Down-weighting: Suspicious batch flagged, confidence reduced by 50%
5. Outcome: Effective weight = 6.9 * 0.5 = 3.45 (not 1000)

**Result**: Attack fails to amplify demand. Fake pattern has low confidence.

### Example 2: Coordinated Small Group

**Attack**: 10 people coordinate to submit signals for "milling" in "zone_b" during "afternoon" for 7 consecutive days.

**Defense**:
1. Temporal Friction: Signals persist across 7 cycles (meets 5+ threshold)
2. Cross-Source Dependence: Human-only signals have base confidence 0.5
3. LUMOZA Evaluation: Pattern appears stable but lacks device corroboration
4. ZENTARI Confidence: Moderate confidence (0.5-0.6) due to lack of cross-source alignment
5. Outcome: Pattern is noted but not high-confidence (not bankable for infrastructure)

**Result**: Attack creates weak pattern. Requires device/proxy alignment for high confidence.

### Example 3: Automated Bot Injection

**Attack**: Bot submits 10,000 signals with random activity types, time windows, and zones.

**Defense**:
1. Rate Limiting: Zone-level rate limits prevent flooding (100/hour per zone)
2. Pattern Entropy: High entropy detected (random distribution)
3. Temporal Friction: No sustained patterns across multiple cycles
4. LUMOZA Filtering: Random signals do not form stable patterns (fail 5-of-7 threshold)
5. Outcome: Signals are noise, filtered out by LUMOZA

**Result**: Attack fails to create coordination patterns. Noise is discarded.

---

## Example Accepted Signals

### Example 1: Valid Human Signal
```json
{
  "activity_type": "irrigation",
  "time_window": "morning",
  "zone_id": "zone_a",
  "signal_source_type": "human"
}
```
**Status**: ✅ Accepted  
**Reason**: All fields valid, no PII, matches schema

### Example 2: Valid Device Signal
```json
{
  "activity_type": "milling",
  "time_window": "afternoon",
  "zone_id": "zone_b",
  "signal_source_type": "device"
}
```
**Status**: ✅ Accepted  
**Reason**: All fields valid, device-level aggregation, no individual tracking

### Example 3: Valid Essential Service Signal
```json
{
  "activity_type": "clinic",
  "time_window": "morning",
  "zone_id": "zone_c",
  "signal_source_type": "proxy"
}
```
**Status**: ✅ Accepted  
**Reason**: Essential service, proxy submission (field agent), no individual identity

---

## Example Rejected Signals

### Example 1: PII Detected (Phone Number)
```json
{
  "activity_type": "irrigation",
  "time_window": "morning",
  "zone_id": "zone_a",
  "signal_source_type": "human",
  "phone": "+254712345678"
}
```
**Status**: ❌ Rejected  
**Reason**: PII_DETECTED - Field 'phone' contains phone number pattern  
**Response**: HTTP 400 Bad Request

### Example 2: GPS Coordinates
```json
{
  "activity_type": "milling",
  "time_window": "afternoon",
  "zone_id": "zone_b",
  "signal_source_type": "human",
  "location": "-1.286389,36.817223"
}
```
**Status**: ❌ Rejected  
**Reason**: PII_DETECTED - Field 'location' contains GPS coordinates  
**Response**: HTTP 400 Bad Request

### Example 3: Extra Fields (Schema Violation)
```json
{
  "activity_type": "cold_storage",
  "time_window": "evening",
  "zone_id": "zone_a",
  "signal_source_type": "human",
  "user_id": "user123"
}
```
**Status**: ❌ Rejected  
**Reason**: SCHEMA_VIOLATION - Field 'user_id' is not allowed  
**Response**: HTTP 400 Bad Request

### Example 4: Invalid Enum Value
```json
{
  "activity_type": "farming",
  "time_window": "morning",
  "zone_id": "zone_a",
  "signal_source_type": "human"
}
```
**Status**: ❌ Rejected  
**Reason**: SCHEMA_VIOLATION - 'farming' is not a valid activity_type  
**Response**: HTTP 400 Bad Request

### Example 5: Invalid Zone
```json
{
  "activity_type": "irrigation",
  "time_window": "morning",
  "zone_id": "zone_xyz",
  "signal_source_type": "human"
}
```
**Status**: ❌ Rejected  
**Reason**: INVALID_ZONE - 'zone_xyz' not in approved whitelist  
**Response**: HTTP 400 Bad Request

### Example 6: Overly Precise Timestamp
```json
{
  "activity_type": "welding",
  "time_window": "2026-05-04T14:23:17Z",
  "zone_id": "zone_b",
  "signal_source_type": "human"
}
```
**Status**: ❌ Rejected  
**Reason**: SCHEMA_VIOLATION - time_window must be coarse (morning/afternoon/evening), not precise timestamp  
**Response**: HTTP 400 Bad Request

---

## Implementation Pseudocode (Python)

```python
import re
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict
import math

# Configuration
ALLOWED_ACTIVITY_TYPES = [
    "irrigation", "milling", "cold_storage", "welding",
    "clinic", "school", "water_system", "emergency_services"
]
ALLOWED_TIME_WINDOWS = ["morning", "afternoon", "evening"]
ALLOWED_SOURCE_TYPES = ["human", "device", "proxy"]
ZONE_WHITELIST = ["zone_a", "zone_b", "zone_c"]
BATCH_WINDOW_HOURS = 6
BUFFER_TTL_HOURS = 2
ZONE_RATE_LIMIT = 100  # signals per zone per hour
SOURCE_RATE_LIMIT = 500  # signals per source_type per hour

# PII Detection Patterns
PHONE_PATTERN = re.compile(r'^\+?[0-9]{7,15}$')
GPS_PATTERN = re.compile(r'^-?\d+\.\d+,-?\d+\.\d+$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)

# In-memory buffer (ephemeral)
signal_buffer = []
rate_limit_counters = defaultdict(lambda: defaultdict(int))

def detect_pii(signal):
    """Detect PII patterns in signal fields"""
    for key, value in signal.items():
        if isinstance(value, str):
            if PHONE_PATTERN.match(value):
                return f"Field '{key}' contains phone number pattern"
            if GPS_PATTERN.match(value):
                return f"Field '{key}' contains GPS coordinates"
            if UUID_PATTERN.match(value):
                return f"Field '{key}' contains device ID pattern"
            if len(value) > 20 and value.isalpha():
                return f"Field '{key}' contains potential name or identifier"
    return None

def validate_schema(signal):
    """Validate signal schema strictness"""
    required_fields = {"activity_type", "time_window", "zone_id", "signal_source_type"}
    
    # Check for extra fields
    extra_fields = set(signal.keys()) - required_fields
    if extra_fields:
        return f"Extra fields not allowed: {extra_fields}"
    
    # Check for missing fields
    missing_fields = required_fields - set(signal.keys())
    if missing_fields:
        return f"Missing required fields: {missing_fields}"
    
    # Validate enum values
    if signal["activity_type"] not in ALLOWED_ACTIVITY_TYPES:
        return f"Invalid activity_type: {signal['activity_type']}"
    
    if signal["time_window"] not in ALLOWED_TIME_WINDOWS:
        return f"Invalid time_window: {signal['time_window']}"
    
    if signal["signal_source_type"] not in ALLOWED_SOURCE_TYPES:
        return f"Invalid signal_source_type: {signal['signal_source_type']}"
    
    # Validate zone
    if signal["zone_id"] not in ZONE_WHITELIST:
        return f"Invalid zone_id: {signal['zone_id']}"
    
    return None

def check_rate_limit(zone_id, source_type):
    """Check zone and source type rate limits"""
    current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    
    # Zone rate limit
    zone_key = f"zone_{zone_id}_{current_hour}"
    if rate_limit_counters["zone"][zone_key] >= ZONE_RATE_LIMIT:
        return "Zone rate limit exceeded"
    
    # Source type rate limit
    source_key = f"source_{source_type}_{current_hour}"
    if rate_limit_counters["source"][source_key] >= SOURCE_RATE_LIMIT:
        return "Source type rate limit exceeded"
    
    return None

def normalize_signal(signal):
    """Normalize signal to canonical format"""
    return {
        "activity_type": signal["activity_type"].lower().strip(),
        "time_window": signal["time_window"].lower().strip(),
        "zone_id": signal["zone_id"].lower().strip(),
        "signal_source_type": signal["signal_source_type"].lower().strip()
    }

def calculate_entropy(signals):
    """Calculate entropy of signal distribution"""
    from collections import Counter
    import math
    
    # Calculate entropy for each dimension
    activity_counts = Counter(s["activity_type"] for s in signals)
    time_counts = Counter(s["time_window"] for s in signals)
    zone_counts = Counter(s["zone_id"] for s in signals)
    
    def entropy(counts):
        total = sum(counts.values())
        return -sum((count/total) * math.log2(count/total) for count in counts.values() if count > 0)
    
    return {
        "activity_entropy": entropy(activity_counts),
        "time_entropy": entropy(time_counts),
        "zone_entropy": entropy(zone_counts)
    }

def apply_volume_dampening(count):
    """Apply logarithmic dampening to signal count"""
    return math.log(1 + count)

def submit_signal(signal):
    """Main signal submission handler"""
    
    # Step 1: PII Detection
    pii_error = detect_pii(signal)
    if pii_error:
        return {
            "status": 400,
            "error": "PII_DETECTED",
            "message": "Signal contains prohibited personal identifiers",
            "detail": pii_error
        }
    
    # Step 2: Schema Validation
    schema_error = validate_schema(signal)
    if schema_error:
        return {
            "status": 400,
            "error": "SCHEMA_VIOLATION",
            "message": "Signal contains invalid or additional fields",
            "detail": schema_error
        }
    
    # Step 3: Rate Limiting
    rate_error = check_rate_limit(signal["zone_id"], signal["signal_source_type"])
    if rate_error:
        return {
            "status": 429,
            "error": "RATE_LIMIT_EXCEEDED",
            "message": rate_error,
            "retry_after": 3600
        }
    
    # Step 4: Normalize
    normalized = normalize_signal(signal)
    
    # Step 5: Add to buffer with TTL
    signal_entry = {
        "signal": normalized,
        "timestamp": datetime.utcnow(),
        "ttl": datetime.utcnow() + timedelta(hours=BUFFER_TTL_HOURS)
    }
    signal_buffer.append(signal_entry)
    
    # Step 6: Update rate limit counters
    current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    zone_key = f"zone_{signal['zone_id']}_{current_hour}"
    source_key = f"source_{signal['signal_source_type']}_{current_hour}"
    rate_limit_counters["zone"][zone_key] += 1
    rate_limit_counters["source"][source_key] += 1
    
    # Step 7: Return success
    batch_window = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    batch_window = batch_window.replace(hour=(batch_window.hour // BATCH_WINDOW_HOURS) * BATCH_WINDOW_HOURS)
    
    return {
        "status": 202,
        "message": "queued",
        "batch_window": batch_window.isoformat() + "Z"
    }

def process_batch():
    """Process batch window and handoff to LUMOZA"""
    global signal_buffer
    
    # Step 1: Remove expired signals
    now = datetime.utcnow()
    signal_buffer = [s for s in signal_buffer if s["ttl"] > now]
    
    # Step 2: Deduplicate and count
    signal_counts = defaultdict(int)
    for entry in signal_buffer:
        sig = entry["signal"]
        key = (sig["activity_type"], sig["time_window"], sig["zone_id"], sig["signal_source_type"])
        signal_counts[key] += 1
    
    # Step 3: Apply volume dampening
    dampened_signals = []
    for key, count in signal_counts.items():
        weight = apply_volume_dampening(count)
        dampened_signals.append({
            "activity_type": key[0],
            "time_window": key[1],
            "zone_id": key[2],
            "signal_source_type": key[3],
            "weight": weight,
            "raw_count": count
        })
    
    # Step 4: Calculate entropy
    raw_signals = [entry["signal"] for entry in signal_buffer]
    entropy_metrics = calculate_entropy(raw_signals)
    
    # Step 5: Flag suspicious batches (low entropy)
    suspicious = any(e < 1.5 for e in entropy_metrics.values())
    if suspicious:
        # Down-weight all signals in batch by 50%
        for sig in dampened_signals:
            sig["weight"] *= 0.5
            sig["flagged"] = "low_entropy"
    
    # Step 6: Handoff to LUMOZA (aggregated, identity-free)
    handoff_to_lumoza(dampened_signals, entropy_metrics)
    
    # Step 7: Delete raw signals (irreversible)
    signal_buffer = []
    
    return {
        "batch_size": len(dampened_signals),
        "entropy": entropy_metrics,
        "suspicious": suspicious
    }

def handoff_to_lumoza(signals, entropy_metrics):
    """Handoff aggregated signals to LUMOZA pipeline"""
    # This would integrate with LUMOZA's time-batch queue
    # For now, just log the handoff
    print(f"Handoff to LUMOZA: {len(signals)} aggregated signals")
    print(f"Entropy metrics: {entropy_metrics}")
    # In production, this would write to a queue or call LUMOZA API

# Example usage
if __name__ == "__main__":
    # Valid signal
    signal1 = {
        "activity_type": "irrigation",
        "time_window": "morning",
        "zone_id": "zone_a",
        "signal_source_type": "human"
    }
    result1 = submit_signal(signal1)
    print("Valid signal:", result1)
    
    # Invalid signal (PII)
    signal2 = {
        "activity_type": "milling",
        "time_window": "afternoon",
        "zone_id": "zone_b",
        "signal_source_type": "human",
        "phone": "+254712345678"
    }
    result2 = submit_signal(signal2)
    print("Invalid signal (PII):", result2)
    
    # Invalid signal (extra field)
    signal3 = {
        "activity_type": "cold_storage",
        "time_window": "evening",
        "zone_id": "zone_a",
        "signal_source_type": "human",
        "user_id": "user123"
    }
    result3 = submit_signal(signal3)
    print("Invalid signal (extra field):", result3)
```

---

## Security & Deployment Requirements

### Low-Bandwidth First

- Minimal payload size (<200 bytes per signal)
- Supports USSD/SMS (text-only, no rich media)
- Batch uploads for offline/intermittent connections
- Compression for bulk submissions

### Offline/Intermittent Environments

- Signals can be queued locally and uploaded when connection available
- No real-time dependency
- Batch handoff tolerates delays
- No session management or authentication required

### Horizontal Scalability

- Stateless gateway (no session state)
- Ephemeral buffer can be distributed across nodes
- Rate limiting by zone/source, not by individual (no shared state needed)
- Batch processing can be parallelized

### Privacy-Safe Logging

- Log only: timestamp, source_type, violation_type, error_code
- Do NOT log: signal content, PII, individual identifiers
- Logs are aggregated and anonymized
- No correlation of logs to individual submissions

### No Telemetry for Re-Identification

- No tracking of submission sources
- No IP address logging (or log only /24 subnet, not full IP)
- No session tokens or cookies
- No user-agent or device fingerprinting

---

## Absolute Constraints (Enforcement)

This system must make it **technically impossible** to:

1. **Track Individuals**:
   - No persistent identifiers accepted or stored
   - No session management or authentication
   - No correlation of signals to individuals
   - Raw signals deleted after batch handoff

2. **Build Behavioral Profiles**:
   - No individual-level data retained
   - No temporal sequences preserved
   - No spatial precision beyond zone-level
   - No cross-batch correlation of individuals

3. **Reconstruct Individual Activity**:
   - Signals are aggregated before storage
   - Raw signals deleted irreversibly
   - No archival or backup of raw data
   - Deduplication prevents reconstruction

4. **Convert Coordination Signals into Control Signals**:
   - No real-time processing or streaming
   - No individual-level outputs
   - No access control or gating based on signals
   - No feedback loop to individuals

**Enforcement Mechanisms**:
- PII detection at ingestion (reject immediately)
- Schema validation (reject extra fields)
- Ephemeral buffer with guaranteed deletion
- No durable storage of raw signals
- API layer enforces refusal guarantees
- Audit trails verify compliance

---

## Conclusion

This Privacy-Preserving Signal Gateway (PPSG) is designed to be **cryptographically and architecturally defensive** under adversarial conditions. It converts decentralized, voluntary activity declarations into coordination-ready signals without identifying, profiling, or tracking any individual.

**Key Achievements**:
- Zero-PII enforcement at ingestion
- No identity, ever (no accounts, no authentication)
- Temporal moat (no real-time processing)
- Anti-gaming mechanisms (volume dampening, entropy checks, cross-source dependence)
- Guaranteed deletion of raw signals
- Fail-soft under attack (degrades gracefully, no data exposure)

**Design Philosophy**: Assume misuse attempts. Make surveillance architecturally impossible. This is infrastructure, not an app.

---

**Document Version**: 1.0  
**Status**: Production-Grade Design Specification  
**Last Updated**: 2026-05-04  
**Maintained By**: KULIMA OS Security & Privacy Team