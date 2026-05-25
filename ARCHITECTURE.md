# Kulima OS Production Architecture Plan

## Overview
Transition from prototype to production-ready architecture with separated layers, API-first design, and multi-user support.

## Production Readiness
Kulima OS production readiness is defined by the system's ability to deliver institution-grade coordination intelligence while preserving privacy and auditability. The `core/prospectus/prospectus_generator.py` implementation generates a `deployment_readiness` package that covers:

- Infrastructure requirements and sizing
- Critical load protection and social reserve policy
- Stakeholder engagement status
- Regulatory and compliance checklist
- Technical, financial, institutional, and community readiness assessment
- Next steps for deployment

See `PRODUCTION_READINESS.md` for the explicit readiness criteria, artifact mapping, and production deployment checklist.

## Current Architecture (Prototype)
- Monolithic Streamlit application
- JSON file-based storage
- Direct engine calls
- No API layer
- Single-user assumption

## Target Architecture (Production)

### Layer Separation

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend Layer                        │
│  (React/Next.js - Future)                                │
│  - Dashboard UI                                          │
│  - Signal input forms                                    │
│  - Prospectus viewer                                     │
│  - Real-time updates                                     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼ HTTP/REST API
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                    │
│  - POST /signal - Receive activity input                 │
│  - GET /summary/{zone} - Return coordination summary    │
│  - POST /generate-prospectus - Trigger PDF generation   │
│  - GET /zones - List available zones                    │
│  - GET /health - Health check                           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Core Engines Layer                      │
│  - LUMOZA (Coordination Engine)                         │
│  - LUNDAI (Spatial Engine)                              │
│  - ZENTARI (Trust Engine)                               │
│  - Prospectus Generator (PDF)                           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Data Layer (SQLite/PostgreSQL)          │
│  - Signals table                                        │
│  - Patterns table                                       │
│  - Prospectuses table                                   │
│  - Users table                                          │
│  - Zones table                                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              External Integrations                        │
│  - WhatsApp Webhook (Twilio/Meta)                       │
│  - SMS Gateway (optional)                               │
│  - Email notifications (optional)                        │
└─────────────────────────────────────────────────────────┘
```

## Updated Folder Structure

```
kulima-os/
├── backend/                          # FastAPI Backend
│   ├── main.py                      # FastAPI application entry
│   ├── api/                         # API endpoints
│   │   ├── __init__.py
│   │   ├── signals.py               # Signal endpoints
│   │   ├── summaries.py             # Summary endpoints
│   │   ├── prospectus.py            # Prospectus endpoints
│   │   └── health.py                # Health check
│   ├── models/                      # Pydantic models
│   │   ├── __init__.py
│   │   ├── signal.py                # Signal data models
│   │   ├── summary.py               # Summary data models
│   │   └── prospectus.py            # Prospectus data models
│   ├── database/                    # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py           # Database connection
│   │   ├── models.py                # SQLAlchemy models
│   │   └── migrations/              # Database migrations
│   ├── services/                    # Business logic
│   │   ├── __init__.py
│   │   ├── signal_service.py       # Signal processing
│   │   ├── summary_service.py      # Summary generation
│   │   └── prospectus_service.py    # Prospectus generation
│   ├── integrations/                # External integrations
│   │   ├── __init__.py
│   │   ├── whatsapp.py              # WhatsApp webhook
│   │   └── notifications.py         # Email/SMS notifications
│   └── config.py                    # Configuration
│
├── core/                            # Core Engines (extracted)
│   ├── __init__.py
│   ├── lumoza/                      # LUMOZA Engine
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── coordination_accumulation.py
│   │   └── lumoza_integration.py
│   ├── lundai/                      # LUNDAI Engine
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   └── lundai_engine.py
│   ├── zentari/                     # ZENTARI Engine
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   └── zentari_engine.py
│   └── prospectus/                  # Prospectus Generator
│       ├── __init__.py
│       ├── generator.py
│       └── prospectus_generator.py
│
├── frontend/                        # React/Next.js (Future)
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   └── public/
│
├── admin/                           # Streamlit Admin Dashboard
│   ├── admin_dashboard.py           # Temporary admin UI
│   └── requirements.txt
│
├── shared/                          # Shared utilities
│   ├── __init__.py
│   ├── utils.py                     # Common utilities
│   ├── constants.py                 # Constants
│   └── validators.py                # Data validators
│
├── assets/                          # Static assets
│   ├── kulima_africa_logo.png
│   └── shadreck-signature.jpg
│
├── tests/                           # Tests
│   ├── test_api/
│   ├── test_core/
│   └── test_integration/
│
├── .env.example                     # Environment variables template
├── .gitignore
├── requirements.txt                # Python dependencies
├── docker-compose.yml              # Docker configuration
├── Dockerfile.backend              # Backend Dockerfile
├── Dockerfile.frontend             # Frontend Dockerfile
└── README.md
```

## API Endpoints Specification

### POST /api/v1/signal
Receive activity input from WhatsApp or manual entry.

**Request:**
```json
{
  "zone": "MZUZU",
  "activity_type": "irrigation",
  "time_window": "morning",
  "timestamp": "2026-05-20T10:00:00Z",
  "source": "whatsapp",
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "status": "success",
  "signal_id": "sig_abc123",
  "message": "Signal received and processed"
}
```

### GET /api/v1/summary/{zone}
Return coordination summary for a zone.

**Response:**
```json
{
  "zone": "MZUZU",
  "total_patterns": 5,
  "high_confidence_patterns": 3,
  "moderate_confidence_patterns": 2,
  "zones_with_coordinated_demand": ["MZUZU"],
  "productive_activities_detected": ["irrigation", "milling"],
  "key_finding": "Strong coordination patterns detected",
  "updated_at": "2026-05-20T10:00:00Z"
}
```

### POST /api/v1/generate-prospectus
Trigger PDF generation for a zone.

**Request:**
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
  "prospectus_id": "pros_abc123",
  "pdf_url": "https://api.kulimaos.artifacts/prospectus_abc123.pdf",
  "json_url": "https://api.kulimaos.artifacts/prospectus_abc123.json",
  "generated_at": "2026-05-20T10:00:00Z"
}
```

### GET /api/v1/zones
List all available zones.

**Response:**
```json
{
  "zones": ["MZUZU", "LILONGWE", "BLANTYRE", "ZOMBA"],
  "total": 4
}
```

### GET /api/v1/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "engines": "operational",
  "timestamp": "2026-05-20T10:00:00Z"
}
```

## Database Schema

### Signals Table
```sql
CREATE TABLE signals (
    id TEXT PRIMARY KEY,
    zone TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    time_window TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    source TEXT NOT NULL,
    user_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_zone (zone),
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id)
);
```

### Patterns Table
```sql
CREATE TABLE patterns (
    id TEXT PRIMARY KEY,
    zone TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    confidence_class TEXT NOT NULL,
    stability_score REAL NOT NULL,
    demand_rhythm JSON NOT NULL,
    evaluation_window TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_zone (zone),
    INDEX idx_confidence (confidence_class)
);
```

### Prospectuses Table
```sql
CREATE TABLE prospectuses (
    id TEXT PRIMARY KEY,
    zone TEXT NOT NULL,
    user_id TEXT NOT NULL,
    pdf_url TEXT NOT NULL,
    json_url TEXT NOT NULL,
    metadata JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_zone (zone),
    INDEX idx_user_id (user_id)
);
```

### Users Table
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    phone_number TEXT UNIQUE,
    email TEXT UNIQUE,
    name TEXT,
    role TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Zones Table
```sql
CREATE TABLE zones (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    settlement_type TEXT,
    infrastructure_status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Multi-User Support

### User Isolation
- Each signal includes `user_id` for tracking
- Patterns are aggregated across users (coordination patterns, not individual behavior)
- Prospectuses are user-specific artifacts
- No cross-user data leakage

### Scalability
- SQLite for local development (single instance)
- PostgreSQL for production (multi-instance, horizontal scaling)
- Connection pooling
- Query optimization with indexes
- Database migrations for schema versioning

## Deployment Strategy

### Phase 1: Backend API (Render)
1. Set up FastAPI backend
2. Implement SQLite database
3. Deploy to Render
4. Configure environment variables
5. Test API endpoints

### Phase 2: Database Migration
1. Migrate from SQLite to PostgreSQL
2. Set up managed PostgreSQL on Render
3. Run database migrations
4. Test data integrity

### Phase 3: WhatsApp Integration
1. Set up WhatsApp Business API (Twilio/Meta)
2. Configure webhook endpoint
3. Test message reception
4. Implement signal processing

### Phase 4: Frontend Migration
1. Create React/Next.js frontend
2. Implement API client
3. Build dashboard UI
4. Deploy to Vercel
5. Configure CORS

### Phase 5: Admin Dashboard
1. Refactor Streamlit to use API
2. Remove direct engine calls
3. Use API for all data operations
4. Deploy as admin-only interface

## Security Considerations

### API Security
- API key authentication
- Rate limiting
- Input validation
- SQL injection prevention (parameterized queries)
- CORS configuration

### Data Privacy
- Zero-PII enforcement (no personal identifiers in patterns)
- User data isolation
- Encrypted storage for sensitive data
- Audit logging

### WhatsApp Security
- Webhook signature verification
- Message encryption
- Access control

## Monitoring & Observability

### Logging
- Structured logging (JSON format)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Log aggregation (Papertrail/Sentry)

### Metrics
- API response times
- Database query performance
- Signal processing throughput
- Error rates

### Alerts
- API downtime
- Database connection failures
- High error rates
- Unusual traffic patterns

## Next Steps

1. Create backend API structure
2. Implement database layer
3. Extract core engines
4. Build API endpoints
5. Set up WhatsApp integration
6. Test multi-user support
7. Deploy to production
8. Begin frontend migration
