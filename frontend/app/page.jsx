'use client';

import { useState, useEffect, useRef } from 'react';

const ZONES = ['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'];
const PUBLIC_LOGO = '/logo.png';

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
  const reportRef = useRef(null);

  const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || '/api/v1').replace(/\/$/, '');
  const BACKEND_BASE = BASE_URL.replace(/\/api\/v1$/, '');
  const reportUrl = reportData?.pdf_url ? `${BACKEND_BASE}${reportData.pdf_url}` : '';

  const clusterData = summary?.clusters?.length ? summary.clusters : summary?.cluster_summaries || [];
  const hasClusters = Array.isArray(clusterData) && clusterData.length > 0;

  useEffect(() => {
    fetchSummary();
  }, [zone]);

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
        setMessage('Report created. You can view, download, or share it now.');
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
    setTimeout(() => reportRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80);
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

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f4f7f3', color: '#173e2e' }}>
      <header style={{ position: 'sticky', top: 0, backgroundColor: '#ffffff', borderBottom: '1px solid #dbe6df', zIndex: 10 }}>
        <div style={{ maxWidth: 1120, margin: '0 auto', padding: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <img src={PUBLIC_LOGO} alt="Kulima OS" style={{ width: 40, height: 40, borderRadius: 12, backgroundColor: '#2d6a4f' }} />
            <div>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Kulima OS</div>
              <div style={{ fontSize: 12, color: '#4a6859' }}>Live coordination intelligence</div>
            </div>
          </div>
          <select value={zone} onChange={(e) => setZone(e.target.value)} style={{ padding: '10px 14px', borderRadius: 12, border: '1px solid #d1e2d8', backgroundColor: '#f5faf7', cursor: 'pointer' }}>
            {ZONES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </div>
      </header>

      <main style={{ maxWidth: 1120, margin: '0 auto', padding: '32px 20px 60px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24, alignItems: 'start' }}>
          <section style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 28, border: '1px solid #e3ece5' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 12 }}>What is happening?</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#0f3b2d', marginBottom: 14 }}>Capture activity in natural language.</div>
              <div style={{ fontSize: 14, color: '#4f6258', marginBottom: 18 }}>Type a sentence like: "We are farming tomatoes in Luwinga this morning" so the platform can classify activity, group it, and reveal cluster intelligence.</div>
              <form onSubmit={handleSubmitActivity} style={{ display: 'grid', gap: 14 }}>
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  rows={5}
                  placeholder="e.g. We are farming tomatoes in Luwinga this morning"
                  style={{ width: '100%', padding: 16, borderRadius: 16, border: '1px solid #d8e7dd', resize: 'vertical', fontSize: 14 }}
                  disabled={loading}
                />
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
                  <button type="submit" disabled={loading || !inputValue.trim()} style={{ flex: '1 1 220px', padding: '14px 18px', borderRadius: 14, border: 'none', backgroundColor: '#2d6a4f', color: '#fff', fontWeight: 700, cursor: loading || !inputValue.trim() ? 'not-allowed' : 'pointer' }}>{loading ? 'Recording...' : 'Record activity'}</button>
                  <button type="button" onClick={() => setInputValue('')} style={{ padding: '14px 18px', borderRadius: 14, border: '1px solid #d8e7dd', backgroundColor: '#f8fbf8', color: '#1f4b34', fontWeight: 700 }}>Clear</button>
                  <div style={{ fontSize: 13, color: '#4f6258' }}>{parseZoneFromText(inputValue) ? `Detected zone: ${parseZoneFromText(inputValue)}` : `Using selected zone: ${zone}`}</div>
                </div>
              </form>
              {message && <div style={{ marginTop: 12, padding: '14px 16px', borderRadius: 14, backgroundColor: '#f1faf4', border: '1px solid #d6ead9', color: '#2a5a39' }}>{message}</div>}
            </div>

            <div style={{ backgroundColor: '#f8fffb', borderRadius: 24, padding: 26, border: '1px solid #d9ede1' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#146c43', marginBottom: 10 }}>Community Insights & Opportunities</div>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#0f4636', marginBottom: 10 }}>See cluster activity, infrastructure gaps, and recommended projects before you download anything.</div>
              <div style={{ fontSize: 14, color: '#41544c', lineHeight: 1.75 }}>These insights are based on real activities recorded in your area. They help identify where investment and infrastructure is needed.</div>
              <div style={{ marginTop: 22, display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                <button onClick={handleViewFullReport} type="button" style={{ padding: '14px 20px', borderRadius: 14, border: 'none', backgroundColor: '#2d6a4f', color: '#fff', fontWeight: 700, cursor: 'pointer' }}>View Full Report</button>
                {reportUrl ? (
                  <a href={reportUrl} download style={{ padding: '14px 20px', borderRadius: 14, border: '1px solid #2d6a4f', backgroundColor: '#fff', color: '#2d6a4f', fontWeight: 700, textDecoration: 'none' }}>Download PDF</a>
                ) : (
                  <button onClick={handleGenerateReport} type="button" disabled={reportLoading} style={{ padding: '14px 20px', borderRadius: 14, border: '1px solid #2d6a4f', backgroundColor: '#fff', color: '#2d6a4f', fontWeight: 700, cursor: reportLoading ? 'not-allowed' : 'pointer' }}>{reportLoading ? 'Building report...' : 'Create report'}</button>
                )}
                <button onClick={handleSharePartner} type="button" style={{ padding: '14px 20px', borderRadius: 14, border: '1px solid #c7dfcc', backgroundColor: '#eff8f0', color: '#1f4b34', fontWeight: 700, cursor: 'pointer' }}>Share report</button>
              </div>
              {shareMessage && <div style={{ marginTop: 14, fontSize: 13, color: '#2d6a4f' }}>{shareMessage}</div>}
            </div>

            <div style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 26, border: '1px solid #e4ece5' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 14 }}>Cluster intelligence</div>
              {hasClusters ? (
                <div style={{ display: 'grid', gap: 20 }}>
                  {clusterData.map((cluster, idx) => (
                    <div key={idx} style={{ backgroundColor: '#f7fbf8', borderRadius: 20, padding: 20, border: '1px solid #d9ebe1' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 18, flexWrap: 'wrap' }}>
                        <div>
                          <div style={{ fontSize: 16, fontWeight: 700, color: '#154734' }}>{cluster.cluster_name || `Cluster ${idx + 1}`}</div>
                          <div style={{ fontSize: 13, color: '#41534c', marginTop: 8 }}>{cluster.summary || 'This cluster is collecting local signals and creating insight.'}</div>
                        </div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: '#14532d', backgroundColor: '#e2f4e8', borderRadius: 999, padding: '8px 12px', whiteSpace: 'nowrap' }}>
                          Confidence: {cluster.confidence || cluster.confidence_score || 'medium'}
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18, marginTop: 18 }}>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 700, color: '#134e4a', marginBottom: 10 }}>Activities</div>
                          <ul style={{ paddingLeft: 18, margin: 0, color: '#2f4f3a', fontSize: 13, lineHeight: 1.8 }}>
                            {Object.entries(cluster.activities || {}).map(([type, count]) => (
                              <li key={type}>{type} ({count})</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 700, color: '#134e4a', marginBottom: 10 }}>What this means</div>
                          <p style={{ margin: 0, color: '#41534c', fontSize: 13, lineHeight: 1.8 }}>{cluster.insight || 'Repeated activity points to local coordination needs and potential investment opportunity.'}</p>
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18, marginTop: 18 }}>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 700, color: '#5f4339', marginBottom: 10 }}>Infrastructure gaps</div>
                          <ul style={{ paddingLeft: 18, margin: 0, color: '#3c4f44', fontSize: 13, lineHeight: 1.8 }}>
                            {(cluster.infrastructure_gaps || []).map((gap, gapIdx) => (
                              <li key={gapIdx}>{gap}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 700, color: '#14532d', marginBottom: 10 }}>Recommended projects</div>
                          <ul style={{ paddingLeft: 18, margin: 0, color: '#2f4f3a', fontSize: 13, lineHeight: 1.8 }}>
                            {(cluster.recommended_projects || []).map((project, projectIdx) => (
                              <li key={projectIdx}>{project}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ padding: 20, borderRadius: 20, border: '1px dashed #cfe4d6', backgroundColor: '#f3faf6', color: '#4c5c50', fontSize: 14 }}>No cluster intelligence is ready yet. Record more real activities to unlock detailed local insights.</div>
              )}
            </div>
          </section>

          <aside style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 22, border: '1px solid #e1ece4' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 12 }}>Quick view</div>
              <div style={{ fontSize: 13, color: '#41534c', marginBottom: 14 }}>Summary of what is happening in {zone}.</div>
              <div style={{ display: 'grid', gap: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#334a3f' }}><span>Signals recorded</span><span>{summary?.signal_count ?? 0}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#334a3f' }}><span>Patterns detected</span><span>{summary?.total_patterns ?? 0}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#334a3f' }}><span>High confidence</span><span>{summary?.high_confidence_patterns ?? 0}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#334a3f' }}><span>Moderate confidence</span><span>{summary?.moderate_confidence_patterns ?? 0}</span></div>
              </div>
            </div>
            <div style={{ backgroundColor: '#ffffff', borderRadius: 24, padding: 22, border: '1px solid #e1ece4' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 12 }}>Report status</div>
              {reportUrl ? (
                <div style={{ fontSize: 13, color: '#41534c', lineHeight: 1.8 }}>
                  Your report is ready. <br />Download it or share the link above.
                </div>
              ) : (
                <div style={{ fontSize: 13, color: '#41534c', lineHeight: 1.8 }}>
                  No report has been created yet. Use Create report to build the PDF.
                </div>
              )}
            </div>
          </aside>
        </div>

        {showFullReport && summary && (
          <section ref={reportRef} style={{ marginTop: 30, backgroundColor: '#ffffff', borderRadius: 24, padding: 26, border: '1px solid #d8e8df' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 14, flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#14532d', marginBottom: 10 }}>Report preview</div>
                <h2 style={{ margin: 0, fontSize: 24, color: '#113f2f' }}>Executive summary</h2>
              </div>
              <button onClick={() => setShowFullReport(false)} style={{ padding: '12px 16px', borderRadius: 14, border: '1px solid #c0d6c7', backgroundColor: '#f7faf7', color: '#1f4b34', fontWeight: 700, cursor: 'pointer' }}>Close preview</button>
            </div>
            <p style={{ marginTop: 18, fontSize: 14, color: '#394d44', lineHeight: 1.8 }}>{summary?.key_finding || 'This preview explains local demand trends, gaps, and opportunities detected in your zone.'}</p>
            <div style={{ display: 'grid', gap: 18, marginTop: 24 }}>
              <div style={{ backgroundColor: '#f7fbf8', borderRadius: 20, padding: 22, border: '1px solid #d9ebe1' }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 10 }}>Cluster overview</div>
                {hasClusters ? clusterData.map((cluster, idx) => (
                  <div key={idx} style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 15, fontWeight: 700, color: '#114136' }}>{cluster.cluster_name || `Cluster ${idx + 1}`}</div>
                    <div style={{ fontSize: 13, color: '#41534c', marginTop: 8 }}>{cluster.summary || 'No summary available yet.'}</div>
                  </div>
                )) : <div style={{ fontSize: 13, color: '#41534c' }}>No cluster overview available. Record more activity to create this content.</div>}
              </div>
              <div style={{ backgroundColor: '#f7fbf8', borderRadius: 20, padding: 22, border: '1px solid #d9ebe1' }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 10 }}>Infrastructure gaps</div>
                {summary?.infrastructure_gaps?.length ? (
                  <ul style={{ paddingLeft: 18, margin: 0, color: '#41534c', fontSize: 13, lineHeight: 1.8 }}>
                    {summary.infrastructure_gaps.map((gap, idx) => (
                      <li key={idx}>{gap}</li>
                    ))}
                  </ul>
                ) : (
                  <div style={{ fontSize: 13, color: '#41534c' }}>No gaps have been found yet. Record more signals to reveal missing infrastructure.</div>
                )}
              </div>
              <div style={{ backgroundColor: '#f7fbf8', borderRadius: 20, padding: 22, border: '1px solid #d9ebe1' }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 10 }}>Recommended projects</div>
                {summary?.recommended_projects?.length ? (
                  <ul style={{ paddingLeft: 18, margin: 0, color: '#41534c', fontSize: 13, lineHeight: 1.8 }}>
                    {summary.recommended_projects.map((project, idx) => (
                      <li key={idx}>{project}</li>
                    ))}
                  </ul>
                ) : (
                  <div style={{ fontSize: 13, color: '#41534c' }}>No projects recommended yet. More local data will help identify action items.</div>
                )}
              </div>
              <div style={{ backgroundColor: '#f7fbf8', borderRadius: 20, padding: 22, border: '1px solid #d9ebe1' }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#14532d', marginBottom: 10 }}>Confidence level</div>
                <div style={{ fontSize: 13, color: '#41534c', lineHeight: 1.8 }}>
                  {summary?.high_confidence_patterns > 0 ? `${summary.high_confidence_patterns} high-confidence pattern${summary.high_confidence_patterns > 1 ? 's' : ''} detected.` : summary?.moderate_confidence_patterns > 0 ? `${summary.moderate_confidence_patterns} moderate-confidence pattern${summary.moderate_confidence_patterns > 1 ? 's' : ''} detected.` : 'No strong patterns yet — keep recording activities to build confidence.'}
                </div>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
