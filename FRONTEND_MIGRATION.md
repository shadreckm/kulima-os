# Frontend Migration Guide

## Overview
This guide explains how to migrate from the current Streamlit-based UI to a React/Next.js frontend that consumes the Kulima OS API.

## Current State
- Streamlit monolithic application
- Direct engine calls
- No API layer
- UI logic mixed with backend logic

## Target State
- React/Next.js frontend
- API-first architecture
- Separated concerns
- Real-time updates

## Prerequisites

### Backend API
Ensure the backend API is running and accessible:
```bash
cd backend
pip install -r requirements.txt
python -m backend.main
```

API will be available at `http://localhost:8000`

### Frontend Setup
```bash
npx create-next-app@latest frontend
cd frontend
npm install axios
```

## API Client

### Create API Client
Create `frontend/src/services/api.js`:

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Signal endpoints
export const createSignal = async (signalData) => {
  const response = await api.post('/signal', signalData);
  return response.data;
};

export const getSignals = async (zone, limit = 100) => {
  const response = await api.get(`/signals/${zone}?limit=${limit}`);
  return response.data;
};

// Summary endpoints
export const getSummary = async (zone) => {
  const response = await api.get(`/summary/${zone}`);
  return response.data;
};

export const getZones = async () => {
  const response = await api.get('/zones');
  return response.data;
};

// Prospectus endpoints
export const generateProspectus = async (zone, userId) => {
  const response = await api.post('/generate-prospectus', { zone, user_id: userId });
  return response.data;
};

export const getProspectus = async (prospectusId) => {
  const response = await api.get(`/prospectus/${prospectusId}`);
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
```

## Component Migration

### Dashboard Component
Create `frontend/src/components/Dashboard.js`:

```javascript
import { useState, useEffect } from 'react';
import { getSummary, getZones } from '../services/api';

export default function Dashboard() {
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState('');
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadZones();
  }, []);

  useEffect(() => {
    if (selectedZone) {
      loadSummary(selectedZone);
    }
  }, [selectedZone]);

  const loadZones = async () => {
    try {
      const data = await getZones();
      setZones(data.zones);
      if (data.zones.length > 0) {
        setSelectedZone(data.zones[0]);
      }
    } catch (error) {
      console.error('Failed to load zones:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async (zone) => {
    try {
      const data = await getSummary(zone);
      setSummary(data);
    } catch (error) {
      console.error('Failed to load summary:', error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <h1>Kulima OS Dashboard</h1>
      
      <div className="zone-selector">
        <label>Select Zone:</label>
        <select 
          value={selectedZone} 
          onChange={(e) => setSelectedZone(e.target.value)}
        >
          {zones.map(zone => (
            <option key={zone} value={zone}>{zone}</option>
          ))}
        </select>
      </div>

      {summary && (
        <div className="summary">
          <h2>Coordination Summary: {summary.zone}</h2>
          <div className="metrics">
            <div className="metric">
              <h3>Total Patterns</h3>
              <p>{summary.total_patterns}</p>
            </div>
            <div className="metric">
              <h3>High Confidence</h3>
              <p>{summary.high_confidence_patterns}</p>
            </div>
            <div className="metric">
              <h3>Moderate Confidence</h3>
              <p>{summary.moderate_confidence_patterns}</p>
            </div>
          </div>
          <div className="activities">
            <h3>Productive Activities:</h3>
            <ul>
              {summary.productive_activities_detected.map(activity => (
                <li key={activity}>{activity}</li>
              ))}
            </ul>
          </div>
          <div className="finding">
            <h3>Key Finding:</h3>
            <p>{summary.key_finding}</p>
          </div>
        </div>
      )}
    </div>
  );
}
```

### Signal Input Component
Create `frontend/src/components/SignalInput.js`:

```javascript
import { useState } from 'react';
import { createSignal } from '../services/api';

export default function SignalInput() {
  const [formData, setFormData] = useState({
    zone: 'MZUZU',
    activity_type: '',
    time_window: '',
    source: 'manual',
    user_id: 'user_123',
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const result = await createSignal({
        ...formData,
        timestamp: new Date().toISOString(),
      });
      setMessage(`Signal created: ${result.signal_id}`);
      setFormData({
        ...formData,
        activity_type: '',
        time_window: '',
      });
    } catch (error) {
      setMessage('Failed to create signal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signal-input">
      <h2>Submit Activity Signal</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Zone:</label>
          <select
            value={formData.zone}
            onChange={(e) => setFormData({...formData, zone: e.target.value})}
          >
            <option value="MZUZU">MZUZU</option>
            <option value="LILONGWE">LILONGWE</option>
            <option value="BLANTYRE">BLANTYRE</option>
            <option value="ZOMBA">ZOMBA</option>
          </select>
        </div>
        <div className="form-group">
          <label>Activity Type:</label>
          <select
            value={formData.activity_type}
            onChange={(e) => setFormData({...formData, activity_type: e.target.value})}
            required
          >
            <option value="">Select activity...</option>
            <option value="irrigation">Irrigation</option>
            <option value="milling">Milling</option>
            <option value="cold_storage">Cold Storage</option>
            <option value="welding">Welding</option>
          </select>
        </div>
        <div className="form-group">
          <label>Time Window:</label>
          <select
            value={formData.time_window}
            onChange={(e) => setFormData({...formData, time_window: e.target.value})}
            required
          >
            <option value="">Select time window...</option>
            <option value="morning">Morning</option>
            <option value="afternoon">Afternoon</option>
            <option value="evening">Evening</option>
          </select>
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Signal'}
        </button>
      </form>
      {message && <div className="message">{message}</div>}
    </div>
  );
}
```

### Prospectus Generator Component
Create `frontend/src/components/ProspectusGenerator.js`:

```javascript
import { useState } from 'react';
import { generateProspectus } from '../services/api';

export default function ProspectusGenerator() {
  const [formData, setFormData] = useState({
    zone: 'MZUZU',
    user_id: 'user_123',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    setResult(null);

    try {
      const data = await generateProspectus(formData.zone, formData.user_id);
      setResult(data);
    } catch (error) {
      console.error('Failed to generate prospectus:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="prospectus-generator">
      <h2>Generate Prospectus</h2>
      <div className="form-group">
        <label>Zone:</label>
        <select
          value={formData.zone}
          onChange={(e) => setFormData({...formData, zone: e.target.value})}
        >
          <option value="MZUZU">MZUZU</option>
          <option value="LILONGWE">LILONGWE</option>
          <option value="BLANTYRE">BLANTYRE</option>
          <option value="ZOMBA">ZOMBA</option>
        </select>
      </div>
      <button onClick={handleGenerate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Prospectus'}
      </button>

      {result && (
        <div className="result">
          <h3>Prospectus Generated</h3>
          <p>ID: {result.prospectus_id}</p>
          <a href={result.pdf_url} target="_blank">Download PDF</a>
          <a href={result.json_url} target="_blank">Download JSON</a>
        </div>
      )}
    </div>
  );
}
```

## Real-Time Updates

### Polling Implementation
For real-time updates, implement polling in your components:

```javascript
import { useState, useEffect } from 'react';
import { getSummary } from '../services/api';

export default function RealTimeDashboard({ zone }) {
  const [summary, setSummary] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(Date.now());

  useEffect(() => {
    const loadSummary = async () => {
      try {
        const data = await getSummary(zone);
        setSummary(data);
        setLastUpdate(Date.now());
      } catch (error) {
        console.error('Failed to load summary:', error);
      }
    };

    // Initial load
    loadSummary();

    // Poll every 30 seconds
    const interval = setInterval(loadSummary, 30000);

    return () => clearInterval(interval);
  }, [zone]);

  return (
    <div>
      <p>Last updated: {new Date(lastUpdate).toLocaleTimeString()}</p>
      {/* Render summary */}
    </div>
  );
}
```

### WebSocket Implementation (Future)
When WebSocket support is added:

```javascript
import { useState, useEffect } from 'react';

export default function WebSocketDashboard({ zone }) {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/summary/${zone}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSummary(data);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return () => ws.close();
  }, [zone]);

  return (
    <div>
      {/* Render summary */}
    </div>
  );
}
```

## Environment Variables

Create `.env.local` in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

For production:

```env
NEXT_PUBLIC_API_URL=https://api.kulimaos.com/api/v1
```

## Styling

Install Tailwind CSS for styling:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Configure `tailwind.config.js`:

```javascript
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

## Deployment

### Vercel Deployment
1. Push frontend code to GitHub
2. Connect repository to Vercel
3. Configure environment variables
4. Deploy

### CORS Configuration
Ensure the backend CORS configuration includes your frontend domain:

```python
# backend/config.py
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend-domain.vercel.app"
]
```

## Migration Checklist

- [ ] Set up Next.js project
- [ ] Install dependencies (axios, tailwindcss)
- [ ] Create API client
- [ ] Migrate Dashboard component
- [ ] Migrate Signal Input component
- [ ] Migrate Prospectus Generator component
- [ ] Implement real-time updates (polling)
- [ ] Configure environment variables
- [ ] Test all components
- [ ] Deploy to Vercel
- [ ] Configure CORS on backend
- [ ] Test end-to-end

## Notes

- Streamlit will remain as a temporary admin dashboard
- All new features should be built in React/Next.js
- API-first architecture ensures frontend independence
- Real-time updates will be enhanced with WebSocket in future
