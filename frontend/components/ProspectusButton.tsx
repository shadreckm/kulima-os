'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

export default function ProspectusButton() {
  const [selectedZone, setSelectedZone] = useState('');
  const [loading, setLoading] = useState(false);
  const [prospectus, setProspectus] = useState<any>(null);
  const [error, setError] = useState('');

  const zones = ['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'];

  const handleGenerate = async () => {
    if (!selectedZone) return;
    
    setLoading(true);
    setError('');
    setProspectus(null);
    
    try {
      const response = await api.generateProspectus(selectedZone);
      if (response.status === 'success') {
        setProspectus(response.data);
      } else {
        setError(response.data.error || 'Failed to generate report');
      }
    } catch (err) {
      setError('Error generating report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Generate Report</h2>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Zone
        </label>
        <select
          value={selectedZone}
          onChange={(e) => setSelectedZone(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Choose a zone...</option>
          {zones.map((zone) => (
            <option key={zone} value={zone}>
              {zone}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={handleGenerate}
        disabled={!selectedZone || loading}
        className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Generating...' : 'Generate Report'}
      </button>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {prospectus && (
        <div className="mt-6 space-y-4">
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="text-lg font-semibold text-green-900 mb-2">
              Report Generated Successfully!
            </h3>
            <p className="text-green-800 text-sm mb-4">
              Report ID: {prospectus.prospectus_id}
            </p>
            
            <div className="space-y-2">
              <a
                href={`https://kulima-os-backend.onrender.com${prospectus.pdf_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 text-center transition-colors"
              >
                Download PDF
              </a>
              <a
                href={`https://kulima-os-backend.onrender.com${prospectus.json_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 text-center transition-colors"
              >
                Download JSON
              </a>
            </div>
          </div>

          <div className="text-sm text-gray-500">
            Generated at: {new Date(prospectus.generated_at).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
}
