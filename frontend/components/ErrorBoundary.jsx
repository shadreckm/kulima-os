'use client';

import React from 'react';
import styles from '../styles/zoneDashboard.module.css';

/**
 * Error Boundary Component
 * Catches JavaScript errors and displays a fallback UI
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className={styles.errorBoundary}>
          <div className={styles.errorBoundaryTitle}>
            ⚠️ Something went wrong
          </div>
          <div className={styles.errorBoundaryMessage}>
            {this.state.error?.message || 'An unexpected error occurred. Please refresh the page.'}
          </div>
          <button
            style={{
              marginTop: '12px',
              padding: '8px 16px',
              backgroundColor: '#721c24',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
          >
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Async boundary wrapper - handles async errors in components
 */
export function withErrorBoundary(Component) {
  return function ErrorBoundaryWrapper(props) {
    return (
      <ErrorBoundary>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}

/**
 * Input Validator - Client-side validation
 */
export const validators = {
  isNotEmpty: (value, fieldName) => {
    if (!value || value.trim() === '') {
      return `${fieldName} is required`;
    }
    return null;
  },

  isValidZone: (zone) => {
    const validZones = ['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'];
    if (!validZones.includes(zone.toUpperCase())) {
      return `Invalid zone. Must be one of: ${validZones.join(', ')}`;
    }
    return null;
  },

  isValidActivity: (activity) => {
    const validActivities = ['irrigation', 'milling', 'cold storage', 'welding', 'trading', 'storage'];
    if (!validActivities.includes(activity.toLowerCase())) {
      return `Invalid activity. Must be one of: ${validActivities.join(', ')}`;
    }
    return null;
  },

  isValidTimeWindow: (timeWindow) => {
    const validWindows = ['morning', 'afternoon', 'evening', 'midday'];
    if (!validWindows.includes(timeWindow.toLowerCase())) {
      return `Invalid time window. Must be one of: ${validWindows.join(', ')}`;
    }
    return null;
  },

  validateSignal: (activity, zone, timeWindow) => {
    const errors = [];
    
    const activityError = validators.isValidActivity(activity);
    if (activityError) errors.push(activityError);
    
    const zoneError = validators.isValidZone(zone);
    if (zoneError) errors.push(zoneError);
    
    const timeWindowError = validators.isValidTimeWindow(timeWindow);
    if (timeWindowError) errors.push(timeWindowError);
    
    return errors.length > 0 ? errors.join('; ') : null;
  }
};

/**
 * Hook for form validation
 */
export function useFormValidation() {
  const [errors, setErrors] = React.useState({});

  const validate = (field, value, validator) => {
    const error = validator(value);
    setErrors(prev => ({
      ...prev,
      [field]: error
    }));
    return error;
  };

  const validateAll = (data, validationRules) => {
    const newErrors = {};
    Object.keys(validationRules).forEach(field => {
      const error = validationRules[field](data[field]);
      if (error) newErrors[field] = error;
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const clearErrors = () => setErrors({});

  return { errors, validate, validateAll, clearErrors };
}
