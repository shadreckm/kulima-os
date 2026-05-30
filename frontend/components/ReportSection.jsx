/**
 * ReportSection Component
 * Displays generated report details and download options
 */
export function ReportSection({ reportData, zone, backendBase }) {
  if (!reportData) return null;

  return (
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
          href={(reportData && (reportData.pdf_url || reportData.pdfUrl || (reportData.report && reportData.report.pdf_url))) || '#'}
          download
          target="_blank"
          rel="noopener noreferrer"
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
  );
}
