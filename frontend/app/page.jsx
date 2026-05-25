'use client';

import { useState, useEffect } from 'react';

const DEMO_SIGNAL_THRESHOLD = 5;

const SAMPLE_SUMMARY = {
  zone: 'MZUZU',
  signal_count: 4,
  total_patterns: 3,
  high_confidence_patterns: 2,
  moderate_confidence_patterns: 1,
  zones_with_coordinated_demand: ['MZUZU'],
  productive_activities_detected: ['irrigation', 'milling', 'cold storage'],
  key_finding: 'Demo activity shows real demand from farming and storage in the community.',
  updated_at: new Date().toISOString()
};

const SAMPLE_SIGNALS = [
  { time: '2026-05-25 09:15', activity: 'irrigation', zone: 'MZUZU', source: 'web' },
  { time: '2026-05-25 09:05', activity: 'milling', zone: 'MZUZU', source: 'whatsapp' },
  { time: '2026-05-25 08:50', activity: 'cold storage', zone: 'MZUZU', source: 'whatsapp' },
  { time: '2026-05-25 08:30', activity: 'trading', zone: 'MZUZA', source: 'web' }
];

const SAMPLE_WHATSAPP_FEED = [
  { time: '09:05', message: 'Maize milling in Mzuzu this morning', sender: '+265 999 123 456' },
  { time: '08:50', message: 'Cold storage cycle started in Mzuzu', sender: '+265 888 234 567' },
  { time: '08:15', message: 'Irrigation pump active in Mzuzu', sender: '+265 777 345 678' }
];

export default function Home() {
  const [zone, setZone] = useState('MZUZU');
  const [summary, setSummary] = useState(null);
  const [signalHistory, setSignalHistory] = useState([]);
  const [whatsappFeed, setWhatsappFeed] = useState(SAMPLE_WHATSAPP_FEED);
  const [reportData, setReportData] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [signalLoading, setSignalLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [signalForm, setSignalForm] = useState({ activity_type: '', time_window: '' });

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const BACKEND_BASE = BASE_URL.replace(/\/api\/v1$/, '');
  const SAMPLE_PROSPECTUS_PATH = '/sample-prospectus.pdf';

  const isDemoMode = !!(!summary || summary.signal_count < DEMO_SIGNAL_THRESHOLD);

  useEffect(() => {
    fetchSummary();
  }, [zone]);

  const fetchSummary = async () => {
    setLoading(true);
    setMessage('');
    try {
      const response = await fetch(`${BASE_URL}/summary/${zone}`);
      const data = await response.json();
      if (data.status === 'success') {
        setSummary(data.data);
      } else {
        setSummary({ ...SAMPLE_SUMMARY, zone });
      }
    } catch (error) {
      console.error('Error fetching summary:', error);
      setSummary({ ...SAMPLE_SUMMARY, zone });
      setMessage('Unable to fetch live summary. Showing demo data.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignalSubmit = async (event) => {
    event.preventDefault();
    setSignalLoading(true);
    setMessage('');

    if (!signalForm.activity_type || !signalForm.time_window) {
      setMessage('Please select both activity and time window.');
      setSignalLoading(false);
      return;
    }

    try {
      const response = await fetch(`${BASE_URL}/signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone, activity_type: signalForm.activity_type, time_window: signalForm.time_window, source: 'web', user_id: 'web_demo_user' })
      });
      const data = await response.json();

      if (data.status === 'success') {
        setMessage('Activity recorded successfully!');
        setSignalForm({ activity_type: '', time_window: '' });
        setSignalHistory((prev) => [
          { time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), activity: signalForm.activity_type, zone, source: 'web' },
          ...prev
        ].slice(0, 6));
        await fetchSummary();
      } else {
        setMessage(data.message || data.data?.error || 'Failed to record activity.');
      }
    } catch (error) {
      console.error('Error recording activity:', error);
      setMessage('Unable to record activity. Please try again.');
    } finally {
      setSignalLoading(false);
    }
  };

  const handleGenerateProspectus = async () => {
    setReportLoading(true);
    setReportData(null);
    setMessage('');

    try {
      const response = await fetch(`${BASE_URL}/generate-prospectus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone, user_id: 'web_demo_user' })
      });
      const data = await response.json();

      if (data.status === 'success') {
        setReportData(data.data);
        setMessage('Real prospectus generated successfully.');
      } else {
        setMessage(data.message || data.data?.error || 'Failed to create investment report.');
      }
    } catch (error) {
      console.error('Error generating prospectus:', error);
      setMessage('Unable to generate prospectus. Please try again.');
    } finally {
      setReportLoading(false);
    }
  };

  const coordinationStatus = (() => {
    if (!summary) return 'Loading';
    if (summary.high_confidence_patterns >= 2) return 'High';
    if (summary.moderate_confidence_patterns >= 1) return 'Medium';
    return 'Low';
  })();

  const activityTrend = (() => {
    const count = isDemoMode ? SAMPLE_SIGNALS.length : summary?.signal_count || 0;
    return [count - 2, count - 1, count, count + 1].map((value, index) => ({ label: `Day ${index + 1}`, value: Math.max(value, 1) }));
  })();

  const prospectusUrl = reportData?.pdf_url ? `${BACKEND_BASE}${reportData.pdf_url}` : null;
  const displayedSummary = isDemoMode ? { ...SAMPLE_SUMMARY, zone } : summary;
  const recentSignals = signalHistory.length ? signalHistory : SAMPLE_SIGNALS;
  const latestWhatsApp = whatsappFeed.slice(0, 3);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f7fbf7', color: '#173f29' }}>
      <header style={{ borderBottom: '1px solid #e6f0ea', backgroundColor: '#ffffff', position: 'sticky', top: 0, zIndex: 20 }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '18px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <img src="/kulima-logo.svg" alt="Kulima Africa" width={140} height={40} />
            <span style={{ fontSize: 14, fontWeight: 600, color: '#2d6a4f' }}>Community Activity</span>
          </div>
          <nav style={{ display: 'flex', alignItems: 'center', gap: 22, flexWrap: 'wrap', fontSize: 14, color: '#2d6a4f' }}>
            <a href="#dashboard" style={{ color: '#2d6a4f', textDecoration: 'none' }}>Dashboard</a>
            <a href="#submit" style={{ color: '#2d6a4f', textDecoration: 'none' }}>Record Activity</a>
            <a href="#prospectus" style={{ color: '#2d6a4f', textDecoration: 'none' }}>Reports</a>
            <a href="#about" style={{ color: '#2d6a4f', textDecoration: 'none' }}>About</a>
          </nav>
        </div>
      </header>

      <main style={{ maxWidth: 1200, margin: '0 auto', padding: '40px 24px 80px' }}>
        <section style={{ backgroundColor: '#ffffff', borderRadius: 28, padding: '48px 40px', boxShadow: '0 30px 80px rgba(22, 63, 41, 0.08)', marginBottom: 40 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 32, alignItems: 'center' }}>
            <div>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, marginBottom: 18, padding: '8px 14px', borderRadius: 999, backgroundColor: '#ecf7ef', color: '#2d6a4f', fontWeight: 700, letterSpacing: 0.5, fontSize: 13 }}>
                Demo Ready • Investor Grade
              </div>
              <h1 style={{ fontSize: 52, lineHeight: 1.05, margin: 0 }}>Kulima OS helps Malawi make better farming and infrastructure decisions using real activity data from communities.</h1>
              <p style={{ marginTop: 22, fontSize: 18, lineHeight: 1.8, maxWidth: 680, color: '#3b5a44' }}>
                It turns community activity into clear insights and reports so leaders can invest where it matters most.
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14, marginTop: 30 }}>
                <a href="#submit" style={{ padding: '14px 24px', borderRadius: 12, backgroundColor: '#2d6a4f', color: '#ffffff', fontWeight: 700, textDecoration: 'none' }}>Record Activity</a>
                <a href="#dashboard" style={{ padding: '14px 24px', borderRadius: 12, backgroundColor: '#e8f7ee', color: '#2d6a4f', fontWeight: 700, textDecoration: 'none' }}>View Live Dashboard</a>
                <a href="/sample-prospectus.pdf" download style={{ padding: '14px 24px', borderRadius: 12, backgroundColor: '#f1f9f1', color: '#2d6a4f', fontWeight: 700, textDecoration: 'none' }}>Download Sample Prospectus</a>
              </div>
            </div>
            <div style={{ backgroundColor: '#eff7ee', borderRadius: 24, padding: 28, minHeight: 300, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <span style={{ display: 'inline-block', padding: '8px 14px', borderRadius: 999, backgroundColor: '#d8f0d3', color: '#22543d', fontWeight: 700, fontSize: 13 }}>Live Pilot Demo</span>
                <h2 style={{ marginTop: 24, fontSize: 24 }}>Trusted by planners, built for investors</h2>
                <p style={{ marginTop: 16, color: '#285238', lineHeight: 1.7 }}>
                  Kulima OS collects real activity data and turns it into clear findings for decisions on farming, energy, and markets.
                </p>
              </div>
              <div style={{ display: 'grid', gap: 12, marginTop: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#ffffff', padding: '18px 20px', borderRadius: 18, boxShadow: '0 14px 40px rgba(45, 106, 79, 0.08)' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#4f7942' }}>Infrastructure Readiness</div>
                    <div style={{ marginTop: 8, fontSize: 20, fontWeight: 700 }}>95%</div>
                  </div>
                  <div style={{ color: '#2d6a4f', fontSize: 12 }}>Demo Insights</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#ffffff', padding: '18px 20px', borderRadius: 18, boxShadow: '0 14px 40px rgba(45, 106, 79, 0.08)' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#4f7942' }}>Report readiness</div>
                    <div style={{ marginTop: 8, fontSize: 20, fontWeight: 700 }}>High</div>
                  </div>
                  <div style={{ color: '#2d6a4f', fontSize: 12 }}>Investor-ready sample</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="dashboard" style={{ marginBottom: 40 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
            <div>
              <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#2d6a4f' }}>Dashboard</p>
              <h2 style={{ margin: '8px 0 0', fontSize: 32 }}>Infrastructure demand snapshot</h2>
            </div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <button onClick={handleGenerateProspectus} disabled={reportLoading} style={{ padding: '14px 20px', borderRadius: 12, backgroundColor: '#2d6a4f', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer' }}>{reportLoading ? 'Creating...' : 'Create Investment Report'}</button>
              <a href="/sample-prospectus.pdf" download style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: '14px 20px', borderRadius: 12, backgroundColor: '#eff7ee', color: '#2d6a4f', textDecoration: 'none', fontWeight: 700 }}>Download Sample Prospectus</a>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20, marginBottom: 24 }}>
            {[
              { title: 'Total Signals', value: displayedSummary?.signal_count ?? '—', subtitle: isDemoMode ? 'Demo and live inputs' : 'Live inputs' },
              { title: 'Active Zone', value: zone, subtitle: 'Operational region' },
              { title: 'Detected Activities', value: displayedSummary?.productive_activities_detected?.length ?? '—', subtitle: 'Key activity categories' },
              { title: 'Strength of demand', value: coordinationStatus, subtitle: 'Strength of demand' }
            ].map((card) => (
              <div key={card.title} style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: '24px 26px', boxShadow: '0 24px 50px rgba(22, 63, 41, 0.08)' }}>
                <p style={{ margin: 0, fontSize: 13, fontWeight: 700, letterSpacing: 0.5, color: '#4f7942' }}>{card.title}</p>
                <p style={{ margin: '18px 0 0', fontSize: 36, fontWeight: 800, color: '#173f29' }}>{card.value}</p>
                <p style={{ margin: '12px 0 0', fontSize: 14, color: '#516a52' }}>{card.subtitle}</p>
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 20, alignItems: 'start' }}>
            <div style={{ borderRadius: 24, backgroundColor: '#ffffff', padding: 28, boxShadow: '0 24px 50px rgba(22, 63, 41, 0.08)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div>
                  <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#2d6a4f' }}>Activity Trends</p>
                  <h3 style={{ margin: '10px 0 0', fontSize: 22 }}>Signal growth over time</h3>
                </div>
                <span style={{ padding: '6px 12px', borderRadius: 999, backgroundColor: '#ecf7ef', color: '#2d6a4f', fontWeight: 700, fontSize: 12 }}>{isDemoMode ? 'Demo Mode' : 'Live Mode'}</span>
              </div>
              <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', height: 200 }}>
                {activityTrend.map((bar) => (
                  <div key={bar.label} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{ width: '100%', minHeight: 40, backgroundColor: '#d8f0d3', borderRadius: 16, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', paddingBottom: 8, height: `${72 + bar.value * 8}px` }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: '#1b4332' }}>{bar.value}</span>
                    </div>
                    <span style={{ marginTop: 12, fontSize: 13, color: '#4f7942' }}>{bar.label}</span>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ borderRadius: 24, backgroundColor: '#ffffff', padding: 28, boxShadow: '0 24px 50px rgba(22, 63, 41, 0.08)' }}>
                  <h3 style={{ margin: 0, fontSize: 20, color: '#173f29' }}>Community updates</h3>
                  <p style={{ margin: '10px 0 20px', color: '#516a52' }}>The latest activity shared by the community.</p>
              <div style={{ display: 'grid', gap: 14 }}>
                {latestWhatsApp.map((item, index) => (
                  <div key={index} style={{ padding: 18, borderRadius: 18, backgroundColor: '#f6fbf6', border: '1px solid #e7f3e8' }}>
                    <p style={{ margin: 0, fontWeight: 700, color: '#194d33' }}>{item.message}</p>
                    <p style={{ margin: '8px 0 0', fontSize: 13, color: '#4f7942' }}>{item.sender} • {item.time}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="submit" style={{ marginBottom: 40, display: 'grid', gap: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, alignItems: 'center' }}>
            <div>
              <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#2d6a4f' }}>Record Activity</p>
              <h2 style={{ margin: '10px 0 0', fontSize: 32 }}>Capture real community activity</h2>
            </div>
            <div style={{ color: '#4f7942', fontWeight: 700 }}>{displayedSummary?.signal_count ?? 0} signals</div>
          </div>
          {message && (
            <div style={{ padding: 20, borderRadius: 18, backgroundColor: '#eff7ee', border: '1px solid #d8f0d3', color: '#1f4d2b' }}>{message}</div>
          )}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24 }}>
            <form onSubmit={handleSignalSubmit} style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 32, boxShadow: '0 24px 50px rgba(22, 63, 41, 0.08)' }}>
              <div style={{ display: 'grid', gap: 18 }}>
                <label style={{ display: 'grid', gap: 8, fontWeight: 700, color: '#285238' }}>
                  Zone
                  <select value={zone} onChange={(e) => setZone(e.target.value)} style={{ width: '100%', padding: '16px 18px', borderRadius: 14, border: '1px solid #d8e6d6', backgroundColor: '#f9fdf9' }}>
                    {['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'].map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                </label>

                <label style={{ display: 'grid', gap: 8, fontWeight: 700, color: '#285238' }}>
                  Activity Type
                  <select value={signalForm.activity_type} onChange={(e) => setSignalForm((prev) => ({ ...prev, activity_type: e.target.value }))} style={{ width: '100%', padding: '16px 18px', borderRadius: 14, border: '1px solid #d8e6d6', backgroundColor: '#f9fdf9' }}>
                    <option value="">Select activity...</option>
                    <option value="irrigation">Irrigation</option>
                    <option value="milling">Milling</option>
                    <option value="cold storage">Cold Storage</option>
                    <option value="welding">Welding</option>
                    <option value="trading">Trading</option>
                  </select>
                </label>

                <label style={{ display: 'grid', gap: 8, fontWeight: 700, color: '#285238' }}>
                  Time Window
                  <select value={signalForm.time_window} onChange={(e) => setSignalForm((prev) => ({ ...prev, time_window: e.target.value }))} style={{ width: '100%', padding: '16px 18px', borderRadius: 14, border: '1px solid #d8e6d6', backgroundColor: '#f9fdf9' }}>
                    <option value="">Select time window...</option>
                    <option value="morning">Morning</option>
                    <option value="midday">Midday</option>
                    <option value="afternoon">Afternoon</option>
                    <option value="evening">Evening</option>
                  </select>
                </label>

                <button type="submit" disabled={signalLoading} style={{ padding: '16px 22px', borderRadius: 14, backgroundColor: '#2d6a4f', color: '#ffffff', fontWeight: 700, border: 'none', cursor: signalLoading ? 'not-allowed' : 'pointer' }}>
                  {signalLoading ? 'Recording...' : 'Record Activity'}
                </button>
              </div>
            </form>

            <aside style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 28, boxShadow: '0 24px 50px rgba(22, 63, 41, 0.08)' }}>
              <h3 style={{ margin: 0, fontSize: 22, color: '#173f29' }}>Recent signal activity</h3>
              <div style={{ marginTop: 20, display: 'grid', gap: 16 }}>
                {recentSignals.map((item, index) => (
                  <div key={index} style={{ padding: 18, borderRadius: 18, backgroundColor: '#eff7ee', border: '1px solid #e1f1de' }}>
                    <p style={{ margin: '0 0 8px', fontWeight: 700, color: '#194d33' }}>{item.activity}</p>
                    <p style={{ margin: 0, color: '#3f5f48', fontSize: 14 }}>{item.zone} • {item.time}</p>
                    <p style={{ margin: '8px 0 0', fontSize: 13, color: '#4f7942' }}>{item.source === 'whatsapp' ? 'WhatsApp' : 'Web'}</p>
                  </div>
                ))}
              </div>
            </aside>
          </div>
        </section>

        <section id="prospectus" style={{ marginBottom: 40, display: 'grid', gap: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, alignItems: 'center' }}>
            <div>
              <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#2d6a4f' }}>Reports</p>
              <h2 style={{ margin: '10px 0 0', fontSize: 32 }}>Download a report that shows where demand is growing and where investment is needed.</h2>
            </div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <a href="/sample-prospectus.pdf" download style={{ padding: '14px 20px', borderRadius: 12, backgroundColor: '#eff7ee', color: '#2d6a4f', textDecoration: 'none', fontWeight: 700 }}>Download Sample Prospectus</a>
              <button onClick={handleGenerateProspectus} disabled={reportLoading} style={{ padding: '14px 20px', borderRadius: 12, backgroundColor: '#2d6a4f', color: '#ffffff', border: 'none', fontWeight: 700, cursor: 'pointer' }}>{reportLoading ? 'Creating...' : 'Create Investment Report'}</button>
            </div>
          </div>
          <div style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 32, boxShadow: '0 24px 50px rgba(22, 63, 41, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 18 }}>
              <div>
                <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#4f7942' }}>Report status</p>
                <h3 style={{ margin: '10px 0 0', fontSize: 24 }}>Ready for investor review</h3>
              </div>
              <div style={{ padding: '10px 16px', borderRadius: 999, backgroundColor: '#e8f7ee', color: '#2d6a4f', fontWeight: 700 }}>{isDemoMode ? 'Demo Mode' : 'Live Data'}</div>
            </div>
            <div style={{ marginTop: 24, display: 'grid', gap: 20 }}>
              <p style={{ margin: 0, color: '#3f5f48', lineHeight: 1.8 }}>
                {isDemoMode ? 'Demo Mode: This shows how the system will work when more people are using it.' : 'Download a report that shows where demand is growing and where investment is needed.'}
              </p>
              {prospectusUrl && (
                <a href={prospectusUrl} target="_blank" rel="noreferrer" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 'fit-content', padding: '14px 22px', borderRadius: 12, backgroundColor: '#2d6a4f', color: '#ffffff', fontWeight: 700, textDecoration: 'none' }}>Download Generated Prospectus</a>
              )}
            </div>
          </div>
        </section>

        <section id="about" style={{ padding: '40px 32px', borderRadius: 24, backgroundColor: '#edf5ee', display: 'grid', gap: 24 }}>
          <div style={{ display: 'grid', gap: 12, maxWidth: 760 }}>
            <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#2d6a4f' }}>About Kulima Africa</p>
            <h2 style={{ margin: 0, fontSize: 32 }}>Built for impact, designed for decision-makers</h2>
            <p style={{ margin: 0, color: '#34523f', lineHeight: 1.8 }}>
              Kulima OS turns grassroots activity into clear community reports. It is made for planners, policymakers, development partners, and investors who need to see real demand before they invest.
            </p>
            <p style={{ margin: 0, color: '#34523f', lineHeight: 1.8 }}>
              This helps governments, investors, and planners understand where real demand exists and invest in the right places.
            </p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 18 }}>
            {[
              { label: 'Food Everywhere', value: 'Real demand signals across agriculture and energy' },
              { label: 'Investor-ready', value: 'Sample prospectus and live report generation' },
              { label: 'Ethical by design', value: 'Privacy-safe community data with no individual profiling' }
            ].map((item) => (
              <div key={item.label} style={{ backgroundColor: '#ffffff', borderRadius: 20, padding: 24, boxShadow: '0 20px 40px rgba(22, 63, 41, 0.06)' }}>
                <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#2d6a4f' }}>{item.label}</p>
                <p style={{ margin: '12px 0 0', color: '#3f5f48', lineHeight: 1.7 }}>{item.value}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer style={{ backgroundColor: '#ffffff', borderTop: '1px solid #e6f0ea', padding: '24px 24px', color: '#2d6a4f' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 14, alignItems: 'center' }}>
          <span style={{ fontWeight: 700 }}>Built by Kulima Africa</span>
          <span>Food Everywhere, For Everyone, At All Times</span>
        </div>
      </footer>
    </div>
  );
}
