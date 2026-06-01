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

const getBadgeClass = (level) => {
  if (level === 'HIGH') return 'badge-glow badge-high';
  if (level === 'MEDIUM') return 'badge-glow badge-medium';
  return 'badge-glow badge-low';
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
  const [bubbles, setBubbles] = useState([]);
  const [speechActive, setSpeechActive] = useState(false);
  const [recordedPhrase, setRecordedPhrase] = useState('');
  const [parsedTag, setParsedTag] = useState({ zone: null, activity: 'Farming', resource: 'Water' });
  const [cardIndex, setCardIndex] = useState(0);

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

  useEffect(() => {
    if (!recordedPhrase) return;
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setBubbles((current) => [...current, { id, text: recordedPhrase, zone: parsedTag.zone || zone }]);
    const timeout = setTimeout(() => setBubbles((current) => current.filter((bubble) => bubble.id !== id)), 7000);
    return () => clearTimeout(timeout);
  }, [recordedPhrase, parsedTag.zone, zone]);

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
        setRecentActivities(data.data);
      }
    } catch {
      // ignore polling failures
    }
  };

  const zoneActivityCounts = ZONES.reduce((counts, zoneId) => {
    counts[zoneId] = recentActivities.filter((item) => (item.zone || '').toUpperCase() === zoneId).length;
    return counts;
  }, {});

  const trustLabel = buildTrustLabel(summary);

  const startVoiceCapture = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMessage('Voice input is not supported in this browser. Use the fallback field.');
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    recognitionRef.current = recognition;

    recognition.onstart = () => {
      setSpeechActive(true);
      setMessage('Listening for your activity phrase...');
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
      setMessage('Activity captured. Submit to register it.');
    };
    recognition.onerror = () => {
      setSpeechActive(false);
      setMessage('Voice capture failed. Please try again or type the activity.');
    };
    recognition.onend = () => setSpeechActive(false);
    recognition.start();
  };

  const submitActivity = async () => {
    if (!inputValue.trim()) {
      setMessage('Please enter or speak an activity before submitting.');
      return;
    }
    const inferredZone = parsedTag.zone || zone;
    setMessage('Saving your activity to the platform...');
    try {
      const response = await fetch(`${BASE_URL}/signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone: inferredZone,
          raw_text: inputValue.trim(),
          source: 'web',
          user_id: `web_user_${Date.now()}`
        })
      });
      const data = await response.json();
      if (data?.status === 'success') {
        setMessage('Activity recorded. Refreshing live insights.');
        setInputValue('');
        setRecordedPhrase('');
        fetchSummary();
        fetchRecentSignals();
      } else {
        setMessage(data?.message || 'Unable to record activity.');
      }
    } catch {
      setMessage('Failed to save activity. Check your connection.');
    }
  };

  const handleGenerateReport = async () => {
    if (!summary || summary.signal_count === 0) {
      setMessage('Record more activities before generating a report.');
      return;
    }
    setReportLoading(true);
    setMessage('Generating a preview report...');
    try {
      const response = await fetch(`${BASE_URL}/generate-prospectus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone, user_id: `web_user_${Date.now()}`, preview: true })
      });
      const data = await response.json();
      if (data?.success) {
        setReportData(data.report || { pdf_url: data.pdf_url, preview_locked: true, coordination_patterns: data.report?.coordination_patterns || [] });
        setShowPreview(true);
        setMessage('Preview ready. Unlock the full report for details.');
      } else {
        setMessage(data?.message || 'Preview generation failed.');
      }
    } catch {
      setMessage('Unable to generate report. Please try again later.');
    } finally {
      setReportLoading(false);
    }
  };

  const previewCards = () => {
    const items = reportData?.coordination_patterns || summary?.coordination_patterns || [];
    if (items.length) {
      return items.slice(0, 3).map((item, index) => ({
        key: `${item.title || index}`,
        title: item.title || item.activity || 'Signal',
        text: item.summary || item.description || 'Repeat demand detected',
        confidence: item.confidence || item.score || 'medium'
      }));
    }
    return [
      { key: 'one', title: 'Farming pulse', text: 'Strong repeat demand from local farmers.', confidence: 'medium' },
      { key: 'two', title: 'Water gap', text: 'Services trail demand in key zones.', confidence: 'high' },
      { key: 'three', title: 'Project ready', text: 'Actionable infrastructure cluster identified.', confidence: 'medium' }
    ];
  };

  const activeZoneCount = zoneActivityCounts[zone] || 0;

  return (
    <div style={{ minHeight: '100vh', padding: 20, background: 'radial-gradient(circle at top left, rgba(0,230,118,0.18), transparent 18%), radial-gradient(circle at bottom right, rgba(0,255,181,0.08), transparent 22%), linear-gradient(180deg, #03120d 0%, #02100c 100%)', color: '#eeffdf' }}>
      <div style={{ maxWidth: 1280, margin: '0 auto', display: 'grid', gap: 22 }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ fontSize: 12, letterSpacing: '0.28em', color: '#8ef4b8', textTransform: 'uppercase' }}>Command interface</div>
            <h1 style={{ margin: '8px 0 0', fontSize: 44, lineHeight: 1.05 }}>Kulima OS mission control</h1>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button onClick={handleGenerateReport} disabled={reportLoading} style={{ padding: '16px 24px', borderRadius: 20, border: 'none', background: '#00e676', color: '#042c18', fontWeight: 800, cursor: reportLoading ? 'not-allowed' : 'pointer' }}>{reportLoading ? 'Creating…' : 'Preview report'}</button>
            <button onClick={() => window.open(PAYCHANGU_LINK, '_blank')} style={{ padding: '16px 24px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.16)', background: 'rgba(255,255,255,0.06)', color: '#e9ffe8', fontWeight: 700 }}>Unlock report</button>
          </div>
        </header>

        <section style={{ display: 'grid', gap: 20, background: 'rgba(255,255,255,0.04)', borderRadius: 30, padding: 28, border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'grid', gap: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 12, letterSpacing: '0.24em', textTransform: 'uppercase', color: '#9dfab3' }}>Zone command</div>
                <div style={{ fontSize: 24, fontWeight: 700 }}>Live map focus: {zone}</div>
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <span style={{ padding: '12px 18px', borderRadius: 999, border: '1px solid rgba(0,255,118,0.24)', background: 'rgba(0,255,118,0.12)', color: '#e9ffe8', fontSize: 12 }}>{trustLabel} confidence</span>
                <span style={{ padding: '12px 18px', borderRadius: 999, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.06)', color: '#e9ffe8', fontSize: 12 }}>Active inputs {recentActivities.length}</span>
              </div>
            </div>

            <div style={{ display: 'grid', gap: 20, gridTemplateColumns: '1.1fr 0.9fr', minHeight: 360 }}>
              <div style={{ display: 'grid', gap: 18 }}>
                <div style={{ display: 'grid', gap: 14 }}>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                    {ZONES.map((zoneId) => {
                      const count = zoneActivityCounts[zoneId] || 0;
                      const alpha = Math.min(0.3, 0.08 + count * 0.04);
                      return (
                        <button
                          key={zoneId}
                          onClick={() => setZone(zoneId)}
                          style={{
                            padding: '14px 18px',
                            borderRadius: 999,
                            border: zone === zoneId ? '1px solid rgba(0,255,118,0.7)' : '1px solid rgba(255,255,255,0.12)',
                            background: `rgba(0,255,118,${alpha})`,
                            color: '#eeffdf',
                            fontWeight: zone === zoneId ? 700 : 500,
                            cursor: 'pointer'
                          }}
                        >
                          {zoneId}
                        </button>
                      );
                    })}
                  </div>

                  <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 28, padding: 20, border: '1px solid rgba(255,255,255,0.12)', minHeight: 240, display: 'grid', gap: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontSize: 12, color: '#bdfccf', textTransform: 'uppercase', letterSpacing: '0.16em' }}>Map-first command view</div>
                        <div style={{ fontSize: 18, fontWeight: 700 }}>Rapid situational awareness</div>
                      </div>
                      <div style={{ fontSize: 12, color: '#cff8d3' }}>{activeZoneCount} local signals</div>
                    </div>
                    <div style={{ flex: 1, background: 'radial-gradient(circle at 20% 25%, rgba(0,255,118,0.16), transparent 22%), radial-gradient(circle at 75% 30%, rgba(0,255,118,0.08), transparent 18%), linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0))', borderRadius: 24, display: 'grid', placeItems: 'center', color: '#d8ffe1', fontSize: 14, textAlign: 'center', padding: 18 }}>
                      Map visualization placeholder
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gap: 18 }}>
                <div style={{ display: 'grid', gap: 14, padding: 22, borderRadius: 28, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
                    <div>
                      <div style={{ fontSize: 12, color: '#bdfccf', textTransform: 'uppercase', letterSpacing: '0.16em' }}>Voice-first capture</div>
                      <div style={{ fontSize: 18, fontWeight: 700 }}>Speak activity into the system</div>
                    </div>
                    <button onClick={startVoiceCapture} style={{ padding: '14px 18px', borderRadius: 18, border: '1px solid rgba(255,255,255,0.16)', background: speechActive ? 'rgba(0,230,118,0.24)' : 'rgba(255,255,255,0.08)', color: '#eeffdf', cursor: 'pointer' }}>{speechActive ? 'Listening…' : 'Start voice'}</button>
                  </div>
                  <div style={{ display: 'grid', gap: 10 }}>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      <span style={{ padding: '9px 13px', borderRadius: 999, background: 'rgba(0,255,118,0.12)', color: '#e7ffe5', fontSize: 12 }}>Zone: {parsedTag.zone || zone}</span>
                      <span style={{ padding: '9px 13px', borderRadius: 999, background: 'rgba(0,255,118,0.08)', color: '#e7ffe5', fontSize: 12 }}>Activity: {parsedTag.activity}</span>
                      <span style={{ padding: '9px 13px', borderRadius: 999, background: 'rgba(0,255,118,0.08)', color: '#e7ffe5', fontSize: 12 }}>Resource: {parsedTag.resource}</span>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 18, padding: 18, color: '#deffdb', minHeight: 110, display: 'grid', gap: 10 }}>
                      <div style={{ fontSize: 14, fontWeight: 700 }}>Voice preview</div>
                      <div style={{ fontSize: 13, lineHeight: 1.7 }}>{recordedPhrase || 'Speak a sentence describing current activity or use the fallback input below.'}</div>
                    </div>
                    <div style={{ display: 'grid', gap: 10 }}>
                      <input value={inputValue} onChange={(e) => setInputValue(e.target.value)} placeholder="Fallback input: describe activity" style={{ width: '100%', height: 50, borderRadius: 16, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.06)', color: '#f0ffec', padding: '0 16px' }} />
                      <button onClick={submitActivity} style={{ padding: '14px 20px', borderRadius: 18, border: 'none', background: '#00e676', color: '#042c18', fontWeight: 700, cursor: 'pointer' }}>Submit activity</button>
                    </div>
                  </div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: 28, padding: 22, border: '1px solid rgba(255,255,255,0.12)' }}>
                  <div style={{ fontSize: 12, letterSpacing: '0.24em', textTransform: 'uppercase', color: '#9bfab8' }}>Live feed</div>
                  <div style={{ marginTop: 12, display: 'grid', gap: 12, minHeight: 180 }}>
                    {recentActivities.slice(0, 5).map((activity, index) => (
                      <div key={index} style={{ padding: 16, borderRadius: 20, background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.1)' }}>
                        <div style={{ fontSize: 13, fontWeight: 700, color: '#d8ffda' }}>{activity.zone || 'Zone'} · {activity.original_text?.slice(0, 34) || activity.raw_text?.slice(0, 34) || 'activity'}</div>
                      </div>
                    ))}
                    {!recentActivities.length && <div style={{ color: '#c8ffc4', fontSize: 13 }}>No recent live activity yet. Submit an activity to see the feed.</div>}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section style={{ display: 'grid', gap: 18, background: 'rgba(255,255,255,0.04)', borderRadius: 30, padding: 28, border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 12, letterSpacing: '0.24em', textTransform: 'uppercase', color: '#9dfab3' }}>Impact cards</div>
                <div style={{ fontSize: 24, fontWeight: 700 }}>What matters now</div>
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <span style={{ padding: '12px 18px', borderRadius: 999, border: '1px solid rgba(0,255,118,0.24)', background: 'rgba(0,255,118,0.12)', color: '#e9ffe8', fontSize: 12 }}>Pulse {recentActivities.length}</span>
                <span style={{ padding: '12px 18px', borderRadius: 999, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.06)', color: '#e9ffe8', fontSize: 12 }}>{trustLabel} trust</span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 16, overflowX: 'auto', paddingBottom: 8 }}>
              {[
                { icon: '🌱', title: 'Farming surge', subtitle: `${activeZoneCount} demand inputs` },
                { icon: '⚠️', title: 'Service gap', subtitle: `${summary?.infrastructure_gaps?.length ?? 1} missing services` },
                { icon: '💡', title: 'Project ready', subtitle: `${summary?.recommended_projects?.[0] || 'More input needed'}` },
                { icon: '✅', title: 'Trusted signal', subtitle: `${trustLabel} consensus` }
              ].map((card, idx) => (
                <div key={idx} style={{ minWidth: 240, borderRadius: 26, padding: 22, background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)' }}>
                  <div style={{ fontSize: 24 }}>{card.icon}</div>
                  <div style={{ fontSize: 18, fontWeight: 700, marginTop: 12 }}>{card.title}</div>
                  <div style={{ marginTop: 8, fontSize: 13, color: '#c8ffc4' }}>{card.subtitle}</div>
                </div>
              ))}
            </div>
          </section>

          <section style={{ display: 'grid', gap: 18, background: 'rgba(255,255,255,0.05)', borderRadius: 30, padding: 28, border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <div style={{ fontSize: 12, letterSpacing: '0.24em', textTransform: 'uppercase', color: '#9dfab3' }}>Demand radar</div>
                <div style={{ fontSize: 24, fontWeight: 700 }}>Infrastructure gap scan</div>
              </div>
              <span style={{ color: '#c8ffc4', fontSize: 13 }}>Tap any gap to highlight it.</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 0.9fr', gap: 22, alignItems: 'center' }}>
              <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 28, padding: 20, border: '1px solid rgba(255,255,255,0.12)' }}>
                <svg viewBox="0 0 240 240" style={{ width: '100%', height: '100%' }}>
                  {[0, 1, 2, 3].map((layer) => (
                    <circle key={layer} cx="120" cy="120" r={100 - layer * 22} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
                  ))}
                  {['Power', 'Water', 'Market'].map((label, index) => {
                    const values = [0.78, 0.62, 0.44];
                    const angle = -20 + index * 120;
                    const x = 120 + Math.cos((angle * Math.PI) / 180) * values[index] * 86;
                    const y = 120 + Math.sin((angle * Math.PI) / 180) * values[index] * 86;
                    return (
                      <g key={label}>
                        <line x1="120" y1="120" x2={x} y2={y} stroke="#00e676" strokeWidth="2" />
                        <circle cx={x} cy={y} r="12" fill="#00e676" />
                        <text x={x} y={y + 28} fill="#d5ffd8" fontSize="10" textAnchor="middle">{label}</text>
                      </g>
                    );
                  })}
                </svg>
              </div>
              <div style={{ display: 'grid', gap: 14 }}>
                {['Power', 'Water', 'Market'].map((label, index) => {
                  const values = [78, 62, 44];
                  return (
                    <button key={label} onClick={() => setMessage(`${label} gap in ${zone} is being monitored.`)} style={{ padding: '16px 18px', borderRadius: 20, border: '1px solid rgba(0,255,118,0.12)', background: 'rgba(255,255,255,0.04)', color: '#e8ffea', textAlign: 'left', cursor: 'pointer' }}>
                      <div style={{ fontSize: 12, color: '#aef6b6' }}>{label}</div>
                      <div style={{ fontSize: 18, fontWeight: 700 }}>{values[index]}%</div>
                    </button>
                  );
                })}
              </div>
            </div>
          </section>
        </section>

        {showPreview && (
          <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.56)', zIndex: 60, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 24 }}>
            <div style={{ width: 'min(100%, 980px)', maxHeight: '90vh', overflowY: 'auto', background: '#02120c', borderRadius: 28, padding: 28, border: '1px solid rgba(0,255,118,0.12)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: 12, letterSpacing: '0.24em', textTransform: 'uppercase', color: '#9dfab8' }}>Preview report</div>
                  <div style={{ fontSize: 28, fontWeight: 800, color: '#e9ffe8' }}>Partial prospectus</div>
                </div>
                <button onClick={() => setShowPreview(false)} style={{ padding: '12px 18px', borderRadius: 18, border: '1px solid rgba(255,255,255,0.16)', background: 'rgba(255,255,255,0.06)', color: '#e9ffe8' }}>Close</button>
              </div>

              <div style={{ display: 'grid', gap: 18, marginTop: 22 }}>
                {previewCards().map((card) => (
                  <div key={card.key} style={{ background: 'rgba(255,255,255,0.05)', borderRadius: 24, padding: 20, border: '1px solid rgba(255,255,255,0.08)' }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#e9ffe8' }}>{card.title}</div>
                    <div style={{ marginTop: 10, fontSize: 13, color: '#c8ffcd' }}>{card.text}</div>
                    <div style={{ marginTop: 12, fontSize: 12, color: '#9bfab8' }}>Confidence {card.confidence}</div>
                  </div>
                ))}

                <div style={{ display: 'grid', gap: 12 }}>
                  {['Detailed analysis 🔒', 'Financial projections 🔒', 'Infrastructure blueprint 🔒'].map((label) => (
                    <div key={label} style={{ position: 'relative', borderRadius: 24, padding: 24, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
                      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(255,255,255,0.04), transparent)', borderRadius: 24 }} />
                      <div style={{ position: 'relative', zIndex: 1, opacity: 0.7, fontSize: 15, fontWeight: 700 }}>{label}</div>
                      <div style={{ position: 'relative', zIndex: 1, marginTop: 10, fontSize: 13, color: '#b8ffc4' }}>Unlock this content to see the full prospectus insights and local strategy map.</div>
                    </div>
                  ))}
                </div>

                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <button onClick={() => setShowUnlock(true)} style={{ padding: '16px 22px', borderRadius: 20, border: 'none', background: '#00e676', color: '#02100c', fontWeight: 800 }}>Unlock full report</button>
                  {reportUrl && <button onClick={() => window.open(reportUrl, '_blank')} style={{ padding: '16px 22px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.16)', background: 'rgba(255,255,255,0.06)', color: '#e9ffe8' }}>Download preview</button>}
                </div>
              </div>
            </div>
          </div>
        )}

        {showUnlock && (
          <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.64)', zIndex: 70, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 24 }}>
            <div style={{ width: 'min(100%, 640px)', background: '#02120c', borderRadius: 28, padding: 28, border: '1px solid rgba(0,255,118,0.14)' }}>
              <div style={{ display: 'grid', gap: 18 }}>
                <div>
                  <div style={{ fontSize: 12, letterSpacing: '0.24em', textTransform: 'uppercase', color: '#9dfab8' }}>Unlock</div>
                  <div style={{ fontSize: 28, fontWeight: 800, color: '#e9ffe8' }}>Full report access</div>
                </div>
                <div style={{ padding: 20, borderRadius: 24, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#e9ffe8' }}>Advanced sections are locked in preview mode.</div>
                  <div style={{ marginTop: 10, fontSize: 13, color: '#b8ffc0' }}>Unlock the complete prospectus and download the full PDF report with infrastructure guidance.</div>
                </div>
                <button onClick={() => window.open(PAYCHANGU_LINK, '_blank')} style={{ padding: '16px 22px', borderRadius: 20, border: 'none', background: '#00e676', color: '#02100c', fontWeight: 800 }}>Open PayChangu to unlock</button>
                <button onClick={() => setShowUnlock(false)} style={{ padding: '14px 18px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.16)', background: 'rgba(255,255,255,0.06)', color: '#e9ffe8' }}>Close</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
