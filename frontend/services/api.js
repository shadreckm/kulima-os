/**
 * API Service Layer
 * Centralized API client for all backend interactions
 * Handles error handling, retries, and caching
 */

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || '/api/v1').replace(/\/$/, '');

class APIClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.timeout = 10000;
    this.cache = new Map();
    this.cacheExpiry = new Map();
  }

  /**
   * Generic fetch wrapper with error handling and retries
   */
  async fetch(endpoint, options = {}, retries = 1) {
    const url = `${this.baseURL}${endpoint}`;
    const cacheKey = `${options.method || 'GET'}:${endpoint}`;
    
    // Check cache for GET requests
    if ((options.method || 'GET') === 'GET' && this.cache.has(cacheKey)) {
      const expiry = this.cacheExpiry.get(cacheKey);
      if (expiry && expiry > Date.now()) {
        return JSON.parse(this.cache.get(cacheKey));
      }
      this.cache.delete(cacheKey);
      this.cacheExpiry.delete(cacheKey);
    }

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Cache GET responses for 5 minutes
        if ((options.method || 'GET') === 'GET') {
          this.cache.set(cacheKey, JSON.stringify(data));
          this.cacheExpiry.set(cacheKey, Date.now() + 5 * 60 * 1000);
        }

        return data;
      } catch (error) {
        if (attempt === retries) {
          console.error(`API Error: ${endpoint}`, error);
          throw error;
        }
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
      }
    }
  }

  /**
   * Signal endpoints
   */
  async createSignal(signalData) {
    return this.fetch('/signal', {
      method: 'POST',
      body: JSON.stringify(signalData),
    });
  }

  async getRecentSignals(limit = 15) {
    return this.fetch(`/recent-signals?limit=${limit}`);
  }

  /**
   * Zone endpoints
   */
  async getZoneData(zone) {
    return this.fetch(`/zone/${zone}`);
  }

  async getZoneSummary(zone) {
    return this.fetch(`/summary/${zone}`);
  }

  async getZonePatterns(zone) {
    return this.fetch(`/patterns/${zone}`);
  }

  async getInfrastructureGaps(zone) {
    return this.fetch(`/infrastructure-gaps/${zone}`);
  }

  /**
   * Prospectus endpoints
   */
  async generateProspectus(zone, userId) {
    return this.fetch('/generate-prospectus', {
      method: 'POST',
      body: JSON.stringify({ zone, user_id: userId }),
    });
  }

  /**
   * Health check
   */
  async getHealth() {
    return this.fetch('/health', { cache: 'no-store' });
  }

  /**
   * Clear cache
   */
  clearCache() {
    this.cache.clear();
    this.cacheExpiry.clear();
  }

  /**
   * Clear specific cache entry
   */
  clearCacheFor(endpoint) {
    const keys = Array.from(this.cache.keys()).filter(k => k.includes(endpoint));
    keys.forEach(k => {
      this.cache.delete(k);
      this.cacheExpiry.delete(k);
    });
  }
}

export const apiClient = new APIClient();

/**
 * Error handling utility
 */
export function getErrorMessage(error) {
  if (error instanceof Error) {
    if (error.name === 'AbortError') {
      return 'Request timed out. Please try again.';
    }
    return error.message;
  }
  return 'An unexpected error occurred. Please try again.';
}

/**
 * Hook for API calls with loading and error states
 */
export function useAPI() {
  return {
    apiClient,
    getErrorMessage,
  };
}
