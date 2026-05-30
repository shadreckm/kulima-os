'use client';

/**
 * Reusable UI Components Library
 * Standardized components for consistent UI across the application
 */

import styles from '../styles/zoneDashboard.module.css';

/**
 * Card Component - Base container with consistent styling
 */
export function Card({ children, className = '' }) {
  return (
    <div className={`${styles.card} ${className}`}>
      {children}
    </div>
  );
}

/**
 * CardTitle Component - Standardized card title
 */
export function CardTitle({ children }) {
  return <div className={styles.cardTitle}>{children}</div>;
}

/**
 * Button Component - Primary button
 */
export function Button({
  onClick,
  disabled = false,
  loading = false,
  children,
  variant = 'primary',
  className = ''
}) {
  const buttonClass = variant === 'primary' ? styles.buttonPrimary : styles.buttonSecondary;
  return (
    <button
      className={`${styles.button} ${buttonClass} ${disabled ? styles.loading : ''} ${className}`}
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading ? '...' : children}
    </button>
  );
}

/**
 * Input Component - Standardized input field
 */
export function Input({
  type = 'text',
  placeholder = '',
  value,
  onChange,
  disabled = false,
  required = false
}) {
  return (
    <input
      className={styles.inputField}
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      disabled={disabled}
      required={required}
    />
  );
}

/**
 * Select Component - Standardized dropdown
 */
export function Select({ options, value, onChange, label }) {
  return (
    <div className={styles.zoneSelector}>
      {label && <label className={styles.zoneSelectorLabel}>{label}</label>}
      <select className={styles.zoneSelect} value={value} onChange={onChange}>
        {options.map(opt => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}

/**
 * Message Component - Success/Error/Info messages
 */
export function Message({ type = 'info', children }) {
  if (!children) return null;
  
  const messageClass = {
    success: styles.messageSuccess,
    error: styles.messageError,
    info: styles.messageInfo,
  }[type] || styles.messageInfo;

  return <div className={`${styles.message} ${messageClass}`}>{children}</div>;
}

/**
 * Toast Component - Bottom-right notification
 */
export function Toast({ message }) {
  if (!message) return null;
  
  return <div className={styles.toast}>{message}</div>;
}

/**
 * Loading Spinner Component
 */
export function Spinner() {
  return (
    <div style={{
      display: 'inline-block',
      width: '16px',
      height: '16px',
      border: '2px solid #e0e8e4',
      borderTop: '2px solid #2d6a4f',
      borderRadius: '50%',
      animation: 'spin 0.8s linear infinite'
    }}>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

/**
 * Grid Component - Responsive grid layout
 */
export function Grid({ children, columns = 2 }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${columns}, 1fr)`,
      gap: '24px',
      '@media (max-width: 768px)': {
        gridTemplateColumns: '1fr'
      }
    }}>
      {children}
    </div>
  );
}

/**
 * StatBox Component - For displaying key metrics
 */
export function StatBox({ label, value, color = '#2d6a4f' }) {
  return (
    <div className={styles.insightBox}>
      <div className={styles.insightValue} style={{ color }}>
        {value}
      </div>
      <div className={styles.insightLabel}>{label}</div>
    </div>
  );
}

/**
 * ActivityItem Component - For displaying individual activities
 */
export function ActivityItem({ activity, zone, time, description }) {
  return (
    <div className={styles.feedItem}>
      <div className={styles.feedItemTitle}>
        {activity} • {time}
      </div>
      <div className={styles.feedItemDescription}>
        {description || `Recorded in ${zone}`}
      </div>
    </div>
  );
}

/**
 * ButtonGroup Component - Horizontal button layout
 */
export function ButtonGroup({ children }) {
  return <div className={styles.buttonGroup}>{children}</div>;
}

/**
 * Divider Component
 */
export function Divider() {
  return (
    <div style={{
      height: '1px',
      backgroundColor: '#e0e8e4',
      margin: '16px 0'
    }} />
  );
}

/**
 * Badge Component - For tags and labels
 */
export function Badge({ children, variant = 'primary' }) {
  const bgColor = variant === 'primary' ? '#e7f6f1' : '#fff9e6';
  const textColor = variant === 'primary' ? '#1f4d38' : '#8b6914';
  
  return (
    <div style={{
      display: 'inline-block',
      padding: '4px 8px',
      borderRadius: '6px',
      backgroundColor: bgColor,
      color: textColor,
      fontSize: '11px',
      fontWeight: '600'
    }}>
      {children}
    </div>
  );
}

/**
 * Section Component - Wrapper for logical sections
 */
export function Section({ title, children, className = '' }) {
  return (
    <Card className={className}>
      {title && <CardTitle>{title}</CardTitle>}
      {children}
    </Card>
  );
}
