'use client';

import { useState, useEffect, useRef } from 'react';

const DEMO_SIGNAL_THRESHOLD = 5;
const DEMO_MODE_MESSAGE = 'This is a sample demonstration. The system shows sample insights and patterns to demonstrate how it works. Once real data arrives, you\'ll see actual community activities.';
const SAMPLE_REPORT_PATH = '/demand_prospectus_mzuzu_2026-05-20T17-07-42.471246.pdf';
const PUBLIC_LOGO = '/logo.png';

const SAMPLE_SUMMARY = {
  zone: 'MZUZU',
  signal_count: 3,
  total_patterns: 2,
  high_confidence_patterns: 1,
  moderate_confidence_patterns: 1,
  zones_with_coordinated_demand: ['MZUZU'],
  productive_activities_detected: ['irrigation', 'milling', 'cold storage'],
  key_finding: 'Activity in Mzuzu shows growing demand for irrigation and milling.',
  insights: [
    'Irrigation activity peaks in early mornings (6-9 AM)',
    'Milling happens mid-morning when farmers bring crops',
    'Cold storage supports same-day supply chains'
  ],
  demand_patterns: [
    { activity: 'Irrigation', frequency: 'Daily', confidence: 'High', impact: 'Morning peak demand' },
    { activity: 'Milling', frequency: 'Daily', confidence: 'Medium', impact: 'Mid-morning load' },
    { activity: 'Cold Storage', frequency: 'Daily', confidence: 'High', impact: 'Consistent baseline' }
  ],
  infrastructure_gaps: [
    'Three-phase power in Zone A (needed for irrigation)',
    'Dedicated milling shed infrastructure',
    'Cold chain capacity upgrade'
  ],
  updated_at: new Date().toISOString()
};

const SAMPLE_ACTIVITY_FEED = [
  { id: 1, time: '09:15 AM', activity: 'Irrigation', zone: 'MZUZU', description: 'Maize irrigation started in field A', source: 'web', status: 'confirmed' },
  { id: 2, time: '08:50 AM', activity: 'Milling', zone: 'MZUZU', description: 'Grinding maize at community mill', source: 'whatsapp', status: 'confirmed' },
  { id: 3, time: '08:20 AM', activity: 'Cold Storage', zone: 'MZUZU', description: 'Cold room cycle began', source: 'infrastructure', status: 'confirmed' }
];

export default function Home() {
  const [zone, setZone] = useState('MZUZU');
  const [inputValue, setInputValue] = useState('');
  const [summary, setSummary] = useState(null);
  const [activityFeed, setActivityFeed] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [assistantResponse, setAssistantResponse] = useState('');
  const [assistantExplanation, setAssistantExplanation] = useState('');
  const [shareMessage, setShareMessage] = useState('');
  const inputRef = useRef(null);
  const insightsRef = useRef(null);

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const BACKEND_BASE = BASE_URL.replace(/\/api\/v1$/, '');
  const isDemoMode = !summary || summary.signal_count < DEMO_SIGNAL_THRESHOLD;
  const displayedSummary = isDemoMode ? SAMPLE_SUMMARY : summary;
  const reportUrl = reportData?.pdf_url
    ? reportData?.is_sample
      ? reportData.pdf_url
      : `${BACKEND_BASE}${reportData.pdf_url}`
    : '';

  useEffect(() => {
    fetchSummary();
  }, [zone]);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BASE_URL}/summary/${zone}`);
      const data = await response.json();
      if (data.status === 'success') {
        setSummary(data.data);
      } else {
        setSummary(SAMPLE_SUMMARY);
      }
    } catch (error) {
      console.error('Error fetching summary:', error);
      setSummary(SAMPLE_SUMMARY);
    } finally {
      setLoading(false);
    }
  };

  // Parse natural language input
  const parseActivityFromInput = (text) => {
    const text_lower = text.toLowerCase();
    let activity_type = '';
    let time_window = 'morning';

    if (text_lower.includes('irrigat')) activity_type = 'irrigation';
    else if (text_lower.includes('mill')) activity_type = 'milling';
    else if (text_lower.includes('cold') || text_lower.includes('storage')) activity_type = 'cold storage';
    else if (text_lower.includes('weld') || text_lower.includes('metal')) activity_type = 'welding';
    else if (text_lower.includes('pump')) activity_type = 'irrigation';
    else if (text_lower.includes('grain')) activity_type = 'milling';
    else activity_type = 'other productive activity';

    if (text_lower.includes('morning') || text_lower.includes('early') || /[6-9]/.test(text)) {
      time_window = 'morning';
    } else if (text_lower.includes('afternoon') || text_lower.includes('noon')) {
      time_window = 'afternoon';
    } else if (text_lower.includes('evening') || text_lower.includes('night')) {
      time_window = 'evening';
    }

    return { activity_type, time_window };
  };

  const handleSubmitActivity = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) {
      setMessage('Please describe an activity.');
      return;
    }

    const { activity_type, time_window } = parseActivityFromInput(inputValue);
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch(`${BASE_URL}/signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone,
          activity_type,
          time_window,
          source: 'web',
          user_id: 'web_user_' + Date.now()
        })
      });

      const data = await response.json();
      if (data.status === 'success') {
        setMessage(`✓ Activity recorded: ${activity_type} in ${time_window}`);
        setAssistantResponse(`We recorded ${activity_type} activity for ${zone} during the ${time_window}.`);
        setAssistantExplanation('This signal has been added to the coordination analysis. Create an investment report to convert it into an investor-ready prospectus.');
        setInputValue('');
        
        setActivityFeed(prev => [
          {
            id: Date.now(),
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            activity: activity_type,
            zone,
            description: inputValue,
            source: 'web',
            status: 'confirmed'
          },
          ...prev
        ].slice(0, 10));

        await fetchSummary();
      } else {
        setMessage('Activity not recorded. Please try again.');
      }
    } catch (error) {
      console.error('Error:', error);
      setMessage('Unable to record activity. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    setReportLoading(true);
    setMessage('');

    if (isDemoMode) {
      setReportData({
        pdf_url: SAMPLE_REPORT_PATH,
        is_sample: true,
        title: 'Sample Investment Report'
      });
      setMessage('This report is a sample demonstration.');
      setReportLoading(false);
      return;
    }
    try {
      const response = await fetch(`${BASE_URL}/generate-prospectus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone, user_id: 'web_user_' + Date.now() })
      });

      const data = await response.json();
      if (data.status === 'success') {
        setReportData(data.data);
        setMessage('✓ Investment report created successfully!');
      } else {
        setMessage('Report generation failed. Please try again.');
      }
    } catch (error) {
      console.error('Error:', error);
      setMessage('Unable to generate report. Please try again.');
    } finally {
      setReportLoading(false);
    }
  };

  const handleDownloadSampleReport = () => {
    window.location.href = SAMPLE_REPORT_PATH;
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
        return;
      } catch (error) {
        // silence share cancel
      }
    }
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(window.location.href);
      setShareMessage('Link copied to clipboard for sharing.');
    } else {
      setShareMessage('Copy this page link to share with your partner.');
    }
  };

  // Prepare structured insight pieces for display (simple, human language)
  const observation = (assistantResponse && assistantResponse.length > 0)
    ? assistantResponse
    : (displayedSummary?.key_finding || 'No clear observation available.');

  const interpretation = (assistantExplanation && assistantExplanation.length > 0)
    ? assistantExplanation
    : (displayedSummary?.insights?.[0] || 'Interpretation not available yet.');

  const implication = displayedSummary?.demand_patterns && displayedSummary.demand_patterns.length > 0
    ? `This suggests ${displayedSummary.demand_patterns[0].impact.toLowerCase()}.`
    : 'This may create demand for nearby energy and water infrastructure.';

  const recommendation = isDemoMode
    ? 'Download the sample report to see how this insight becomes an investor-ready prospectus.'
    : 'Create an investment report to translate this insight into planning guidance.';

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

            {isDemoMode && (
              <span style={{
                padding: '6px 12px',
                borderRadius: 999,
                backgroundColor: '#fef3e0',
                color: '#b8860b',
                fontSize: 11,
                fontWeight: 600
              }}>
                Sample Demo
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: 1000, margin: '0 auto', padding: '48px 24px' }}>
        {/* Hero Section - Main Input */}
        {!reportData && (
          <section style={{
            marginBottom: 48,
            animation: 'fadeIn 0.3s ease-in'
          }}>
            <div style={{ textAlign: 'center', marginBottom: 48 }}>
              <h1 style={{
                fontSize: 44,
                lineHeight: 1.2,
                margin: 0,
                fontWeight: 700,
                color: '#172d20',
                marginBottom: 12
              }}>
                What is happening in your area?
              </h1>
              <p style={{
                fontSize: 18,
                color: '#4a6b57',
                margin: '12px 0 0',
                maxWidth: 760,
                marginLeft: 'auto',
                marginRight: 'auto'
              }}>
                Kulima OS is a digital public infrastructure for planning energy and infrastructure using real-world activity.
              </p>
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: 12,
              flexWrap: 'wrap',
              marginBottom: 32
            }}>
              <div style={{
                padding: '12px 18px',
                borderRadius: 999,
                backgroundColor: '#eef7ee',
                color: '#1f4d38',
                fontSize: 12,
                fontWeight: 700,
                border: '1px solid #cde6d3'
              }}>
                Try the system
              </div>
              <div style={{
                padding: '12px 18px',
                borderRadius: 999,
                backgroundColor: '#ffffff',
                color: '#406e54',
                fontSize: 12,
                border: '1px solid #d4e0d9'
              }}>
                1. Type activity
              </div>
              <div style={{
                padding: '12px 18px',
                borderRadius: 999,
                backgroundColor: '#ffffff',
                color: '#406e54',
                fontSize: 12,
                border: '1px solid #d4e0d9'
              }}>
                2. See insight
              </div>
              <div style={{
                padding: '12px 18px',
                borderRadius: 999,
                backgroundColor: '#ffffff',
                color: '#406e54',
                fontSize: 12,
                border: '1px solid #d4e0d9'
              }}>
                3. Download report
              </div>
            </div>

            {/* Input Card */}
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: 16,
              padding: '32px',
              boxShadow: '0 4px 16px rgba(23, 45, 32, 0.08)',
              border: '1px solid #e0e8e4',
              marginBottom: 24
            }}>
              <form onSubmit={handleSubmitActivity}>
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Describe what is happening in your area… e.g. 'We are irrigating maize in the morning' or 'Grinding crops at the mill'"
                  style={{
                    width: '100%',
                    padding: '16px 18px',
                    borderRadius: 12,
                    border: '1px solid #d4e0d9',
                    backgroundColor: '#f5f7f6',
                    fontSize: 15,
                    fontFamily: 'inherit',
                    color: '#172d20',
                    resize: 'vertical',
                    minHeight: 120,
                    boxSizing: 'border-box',
                    lineHeight: 1.5
                  }}
                  disabled={loading}
                />
                <div style={{ display: 'flex', gap: 12, marginTop: 20, justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    {isDemoMode && (
                      <span style={{
                        fontSize: 12,
                        color: '#5a7a66',
                        fontStyle: 'italic'
                      }}>
                        Try: "Irrigating in the morning" or "Cold storage running"
                      </span>
                    )}
                  </div>
                  <button
                    type="submit"
                    disabled={loading || !inputValue.trim()}
                    style={{
                      padding: '14px 32px',
                      borderRadius: 10,
                      backgroundColor: inputValue.trim() && !loading ? '#2d6a4f' : '#d4e0d9',
                      color: '#fff',
                      border: 'none',
                      fontWeight: 600,
                      fontSize: 15,
                      cursor: inputValue.trim() && !loading ? 'pointer' : 'not-allowed',
                      transition: 'background 0.2s'
                    }}
                    onMouseOver={(e) => {
                      if (inputValue.trim() && !loading) {
                        e.target.style.backgroundColor = '#1f4d38';
                      }
                    }}
                    onMouseOut={(e) => {
                      if (inputValue.trim() && !loading) {
                        e.target.style.backgroundColor = '#2d6a4f';
                      }
                    }}
                  >
                    {loading ? 'Recording...' : 'Analyze Activity'}
                  </button>
                </div>
              </form>
            </div>

            <section style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: 16,
              marginBottom: 32
            }}>
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: 16,
                padding: '24px',
                border: '1px solid #e0e8e4',
                minHeight: 150
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#2d6a4f', marginBottom: 12 }}>Who uses this system</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#172d20', marginBottom: 12 }}>Communities</div>
                <div style={{ fontSize: 14, color: '#4a6b57' }}>Record real activity in the field and make demand visible.</div>
              </div>
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: 16,
                padding: '24px',
                border: '1px solid #e0e8e4',
                minHeight: 150
              }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#172d20', marginBottom: 12 }}>Planners</div>
                <div style={{ fontSize: 14, color: '#4a6b57' }}>Understand where demand exists and where capacity is needed.</div>
              </div>
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: 16,
                padding: '24px',
                border: '1px solid #e0e8e4',
                minHeight: 150
              }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#172d20', marginBottom: 12 }}>Investors</div>
                <div style={{ fontSize: 14, color: '#4a6b57' }}>Identify infrastructure opportunities backed by real coordination signals.</div>
              </div>
            </section>

            <section style={{
              marginBottom: 32,
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: 16
            }}>
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: 16,
                padding: '24px',
                border: '1px solid #e0e8e4'
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#2d6a4f', marginBottom: 12 }}>Why it matters</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#172d20', marginBottom: 12 }}>Reduce risk, improve planning, grow economies.</div>
                <div style={{ display: 'grid', gap: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    <span style={{ width: 28, height: 28, borderRadius: 8, backgroundColor: '#e7f6f1', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#2d6a4f', fontWeight: 700 }}>✓</span>
                    <div style={{ color: '#4a6b57', fontSize: 14 }}>Reduce failed investments with verified demand signals.</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    <span style={{ width: 28, height: 28, borderRadius: 8, backgroundColor: '#eef5fb', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#175a9f', fontWeight: 700 }}>⇄</span>
                    <div style={{ color: '#4a6b57', fontSize: 14 }}>Improve infrastructure planning with clear coordination evidence.</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    <span style={{ width: 28, height: 28, borderRadius: 8, backgroundColor: '#fff3e0', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#b9690b', fontWeight: 700 }}>↑</span>
                    <div style={{ color: '#4a6b57', fontSize: 14 }}>Support real economic growth through demand-led investment.</div>
                  </div>
                </div>
              </div>
            </section>

            {/* Status Message */}
            {message && (
              <div style={{
                padding: '16px 18px',
                borderRadius: 12,
                backgroundColor: message.includes('✓') ? '#ecf7ef' : '#fef3e0',
                color: message.includes('✓') ? '#1f4d2b' : '#b8860b',
                marginBottom: 24,
                fontSize: 14,
                fontWeight: 500,
                border: `1px solid ${message.includes('✓') ? '#d8f0d3' : '#fce8d4'}`
              }}>
                {message}
              </div>
            )}
          </section>
        )}

        {/* Demo Banner */}
        {isDemoMode && !reportData && (
          <div style={{
            backgroundColor: '#fffbf0',
            borderRadius: 12,
            padding: '16px 18px',
            marginBottom: 32,
            border: '1px solid #fce8d4',
            display: 'flex',
            flexDirection: 'column',
            gap: 16
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
              <span style={{ fontSize: 18, flexShrink: 0 }}>ℹ️</span>
              <div style={{ fontSize: 13, color: '#5a7a66', lineHeight: 1.6 }}>
                <div style={{ fontWeight: 600, color: '#172d20', marginBottom: 4 }}>Sample Demonstration</div>
                {DEMO_MODE_MESSAGE}
              </div>
            </div>
            <button
              onClick={handleDownloadSampleReport}
              type="button"
              style={{
                alignSelf: 'flex-start',
                padding: '12px 20px',
                borderRadius: 10,
                backgroundColor: '#2d6a4f',
                color: '#fff',
                border: 'none',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Download sample prospectus
            </button>
          </div>
        )}

        {/* Insights Response Section */}
        {displayedSummary && !reportData && (
          <section ref={insightsRef} style={{
            marginBottom: 48,
            animation: 'slideUp 0.3s ease-out'
          }}>
            {/* Assistant Response - Structured Reasoning Card */}
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

            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: 16,
              border: '1px solid #d4e0d9',
              padding: '24px',
              marginBottom: 24
            }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#2d6a4f', marginBottom: 12 }}>Based on current activity</div>
              <div style={{ fontSize: 16, color: '#172d20', marginBottom: 18, lineHeight: 1.6 }}>
                {displayedSummary?.key_finding || 'There is emerging demand for productive activity that can guide infrastructure decisions.'}
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
                    cursor: reportLoading ? 'not-allowed' : 'pointer'
                  }}
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
                    cursor: 'pointer'
                  }}
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
                    cursor: 'pointer'
                  }}
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
                  {displayedSummary?.signal_count || 0}
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
                  {displayedSummary?.total_patterns || 0}
                </div>
                <div style={{ fontSize: 13, color: '#5a7a66' }}>
                  Patterns detected
                </div>
              </div>
            </div>

            {/* Activities Detected */}
            {displayedSummary?.productive_activities_detected && displayedSummary.productive_activities_detected.length > 0 && (
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
                  {displayedSummary.productive_activities_detected.map((activity, idx) => (
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
            {displayedSummary?.demand_patterns && displayedSummary.demand_patterns.length > 0 && (
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
                  {displayedSummary.demand_patterns.map((pattern, idx) => (
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
            {displayedSummary?.infrastructure_gaps && displayedSummary.infrastructure_gaps.length > 0 && (
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
                  {displayedSummary.infrastructure_gaps.slice(0, 3).map((gap, idx) => (
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
              {reportLoading ? '⏳ Creating Investment Report...' : isDemoMode ? '📄 Create Sample Investment Report' : '📄 Create Investment Report'}
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
        <section style={{
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
      </main>

      {/* Footer */}
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
      `}</style>
    </div>
  );
}
