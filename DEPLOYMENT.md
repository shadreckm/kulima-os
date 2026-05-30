# Deployment Guide

## Overview
This guide explains how to deploy Kulima OS to production using Render (backend), Vercel (frontend), and managed database services.

## Prerequisites

- GitHub account
- Render account (free tier available)
- Vercel account (free tier available)
- WhatsApp Business API account (optional)

## Phase 1: Backend Deployment (Render)

### 1. Prepare Repository
Ensure your code is pushed to GitHub with the new structure:
```
kulima-os/
├── backend/
├── core/
├── shared/
├── admin/
├── requirements.txt
├── Dockerfile.backend
└── .env.example
```

### 2. Create Render Service

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure build settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Runtime**: Python 3.11

### 3. Configure Environment Variables

Add these environment variables in Render:

```env
DATABASE_URL=postgresql://user:password@host:port/database
DEBUG=False
SECRET_KEY=your-production-secret-key
API_KEY=your-production-api-key
CORS_ORIGINS=https://your-frontend-domain.vercel.app
WHATSAPP_VERIFY_TOKEN=your-verify-token
```

### 4. Database Setup (PostgreSQL)

1. In Render, create a new PostgreSQL database
2. Copy the internal database URL
3. Add it as `DATABASE_URL` environment variable to your backend service
4. Run migrations (if using Alembic) or let SQLAlchemy create tables

### 5. Deploy

Click "Deploy Web Service". Render will:
- Clone your repository
- Install dependencies
- Start the FastAPI application
- Provide a public URL (e.g., `https://kulima-os-api.onrender.com`)

### 6. Verify Deployment

Check the health endpoint:
```bash
curl https://kulima-os-api.onrender.com/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "engines": "operational",
  "timestamp": "2026-05-20T10:00:00Z"
}
```

## Phase 2: Frontend Deployment (Vercel)

### 1. Create Next.js Project

```bash
npx create-next-app@latest frontend
cd frontend
npm install axios
```

### 2. Configure API Client

Update `frontend/services/api.js`:
```javascript
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || '/api/v1').replace(/\/$/, '');
```

### 3. Create Environment File

Create `.env.local`:
```env
NEXT_PUBLIC_API_URL=https://kulima-os-api.onrender.com/api/v1
```

### 4. Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
5. Add environment variable:
   - `NEXT_PUBLIC_API_URL`: `https://kulima-os-api.onrender.com/api/v1`
6. Click "Deploy"

### 5. Verify Deployment

Visit your Vercel URL and check:
- Dashboard loads correctly
- API calls succeed
- Real-time updates work

## Phase 3: WhatsApp Integration

### 1. Set Up WhatsApp Business API

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create a WhatsApp Business App
3. Get your phone number ID and access token
4. Configure webhook URL: `https://kulima-os-api.onrender.com/api/v1/webhook/whatsapp`
5. Set verify token

### 2. Update Backend Configuration

Add to Render environment variables:
```env
WHATSAPP_WEBHOOK_URL=https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages
WHATSAPP_VERIFY_TOKEN=your-verify-token
```

### 3. Test Webhook

Send a test message to your WhatsApp number and verify:
- Webhook receives the message
- Signal is created in database
- Processing works correctly

## Phase 4: Admin Dashboard

### 1. Deploy Streamlit Admin

Option 1: Streamlit Cloud (Easiest)
1. Push `admin/admin_dashboard.py` to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository and deploy

Option 2: Render
1. Create a new Render web service
2. Build command: `pip install -r requirements.txt`
3. Start command: `streamlit run admin/admin_dashboard.py --server.port $PORT --server.address 0.0.0.0`

### 2. Configure Admin Dashboard

Update admin dashboard to use API instead of direct engine calls:
```python
import requests

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

def get_summary(zone):
    response = requests.get(f"{API_BASE_URL}/summary/{zone}")
    return response.json()
```

## Phase 5: Monitoring

### 1. Enable Render Logs

- Go to your Render service
- Click "Logs" to view real-time logs
- Set up log retention

### 2. Set Up Alerts

Configure Render alerts for:
- Service downtime
- High error rates
- High response times

### 3. Database Monitoring

- Monitor PostgreSQL performance in Render
- Set up backups (automatic in Render)
- Monitor storage usage

## Phase 6: Security

### 1. API Authentication

Implement API key authentication in production:
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
```

### 2. Rate Limiting

Install and configure rate limiting:
```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/signal")
@limiter.limit("10/minute")
async def create_signal(...):
    ...
```

### 3. CORS Configuration

Restrict CORS to specific origins:
```python
CORS_ORIGINS = [
    "https://your-frontend-domain.vercel.app"
]
```

## Phase 7: Multi-User Support

### 1. User Management

The database schema already includes:
- `users` table for user data
- `signals` table with `user_id` for tracking
- `prospectuses` table with `user_id` for ownership

### 2. User Isolation

- Each signal includes `user_id` for tracking
- Patterns are aggregated across users (coordination patterns, not individual behavior)
- Prospectuses are user-specific artifacts
- No cross-user data leakage

### 3. Testing Multi-User Support

Test with multiple users:
1. Create signals from different users
2. Verify patterns aggregate correctly
3. Verify prospectuses are user-specific
4. Verify no data leakage between users

## Troubleshooting

### Backend Issues

**Service won't start:**
- Check Render logs for errors
- Verify environment variables are set
- Check database connection string

**Database connection failed:**
- Verify DATABASE_URL is correct
- Check PostgreSQL service is running
- Test connection locally

**API returns 500 errors:**
- Check application logs
- Verify all dependencies are installed
- Check database schema is correct

### Frontend Issues

**API calls fail:**
- Verify NEXT_PUBLIC_API_URL is correct
- Check CORS configuration on backend
- Verify backend is running

**Real-time updates not working:**
- Check polling interval
- Verify WebSocket connection (if implemented)
- Check browser console for errors

### WhatsApp Issues

**Webhook not receiving messages:**
- Verify webhook URL is correct
- Check verify token matches
- Verify Meta for Business API configuration

**Messages not processing:**
- Check webhook logs
- Verify signal creation logic
- Check database writes

## Cost Estimation

### Render (Free Tier)
- Backend: $0/month (free tier)
- PostgreSQL: $0/month (free tier)
- Storage: $0/month (free tier)

### Vercel (Free Tier)
- Frontend: $0/month (free tier)
- Bandwidth: $0/month (free tier)

### WhatsApp Business API
- Free tier: 1,000 conversations/month
- Paid tier: Based on usage

### Total Estimated Cost: $0/month (free tiers)

## Scaling

### When to Upgrade

**Backend (Render):**
- Upgrade when: >100 concurrent users or >10,000 requests/day
- Cost: ~$7/month for starter plan

**Database (PostgreSQL):**
- Upgrade when: >1GB storage or >100 concurrent connections
- Cost: ~$7/month for starter plan

**Frontend (Vercel):**
- Upgrade when: >100GB bandwidth/month
- Cost: ~$20/month for pro plan

## Maintenance

### Regular Tasks

- Monitor logs daily
- Check database storage weekly
- Review API usage monthly
- Update dependencies regularly
- Test backup restoration quarterly

### Backup Strategy

- Render automatically backs up PostgreSQL
- Export prospectus PDFs to cloud storage
- Keep local copy of critical data
- Document recovery procedures

## Support

For issues or questions:
- Check Render documentation: https://render.com/docs
- Check Vercel documentation: https://vercel.com/docs
- Check WhatsApp API documentation: https://developers.facebook.com/docs/whatsapp
