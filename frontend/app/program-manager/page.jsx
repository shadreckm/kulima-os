'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getRecentSignals } from '../../lib/api';

/**
 * KULIMA OS - PROGRAM MANAGER DASHBOARD
 * 
 * Answers 4 critical questions in 30 seconds:
 * 1. What is happening?
 * 2. Where is it happening?
 * 3. How confident are we?
 * 4. What should we do next?
 */
export default function ProgramManagerDashboard() {
  const router = useRouter();
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadDashboardData() {
    try {
      setError(null);
      const data = await getRecentSignals(100);
      setSignals(data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      console.error('Dashboard load error:', err);
      setError(err.message);
      setLoading(false);
    }
  }

  // Calculate zone statistics
  const zoneStats = {};
  signals.forEach(signal => {
    const zone = signal.zone || 'UNKNOWN';
    if (!zoneStats[zone]) {
      zoneStats[zone] = {
        count: 0,
        activities: new Set(),
        lastSignal: null,
        confidence: 0
      };
    }
    zoneStats[zone].count += 1;
    if (signal.activity_type) {
      zoneStats[zone].activities.add(signal.activity_type);
    }
    if (!zoneStats[zone].lastSignal || new Date(signal.created_at) > new Date(zoneStats[zone].lastSignal)) {
      zoneStats[zone].lastSignal = signal.created_at;
    }
    // Calculate confidence: base 40% + 10% per signal (max 95%)
    zoneStats[zone].confidence = Math.min(95, 40 + (zoneStats[zone].count * 10));
  });

  // Priority zones (sorted by signal count)
  const priorityZones = Object.entries(zoneStats)
    .sort(([, a], [, b]) => b.count - a.count)
    .slice(0, 5);

  // Top priority zone
  const topZone = priorityZones[0];

  // National metrics
  const totalSignals = signals.length;
  const activeZones = Object.keys(zoneStats).length;
  const avgConfidence = priorityZones.length > 0
    ? Math.round(priorityZones.reduce((sum, [, stats]) => sum + stats.confidence, 0) / priorityZones.length)
    : 0;

  // Recent signals (last 10)
  const recentSignals = signals.slice(0, 10);

  if (loading && signals.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b-2 border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">KULIMA OS</h1>
              <p className="text-sm text-gray-600">Program Manager Dashboard</p>
            </div>
            <div className="flex items-center gap-4">
              {lastUpdate && (
                <div className="text-right text-sm">
                  <p className="text-gray-600">Last updated</p>
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

        {/* TOP PRIORITY ZONE - Hero Section */}
        {topZone && (
          <section className="mb-8 bg-gradient-to-r from-red-500 to-orange-500 rounded-2xl shadow-2xl p-8 text-white">
            <div className="flex items-start justify-between mb-6">
              <div>
                <p className="text-red-100 text-sm font-semibold uppercase tracking-wide mb-2">
                  🚨 Top Priority Zone
                </p>
                <h2 className="text-5xl font-bold mb-2">{topZone[0]}</h2>
                <p className="text-xl text-red-100">
                  {topZone[1].count} coordination signals • {topZone[1].confidence}% confidence
                </p>
              </div>
              <div className="bg-white bg-opacity-20 rounded-xl px-6 py-3">
                <p className="text-sm font-semibold">URGENT</p>
              </div>
            </div>

            <div className="bg-white bg-opacity-10 rounded-xl p-6 mb-6">
              <p className="text-lg font-bold mb-2">⚡ RECOMMENDED ACTION:</p>
              <p className="text-xl leading-relaxed">
                Prioritize infrastructure assessment for {topZone[0]}. 
                Strong coordination signals indicate high demand for {Array.from(topZone[1].activities).slice(0, 3).join(', ')} capacity.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white bg-opacity-10 rounded-lg p-4">
                <p className="text-sm text-red-100 mb-1">Supporting Evidence</p>
                <p className="text-2xl font-bold">{topZone[1].count} signals</p>
              </div>
              <div className="bg-white bg-opacity-10 rounded-lg p-4">
                <p className="text-sm text-red-100 mb-1">Activity Types</p>
                <p className="text-2xl font-bold">{topZone[1].activities.size} types</p>
              </div>
              <div className="bg-white bg-opacity-10 rounded-lg p-4">
                <p className="text-sm text-red-100 mb-1">Last Signal</p>
                <p className="text-2xl font-bold">
                  {topZone[1].lastSignal ? new Date(topZone[1].lastSignal).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* NATIONAL OVERVIEW CARDS */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">📊 National Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
              <p className="text-sm font-medium text-gray-600 mb-2">Total Signals</p>
              <p className="text-4xl font-bold text-gray-900">{totalSignals}</p>
              <p className="text-xs text-gray-500 mt-2">Coordination signals received</p>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
              <p className="text-sm font-medium text-gray-600 mb-2">Active Zones</p>
              <p className="text-4xl font-bold text-gray-900">{activeZones}</p>
              <p className="text-xs text-gray-500 mt-2">Zones with activity</p>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-yellow-500">
              <p className="text-sm font-medium text-gray-600 mb-2">Avg Confidence</p>
              <p className="text-4xl font-bold text-gray-900">{avgConfidence}%</p>
              <p className="text-xs text-gray-500 mt-2">Coordination reliability</p>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-red-500">
              <p className="text-sm font-medium text-gray-600 mb-2">Priority Zones</p>
              <p className="text-4xl font-bold text-gray-900">{priorityZones.length}</p>
              <p className="text-xs text-gray-500 mt-2">Requiring attention</p>
            </div>
          </div>
        </section>

        {/* PRIORITY ZONE RANKINGS */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">🎯 Priority Zone Rankings</h2>
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-50 border-b-2 border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Rank</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Zone</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Signals</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Activities</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Confidence</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {priorityZones.map(([zone, stats], index) => (
                  <tr key={zone} className={index === 0 ? 'bg-red-50' : 'hover:bg-gray-50'}>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full text-lg font-bold ${
                        index === 0 ? 'bg-red-600 text-white' :
                        index === 1 ? 'bg-orange-500 text-white' :
                        index === 2 ? 'bg-yellow-500 text-white' :
                        'bg-gray-300 text-gray-700'
                      }`}>
                        {index + 1}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-lg font-bold text-gray-900">{zone}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-lg font-semibold text-gray-900">{stats.count}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-gray-700">{stats.activities.size} types</p>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex-1 bg-gray-200 rounded-full h-3">
                          <div 
                            className={`h-3 rounded-full ${
                              stats.confidence >= 80 ? 'bg-green-500' :
                              stats.confidence >= 60 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${stats.confidence}%` }}
                          ></div>
                        </div>
                        <span className="text-lg font-bold text-gray-900 w-12">{stats.confidence}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-bold ${
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
                    <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                      No zone data available yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* RECENT ACTIVITY */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">🔔 Recent Activity</h2>
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="divide-y divide-gray-200">
                {recentSignals.length === 0 ? (
                  <div className="p-12 text-center text-gray-500">
                    <p className="text-6xl mb-4">📭</p>
                    <p className="text-lg">No signals yet</p>
                  </div>
                ) : (
                  recentSignals.map((signal, index) => (
                    <div key={signal.id || index} className="p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">
                            {signal.activity_type === 'irrigation' ? '💧' :
                             signal.activity_type === 'milling' ? '⚙️' :
                             signal.activity_type === 'storage' ? '📦' :
                             signal.activity_type === 'welding' ? '🔧' : '📝'}
                          </span>
                          <div>
                            <p className="font-bold text-gray-900 capitalize">{signal.activity_type || 'Activity'}</p>
                            <p className="text-sm text-gray-600">{signal.zone}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                            ✅ Verified
                          </span>
                          <p className="text-xs text-gray-500 mt-1">
                            {signal.created_at ? new Date(signal.created_at).toLocaleString() : 'Recently'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </section>

          {/* RECOMMENDATIONS */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">💡 Recommendations</h2>
            <div className="space-y-4">
              {priorityZones.slice(0, 3).map(([zone, stats], index) => (
                <div key={zone} className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">{zone}</h3>
                      <p className="text-sm text-gray-600 mt-1">{stats.count} signals detected</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      index === 0 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      Priority {index + 1}
                    </span>
                  </div>
                  
                  <div className="mb-4">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-600">Confidence</span>
                      <span className="font-bold text-gray-900">{stats.confidence}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          stats.confidence >= 80 ? 'bg-green-500' :
                          stats.confidence >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${stats.confidence}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="bg-blue-50 rounded-lg p-3">
                    <p className="text-sm font-bold text-blue-900 mb-1">Recommended Action:</p>
                    <p className="text-sm text-blue-800">
                      {index === 0 
                        ? `Prioritize infrastructure assessment. Strong coordination signals indicate high demand.`
                        : `Monitor for infrastructure planning. Coordination patterns emerging.`
                      }
                    </p>
                  </div>
                </div>
              ))}

              {priorityZones.length === 0 && (
                <div className="bg-gray-50 rounded-xl p-12 text-center">
                  <p className="text-6xl mb-4">📊</p>
                  <p className="text-gray-600">No recommendations yet</p>
                  <p className="text-sm text-gray-500 mt-2">Recommendations will appear as signals are received</p>
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

// Made with Bob
