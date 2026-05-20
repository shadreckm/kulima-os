# Kulima OS API Documentation

## Overview
Kulima OS API provides RESTful endpoints for coordination intelligence processing, signal management, and prospectus generation.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently no authentication required (development mode). Production will use API key authentication.

## Endpoints

### Health Check

#### GET /health
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "engines": "operational",
  "timestamp": "2026-05-20T10:00:00Z"
}
```

### Signals

#### POST /signal
Receive activity input from WhatsApp or manual entry.

**Request Body:**
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

**Error Response:**
```json
{
  "detail": "Error message"
}
```

#### GET /signals/{zone}
Get signals for a specific zone.

**Parameters:**
- `zone` (path): Zone name (e.g., "MZUZU")
- `limit` (query, optional): Maximum number of signals to return (default: 100)

**Response:**
```json
{
  "zone": "MZUZU",
  "signals": [],
  "total": 0,
  "limit": 100
}
```

### Summaries

#### GET /summary/{zone}
Return coordination summary for a zone.

**Parameters:**
- `zone` (path): Zone name (e.g., "MZUZU")

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

#### GET /zones
List all available zones.

**Response:**
```json
{
  "zones": ["MZUZU", "LILONGWE", "BLANTYRE", "ZOMBA"],
  "total": 4
}
```

### Prospectus

#### POST /generate-prospectus
Trigger PDF generation for a zone.

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
  "prospectus_id": "pros_abc123",
  "pdf_url": "https://api.kulimaos.artifacts/prospectus_abc123.pdf",
  "json_url": "https://api.kulimaos.artifacts/prospectus_abc123.json",
  "generated_at": "2026-05-20T10:00:00Z"
}
```

#### GET /prospectus/{prospectus_id}
Get prospectus details by ID.

**Parameters:**
- `prospectus_id` (path): Prospectus ID (e.g., "pros_abc123")

**Response:**
```json
{
  "prospectus_id": "pros_abc123",
  "status": "found",
  "metadata": {}
}
```

### WhatsApp Webhook

#### POST /webhook/whatsapp
Receive WhatsApp messages via webhook.

**Request Body:**
```json
{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              {
                "from": "1234567890",
                "text": {
                  "body": "irrigation morning"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**Response:**
```json
{
  "status": "received"
}
```

#### GET /webhook/whatsapp/verify
Verify WhatsApp webhook.

**Parameters:**
- `hub_mode` (query): "subscribe"
- `hub_verify_token` (query): Verification token
- `hub_challenge` (query): Challenge string

**Response:**
Returns the challenge string if verification succeeds.

## Data Models

### Signal
```json
{
  "id": "sig_abc123",
  "zone": "MZUZU",
  "activity_type": "irrigation",
  "time_window": "morning",
  "timestamp": "2026-05-20T10:00:00Z",
  "source": "whatsapp",
  "user_id": "user_123",
  "created_at": "2026-05-20T10:00:00Z"
}
```

### Pattern
```json
{
  "id": "pat_abc123",
  "zone": "MZUZU",
  "activity_type": "irrigation",
  "confidence_class": "high",
  "stability_score": 0.85,
  "demand_rhythm": {
    "time_window": "morning",
    "frequency": "6 of 7 cycles"
  },
  "evaluation_window": "7-cycle window",
  "created_at": "2026-05-20T10:00:00Z"
}
```

### Prospectus
```json
{
  "id": "pros_abc123",
  "zone": "MZUZU",
  "user_id": "user_123",
  "pdf_url": "https://api.kulimaos.artifacts/prospectus_abc123.pdf",
  "json_url": "https://api.kulimaos.artifacts/prospectus_abc123.json",
  "metadata": {
    "is_sample": false,
    "pilot_region": "MZUZU",
    "evaluation_period": "7-cycle window"
  },
  "created_at": "2026-05-20T10:00:00Z"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting
Currently no rate limiting (development mode). Production will implement rate limiting.

## CORS
CORS is enabled for all origins in development mode. Production will restrict to specific origins.

## Testing
Use the interactive API documentation at `/docs` (Swagger UI) or `/redoc` (ReDoc) to test endpoints.

## WebSocket Support
WebSocket support will be added for real-time updates in future versions.
