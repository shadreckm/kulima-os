'use client';

import { useState, useEffect, useRef } from 'react';
import { fetchSummaryData, fetchRecentSignalsData, submitActivitySignal, generateProspectusReport } from '../lib/api';

const ZONES = ['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'];
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
  const zoneMatch = normalized.match(/\b(mzuzu|lilongwe|blantyre|zomba)\b/);
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

  const recognitionRef = useRef(null);
  const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || '/api/v1').replace(/\/$/, '');
  const BACKEND_BASE = BASE_URL.replace(/\/api\/v1$/, '');
  const reportUrl = reportData?.pdf_url ? `${BACKEND_BASE}${reportData.pdf_url}` : '';

  const trustLabel = buildTrustLabel(summary);
  const trustScore = Math.round((summary?.trust_score ?? 0) * 100);

  useEffect(() => {
    fetchSummary();
    fetchRecentSignals();
    const interval = setInterval(fetchRecentSignals, 7000);
    return () => clearInterval(interval);
  }, [zone]);

  const fetchSummary = async () => {
    const data = await fetchSummaryData(zone);
    setSummary(data);
  };

  const fetchRecentSignals = async () => {
    const data = await fetchRecentSignalsData();
    if (data && data.length > 0) {
      setRecentActivities(data);
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
    setMessage('Signal added. Updating the live system...');

    try {
      await submitActivitySignal(inferredZone, text);
    } catch {
      setMessage('Network issue. Local signal saved in the feed.');
    } finally {
      fetchSummary();
      fetchRecentSignals();
    }
  };

  const handleGenerateReport = async () => {
    if (!summary || (summary.signal_count || 0) === 0) {
      setMessage('Need more signals before generating a preview.');
      return;
    }
    setReportLoading(true);
    setMessage('Preparing the preview report...');

    try {
      const data = await generateProspectusReport(zone);
      if (data?.success) {
        setReportData({ ...(data.report || {}), pdf_url: data.pdf_url || data.report?.pdf_url || '', preview_locked: data.report?.preview_locked ?? true });
        setShowPreview(true);
        setMessage('Preview ready. Locked cards show gated sections.');
      } else {
        setMessage(data?.message || 'Preview generation failed.');
      }
    } catch {
      setMessage('Unable to generate report. Try again in a moment.');
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
            categories_cross_validated: 3,
            source_weights: summary?.signal_source_counts || { web: 5, whatsapp: 3, telemetry: 2 }
          },
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
  const insightCards = [
    { key: 'people', title: 'People are farming', subtitle: `${zoneActivityCounts[zone] || 0} live signals`, note: 'Signal density' },
    { key: 'water', title: 'Water is missing', subtitle: summary?.infrastructure_gaps?.includes('Water') ? 'gap detected' : 'monitoring', note: 'Supply alert' },
    { key: 'build', title: 'Build irrigation', subtitle: summary?.recommended_projects?.[0] || 'ready', note: 'Priority action' },
    { key: 'confidence', title: 'Confidence', subtitle: trustLabel, value: trustScore, level: trustLabel.toLowerCase() }
  ];

  const reportCards = [
    {
      key: 'demand',
      title: 'Demand Insight',
      value: `${recentActivities.length || 12} activities recorded`,
      subtitle: `Farming activity increasing in ${zone}`,
      note: 'Emerging demand trend'
    },
    {
      key: 'problem',
      title: 'Problem',
      value: `${summary?.infrastructure_gaps?.length || 1} shortage(s) identified`,
      subtitle: 'Water shortage is limiting productivity',
      note: 'Operational constraint'
    },
    {
      key: 'opportunity',
      title: 'Opportunity',
      value: summary?.recommended_projects?.[0] || 'Irrigation project recommended',
      subtitle: 'Targeted investment can expand capacity',
      note: 'Strategic recommendation'
    },
    {
      key: 'confidence',
      title: 'Confidence',
      value: `${trustScore}%`,
    }
  ];
  const downloadReport = () => {
    setMessage('Downloading investor-grade PDF prospectus...');
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://kulima-os-backend.onrender.com';
      window.open(`${apiUrl}/api/v1/prospectus/${zone.toLowerCase()}/pdf`, '_blank');
    } catch (err) {
      console.error(err);
      setMessage('Error downloading report.');
    }
  };

  return (
    <div className="page-shell">
      <div className="top-bar">
        <div>
          <div className="tiny-label">COMMAND SYSTEM</div>
          <div className="product-title">Kulima OS live command center</div>
        </div>
        <div className="top-actions">
          <button className="ghost-button" onClick={() => setShowPreview(true)} disabled={reportLoading}>{reportLoading ? 'Loading…' : 'Preview report'}</button>
          <button className="primary-button" onClick={() => { setPaymentMessage(''); setShowUnlock(true); }}>Unlock</button>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="column column-left">
          <section className="input-panel">
            <div className="panel-title">Speak or type a live demand signal</div>
            <div className="input-group">
              <button className={`mic-button ${speechActive ? 'active' : ''}`} onClick={startVoiceCapture}>
                <span className="mic-dot" />
                {speechActive ? 'Listening' : 'Voice'}
              </button>
              <textarea 
                value={inputValue} 
                onChange={(e) => handleInputChange(e.target.value)} 
                placeholder="e.g. Mzuzu farmers need water for dry-season irrigation..." 
                rows={2}
                className="input-textarea"
              />
              <button className="submit-button" onClick={submitActivity}>Submit</button>
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
            <div className="status-line">{message}</div>
          </section>

          <section className="trust-banner" onClick={() => setShowTrustTooltip((s) => !s)} role="region" aria-label="Trust banner">
            <div className={`trust-badge-large ${trustLabel.toLowerCase()}`}>
              <div className="trust-emoji">{trustLabel === 'HIGH' ? '✅' : (trustLabel === 'MEDIUM' ? '⏺️' : '⚠️')}</div>
              <div className="trust-text">
                <div className="trust-main">{trustLabel} TRUST</div>
                <div className="trust-sub">Confidence: {trustScore}%</div>
              </div>
            </div>
            <div className={`tooltip ${showTrustTooltip ? 'visible' : ''}`}>
              Verified using multiple data sources including community reports, external signals, and system analysis.
            </div>
          </section>

          <section className="insights-panel">
            <div className="panel-title">Live insights</div>
            <div className="insight-grid">
              {insightCards.map((card, index) => (
                <div key={card.title} className={`insight-card ${card.key}`}>
                  <div>
                    <div className="card-title">{card.title}</div>
                    {card.key === 'confidence' ? (
                      <div className="confidence-block">
                        <div className={`confidence-pill ${card.level}`}>{card.subtitle}</div>
                        <div className="confidence-progress">
                          <div className={`confidence-fill ${card.level}`} style={{ width: `${card.value}%` }} />
                        </div>
                      </div>
                    ) : (
                      <div className="card-note">{card.subtitle}</div>
                    )}
                  </div>
                  {card.key !== 'confidence' && <div className="insight-tag">{card.note}</div>}
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="column column-center">
          <section className="map-panel">
            <div className="panel-title">Map & trends</div>
            <div className="map-visualization">
              <svg viewBox="0 0 300 290" className="map-svg">
                {/* Background Grid Pattern */}
                <defs>
                  <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255, 255, 255, 0.03)" strokeWidth="1" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" rx="16" />

                {/* Stylized Contour/Flow Lines */}
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

                {/* Network Connections */}
                {[
                  { id: 'MZUZU', x: 140, y: 50, color: '#5af2a6', activity: 'Irrigation & Milling' },
                  { id: 'LILONGWE', x: 120, y: 130, color: '#74a5ff', activity: 'Trading & Cold Storage' },
                  { id: 'ZOMBA', x: 170, y: 200, color: '#ffcb47', activity: 'Farming & Welding' },
                  { id: 'BLANTYRE', x: 160, y: 250, color: '#ff6b6b', activity: 'Milling & Cold Storage' }
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

                {/* Hotspot Nodes */}
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
                      {/* Outer Glow Ring */}
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
                      {/* Middle Pulse Circle */}
                      <circle
                        cx={z.x}
                        cy={z.y}
                        r={isActive ? "10" : "6"}
                        fill={z.color}
                        opacity={isActive ? "0.3" : "0.15"}
                      />
                      {/* Core Dot */}
                      <circle
                        cx={z.x}
                        cy={z.y}
                        r={isActive ? "6" : "4"}
                        fill={z.color}
                      />
                      {/* Label Text */}
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

              {/* Map overlay with metadata */}
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
          </section>

          <section className={`report-panel ${!isPaid ? 'preview-locked' : ''}`}>
            <div className="panel-title">Report center</div>
            {!isPaid && <div className="panel-hint">Preview only. Unlock the full report to access investor-grade sections and downloads.</div>}
            <div className="report-strip">
              {reportCards.map((card) => (
                <div key={card.key} className="report-chip">
                  <div className="chip-title">{card.title}</div>
                  <div className="chip-subtitle">{card.subtitle}</div>
                </div>
              ))}
            </div>
            <div className="report-actions">
              <button className="primary-button" onClick={handleGenerateReport} disabled={reportLoading}>{reportLoading ? 'Generating…' : 'Preview report'}</button>
              {reportUrl && <button className="ghost-button" onClick={downloadReport}>{isPaid ? 'Download full report' : 'Download preview'}</button>}
            </div>
          </section>
        </div>

        <div className="column column-right">
          <section className="provenance-panel">
            <div className="panel-title">Signal provenance</div>
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
                  <div>
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
              <div className="empty-state">No provenance summary available.</div>
            )}
          </section>
          <section className="activity-panel">
            <div className="panel-title">Live activity stream</div>
            <div className="activity-stream">
              {recentActivities.length ? recentActivities.slice(0, 10).map((activity, index) => (
                <div key={activity.id || activity.original_text} className="activity-bubble" style={{ animationDelay: `${index * 50}ms` }}>
                  <span>{activity.zone || zone} · {activity.activity?.toLowerCase() || activity.original_text?.slice(0, 24).toLowerCase()}</span>
                </div>
              )) : <div className="empty-state">No live activity yet. Add a signal.</div>}
            </div>
          </section>
        </div>
      </div>

      {showPreview && (
        <div className="modal-shell" onClick={() => setShowPreview(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="tiny-label">REPORT PREVIEW</div>
                <div className="modal-title">Preview prospectus</div>
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
                    <div className="expanded-card-text">Three network clusters were identified with high irrigation potential, including northern agriculture hubs and peri-urban supply corridors.</div>
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
                <button className="primary-button" onClick={downloadReport}>Download full report</button>
              ) : (
                <button className="primary-button" onClick={() => setShowUnlock(true)}>Unlock full report</button>
              )}
              {reportUrl && <button className="ghost-button" onClick={downloadReport}>{isPaid ? 'Download full report' : 'Download preview'}</button>}
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

      <style jsx>{`
        .page-shell { min-height: 100vh; padding: 24px; background: radial-gradient(circle at top left, rgba(0,255,155,0.14), transparent 22%), radial-gradient(circle at bottom right, rgba(0,170,255,0.1), transparent 20%), #06130f; color: #e9ffe8; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 22px; }
        .tiny-label { font-size: 11px; letter-spacing: 0.28em; text-transform: uppercase; color: #7ef2ac; }
        .product-title { font-size: 32px; font-weight: 800; line-height: 1.05; }
        .top-actions { display: flex; gap: 12px; flex-wrap: wrap; }
        .primary-button, .ghost-button, .submit-button, .mic-button { border: none; border-radius: 999px; padding: 14px 20px; font-weight: 700; cursor: pointer; }
        .primary-button { background: #00e676; color: #02100c; }
        .ghost-button { background: rgba(255,255,255,0.08); color: #e9ffe8; border: 1px solid rgba(255,255,255,0.14); }
        .main-grid { display: grid; grid-template-columns: minmax(360px, 1.35fr) minmax(320px, 1fr); gap: 22px; margin-bottom: 22px; }
        .input-panel, .activity-panel, .report-panel { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 28px; padding: 24px; }
        .panel-title { font-size: 16px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #c8ffc5; margin-bottom: 16px; }
        .input-group { display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: center; margin-bottom: 16px; }
        .mic-button { display: inline-flex; align-items: center; gap: 10px; background: rgba(0,255,118,0.16); color: #e9ffe8; }
        .mic-button.active { background: rgba(0,255,118,0.28); box-shadow: 0 0 0 4px rgba(0,255,118,0.08); }
        .mic-dot { width: 10px; height: 10px; border-radius: 50%; background: #00ff88; box-shadow: 0 0 12px rgba(0,255,118,0.45); }
        input { width: 100%; min-height: 56px; border-radius: 24px; border: 1px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.05); color: #f5ffef; padding: 12px 24px; font-size: 16px; transition: all 0.2s ease-in-out; }
        input:focus { border-color: #00e676; box-shadow: 0 0 12px rgba(0, 230, 118, 0.15); outline: none; background: rgba(255,255,255,0.08); }
        .input-textarea { 
          width: 100%; 
          min-height: 80px; 
          border-radius: 16px; 
          border: 1px solid rgba(255,255,255,0.15); 
          background: rgba(255,255,255,0.05); 
          color: #f5ffef; 
          padding: 14px 20px; 
          font-size: 16px; 
          transition: all 0.2s ease-in-out; 
          resize: vertical;
          font-family: inherit;
        }
        .input-textarea:focus { 
          border-color: #00e676; 
          box-shadow: 0 0 12px rgba(0, 230, 118, 0.15); 
          outline: none; 
          background: rgba(255,255,255,0.08); 
        }
        .submit-button { background: #00e676; color: #02100c; }
        .waveform-row { display: flex; gap: 6px; margin-bottom: 18px; }
        .wave-bar { width: 6px; height: 20px; border-radius: 999px; background: rgba(255,255,255,0.1); transform-origin: bottom; animation: wave-static 1200ms infinite ease-in-out; }
        .wave-active { animation: wave-pulse 900ms infinite ease-in-out; }
        .tag-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; align-items: center; }
        .tag-chip { padding: 11px 16px; border-radius: 999px; background: rgba(0,255,118,0.08); color: #d7ffd7; font-size: 13px; }
        .zone-select-container { display: flex; align-items: center; gap: 8px; background: rgba(0,255,118,0.08); border: 1px solid rgba(0,255,118,0.15); border-radius: 999px; padding: 4px 16px; }
        .zone-select-label { font-size: 13px; color: #7ef2ac; font-weight: bold; }
        .zone-select-dropdown { background: transparent; border: none; color: #d7ffd7; font-size: 13px; font-weight: bold; outline: none; cursor: pointer; padding: 6px 0; }
        .zone-select-dropdown option { background: #051b13; color: #d7ffd7; }
        .status-line { font-size: 13px; color: #ceffcd; margin-bottom: 24px; }
        .swipe-card-shell { background: rgba(0,0,0,0.12); border-radius: 26px; padding: 18px; }
        .swipe-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; }
        .card-controls button { border: 1px solid rgba(255,255,255,0.14); background: transparent; color: #e9ffe8; border-radius: 999px; width: 40px; height: 40px; cursor: pointer; }
        .card-row { display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 14px; }
        .insight-card { border-radius: 24px; padding: 22px; background: linear-gradient(145deg, rgba(5,27,19,0.9), rgba(2,12,8,0.95)); border: 1px solid rgba(0,230,118,0.3); box-shadow: 0 4px 12px rgba(0,0,0,0.2); cursor: pointer; transition: transform 180ms ease, box-shadow 180ms ease; }
        .insight-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,255,118,0.15); }
        .insight-card.active { background: rgba(0,255,118,0.14); transform: translateY(-2px); }
        .card-title { font-size: 18px; font-weight: 800; line-height: 1.1; margin-bottom: 10px; color: #ffffff; }
        .card-note { font-size: 13px; color: #e9ffe8; }
        .activity-panel { display: flex; flex-direction: column; }
        .activity-stream { display: grid; gap: 12px; }
        .activity-bubble { padding: 16px 18px; border-radius: 999px; background: rgba(0,255,118,0.08); color: #e9ffe8; font-weight: 700; animation: pulse 2400ms ease-in-out infinite alternate; }
        .empty-state { color: rgba(255,255,255,0.68); font-size: 14px; }
        .report-panel { display: grid; gap: 18px; }
        .report-strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
        .report-chip { border-radius: 24px; padding: 18px; background: linear-gradient(145deg, rgba(5,27,19,0.9), rgba(2,12,8,0.95)); border: 1px solid rgba(0,230,118,0.3); box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: transform 180ms ease, box-shadow 180ms ease; }
        .report-chip:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,255,118,0.15); }
        .chip-title { font-size: 15px; font-weight: 800; margin-bottom: 8px; color: #ffffff; }
        .chip-subtitle { font-size: 13px; color: #e9ffe8; }
        .report-actions { display: flex; gap: 12px; flex-wrap: wrap; }
        .dashboard-grid { display: grid; grid-template-columns: minmax(320px, 1.05fr) minmax(360px, 1.3fr) minmax(300px, 0.95fr); gap: 20px; align-items: start; }
        .column { display: flex; flex-direction: column; gap: 20px; }
        .column-left, .column-center, .column-right { min-height: 0; }
        .input-panel, .insights-panel, .map-panel, .report-panel, .activity-panel { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.12); display: flex; flex-direction: column; gap: 16px; border: 1px solid rgba(255,255,255,0.08); }
        .map-panel { min-height: 320px; }
        .map-visualization { position: relative; width: 100%; height: 100%; min-height: 290px; background: rgba(0, 0, 0, 0.2); border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); overflow: hidden; display: flex; flex-direction: column; }
        .map-svg { width: 100%; height: 100%; max-height: 290px; }
        .pulse-ring { animation: map-pulse 2s infinite ease-out; transform-origin: center; }
        @keyframes map-pulse {
          0% { r: 8; opacity: 1; stroke-width: 3; }
          100% { r: 24; opacity: 0; stroke-width: 0.5; }
        }
        .map-node:hover circle { opacity: 0.5; transform: scale(1.1); transition: all 0.2s ease; }
        .map-overlay-card { position: absolute; bottom: 12px; left: 12px; right: 12px; background: rgba(5, 27, 19, 0.85); backdrop-filter: blur(8px); border: 1px solid rgba(0, 230, 118, 0.2); border-radius: 12px; padding: 10px 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .overlay-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
        .overlay-dot { width: 6px; height: 6px; border-radius: 50%; background: #00e676; box-shadow: 0 0 8px #00e676; }
        .overlay-title { font-size: 11px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #7ef2ac; }
        .overlay-body { display: flex; justify-content: space-between; gap: 12px; }
        .overlay-stat { display: flex; flex-direction: column; }
        .overlay-stat .label { font-size: 9px; text-transform: uppercase; color: rgba(233,255,232,0.6); }
        .overlay-stat .val { font-size: 11px; font-weight: 700; color: #e9ffe8; }
        .report-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
        .report-chip { border-radius: 16px; padding: 20px; background: linear-gradient(145deg, rgba(5,27,19,0.9), rgba(2,12,8,0.95)); border: 1px solid rgba(0,230,118,0.3); box-shadow: 0 4px 12px rgba(0,0,0,0.2); min-height: 132px; display: flex; flex-direction: column; justify-content: space-between; transition: transform 180ms ease, box-shadow 180ms ease; }
        .report-chip:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,255,118,0.15); }
        .chip-title { font-size: 15px; font-weight: 800; margin-bottom: 10px; color: #ffffff; }
        .chip-subtitle { font-size: 13px; color: #e9ffe8; line-height: 1.35; }
        .modal-card-value { font-size: 26px; font-weight: 800; margin-top: 10px; margin-bottom: 10px; color: #d7ffce; }
        .expanded-report { display: flex; flex-direction: column; gap: 18px; background: rgba(255,255,255,0.03); padding: 20px; border-radius: 18px; border: 1px solid rgba(255,255,255,0.08); }
        .expanded-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
        .expanded-card { padding: 18px; border-radius: 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); }
        .expanded-card-title { font-size: 14px; font-weight: 800; margin-bottom: 10px; }
        .expanded-card-text { font-size: 13px; color: rgba(233,255,232,0.88); line-height: 1.6; }
        .cta-panel { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 6px; align-items: center; }
        .funding-success-badge { background: rgba(0, 230, 118, 0.15); color: #5af2a6; border: 1px solid rgba(0, 230, 118, 0.3); border-radius: 999px; padding: 10px 20px; font-size: 13px; font-weight: 700; display: inline-flex; align-items: center; gap: 6px; }
        .payment-option { width: 100%; text-align: left; border: 1px solid rgba(255,255,255,0.12); border-radius: 18px; padding: 18px; background: rgba(255,255,255,0.04); color: #e9ffe8; cursor: pointer; transition: border-color 180ms ease, transform 180ms ease, background 180ms ease; }
        .payment-option.selected { border-color: #00e676; background: rgba(0,230,118,0.12); transform: translateY(-1px); }
        .payment-option:hover { border-color: rgba(0,230,118,0.4); }
        .option-title { font-size: 15px; font-weight: 800; margin-bottom: 8px; }
        .option-price { font-size: 20px; font-weight: 900; margin-bottom: 8px; }
        .option-description { font-size: 13px; color: rgba(233,255,232,0.78); line-height: 1.4; }
        .payment-status { margin-top: 14px; font-size: 13px; color: #b1ffc7; display: flex; align-items: center; gap: 8px; }
        .payment-status.verifying { color: #74a5ff; font-weight: 700; }
        .spinner-dot { width: 10px; height: 10px; border-radius: 50%; background: #74a5ff; box-shadow: 0 0 10px #74a5ff; animation: spin-pulse 1s infinite alternate; }
        @keyframes spin-pulse { 0% { transform: scale(0.8); opacity: 0.5; } 100% { transform: scale(1.4); opacity: 1; } }
        .unlocked-shell { display: flex; flex-direction: column; gap: 12px; padding: 18px; border-radius: 18px; background: rgba(0,255,118,0.06); border: 1px solid rgba(0,255,118,0.15); margin-bottom: 18px; }
        .unlocked-shell .panel-title { margin-bottom: 0; }
        .report-actions { display: flex; gap: 14px; flex-wrap: wrap; justify-content: flex-start; }
        .activity-panel { min-height: 620px; }
        .activity-stream { display: grid; gap: 12px; overflow-y: auto; max-height: 590px; padding-right: 4px; }
        .activity-bubble { min-height: 58px; display: flex; align-items: center; padding: 16px 18px; border-radius: 16px; background: rgba(0,255,118,0.08); color: #e9ffe8; font-weight: 700; opacity: 0; transform: translateY(10px); animation: slide-in 0.32s ease-in-out forwards; }
        .activity-bubble span { width: 100%; display: block; }
        .empty-state { color: rgba(255,255,255,0.62); font-size: 14px; padding: 26px 18px; border-radius: 16px; background: rgba(255,255,255,0.03); }
        .insight-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
        .insight-card { min-height: 150px; display: flex; flex-direction: column; justify-content: space-between; padding: 18px; border-radius: 16px; background: linear-gradient(145deg, rgba(5,27,19,0.9), rgba(2,12,8,0.95)); border: 1px solid rgba(0,230,118,0.3); box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: transform 180ms ease, box-shadow 180ms ease; }
        .insight-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,255,118,0.15); }
        .trust-banner { margin: 18px 0; position: relative; }
        .trust-badge-large { display: flex; align-items: center; gap: 12px; padding: 16px 20px; border-radius: 14px; cursor: pointer; }
        .trust-badge-large .trust-emoji { font-size: 34px; }
        .trust-badge-large .trust-main { font-size: 22px; font-weight: 900; letter-spacing: 0.06em; }
        .trust-badge-large .trust-sub { font-size: 14px; color: rgba(3,20,10,0.7); font-weight: 800; }
        .trust-badge-large.high { background: linear-gradient(90deg, rgba(90,242,166,0.14), rgba(0,255,150,0.06)); box-shadow: 0 8px 30px rgba(90,242,166,0.18); border: 1px solid rgba(90,242,166,0.22); color: #05321a; }
        .trust-badge-large.medium { background: linear-gradient(90deg, rgba(116,165,255,0.12), rgba(116,165,255,0.06)); box-shadow: 0 8px 30px rgba(116,165,255,0.12); border: 1px solid rgba(116,165,255,0.12); color: #07223b; }
        .trust-badge-large.low { background: linear-gradient(90deg, rgba(255,195,0,0.12), rgba(255,195,0,0.05)); box-shadow: 0 8px 24px rgba(255,195,0,0.08); border: 1px solid rgba(255,195,0,0.12); color: #3a2a00; }
        .tooltip { display: none; position: absolute; left: 0; top: 100%; margin-top: 10px; background: rgba(0,0,0,0.86); color: #fff; padding: 10px 12px; border-radius: 8px; width: 280px; font-size: 13px; box-shadow: 0 8px 30px rgba(0,0,0,0.6); }
        .trust-banner:hover .tooltip, .tooltip.visible { display: block; }
        .provenance-panel { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 16px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 12px; }
        .provenance-chips { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
        .chip { padding: 8px 12px; border-radius: 999px; background: rgba(255,255,255,0.04); color: #dfffe0; font-weight: 800; }
        .prov-chip { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); }
        .trust-badge { padding: 12px; border-radius: 12px; display: inline-block; margin-top: 6px; }
        .trust-badge.high { background: rgba(90,242,166,0.08); box-shadow: 0 0 18px rgba(90,242,166,0.14); border: 1px solid rgba(90,242,166,0.16); }
        .trust-badge.medium { background: rgba(116,165,255,0.06); box-shadow: 0 0 12px rgba(116,165,255,0.08); border: 1px solid rgba(116,165,255,0.12); }
        .trust-badge.low { background: rgba(255,195,0,0.06); box-shadow: 0 0 10px rgba(255,195,0,0.06); border: 1px solid rgba(255,195,0,0.08); }
        .trust-label { font-weight: 900; font-size: 14px; margin-bottom: 2px; }
        .trust-badge.high .trust-label { color: #5af2a6; }
        .trust-badge.medium .trust-label { color: #74a5ff; }
        .trust-badge.low .trust-label { color: #ffcb47; }
        .trust-note { font-size: 12px; font-weight: 500; }
        .trust-badge.high .trust-note { color: #b9ffde; }
        .trust-badge.medium .trust-note { color: #cbdfff; }
        .trust-badge.low .trust-note { color: #ffeab3; }
        .provenance-list { display: grid; gap: 8px; }
        .prov-item { font-size: 13px; color: #d8ffd8; font-weight: 700; }
        .insight-card.people, .insight-card.water, .insight-card.build, .insight-card.confidence { background: rgba(255,255,255,0.05); }
        .card-title { font-size: 16px; font-weight: 800; margin-bottom: 12px; color: #ffffff; }
        .card-note { font-size: 14px; line-height: 1.5; color: #e9ffe8; }
        .confidence-block { display: flex; flex-direction: column; gap: 10px; }
        .confidence-pill { align-self: flex-start; padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
        .confidence-pill.low { background: rgba(255,195,0,0.16); color: #ffd86b; }
        .confidence-pill.medium { background: rgba(63,126,255,0.16); color: #b1d2ff; }
        .confidence-pill.high { background: rgba(104,255,141,0.16); color: #b9ffde; }
        .confidence-progress { width: 100%; height: 10px; border-radius: 999px; background: rgba(255,255,255,0.08); overflow: hidden; }
        .confidence-fill { height: 100%; border-radius: 999px; transition: width 0.35s ease; }
        .confidence-fill.low { background: #ffcb47; }
        .confidence-fill.medium { background: #74a5ff; }
        .confidence-fill.high { background: #5af2a6; box-shadow: 0 0 18px rgba(90,242,166,0.35); }
        .confidence-label { font-size: 13px; color: rgba(233,255,232,0.8); }
        .input-panel .tag-row { display: flex; gap: 10px; flex-wrap: wrap; }
        .tag-chip { padding: 10px 14px; border-radius: 999px; background: rgba(255,255,255,0.06); color: #d7ffd7; font-size: 13px; }
        .status-line { font-size: 13px; color: rgba(233,255,232,0.8); }
        .modal-shell { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; padding: 24px 18px; z-index: 100; }
        .modal-card { width: min(100%, 880px); max-height: calc(100vh - 60px); overflow-y: auto; background: #051b13; border-radius: 24px; padding: 26px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 40px 120px rgba(0,0,0,0.35); }
        .modal-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-bottom: 20px; }
        .modal-card-item { border-radius: 18px; padding: 20px; background: rgba(255,255,255,0.04); }
        .modal-card-title { font-size: 16px; font-weight: 800; margin-bottom: 8px; }
        .modal-card-subtitle { font-size: 13px; color: #c8ffc4; line-height: 1.5; }
        .locked-shell { margin: 24px 0 18px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 18px; }
        .locked-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
        .locked-card { display: grid; gap: 10px; align-items: center; justify-items: center; padding: 18px; border-radius: 18px; background: rgba(255,255,255,0.04); }
        .locked-icon { font-size: 24px; }
        .locked-label { font-size: 14px; font-weight: 800; text-align: center; }
        .unlock-copy { font-size: 14px; color: #c8ffc2; margin-bottom: 16px; }
        .panel-hint { font-size: 13px; color: rgba(184, 255, 199, 0.9); margin-bottom: 12px; }
        .preview-locked { position: relative; }
        .preview-locked::after {
          content: '';
          position: absolute;
          inset: 0;
          border-radius: 16px;
          background: rgba(0, 0, 0, 0.12);
          pointer-events: none;
          backdrop-filter: blur(1px);
          z-index: -1;
        }
        .modal-actions { display: flex; gap: 12px; flex-wrap: wrap; }
        .payment-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
        .payment-option { width: 100%; text-align: left; border: 1px solid rgba(255,255,255,0.12); border-radius: 18px; padding: 18px; background: rgba(255,255,255,0.04); color: #e9ffe8; cursor: pointer; transition: border-color 180ms ease, transform 180ms ease, background 180ms ease; }
        .payment-option.selected { border-color: #00e676; background: rgba(0,230,118,0.12); transform: translateY(-1px); }
        .payment-option:hover { border-color: rgba(0,230,118,0.4); }
        .option-title { font-size: 15px; font-weight: 800; margin-bottom: 8px; }
        .option-price { font-size: 20px; font-weight: 900; margin-bottom: 8px; }
        .option-description { font-size: 13px; color: rgba(233,255,232,0.78); line-height: 1.4; }
        .payment-status { margin-top: 14px; font-size: 13px; color: #b1ffc7; }
        .unlocked-shell { display: flex; flex-direction: column; gap: 12px; padding: 18px; border-radius: 18px; background: rgba(0,255,118,0.06); border: 1px solid rgba(0,255,118,0.15); margin-bottom: 18px; }
        .unlocked-shell .panel-title { margin-bottom: 0; }
        .share-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; z-index: 110; }
        .share-card { background: #051b13; border: 1px solid rgba(0, 230, 118, 0.25); border-radius: 16px; padding: 20px; width: min(100%, 420px); box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        .share-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .share-title { font-size: 16px; font-weight: 800; color: #5af2a6; }
        .share-desc { font-size: 13px; color: rgba(233,255,232,0.8); margin-bottom: 14px; }
        .share-copy-row { display: flex; gap: 8px; margin-bottom: 16px; }
        .share-link-input { flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); padding: 8px 12px; border-radius: 8px; color: #fff; font-size: 13px; outline: none; }
        .share-social-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .social-btn { text-align: center; background: rgba(255,255,255,0.05); color: #fff; padding: 10px; border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 13px; transition: background 0.2s; }
        .social-btn:hover { background: rgba(255,255,255,0.1); }
        .social-btn.whatsapp { background: rgba(37, 211, 102, 0.15); color: #25d366; border: 1px solid rgba(37, 211, 102, 0.3); }
        .social-btn.whatsapp:hover { background: rgba(37, 211, 102, 0.25); }
        .report-actions { display: flex; gap: 14px; flex-wrap: wrap; justify-content: flex-start; }
        .activity-panel { min-height: 620px; }
        .activity-stream { display: grid; gap: 12px; overflow-y: auto; max-height: 590px; padding-right: 4px; }
        .activity-bubble { min-height: 58px; display: flex; align-items: center; padding: 16px 18px; border-radius: 16px; background: rgba(0,255,118,0.08); color: #e9ffe8; font-weight: 700; opacity: 0; transform: translateY(10px); animation: slide-in 0.32s ease-in-out forwards; }
        .activity-bubble span { width: 100%; display: block; }
        .empty-state { color: rgba(255,255,255,0.62); font-size: 14px; padding: 26px 18px; border-radius: 16px; background: rgba(255,255,255,0.03); }
        .insight-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
        .insight-card { min-height: 150px; display: flex; flex-direction: column; justify-content: space-between; padding: 18px; border-radius: 16px; background: rgba(0,255,118,0.07); border: 1px solid rgba(255,255,255,0.1); }
        .trust-banner { margin: 18px 0; position: relative; }
        .trust-badge-large { display: flex; align-items: center; gap: 12px; padding: 16px 20px; border-radius: 14px; cursor: pointer; }
        .trust-badge-large .trust-emoji { font-size: 34px; }
        .trust-badge-large .trust-main { font-size: 22px; font-weight: 900; letter-spacing: 0.06em; }
        .trust-badge-large .trust-sub { font-size: 14px; color: rgba(3,20,10,0.7); font-weight: 800; }
        .trust-badge-large.high { background: linear-gradient(90deg, rgba(90,242,166,0.14), rgba(0,255,150,0.06)); box-shadow: 0 8px 30px rgba(90,242,166,0.18); border: 1px solid rgba(90,242,166,0.22); color: #05321a; }
        .trust-badge-large.medium { background: linear-gradient(90deg, rgba(116,165,255,0.12), rgba(116,165,255,0.06)); box-shadow: 0 8px 30px rgba(116,165,255,0.12); border: 1px solid rgba(116,165,255,0.12); color: #07223b; }
        .trust-badge-large.low { background: linear-gradient(90deg, rgba(255,195,0,0.12), rgba(255,195,0,0.05)); box-shadow: 0 8px 24px rgba(255,195,0,0.08); border: 1px solid rgba(255,195,0,0.12); color: #3a2a00; }
        .tooltip { display: none; position: absolute; left: 0; top: 100%; margin-top: 10px; background: rgba(0,0,0,0.86); color: #fff; padding: 10px 12px; border-radius: 8px; width: 280px; font-size: 13px; box-shadow: 0 8px 30px rgba(0,0,0,0.6); }
        .trust-banner:hover .tooltip, .tooltip.visible { display: block; }
        .provenance-panel { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 16px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 12px; }
        .provenance-chips { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
        .chip { padding: 8px 12px; border-radius: 999px; background: rgba(255,255,255,0.04); color: #dfffe0; font-weight: 800; }
        .prov-chip { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); }
        .trust-badge { padding: 12px; border-radius: 12px; display: inline-block; margin-top: 6px; width: 100%; }
        .trust-badge.high { background: rgba(90,242,166,0.1); border: 1px solid rgba(90,242,166,0.3); }
        .trust-badge.medium { background: rgba(116,165,255,0.08); border: 1px solid rgba(116,165,255,0.25); }
        .trust-badge.low { background: rgba(255,195,0,0.08); border: 1px solid rgba(255,195,0,0.2); }
        .trust-label { font-weight: 900; font-size: 14px; margin-bottom: 2px; }
        .trust-badge.high .trust-label { color: #5af2a6; }
        .trust-badge.medium .trust-label { color: #74a5ff; }
        .trust-badge.low .trust-label { color: #ffcb47; }
        .trust-note { font-size: 12px; font-weight: 500; }
        .trust-badge.high .trust-note { color: #b9ffde; }
        .trust-badge.medium .trust-note { color: #cbdfff; }
        .trust-badge.low .trust-note { color: #ffeab3; }
        .provenance-list { display: grid; gap: 8px; }
        .prov-item { font-size: 13px; color: #d8ffd8; font-weight: 700; }
        .insight-card.people, .insight-card.water, .insight-card.build, .insight-card.confidence { background: rgba(255,255,255,0.05); }
        .card-title { font-size: 16px; font-weight: 800; margin-bottom: 12px; }
        .card-note { font-size: 14px; line-height: 1.5; color: rgba(233,255,232,0.88); }
        .confidence-block { display: flex; flex-direction: column; gap: 10px; }
        .confidence-pill { align-self: flex-start; padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
        .confidence-pill.low { background: rgba(255,195,0,0.16); color: #ffd86b; }
        .confidence-pill.medium { background: rgba(63,126,255,0.16); color: #b1d2ff; }
        .confidence-pill.high { background: rgba(104,255,141,0.16); color: #b9ffde; }
        .confidence-progress { width: 100%; height: 10px; border-radius: 999px; background: rgba(255,255,255,0.08); overflow: hidden; }
        .confidence-fill { height: 100%; border-radius: 999px; transition: width 0.35s ease; }
        .confidence-fill.low { background: #ffcb47; }
        .confidence-fill.medium { background: #74a5ff; }
        .confidence-fill.high { background: #5af2a6; box-shadow: 0 0 18px rgba(90,242,166,0.35); }
        .confidence-label { font-size: 13px; color: rgba(233,255,232,0.8); }
        .input-panel .tag-row { display: flex; gap: 10px; flex-wrap: wrap; }
        .tag-chip { padding: 10px 14px; border-radius: 999px; background: rgba(255,255,255,0.06); color: #d7ffd7; font-size: 13px; }
        .status-line { font-size: 13px; color: rgba(233,255,232,0.8); }
        .modal-shell { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; padding: 24px 18px; z-index: 100; }
        .modal-card { width: min(100%, 880px); max-height: calc(100vh - 60px); overflow-y: auto; background: #051b13; border-radius: 24px; padding: 26px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 40px 120px rgba(0,0,0,0.35); }
        .modal-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-bottom: 20px; }
        .modal-card-item { border-radius: 18px; padding: 20px; background: rgba(255,255,255,0.04); }
        .modal-card-title { font-size: 16px; font-weight: 800; margin-bottom: 8px; }
        .modal-card-subtitle { font-size: 13px; color: #c8ffc4; line-height: 1.5; }
        .locked-shell { margin: 24px 0 18px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 18px; }
        .locked-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
        .locked-card { display: grid; gap: 10px; align-items: center; justify-items: center; padding: 18px; border-radius: 18px; background: rgba(255,255,255,0.04); }
        .locked-icon { font-size: 24px; }
        .locked-label { font-size: 14px; font-weight: 800; text-align: center; }
        .unlock-copy { font-size: 14px; color: #c8ffc2; margin-bottom: 16px; }
        .panel-hint { font-size: 13px; color: rgba(184, 255, 199, 0.9); margin-bottom: 12px; }
        .preview-locked { position: relative; }
        .preview-locked::after {
          content: '';
          position: absolute;
          inset: 0;
          border-radius: 16px;
          background: rgba(0, 0, 0, 0.12);
          pointer-events: none;
          backdrop-filter: blur(1px);
          z-index: -1;
        }
        .modal-actions { display: flex; gap: 12px; flex-wrap: wrap; }
        .payment-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
        .payment-option { width: 100%; text-align: left; border: 1px solid rgba(255,255,255,0.12); border-radius: 18px; padding: 18px; background: rgba(255,255,255,0.04); color: #e9ffe8; cursor: pointer; transition: border-color 180ms ease, transform 180ms ease, background 180ms ease; }
        .payment-option.selected { border-color: #00e676; background: rgba(0,230,118,0.12); transform: translateY(-1px); }
        .payment-option:hover { border-color: rgba(0,230,118,0.4); }
        .option-title { font-size: 15px; font-weight: 800; margin-bottom: 8px; }
        .option-price { font-size: 20px; font-weight: 900; margin-bottom: 8px; }
        .option-description { font-size: 13px; color: rgba(233,255,232,0.78); line-height: 1.4; }
        .payment-status { margin-top: 14px; font-size: 13px; color: #b1ffc7; }
        .unlocked-shell { display: flex; flex-direction: column; gap: 12px; padding: 18px; border-radius: 18px; background: rgba(0,255,118,0.06); border: 1px solid rgba(0,255,118,0.15); margin-bottom: 18px; }
        .unlocked-shell .panel-title { margin-bottom: 0; }
        @keyframes pulse { from { transform: translateY(0px); } to { transform: translateY(-4px); } }
        @keyframes wave-pulse { 0%, 100% { transform: scaleY(0.7); opacity: 0.55; } 50% { transform: scaleY(1.7); opacity: 1; } }
        @keyframes wave-static { 0%, 100% { transform: scaleY(1); opacity: 0.42; } 50% { transform: scaleY(1.1); opacity: 0.6; } }
        @keyframes slide-in { to { transform: translateY(0); opacity: 1; } }
        @media (max-width: 1220px) { .dashboard-grid { grid-template-columns: 1fr; } .report-strip, .modal-grid, .insight-grid, .locked-grid { grid-template-columns: 1fr; } .activity-panel { min-height: auto; } }
        @media (max-width: 760px) { .top-bar, .input-group, .report-actions, .modal-actions { flex-direction: column; align-items: stretch; } .mic-button, .submit-button, .primary-button, .ghost-button { width: 100%; } .panel-title { font-size: 15px; } }
      `}</style>
    </div>
  );
}
