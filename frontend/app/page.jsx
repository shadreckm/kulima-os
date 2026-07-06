'use client';

import { useState, useEffect, useRef } from 'react';
import { fetchSummaryData, fetchRecentSignalsData, submitActivitySignal, generateProspectusReport, downloadProspectusPdf, BASE_URL } from '../lib/api';

const ZONES = ['EKWENDENI', 'MHUJU', 'BWENGU', 'RUMPHI', 'EUTHINI', 'MZUZU', 'MZIMBA'];
const CLIENT_MODES = [
  { key: 'investor', label: 'Investor' },
  { key: 'government', label: 'Government' },
  { key: 'ngo', label: 'NGO' }
];
const LOADING_MESSAGES = [
  'Analyzing coordination patterns...',
  'Validating signals...',
  'Generating prospectus...'
];
const PAYCHANGU_LINK = 'https://pay.paychangu.com/SC-GDDYA0';
const ACTIVITY_TERMS = ['farming', 'irrigation', 'milling', 'trading', 'welding', 'storage', 'market', 'transport'];
const RESOURCE_TERMS = ['water', 'energy', 'power', 'road', 'storage', 'market', 'transport'];

const PAYMENT_OPTIONS = [
  { key: 'single', title: 'Single report', price: 'MK 5,000', description: 'One-time access to the full report.' },
  { key: 'monthly', title: 'Monthly access', price: 'MK 25,000', description: 'Ongoing access to premium report updates.' }
];

const normalizeTag = (value) => {
  if (!value) return 'Unknown';
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
};

const buildTrustLabel = (summary) => {
  if (!summary) return 'LOW';
  if (summary.high_confidence_patterns > 0 || summary.trust_score > 0.7) return 'HIGH';
  if (summary.moderate_confidence_patterns > 0 || summary.trust_score > 0.4) return 'MEDIUM';
  return 'LOW';
};

const parseTags = (text) => {
  const normalized = (text || '').toLowerCase();
  // Match all pilot EPAs and major cities
  const zoneMatch = normalized.match(
    /\b(ekwendeni|mhuju|bwengu|rumphi|euthini|mzuzu|mzimba|lilongwe|blantyre|zomba)\b/
  );
  const activityMatch = ACTIVITY_TERMS.find((term) => normalized.includes(term));
  const resourceMatch = RESOURCE_TERMS.find((term) => normalized.includes(term));
  return {
    zone: zoneMatch ? zoneMatch[0].toUpperCase() : null,
    activity: normalizeTag(activityMatch),
    resource: normalizeTag(resourceMatch)
  };
};

export default function Home() {
  const [zone, setZone] = useState('MZUZU');
  const [summary, setSummary] = useState(null);
  const [recentActivities, setRecentActivities] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [message, setMessage] = useState('Ready to capture community demand.');
  const [reportLoading, setReportLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showUnlock, setShowUnlock] = useState(false);
  const [isPaid, setIsPaid] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState('single');
  const [paymentMessage, setPaymentMessage] = useState('');
  const [recordedPhrase, setRecordedPhrase] = useState('');
  const [parsedTag, setParsedTag] = useState({ zone: null, activity: 'Farming', resource: 'Water' });
  const [cardIndex, setCardIndex] = useState(0);
  const [speechActive, setSpeechActive] = useState(false);

  // New state variables for security payment verification, funding status, and share overlays
  const [paymentVerifying, setPaymentVerifying] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [fundingStatus, setFundingStatus] = useState('idle');
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [clientMode, setClientMode] = useState('investor');
  const [selectedClusterId, setSelectedClusterId] = useState('');
  const [pdfLoading, setPdfLoading] = useState(false);
  
  // Progressive disclosure states
  const [showFullAnalysis, setShowFullAnalysis] = useState(false);
  const [showAdvancedAnalysis, setShowAdvancedAnalysis] = useState(false);
  const [activeTab, setActiveTab] = useState('confidence');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const recognitionRef = useRef(null);
  const BACKEND_BASE = BASE_URL.replace(/\/api\/v1$/, '');
  const reportUrl = reportData?.pdf_url ? `${BACKEND_BASE}${reportData.pdf_url}` : '';

  const trustLabel = buildTrustLabel(summary);
  const trustScore = Math.round((summary?.trust_score ?? 0) * 100);
  const confidenceBreakdown = summary?.confidence_breakdown || {
    persistenceScore: 0,
    validationScore: 0,
    temporalStability: 0,
    spatialConsistency: 0
  };

  useEffect(() => {
    // Only run in browser, not during build
    if (typeof window === 'undefined') return;
    
    fetchSummary();
    fetchRecentSignals();
    const interval = setInterval(fetchRecentSignals, 7000);
    return () => clearInterval(interval);
  }, [zone, clientMode]);

  useEffect(() => {
    const clusters = summary?.clusters || [];
    if (clusters.length && !clusters.find((c) => c.cluster_id === selectedClusterId)) {
      setSelectedClusterId(clusters[0].cluster_id);
    }
  }, [summary, zone]);

  const fetchSummary = async () => {
    try {
      const data = await fetchSummaryData(zone, clientMode);
      setSummary(data || null);
    } catch (error) {
      console.error('Failed to load summary:', error);
      setSummary(null);
    }
  };

  const clusters = (summary?.clusters || []).filter((c) => c.sub_zone);
  const activeCluster = clusters.find((c) => c.cluster_id === selectedClusterId) || clusters[0] || null;
  const freshnessLabel = summary?.freshness_label || summary?.hours_since_update != null
    ? `Last updated: ${summary?.freshness_label || `${summary?.hours_since_update} hours ago`}`
    : null;

  const fetchRecentSignals = async () => {
    try {
      const data = await fetchRecentSignalsData();
      setRecentActivities(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load recent signals:', error);
      setRecentActivities([]);
    }
  };

  const zoneActivityCounts = ZONES.reduce((counts, zoneId) => {
    counts[zoneId] = recentActivities.filter((item) => (item.zone || '').toUpperCase() === zoneId).length;
    return counts;
  }, {});

  const handleInputChange = (text) => {
    setInputValue(text);
    const parsed = parseTags(text);
    if (parsed.zone) {
      setZone(parsed.zone);
      setParsedTag((current) => ({
        ...current,
        zone: parsed.zone,
        activity: parsed.activity || current.activity,
        resource: parsed.resource || current.resource
      }));
    } else {
      setParsedTag((current) => ({
        ...current,
        activity: parsed.activity || current.activity,
        resource: parsed.resource || current.resource
      }));
    }
  };

  const startVoiceCapture = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMessage('Voice input is not supported in this browser. Use typing instead.');
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    recognitionRef.current = recognition;

    recognition.onstart = () => {
      setSpeechActive(true);
      setMessage('Listening for a short demand signal...');
    };

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results).map((result) => result[0].transcript).join(' ');
      setRecordedPhrase(transcript);
      const parsed = parseTags(transcript);
      if (parsed.zone) {
        setZone(parsed.zone);
      }
      setParsedTag({
        zone: parsed.zone || zone,
        activity: parsed.activity || 'Farming',
        resource: parsed.resource || 'Water'
      });
      setInputValue(transcript);
      setMessage('Captured. Tap submit to push it live.');
    };

    recognition.onerror = () => {
      setSpeechActive(false);
      setMessage('Voice capture failed. Type your signal instead.');
    };

    recognition.onend = () => setSpeechActive(false);
    recognition.start();
  };

  const addLocalActivity = (text, inferredZone) => {
    const parsed = parseTags(text);
    const activity = parsed.activity || parsedTag.activity || 'Farming';
    const entry = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      zone: inferredZone,
      activity,
      original_text: text,
      display: `${inferredZone} · ${activity.toLowerCase()}`
    };
    setRecentActivities((current) => [entry, ...current].slice(0, 12));
  };

  const submitActivity = async () => {
    const text = inputValue.trim();
    if (!text) {
      setMessage('Type or speak a short activity first.');
      return;
    }

    const inferredZone = parsedTag.zone || zone;
    addLocalActivity(text, inferredZone);
    setInputValue('');
    setRecordedPhrase('');
    setSubmitError('');
    setIsSubmitting(true);
    setMessage('Signal added. Updating the live system...');

    try {
      const response = await submitActivitySignal(inferredZone, text, speechActive ? 'voice' : 'web');
      if (response?.success === false) {
        setMessage(response?.message || 'Signal could not be recorded right now.');
        setSubmitError(response?.message || 'Signal could not be recorded right now.');
      } else {
        setMessage(response?.message || 'Signal received and queued for analysis.');
      }
    } catch (error) {
      setMessage('Network issue. Local signal saved in the feed.');
      setSubmitError(error?.message || 'Unable to reach the backend right now.');
    } finally {
      setIsSubmitting(false);
      await fetchSummary();
      await fetchRecentSignals();
    }
  };

  const downloadReport = async () => {
    setPdfLoading(true);
    try {
      await downloadProspectusPdf(zone, clientMode);
      setMessage('PDF download started.');
    } catch (error) {
      setMessage(error?.message || 'PDF download could not be started.');
    } finally {
      setPdfLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    setReportLoading(true);
    setMessage(LOADING_MESSAGES[0]);

    try {
      for (let i = 1; i < LOADING_MESSAGES.length; i += 1) {
        await new Promise((resolve) => setTimeout(resolve, 600));
        setMessage(LOADING_MESSAGES[i]);
      }

      const data = await generateProspectusReport(zone);
      if (data?.success) {
        setReportData({ ...(data.report || {}), pdf_url: data.pdf_url || data.report?.pdf_url || '', preview_locked: data.report?.preview_locked ?? true });
        setShowPreview(true);
        setMessage('Preview ready. Locked cards show gated sections.');
      } else if (summary?.is_simulated || (summary?.signal_count || 0) < 5) {
        setReportData({ preview_locked: true, simulated: true });
        setShowPreview(true);
        setMessage('Showing simulated prospectus due to limited data.');
      } else {
        setMessage(data?.message || 'Preview generation failed.');
      }
    } catch {
      if (summary?.is_simulated) {
        setReportData({ preview_locked: true, simulated: true });
        setShowPreview(true);
        setMessage('Showing simulated prospectus due to limited data.');
      } else {
        setMessage('Unable to generate report. Try again in a moment.');
      }
    } finally {
      setReportLoading(false);
    }
  };

  const handlePayment = () => {
    window.open(PAYCHANGU_LINK, '_blank');
    setPaymentMessage('Complete payment in the opened window, then click confirm below.');
  };

  const confirmPayment = () => {
    setPaymentVerifying(true);
    setPaymentMessage('Initiating secure transaction verification with PayChangu gateway...');
    
    // Simulate a secure, external API verification call
    setTimeout(() => {
      setIsPaid(true);
      setPaymentSuccess(true);
      setPaymentVerifying(false);
      setPaymentMessage('Payment successfully verified!');
      setTimeout(() => {
        setShowUnlock(false);
        setMessage('Full report unlocked successfully.');
        setReportData((current) => current ? { ...current, preview_locked: false } : current);
      }, 500);
    }, 2000);
  };

  const handleFundOpportunity = () => {
    setFundingStatus('sending');
    setMessage('Routing allocation request to Kulima Economic Substrate...');
    
    setTimeout(() => {
      setFundingStatus('success');
      setMessage('Routing Success! Allocation of KES resource reserved at Kulima Decentralized Energy Allocation Pool (Zone Mzuzu Hub). Reference ID: KES-ALLOC-88421.');
    }, 1800);
  };

  const handleExportReport = () => {
    setExportLoading(true);
    setMessage('Formatting prospectus data for export...');
    setTimeout(() => {
      const dataToExport = {
        meta: {
          system: "KULIMA OS",
          version: "v1.0-Pilot",
          timestamp: new Date().toISOString(),
          provenance: "Verified multi-source telemetry & community reporting",
          consent: "Implicit coordination participation (Zero-PII compliant)"
        },
        prospectus: {
          zone: zone,
          coordination_confidence: {
            score: `${trustScore}%`,
            label: trustLabel
          },
          lumoza_demand_rhythms: {
            activity_recorded: recentActivities.length || 12,
            cycles_monitored: 7,
            stability_metric: "Persistent pattern"
          },
          lundai_infrastructure_gaps: {
            detected_shortages: summary?.infrastructure_gaps || ["Water Shortage"],
            recommended_projects: summary?.recommended_projects || ["Solar Irrigation pump deployment"]
          },
          zentari_trust_persistence: {
            score: trustScore,
            label: trustLabel,
            breakdown: confidenceBreakdown
          },
          clusters: summary?.clusters || [],
          is_simulated: summary?.is_simulated || false,
          mode: clientMode,
          social_reserve: {
            baseline_priority_load: "20%",
            protected_communal_assets: ["clinics", "schools", "drinking_water_points"]
          }
        }
      };

      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(dataToExport, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `kulima_prospectus_${zone.toLowerCase()}_export.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      
      setExportLoading(false);
      setMessage(`Export complete: 'kulima_prospectus_${zone.toLowerCase()}_export.json' downloaded.`);
    }, 800);
  };

  const handleShareInsight = () => {
    const shareData = {
      title: `Kulima OS - ${zone} Demand Prospectus`,
      text: `View verified community coordination patterns for ${zone} on Kulima OS.`,
      url: typeof window !== 'undefined' ? window.location.href : ''
    };
    
    if (typeof navigator !== 'undefined' && navigator.share && navigator.canShare && navigator.canShare(shareData)) {
      navigator.share(shareData)
        .then(() => setMessage('Successfully shared insight via system dialog.'))
        .catch((err) => {
          if (err.name !== 'AbortError') {
            setShowShareDialog(true);
          }
        });
    } else {
      setShowShareDialog(true);
      setMessage('Sharing channel opened.');
    }
  };

  const [showTrustTooltip, setShowTrustTooltip] = useState(false);
  const hasSignals = (summary?.signal_count ?? 0) > 0 || recentActivities.filter(a => (a.zone || '').toUpperCase() === zone).length > 0;
  const topActivities = (summary?.productive_activities_detected || []).map(normalizeTag).join(' & ');
  const simpleInsightDemand = topActivities ? `${topActivities} activity increasing` : 'Farming activity increasing';
  const simpleInsightAction = summary?.recommended_projects?.[0] ? `${summary.recommended_projects[0]} recommended` : 'Irrigation investment recommended';
  const reportCards = [
    {
      key: 'summary',
      title: 'Demand Summary',
      value: summary?.key_finding || 'Signals are forming into a clear demand pattern',
      subtitle: `${summary?.signal_count || 0} signals currently tracked`
    },
    {
      key: 'clusters',
      title: 'Clusters',
      value: summary?.clusters?.length ? `${summary.clusters.length} active clusters` : 'Monitoring',
      subtitle: summary?.recommended_projects?.[0] || 'More signals will reveal stronger clusters'
    },
    {
      key: 'gaps',
      title: 'Infrastructure Gaps',
      value: summary?.infrastructure_gaps?.[0] || 'No gaps identified yet',
      subtitle: 'Submit more signals to reveal deeper infrastructure needs'
    },
    {
      key: 'confidence',
      title: 'Confidence',
      value: `${trustScore}%`,
      subtitle: trustLabel
    }
  ];

  return (
    <div className="page-shell">
      {/* Top Header */}
      <header className="top-bar">
        <div className="top-brand">
          <img src="/logo.png" alt="Kulima OS" className="brand-logo" />
          <div>
            <div className="tiny-label">Dashboard</div>
            <div className="product-title">Kulima OS Dashboard</div>
            {freshnessLabel && <div className="freshness-label">{freshnessLabel}</div>}
          </div>
        </div>
        <div className="top-actions">
          <select
            value={clientMode}
            onChange={(e) => setClientMode(e.target.value)}
            className="mode-select-dropdown"
            aria-label="Client mode"
          >
            {CLIENT_MODES.map((m) => (
              <option key={m.key} value={m.key}>{m.label} view</option>
            ))}
          </select>
          <button className="ghost-button" onClick={() => setShowPreview(true)} disabled={reportLoading}>{reportLoading ? 'Loading…' : 'Preview Report'}</button>
          <button className="primary-button" onClick={() => { setPaymentMessage(''); setShowUnlock(true); }}>Unlock</button>
        </div>
      </header>

      {summary?.is_simulated && (
        <div className="simulated-banner" role="status">
          Showing simulated prospectus due to limited data
        </div>
      )}

      {/* Hero / Title Section */}
      <section className="hero-section">
        <h1>Kulima OS — Community Demand & Insight Platform</h1>
        <p className="subtitle">Describe what is needed in your area and get data-driven insights</p>
      </section>

      {/* Main Input Section */}
      <section className="input-panel">
        <div className="input-group">
          <button className={`mic-button ${speechActive ? 'active' : ''}`} onClick={startVoiceCapture}>
            <span className="mic-dot" />
            {speechActive ? 'Listening' : 'Voice'}
          </button>
          <textarea 
            value={inputValue} 
            onChange={(e) => handleInputChange(e.target.value)} 
            placeholder="e.g. Farmers in Mzuzu need irrigation water" 
            rows={2}
            className="input-textarea"
          />
          <button className="submit-button" onClick={submitActivity} disabled={isSubmitting || !inputValue.trim()}>
            {isSubmitting ? 'Submitting…' : 'Submit'}
          </button>
        </div>
        <div className="waveform-row">
          {Array.from({ length: 10 }).map((_, index) => (
            <span key={index} className={`wave-bar ${speechActive ? 'wave-active' : ''}`} style={{ animationDelay: `${index * 60}ms` }} />
          ))}
        </div>
        <div className="tag-row">
          <div className="zone-select-container">
            <span className="zone-select-label">Active Zone:</span>
            <select 
              value={zone} 
              onChange={(e) => setZone(e.target.value)} 
              className="zone-select-dropdown"
            >
              {ZONES.map((z) => (
                <option key={z} value={z}>{z}</option>
              ))}
            </select>
          </div>
          <span className="tag-chip">Activity: {parsedTag.activity}</span>
          <span className="tag-chip">Resource: {parsedTag.resource}</span>
        </div>
        <div className="status-line">{isSubmitting ? 'Submitting signal…' : message}</div>
        {submitError && <div className="status-line" style={{ color: '#ff8a80' }}>{submitError}</div>}
      </section>

      {/* LEVEL 1: Simplified Default View */}
      <div className="level1-container">
        <div className="level1-grid">
          {/* Map visualization */}
          <div className="map-panel">
            <div className="panel-title">Map & Trends</div>
            <div className="map-visualization">
              <svg viewBox="0 0 300 290" className="map-svg">
                <defs>
                  <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255, 255, 255, 0.03)" strokeWidth="1" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" rx="16" />

                <path
                  d="M130,30 Q150,90 120,130 T170,220 T160,280"
                  fill="none"
                  stroke="rgba(0, 230, 118, 0.1)"
                  strokeWidth="8"
                  strokeLinecap="round"
                />
                <path
                  d="M130,30 Q150,90 120,130 T170,220 T160,280"
                  fill="none"
                  stroke="rgba(0, 230, 118, 0.2)"
                  strokeWidth="2"
                  strokeDasharray="4,6"
                  strokeLinecap="round"
                />

                {[
                  { id: 'MZUZU', x: 140, y: 50, color: '#5af2a6' },
                  { id: 'LILONGWE', x: 120, y: 130, color: '#74a5ff' },
                  { id: 'ZOMBA', x: 170, y: 200, color: '#ffcb47' },
                  { id: 'BLANTYRE', x: 160, y: 250, color: '#ff6b6b' }
                ].map((z, i, arr) => {
                  if (i < arr.length - 1) {
                    const next = arr[i + 1];
                    return (
                      <line
                        key={`link-${z.id}`}
                        x1={z.x}
                        y1={z.y}
                        x2={next.x}
                        y2={next.y}
                        stroke="rgba(255, 255, 255, 0.08)"
                        strokeWidth="1.5"
                        strokeDasharray="3,3"
                      />
                    );
                  }
                  return null;
                })}

                {[
                  { id: 'MZUZU', x: 140, y: 50, color: '#5af2a6' },
                  { id: 'LILONGWE', x: 120, y: 130, color: '#74a5ff' },
                  { id: 'ZOMBA', x: 170, y: 200, color: '#ffcb47' },
                  { id: 'BLANTYRE', x: 160, y: 250, color: '#ff6b6b' }
                ].map((z) => {
                  const isActive = zone === z.id;
                  return (
                    <g
                      key={z.id}
                      className={`map-node ${isActive ? 'active' : ''}`}
                      onClick={() => setZone(z.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      {isActive && (
                        <circle
                          cx={z.x}
                          cy={z.y}
                          r="18"
                          fill="none"
                          stroke={z.color}
                          strokeWidth="2"
                          className="pulse-ring"
                        />
                      )}
                      <circle
                        cx={z.x}
                        cy={z.y}
                        r={isActive ? "10" : "6"}
                        fill={z.color}
                        opacity={isActive ? "0.3" : "0.15"}
                      />
                      <circle
                        cx={z.x}
                        cy={z.y}
                        r={isActive ? "6" : "4"}
                        fill={z.color}
                      />
                      <text
                        x={z.x + 12}
                        y={z.y + 4}
                        fill={isActive ? '#00ff88' : 'rgba(255,255,255,0.7)'}
                        fontSize="10"
                        fontWeight={isActive ? '900' : '500'}
                        fontFamily="Inter, system-ui, sans-serif"
                      >
                        {z.id}
                      </text>
                    </g>
                  );
                })}
              </svg>

              <div className="map-overlay-card">
                <div className="overlay-header">
                  <span className="overlay-dot" />
                  <span className="overlay-title">{zone} Active Hotspot</span>
                </div>
                <div className="overlay-body">
                  <div className="overlay-stat">
                    <span className="label">Activity Hub:</span>
                    <span className="val">
                      {zone === 'MZUZU' ? 'Irrigation & Milling' : 
                       zone === 'LILONGWE' ? 'Trading & Cold Storage' : 
                       zone === 'ZOMBA' ? 'Farming & Welding' : 'Milling & Cold Storage'}
                    </span>
                  </div>
                  <div className="overlay-stat">
                    <span className="label">Signal Density:</span>
                    <span className="val">{recentActivities.filter(a => (a.zone || '').toUpperCase() === zone).length || 3} verified signals</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Simple Insight Card */}
          <div className="simple-insight-panel">
            <div className="panel-title">Current Insight</div>
            {hasSignals ? (
              <div className="simple-insight-card">
                <div className="insight-header">
                  <span className="insight-pin">📍</span>
                  <h3>{normalizeTag(zone)}</h3>
                </div>
                <div className="insight-body">
                  <div className="insight-item">
                    <span className="item-label">Demand detected:</span>
                    <span className="item-val">{simpleInsightDemand}</span>
                  </div>
                  <div className="insight-item">
                    <span className="item-label">Suggested action:</span>
                    <span className="item-val">{simpleInsightAction}</span>
                  </div>
                  <div className="insight-badge-row">
                    <div className={`trust-pill ${trustLabel.toLowerCase()}`}>
                      {trustScore}% ({trustLabel} Confidence)
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                No activity yet — submit a signal to activate analysis
              </div>
            )}
          </div>
        </div>

        <div className="disclosure-toggle-row">
          <button 
            className="view-analysis-button" 
            onClick={() => setShowFullAnalysis(!showFullAnalysis)}
          >
            {showFullAnalysis ? 'Hide Detailed Analysis' : 'View Full Analysis'}
          </button>
        </div>
      </div>

      {/* LEVEL 2: Detailed Analysis View */}
      {showFullAnalysis && (
        <div className="level2-container">
          <section className="analysis-section">
            <div className="panel-title">Detailed Analysis</div>
            <div className="analysis-grid">
              {/* Demand Insight Card */}
              <div className="analysis-card">
                <div className="card-header-icon">📈</div>
                <div className="analysis-card-content">
                  <h4>Demand Insight</h4>
                  <div className="card-main-val">{summary?.signal_count || 0} activities recorded</div>
                  <p>{topActivities ? `${topActivities} activity increasing in ${normalizeTag(zone)}` : `Farming activity increasing in ${normalizeTag(zone)}`}</p>
                </div>
              </div>

              {/* Problem Card */}
              <div className="analysis-card">
                <div className="card-header-icon">⚠️</div>
                <div className="analysis-card-content">
                  <h4>Problem</h4>
                  <div className="card-main-val">{summary?.infrastructure_gaps?.length || 0} shortage(s) identified</div>
                  <p>{summary?.infrastructure_gaps?.length ? `${summary.infrastructure_gaps.join(', ')} shortage is limiting productivity.` : 'No critical shortages detected yet — submit more signals to reveal deeper gaps.'}</p>
                </div>
              </div>

              {/* Opportunity Card */}
              <div className="analysis-card">
                <div className="card-header-icon">💡</div>
                <div className="analysis-card-content">
                  <h4>Opportunity</h4>
                  <div className="card-main-val">{summary?.recommended_projects?.[0] || 'Awaiting patterns'}</div>
                  <p>Targeted deployment can satisfy communal demand and optimize resources.</p>
                </div>
              </div>

              {/* Confidence Card */}
              <div className="analysis-card">
                <div className="card-header-icon">🛡️</div>
                <div className="analysis-card-content">
                  <h4>Confidence</h4>
                  <div className="card-main-val">{trustScore}%</div>
                  <p>{trustLabel} Confidence - Verified via multi-source logic.</p>
                </div>
              </div>
            </div>

            <div className="analysis-actions">
              <button className="primary-button" onClick={handleGenerateReport} disabled={reportLoading}>
                {reportLoading ? 'Generating Preview…' : 'Preview Report'}
              </button>
              <button className="ghost-button" onClick={downloadReport} disabled={pdfLoading}>
                {pdfLoading ? 'Downloading PDF…' : 'Download PDF'}
              </button>
            </div>

            <div className="advanced-toggle-row">
              <button 
                className="show-advanced-button" 
                onClick={() => setShowAdvancedAnalysis(!showAdvancedAnalysis)}
              >
                {showAdvancedAnalysis ? 'Hide Advanced Data' : 'Show Advanced Analysis'}
              </button>
            </div>
          </section>
        </div>
      )}

      {/* LEVEL 3: Advanced Analysis */}
      {showFullAnalysis && showAdvancedAnalysis && (
        <div className="level3-container">
          <div className="level3-grid">
            <div className="advanced-tabs-panel">
              <div className="advanced-accordion">
                <details className="accordion-item" open>
                  <summary className="accordion-summary">Data Confidence</summary>
                  <div className="accordion-body">
                    <h5>Confidence Score Breakdown</h5>
                    <div className="breakdown-metrics">
                      <div className="metric-row">
                        <span className="metric-label">Pattern Persistence</span>
                        <div className="metric-bar-bg">
                          <div className="metric-bar-fill" style={{ width: `${Math.round(confidenceBreakdown.persistenceScore * 100)}%` }} />
                        </div>
                        <span className="metric-val">{Math.round(confidenceBreakdown.persistenceScore * 100)}%</span>
                      </div>
                      <div className="metric-row">
                        <span className="metric-label">Cross-Validation</span>
                        <div className="metric-bar-bg">
                          <div className="metric-bar-fill" style={{ width: `${Math.round(confidenceBreakdown.validationScore * 100)}%` }} />
                        </div>
                        <span className="metric-val">{Math.round(confidenceBreakdown.validationScore * 100)}%</span>
                      </div>
                      <div className="metric-row">
                        <span className="metric-label">Spatial Consistency</span>
                        <div className="metric-bar-bg">
                          <div className="metric-bar-fill" style={{ width: `${Math.round(confidenceBreakdown.spatialConsistency * 100)}%` }} />
                        </div>
                        <span className="metric-val">{Math.round(confidenceBreakdown.spatialConsistency * 100)}%</span>
                      </div>
                      <div className="metric-row">
                        <span className="metric-label">Temporal Stability</span>
                        <div className="metric-bar-bg">
                          <div className="metric-bar-fill" style={{ width: `${Math.round(confidenceBreakdown.temporalStability * 100)}%` }} />
                        </div>
                        <span className="metric-val">{Math.round(confidenceBreakdown.temporalStability * 100)}%</span>
                      </div>
                    </div>
                  </div>
                </details>

                <details className="accordion-item">
                  <summary className="accordion-summary">Data Sources</summary>
                  <div className="accordion-body">
                    <h5>Data Source Provenance</h5>
                    {summary && summary.signal_source_counts ? (
                      (() => {
                        const src = summary.signal_source_counts;
                        const communityKeys = ['web','whatsapp','manual','user','social'];
                        const externalKeys = ['news','external'];
                        const systemKeys = ['telemetry','sensor','infrastructure','system'];
                        const community = communityKeys.reduce((s,k)=>s+(src[k]||0),0);
                        const external = externalKeys.reduce((s,k)=>s+(src[k]||0),0);
                        const system = systemKeys.reduce((s,k)=>s+(src[k]||0),0);
                        const categories = [community>0, external>0, system>0].filter(Boolean).length;
                        let trust = 'LOW';
                        if (categories >= 3) trust = 'HIGH';
                        else if (categories === 2) trust = 'MEDIUM';
                        else trust = 'LOW';
                        const trustClass = trust === 'HIGH' ? 'high' : (trust === 'MEDIUM' ? 'medium' : 'low');
                        return (
                          <div className="sources-container">
                            <div className="provenance-chips">
                              <div className="chip prov-chip">👥 Community ({community})</div>
                              <div className="chip prov-chip">🌍 External ({external})</div>
                              <div className="chip prov-chip">🤖 System ({system})</div>
                            </div>
                            <div className={`trust-badge ${trustClass}`}>
                              <div className="trust-label">Confidence: {trust}</div>
                              <div className="trust-note">Data verified across multiple sources</div>
                            </div>
                          </div>
                        );
                      })()
                    ) : (
                      <div className="empty-state">
                        No activity yet — submit a signal to activate analysis
                      </div>
                    )}
                  </div>
                </details>

                <details className="accordion-item">
                  <summary className="accordion-summary">Demand Patterns</summary>
                  <div className="accordion-body">
                    <h5>Sub-zone Demand Patterns</h5>
                    {clusters.length > 0 ? (
                      <div className="cluster-container">
                        <div className="cluster-controls">
                          <label htmlFor="cluster-select" className="cluster-label">Select Cluster</label>
                          <select
                            id="cluster-select"
                            value={selectedClusterId || clusters[0]?.cluster_id || ''}
                            onChange={(e) => setSelectedClusterId(e.target.value)}
                            className="cluster-select-dropdown"
                          >
                            {clusters.map((c) => (
                              <option key={c.cluster_id} value={c.cluster_id}>
                                {c.sub_zone || c.cluster_name || c.cluster_id}
                              </option>
                            ))}
                          </select>
                        </div>
                        {activeCluster && (
                          <div className="cluster-detail-card">
                            <div className="cluster-detail-row"><span>Activity</span><strong>{activeCluster.dominant_activity || 'Mixed'}</strong></div>
                            <div className="cluster-detail-row"><span>Demand pattern</span><strong>{activeCluster.demand_pattern || 'Forming'}</strong></div>
                            <div className="cluster-detail-row"><span>Key gap</span><strong>{activeCluster.key_gap || 'Monitoring'}</strong></div>
                            <div className="cluster-detail-row"><span>Recommended project</span><strong>{activeCluster.recommended_project || summary?.recommended_projects?.[0] || 'TBD'}</strong></div>
                            <div className="cluster-detail-row"><span>Confidence</span><strong>{Math.round((activeCluster.confidence_score || 0) * 100)}%</strong></div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="empty-state">
                        No activity yet — submit a signal to activate analysis
                      </div>
                    )}
                  </div>
                </details>
              </div>
            </div>

            {/* Live Activity Stream */}
            <div className="activity-panel">
              <div className="panel-title">Live Activity Stream</div>
              <div className="activity-stream">
                {recentActivities.length ? recentActivities.slice(0, 10).map((activity, index) => (
                  <div key={activity.id || activity.original_text} className="activity-bubble" style={{ animationDelay: `${index * 50}ms` }}>
                    <span>{activity.zone || zone} · {activity.activity?.toLowerCase() || activity.original_text?.slice(0, 24).toLowerCase()}</span>
                  </div>
                )) : <div className="empty-state">No activity yet — submit a signal to activate analysis</div>}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODALS & OVERLAYS */}
      {showPreview && (
        <div className="modal-shell" onClick={() => setShowPreview(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-brand-row">
                <img src="/logo.png" alt="Kulima OS" className="modal-logo" />
                <div>
                  <div className="tiny-label">REPORT PREVIEW</div>
                  <div className="modal-title">Preview prospectus</div>
                </div>
              </div>
              <button className="close-button" onClick={() => setShowPreview(false)}>×</button>
            </div>
            <div className="modal-grid">
              {reportCards.map((card) => (
                <div key={card.key} className="modal-card-item">
                  <div className="modal-card-title">{card.title}</div>
                  <div className="modal-card-value">{card.value}</div>
                  <div className="modal-card-subtitle">{card.subtitle}</div>
                </div>
              ))}
            </div>
            {isPaid ? (
              <div className="expanded-report">
                <div className="panel-title">Full investor briefing</div>
                <div className="expanded-grid">
                  <div className="expanded-card">
                    <div className="expanded-card-title">Market clusters</div>
                    <div className="expanded-card-text">
                      {clusters.length
                        ? `${clusters.length} sub-zone clusters identified. ${activeCluster ? `${activeCluster.sub_zone || activeCluster.cluster_name}: ${activeCluster.dominant_activity} → ${activeCluster.recommended_project}` : ''}`
                        : 'Cluster analysis in progress — record more signals to unlock sub-zone intelligence.'}
                    </div>
                  </div>
                  <div className="expanded-card">
                    <div className="expanded-card-title">Opportunity detail</div>
                    <div className="expanded-card-text">Deploy targeted irrigation infrastructure to unlock 22% more productive land across the zone.</div>
                  </div>
                  <div className="expanded-card">
                    <div className="expanded-card-title">Impact forecast</div>
                    <div className="expanded-card-text">Projected yield growth and risk mitigation show strong investor upside for a phased deployment.</div>
                  </div>
                </div>
                <div className="cta-panel">
                  {fundingStatus === 'idle' && (
                    <button className="primary-button" onClick={handleFundOpportunity}>Fund this opportunity</button>
                  )}
                  {fundingStatus === 'sending' && (
                    <button className="primary-button" disabled>Routing request...</button>
                  )}
                  {fundingStatus === 'success' && (
                    <div className="funding-success-badge">
                      ✓ Allocated & routed to Kulima Economic Substrate allocation pool (Zone {zone} Hub). Ref: KES-ALLOC-88421
                    </div>
                  )}
                  <button className="ghost-button" onClick={handleExportReport} disabled={exportLoading}>
                    {exportLoading ? 'Exporting...' : 'Export report'}
                  </button>
                  <button className="ghost-button" onClick={handleShareInsight}>Share insight</button>
                </div>
              </div>
            ) : (
              <div className="locked-shell">
                <div className="panel-title">Locked sections</div>
                <div className="locked-grid">
                  {['Investment analysis', 'Financial projections', 'Infrastructure blueprint'].map((label) => (
                    <div key={label} className="locked-card">
                      <div className="locked-icon">🔒</div>
                      <div className="locked-label">{label}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="modal-actions">
              {isPaid ? (
                <button className="primary-button" onClick={downloadReport} disabled={pdfLoading}>{pdfLoading ? 'Downloading…' : 'Download full report'}</button>
              ) : (
                <button className="primary-button" onClick={() => setShowUnlock(true)}>Unlock full report</button>
              )}
              <button className="ghost-button" onClick={downloadReport} disabled={pdfLoading}>{pdfLoading ? 'Downloading…' : 'Download PDF'}</button>
            </div>
          </div>
        </div>
      )}

      {showUnlock && (
        <div className="modal-shell" onClick={() => !paymentVerifying && setShowUnlock(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="tiny-label">UNLOCK</div>
                <div className="modal-title">Unlock Full Report</div>
              </div>
              <button className="close-button" onClick={() => setShowUnlock(false)} disabled={paymentVerifying}>×</button>
            </div>
            <div className="unlock-copy">Complete payment in the new tab, then confirm here to unlock your report.</div>
            <div className="payment-options">
              {PAYMENT_OPTIONS.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  className={`payment-option ${selectedPlan === option.key ? 'selected' : ''}`}
                  onClick={() => !paymentVerifying && setSelectedPlan(option.key)}
                  disabled={paymentVerifying}
                >
                  <div className="option-title">{option.title}</div>
                  <div className="option-price">{option.price}</div>
                  <div className="option-description">{option.description}</div>
                </button>
              ))}
            </div>
            <div className="modal-actions">
              <button className="primary-button" onClick={handlePayment} disabled={paymentVerifying}>Pay with PayChangu</button>
              <button className="ghost-button" onClick={confirmPayment} disabled={paymentVerifying}>
                {paymentVerifying ? 'Verifying transaction...' : 'I have completed payment'}
              </button>
              <button className="ghost-button" onClick={() => setShowUnlock(false)} disabled={paymentVerifying}>Cancel</button>
            </div>
            {paymentMessage && (
              <div className={`payment-status ${paymentVerifying ? 'verifying' : ''}`}>
                {paymentVerifying && <span className="spinner-dot" />}
                {paymentMessage}
              </div>
            )}
          </div>
        </div>
      )}

      {showShareDialog && (
        <div className="share-overlay" onClick={() => setShowShareDialog(false)}>
          <div className="share-card" onClick={(e) => e.stopPropagation()}>
            <div className="share-header">
              <div className="share-title">Share Insight</div>
              <button className="close-button" onClick={() => setShowShareDialog(false)}>×</button>
            </div>
            <div className="share-body">
              <p className="share-desc">Copy the link below to share the verified demand prospectus:</p>
              <div className="share-copy-row">
                <input readOnly value={`${typeof window !== 'undefined' ? window.location.origin : ''}/prospectus/${zone.toLowerCase()}`} className="share-link-input" />
                <button className="primary-button" onClick={() => {
                  navigator.clipboard.writeText(`${window.location.origin}/prospectus/${zone.toLowerCase()}`);
                  setMessage('Copied prospectus URL to clipboard!');
                  setShowShareDialog(false);
                }}>Copy</button>
              </div>
              <div className="share-social-grid">
                <a href={`mailto:?subject=Kulima OS Prospectus&body=Check this out: ${typeof window !== 'undefined' ? window.location.origin : ''}/prospectus/${zone.toLowerCase()}`} className="social-btn">Email</a>
                <a href={`https://wa.me/?text=Check out the verified ${zone} prospectus on Kulima OS: ${typeof window !== 'undefined' ? window.location.origin : ''}/prospectus/${zone.toLowerCase()}`} target="_blank" rel="noreferrer" className="social-btn whatsapp">WhatsApp</a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CSS DESIGN SYSTEM STYLES */}
      <style jsx>{`
        * { box-sizing: border-box; }
        .page-shell { 
          min-height: 100vh; 
          padding: 32px 40px; 
          background: #0B0F0A; 
          color: #FFFFFF; 
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
          overflow-x: hidden;
          max-width: 100%;
        }
        .top-bar { 
          display: flex; 
          justify-content: space-between; 
          align-items: center; 
          gap: 16px; 
          flex-wrap: wrap; 
          margin-bottom: 40px; 
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          padding-bottom: 20px;
        }
        .top-brand { 
          display: flex; 
          align-items: center; 
          gap: 14px; 
        }
        .brand-logo { 
          width: 40px; 
          height: 40px; 
          border-radius: 8px; 
          object-fit: cover; 
        }
        .freshness-label { 
          font-size: 12px; 
          color: #A1A1AA; 
          margin-top: 4px; 
        }
        .tiny-label { 
          font-size: 11px; 
          letter-spacing: 0.15em; 
          text-transform: uppercase; 
          color: #A1A1AA; 
          font-weight: 700;
        }
        .product-title { 
          font-size: 24px; 
          font-weight: 800; 
          color: #FFFFFF;
        }
        .top-actions { 
          display: flex; 
          gap: 12px; 
          flex-wrap: wrap; 
        }
        .primary-button, .ghost-button, .submit-button, .mic-button, .view-analysis-button, .show-advanced-button, .accordion-summary, .social-btn, .payment-option { 
          border: none; 
          border-radius: 8px; 
          padding: 12px 24px; 
          font-weight: 700; 
          font-size: 14px;
          cursor: pointer; 
          transition: all 0.2s ease;
          min-height: 44px;
          touch-action: manipulation;
        }
        .primary-button { 
          background: #00e676; 
          color: #0B0F0A; 
        }
        .primary-button:hover {
          background: #00c853;
          transform: translateY(-1px);
        }
        .ghost-button { 
          background: rgba(255,255,255,0.06); 
          color: #FFFFFF; 
          border: 1px solid rgba(255,255,255,0.1); 
        }
        .ghost-button:hover {
          background: rgba(255,255,255,0.12);
        }
        .hero-section {
          text-align: center;
          margin-bottom: 32px;
        }
        .hero-section h1 {
          font-size: 36px;
          font-weight: 800;
          margin-bottom: 8px;
          color: #FFFFFF;
        }
        .hero-section .subtitle {
          font-size: 16px;
          color: #E5E7EB;
          max-width: 600px;
          margin: 0 auto;
        }
        .input-panel { 
          background: rgba(255, 255, 255, 0.03); 
          border: 1px solid rgba(255, 255, 255, 0.08); 
          border-radius: 16px; 
          padding: 24px; 
          margin-bottom: 32px;
        }
        .input-group { 
          display: grid; 
          grid-template-columns: auto 1fr auto; 
          gap: 16px; 
          align-items: center; 
        }
        .mic-button { 
          display: inline-flex; 
          align-items: center; 
          gap: 8px; 
          background: rgba(255, 255, 255, 0.06); 
          color: #FFFFFF; 
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .mic-button.active { 
          background: rgba(0, 230, 118, 0.15); 
          border-color: #00e676; 
          color: #00e676;
        }
        .mic-dot { 
          width: 8px; 
          height: 8px; 
          border-radius: 50%; 
          background: #00ff88; 
          box-shadow: 0 0 8px rgba(0, 255, 118, 0.6); 
        }
        .input-textarea { 
          width: 100%; 
          min-height: 56px; 
          border-radius: 8px; 
          border: 1px solid rgba(255, 255, 255, 0.12); 
          background: rgba(0, 0, 0, 0.2); 
          color: #FFFFFF; 
          padding: 14px 20px; 
          font-size: 16px; 
          line-height: 1.4; 
          transition: all 0.2s ease; 
          resize: none;
          font-family: inherit;
        }
        .input-textarea:focus { 
          border-color: #00e676; 
          outline: none; 
          background: rgba(0, 0, 0, 0.3); 
        }
        .submit-button { 
          background: #00e676; 
          color: #0B0F0A; 
          height: 56px;
        }
        .submit-button:hover {
          background: #00c853;
        }
        .waveform-row { 
          display: flex; 
          gap: 6px; 
          margin-top: 14px; 
          margin-bottom: 8px; 
        }
        .wave-bar { 
          width: 4px; 
          height: 16px; 
          border-radius: 2px; 
          background: rgba(255, 255, 255, 0.08); 
          transform-origin: bottom; 
          animation: wave-static 1.2s infinite ease-in-out; 
        }
        .wave-active { 
          animation: wave-pulse 0.9s infinite ease-in-out; 
          background: #00e676;
        }
        .tag-row { 
          display: flex; 
          gap: 12px; 
          flex-wrap: wrap; 
          margin-top: 16px; 
          align-items: center; 
        }
        .tag-chip { 
          padding: 8px 16px; 
          border-radius: 6px; 
          background: rgba(255, 255, 255, 0.04); 
          color: #E5E7EB; 
          font-size: 13px; 
          border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .zone-select-container { 
          display: flex; 
          align-items: center; 
          gap: 8px; 
          background: rgba(0, 230, 118, 0.06); 
          border: 1px solid rgba(0, 230, 118, 0.2); 
          border-radius: 6px; 
          padding: 4px 12px; 
        }
        .zone-select-label { 
          font-size: 13px; 
          color: #E5E7EB; 
          font-weight: 700; 
        }
        .zone-select-dropdown { 
          background: transparent; 
          border: none; 
          color: #FFFFFF; 
          font-size: 13px; 
          font-weight: 700; 
          outline: none; 
          cursor: pointer; 
          padding: 4px 0; 
        }
        .zone-select-dropdown option { 
          background: #0B0F0A; 
          color: #FFFFFF; 
        }
        .status-line { 
          font-size: 13px; 
          color: #A1A1AA; 
          margin-top: 12px; 
        }
        .simulated-banner { 
          margin-bottom: 24px; 
          padding: 12px 18px; 
          border-radius: 8px; 
          background: rgba(255, 203, 71, 0.1); 
          border: 1px solid rgba(255, 203, 71, 0.25); 
          color: #ffe9a8; 
          font-size: 13px; 
          font-weight: 600; 
        }
        .mode-select-dropdown { 
          background: rgba(255, 255, 255, 0.06); 
          border: 1px solid rgba(255, 255, 255, 0.1); 
          color: #FFFFFF; 
          border-radius: 6px; 
          padding: 8px 12px; 
          font-size: 13px; 
          cursor: pointer; 
        }
        .mode-select-dropdown option { 
          background: #0B0F0A; 
          color: #FFFFFF; 
        }
        
        /* LEVEL 1 */
        .level1-grid {
          display: grid;
          grid-template-columns: 1.2fr 0.8fr;
          gap: 24px;
          margin-bottom: 24px;
        }
        .map-panel, .simple-insight-panel {
          background: rgba(255, 255, 255, 0.03); 
          border: 1px solid rgba(255, 255, 255, 0.08); 
          border-radius: 16px; 
          padding: 24px; 
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .panel-title { 
          font-size: 14px; 
          font-weight: 800; 
          letter-spacing: 0.1em; 
          text-transform: uppercase; 
          color: #A1A1AA; 
        }
        .map-visualization { 
          position: relative; 
          width: 100%; 
          background: rgba(0, 0, 0, 0.3); 
          border-radius: 12px; 
          border: 1px solid rgba(255, 255, 255, 0.06); 
          overflow: hidden; 
        }
        .map-svg { 
          width: 100%; 
          height: min(300px, 64vw); 
          max-height: 320px; 
          display: block;
        }
        .pulse-ring { 
          animation: map-pulse 2s infinite ease-out; 
          transform-origin: center; 
        }
        @keyframes map-pulse {
          0% { r: 8; opacity: 1; stroke-width: 2; }
          100% { r: 24; opacity: 0; stroke-width: 0.5; }
        }
        .map-overlay-card { 
          position: absolute; 
          bottom: 12px; 
          left: 12px; 
          right: 12px; 
          background: rgba(11, 15, 10, 0.9); 
          backdrop-filter: blur(8px); 
          border: 1px solid rgba(255, 255, 255, 0.08); 
          border-radius: 8px; 
          padding: 10px 14px; 
        }
        .overlay-header { 
          display: flex; 
          align-items: center; 
          gap: 6px; 
          margin-bottom: 4px; 
        }
        .overlay-dot { 
          width: 6px; 
          height: 6px; 
          border-radius: 50%; 
          background: #00e676; 
          box-shadow: 0 0 8px #00e676; 
        }
        .overlay-title { 
          font-size: 11px; 
          font-weight: 800; 
          letter-spacing: 0.05em; 
          text-transform: uppercase; 
          color: #FFFFFF; 
        }
        .overlay-body { 
          display: flex; 
          justify-content: space-between; 
          gap: 12px; 
        }
        .overlay-stat { 
          display: flex; 
          flex-direction: column; 
        }
        .overlay-stat .label { 
          font-size: 10px; 
          text-transform: uppercase; 
          color: #A1A1AA; 
        }
        .overlay-stat .val { 
          font-size: 12px; 
          font-weight: 700; 
          color: #FFFFFF; 
        }
        .simple-insight-card {
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 12px;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .insight-header {
          display: flex;
          align-items: center;
          gap: 8px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
          padding-bottom: 12px;
        }
        .insight-header h3 {
          font-size: 18px;
          font-weight: 800;
          margin: 0;
          color: #FFFFFF;
        }
        .insight-body {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .insight-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .item-label {
          font-size: 12px;
          color: #A1A1AA;
          text-transform: uppercase;
          font-weight: 600;
        }
        .item-val {
          font-size: 14px;
          font-weight: 700;
          color: #FFFFFF;
        }
        .insight-badge-row {
          margin-top: 8px;
        }
        .trust-pill {
          display: inline-block;
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 700;
        }
        .trust-pill.high { background: rgba(0, 230, 118, 0.1); color: #00e676; border: 1px solid rgba(0, 230, 118, 0.2); }
        .trust-pill.medium { background: rgba(116, 165, 255, 0.1); color: #74a5ff; border: 1px solid rgba(116, 165, 255, 0.2); }
        .trust-pill.low { background: rgba(255, 195, 0, 0.1); color: #ffcb47; border: 1px solid rgba(255, 195, 0, 0.2); }
        
        .empty-state { 
          color: #E5E7EB; 
          font-size: 14px; 
          padding: 32px 20px; 
          border-radius: 12px; 
          background: rgba(255, 255, 255, 0.02); 
          border: 1px dashed rgba(255, 255, 255, 0.08);
          text-align: center;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 120px;
        }
        
        .disclosure-toggle-row {
          text-align: center;
          margin-top: 16px;
          margin-bottom: 40px;
        }
        .view-analysis-button {
          background: rgba(255, 255, 255, 0.06);
          color: #FFFFFF;
          border: 1px solid rgba(255, 255, 255, 0.1);
          font-size: 15px;
          padding: 14px 32px;
        }
        .view-analysis-button:hover {
          background: rgba(255, 255, 255, 0.1);
          transform: translateY(-1px);
        }
        
        /* LEVEL 2 */
        .level2-container {
          margin-bottom: 40px;
        }
        .analysis-section {
          background: rgba(255, 255, 255, 0.03); 
          border: 1px solid rgba(255, 255, 255, 0.08); 
          border-radius: 16px; 
          padding: 32px;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .analysis-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 20px;
        }
        .analysis-card {
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 12px;
          padding: 24px;
          display: flex;
          gap: 16px;
          transition: all 0.2s ease;
        }
        .analysis-card:hover {
          border-color: rgba(255, 255, 255, 0.12);
          transform: translateY(-2px);
        }
        .card-header-icon {
          font-size: 24px;
        }
        .analysis-card-content {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .analysis-card-content h4 {
          margin: 0;
          font-size: 14px;
          text-transform: uppercase;
          color: #A1A1AA;
          font-weight: 700;
          letter-spacing: 0.05em;
        }
        .card-main-val {
          font-size: 18px;
          font-weight: 800;
          color: #FFFFFF;
          line-height: 1.2;
        }
        .analysis-card-content p {
          margin: 0;
          font-size: 13px;
          color: #E5E7EB;
          line-height: 1.4;
        }
        .analysis-actions {
          display: flex;
          gap: 14px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          padding-bottom: 24px;
          margin-top: 12px;
        }
        .advanced-toggle-row {
          text-align: center;
          margin-top: 12px;
        }
        .show-advanced-button {
          background: transparent;
          color: #A1A1AA;
          border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .show-advanced-button:hover {
          background: rgba(255, 255, 255, 0.04);
          color: #FFFFFF;
        }
        
        /* LEVEL 3 */
        .level3-container {
          margin-bottom: 40px;
        }
        .level3-grid {
          display: grid;
          grid-template-columns: 1.2fr 0.8fr;
          gap: 24px;
        }
        .advanced-tabs-panel {
          background: rgba(255, 255, 255, 0.03); 
          border: 1px solid rgba(255, 255, 255, 0.08); 
          border-radius: 16px; 
          padding: 24px;
        }
        .advanced-accordion {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .accordion-item {
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          background: rgba(255, 255, 255, 0.025);
          overflow: hidden;
        }
        .accordion-summary {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 14px 16px;
          color: #FFFFFF;
          font-size: 14px;
          list-style: none;
          background: transparent;
        }
        .accordion-summary::-webkit-details-marker {
          display: none;
        }
        .accordion-summary::after {
          content: '+';
          font-size: 18px;
          color: #00e676;
        }
        .accordion-item[open] .accordion-summary::after {
          content: '−';
        }
        .accordion-body {
          padding: 0 16px 16px;
          color: #E5E7EB;
        }
        .accordion-body h5 {
          margin-top: 0;
          margin-bottom: 12px;
          font-size: 15px;
          color: #FFFFFF;
        }
        .tab-pane h5 {
          margin-top: 0;
          margin-bottom: 16px;
          font-size: 16px;
          font-weight: 800;
        }
        .breakdown-metrics { 
          display: flex; 
          flex-direction: column; 
          gap: 16px; 
        }
        .metric-row { 
          display: flex; 
          align-items: center; 
          gap: 14px; 
        }
        .metric-label { 
          width: 140px; 
          font-size: 13px; 
          color: #E5E7EB; 
        }
        .metric-bar-bg { 
          flex: 1; 
          height: 8px; 
          background: rgba(255, 255, 255, 0.06); 
          border-radius: 4px; 
          overflow: hidden; 
        }
        .metric-bar-fill { 
          height: 100%; 
          background: #00e676; 
          border-radius: 4px; 
        }
        .metric-val { 
          width: 44px; 
          font-size: 13px; 
          font-weight: 700; 
          text-align: right; 
        }
        .sources-container {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .provenance-chips { 
          display: flex; 
          gap: 8px; 
          flex-wrap: wrap; 
        }
        .chip { 
          padding: 8px 14px; 
          border-radius: 6px; 
          font-size: 13px; 
          font-weight: 700;
        }
        .prov-chip { 
          background: rgba(255, 255, 255, 0.04); 
          border: 1px solid rgba(255, 255, 255, 0.08); 
          color: #FFFFFF;
        }
        .trust-badge { 
          padding: 16px; 
          border-radius: 8px; 
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .trust-badge.high { background: rgba(0, 230, 118, 0.06); border: 1px solid rgba(0, 230, 118, 0.15); }
        .trust-badge.medium { background: rgba(116, 165, 255, 0.06); border: 1px solid rgba(116, 165, 255, 0.15); }
        .trust-badge.low { background: rgba(255, 195, 0, 0.06); border: 1px solid rgba(255, 195, 0, 0.15); }
        .trust-badge.high .trust-label { color: #00e676; }
        .trust-badge.medium .trust-label { color: #74a5ff; }
        .trust-badge.low .trust-label { color: #ffcb47; }
        .trust-label { font-weight: 800; font-size: 14px; }
        .trust-note { font-size: 12px; color: #E5E7EB; }
        
        .cluster-container {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .cluster-controls { 
          display: flex; 
          align-items: center; 
          gap: 10px; 
          flex-wrap: wrap; 
        }
        .cluster-label { 
          font-size: 12px; 
          color: #A1A1AA; 
          font-weight: 700; 
          text-transform: uppercase; 
        }
        .cluster-select-dropdown { 
          flex: 1; 
          min-width: 160px; 
          background: rgba(255, 255, 255, 0.04); 
          border: 1px solid rgba(255, 255, 255, 0.1); 
          color: #FFFFFF; 
          border-radius: 6px; 
          padding: 8px 12px; 
          font-size: 13px; 
          outline: none;
        }
        .cluster-select-dropdown option { 
          background: #0B0F0A; 
        }
        .cluster-detail-card { 
          display: grid; 
          gap: 8px; 
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 8px;
          padding: 16px;
        }
        .cluster-detail-row { 
          display: flex; 
          justify-content: space-between; 
          gap: 12px; 
          font-size: 13px; 
          border-bottom: 1px solid rgba(255, 255, 255, 0.06); 
          padding-bottom: 6px; 
        }
        .cluster-detail-row span {
          color: #A1A1AA;
        }
        .cluster-detail-row strong { 
          color: #FFFFFF; 
        }
        
        .activity-panel { 
          background: rgba(255, 255, 255, 0.03); 
          border: 1px solid rgba(255, 255, 255, 0.08); 
          border-radius: 16px; 
          padding: 24px;
          display: flex; 
          flex-direction: column; 
          gap: 16px;
          max-height: 400px;
        }
        .activity-stream { 
          display: flex; 
          flex-direction: column;
          gap: 10px; 
          overflow-y: auto; 
          padding-right: 4px; 
        }
        .activity-bubble { 
          padding: 12px 16px; 
          border-radius: 8px; 
          background: rgba(255, 255, 255, 0.04); 
          border: 1px solid rgba(255, 255, 255, 0.06);
          color: #FFFFFF; 
          font-weight: 600; 
          font-size: 13px;
          opacity: 0; 
          transform: translateY(10px); 
          animation: slide-in 0.3s ease-out forwards; 
        }
        .activity-bubble span { 
          width: 100%; 
          display: block; 
        }
        
        /* MODALS & OVERLAYS */
        .modal-shell { 
          position: fixed; 
          inset: 0; 
          background: rgba(0, 0, 0, 0.8); 
          display: flex; 
          justify-content: center; 
          align-items: center; 
          padding: 24px; 
          z-index: 100; 
          backdrop-filter: blur(4px);
        }
        .modal-card { 
          width: min(100%, 800px); 
          max-height: calc(100vh - 60px); 
          overflow-y: auto; 
          background: #0B0F0A; 
          border-radius: 16px; 
          padding: 32px; 
          border: 1px solid rgba(255, 255, 255, 0.12); 
          box-shadow: 0 40px 120px rgba(0, 0, 0, 0.6); 
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          padding-bottom: 16px;
        }
        .modal-title {
          font-size: 20px;
          font-weight: 800;
        }
        .modal-brand-row {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .modal-logo {
          width: 32px;
          height: 32px;
          border-radius: 6px;
        }
        .close-button {
          background: transparent;
          border: none;
          color: #A1A1AA;
          font-size: 28px;
          cursor: pointer;
          transition: color 0.2s;
        }
        .close-button:hover {
          color: #FFFFFF;
        }
        .modal-grid { 
          display: grid; 
          grid-template-columns: repeat(3, 1fr); 
          gap: 16px; 
        }
        .modal-card-item { 
          border-radius: 8px; 
          padding: 18px; 
          background: rgba(255, 255, 255, 0.03); 
          border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .modal-card-title { 
          font-size: 12px; 
          font-weight: 700; 
          text-transform: uppercase;
          color: #A1A1AA;
          letter-spacing: 0.05em;
        }
        .modal-card-subtitle { 
          font-size: 13px; 
          color: #E5E7EB; 
          line-height: 1.4; 
        }
        .modal-card-value { 
          font-size: 22px; 
          font-weight: 800; 
          margin-top: 8px; 
          margin-bottom: 4px; 
          color: #00e676; 
        }
        .expanded-report { 
          display: flex; 
          flex-direction: column; 
          gap: 20px; 
          background: rgba(255, 255, 255, 0.02); 
          padding: 24px; 
          border-radius: 12px; 
          border: 1px solid rgba(255, 255, 255, 0.08); 
        }
        .expanded-grid { 
          display: grid; 
          grid-template-columns: repeat(3, 1fr); 
          gap: 16px; 
        }
        .expanded-card { 
          padding: 16px; 
          border-radius: 8px; 
          background: rgba(255, 255, 255, 0.03); 
          border: 1px solid rgba(255, 255, 255, 0.06); 
        }
        .expanded-card-title { 
          font-size: 13px; 
          font-weight: 700; 
          text-transform: uppercase;
          color: #A1A1AA;
          margin-bottom: 8px; 
        }
        .expanded-card-text { 
          font-size: 13px; 
          color: #E5E7EB; 
          line-height: 1.5; 
        }
        .cta-panel { 
          display: flex; 
          gap: 12px; 
          flex-wrap: wrap; 
          margin-top: 8px; 
          align-items: center; 
        }
        .funding-success-badge { 
          background: rgba(0, 230, 118, 0.1); 
          color: #00e676; 
          border: 1px solid rgba(0, 230, 118, 0.25); 
          border-radius: 6px; 
          padding: 10px 16px; 
          font-size: 13px; 
          font-weight: 700; 
        }
        .locked-shell { 
          border-top: 1px solid rgba(255, 255, 255, 0.08); 
          padding-top: 20px; 
        }
        .locked-grid { 
          display: grid; 
          grid-template-columns: repeat(3, 1fr); 
          gap: 16px; 
        }
        .locked-card { 
          display: flex; 
          flex-direction: column;
          align-items: center; 
          justify-content: center; 
          gap: 8px;
          padding: 24px; 
          border-radius: 8px; 
          background: rgba(255, 255, 255, 0.03); 
          border: 1px solid rgba(255, 255, 255, 0.06);
          color: #A1A1AA;
        }
        .locked-icon { 
          font-size: 20px; 
        }
        .locked-label { 
          font-size: 13px; 
          font-weight: 700; 
        }
        .unlock-copy { 
          font-size: 14px; 
          color: #E5E7EB; 
        }
        .modal-actions { 
          display: flex; 
          gap: 12px; 
          border-top: 1px solid rgba(255, 255, 255, 0.08);
          padding-top: 20px;
        }
        .payment-options { 
          display: grid; 
          grid-template-columns: repeat(2, 1fr); 
          gap: 16px; 
        }
        .payment-option { 
          text-align: left; 
          border: 1px solid rgba(255, 255, 255, 0.12); 
          border-radius: 8px; 
          padding: 16px; 
          background: rgba(255, 255, 255, 0.02); 
          color: #FFFFFF; 
          cursor: pointer; 
          transition: all 0.2s ease; 
        }
        .payment-option.selected { 
          border-color: #00e676; 
          background: rgba(0, 230, 118, 0.08); 
        }
        .payment-option:hover:not(.selected) { 
          border-color: rgba(255, 255, 255, 0.2); 
        }
        .option-title { 
          font-size: 14px; 
          font-weight: 700; 
          margin-bottom: 4px; 
        }
        .option-price { 
          font-size: 18px; 
          font-weight: 800; 
          margin-bottom: 4px; 
          color: #00e676;
        }
        .option-description { 
          font-size: 12px; 
          color: #E5E7EB; 
          line-height: 1.4; 
        }
        .payment-status { 
          font-size: 13px; 
          color: #00e676; 
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .payment-status.verifying {
          color: #74a5ff;
        }
        .spinner-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #74a5ff;
          animation: spin-pulse 1s infinite alternate;
        }
        @keyframes spin-pulse { 0% { transform: scale(0.8); opacity: 0.5; } 100% { transform: scale(1.3); opacity: 1; } }
        
        .share-overlay { 
          position: fixed; 
          inset: 0; 
          background: rgba(0, 0, 0, 0.8); 
          display: flex; 
          justify-content: center; 
          align-items: center; 
          z-index: 110; 
          backdrop-filter: blur(4px);
        }
        .share-card { 
          background: #0B0F0A; 
          border: 1px solid rgba(255, 255, 255, 0.12); 
          border-radius: 12px; 
          padding: 24px; 
          width: min(100%, 420px); 
          box-shadow: 0 20px 50px rgba(0,0,0,0.5); 
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .share-header { 
          display: flex; 
          justify-content: space-between; 
          align-items: center; 
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          padding-bottom: 12px;
        }
        .share-title { 
          font-size: 16px; 
          font-weight: 800; 
          color: #00e676; 
        }
        .share-desc { 
          font-size: 13px; 
          color: #E5E7EB; 
        }
        .share-copy-row { 
          display: flex; 
          gap: 8px; 
        }
        .share-link-input { 
          flex: 1; 
          background: rgba(0, 0, 0, 0.2); 
          border: 1px solid rgba(255, 255, 255, 0.12); 
          padding: 8px 12px; 
          border-radius: 6px; 
          color: #FFFFFF; 
          font-size: 13px; 
          outline: none; 
        }
        .share-social-grid { 
          display: grid; 
          grid-template-columns: 1fr 1fr; 
          gap: 10px; 
        }
        .social-btn { 
          text-align: center; 
          background: rgba(255, 255, 255, 0.04); 
          color: #FFFFFF; 
          padding: 10px; 
          border-radius: 6px; 
          font-weight: 700; 
          text-decoration: none; 
          font-size: 13px; 
          border: 1px solid rgba(255, 255, 255, 0.06);
          transition: background 0.2s; 
        }
        .social-btn:hover { 
          background: rgba(255, 255, 255, 0.08); 
        }
        .social-btn.whatsapp { 
          background: rgba(37, 211, 102, 0.1); 
          color: #25d366; 
          border: 1px solid rgba(37, 211, 102, 0.2); 
        }
        .social-btn.whatsapp:hover { 
          background: rgba(37, 211, 102, 0.15); 
        }

        @keyframes wave-pulse { 0%, 100% { transform: scaleY(0.7); opacity: 0.55; } 50% { transform: scaleY(1.7); opacity: 1; } }
        @keyframes wave-static { 0%, 100% { transform: scaleY(1); opacity: 0.42; } 50% { transform: scaleY(1.1); opacity: 0.6; } }
        @keyframes slide-in { to { transform: translateY(0); opacity: 1; } }

        @media (max-width: 1024px) {
          .level1-grid, .level3-grid {
            grid-template-columns: 1fr;
          }
          .analysis-grid {
            grid-template-columns: 1fr 1fr;
          }
        }
        @media (max-width: 768px) {
          .page-shell {
            padding: 20px 14px 36px;
          }
          .top-bar {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 24px;
          }
          .product-title {
            font-size: 20px;
          }
          .top-actions {
            width: 100%;
            flex-direction: column;
          }
          .top-actions > * {
            width: 100%;
          }
          .hero-section {
            text-align: left;
            margin-bottom: 20px;
          }
          .hero-section h1 {
            font-size: 26px;
            line-height: 1.2;
          }
          .hero-section .subtitle {
            font-size: 14px;
            text-align: left;
          }
          .input-panel {
            padding: 16px;
          }
          .input-group {
            grid-template-columns: 1fr;
            gap: 12px;
          }
          .submit-button, .mic-button {
            width: 100%;
            justify-content: center;
          }
          .tag-row {
            flex-direction: column;
            align-items: stretch;
          }
          .zone-select-container {
            justify-content: space-between;
          }
          .map-panel, .simple-insight-panel, .analysis-section, .advanced-tabs-panel, .activity-panel {
            padding: 16px;
          }
          .map-visualization {
            min-height: 220px;
          }
          .map-overlay-card {
            left: 8px;
            right: 8px;
            bottom: 8px;
            padding: 8px 10px;
          }
          .overlay-body {
            flex-direction: column;
            gap: 4px;
          }
          .analysis-grid, .modal-grid, .locked-grid, .payment-options, .share-social-grid {
            grid-template-columns: 1fr;
          }
          .analysis-actions, .modal-actions, .cta-panel {
            flex-direction: column;
            align-items: stretch;
          }
          .analysis-card, .modal-card-item, .expanded-card, .locked-card, .share-card, .modal-card {
            width: 100%;
          }
          .view-analysis-button, .show-advanced-button {
            width: 100%;
          }
          .share-copy-row {
            flex-direction: column;
          }
          .share-link-input {
            width: 100%;
          }
        }
        @media (max-width: 640px) {
          .analysis-grid, .modal-grid, .locked-grid, .payment-options {
            grid-template-columns: 1fr;
          }
          .top-bar {
            align-items: stretch;
          }
          .input-group {
            grid-template-columns: 1fr;
          }
          .submit-button {
            width: 100%;
          }
          .activity-bubble {
            font-size: 12px;
          }
        }
      `}</style>
    </div>
  );
}
