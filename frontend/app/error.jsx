'use client';
 
import { useEffect } from 'react';
 
export default function Error({ error, reset }) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
  }, [error]);
 
  return (
    <div style={{ padding: '2rem', textAlign: 'center', fontFamily: 'system-ui, sans-serif' }}>
      <h2>Something went wrong!</h2>
      <p style={{ color: '#666', marginBottom: '1rem' }}>We experienced an unexpected error loading the Kulima OS command center.</p>
      <button
        onClick={
          // Attempt to recover by trying to re-render the segment
          () => reset()
        }
        style={{
          padding: '0.75rem 1.5rem',
          backgroundColor: '#00ff88',
          color: '#000',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontWeight: 'bold'
        }}
      >
        Try again
      </button>
    </div>
  );
}
