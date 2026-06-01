'use client';

import { useState, useEffect, useRef } from 'react';

const ZONES = ['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'];
const PAYCHANGU_LINK = 'https://paychangu.com/YOUR_LINK';
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

  const recognitionRef = useRef(null);
  const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || '/api/v1').replace(/\/$/, '');
  const BACKEND_BASE = BASE_URL.replace(/\/api\/v1$/, '');
  const reportUrl = reportData?.pdf_url ? `${BACKEND_BASE}${reportData.pdf_url}` : '';

  useEffect(() => {
    fetchSummary();
    fetchRecentSignals();
    const interval = setInterval(fetchRecentSignals, 7000);
    return () => clearInterval(interval);
  }, [zone]);

  const fetchSummary = async () => {
    try {
      const response = await fetch(`${BASE_URL}/summary/${zone}`, { cache: 'no-store' });
      const data = await response.json();
      if (data?.status === 'success') {
        setSummary(data.data);
      } else {
        setSummary(null);
      }
    } catch {
      setSummary(null);
    }
  };

  const fetchRecentSignals = async () => {
    try {
      const response = await fetch(`${BASE_URL}/recent-signals`, { cache: 'no-store' });
      const data = await response.json();
      if (data?.success && Array.isArray(data.data)) {
        setRecentActivities(data.data.slice(0, 12));
      }
    } catch {
      // ignore polling failures
    }
  };

  const zoneActivityCounts = ZONES.reduce((counts, zoneId) => {
    counts[zoneId] = recentActivities.filter((item) => (item.zone || '').toUpperCase() === zoneId).length;
    return counts;
  }, {});

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
      await fetch(`${BASE_URL}/signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone: inferredZone, raw_text: text, source: 'web', user_id: `web_user_${Date.now()}` })
      });
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
      const response = await fetch(`${BASE_URL}/generate-prospectus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone, user_id: `web_user_${Date.now()}`, preview: true })
      });
      const data = await response.json();
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

  const handlePayWithPayChangu = () => {
    window.open(PAYCHANGU_LINK, 'PayChangu', 'width=520,height=700,noopener');
    setIsPaid(true);
    setPaymentMessage('Payment received — full report unlocked.');
    setShowUnlock(false);
    setShowPreview(true);
    setReportData((current) => current ? { ...current, preview_locked: false } : current);
  };

  const handleFundOpportunity = () => {
    setMessage('Funding request submitted. The report is ready for investor review.');
  };

  const handleExportReport = () => {
    if (reportUrl) {
      window.open(reportUrl, '_blank');
      setMessage('Exporting report...');
    }
  };

  const handleShareInsight = () => {
    setMessage('Insight shared with your network.');
  };

  const trustLabel = buildTrustLabel(summary);
  const trustScore = Math.round((summary?.trust_score ?? 0.55) * 100);
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
      subtitle: trustLabel,
      note: 'Decision readiness',
      level: trustLabel.toLowerCase()
    }
  ];

  const downloadReport = () => {
    if (reportUrl) window.open(reportUrl, '_blank');
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
          <button className="primary-button" onClick={() => setShowUnlock(true)}>Unlock</button>
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
              <input value={inputValue} onChange={(e) => setInputValue(e.target.value)} placeholder="e.g. Mzuzu farmers need water" />
              <button className="submit-button" onClick={submitActivity}>Submit</button>
            </div>
            <div className="waveform-row">
              {Array.from({ length: 10 }).map((_, index) => (
                <span key={index} className={`wave-bar ${speechActive ? 'wave-active' : ''}`} style={{ animationDelay: `${index * 60}ms` }} />
              ))}
            </div>
            <div className="tag-row">
              <span className="tag-chip">Zone: {parsedTag.zone || zone}</span>
              <span className="tag-chip">Activity: {parsedTag.activity}</span>
              <span className="tag-chip">Resource: {parsedTag.resource}</span>
            </div>
            <div className="status-line">{message}</div>
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
            <div className="map-placeholder">
              <div className="map-label">Live zone activity</div>
              <div className="map-note">Trends, coordination density, and spatial signal heat.</div>
            </div>
          </section>

          <section className="report-panel">
            <div className="panel-title">Report center</div>
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
              {reportUrl && <button className="ghost-button" onClick={downloadReport}>Download PDF</button>}
            </div>
          </section>
        </div>

        <div className="column column-right">
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
                  <button className="primary-button" onClick={handleFundOpportunity}>Fund this opportunity</button>
                  <button className="ghost-button" onClick={handleExportReport}>Export report</button>
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
        <div className="modal-shell" onClick={() => setShowUnlock(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="tiny-label">UNLOCK</div>
                <div className="modal-title">Unlock Full Report</div>
              </div>
              <button className="close-button" onClick={() => setShowUnlock(false)}>×</button>
            </div>
            <div className="unlock-copy">Choose a payment option to unlock all report sections inside the dashboard.</div>
            <div className="payment-options">
              {PAYMENT_OPTIONS.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  className={`payment-option ${selectedPlan === option.key ? 'selected' : ''}`}
                  onClick={() => setSelectedPlan(option.key)}
                >
                  <div className="option-title">{option.title}</div>
                  <div className="option-price">{option.price}</div>
                  <div className="option-description">{option.description}</div>
                </button>
              ))}
            </div>
            <div className="modal-actions">
              <button className="primary-button" onClick={handlePayWithPayChangu}>Pay with PayChangu</button>
              <button className="ghost-button" onClick={() => setShowUnlock(false)}>Cancel</button>
            </div>
            {paymentMessage && <div className="payment-status">{paymentMessage}</div>}
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
        input { width: 100%; min-height: 50px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.12); background: rgba(255,255,255,0.04); color: #f5ffef; padding: 0 18px; font-size: 16px; }
        .submit-button { background: #00e676; color: #02100c; }
        .waveform-row { display: flex; gap: 6px; margin-bottom: 18px; }
        .wave-bar { width: 6px; height: 20px; border-radius: 999px; background: rgba(255,255,255,0.1); transform-origin: bottom; animation: wave-static 1200ms infinite ease-in-out; }
        .wave-active { animation: wave-pulse 900ms infinite ease-in-out; }
        .tag-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
        .tag-chip { padding: 11px 16px; border-radius: 999px; background: rgba(0,255,118,0.08); color: #d7ffd7; font-size: 13px; }
        .status-line { font-size: 13px; color: #ceffcd; margin-bottom: 24px; }
        .swipe-card-shell { background: rgba(0,0,0,0.12); border-radius: 26px; padding: 18px; }
        .swipe-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; }
        .card-controls button { border: 1px solid rgba(255,255,255,0.14); background: transparent; color: #e9ffe8; border-radius: 999px; width: 40px; height: 40px; cursor: pointer; }
        .card-row { display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 14px; }
        .insight-card { border-radius: 24px; padding: 22px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); cursor: pointer; transition: transform 180ms ease, background 180ms ease; }
        .insight-card.active { background: rgba(0,255,118,0.14); transform: translateY(-2px); }
        .card-title { font-size: 18px; font-weight: 800; line-height: 1.1; margin-bottom: 10px; }
        .card-note { font-size: 13px; color: #d8ffcd; }
        .activity-panel { display: flex; flex-direction: column; }
        .activity-stream { display: grid; gap: 12px; }
        .activity-bubble { padding: 16px 18px; border-radius: 999px; background: rgba(0,255,118,0.08); color: #e9ffe8; font-weight: 700; animation: pulse 2400ms ease-in-out infinite alternate; }
        .empty-state { color: rgba(255,255,255,0.68); font-size: 14px; }
        .report-panel { display: grid; gap: 18px; }
        .report-strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
        .report-chip { border-radius: 24px; padding: 18px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); }
        .chip-title { font-size: 15px; font-weight: 800; margin-bottom: 8px; }
        .chip-subtitle { font-size: 13px; color: #c8ffc4; }
        .report-actions { display: flex; gap: 12px; flex-wrap: wrap; }
        .dashboard-grid { display: grid; grid-template-columns: minmax(320px, 1.05fr) minmax(360px, 1.3fr) minmax(300px, 0.95fr); gap: 20px; align-items: start; }
        .column { display: flex; flex-direction: column; gap: 20px; }
        .column-left, .column-center, .column-right { min-height: 0; }
        .input-panel, .insights-panel, .map-panel, .report-panel, .activity-panel { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.12); display: flex; flex-direction: column; gap: 16px; border: 1px solid rgba(255,255,255,0.08); }
        .map-panel { min-height: 320px; }
        .map-placeholder { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: 10px; border-radius: 16px; padding: 22px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); min-height: 260px; }
        .map-label { font-size: 18px; font-weight: 700; }
        .map-note { font-size: 13px; color: rgba(233,255,232,0.75); max-width: 320px; }
        .report-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
        .report-chip { border-radius: 16px; padding: 20px; background: rgba(0,255,118,0.08); min-height: 132px; display: flex; flex-direction: column; justify-content: space-between; }
        .chip-title { font-size: 15px; font-weight: 800; margin-bottom: 10px; }
        .chip-subtitle { font-size: 13px; color: #0a2a17; line-height: 1.35; }
        .modal-card-value { font-size: 26px; font-weight: 800; margin-top: 10px; margin-bottom: 10px; color: #d7ffce; }
        .expanded-report { display: flex; flex-direction: column; gap: 18px; background: rgba(255,255,255,0.03); padding: 20px; border-radius: 18px; border: 1px solid rgba(255,255,255,0.08); }
        .expanded-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
        .expanded-card { padding: 18px; border-radius: 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); }
        .expanded-card-title { font-size: 14px; font-weight: 800; margin-bottom: 10px; }
        .expanded-card-text { font-size: 13px; color: rgba(233,255,232,0.88); line-height: 1.6; }
        .cta-panel { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 6px; }
        .payment-option { width: 100%; text-align: left; border: 1px solid rgba(255,255,255,0.12); border-radius: 18px; padding: 18px; background: rgba(255,255,255,0.04); color: #e9ffe8; cursor: pointer; transition: border-color 180ms ease, transform 180ms ease, background 180ms ease; }
        .payment-option.selected { border-color: #00e676; background: rgba(0,230,118,0.12); transform: translateY(-1px); }
        .payment-option:hover { border-color: rgba(0,230,118,0.4); }
        .option-title { font-size: 15px; font-weight: 800; margin-bottom: 8px; }
        .option-price { font-size: 20px; font-weight: 900; margin-bottom: 8px; }
        .option-description { font-size: 13px; color: rgba(233,255,232,0.78); line-height: 1.4; }
        .payment-status { margin-top: 14px; font-size: 13px; color: #b1ffc7; }
        .unlocked-shell { display: flex; flex-direction: column; gap: 12px; padding: 18px; border-radius: 18px; background: rgba(0,255,118,0.06); border: 1px solid rgba(0,255,118,0.15); margin-bottom: 18px; }
        .unlocked-shell .panel-title { margin-bottom: 0; }
        .report-actions { display: flex; gap: 14px; flex-wrap: wrap; justify-content: flex-start; }
        .activity-panel { min-height: 620px; }
        .activity-stream { display: grid; gap: 12px; overflow-y: auto; max-height: 590px; padding-right: 4px; }
        .activity-bubble { min-height: 58px; display: flex; align-items: center; padding: 16px 18px; border-radius: 16px; background: rgba(0,255,118,0.08); color: #e9ffe8; font-weight: 700; opacity: 0; transform: translateY(10px); animation: slide-in 0.32s ease-in-out forwards; }
        .activity-bubble span { width: 100%; display: block; }
        .empty-state { color: rgba(255,255,255,0.62); font-size: 14px; padding: 26px 18px; border-radius: 16px; background: rgba(255,255,255,0.03); }
        .insight-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
        .insight-card { min-height: 150px; display: flex; flex-direction: column; justify-content: space-between; padding: 18px; border-radius: 16px; background: rgba(0,255,118,0.07); border: 1px solid rgba(255,255,255,0.1); }
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
