'use client';

import { useState, useEffect, useRef } from 'react';

const DEMO_SIGNAL_THRESHOLD = 5;
const DEMO_MODE_MESSAGE = 'This is a demonstration of how the system works when more people are using it.';

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
  const inputRef = useRef(null);

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const BACKEND_BASE = BASE_URL.replace(/\/api\/v1$/, '');
  const isDemoMode = !summary || summary.signal_count < DEMO_SIGNAL_THRESHOLD;
  const displayedSummary = isDemoMode ? SAMPLE_SUMMARY : summary;

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
    window.location.href = '/sample-prospectus.pdf';
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8faf8', color: '#172d20' }}>
      {/* Header */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e0e8e4',
        boxShadow: '0 2px 8px rgba(23, 45, 32, 0.04)'
      }}>
        <div style={{
          maxWidth: 1400,
          margin: '0 auto',
          padding: '16px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 36,
              height: 36,
              backgroundColor: '#2d6a4f',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 700,
              fontSize: 18
            }}>
              K
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#172d20' }}>Kulima OS</div>
              <div style={{ fontSize: 11, color: '#5a7a66' }}>Community Activity System</div>
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
                backgroundColor: '#f8faf8',
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
                fontSize: 12,
                fontWeight: 600
              }}>
                Demo Mode
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: 1400, margin: '0 auto', padding: '32px 24px 64px' }}>
        {/* Hero Section */}
        <section style={{
          backgroundColor: '#ffffff',
          borderRadius: 16,
          padding: '40px 48px',
          marginBottom: 48,
          boxShadow: '0 4px 16px rgba(23, 45, 32, 0.06)',
          borderLeft: '4px solid #2d6a4f'
        }}>
          <div style={{ maxWidth: 800 }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 14px',
              borderRadius: 999,
              backgroundColor: '#e7f6f1',
              color: '#2d6a4f',
              fontSize: 12,
              fontWeight: 600,
              marginBottom: 16
            }}>
              ✓ Real Activity • Real Insights • Real Decisions
            </div>

            <h1 style={{
              fontSize: 42,
              lineHeight: 1.2,
              margin: 0,
              fontWeight: 700,
              color: '#172d20'
            }}>
              Turn community activity into investment-ready intelligence
            </h1>

            <p style={{
              fontSize: 18,
              lineHeight: 1.6,
              color: '#4a6b57',
              margin: '20px 0 0',
              maxWidth: 720
            }}>
              Kulima OS collects real activities from farmers, traders, and communities using simple messages. 
              It transforms this into clear patterns and reports that help policymakers, investors, and planners 
              understand where real demand exists.
            </p>

            <div style={{
              display: 'flex',
              gap: 12,
              marginTop: 28,
              flexWrap: 'wrap'
            }}>
              <button
                onClick={() => inputRef.current?.focus()}
                style={{
                  padding: '12px 24px',
                  borderRadius: 10,
                  backgroundColor: '#2d6a4f',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 600,
                  fontSize: 15,
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#1f4d38'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#2d6a4f'}
              >
                → Record Activity
              </button>
              <button
                onClick={handleGenerateReport}
                disabled={reportLoading}
                style={{
                  padding: '12px 24px',
                  borderRadius: 10,
                  backgroundColor: '#e7f6f1',
                  color: '#2d6a4f',
                  border: '2px solid #2d6a4f',
                  fontWeight: 600,
                  fontSize: 15,
                  cursor: 'pointer'
                }}
              >
                {reportLoading ? 'Creating...' : '↓ Create Report'}
              </button>
              <button
                onClick={handleDownloadSampleReport}
                style={{
                  padding: '12px 24px',
                  borderRadius: 10,
                  backgroundColor: '#f5f5f5',
                  color: '#172d20',
                  border: '1px solid #d4e0d9',
                  fontWeight: 600,
                  fontSize: 15,
                  cursor: 'pointer'
                }}
              >
                📄 Sample Report
              </button>
            </div>
          </div>
        </section>

        {/* Demo Mode Banner */}
        {isDemoMode && (
          <div style={{
            backgroundColor: '#fffbf0',
            borderRadius: 12,
            padding: '16px 20px',
            marginBottom: 32,
            border: '1px solid #fce8d4',
            display: 'flex',
            alignItems: 'center',
            gap: 12
          }}>
            <span style={{ fontSize: 18 }}>ℹ️</span>
            <div>
              <div style={{ fontWeight: 600, color: '#172d20', fontSize: 14 }}>{DEMO_MODE_MESSAGE}</div>
              <div style={{ fontSize: 13, color: '#6b8575', marginTop: 4 }}>
                The system shows sample insights and patterns to demonstrate how it works. Once real data arrives, you'll see actual community activities.
              </div>
            </div>
          </div>
        )}

        {/* Status Message */}
        {message && (
          <div style={{
            padding: '14px 18px',
            borderRadius: 10,
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

        {/* Two-Column Layout: Input + Activity Feed (Left) | Insights (Right) */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 32,
          alignItems: 'start'
        }}>
          {/* LEFT: Input & Activity Feed */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Input Box */}
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: 14,
              padding: 24,
              boxShadow: '0 2px 8px rgba(23, 45, 32, 0.04)',
              border: '1px solid #e0e8e4'
            }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#2d6a4f', marginBottom: 12 }}>
                What is happening right now?
              </label>
              <form onSubmit={handleSubmitActivity}>
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Type what is happening… e.g. 'We are irrigating maize in the morning' or 'Grinding crops at the mill'"
                  style={{
                    width: '100%',
                    padding: '14px',
                    borderRadius: 10,
                    border: '1px solid #d4e0d9',
                    backgroundColor: '#f8faf8',
                    fontSize: 14,
                    fontFamily: 'inherit',
                    color: '#172d20',
                    resize: 'vertical',
                    minHeight: 100,
                    boxSizing: 'border-box'
                  }}
                  disabled={loading}
                />
                <div style={{ display: 'flex', gap: 12, marginTop: 14 }}>
                  <button
                    type="submit"
                    disabled={loading || !inputValue.trim()}
                    style={{
                      flex: 1,
                      padding: '12px 18px',
                      borderRadius: 10,
                      backgroundColor: inputValue.trim() ? '#2d6a4f' : '#d4e0d9',
                      color: '#fff',
                      border: 'none',
                      fontWeight: 600,
                      fontSize: 14,
                      cursor: inputValue.trim() ? 'pointer' : 'not-allowed',
                      transition: 'background 0.2s'
                    }}
                  >
                    {loading ? 'Recording...' : 'Record Activity'}
                  </button>
                </div>
              </form>
            </div>

            {/* Activity Feed */}
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: 14,
              padding: 24,
              boxShadow: '0 2px 8px rgba(23, 45, 32, 0.04)',
              border: '1px solid #e0e8e4'
            }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#2d6a4f', marginBottom: 16 }}>
                Recent Activity ({(isDemoMode ? SAMPLE_ACTIVITY_FEED : activityFeed).length})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {(isDemoMode ? SAMPLE_ACTIVITY_FEED : activityFeed).slice(0, 6).map(item => (
                  <div key={item.id} style={{
                    padding: '12px 14px',
                    borderRadius: 10,
                    backgroundColor: '#f8faf8',
                    border: '1px solid #e0e8e4',
                    fontSize: 13
                  }}>
                    <div style={{ fontWeight: 600, color: '#172d20' }}>
                      {item.activity} • {item.time}
                    </div>
                    <div style={{ color: '#5a7a66', marginTop: 4, fontSize: 12 }}>
                      {item.description}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT: Insights Panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Key Finding */}
            <div style={{
              backgroundColor: '#e7f6f1',
              borderRadius: 14,
              padding: 24,
              border: '1px solid #b8e6d5'
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#2d6a4f', marginBottom: 8 }}>
                KEY INSIGHT
              </div>
              <div style={{
                fontSize: 18,
                fontWeight: 700,
                color: '#1f4d38',
                lineHeight: 1.4
              }}>
                {displayedSummary?.key_finding || 'Building coordination intelligence...'}
              </div>
            </div>

            {/* Quick Stats */}
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: 14,
              padding: 20,
              boxShadow: '0 2px 8px rgba(23, 45, 32, 0.04)',
              border: '1px solid #e0e8e4'
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div style={{ textAlign: 'center', paddingBottom: 16, borderBottom: '1px solid #e0e8e4' }}>
                  <div style={{ fontSize: 32, fontWeight: 700, color: '#2d6a4f' }}>
                    {displayedSummary?.signal_count || 0}
                  </div>
                  <div style={{ fontSize: 12, color: '#5a7a66', marginTop: 4 }}>
                    Activities recorded
                  </div>
                </div>
                <div style={{ textAlign: 'center', paddingBottom: 16, borderBottom: '1px solid #e0e8e4' }}>
                  <div style={{ fontSize: 32, fontWeight: 700, color: '#2d6a4f' }}>
                    {displayedSummary?.total_patterns || 0}
                  </div>
                  <div style={{ fontSize: 12, color: '#5a7a66', marginTop: 4 }}>
                    Patterns found
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#2d6a4f' }}>
                    {displayedSummary?.high_confidence_patterns || 0}
                  </div>
                  <div style={{ fontSize: 12, color: '#5a7a66', marginTop: 4 }}>
                    High confidence
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#2d6a4f' }}>
                    {displayedSummary?.productive_activities_detected?.length || 0}
                  </div>
                  <div style={{ fontSize: 12, color: '#5a7a66', marginTop: 4 }}>
                    Activity types
                  </div>
                </div>
              </div>
            </div>

            {/* Activity Types */}
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: 14,
              padding: 20,
              boxShadow: '0 2px 8px rgba(23, 45, 32, 0.04)',
              border: '1px solid #e0e8e4'
            }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#2d6a4f', marginBottom: 14 }}>
                Activities Detected
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {displayedSummary?.productive_activities_detected?.map((activity, idx) => (
                  <div key={idx} style={{
                    padding: '10px 12px',
                    borderRadius: 8,
                    backgroundColor: '#f8faf8',
                    border: '1px solid #e0e8e4',
                    fontSize: 13,
                    fontWeight: 500,
                    color: '#2d6a4f',
                    textTransform: 'capitalize'
                  }}>
                    ✓ {activity}
                  </div>
                ))}
              </div>
            </div>

            {/* Demand Patterns */}
            {displayedSummary?.demand_patterns && displayedSummary.demand_patterns.length > 0 && (
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: 14,
                padding: 20,
                boxShadow: '0 2px 8px rgba(23, 45, 32, 0.04)',
                border: '1px solid #e0e8e4'
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#2d6a4f', marginBottom: 14 }}>
                  Demand Patterns
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {displayedSummary.demand_patterns.map((pattern, idx) => (
                    <div key={idx} style={{
                      padding: '12px',
                      borderRadius: 8,
                      backgroundColor: '#f8faf8',
                      border: '1px solid #e0e8e4',
                      fontSize: 12
                    }}>
                      <div style={{ fontWeight: 600, color: '#172d20' }}>
                        {pattern.activity}
                      </div>
                      <div style={{ color: '#5a7a66', marginTop: 4 }}>
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
                borderRadius: 14,
                padding: 20,
                border: '1px solid #fce8d4'
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#b8860b', marginBottom: 12 }}>
                  ⚡ Infrastructure Needs
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {displayedSummary.infrastructure_gaps.slice(0, 3).map((gap, idx) => (
                    <div key={idx} style={{
                      fontSize: 12,
                      color: '#8b6914',
                      lineHeight: 1.4
                    }}>
                      • {gap}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Report Section */}
        {reportData && (
          <section style={{
            marginTop: 48,
            backgroundColor: '#ffffff',
            borderRadius: 14,
            padding: 32,
            boxShadow: '0 4px 16px rgba(23, 45, 32, 0.06)',
            border: '2px solid #2d6a4f'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 24
            }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 28, fontWeight: 700, color: '#172d20' }}>
                  ✓ Investment Report Ready
                </h2>
                <p style={{ margin: '8px 0 0', color: '#5a7a66', fontSize: 14 }}>
                  Your demand signal prospectus is ready for review by investors and planners.
                </p>
              </div>
              <a
                href={reportData?.pdf_url ? `${BACKEND_BASE}${reportData.pdf_url}` : '#'}
                download
                style={{
                  padding: '12px 24px',
                  borderRadius: 10,
                  backgroundColor: '#2d6a4f',
                  color: '#fff',
                  fontWeight: 600,
                  textDecoration: 'none',
                  cursor: 'pointer'
                }}
              >
                ↓ Download PDF
              </a>
            </div>
            <div style={{
              padding: 20,
              borderRadius: 10,
              backgroundColor: '#f8faf8',
              border: '1px solid #e0e8e4',
              fontSize: 13,
              color: '#5a7a66',
              lineHeight: 1.6
            }}>
              <strong>Report includes:</strong>
              <ul style={{ margin: '10px 0 0', paddingLeft: 20 }}>
                <li>Executive summary of demand patterns</li>
                <li>Activities observed in {zone}</li>
                <li>Timing and frequency of activities</li>
                <li>Infrastructure gaps identified</li>
                <li>Investment opportunity analysis</li>
                <li>Confidence scores and next steps</li>
              </ul>
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer style={{
        backgroundColor: '#2d6a4f',
        color: '#e0e8e4',
        padding: '32px 24px',
        marginTop: 64
      }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 32, marginBottom: 32 }}>
            <div>
              <div style={{ fontWeight: 700, color: '#fff', marginBottom: 12 }}>Kulima OS</div>
              <div style={{ fontSize: 13, lineHeight: 1.6 }}>
                Community Activity System for infrastructure planning and decision-making.
              </div>
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#fff', marginBottom: 12 }}>Our Principle</div>
              <div style={{ fontSize: 13 }}>
                Food Everywhere, For Everyone, At All Times
              </div>
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#fff', marginBottom: 12 }}>Status</div>
              <div style={{ fontSize: 13 }}>
                <div>✓ Pilot Active</div>
                <div>✓ Data Flowing</div>
                <div>✓ Reports Ready</div>
              </div>
            </div>
          </div>
          <div style={{
            borderTop: '1px solid rgba(224, 232, 228, 0.3)',
            paddingTop: 20,
            fontSize: 12,
            color: '#b8d4c5'
          }}>
            © 2026 Kulima Africa. Built for better decisions.
          </div>
        </div>
      </footer>
    </div>
  );
}
