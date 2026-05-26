# KULIMA OS Frontend Implementation Guide

## Quick Start

### For Developers
```bash
# Navigate to frontend
cd frontend

# Install dependencies (if first time)
npm install

# Run dev server
npm run dev

# Visit http://localhost:3000
```

### For Designers
The entire UI is built with inline React styles. To modify:
1. Open `frontend/app/page.jsx`
2. Find the component section
3. Modify the `style={{...}}` objects
4. Colors: `#2d6a4f` (primary), `#f8faf8` (bg)

---

## Component Architecture

### Main Page: `frontend/app/page.jsx`

**State Management:**
```javascript
- zone: Selected zone (MZUZU, LILONGWE, etc.)
- inputValue: User's natural language input
- summary: Current zone summary from API
- activityFeed: Recent activities
- message: Status messages (success/error)
- loading: API loading state
- reportLoading: Report generation state
- reportData: Generated report details
- inputRef: Ref for focusing input box
```

**Key Functions:**
```javascript
parseActivityFromInput(text)      // NLP parsing
fetchSummary()                    // GET /summary/{zone}
handleSubmitActivity(e)           // POST /signal
handleGenerateReport()            // POST /generate-prospectus
handleDownloadSampleReport()      // Client-side download
```

### Component Breakdown

#### 1. Header (Sticky)
- Logo + branding
- Zone selector dropdown
- Demo mode indicator
- Height: 60px, fixed top

#### 2. Hero Section
- Value proposition
- Three CTAs
- Background: white with subtle green border-left

#### 3. Demo Banner
- Conditional render: `isDemoMode && <div>...`
- Explains system is demonstration
- Light yellow background

#### 4. Status Message
- Conditional render: `message && <div>...`
- Green for success, yellow for alerts
- Dismissable manually

#### 5. Two-Column Layout
- Grid: `gridTemplateColumns: '1fr 1fr'`
- Gap: 32px
- Responsive: stacks on mobile

**Left Column:**
- InputBox component
- ActivityFeed component

**Right Column:**
- Key insight highlight
- Quick stats grid
- Activity types list
- Demand patterns (if available)
- Infrastructure gaps (if available)

#### 6. Report Section
- Conditional render: `reportData && <section>...`
- Green border highlight
- Download button
- Contents preview

#### 7. Footer
- Dark green background (#2d6a4f)
- Three-column layout
- Mission statement

---

## Natural Language Parsing

### Activity Type Detection
```javascript
const activityMap = {
  'irrigat': 'irrigation',
  'mill': 'milling',
  'cold|storage': 'cold storage',
  'weld|metal': 'welding',
  'pump': 'irrigation',
  'grain': 'milling'
};
```

### Time Window Detection
```javascript
const timeMap = {
  'morning|early|[6-9]': 'morning',
  'afternoon|noon|[12-3]': 'afternoon',
  'evening|night|[5-8]': 'evening'
};
```

### Example Parsing
```
Input: "We are irrigating maize in the morning"
→ { activity_type: 'irrigation', time_window: 'morning' }

Input: "Milling crops"
→ { activity_type: 'milling', time_window: 'morning' } (default)

Input: "Cold room evening cycle"
→ { activity_type: 'cold storage', time_window: 'evening' }
```

---

## API Integration

### Endpoints Used
```javascript
BASE_URL = http://127.0.0.1:8000/api/v1

// 1. Get zone summary
GET /summary/{zone}
Response: { status, data: { signal_count, patterns, key_finding, ... } }

// 2. Submit activity signal
POST /signal
Body: { zone, activity_type, time_window, source: 'web', user_id }
Response: { status, signal_id, message }

// 3. Generate prospectus
POST /generate-prospectus
Body: { zone, user_id }
Response: { status, data: { prospectus_id, pdf_url, json_url, ... } }
```

### Error Handling
```javascript
// Graceful fallback to demo data
try {
  const response = await fetch(`${BASE_URL}/summary/${zone}`);
  const data = await response.json();
  if (data.status === 'success') {
    setSummary(data.data);
  } else {
    setSummary(SAMPLE_SUMMARY);  // Fallback
  }
} catch (error) {
  console.error('Error:', error);
  setSummary(SAMPLE_SUMMARY);    // Fallback
}
```

---

## Demo Mode Logic

### How It Works
```javascript
const isDemoMode = !summary || summary.signal_count < DEMO_SIGNAL_THRESHOLD;
// DEMO_SIGNAL_THRESHOLD = 5

// When in demo mode:
const displayedSummary = isDemoMode ? SAMPLE_SUMMARY : summary;
const displayedActivities = isDemoMode ? SAMPLE_ACTIVITY_FEED : activityFeed;
```

### Sample Data Structure
```javascript
const SAMPLE_SUMMARY = {
  zone: 'MZUZU',
  signal_count: 3,
  total_patterns: 2,
  high_confidence_patterns: 1,
  productive_activities_detected: ['irrigation', 'milling', 'cold storage'],
  key_finding: 'Activity in Mzuzu shows growing demand...',
  demand_patterns: [
    { activity: 'Irrigation', frequency: 'Daily', confidence: 'High' },
    // ...
  ],
  infrastructure_gaps: [
    'Three-phase power in Zone A',
    // ...
  ]
};
```

---

## Styling System

### Color Palette
```javascript
// Primary Colors
'#2d6a4f'    // Dark green (primary)
'#1f4d38'    // Darker green (hover)
'#e7f6f1'    // Light green (highlights)
'#ffffff'    // White (cards)

// Neutral Colors
'#f8faf8'    // Very light gray (backgrounds)
'#e0e8e4'    // Light gray (borders)
'#5a7a66'    // Medium gray (secondary text)
'#172d20'    // Very dark (primary text)

// Accent Colors
'#fef3e0'    // Light yellow (demo, alerts)
'#b8860b'    // Golden (warning text)
'#fff9e6'    // Pale yellow (warning bg)
```

### Common Style Patterns
```javascript
// Card styling
backgroundColor: '#ffffff'
borderRadius: 14
padding: 24
boxShadow: '0 2px 8px rgba(23, 45, 32, 0.04)'
border: '1px solid #e0e8e4'

// Text styles
fontSize: 13-14 (body), 18-28 (headings), 32+ (stats)
fontWeight: 400 (normal), 500 (medium), 600 (semi-bold), 700 (bold)
color: '#172d20' (primary), '#5a7a66' (secondary)

// Button styling
padding: '12px 24px'
borderRadius: 10
fontWeight: 600
cursor: pointer
transition: 'background 0.2s'
```

---

## Responsive Design

### Layout Breakpoints
```javascript
// Header: Always 1 row
// Hero: 1 column on mobile, auto on desktop
// Two-column section: Stacks on mobile
  Desktop: gridTemplateColumns: '1fr 1fr'
  Mobile: gridTemplateColumns: '1fr' (stack)

// Max widths
maxWidth: 1400   // Main container
maxWidth: 800    // Hero text
maxWidth: 720    // Paragraphs
```

### Mobile Optimization
- Padding reduces from 48px to 24px
- Font sizes scale down ~12.5%
- Gaps reduce from 32px to 24px
- Cards stack vertically
- Header wraps buttons if needed

---

## Extending the System

### Adding New Activity Types
1. Edit `parseActivityFromInput()` in `page.jsx`
2. Add new pattern to activity detection
3. Test with example input

```javascript
// Add welding detection
else if (text_lower.includes('weld')) activity_type = 'welding';
```

### Adding New Insight Cards
1. Check if data exists: `displayedSummary?.new_field`
2. Add conditional render in right panel
3. Style consistently with existing cards

```javascript
{displayedSummary?.new_field && (
  <div style={{...cardStyles}}>
    <div style={{fontSize: 13, fontWeight: 600, color: '#2d6a4f'}}>
      NEW SECTION TITLE
    </div>
    {/* Content here */}
  </div>
)}
```

### Customizing Colors
1. Search-replace color codes globally
2. Update all hex values at once
3. Maintain contrast ratios (WCAG AA minimum)

```bash
# Find all colors
grep -r '#2d6a4f' frontend/

# Update to new color
sed -i 's/#2d6a4f/#YOUR-COLOR/g' frontend/app/page.jsx
```

---

## Troubleshooting

### Issue: Natural language parsing not working
**Solution:** Update regex patterns in `parseActivityFromInput()` to match your activity names

### Issue: API errors silently fail
**Solution:** Check console logs, verify BASE_URL environment variable
```javascript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
// Set in .env.local: NEXT_PUBLIC_API_URL=your-url
```

### Issue: Demo mode not showing
**Solution:** Verify signal_count < DEMO_SIGNAL_THRESHOLD (5)
```javascript
// Force demo mode for testing
const isDemoMode = true;  // Temporary override
```

### Issue: Reports not downloading
**Solution:** Verify pdf_url path construction
```javascript
const prospectusUrl = reportData?.pdf_url 
  ? `${BACKEND_BASE}${reportData.pdf_url}` 
  : null;
```

---

## Performance Tips

1. **Memoize expensive renders:**
   ```javascript
   const displayedSummary = useMemo(() => 
     isDemoMode ? SAMPLE_SUMMARY : summary,
     [isDemoMode, summary]
   );
   ```

2. **Lazy load images:**
   ```javascript
   <img loading="lazy" src="..." />
   ```

3. **Debounce zone changes:**
   ```javascript
   useEffect(() => {
     const timer = setTimeout(() => fetchSummary(), 300);
     return () => clearTimeout(timer);
   }, [zone]);
   ```

---

## Security Checklist

- ✓ No PII in input validation
- ✓ All user input sanitized
- ✓ API calls over HTTPS (in production)
- ✓ No hardcoded credentials
- ✓ CORS properly configured
- ✓ Error messages don't leak system details

---

## Deployment Checklist

- [ ] Environment variables set (.env.local)
- [ ] API endpoints verified
- [ ] Sample PDF asset in place
- [ ] Mobile responsive tested
- [ ] Browser compatibility checked (Chrome, Firefox, Safari)
- [ ] Accessibility audit passed
- [ ] Performance metrics good (Core Web Vitals)
- [ ] Error handling tested
- [ ] Demo mode works offline
- [ ] Sample report downloads

---

## Support & Questions

For issues or questions:
1. Check the AGENTS.md file for system principles
2. Review API_DOCUMENTATION.md for backend specs
3. Check ARCHITECTURE.md for system design
4. Consult FRONTEND_TRANSFORMATION_SUMMARY.md for overview

**Remember:** The frontend is designed to preserve all backend invariants. Modifications should only enhance UX, never alter core logic.
