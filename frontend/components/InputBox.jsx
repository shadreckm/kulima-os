/**
 * InputBox Component
 * ChatGPT-style natural language input for activities
 */
export function InputBox({ value, onChange, onSubmit, isLoading }) {
  return (
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
      <form onSubmit={onSubmit}>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Type what is happening… e.g. 'We are irrigating maize in the morning'"
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
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !value.trim()}
          style={{
            width: '100%',
            marginTop: 14,
            padding: '12px 18px',
            borderRadius: 10,
            backgroundColor: value.trim() ? '#2d6a4f' : '#d4e0d9',
            color: '#fff',
            border: 'none',
            fontWeight: 600,
            fontSize: 14,
            cursor: value.trim() ? 'pointer' : 'not-allowed'
          }}
        >
          {isLoading ? 'Recording...' : 'Record Activity'}
        </button>
      </form>
    </div>
  );
}
