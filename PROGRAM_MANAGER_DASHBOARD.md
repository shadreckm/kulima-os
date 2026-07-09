# KULIMA OS - PROGRAM MANAGER DASHBOARD

## Overview

The Program Manager Dashboard is designed specifically for **Grace Banda** and other NGO decision-makers who need to make infrastructure investment decisions based on coordination intelligence.

**Design Philosophy**: Africa CDC Dashboard + UNDP Monitoring Dashboard + Crisis Early Warning System

**Access**: https://kulima-os.vercel.app/dashboard

## Purpose

The dashboard answers 4 critical questions within 30 seconds:

1. **What is happening?** → National Summary Cards
2. **Where is it happening?** → Priority Zone Rankings
3. **How confident are we?** → Coordination Confidence Scores
4. **What should we do next?** → Recommendation Panel

## Dashboard Components

### 1. National Overview Cards

Four key metrics displayed prominently at the top:

**Total Signals**
- Count of all coordination signals received
- Indicates overall system activity
- Blue indicator (information)

**Active Zones**
- Number of zones with coordination activity
- Shows geographic spread of demand
- Green indicator (positive)

**Average Confidence**
- Mean coordination confidence across priority zones
- Ranges from 0-100%
- Yellow indicator (caution)

**Priority Zones**
- Number of zones requiring immediate attention
- Based on signal volume and confidence
- Red indicator (urgent)

### 2. Priority Zone Rankings Table

Ranked list of zones by coordination signal volume:

**Columns**:
- **Rank**: Visual ranking (1-5) with color coding
  - Rank 1: Red (URGENT)
  - Rank 2-3: Orange/Yellow (HIGH)
  - Rank 4-5: Gray (MONITOR)
- **Zone**: Zone name (e.g., EKWENDENI, MHUJU)
- **Signals**: Total coordination signals received
- **Activities**: Number of distinct activity types
- **Confidence**: Visual progress bar + percentage (0-100%)
- **Last Signal**: Date of most recent signal
- **Status**: URGENT / HIGH / MONITOR

**Confidence Scoring Logic**:
- Base: 40%
- +10% per signal (capped at 95%)
- Color coding:
  - Green: ≥80% (high confidence)
  - Yellow: 60-79% (moderate confidence)
  - Red: <60% (low confidence)

### 3. Recent Coordination Signals Table

Real-time feed of the last 10 signals:

**Columns**:
- **Zone**: Where the signal originated
- **Activity**: Type of productive activity (irrigation, milling, etc.)
- **Time**: Timestamp of signal receipt

**Purpose**: Shows live system activity and validates that coordination signals are being received.

### 4. Recommendation Panel

Actionable recommendations for top 3 priority zones:

**Each Recommendation Card Contains**:
- Zone name and priority ranking
- Signal count
- Coordination confidence score with visual progress bar
- Recommended action (context-specific)
- Last signal timestamp

**Recommendation Logic**:
- **Priority 1 (Highest signals)**: "Prioritize infrastructure assessment. Strong coordination signals indicate high demand."
- **Priority 2-3**: "Monitor for infrastructure planning. Coordination patterns emerging."

**Purpose**: Translates data into actionable decisions for program managers.

### 5. Evidence & Trust Section

Summary of evidence layer status:

**Metrics**:
- **Verified Signals**: Total coordination signals with trust validation
- **Trust Score**: Average coordination confidence across all zones
- **Evidence Items**: Count of uploaded photos/documents (currently 0 in pilot)

**Purpose**: Shows system integrity and readiness for institutional decision-making.

## Data Flow

### Backend APIs Used

1. **GET /api/v1/signals/recent**
   - Fetches recent coordination signals
   - Returns: `[{id, zone, activity_type, sector, time_window, created_at, source}]`

2. **GET /api/v1/summaries/{zone}** (future)
   - Fetches zone-specific summaries
   - Returns: `{zone, signal_count, confidence_score, patterns}`

### Data Processing

**Zone Statistics Calculation**:
```javascript
// For each signal, aggregate by zone
stats[zone] = {
  count: number of signals,
  activities: Set of unique activity types,
  lastSignal: most recent timestamp,
  confidence: calculated score (40 + count * 10, max 95)
}
```

**Priority Ranking**:
```javascript
// Sort zones by signal count (descending)
priorityZones = Object.entries(zoneStats)
  .sort(([, a], [, b]) => b.count - a.count)
  .slice(0, 5)
```

**National Metrics**:
```javascript
totalSignals = signals.length
activeZones = Object.keys(zoneStats).length
avgConfidence = mean(priorityZones.map(z => z.confidence))
```

## User Experience Design

### Visual Hierarchy

1. **National Overview** (top) → Big picture
2. **Priority Rankings** (middle) → Where to focus
3. **Recent Activity + Recommendations** (bottom) → What's happening + What to do

### Color Coding

- **Blue**: Information, system status
- **Green**: Positive, operational
- **Yellow**: Caution, moderate priority
- **Red**: Urgent, high priority
- **Gray**: Neutral, monitoring

### Refresh Strategy

- **Auto-refresh**: Every 30 seconds
- **Manual refresh**: Reload page
- **Last update timestamp**: Displayed in header

### Loading States

- **Initial load**: Full-screen spinner with "Loading dashboard data..."
- **Refresh**: Existing data remains visible during background refresh
- **Error state**: Red banner with error message, existing data preserved

## Decision-Making Workflow

### For Grace Banda (Program Manager)

**Step 1: Check National Overview (5 seconds)**
- How many signals? → System activity level
- How many zones? → Geographic spread
- What's the confidence? → Data reliability

**Step 2: Review Priority Rankings (10 seconds)**
- Which zone is #1? → Immediate focus
- What's the confidence? → Investment readiness
- When was last signal? → Pattern recency

**Step 3: Read Recommendations (10 seconds)**
- What action for top zone? → Next step
- What's the justification? → Decision rationale
- What's the timeline? → Urgency level

**Step 4: Validate with Recent Signals (5 seconds)**
- Are signals coming in? → System operational
- What activities? → Demand type validation
- Which zones? → Cross-check with rankings

**Total Time: 30 seconds to decision-ready state**

## Technical Implementation

### Frontend Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: JavaScript (React)
- **Styling**: Tailwind CSS (utility-first)
- **State Management**: React hooks (useState, useEffect)
- **API Client**: Custom fetch wrapper (lib/api.js)

### Key Files

- `frontend/app/dashboard/page.jsx` (485 lines) - Main dashboard component
- `frontend/lib/api.js` - API client functions
- `frontend/app/page.jsx` (27 lines) - Landing page with redirect

### Performance Optimizations

- **Client-side rendering**: Fast initial load
- **Incremental updates**: Only changed data re-renders
- **Efficient sorting**: O(n log n) for priority rankings
- **Minimal API calls**: Single endpoint for all signals

### Error Handling

- **Network errors**: Displayed in red banner, existing data preserved
- **Empty states**: Friendly messages ("No signals received yet")
- **Malformed data**: Defensive checks with fallbacks (e.g., `signal.zone || 'UNKNOWN'`)

## Deployment

### Production URLs

- **Frontend**: https://kulima-os.vercel.app/dashboard
- **Backend**: https://kulima-os-backend.onrender.com
- **Database**: Supabase PostgreSQL

### Environment Variables

```bash
NEXT_PUBLIC_API_URL=https://kulima-os-backend.onrender.com
```

### Build Command

```bash
cd frontend
npm install
npm run build
```

### Deployment Platform

- **Vercel** (frontend)
- **Render** (backend)
- **Supabase** (database)

## Zero-PII Compliance

The dashboard maintains KULIMA OS's Zero-PII invariant:

✅ **No Personal Identifiers**: Only zone names, activity types, timestamps
✅ **Aggregated Data**: All metrics are collective, not individual
✅ **Coordination Focus**: Displays patterns, not people
✅ **Temporal Moat**: Signals are batched, not real-time tracked

**Audit Trail**: All data displayed comes from aggregated coordination signals, never raw individual data.

## Future Enhancements

### Phase 2 (Post-Pilot)

1. **Zone Detail View**: Click zone to see detailed coordination patterns
2. **Activity Breakdown Charts**: Visual distribution of activity types
3. **Demand Rhythm Heatmap**: Temporal patterns visualization
4. **Export Functionality**: Download reports as PDF/CSV
5. **Evidence Gallery**: Display uploaded photos/documents with trust scores

### Phase 3 (Scale)

1. **Multi-Country Support**: Country selector in header
2. **Comparative Analytics**: Zone-to-zone comparisons
3. **Predictive Insights**: ML-based demand forecasting
4. **Mobile Optimization**: Responsive design for field use

## Success Metrics

### User Experience

- **Time to Decision**: <30 seconds from page load to actionable insight
- **Comprehension Rate**: 100% of users understand dashboard within 60 seconds
- **Decision Confidence**: Users feel confident making infrastructure decisions

### System Performance

- **Page Load Time**: <2 seconds (first contentful paint)
- **API Response Time**: <500ms (backend)
- **Refresh Rate**: 30 seconds (auto-refresh)
- **Uptime**: 99.9% (production SLA)

### Data Quality

- **Signal Accuracy**: 95%+ coordination signals are valid
- **Confidence Calibration**: Confidence scores correlate with actual demand
- **Zero False Positives**: No infrastructure recommendations without genuine coordination

## Support & Maintenance

### Monitoring

- **Frontend**: Vercel Analytics
- **Backend**: Render Metrics
- **Database**: Supabase Dashboard

### Troubleshooting

**Dashboard not loading?**
1. Check backend health: https://kulima-os-backend.onrender.com/health
2. Check browser console for errors
3. Verify API_URL environment variable

**No signals showing?**
1. Verify database has signals: Check Supabase dashboard
2. Check API endpoint: GET /api/v1/signals/recent
3. Review backend logs on Render

**Confidence scores seem wrong?**
1. Review calculation logic in dashboard code
2. Verify signal counts in database
3. Check for data quality issues

### Contact

- **Technical Issues**: Check GitHub repository
- **Product Questions**: Contact KULIMA OS team
- **Infrastructure Support**: Refer to DEPLOYMENT.md

---

**Document Version**: 1.0  
**Last Updated**: 2026-07-09  
**Author**: KULIMA OS Development Team  
**Status**: Production Ready