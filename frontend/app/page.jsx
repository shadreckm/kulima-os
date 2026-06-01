'use client';

import { useState, useEffect, useRef } from 'react';

const ZONES = ['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'];
const PAYCHANGU_LINK = 'https://paychangu.com/YOUR_LINK';
const ACTIVITY_TERMS = ['farming', 'irrigation', 'milling', 'trading', 'welding', 'storage', 'market', 'transport'];
const RESOURCE_TERMS = ['water', 'energy', 'power', 'road', 'storage', 'market', 'transport'];

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

  const trustLabel = buildTrustLabel(summary);

  const insightCards = [
    { title: '🌱 People are farming', subtitle: `${zoneActivityCounts[zone] || 0} live signals` },
    { title: '⚠️ Water is missing', subtitle: summary?.infrastructure_gaps?.includes('Water') ? 'gap detected' : 'monitoring' },
    { title: '💡 Build irrigation', subtitle: summary?.recommended_projects?.[0] || 'ready' },
    { title: `✅ Confidence: ${trustLabel}`, subtitle: `${Math.round((summary?.trust_score ?? 0.55) * 100)}%` }
  ];

  const reportCards = reportData?.coordination_patterns?.slice(0, 3).map((item, index) => ({
    key: `report-${index}`,
    title: item.title || item.activity || `Insight ${index + 1}`,
    subtitle: item.summary || item.description || 'Data-driven finding'
  })) || [
    { key: 'preview-1', title: 'Farming pulse', subtitle: 'Repeat demand in crop zones' },
    { key: 'preview-2', title: 'Water gap', subtitle: 'Service shortfall detected' },
    { key: 'preview-3', title: 'Project ready', subtitle: 'Targeted irrigation build' }
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
          <button className="primary-button" onClick={() => window.open(PAYCHANGU_LINK, '_blank')}>Unlock</button>
        </div>
      </div>

      <div className="main-grid">
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

          <div className="swipe-card-shell">
            <div className="swipe-header">
              <div className="panel-title">Live insights</div>
              <div className="card-controls">
                <button onClick={() => setCardIndex((prev) => (prev + insightCards.length - 1) % insightCards.length)}>←</button>
                <button onClick={() => setCardIndex((prev) => (prev + 1) % insightCards.length)}>→</button>
              </div>
            </div>
            <div className="card-row">
              {insightCards.map((card, index) => (
                <div key={card.title} className={`insight-card ${index === cardIndex ? 'active' : ''}`} onClick={() => setCardIndex(index)}>
                  <div className="card-title">{card.title}</div>
                  <div className="card-note">{card.subtitle}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="activity-panel">
          <div className="panel-title">Live activity stream</div>
          <div className="activity-stream">
            {recentActivities.length ? recentActivities.slice(0, 10).map((activity) => (
              <div key={activity.id || activity.original_text} className="activity-bubble">
                <span>{activity.zone || zone} · {activity.activity?.toLowerCase() || activity.original_text?.slice(0, 24).toLowerCase()}</span>
              </div>
            )) : <div className="empty-state">No live activity yet. Add a signal.</div>}
          </div>
        </section>
      </div>

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
          <button className="primary-button" onClick={handleGenerateReport} disabled={reportLoading}>{reportLoading ? 'Generating…' : 'Open preview'}</button>
          {reportUrl && <button className="ghost-button" onClick={downloadReport}>Download PDF</button>}
        </div>
      </section>

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
                  <div className="modal-card-subtitle">{card.subtitle}</div>
                </div>
              ))}
            </div>
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
            <div className="modal-actions">
              <button className="primary-button" onClick={() => setShowUnlock(true)}>Unlock full report</button>
              {reportUrl && <button className="ghost-button" onClick={downloadReport}>Download preview</button>}
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
                <div className="modal-title">Full report access</div>
              </div>
              <button className="close-button" onClick={() => setShowUnlock(false)}>×</button>
            </div>
            <div className="unlock-copy">Full report sections are locked in preview mode. Unlock to access the complete analysis package.</div>
            <div className="modal-actions">
              <button className="primary-button" onClick={() => window.open(PAYCHANGU_LINK, '_blank')}>Open PayChangu</button>
              <button className="ghost-button" onClick={() => setShowUnlock(false)}>Close</button>
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
        .modal-shell { position: fixed; inset: 0; background: rgba(0,0,0,0.75); display: flex; justify-content: center; align-items: center; padding: 24px; z-index: 100; }
        .modal-card { width: min(100%, 840px); background: #041a12; border-radius: 32px; padding: 26px; border: 1px solid rgba(0,255,118,0.16); }
        .modal-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 20px; }
        .modal-title { font-size: 28px; font-weight: 800; }
        .close-button { border: none; background: rgba(255,255,255,0.08); color: #e9ffe8; font-size: 26px; width: 48px; height: 48px; border-radius: 999px; cursor: pointer; }
        .modal-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-bottom: 20px; }
        .modal-card-item { border-radius: 24px; padding: 20px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); }
        .modal-card-title { font-size: 16px; font-weight: 800; margin-bottom: 10px; }
        .modal-card-subtitle { font-size: 13px; color: #c8ffc4; }
        .locked-shell { margin-bottom: 20px; }
        .locked-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
        .locked-card { display: grid; gap: 12px; align-items: center; justify-items: center; padding: 20px; border-radius: 24px; background: rgba(255,255,255,0.04); border: 1px dashed rgba(255,255,255,0.12); }
        .locked-icon { font-size: 24px; }
        .locked-label { font-size: 14px; font-weight: 800; text-align: center; }
        .modal-actions { display: flex; gap: 12px; flex-wrap: wrap; }
        .unlock-copy { font-size: 14px; color: #c8ffc2; margin-bottom: 24px; }
        @keyframes pulse { from { transform: translateY(0px); } to { transform: translateY(-4px); } }
        @keyframes wave-pulse { 0%, 100% { transform: scaleY(0.7); opacity: 0.55; } 50% { transform: scaleY(1.7); opacity: 1; } }
        @keyframes wave-static { 0%, 100% { transform: scaleY(1); opacity: 0.42; } 50% { transform: scaleY(1.1); opacity: 0.6; } }
        @media (max-width: 1120px) { .main-grid { grid-template-columns: 1fr; } .card-row { grid-template-columns: 1fr 1fr; } .report-strip { grid-template-columns: 1fr; } .locked-grid { grid-template-columns: 1fr; } }
        @media (max-width: 760px) { .top-bar, .input-group, .report-actions { flex-direction: column; align-items: stretch; } .mic-button, .submit-button, .primary-button, .ghost-button { width: 100%; } }
      `}</style>
    </div>
  );
}
