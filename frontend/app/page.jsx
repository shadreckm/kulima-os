'use client';

import { useState, useEffect, useRef } from 'react';

const ZONES = ['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'];
const PUBLIC_LOGO = '/logo.png';
const CARD_CONTENT = [
  {
    title: 'Local activity patterns',
    description: 'See when local farming and service activity repeats so you can spot reliable demand windows.',
    color: '#2d6a4f'
  },
  {
    title: 'Service gaps nearby',
    description: 'Discover repeated activity that points to missing power, water, or transport support.',
    color: '#146c43'
  },
  {
    title: 'Action-ready projects',
    description: 'Turn repeated local activity into practical recommendations for community infrastructure.',
    color: '#0f5132'
  }
];

export default function Home() {
  const [zone, setZone] = useState('MZUZU');
  const [inputValue, setInputValue] = useState('');
  const [summary, setSummary] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [showFullReport, setShowFullReport] = useState(false);
  const [shareMessage, setShareMessage] = useState('');
  const [recentActivities, setRecentActivities] = useState([]);
  const [cardIndex, setCardIndex] = useState(0);
  const reportRef = useRef(null);

  const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || '/api/v1').replace(/\/$/, '');
  const BACKEND_BASE = BASE_URL.replace(/\/api\/v1$/, '');
  const reportUrl = reportData?.pdf_url ? `${BACKEND_BASE}${reportData.pdf_url}` : '';

  const clusterData = summary?.clusters?.length ? summary.clusters : summary?.cluster_summaries || [];
  const hasClusters = Array.isArray(clusterData) && clusterData.length > 0;

  useEffect(() => {
    fetchSummary();
  }, [zone]);

  useEffect(() => {
    fetchRecentSignals();
    const interval = setInterval(fetchRecentSignals, 7000);
    return () => clearInterval(interval);
  }, []);

  const fetchRecentSignals = async () => {
    try {
      const response = await fetch(`${BASE_URL}/recent-signals`, { cache: 'no-store' });
      const data = await response.json();
      if (data?.success && Array.isArray(data.data)) {
        setRecentActivities(data.data);
      }
    } catch (error) {
      // Polling errors are not fatal
    }
  };

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BASE_URL}/summary/${zone}`, { cache: 'no-store' });
      const data = await response.json();
      if (data?.status === 'success' && data?.data) {
        setSummary(data.data);
        setMessage('Insights refreshed for your zone.');
      } else {
        setSummary(null);
        setMessage('No coordination data available yet. Record an activity to unlock insights.');
      }
    } catch (error) {
      setSummary(null);
      setMessage('Unable to load insights. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const parseZoneFromText = (text) => {
    const normalized = text?.toLowerCase() || '';
    if (/mzuzu/.test(normalized)) return 'MZUZU';
    if (/lilongwe/.test(normalized)) return 'LILONGWE';
    if (/blantyre/.test(normalized)) return 'BLANTYRE';
    if (/zomba/.test(normalized)) return 'ZOMBA';
    return null;
  };

  const handleSubmitActivity = async (event) => {
    event.preventDefault();
    if (!inputValue.trim()) {
      setMessage('Please describe an activity before submitting.');
      return;
    }

    const inferredZone = parseZoneFromText(inputValue) || zone;
    if (inferredZone !== zone) {
      setZone(inferredZone);
    }

    setLoading(true);
    setMessage('Recording activity and building insight...');

    try {
      const response = await fetch(`${BASE_URL}/signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone: inferredZone,
          raw_text: inputValue,
          source: 'web',
          user_id: `web_user_${Date.now()}`
        })
      });
      const data = await response.json();
      if (data?.status === 'success') {
        setMessage('Activity recorded. Refreshing insights...');
        setInputValue('');
        await fetchSummary();
      } else {
        setMessage(data?.message || 'Unable to record activity. Try again.');
      }
    } catch (error) {
      setMessage('Unable to record activity. Check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!summary || summary.signal_count === 0) {
      setMessage('More data is needed to create a full report. Record additional activities.');
      return;
    }
    setReportLoading(true);
    setMessage('Generating your investment report...');
    try {
      const response = await fetch(`${BASE_URL}/generate-prospectus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone, user_id: `web_user_${Date.now()}` })
      });
      const data = await response.json();
      if (data?.success) {
        setReportData(data.report || { pdf_url: data.pdf_url });
        setShowFullReport(true);
        setMessage('Report ready. Preview, download, or share it with local partners.');
      } else {
        setMessage(data?.message || 'Unable to generate report. Record more activity and try again.');
      }
    } catch (error) {
      setMessage('Unable to generate report. Please try again later.');
    } finally {
      setReportLoading(false);
    }
  };

  const handleViewFullReport = () => {
    if (!summary) {
      setMessage('Record activity first to unlock the full report preview.');
      return;
    }
    setShowFullReport(true);
  };

  const handleSharePartner = async () => {
    const text = reportUrl ? `Kulima OS report: ${reportUrl}` : `Kulima OS insights for ${zone} - ${window.location.href}`;
    if (navigator.share) {
      try {
        await navigator.share({ title: 'Kulima OS insights', text, url: reportUrl || window.location.href });
        setShareMessage('Report link shared successfully.');
        return;
      } catch (error) {
        // user canceled or unsupported
      }
    }
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(reportUrl || window.location.href);
      setShareMessage('Link copied to clipboard for sharing.');
    } else {
      setShareMessage('Copy this page or report URL to share with your partner.');
    }
  };

  const handleWhatsappShare = () => {
    const text = encodeURIComponent(reportUrl ? `Kulima OS report: ${reportUrl}` : `Kulima OS insights for ${zone}`);
    window.open(`https://wa.me/?text=${text}`, '_blank');
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f4f7f3', color: '#173e2e' }}>
      <header style={{ position: 'sticky', top: 0, backgroundColor: '#ffffff', borderBottom: '1px solid #dbe6df', zIndex: 10 }}>
        <div style={{ maxWidth: 1120, margin: '0 auto', padding: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <img src={PUBLIC_LOGO} alt="Kulima OS" style={{ width: 40, height: 40, borderRadius: 12, backgroundColor: '#2d6a4f' }} />
            <div>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Kulima OS</div>
              <div style={{ fontSize: 12, color: '#4a6859' }}>Live community demand insights</div>
            </div>
          </div>
          <select value={zone} onChange={(e) => setZone(e.target.value)} style={{ padding: '10px 14px', borderRadius: 12, border: '1px solid #d1e2d8', backgroundColor: '#f5faf7', cursor: 'pointer' }}>
            {ZONES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </div>
      </header>

      <main style={{ maxWidth: 1120, margin: '0 auto', padding: '32px 20px 60px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.45fr 1fr', gap: 24, alignItems: 'start' }}>
          <section style={{ display: 'grid', gap: 20 }}>
            <div style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 28, border: '1px solid #e3ece5' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 12 }}>Describe your activity</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#0f3b2d', marginBottom: 14 }}>Share a local activity.</div>
              <p style={{ fontSize: 15, color: '#41534c', lineHeight: 1.8 }}>Write one sentence describing what is happening in your area. The platform turns it into community insights.</p>
              <form onSubmit={handleSubmitActivity} style={{ display: 'grid', gap: 14 }}>
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  rows={5}
                  placeholder="e.g. Women are using a diesel mill in Mzuzu this afternoon to process rice"
                  style={{ width: '100%', padding: 18, borderRadius: 18, border: '1px solid #d8e7dd', resize: 'vertical', fontSize: 15 }}
                  disabled={loading}
                />
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
                  <button type="submit" disabled={loading || !inputValue.trim()} style={{ flex: '1 1 240px', padding: '14px 20px', borderRadius: 16, border: 'none', backgroundColor: '#2d6a4f', color: '#fff', fontWeight: 700, cursor: loading || !inputValue.trim() ? 'not-allowed' : 'pointer' }}>{loading ? 'Recording...' : 'Record activity'}</button>
                  <button type="button" onClick={() => setInputValue('')} style={{ padding: '14px 20px', borderRadius: 16, border: '1px solid #d8e7dd', backgroundColor: '#f8fbf8', color: '#1f4b34', fontWeight: 700 }}>Clear</button>
                  <span style={{ fontSize: 13, color: '#4f6258' }}>{parseZoneFromText(inputValue) ? `Detected zone: ${parseZoneFromText(inputValue)}` : `Selected zone: ${zone}`}</span>
                </div>
              </form>
              {message && <div style={{ marginTop: 14, padding: '16px', borderRadius: 16, backgroundColor: '#f1faf4', border: '1px solid #d6ead9', color: '#2a5a39' }}>{message}</div>}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 20 }}>
              <div style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 24, border: '1px solid #e3ece5' }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#14532d', marginBottom: 10 }}>Signals recorded</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: '#0f3b2d' }}>{summary?.signal_count ?? 0}</div>
                <div style={{ marginTop: 8, fontSize: 13, color: '#4f6258' }}>Activity points collected in this zone.</div>
              </div>
              <div style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 24, border: '1px solid #e3ece5' }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#14532d', marginBottom: 10 }}>Patterns detected</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: '#0f3b2d' }}>{summary?.total_patterns ?? 0}</div>
                <div style={{ marginTop: 8, fontSize: 13, color: '#4f6258' }}>Stable coordination patterns extracted.</div>
              </div>
            </div>

            <div style={{ display: 'grid', gap: 20 }}>
              {CARD_CONTENT.map((card, idx) => (
                <div key={idx} style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 24, border: '1px solid #e3ece5' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
                    <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: card.color }} />
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#14532d' }}>{card.title}</div>
                  </div>
                  <div style={{ fontSize: 16, color: '#1d433d', lineHeight: 1.7 }}>{card.description}</div>
                  {card.note && <div style={{ marginTop: 16, fontSize: 13, color: '#4f6258' }}>{card.note}</div>}
                </div>
              ))}
            </div>
          </section>

          <aside style={{ display: 'grid', gap: 20 }}>
            <div style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 24, border: '1px solid #e3ece5' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d' }}>Action center</div>
                  <div style={{ fontSize: 13, color: '#4f6258' }}>Create and share your community report.</div>
                </div>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <button onClick={handleGenerateReport} type="button" disabled={reportLoading} style={{ padding: '12px 16px', borderRadius: 14, border: 'none', backgroundColor: '#2d6a4f', color: '#fff', fontWeight: 700, cursor: reportLoading ? 'not-allowed' : 'pointer' }}>{reportLoading ? 'Generating...' : 'Create report'}</button>
                  <button onClick={handleWhatsappShare} type="button" style={{ padding: '12px 16px', borderRadius: 14, border: '1px solid #2d6a4f', backgroundColor: '#eff8f0', color: '#1f4b34', fontWeight: 700, cursor: 'pointer' }}>WhatsApp share</button>
                </div>
              </div>
              <div style={{ marginTop: 20, display: 'grid', gap: 12 }}>
                <button onClick={handleViewFullReport} type="button" style={{ width: '100%', padding: '14px 16px', borderRadius: 16, border: '1px solid #c7dfcc', backgroundColor: '#f8fbf8', color: '#1f4b34', fontWeight: 700 }}>Preview report</button>
                {reportUrl && <a href={reportUrl} download style={{ width: '100%', textAlign: 'center', padding: '14px 16px', borderRadius: 16, border: '1px solid #2d6a4f', backgroundColor: '#fff', color: '#2d6a4f', fontWeight: 700, textDecoration: 'none' }}>Download PDF</a>}
                <div style={{ fontSize: 13, color: '#4f6258' }}>{shareMessage || 'Share the report or preview the full insights summary.'}</div>
              </div>
            </div>

            <div style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 24, border: '1px solid #e3ece5' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 14 }}>Live activity feed</div>
              <div style={{ fontSize: 13, color: '#4f6258', marginBottom: 16 }}>Recent activity captured from the community.</div>
              <div style={{ display: 'grid', gap: 12 }}>
                {recentActivities.length ? recentActivities.slice(0, 4).map((activity, idx) => (
                  <div key={idx} style={{ padding: 14, borderRadius: 16, border: '1px solid #dbe6df', backgroundColor: '#f7faf7' }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#1f4b34' }}>{activity.zone || 'Unknown zone'}</div>
                    <div style={{ marginTop: 6, fontSize: 13, color: '#41534c' }}>{activity.raw_text}</div>
                  </div>
                )) : <div style={{ fontSize: 13, color: '#4f6258' }}>No recent activities yet. Record something to populate this feed.</div>}
              </div>
            </div>

            <div style={{ backgroundColor: '#f7fffb', borderRadius: 24, padding: 24, border: '1px solid #d9ede1' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 12 }}>Report snapshot</div>
              <div style={{ fontSize: 13, color: '#41534c', marginBottom: 18 }}>Review top observations, service gaps, and local readiness before sharing.</div>
              <div style={{ display: 'grid', gap: 12 }}>
                <div style={{ fontSize: 13, color: '#334a3f' }}>High-confidence patterns: {summary?.high_confidence_patterns ?? 0}</div>
                <div style={{ fontSize: 13, color: '#334a3f' }}>Moderate-confidence patterns: {summary?.moderate_confidence_patterns ?? 0}</div>
                <div style={{ fontSize: 13, color: '#334a3f' }}>Recommended local projects: {summary?.recommended_projects?.length ?? 0}</div>
              </div>
            </div>
          </aside>
        </div>

        {showFullReport && summary && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 57, 45, 0.65)', zIndex: 50, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 24 }}>
            <div style={{ width: 'min(100%, 960px)', maxHeight: '90vh', overflowY: 'auto', backgroundColor: '#ffffff', borderRadius: 24, padding: 28, boxShadow: '0 20px 80px rgba(15, 57, 45, 0.18)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#14532d', marginBottom: 10 }}>Report preview</div>
                  <h2 style={{ margin: 0, fontSize: 26, color: '#113f2f' }}>Community infrastructure prospectus</h2>
                </div>
                <button onClick={() => setShowFullReport(false)} style={{ padding: '12px 18px', borderRadius: 16, border: '1px solid #c0d6c7', backgroundColor: '#f7faf7', color: '#1f4b34', fontWeight: 700, cursor: 'pointer' }}>Close</button>
              </div>

              <div style={{ marginTop: 22, display: 'grid', gap: 18 }}>
                <div style={{ fontSize: 13, color: '#41534c', lineHeight: 1.8 }}>{summary?.key_finding || 'This preview explains local activity trends, missing services, and practical recommendations for your zone.'}</div>

                <div style={{ display: 'grid', gap: 16 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                    <div style={{ backgroundColor: '#f7fbf8', borderRadius: 20, padding: 20, border: '1px solid #d9ebe1' }}>
                      <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 8 }}>Top infrastructure gap</div>
                      <div style={{ fontSize: 13, color: '#41534c', lineHeight: 1.7 }}>{summary?.infrastructure_gaps?.[0] || 'No major infrastructure gaps identified yet.'}</div>
                    </div>
                    <div style={{ backgroundColor: '#f7fbf8', borderRadius: 20, padding: 20, border: '1px solid #d9ebe1' }}>
                      <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 8 }}>Recommended project</div>
                      <div style={{ fontSize: 13, color: '#41534c', lineHeight: 1.7 }}>{summary?.recommended_projects?.[0] || 'Add more activity signals to generate a project recommendation.'}</div>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gap: 12 }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d' }}>Local confidence and trends</div>
                    <div style={{ fontSize: 13, color: '#41534c', lineHeight: 1.7 }}>
                      {summary?.high_confidence_patterns > 0 ? `${summary.high_confidence_patterns} high-confidence pattern${summary.high_confidence_patterns > 1 ? 's' : ''}` : 'No high-confidence patterns yet.'}
                      <br />
                      {summary?.moderate_confidence_patterns > 0 ? `${summary.moderate_confidence_patterns} moderate-confidence pattern${summary.moderate_confidence_patterns > 1 ? 's' : ''}` : 'No moderate-confidence patterns yet.'}
                    </div>
                  </div>

                  <div style={{ display: 'grid', gap: 12 }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d' }}>Top local observations</div>
                    {clusterData.length > 0 ? clusterData.slice(0, 3).map((cluster, idx) => (
                      <div key={idx} style={{ backgroundColor: '#f7fbf8', borderRadius: 20, padding: 18, border: '1px solid #d9ebe1' }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: '#134e4a' }}>{cluster.cluster_name || `Cluster ${idx + 1}`}</div>
                        <div style={{ marginTop: 8, fontSize: 13, color: '#41534c', lineHeight: 1.75 }}>{cluster.summary || 'No cluster summary yet.'}</div>
                      </div>
                    )) : <div style={{ fontSize: 13, color: '#41534c' }}>No local signal highlights available yet.</div>}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
