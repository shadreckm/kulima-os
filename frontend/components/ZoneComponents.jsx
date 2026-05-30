'use client';

import { useState, useRef, useEffect } from 'react';
import styles from '../../styles/zoneDashboard.module.css';
import {
  Card, CardTitle, Button, Input, Select, Message, Toast,
  ButtonGroup, Section, StatBox, ActivityItem, Badge
} from './UI';
import { apiClient, getErrorMessage } from '../../services/api';

/**
 * Header Component
 */
export function Header({ zone, onZoneChange }) {
  return (
    <header className={styles.header}>
      <div className={styles.headerContent}>
        <div className={styles.headerTitle}>🌱 Kulima OS</div>
        <Select
          options={['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA']}
          value={zone}
          onChange={(e) => onZoneChange(e.target.value)}
          label="Zone:"
        />
      </div>
    </header>
  );
}

/**
 * Activity Input Component
 */
export function ActivityInput({ zone, onSignalSubmitted }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const inputRef = useRef(null);

  const handleSubmit = async () => {
    if (!input.trim()) {
      setMessage('Please enter an activity. Example: "irrigation mzuzu morning"');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await apiClient.createSignal({
        raw_text: input,
        zone,
        timestamp: new Date().toISOString(),
        source: 'web'
      });

      if (response.status === 'success') {
        setMessage('✓ Activity recorded successfully');
        setInput('');
        onSignalSubmitted?.();
        inputRef.current?.focus();
        setTimeout(() => setMessage(''), 2500);
      } else {
        setMessage(response.message || 'Failed to record activity');
      }
    } catch (error) {
      setMessage(`Error: ${getErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleSubmit();
    }
  };

  return (
    <Section title="Record Activity">
      <div className={styles.inputSection}>
        {message && (
          <Message type={message.includes('✓') ? 'success' : 'error'}>
            {message}
          </Message>
        )}
        <Input
          ref={inputRef}
          placeholder="e.g., irrigation mzuzu morning"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
        />
        <Button
          onClick={handleSubmit}
          disabled={loading}
          loading={loading}
        >
          {loading ? 'Recording...' : 'Record Activity'}
        </Button>
      </div>
    </Section>
  );
}

/**
 * Live Feed Component
 */
export function LiveFeed({ activities = [], loading = false }) {
  if (loading && activities.length === 0) {
    return (
      <Section title="Live Activity Feed">
        <div style={{ textAlign: 'center', color: '#5a7a66', padding: '20px 0' }}>
          Loading activities...
        </div>
      </Section>
    );
  }

  return (
    <Section title={`Live Activity Feed (${activities.length})`}>
      <div className={styles.feedContainer}>
        {activities.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#5a7a66', padding: '20px 0' }}>
            No activities recorded yet. Start by recording an activity above.
          </div>
        ) : (
          activities.map((activity, idx) => (
            <ActivityItem
              key={activity.id || idx}
              activity={activity.activity_type || activity.activity}
              zone={activity.zone}
              time={new Date(activity.timestamp).toLocaleTimeString()}
              description={activity.original_text}
            />
          ))
        )}
      </div>
    </Section>
  );
}

/**
 * Insights Display Component
 */
export function InsightsDisplay({ summary = null, loading = false }) {
  if (loading) {
    return (
      <Section title="Insights">
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          Analyzing patterns...
        </div>
      </Section>
    );
  }

  if (!summary) {
    return (
      <Section title="Insights">
        <div style={{ textAlign: 'center', color: '#5a7a66', padding: '20px 0' }}>
          Patterns are forming. Record more activities to unlock insights.
        </div>
      </Section>
    );
  }

  return (
    <Section title="Insights">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {summary.key_finding && (
          <Card style={{ backgroundColor: '#e7f6f1', border: '1px solid #b8e6d5' }}>
            <div style={{ fontSize: '14px', fontWeight: '700', color: '#1f4d38' }}>
              {summary.key_finding}
            </div>
          </Card>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <StatBox label="Activities" value={summary.signal_count || 0} />
          <StatBox label="Patterns" value={summary.total_patterns || 0} />
        </div>

        {summary.productive_activities_detected && summary.productive_activities_detected.length > 0 && (
          <div>
            <div style={{ fontSize: '12px', fontWeight: '600', color: '#2d6a4f', marginBottom: '8px' }}>
              Activities Detected
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {summary.productive_activities_detected.map((activity, idx) => (
                <Badge key={idx}>{activity}</Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </Section>
  );
}

/**
 * Report Generation Component
 */
export function ReportSection({ zone, summary, onReportGenerated }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [reportUrl, setReportUrl] = useState('');

  const handleGenerateReport = async () => {
    if (!summary || (typeof summary.signal_count !== 'undefined' && summary.signal_count === 0)) {
      setMessage('More data is needed. Record at least 3 activities to generate a report.');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await apiClient.generateProspectus(
        zone,
        'web_user_' + Date.now()
      );

      if (response && response.success) {
        // prefer top-level pdf_url, fall back to nested report
        const pdf = response.pdf_url || (response.report && response.report.pdf_url) || '';
        setReportUrl(pdf);
        setMessage('✓ Report generated successfully');
        onReportGenerated?.(response.report || { pdf_url: pdf });
      } else {
        setMessage(response?.message || 'Failed to generate report');
      }
    } catch (error) {
      setMessage(`Error: ${getErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Section title="Investment Report">
      <div className={styles.inputSection}>
        {message && (
          <Message type={message.includes('✓') ? 'success' : 'error'}>
            {message}
          </Message>
        )}

        <Button
          onClick={handleGenerateReport}
          disabled={loading || (summary && summary.signal_count === 0)}
          loading={loading}
        >
          {loading ? 'Generating...' : 'Generate Prospectus'}
        </Button>

        {reportUrl && (
          <Button
            variant="secondary"
            onClick={() => window.open(reportUrl, '_blank')}
          >
            📄 Download Report
          </Button>
        )}
      </div>
    </Section>
  );
}

/**
 * Zone Info Component
 */
export function ZoneInfo({ zone, loading = false }) {
  const [zoneData, setZoneData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!zone) return;

    const fetchZoneData = async () => {
      try {
        const data = await apiClient.getZoneData(zone);
        if (data.status === 'success') {
          setZoneData(data.data);
          setError('');
        }
      } catch (err) {
        setError(getErrorMessage(err));
      }
    };

    fetchZoneData();
  }, [zone]);

  if (loading || !zoneData) return null;

  if (error) {
    return (
      <Section title="Zone Info">
        <Message type="error">{error}</Message>
      </Section>
    );
  }

  return (
    <Section title={`Zone: ${zoneData.metadata?.name}`}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
        <div><strong>Region:</strong> {zoneData.metadata?.region}</div>
        <div><strong>Type:</strong> {zoneData.metadata?.settlement_type}</div>
        <div><strong>Status:</strong> {zoneData.metadata?.infrastructure_status}</div>
      </div>
    </Section>
  );
}

/**
 * Infrastructure Gaps Component
 */
export function InfrastructureGaps({ zone }) {
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!zone) return;

    const fetchGaps = async () => {
      setLoading(true);
      try {
        const data = await apiClient.getInfrastructureGaps(zone);
        if (data.status === 'success') {
          setGaps(data.data.gaps);
        }
      } catch (error) {
        console.error('Error fetching infrastructure gaps:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchGaps();
  }, [zone]);

  if (loading) return null;
  if (gaps.length === 0) return null;

  return (
    <Section title="⚡ Infrastructure Opportunities">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {gaps.slice(0, 3).map((gap, idx) => (
          <div key={idx} style={{
            padding: '12px',
            backgroundColor: '#fff9e6',
            borderRadius: '8px',
            fontSize: '12px',
            borderLeft: '3px solid #ffc107'
          }}>
            <div style={{ fontWeight: '600', color: '#b8860b', marginBottom: '4px' }}>
              {gap.activity_type}
            </div>
            <div style={{ color: '#8b6914' }}>
              {gap.recommendation}
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}
