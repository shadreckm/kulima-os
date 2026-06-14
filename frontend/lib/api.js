/**
 * API Service for Kulima OS Frontend
 * Handles fetching, error handling, and retries.
 */

const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || '/api/v1').replace(/\/$/, '');

/**
 * Helper to perform fetch with retries
 */
async function fetchWithRetry(url, options = {}, retries = 3, backoff = 300) {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      if (response.status >= 500 && retries > 0) {
        throw new Error(`Server error: ${response.status}`);
      }
      return await response.json(); // May contain structured error
    }
    return await response.json();
  } catch (error) {
    if (retries > 0) {
      await new Promise(resolve => setTimeout(resolve, backoff));
      return fetchWithRetry(url, options, retries - 1, backoff * 2);
    }
    throw error;
  }
}

export async function fetchSummaryData(zone) {
  try {
    const data = await fetchWithRetry(`${BASE_URL}/summary/${zone}`, { cache: 'no-store' });
    if (data?.status === 'success') {
      return data.data;
    }
    return null;
  } catch (error) {
    console.error("Failed to fetch summary:", error);
    return null;
  }
}

export async function fetchRecentSignalsData() {
  try {
    const data = await fetchWithRetry(`${BASE_URL}/recent-signals`, { cache: 'no-store' });
    if (data?.success && Array.isArray(data.data)) {
      return data.data.slice(0, 12);
    }
    return [];
  } catch (error) {
    console.error("Failed to fetch recent signals:", error);
    return [];
  }
}

export async function submitActivitySignal(zone, raw_text) {
  return fetchWithRetry(`${BASE_URL}/signal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // Zero-PII compliance: no user_id or personal data
    body: JSON.stringify({ zone, raw_text, source: 'web' })
  });
}

export async function generateProspectusReport(zone) {
  return fetchWithRetry(`${BASE_URL}/generate-prospectus`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // Zero-PII compliance: no user_id
    body: JSON.stringify({ zone, preview: true })
  });
}
