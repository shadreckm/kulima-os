'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function Dashboard() {
  const [selectedZone, setSelectedZone] = useState('');
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const zones = ['MZUZU', 'LILONGWE', 'BLANTYRE', 'ZOMBA'];

  const fetchSummary = async () => {
    if (!selectedZone) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await api.getSummary(selectedZone);
      if (response.status === 'success') {
        setSummary(response.data);
      } else {
        setError(response.data.error || 'Failed to fetch summary');
      }
    } catch (err) {
      setError('Error fetching summary. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Activity Summary</h2>
      
      <div className="mb-6">
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
        onClick={fetchSummary}
        disabled={!selectedZone || loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Loading...' : 'View Summary'}
      </button>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {summary && (
        <div className="mt-6 space-y-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Insight</h3>
            <p className="text-blue-800">{summary.key_finding}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="text-sm font-medium text-green-900">Total Activities Detected</h4>
              <p className="text-2xl font-bold text-green-700">{summary.total_patterns}</p>
            </div>
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="text-sm font-medium text-yellow-900">Strong Patterns</h4>
              <p className="text-2xl font-bold text-yellow-700">{summary.high_confidence_patterns}</p>
            </div>
          </div>

          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Main Activities</h4>
            <div className="flex flex-wrap gap-2">
              {summary.productive_activities_detected.map((activity) => (
                <span
                  key={activity}
                  className="px-3 py-1 bg-gray-200 text-gray-800 rounded-full text-sm"
                >
                  {activity}
                </span>
              ))}
            </div>
          </div>

          <div className="text-sm text-gray-500">
            Last updated: {new Date(summary.updated_at).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
}
