'use client';

import { useState, useEffect } from 'react';

export default function Home() {
  const [zone, setZone] = useState('MZUZU');
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [signalLoading, setSignalLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [signalForm, setSignalForm] = useState({
    activity_type: '',
    time_window: ''
  });
  const [message, setMessage] = useState('');

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://kulima-os-backend.onrender.com/api/v1';

  useEffect(() => {
    fetchSummary();
  }, [zone]);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/summary/${zone}`);
      const data = await res.json();
      if (data.status === 'success') {
        setSummary(data.data);
      }
    } catch (err) {
      console.error('Error fetching summary:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSignalSubmit = async (e) => {
    e.preventDefault();
    setSignalLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${BASE_URL}/signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone,
          activity_type: signalForm.activity_type,
          time_window: signalForm.time_window,
          source: 'web'
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setMessage('Activity recorded successfully!');
        setSignalForm({ activity_type: '', time_window: '' });
        fetchSummary();
      } else {
        setMessage('Failed to record activity');
      }
    } catch (err) {
      setMessage('Error recording activity');
    } finally {
      setSignalLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    setReportLoading(true);
    setReportData(null);
    try {
      const res = await fetch(`${BASE_URL}/generate-prospectus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setReportData(data.data);
      } else {
        setMessage('Failed to generate report');
      }
    } catch (err) {
      setMessage('Error generating report');
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
      {/* Hero Section */}
      <div style={{ textAlign: 'center', marginBottom: '60px', padding: '60px 20px', backgroundColor: '#f8f9fa', borderRadius: '12px' }}>
        <h1 style={{ fontSize: '48px', fontWeight: 'bold', marginBottom: '20px', color: '#1a1a1a' }}>
          Kulima OS
        </h1>
        <p style={{ fontSize: '20px', color: '#555', maxWidth: '800px', margin: '0 auto', lineHeight: '1.6' }}>
          Helping Malawi plan farming and infrastructure using real activity data
        </p>
      </div>

      {/* Problem Section */}
      <div style={{ marginBottom: '60px', padding: '40px', backgroundColor: '#fff3cd', borderRadius: '12px', borderLeft: '4px solid #ffc107' }}>
        <h2 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '20px', color: '#856404' }}>
          The Problem
        </h2>
        <p style={{ fontSize: '18px', color: '#555', lineHeight: '1.6' }}>
          Many investments fail because they are based on assumptions instead of real activity.
        </p>
      </div>

      {/* Solution Section */}
      <div style={{ marginBottom: '60px', padding: '40px', backgroundColor: '#d4edda', borderRadius: '12px', borderLeft: '4px solid #28a745' }}>
        <h2 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '20px', color: '#155724' }}>
          The Solution
        </h2>
        <p style={{ fontSize: '18px', color: '#555', lineHeight: '1.6' }}>
          Kulima OS collects real activity data and turns it into insights for better planning.
        </p>
      </div>

      {/* How It Works Section */}
      <div style={{ marginBottom: '60px', padding: '40px', backgroundColor: '#e2e3e5', borderRadius: '12px' }}>
        <h2 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '30px', textAlign: 'center', color: '#1a1a1a' }}>
          How It Works
        </h2>
        <div style={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: '20px' }}>
          <div style={{ textAlign: 'center', flex: '1', minWidth: '200px' }}>
            <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#007bff', marginBottom: '10px' }}>1</div>
            <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '10px', color: '#1a1a1a' }}>Record Activity</h3>
            <p style={{ fontSize: '16px', color: '#555' }}>Submit farming and trading activities</p>
          </div>
          <div style={{ textAlign: 'center', flex: '1', minWidth: '200px' }}>
            <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#007bff', marginBottom: '10px' }}>2</div>
            <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '10px', color: '#1a1a1a' }}>View Insights</h3>
            <p style={{ fontSize: '16px', color: '#555' }}>See patterns and trends in real-time</p>
          </div>
          <div style={{ textAlign: 'center', flex: '1', minWidth: '200px' }}>
            <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#007bff', marginBottom: '10px' }}>3</div>
            <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '10px', color: '#1a1a1a' }}>Generate Report</h3>
            <p style={{ fontSize: '16px', color: '#555' }}>Download detailed investment reports</p>
          </div>
        </div>
      </div>

      {message && (
        <div style={{ padding: '15px', marginBottom: '30px', backgroundColor: '#e8f5e9', border: '1px solid #4caf50', borderRadius: '8px', textAlign: 'center' }}>
          {message}
        </div>
      )}

      {/* Interactive Demo Section */}
      <div style={{ marginBottom: '40px', padding: '40px', backgroundColor: '#f5f5f5', borderRadius: '12px' }}>
        <h2 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '30px', textAlign: 'center', color: '#1a1a1a' }}>
          Try It Now
        </h2>
        
        <div style={{ marginBottom: '30px', padding: '30px', backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ fontSize: '22px', fontWeight: 'bold', marginBottom: '20px', color: '#1a1a1a' }}>Record Activity</h3>
          <form onSubmit={handleSignalSubmit}>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '16px', color: '#333' }}>Zone</label>
              <select
                value={zone}
                onChange={(e) => setZone(e.target.value)}
                style={{ width: '100%', padding: '12px', borderRadius: '6px', border: '1px solid #ddd', fontSize: '16px' }}
              >
                <option value="MZUZU">MZUZU</option>
                <option value="LILONGWE">LILONGWE</option>
                <option value="BLANTYRE">BLANTYRE</option>
                <option value="ZOMBA">ZOMBA</option>
              </select>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '16px', color: '#333' }}>Activity Type</label>
              <select
                value={signalForm.activity_type}
                onChange={(e) => setSignalForm({ ...signalForm, activity_type: e.target.value })}
                required
                style={{ width: '100%', padding: '12px', borderRadius: '6px', border: '1px solid #ddd', fontSize: '16px' }}
              >
                <option value="">Select activity...</option>
                <option value="irrigation">Irrigation</option>
                <option value="milling">Milling</option>
                <option value="cold storage">Cold Storage</option>
                <option value="welding">Welding</option>
              </select>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '16px', color: '#333' }}>Time Window</label>
              <select
                value={signalForm.time_window}
                onChange={(e) => setSignalForm({ ...signalForm, time_window: e.target.value })}
                required
                style={{ width: '100%', padding: '12px', borderRadius: '6px', border: '1px solid #ddd', fontSize: '16px' }}
              >
                <option value="">Select time window...</option>
                <option value="morning">Morning</option>
                <option value="midday">Midday</option>
                <option value="evening">Evening</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={signalLoading}
              style={{ padding: '14px 28px', backgroundColor: '#4caf50', color: 'white', border: 'none', borderRadius: '6px', cursor: signalLoading ? 'not-allowed' : 'pointer', fontSize: '16px', fontWeight: 'bold', width: '100%' }}
            >
              {signalLoading ? 'Recording...' : 'Record Activity'}
            </button>
          </form>
        </div>

        <div style={{ marginBottom: '30px', padding: '30px', backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ fontSize: '22px', fontWeight: 'bold', marginBottom: '20px', color: '#1a1a1a' }}>Activity Summary</h3>
          {loading ? (
            <p style={{ textAlign: 'center', fontSize: '18px', color: '#666' }}>Loading...</p>
          ) : summary ? (
            <div>
              <div style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#e3f2fd', borderRadius: '8px' }}>
                <h4 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '10px', color: '#0d47a1' }}>Insight</h4>
                <p style={{ fontSize: '16px', color: '#333', lineHeight: '1.6' }}>{summary.key_finding}</p>
              </div>
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '10px', color: '#1a1a1a' }}>Total Activities Detected</h4>
                <p style={{ fontSize: '36px', fontWeight: 'bold', color: '#4caf50', textAlign: 'center' }}>{summary.total_patterns}</p>
              </div>
              <div>
                <h4 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '10px', color: '#1a1a1a' }}>Main Activities</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                  {summary.productive_activities_detected.map((activity) => (
                    <span key={activity} style={{ padding: '8px 16px', backgroundColor: '#e0e0e0', borderRadius: '20px', fontSize: '14px', fontWeight: 'bold', color: '#333' }}>
                      {activity}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p style={{ textAlign: 'center', fontSize: '18px', color: '#666' }}>No summary available</p>
          )}
        </div>

        <div style={{ padding: '30px', backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ fontSize: '22px', fontWeight: 'bold', marginBottom: '20px', color: '#1a1a1a' }}>Generate Report</h3>
          <button
            onClick={handleGenerateReport}
            disabled={reportLoading}
            style={{ padding: '14px 28px', backgroundColor: '#9c27b0', color: 'white', border: 'none', borderRadius: '6px', cursor: reportLoading ? 'not-allowed' : 'pointer', fontSize: '16px', fontWeight: 'bold', width: '100%' }}
          >
            {reportLoading ? 'Generating...' : 'Generate Report'}
          </button>
          {reportData && (
            <div style={{ marginTop: '25px', padding: '20px', backgroundColor: '#e8f5e9', borderRadius: '8px' }}>
              <h4 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '15px', color: '#155724' }}>Report Generated Successfully!</h4>
              <p style={{ marginBottom: '15px', fontSize: '16px', color: '#333' }}>Report ID: {reportData.prospectus_id}</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <a
                  href={`https://kulima-os-backend.onrender.com${reportData.pdf_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ display: 'block', padding: '14px', backgroundColor: '#2196f3', color: 'white', textAlign: 'center', textDecoration: 'none', borderRadius: '6px', fontSize: '16px', fontWeight: 'bold' }}
                >
                  Download PDF
                </a>
                <a
                  href={`https://kulima-os-backend.onrender.com${reportData.json_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ display: 'block', padding: '14px', backgroundColor: '#607d8b', color: 'white', textAlign: 'center', textDecoration: 'none', borderRadius: '6px', fontSize: '16px', fontWeight: 'bold' }}
                >
                  Download JSON
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
