/**
 * ActivityFeed Component
 * Displays recent activities from community
 */
export function ActivityFeed({ activities }) {
  return (
    <div style={{
      backgroundColor: '#ffffff',
      borderRadius: 14,
      padding: 24,
      boxShadow: '0 2px 8px rgba(23, 45, 32, 0.04)',
      border: '1px solid #e0e8e4'
    }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#2d6a4f', marginBottom: 16 }}>
        Recent Activity ({activities.length})
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {activities.slice(0, 6).map(item => (
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
  );
}
