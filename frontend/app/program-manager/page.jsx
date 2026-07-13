'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getRecentSignals, getZoneSummary } from '../../lib/api';

/**
 * KULIMA OS - PROGRAM MANAGER DASHBOARD
 * 
 * Powered by LUMOZA, LUNDAI, and ZENTARI engines.
 */
export default function ProgramManagerDashboard() {
  const router = useRouter();
  const [signals, setSignals] = useState([]);
  const [zoneSummaries, setZoneSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 60000); // 1 minute
    return () => clearInterval(interval);
  }, []);

  async function loadDashboardData() {
    try {
      setError(null);
      
      // 1. Fetch raw activity signals
      const recentSignals = await getRecentSignals(100);
      setSignals(recentSignals);
      
      // 2. Identify active zones
      const zones = [...new Set(recentSignals.map(s => s.zone).filter(Boolean))];
      
      // 3. Fetch Intelligence Engine summaries for top zones
      const summaryPromises = zones.slice(0, 5).map(z => getZoneSummary(z, 'investor'));
      const summaries = await Promise.all(summaryPromises);
      
      const validSummaries = summaries.filter(s => s !== null).sort((a, b) => b.trust_score - a.trust_score);
      
      setZoneSummaries(validSummaries);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      console.error('Dashboard load error:', err);
      setError(err.message);
      setLoading(false);
    }
  }

  // National metrics derived from Engine outputs
  const totalSignals = signals.length;
  const activeZones = [...new Set(signals.map(s => s.zone).filter(Boolean))].length;
  const avgConfidence = zoneSummaries.length > 0
    ? Math.round(zoneSummaries.reduce((sum, s) => sum + (s.trust_score * 100), 0) / zoneSummaries.length)
    : 0;

  const recentSignals = signals.slice(0, 10);
  const topZone = zoneSummaries.length > 0 ? zoneSummaries[0] : null;

  if (loading && signals.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">Loading Intelligence Engines (LUMOZA, LUNDAI, ZENTARI)...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b-2 border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">KULIMA OS</h1>
              <p className="text-sm text-gray-600">Decision Intelligence Platform</p>
            </div>
            <div className="flex items-center gap-4">
              {lastUpdate && (
                <div className="text-right text-sm">
                  <p className="text-gray-600">Intelligence Sync</p>
                  <p className="text-gray-900 font-medium">{lastUpdate.toLocaleTimeString()}</p>
                </div>
              )}
              <button
                onClick={() => router.push('/')}
                className="bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-lg transition-colors font-medium"
              >
                ← Back
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-lg p-4">
            <p className="text-red-800 font-medium">⚠️ Error: {error}</p>
          </div>
        )}

        {topZone && (
          <section className="mb-8 bg-gradient-to-r from-blue-700 to-indigo-800 rounded-2xl shadow-2xl p-8 text-white">
            <div className="flex items-start justify-between mb-6">
              <div>
                <p className="text-blue-200 text-sm font-semibold uppercase tracking-wide mb-2">
                  🏆 Top Verified Prospectus
                </p>
                <h2 className="text-5xl font-bold mb-2">{topZone.zone}</h2>
                <p className="text-xl text-blue-100">
                  {Math.round(topZone.trust_score * 100)}% Coordination Confidence (ZENTARI)
                </p>
              </div>
              <div className="bg-white bg-opacity-20 rounded-xl px-6 py-3 border border-blue-400">
                <p className="text-sm font-semibold tracking-wider">BANKABLE</p>
              </div>
            </div>

            <div className="bg-white bg-opacity-10 rounded-xl p-6 mb-6 backdrop-blur-sm border border-white border-opacity-20">
              <p className="text-lg font-bold mb-2">⚡ LUNDAI RECOMMENDATION:</p>
              <p className="text-xl leading-relaxed">
                {topZone.key_finding}
              </p>
              {topZone.recommended_projects && topZone.recommended_projects.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {topZone.recommended_projects.map(proj => (
                    <span key={proj} className="bg-white text-blue-900 text-sm font-bold px-3 py-1 rounded-full">
                      {proj}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white bg-opacity-10 rounded-lg p-4 backdrop-blur-sm">
                <p className="text-sm text-blue-200 mb-1">High Confidence Patterns</p>
                <p className="text-3xl font-bold">{topZone.high_confidence_patterns}</p>
              </div>
              <div className="bg-white bg-opacity-10 rounded-lg p-4 backdrop-blur-sm">
                <p className="text-sm text-blue-200 mb-1">Productive Activities</p>
                <p className="text-2xl font-bold">{(topZone.productive_activities_detected || []).length} types</p>
              </div>
              <div className="bg-white bg-opacity-10 rounded-lg p-4 backdrop-blur-sm">
                <p className="text-sm text-blue-200 mb-1">Infrastructure Gaps</p>
                <p className="text-2xl font-bold">{(topZone.infrastructure_gaps || []).length} identified</p>
              </div>
            </div>
          </section>
        )}

        <section className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">📊 National Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-gray-400">
              <p className="text-sm font-medium text-gray-600 mb-2">Total Signals</p>
              <p className="text-4xl font-bold text-gray-900">{totalSignals}</p>
              <p className="text-xs text-gray-500 mt-2">Raw ingestion</p>
            </div>
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
              <p className="text-sm font-medium text-gray-600 mb-2">Active Zones</p>
              <p className="text-4xl font-bold text-gray-900">{activeZones}</p>
              <p className="text-xs text-gray-500 mt-2">Coordination tracking</p>
            </div>
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
              <p className="text-sm font-medium text-gray-600 mb-2">Zentari Trust</p>
              <p className="text-4xl font-bold text-gray-900">{avgConfidence}%</p>
              <p className="text-xs text-gray-500 mt-2">Verified coordination</p>
            </div>
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
              <p className="text-sm font-medium text-gray-600 mb-2">Bankable Zones</p>
              <p className="text-4xl font-bold text-gray-900">{zoneSummaries.filter(s => s.trust_score >= 0.7).length}</p>
              <p className="text-xs text-gray-500 mt-2">Ready for investment</p>
            </div>
          </div>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">🎯 Coordination Trust Rankings (LUMOZA & ZENTARI)</h2>
          <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
            <table className="min-w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Rank</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Zone</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Patterns</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Activities</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Trust Score</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {zoneSummaries.map((summary, index) => {
                  const conf = Math.round(summary.trust_score * 100);
                  return (
                    <tr key={summary.zone} className="hover:bg-blue-50 transition-colors">
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                          index === 0 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
                        }`}>
                          {index + 1}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-lg font-bold text-gray-900">{summary.zone}</p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-md font-semibold text-gray-700">{summary.total_patterns} total</p>
                        <p className="text-xs text-green-600 font-medium">{summary.high_confidence_patterns} high confidence</p>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {(summary.productive_activities_detected || []).map(act => (
                            <span key={act} className="text-xs bg-gray-100 px-2 py-1 rounded border border-gray-200 capitalize">
                              {act}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex-1 bg-gray-200 rounded-full h-2 w-24">
                            <div 
                              className={`h-2 rounded-full ${
                                conf >= 75 ? 'bg-green-500' :
                                conf >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${conf}%` }}
                            ></div>
                          </div>
                          <span className="text-md font-bold text-gray-900">{conf}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold tracking-wide ${
                          conf >= 75 ? 'bg-green-100 text-green-800' :
                          conf >= 50 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {conf >= 75 ? 'BANKABLE' : conf >= 50 ? 'EMERGING' : 'NOISY'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
                {zoneSummaries.length === 0 && (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                      No zone intelligence available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">🔔 Raw Ingestion (Live)</h2>
            <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
              <div className="divide-y divide-gray-100">
                {recentSignals.map((signal, index) => (
                  <div key={signal.id || index} className="p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-bold text-gray-900 capitalize">{signal.activity_type || 'Unknown'}</p>
                        <p className="text-sm text-gray-500">{signal.zone}</p>
                      </div>
                      <span className="text-xs text-gray-400">
                        {signal.created_at ? new Date(signal.created_at).toLocaleTimeString() : 'Now'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">💡 Prospectus Generation (LUNDAI)</h2>
            <div className="space-y-4">
              {zoneSummaries.slice(0, 3).map((summary, index) => (
                <div key={summary.zone} className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-bold text-gray-900">{summary.zone}</h3>
                    <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded">Rank {index + 1}</span>
                  </div>
                  <p className="text-sm text-gray-700 mb-4">{summary.key_finding}</p>
                  
                  {summary.infrastructure_gaps && summary.infrastructure_gaps.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs font-bold text-red-600 uppercase mb-1">Identified Gaps:</p>
                      <ul className="text-sm text-gray-600 list-disc list-inside">
                        {summary.infrastructure_gaps.map(gap => <li key={gap}>{gap}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
