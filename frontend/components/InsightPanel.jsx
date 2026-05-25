/**
 * InsightPanel Component
 * Displays key insights, patterns, and infrastructure gaps
 */
export function InsightPanel({ summary }) {
  if (!summary) return null;

  return (
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
          {summary.key_finding}
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
              {summary.signal_count || 0}
            </div>
            <div style={{ fontSize: 12, color: '#5a7a66', marginTop: 4 }}>
              Activities recorded
            </div>
          </div>
          <div style={{ textAlign: 'center', paddingBottom: 16, borderBottom: '1px solid #e0e8e4' }}>
            <div style={{ fontSize: 32, fontWeight: 700, color: '#2d6a4f' }}>
              {summary.total_patterns || 0}
            </div>
            <div style={{ fontSize: 12, color: '#5a7a66', marginTop: 4 }}>
              Patterns found
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#2d6a4f' }}>
              {summary.high_confidence_patterns || 0}
            </div>
            <div style={{ fontSize: 12, color: '#5a7a66', marginTop: 4 }}>
              High confidence
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#2d6a4f' }}>
              {summary.productive_activities_detected?.length || 0}
            </div>
            <div style={{ fontSize: 12, color: '#5a7a66', marginTop: 4 }}>
              Activity types
            </div>
          </div>
        </div>
      </div>

      {/* Activity Types */}
      {summary.productive_activities_detected && summary.productive_activities_detected.length > 0 && (
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
            {summary.productive_activities_detected.map((activity, idx) => (
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
      )}

      {/* Infrastructure Gaps */}
      {summary.infrastructure_gaps && summary.infrastructure_gaps.length > 0 && (
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
            {summary.infrastructure_gaps.slice(0, 3).map((gap, idx) => (
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
  );
}
