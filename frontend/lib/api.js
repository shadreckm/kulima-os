// KULIMA OS - API Client
// Connects frontend to Render backend with proper error handling

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://kulima-os-backend.onrender.com';
const API_BASE = `${BACKEND_URL}/api/v1`;

/**
 * Enhanced fetch with detailed error logging
 */
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  try {
    console.log(`[API] ${options.method || 'GET'} ${url}`);
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const contentType = response.headers.get('content-type') || '';
    let data;

    if (contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      data = { message: text };
    }

    if (!response.ok) {
      console.error(`[API ERROR] ${response.status}:`, data);
      throw new Error(data.message || data.error || `HTTP ${response.status}`);
    }

    console.log(`[API SUCCESS] ${url}:`, data);
    return data;

  } catch (error) {
    console.error(`[API FAILED] ${url}:`, error.message);
    throw error;
  }
}

/**
 * Submit coordination signal (Farmer)
 */
export async function submitSignal(zone, activityType, timeWindow, rawText = '') {
  try {
    const payload = {
      zone: zone.toUpperCase(),
      activity_type: activityType,
      time_window: timeWindow,
      raw_text: rawText || `${activityType} in ${zone} during ${timeWindow}`,
      source: 'web',
      timestamp: new Date().toISOString()
    };

    const result = await apiFetch('/signal', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    // Backend returns: { success: true, status: "success", data: { signal_id, message } }
    if (result.success && result.data) {
      return {
        success: true,
        signalId: result.data.signal_id,
        message: result.data.message || 'Signal submitted successfully'
      };
    }

    throw new Error(result.message || 'Signal submission failed');

  } catch (error) {
    console.error('[submitSignal] Error:', error);
    return {
      success: false,
      error: error.message || 'Failed to submit signal'
    };
  }
}

/**
 * Get recent signals (Program Manager)
 */
export async function getRecentSignals(limit = 50) {
  try {
    const result = await apiFetch(`/recent-signals?limit=${limit}`);
    
    // Backend returns: { success: true, status: "success", data: [...signals] }
    if (result.success && Array.isArray(result.data)) {
      return result.data;
    }

    console.warn('[getRecentSignals] Unexpected response format:', result);
    return [];

  } catch (error) {
    console.error('[getRecentSignals] Error:', error);
    return [];
  }
}

/**
 * Get signals for specific zone (Program Manager)
 */
export async function getZoneSignals(zone, limit = 100) {
  try {
    const result = await apiFetch(`/signals/${zone.toUpperCase()}?limit=${limit}`);
    
    // Backend returns: { status: "success", data: { zone, signals: [...], pagination } }
    if (result.status === 'success' && result.data && Array.isArray(result.data.signals)) {
      return result.data.signals;
    }

    console.warn('[getZoneSignals] Unexpected response format:', result);
    return [];

  } catch (error) {
    console.error('[getZoneSignals] Error:', error);
    return [];
  }
}

/**
 * Get all signals with filtering (Program Manager)
 */
export async function getAllSignals(filters = {}) {
  try {
    const params = new URLSearchParams();
    if (filters.zone) params.append('zone', filters.zone.toUpperCase());
    if (filters.activity_type) params.append('activity_type', filters.activity_type);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);

    const result = await apiFetch(`/signals?${params.toString()}`);
    
    // Backend returns: { status: "success", data: { zone, signals: [...], pagination } }
    if (result.status === 'success' && result.data && Array.isArray(result.data.signals)) {
      return {
        signals: result.data.signals,
        pagination: result.data.pagination
      };
    }

    console.warn('[getAllSignals] Unexpected response format:', result);
    return { signals: [], pagination: null };

  } catch (error) {
    console.error('[getAllSignals] Error:', error);
    return { signals: [], pagination: null };
  }
}

/**
 * Health check
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`);
    const data = await response.json();
    return {
      healthy: response.ok && (data.status === 'healthy' || data.status === 'OK'),
      data
    };
  } catch (error) {
    console.error('[checkHealth] Error:', error);
    return { healthy: false, error: error.message };
  }
}

export { API_BASE, BACKEND_URL };

// Made with Bob
