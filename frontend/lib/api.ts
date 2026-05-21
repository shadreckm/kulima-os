const API_URL = 'https://kulima-os-backend.onrender.com/api/v1';

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
}

export interface SignalData {
  zone: string;
  activity_type: string;
  time_window: string;
  timestamp?: string;
  source?: string;
  user_id?: string;
}

export interface SummaryData {
  zone: string;
  total_patterns: number;
  high_confidence_patterns: number;
  moderate_confidence_patterns: number;
  zones_with_coordinated_demand: string[];
  productive_activities_detected: string[];
  key_finding: string;
  updated_at: string;
}

export interface ProspectusData {
  prospectus_id: string;
  pdf_url: string;
  json_url: string;
  generated_at: string;
}

export const api = {
  // Get summary for a zone
  async getSummary(zone: string): Promise<ApiResponse<SummaryData>> {
    const response = await fetch(`${API_URL}/summary/${zone}`);
    return response.json();
  },

  // Submit a signal
  async submitSignal(signal: SignalData): Promise<ApiResponse<{ signal_id: string; message: string }>> {
    const response = await fetch(`${API_URL}/signal`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(signal),
    });
    return response.json();
  },

  // Generate prospectus
  async generateProspectus(zone: string, userId?: string): Promise<ApiResponse<ProspectusData>> {
    const response = await fetch(`${API_URL}/generate-prospectus`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ zone, user_id: userId }),
    });
    return response.json();
  },

  // Get available zones
  async getZones(): Promise<ApiResponse<{ zones: string[]; total: number }>> {
    const response = await fetch(`${API_URL}/zones`);
    return response.json();
  },
};
