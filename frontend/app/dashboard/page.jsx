'use client';

import { useState, useEffect } from 'react';
import { fetchSummaryData, fetchRecentSignalsData } from '../../lib/api';

/**
 * KULIMA OS - PROGRAM MANAGER DASHBOARD
 * 
 * Designed for: Grace Banda (NGO Program Manager)
 * Purpose: Infrastructure investment decision support
 * 
 * Answers 4 critical questions:
 * 1. What is happening?
 * 2. Where is it happening?
 * 3. How confident are we?
 * 4. What should we do next?
 * 
 * Style: Africa CDC + UNDP Monitoring + Crisis Early Warning
 */

export default function ProgramManagerDashboard() {
  const [loading, setLoading] = useState(true);
  const [signals, setSignals] = useState([]);
  const [zoneStats, setZoneStats] = useState({});
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadDashboardData() {
    try {
      setLoading(true);
      setError(null);

      // Fetch recent signals
      const signalsData = await fetchRecentSignalsData();
      
      // Handle nested data structure
      const signalsList = Array.isArray(signalsData) 
        ? signalsData 
        : (signalsData?.data || []);

      setSignals(signalsList);
      setLastUpdate(new Date());

      // Calculate zone statistics
      const stats = {};
      signalsList.forEach(signal => {
        const zone = signal.zone || 'UNKNOWN';
        if (!stats[zone]) {
          stats[zone] = {
            count: 0,
            activities: new Set(),
            lastSignal: null,
            confidence: 0
          };
        }
        stats[zone].count += 1;
        if (signal.activity_type) {
          stats[zone].activities.add(signal.activity_type);
        }
        if (!stats[zone].lastSignal || new Date(signal.created_at) > new Date(stats[zone].lastSignal)) {
          stats[zone].lastSignal = signal.created_at;
        }
        // Calculate simple confidence based on signal count
        stats[zone].confidence = Math.min(95, 40 + (stats[zone].count * 10));
      });

      setZoneStats(stats);
      setLoading(false);
    } catch (err) {
      console.error('Dashboard load error:', err);
      setError(err.message);
      setLoading(false);
    }
  }

  // Calculate priority zones (most signals = highest priority)
  const priorityZones = Object.entries(zoneStats)
    .sort(([, a], [, b]) => b.count - a.count)
    .slice(0, 5);

  // Get recent signals (last 10)
  const recentSignals = signals.slice(0, 10);

  // Calculate national statistics
  const totalSignals = signals.length;
  const activeZones = Object.keys(zoneStats).length;
  const avgConfidence = priorityZones.length > 0
    ? Math.round(priorityZones.reduce((sum, [, stats]) => sum + stats.confidence, 0) / priorityZones.length)
    : 0;

  if (loading && signals.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">KULIMA OS</h1>
              <p className="text-sm text-gray-600">Infrastructure Planning Intelligence</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Program Manager Dashboard</p>
              {lastUpdate && (
                <p className="text-xs text-gray-500">
                  Last updated: {lastUpdate.toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">Error loading data: {error}</p>
          </div>
        )}

        {/* National Summary Cards */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">National Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Total Signals */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Signals</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{totalSignals}</p>
                </div>
                <div className="bg-blue-100 rounded-full p-3">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">Coordination signals received</p>
            </div>

            {/* Active Zones */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Zones</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{activeZones}</p>
                </div>
                <div className="bg-green-100 rounded-full p-3">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">Zones with coordination activity</p>
            </div>

            {/* Average Confidence */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Confidence</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{avgConfidence}%</p>
                </div>
                <div className="bg-yellow-100 rounded-full p-3">
                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">Coordination reliability score</p>
            </div>

            {/* Priority Zones */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Priority Zones</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{priorityZones.length}</p>
                </div>
                <div className="bg-red-100 rounded-full p-3">
                  <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">Zones requiring attention</p>
            </div>
          </div>
        </section>

        {/* Priority Zone Rankings */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Priority Zone Rankings</h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Zone</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Signals</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Activities</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Signal</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {priorityZones.map(([zone, stats], index) => (
                  <tr key={zone} className={index === 0 ? 'bg-red-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                        index === 0 ? 'bg-red-600 text-white' :
                        index === 1 ? 'bg-orange-500 text-white' :
                        index === 2 ? 'bg-yellow-500 text-white' :
                        'bg-gray-300 text-gray-700'
                      }`}>
                        {index + 1}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{zone}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{stats.count}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{stats.activities.size} types</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                          <div 
                            className={`h-2 rounded-full ${
                              stats.confidence >= 80 ? 'bg-green-500' :
                              stats.confidence >= 60 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${stats.confidence}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-gray-900">{stats.confidence}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.lastSignal ? new Date(stats.lastSignal).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        index === 0 ? 'bg-red-100 text-red-800' :
                        index <= 2 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {index === 0 ? 'URGENT' : index <= 2 ? 'HIGH' : 'MONITOR'}
                      </span>
                    </td>
                  </tr>
                ))}
                {priorityZones.length === 0 && (
                  <tr>
                    <td colSpan="7" className="px-6 py-4 text-center text-sm text-gray-500">
                      No zone data available yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Signals Table */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Coordination Signals</h2>
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Zone</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Activity</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {recentSignals.map((signal, index) => (
                      <tr key={signal.id || index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="text-sm font-medium text-gray-900">{signal.zone || 'UNKNOWN'}</span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm text-gray-600">{signal.activity_type || 'General'}</span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {signal.created_at ? new Date(signal.created_at).toLocaleString() : 'N/A'}
                        </td>
                      </tr>
                    ))}
                    {recentSignals.length === 0 && (
                      <tr>
                        <td colSpan="3" className="px-4 py-8 text-center text-sm text-gray-500">
                          No signals received yet
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* Recommendation Panel */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recommended Actions</h2>
            <div className="space-y-4">
              {priorityZones.slice(0, 3).map(([zone, stats], index) => (
                <div key={zone} className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{zone}</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        {stats.count} coordination signals detected
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      index === 0 ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      Priority {index + 1}
                    </span>
                  </div>
                  
                  <div className="mb-4">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-600">Coordination Confidence</span>
                      <span className="font-semibold text-gray-900">{stats.confidence}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          stats.confidence >= 80 ? 'bg-green-500' :
                          stats.confidence >= 60 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${stats.confidence}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="bg-blue-50 rounded p-3 mb-3">
                    <p className="text-sm font-medium text-blue-900 mb-1">Recommended Action:</p>
                    <p className="text-sm text-blue-800">
                      {index === 0 
                        ? `Prioritize infrastructure assessment for ${zone}. Strong coordination signals indicate high demand.`
                        : `Monitor ${zone} for infrastructure planning. Coordination patterns emerging.`
                      }
                    </p>
                  </div>

                  <div className="flex items-center text-xs text-gray-500">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Last signal: {stats.lastSignal ? new Date(stats.lastSignal).toLocaleDateString() : 'N/A'}
                  </div>
                </div>
              ))}

              {priorityZones.length === 0 && (
                <div className="bg-gray-50 rounded-lg p-8 text-center">
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-gray-600">No recommendations yet</p>
                  <p className="text-sm text-gray-500 mt-1">Recommendations will appear as coordination signals are received</p>
                </div>
              )}
            </div>
          </section>
        </div>

        {/* Evidence Overview */}
        <section className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Evidence & Trust</h2>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-3">
                  <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-2xl font-bold text-gray-900">{totalSignals}</p>
                <p className="text-sm text-gray-600">Verified Signals</p>
              </div>
              <div className="text-center">
                <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-3">
                  <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <p className="text-2xl font-bold text-gray-900">{avgConfidence}%</p>
                <p className="text-sm text-gray-600">Trust Score</p>
              </div>
              <div className="text-center">
                <div className="bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-3">
                  <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-2xl font-bold text-gray-900">0</p>
                <p className="text-sm text-gray-600">Evidence Items</p>
              </div>
            </div>
            <div className="mt-6 pt-6 border-t border-gray-200">
              <p className="text-sm text-gray-600 text-center">
                Evidence layer operational. Upload photos and documents to strengthen coordination confidence.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

// Made with Bob
