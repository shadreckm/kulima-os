'use client';

import { useState, useEffect, useRef } from 'react';

// Production mode: remove demo/sample fallbacks
const PUBLIC_LOGO = '/logo.png';

const ACTIVITY_EXAMPLES = ['Irrigation', 'Trading', 'Regenerative Farming', 'Transport', 'Storage', 'Food Processing'];
const ZONES = ['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'];
const WHATSAPP_NUMBER = '+1 415 523 8886';
const WHATSAPP_JOIN_CODE = 'join%20week-saved';
const WHATSAPP_ONBOARDING_LINK = `https://wa.me/14155238886?text=${WHATSAPP_JOIN_CODE}`;
const WHATSAPP_QR_IMAGE = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(WHATSAPP_ONBOARDING_LINK)}`;

// Button styles for consistent CTAs
const BUTTON_PRIMARY = {
  padding: '12px 16px',
  borderRadius: 10,
  backgroundColor: '#2d6a4f',
  color: '#fff',
  border: 'none',
  fontWeight: 700,
  cursor: 'pointer'
};
const BUTTON_SECONDARY = {
  padding: '12px 16px',
  borderRadius: 10,
  backgroundColor: '#fff',
  border: '1px solid #d4e0d9',
  color: '#2d6a4f',
  fontWeight: 700,
  cursor: 'pointer'
};

export default function Home() {
  const [zone, setZone] = useState('MZUZU');
  const [inputValue, setInputValue] = useState('');
  const [summary, setSummary] = useState(null);
  const [recentSignals, setRecentSignals] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const [shareMessage, setShareMessage] = useState('');
  const inputRef = useRef(null);
  const insightsRef = useRef(null);
  const liveScrollRef = useRef(null);
  const analysisTimeoutsRef = useRef([]);
  const signalPollRef = useRef(null);
  const prevSignalIdsRef = useRef(new Set());
  const [flashIds, setFlashIds] = useState([]);
  const [nextSuggestion, setNextSuggestion] = useState('');
  const [toastMessage, setToastMessage] = useState('');
  const [analysisStage, setAnalysisStage] = useState('');
  const [insightExpanded, setInsightExpanded] = useState(false);

  const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || '/api/v1').replace(/\/$/, '');
  const BACKEND_BASE = BASE_URL.replace(/\/api\/v1$/, '');
  // Production behavior: rely on backend summary only
  const reportUrl = reportData?.pdf_url ? `${BACKEND_BASE}${reportData.pdf_url}` : '';

  useEffect(() => {
    fetchSummary();
  }, [zone]);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BASE_URL}/summary/${zone}`, { cache: 'no-store' });
      const data = await response.json();
      if (data.status === 'success') {
        setSummary(data.data);
      } else {
        setSummary(null);
        setMessage('Patterns are forming. Continue recording activity to unlock insights.');
      }
    } catch (error) {
      setSummary(null);
      setMessage('Unable to fetch summary. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const parseZoneFromText = (text) => {
    const normalized = text.toLowerCase();
    if (/mzuzu/.test(normalized)) return 'MZUZU';
    if (/lilongwe/.test(normalized)) return 'LILONGWE';
    if (/blantyre/.test(normalized)) return 'BLANTYRE';
    if (/zomba/.test(normalized)) return 'ZOMBA';
    return null;
  };

  const fetchRecentSignals = async (isFirstLoad = false) => {
    if (isFirstLoad) {
      setLiveLoading(true);
    }
    try {
      const response = await fetch(`${BASE_URL}/recent-signals`, { cache: 'no-store' });
      const data = await response.json();
      if (data.status === 'success' && Array.isArray(data.data)) {
        const fetched = data.data.slice(0, 15);
        const fetchedIds = fetched.map((s, i) => s.id || s.timestamp || `${s.activity || s.activity_type}-${s.zone || s.zone_name || s.location}-${i}`);
        const newIds = fetchedIds.filter(id => !prevSignalIdsRef.current.has(id));
        if (newIds.length > 0) {
          setFlashIds(prev => [...prev, ...newIds]);
          // show concise toast for the first new signal
          const firstNew = fetched[newIds.indexOf(newIds[0])] || fetched[0];
          const signalZone = firstNew?.zone || firstNew?.zone_name || firstNew?.location || zone;
          setToastMessage(`New activity recorded in ${signalZone}`);
          setTimeout(() => setToastMessage(''), 2500);
          // remove flash after 3.5s
          setTimeout(() => setFlashIds(prev => prev.filter(x => !newIds.includes(x))), 3500);
        }
        prevSignalIdsRef.current = new Set(fetchedIds);
        setRecentSignals(fetched);
      }
    } catch (error) {
      // keep existing live feed if polling fails
    } finally {
      if (isFirstLoad) {
        setLiveLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchRecentSignals(true);
    signalPollRef.current = setInterval(() => fetchRecentSignals(false), 5000);
    return () => clearInterval(signalPollRef.current);
  }, []);

  // Loading safety guards to prevent infinite cooking states
  useEffect(() => {
    let timeoutId;
    if (loading) {
      timeoutId = setTimeout(() => {
        setLoading(false);
        setMessage('Request timed out. Please try again.');
      }, 15000);
    }
    return () => clearTimeout(timeoutId);
  }, [loading]);

  useEffect(() => {
    let timeoutId;
    if (reportLoading) {
      timeoutId = setTimeout(() => {
        setReportLoading(false);
        setMessage('Report generation timed out. Please try again.');
      }, 15000);
    }
    return () => clearTimeout(timeoutId);
  }, [reportLoading]);

  useEffect(() => {
    if (liveScrollRef.current) {
      liveScrollRef.current.scrollTop = 0;
    }
  }, [recentSignals]);

  // Production: send raw text to backend and rely on backend normalization

  const handleSubmitActivity = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) {
      setMessage('Please describe an activity.');
      return;
    }

    const inferredZone = parseZoneFromText(inputValue) || zone;
    if (inferredZone !== zone) {
      setZone(inferredZone);
    }

    setLoading(true);
    setMessage('Submitting activity...');

    // Micro-feedback stages
    setAnalysisStage('Analyzing activity...');
    analysisTimeoutsRef.current.push(setTimeout(() => setAnalysisStage('Detecting patterns...'), 700));
    analysisTimeoutsRef.current.push(setTimeout(() => setAnalysisStage('Generating insight...'), 1400));

    try {
      const response = await fetch(`${BASE_URL}/signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            zone: inferredZone,
          raw_text: inputValue,
          source: 'web',
          user_id: 'web_user_' + Date.now()
        })
      });

      const data = await response.json();
      if (data.status === 'success') {
        setMessage('\u2705 Activity recorded. System is learning from your area.');
        setInputValue('');
        await fetchSummary();
        await fetchRecentSignals();
      } else {
        setMessage("Unable to process activity. Try: 'irrigation mzuzu morning'");
      }
    } catch (err) {
      setMessage("Unable to process activity. Try: 'irrigation mzuzu morning'");
    } finally {
      // clear micro-feedback timers
      analysisTimeoutsRef.current.forEach(t => clearTimeout(t));
      analysisTimeoutsRef.current = [];
      setAnalysisStage('');
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!summary || (typeof summary.signal_count !== 'undefined' && summary.signal_count === 0)) {
      setMessage('More data is needed to generate a full report. Continue recording activities.');
      return;
    }
    setReportLoading(true);
    setMessage('Generating report...');
    try {
      const response = await fetch(`${BASE_URL}/generate-prospectus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone, user_id: 'web_user_' + Date.now() })
      });

      const data = await response.json();
      if (data.status === 'success') {
        setReportData(data.data);
        setMessage('Investment report created successfully.');
        setNextSuggestion('Share this report with a partner');
        // encourage continuous interaction
        setTimeout(() => inputRef.current?.focus(), 300);
      } else {
        setReportData(null);
        const errorMessage = data?.data?.error || data?.error || 'More data is needed to generate a full report. Continue recording activities.';
        setMessage(errorMessage);
      }
    } catch (err) {
      setReportData(null);
      setMessage('More data is needed to generate a full report. Continue recording activities.');
    } finally {
      setReportLoading(false);
    }
  };

  const handleViewInsights = () => {
    if (insightsRef.current) {
      insightsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleSharePartner = async () => {
    const shareText = `Kulima OS demand insights for ${zone} - ${window.location.href}`;
    if (navigator.share) {
      try {
        await navigator.share({ title: 'Kulima OS insights', text: shareText, url: window.location.href });
        setShareMessage('Shared successfully with your partner.');
        setNextSuggestion('Record more activity to strengthen insights');
        setTimeout(() => inputRef.current?.focus(), 300);
        return;
      } catch (error) {
        // silence share cancel
      }
    }
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(window.location.href);
      setShareMessage('Link copied to clipboard for sharing.');
      setNextSuggestion('Record more activity to strengthen insights');
      setTimeout(() => inputRef.current?.focus(), 300);
    } else {
      setShareMessage('Copy this page link to share with your partner.');
    }
  };

  // Prepare structured insight pieces for display (simple, human language)
  const observation = summary?.key_finding || 'Patterns are forming — record more activity to unlock insights.';

  const interpretation = summary?.productive_activities_detected?.length
    ? `Detected activities: ${summary.productive_activities_detected.join(', ')}.`
    : 'Continue recording activity to detect coordination patterns.';

  const implication = summary?.high_confidence_patterns > 0
    ? 'Stable coordination means this zone may be ready for infrastructure planning.'
    : 'More activity records are needed to confirm infrastructure demand.';

  const recommendation = 'Create an investment report to translate this insight into planning guidance.';

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f7f6', color: '#172d20' }}>
      {/* Header */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e0e8e4',
        boxShadow: '0 2px 4px rgba(23, 45, 32, 0.04)'
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '16px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <img src={PUBLIC_LOGO} alt="Kulima OS" style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              objectFit: 'cover',
              backgroundColor: '#2d6a4f'
            }} />
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#172d20' }}>Kulima OS</div>
              <div style={{ fontSize: 11, color: '#5a7a66' }}>Infrastructure Planning</div>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <select
              value={zone}
              onChange={(e) => setZone(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: 8,
                border: '1px solid #d4e0d9',
                backgroundColor: '#f5f7f6',
                fontSize: 13,
                fontWeight: 500,
                color: '#172d20',
                cursor: 'pointer'
              }}
            >
              {['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'].map(z => (
                <option key={z} value={z}>{z}</option>
              ))}
            </select>

            <div style={{
              padding: '6px 12px',
              borderRadius: 999,
              backgroundColor: '#e7f6f1',
              color: '#2d6a4f',
              fontSize: 11,
              fontWeight: 600
            }}>
              Current zone: {zone}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: 1000, margin: '0 auto', padding: '48px 24px' }}>
  <div style={{ maxWidth: 1200, margin: '0 auto' }}>
    <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Hero Section - Action-first Input */}
        {!reportData && (
          <section id="what-is-happening" style={{
            marginBottom: 28,
            animation: 'fadeIn 0.3s ease-in'
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <div style={{ textAlign: 'center' }}>
                <h1 style={{ fontSize: 36, margin: 0, fontWeight: 800, color: '#172d20' }}>What is happening?</h1>
                <div style={{ fontSize: 14, color: '#4a6b57', marginTop: 6 }}>Tap an action or type briefly to record activity.</div>
              </div>

              {/* Activity examples */}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 13, color: '#5a7a66', marginBottom: 8 }}>
                  You can type any activity happening in your area
                </div>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'center' }}>
                  {ACTIVITY_EXAMPLES.map((example) => (
                    <button
                      key={example}
                      type="button"
                      onClick={() => { setInputValue(example); inputRef.current?.focus(); }}
                      style={{
                        padding: '8px 14px',
                        borderRadius: 999,
                        backgroundColor: '#ffffff',
                        border: '1px solid #d4e0d9',
                        color: '#2d6a4f',
                        fontWeight: 600,
                        fontSize: 13,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseOver={(e) => { e.target.style.transform = 'scale(1.05)'; e.target.style.backgroundColor = '#e7f6f1'; }}
                      onMouseOut={(e) => { e.target.style.transform = 'scale(1)'; e.target.style.backgroundColor = '#ffffff'; }}
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>

              {/* Input card */}
              <div style={{ backgroundColor: '#ffffff', borderRadius: 14, padding: 18, border: '1px solid #e6efe8' }}>
                <form onSubmit={handleSubmitActivity} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  <textarea
                    ref={inputRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="e.g. Irrigation in the morning"
                    style={{ flex: 1, minHeight: 100, padding: 12, borderRadius: 10, border: '1px solid #e8f0ea', resize: 'vertical' }}
                    disabled={loading}
                  />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10, minWidth: 180 }}>
                    <button
                      type="submit"
                      disabled={loading || !inputValue.trim()}
                      style={{ padding: '12px 14px', borderRadius: 10, backgroundColor: inputValue.trim() && !loading ? '#2d6a4f' : '#d4e0d9', color: '#fff', border: 'none', fontWeight: 700, cursor: inputValue.trim() && !loading ? 'pointer' : 'not-allowed', transition: 'all 0.2s ease' }}
                      onMouseOver={(e) => { if (inputValue.trim() && !loading) { e.target.style.backgroundColor = '#1f4d38'; e.target.style.transform = 'scale(1.02)'; } }}
                      onMouseOut={(e) => { if (inputValue.trim() && !loading) { e.target.style.backgroundColor = '#2d6a4f'; e.target.style.transform = 'scale(1)'; } }}
                    >
                      {loading ? 'Recording...' : 'Record'}
                    </button>

                    <button type="button" onClick={() => { setInputValue(''); inputRef.current?.focus(); }} style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid #d4e0d9', backgroundColor: '#fff', color: '#2d6a4f', fontWeight: 700 }}>Clear</button>

                    <div style={{ fontSize: 13, color: '#5a7a66', minHeight: 22 }}>
                      {parseZoneFromText(inputValue) ? `Detected zone: ${parseZoneFromText(inputValue)}` : `Using selected zone: ${zone}`}
                    </div>
                  </div>
                </form>

                {/* Micro-feedback */}
                <div style={{ marginTop: 12, minHeight: 22 }}>
                  {loading && analysisStage && (
                    <div style={{ fontSize: 13, color: '#175a9f', animation: 'pulseLoading 1.2s ease-in-out infinite' }}>{analysisStage}</div>
                  )}
                </div>
              </div>

              {/* Compact visual insight preview */}
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center', alignItems: 'stretch', marginTop: 10 }}>
                <div style={{ display: 'flex', gap: 10, flex: 1, justifyContent: 'space-between', maxWidth: 760 }}>
                  <div style={{ backgroundColor: '#fff', borderRadius: 12, padding: 12, border: '1px solid #e6efe8', flex: 1, textAlign: 'center', cursor: 'pointer' }} onClick={() => { setInsightExpanded(!insightExpanded); if (!insightExpanded) setTimeout(() => insightsRef.current?.scrollIntoView({ behavior: 'smooth' }), 80); }}>
                    <div style={{ fontSize: 18 }}>🔥</div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#172d20' }}>{summary?.productive_activities_detected?.[0] || 'Activity detected'}</div>
                  </div>
                  <div style={{ backgroundColor: '#fff', borderRadius: 12, padding: 12, border: '1px solid #e6efe8', flex: 1, textAlign: 'center', cursor: 'pointer' }} onClick={() => { setInsightExpanded(!insightExpanded); if (!insightExpanded) setTimeout(() => insightsRef.current?.scrollIntoView({ behavior: 'smooth' }), 80); }}>
                    <div style={{ fontSize: 18 }}>🕒</div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#172d20' }}>{summary?.demand_patterns?.[0]?.frequency || 'Time pattern'}</div>
                  </div>
                  <div style={{ backgroundColor: '#fff', borderRadius: 12, padding: 12, border: '1px solid #e6efe8', flex: 1, textAlign: 'center', cursor: 'pointer' }} onClick={() => { setInsightExpanded(!insightExpanded); if (!insightExpanded) setTimeout(() => insightsRef.current?.scrollIntoView({ behavior: 'smooth' }), 80); }}>
                    <div style={{ fontSize: 18 }}>⚡</div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#172d20' }}>{summary?.high_confidence_patterns ? 'Demand signal' : 'Demand signal'}</div>
                  </div>
                </div>
              </div>
            </div>
            {message && (
              <div style={{
                padding: '16px 18px',
                borderRadius: 12,
                backgroundColor: message.includes('\u2705') || message.includes('\u2713') ? '#ecf7ef' : '#fef3e0',
                color: message.includes('\u2705') || message.includes('\u2713') ? '#1f4d2b' : '#b8860b',
                marginBottom: 24,
                fontSize: 14,
                fontWeight: 500,
                border: `1px solid ${message.includes('\u2705') || message.includes('\u2713') ? '#d8f0d3' : '#fce8d4'}`,
                animation: 'fadeIn 0.3s ease-in'
              }}>
                {message}
              </div>
            )}
          </section>
        )}

            {/* Production: no demo/banner shown */}

        {/* Insights Response Section */}
        {summary && !reportData && (
          <section id="what-it-means" ref={insightsRef} style={{
            marginBottom: 48,
            animation: 'slideUp 0.3s ease-out'
          }}>
            {/* How it works block */}
            <div style={{
              backgroundColor: '#f0f7ff',
              borderRadius: 16,
              padding: '20px',
              border: '1px solid #c4daf6',
              marginBottom: 24
            }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#1a5276', marginBottom: 12 }}>
                How Kulima OS works:
              </div>
              <div style={{ fontSize: 13, color: '#2d3748', lineHeight: 1.8 }}>
                <div style={{ marginBottom: 8 }}>1. You record activity</div>
                <div style={{ marginBottom: 8 }}>2. The system groups similar signals</div>
                <div style={{ marginBottom: 8 }}>3. Repeated signals create demand patterns</div>
                <div>4. Patterns reveal infrastructure needs</div>
              </div>
            </div>

            {/* Coordination patterns explanation */}
            <div style={{
              backgroundColor: '#fffaf0',
              borderRadius: 12,
              padding: '16px',
              border: '1px solid #fce8d4',
              marginBottom: 24
            }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#b8860b', marginBottom: 8 }}>
                About Coordination Patterns
              </div>
              <div style={{ fontSize: 13, color: '#4a4a4a', lineHeight: 1.6 }}>
                Patterns form when similar activities are recorded multiple times in the same area.
              </div>
              <div style={{ fontSize: 12, color: '#666', marginTop: 8 }}>
                {summary?.signal_count || 0} signals recorded → {Math.max(0, 3 - (summary?.signal_count || 0))}–{Math.max(0, 5 - (summary?.signal_count || 0))} more needed to detect a pattern
              </div>
            </div>
            {/* Assistant Response - Structured Reasoning Card */}
            {insightExpanded && (
              <div style={{
                backgroundColor: '#e7f6f1',
                borderRadius: 16,
                padding: '20px',
                border: '1px solid #b8e6d5',
                marginBottom: 24
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#2d6a4f', marginBottom: 10 }}>
                  SYSTEM INSIGHT
                </div>
                <div style={{ display: 'grid', gap: 12 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 12, alignItems: 'start', padding: 12, backgroundColor: '#ffffff', borderRadius: 12, border: '1px solid #dff0e8' }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: '#175a9f' }}>Observation</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: '#172d20', lineHeight: 1.4 }}>{observation}</div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 12, alignItems: 'start', padding: 12, backgroundColor: '#ffffff', borderRadius: 12, border: '1px solid #dfeff0' }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: '#175a9f' }}>Interpretation</div>
                    <div style={{ fontSize: 14, color: '#2d6a4f', lineHeight: 1.5 }}>{interpretation}</div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 12, alignItems: 'start', padding: 12, backgroundColor: '#ffffff', borderRadius: 12, border: '1px solid #f6f0e6' }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: '#b9690b' }}>Implication</div>
                    <div style={{ fontSize: 14, color: '#4a6b57', lineHeight: 1.5 }}>{implication}</div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 12, alignItems: 'start', padding: 12, backgroundColor: '#ffffff', borderRadius: 12, border: '1px solid #dfe7e0' }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: '#2d6a4f' }}>Recommendation</div>
                    <div style={{ fontSize: 14, color: '#2d6a4f', lineHeight: 1.5 }}>{recommendation}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Next Step suggestion - appears after the System Insight card */}
            {insightExpanded && (
              <div style={{
                backgroundColor: '#fffef6',
                borderRadius: 12,
                padding: '14px',
                border: '1px solid #fbedd4',
                marginBottom: 18,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 12
              }}>
                <div style={{ fontSize: 14, color: '#6b4f1a' }}>
                  <strong>Next step:</strong> {nextSuggestion || 'Would you like to generate an investment report based on this activity?'}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={handleGenerateReport} disabled={reportLoading} style={{ padding: '10px 12px', borderRadius: 10, backgroundColor: '#2d6a4f', color: '#fff', border: 'none', fontWeight: 700 }}>Generate Report</button>
                  <button onClick={() => { setInputValue(''); inputRef.current?.focus(); setNextSuggestion(''); }} style={{ padding: '10px 12px', borderRadius: 10, backgroundColor: '#fff', border: '1px solid #d4e0d9', color: '#2d6a4f', fontWeight: 700 }}>Continue Recording</button>
                  <button onClick={handleSharePartner} style={{ padding: '10px 12px', borderRadius: 10, backgroundColor: '#f4f7f5', border: '1px solid #cde6d3', color: '#2d6a4f', fontWeight: 700 }}>Share Insight</button>
                </div>
              </div>
            )}

            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: 16,
              border: '1px solid #d4e0d9',
              padding: '24px',
              marginBottom: 24
            }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#2d6a4f', marginBottom: 12 }}>Based on current activity</div>

              {/* Signal Confidence Indicator */}
              {(() => {
                const count = summary?.signal_count || 0;
                let level, color, bg, border;
                if (count >= 6) { level = 'HIGH'; color = '#1a6b3c'; bg = '#e7f6ef'; border = '#b8e6d0'; }
                else if (count >= 3) { level = 'MEDIUM'; color = '#7a6b14'; bg = '#fff9e6'; border = '#fce8b4'; }
                else { level = 'LOW'; color = '#8b4513'; bg = '#fef3e8'; border = '#fce0c4'; }
                return (
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 14px', borderRadius: 8, backgroundColor: bg, border: `1px solid ${border}`, marginBottom: 14, fontSize: 12, fontWeight: 600 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: color, display: 'inline-block' }} />
                    <span style={{ color }}>Signal Strength: {level}</span>
                    <span style={{ color: '#5a7a66', fontWeight: 400 }}>({count} signal{count !== 1 ? 's' : ''})</span>
                  </div>
                );
              })()}
              <div style={{ fontSize: 16, color: '#172d20', marginBottom: 18, lineHeight: 1.6 }}>
                {summary?.key_finding || 'There is emerging demand for productive activity that can guide infrastructure decisions.'}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                <button
                  onClick={handleGenerateReport}
                  disabled={reportLoading}
                  style={{
                    flex: '1 1 200px',
                    padding: '14px 20px',
                    borderRadius: 12,
                    backgroundColor: '#2d6a4f',
                    color: '#fff',
                    border: 'none',
                    fontWeight: 700,
                    cursor: reportLoading ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseOver={(e) => { if (!reportLoading) { e.target.style.backgroundColor = '#1f4d38'; e.target.style.transform = 'scale(1.02)'; } }}
                  onMouseOut={(e) => { if (!reportLoading) { e.target.style.backgroundColor = '#2d6a4f'; e.target.style.transform = 'scale(1)'; } }}
                >
                  {reportLoading ? 'Creating report…' : 'Create Investment Report'}
                </button>
                <button
                  onClick={handleViewInsights}
                  type="button"
                  style={{
                    flex: '1 1 200px',
                    padding: '14px 20px',
                    borderRadius: 12,
                    border: '1px solid #2d6a4f',
                    backgroundColor: '#ffffff',
                    color: '#2d6a4f',
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseOver={(e) => { e.target.style.backgroundColor = '#e7f6f1'; e.target.style.transform = 'scale(1.02)'; }}
                  onMouseOut={(e) => { e.target.style.backgroundColor = '#ffffff'; e.target.style.transform = 'scale(1)'; }}
                >
                  View Full Insights
                </button>
                <button
                  onClick={handleSharePartner}
                  type="button"
                  style={{
                    flex: '1 1 200px',
                    padding: '14px 20px',
                    borderRadius: 12,
                    backgroundColor: '#f4f7f5',
                    color: '#2d6a4f',
                    border: '1px solid #cde6d3',
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseOver={(e) => { e.target.style.backgroundColor = '#e7f6f1'; e.target.style.transform = 'scale(1.02)'; }}
                  onMouseOut={(e) => { e.target.style.backgroundColor = '#f4f7f5'; e.target.style.transform = 'scale(1)'; }}
                >
                  Share with Partner
                </button>
              </div>
              {shareMessage && (
                <div style={{ marginTop: 16, fontSize: 13, color: '#2d6a4f' }}>
                  {shareMessage}
                </div>
              )}
            </div>

            {/* Key Stats Grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: 16,
              marginBottom: 24
            }}>
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: 12,
                padding: '20px',
                border: '1px solid #e0e8e4'
              }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: '#2d6a4f', marginBottom: 6 }}>
                  {summary?.signal_count ?? 0}
                </div>
                <div style={{ fontSize: 13, color: '#5a7a66' }}>
                  Activities recorded
                </div>
              </div>
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: 12,
                padding: '20px',
                border: '1px solid #e0e8e4'
              }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: '#2d6a4f', marginBottom: 6 }}>
                  {summary?.total_patterns ?? 0}
                </div>
                <div style={{ fontSize: 13, color: '#5a7a66' }}>
                  Patterns detected
                </div>
              </div>
            </div>

            {/* Activities Detected */}
            {summary?.productive_activities_detected && summary.productive_activities_detected.length > 0 && (
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: 12,
                padding: '20px',
                border: '1px solid #e0e8e4',
                marginBottom: 24
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#2d6a4f', marginBottom: 14 }}>
                  ACTIVITIES DETECTED
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                  {summary.productive_activities_detected.map((activity, idx) => (
                    <div key={idx} style={{
                      padding: '8px 14px',
                      borderRadius: 8,
                      backgroundColor: '#e7f6f1',
                      border: '1px solid #b8e6d5',
                      fontSize: 13,
                      fontWeight: 600,
                      color: '#2d6a4f',
                      textTransform: 'capitalize'
                    }}>
                      ✓ {activity}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Demand Patterns */}
            {summary?.demand_patterns && summary.demand_patterns.length > 0 && (
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: 12,
                padding: '20px',
                border: '1px solid #e0e8e4',
                marginBottom: 24
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#2d6a4f', marginBottom: 14 }}>
                  DEMAND PATTERNS
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {summary.demand_patterns.map((pattern, idx) => (
                    <div key={idx} style={{
                      padding: '12px 14px',
                      borderRadius: 8,
                      backgroundColor: '#f5f7f6',
                      border: '1px solid #e0e8e4',
                      fontSize: 13
                    }}>
                      <div style={{ fontWeight: 600, color: '#172d20', marginBottom: 4 }}>
                        {pattern.activity}
                      </div>
                      <div style={{ color: '#5a7a66', fontSize: 12 }}>
                        {pattern.frequency} • Confidence: {pattern.confidence}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Infrastructure Gaps */}
            {summary?.infrastructure_gaps && summary.infrastructure_gaps.length > 0 && (
              <div style={{
                backgroundColor: '#fff9e6',
                borderRadius: 12,
                padding: '20px',
                border: '1px solid #fce8d4',
                marginBottom: 24
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#b8860b', marginBottom: 12 }}>
                  ⚡ INFRASTRUCTURE NEEDS
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {summary.infrastructure_gaps.slice(0, 3).map((gap, idx) => (
                    <div key={idx} style={{
                      fontSize: 13,
                      color: '#6b5914',
                      lineHeight: 1.5
                    }}>
                      • {gap}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Infrastructure Opportunity Card */}
            {(() => {
              const activities = summary?.productive_activities_detected || [];
              const gaps = summary?.infrastructure_gaps || [];
              const signalCount = summary?.signal_count || 0;
              const patternCount = summary?.total_patterns || 0;
              const hasGaps = gaps.length > 0;
              const dominantActivity = activities[0] || 'productive';
              const hasRepeatedActivity = signalCount > 2;
              const noPatternYet = patternCount === 0;
              if (!hasRepeatedActivity && !hasGaps) return null;
              return (
                <div style={{
                  backgroundColor: '#f0f7ff',
                  borderRadius: 12,
                  padding: '20px',
                  border: '1px solid #c4daf6',
                  marginBottom: 24
                }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#1a5276', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                    \u26A0\uFE0F {hasGaps ? 'INFRASTRUCTURE GAP DETECTED' : 'INFRASTRUCTURE OPPORTUNITY'}
                  </div>
                  <div style={{ fontSize: 14, color: '#1a3a5c', lineHeight: 1.6, marginBottom: 10 }}>
                    {hasGaps
                      ? `High ${dominantActivity} activity in ${zone} with limited infrastructure presence.`
                      : hasRepeatedActivity && noPatternYet
                        ? `Repeated ${dominantActivity} activity detected but no confirmed infrastructure pattern yet.`
                        : `Repeated ${dominantActivity} activity in ${zone} suggests emerging coordination.`
                    }
                  </div>
                  <div style={{ fontSize: 13, color: '#2d6a4f', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                    \u2192 {hasGaps ? 'Opportunity emerging for investment' : 'Opportunity emerging'}
                  </div>
                </div>
              );
            })()}

            {/* Report Generation CTA */}
            <button
              onClick={handleGenerateReport}
              disabled={reportLoading}
              style={{
                width: '100%',
                padding: '16px 24px',
                borderRadius: 12,
                backgroundColor: '#2d6a4f',
                color: '#fff',
                border: 'none',
                fontWeight: 600,
                fontSize: 15,
                cursor: reportLoading ? 'not-allowed' : 'pointer',
                transition: 'background 0.2s',
                marginTop: 12
              }}
              onMouseOver={(e) => {
                if (!reportLoading) e.target.style.backgroundColor = '#1f4d38';
              }}
              onMouseOut={(e) => {
                if (!reportLoading) e.target.style.backgroundColor = '#2d6a4f';
              }}
            >
              {reportLoading ? '⏳ Creating Investment Report...' : '📄 Create Investment Report'}
            </button>
          </section>
        )}

        {/* Report Section */}
        {reportData && (
          <section style={{
            backgroundColor: '#ffffff',
            borderRadius: 16,
            padding: '32px',
            boxShadow: '0 4px 16px rgba(23, 45, 32, 0.08)',
            border: '2px solid #2d6a4f',
            textAlign: 'center'
          }}>
            <div style={{ marginBottom: 24 }}>
              <h2 style={{
                margin: '0 0 12px 0',
                fontSize: 32,
                fontWeight: 700,
                color: '#172d20'
              }}>
                ✓ {reportData?.is_sample ? 'Sample Prospectus Ready' : 'Investment Report Ready'}
              </h2>
              <p style={{
                margin: 0,
                color: '#5a7a66',
                fontSize: 14,
                lineHeight: 1.6
              }}>
                Your demand signal prospectus is ready for review by investors and planners.
              </p>
            </div>

            <div style={{
              padding: '24px',
              borderRadius: 12,
              backgroundColor: '#e7f6f1',
              border: '1px solid #b8e6d5',
              marginBottom: 24,
              fontSize: 13,
              color: '#2d6a4f',
              lineHeight: 1.7
            }}>
              <strong>Your report includes:</strong>
              <ul style={{ margin: '12px 0 0 20px', paddingLeft: 0 }}>
                <li>Executive summary of demand patterns</li>
                <li>Activities observed in {zone}</li>
                <li>Timing and frequency of peak demand</li>
                <li>Infrastructure gaps and needs</li>
                <li>Investment opportunity analysis</li>
                <li>Confidence scores and reliability metrics</li>
                <li>Recommended next steps</li>
              </ul>
            </div>

            <a
              href={reportUrl || '#'}
              download
              style={{
                display: 'inline-block',
                padding: '14px 28px',
                borderRadius: 10,
                backgroundColor: '#2d6a4f',
                color: '#fff',
                fontWeight: 600,
                textDecoration: 'none',
                cursor: 'pointer',
                transition: 'background 0.2s',
                marginRight: 12
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#1f4d38'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#2d6a4f'}
            >
              ↓ Download PDF Report
            </a>

            <button
              onClick={() => {
                setReportData(null);
                setInputValue('');
                setMessage('');
                inputRef.current?.focus();
              }}
              style={{
                display: 'inline-block',
                padding: '14px 28px',
                borderRadius: 10,
                backgroundColor: '#e7f6f1',
                color: '#2d6a4f',
                border: '2px solid #2d6a4f',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'background 0.2s'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#d0f0e5'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#e7f6f1'}
            >
              ↻ Create Another Report
            </button>
          </section>
        )}
        {!summary && (
        <section id="what-to-do" style={{
          backgroundColor: '#f1faf5',
          borderRadius: 24,
          padding: '32px',
          marginBottom: 48,
          border: '1px solid #dce8df'
        }}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 24,
            maxWidth: 1000,
            margin: '0 auto'
          }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#2d6a4f', marginBottom: 10 }}>FOR DECISION-MAKERS</div>
              <h2 style={{ fontSize: 28, fontWeight: 700, margin: 0, color: '#172d20' }}>
                Turn coordination signals into action.
              </h2>
              <p style={{ fontSize: 15, color: '#4a6b57', lineHeight: 1.7, maxWidth: 760, marginTop: 10 }}>
                Request complete planning reports, partner with Kulima Africa, and use the PayChangu workflow for transparent funding and deployment tracking.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 18 }}>
              <a
                href="mailto:info@kulima.africa?subject=Request%20Full%20Kulima%20Report"
                style={{
                  display: 'block',
                  padding: '22px',
                  borderRadius: 18,
                  backgroundColor: '#ffffff',
                  border: '1px solid #d4e0d9',
                  textDecoration: 'none',
                  color: '#172d20'
                }}
              >
                <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 10 }}>Request Full Reports</div>
                <div style={{ fontSize: 13, color: '#4a6b57', lineHeight: 1.6 }}>
                  Get a complete investor-grade prospectus and coordination profile for your project area.
                </div>
              </a>

              <a
                href="mailto:info@kulima.africa?subject=Partner%20with%20Kulima%20Africa"
                style={{
                  display: 'block',
                  padding: '22px',
                  borderRadius: 18,
                  backgroundColor: '#ffffff',
                  border: '1px solid #d4e0d9',
                  textDecoration: 'none',
                  color: '#172d20'
                }}
              >
                <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 10 }}>Partner with Kulima Africa</div>
                <div style={{ fontSize: 13, color: '#4a6b57', lineHeight: 1.6 }}>
                  Collaborate on demand-led infrastructure planning and asset deployment in underserved zones.
                </div>
              </a>

              <div style={{
                padding: '22px',
                borderRadius: 18,
                backgroundColor: '#e9f4ef',
                border: '1px solid #c9e5d5'
              }}>
                <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 10, color: '#175a9f' }}>Funding Transparency</div>
                <div style={{ fontSize: 13, color: '#4a6b57', lineHeight: 1.6 }}>
                  Payments are managed through PayChangu so stakeholders maintain clear, auditable financial flows for demo and pilot funding.
                </div>
              </div>
            </div>
          </div>
        </section>
        )}
            </div>
      <div style={{ width: 320, minWidth: 280 }}>
        <div style={{ background: '#fff', borderRadius: 12, padding: 12, boxShadow: '0 8px 24px rgba(12,36,22,0.06)' }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: 16 }}>Live Activity</h3>
          <div style={{ maxHeight: 520, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }} ref={liveScrollRef}>
            {recentSignals.length === 0 && !liveLoading && (
              <div style={{ color: '#5a7a66', padding: '18px 14px', textAlign: 'center', backgroundColor: '#f8faf8', borderRadius: 10, border: '1px dashed #d4e0d9', lineHeight: 1.6, fontSize: 13 }}>
                Waiting for first signal...<br />Be the first to record activity \uD83D\uDD25
              </div>
            )}
            {recentSignals.length > 0 && recentSignals.map(sig => {
              const isFlashing = flashIds.includes(sig.id);
              return (
              <div key={sig.id} style={{
                padding: 10,
                borderRadius: 8,
                background: isFlashing ? 'linear-gradient(90deg, rgba(45,106,79,0.12), rgba(45,106,79,0.03))' : '#fbfffd',
                boxShadow: isFlashing ? '0 8px 20px rgba(45,106,79,0.12)' : 'none',
                border: isFlashing ? '1px solid rgba(45,106,79,0.25)' : '1px solid rgba(18, 60, 38, 0.04)',
                transition: 'all 0.6s ease',
                animation: isFlashing ? 'signalGlow 2.5s ease-out' : 'none'
              }}>
                <div style={{ fontSize: 13, fontWeight: 700, textTransform: 'capitalize' }}>{sig.activity_type || sig.activity || sig.type || 'Activity'}</div>
                <div style={{ fontSize: 12, color: '#666' }}>{sig.zone || sig.zone_name || sig.location || '—'} {sig.time_window && sig.time_window !== 'unknown' ? `• ${sig.time_window}` : ''}</div>
                <div style={{ marginTop: 6, fontSize: 12, color: '#444' }}>{sig.original_text?.slice(0, 80) || sig.raw_text?.slice(0, 80) || ''}</div>
                {sig.timestamp && <div style={{ marginTop: 4, fontSize: 11, color: '#999' }}>{new Date(sig.timestamp).toLocaleString()}</div>}
              </div>
              );
            })}
          </div>
        </div>

          <div style={{ marginTop: 20, background: '#f7fbf7', borderRadius: 16, padding: 20, border: '1px solid #d8e8d6' }}>
            <h3 style={{ margin: '0 0 14px 0', fontSize: 16, color: '#14532d' }}>Connect via WhatsApp</h3>
            <p style={{ fontSize: 13, color: '#0f5132', marginTop: 0, marginBottom: 16, lineHeight: 1.5 }}>
              Scan to connect via WhatsApp and start sending activities instantly.
            </p>
            <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
              <img src={WHATSAPP_QR_IMAGE} alt="WhatsApp onboarding QR code" style={{ width: 110, height: 110, borderRadius: 14, border: '2px solid #cfe8d4', flexShrink: 0 }} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontSize: 13, color: '#2d6a4f', lineHeight: 1.8 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 20, height: 20, borderRadius: '50%', backgroundColor: '#2d6a4f', color: '#fff', fontSize: 11, fontWeight: 700, flexShrink: 0 }}>1</span>
                    <span>Scan QR code</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 20, height: 20, borderRadius: '50%', backgroundColor: '#2d6a4f', color: '#fff', fontSize: 11, fontWeight: 700, flexShrink: 0 }}>2</span>
                    <span>Send: <strong>join week-saved</strong></span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 20, height: 20, borderRadius: '50%', backgroundColor: '#2d6a4f', color: '#fff', fontSize: 11, fontWeight: 700, flexShrink: 0 }}>3</span>
                    <span>Start sending activity <em>(e.g. "trading mzuzu morning")</em></span>
                  </div>
                </div>
              </div>
            </div>
            <a
              href={WHATSAPP_ONBOARDING_LINK}
              target="_blank"
              rel="noreferrer"
              style={{ display: 'inline-block', marginTop: 16, padding: '10px 16px', borderRadius: 12, backgroundColor: '#25D366', color: '#fff', textDecoration: 'none', fontWeight: 700, fontSize: 13, transition: 'all 0.2s ease' }}
              onMouseOver={(e) => { e.target.style.backgroundColor = '#1fba59'; e.target.style.transform = 'scale(1.02)'; }}
              onMouseOut={(e) => { e.target.style.backgroundColor = '#25D366'; e.target.style.transform = 'scale(1)'; }}
            >
              Open WhatsApp
            </a>
          </div>
        </div>
      </div>
    </div>
    </main>

      <footer style={{
        backgroundColor: '#2d6a4f',
        color: '#e0e8e4',
        padding: '40px 24px',
        marginTop: 80,
        borderTop: '1px solid #1f4d38'
      }}>
        <div style={{ maxWidth: 1000, margin: '0 auto', textAlign: 'center' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gap: 32,
            marginBottom: 32
          }}>
            <div>
              <div style={{ fontWeight: 700, color: '#fff', marginBottom: 10, fontSize: 14 }}>Kulima OS</div>
              <div style={{ fontSize: 12, lineHeight: 1.6, color: '#b8d4c5' }}>
                Infrastructure planning powered by real community activity.
              </div>
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#fff', marginBottom: 10, fontSize: 14 }}>Our Mission</div>
              <div style={{ fontSize: 12, color: '#b8d4c5' }}>
                Food Everywhere, For Everyone, At All Times
              </div>
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#fff', marginBottom: 10, fontSize: 14 }}>Status</div>
              <div style={{ fontSize: 12, color: '#b8d4c5' }}>
                ✓ Pilot Active • Data Flowing • Ready for Scale
              </div>
            </div>
          </div>
          <div style={{
            borderTop: '1px solid rgba(224, 232, 228, 0.2)',
            paddingTop: 20,
            fontSize: 11,
            color: '#8ab39c'
          }}>
            © 2026 Kulima Africa. Built for better decisions. Real activity. Real intelligence.
          </div>
        </div>
      </footer>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes liveItemEnter {
          from { opacity: 0; transform: translateY(-6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes signalGlow {
          0% { box-shadow: 0 0 0 0 rgba(45,106,79,0.3); }
          40% { box-shadow: 0 0 12px 4px rgba(45,106,79,0.15); }
          100% { box-shadow: 0 0 0 0 rgba(45,106,79,0); }
        }
        @keyframes pulseLoading {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
      `}</style>

      {/* Toast notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          padding: '12px 20px',
          borderRadius: 12,
          backgroundColor: '#2d6a4f',
          color: '#fff',
          fontSize: 13,
          fontWeight: 600,
          boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
          zIndex: 100,
          animation: 'fadeIn 0.3s ease-in'
        }}>
          {toastMessage}
        </div>
      )}
    </div>
  );
}
