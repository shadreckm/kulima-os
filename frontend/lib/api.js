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
      return await response.json();
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

export async function fetchSummaryData(zone, mode = 'investor') {
  try {
    const params = new URLSearchParams({ mode });
    const data = await fetchWithRetry(`${BASE_URL}/summary/${zone}?${params}`, { cache: 'no-store' });
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
    body: JSON.stringify({ zone, raw_text, source: 'web' })
  });
}

export async function generateProspectusReport(zone) {
  return fetchWithRetry(`${BASE_URL}/generate-prospectus`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ zone, preview: true })
  });
}

/**
 * Download zone prospectus PDF via blob fetch (correct endpoint, no duplicate /api/v1).
 */
export async function downloadProspectusPdf(zone, mode = 'investor') {
  const params = new URLSearchParams({ mode });
  const url = `${BASE_URL}/prospectus/${zone.toLowerCase()}/pdf?${params}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`PDF download failed: ${response.status}`);
  }
  const blob = await response.blob();
  const blobUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = blobUrl;
  anchor.download = `kulima_prospectus_${zone.toLowerCase()}.pdf`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(blobUrl);
}

export { BASE_URL };
