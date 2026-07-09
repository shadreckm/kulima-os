'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { submitSignal, getRecentSignals } from '../../lib/api';

/**
 * KULIMA OS - FARMER VIEW
 * 
 * Simple interface for farmers to:
 * 1. Submit coordination signals
 * 2. View their recent reports
 * 3. See submission status
 */
export default function FarmerView() {
  const router = useRouter();
  
  // Form state
  const [zone, setZone] = useState('EKWENDENI');
  const [activityType, setActivityType] = useState('irrigation');
  const [timeWindow, setTimeWindow] = useState('morning');
  const [submitting, setSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null);
  
  // Reports state
  const [myReports, setMyReports] = useState([]);
  const [loading, setLoading] = useState(true);

  // Load recent signals on mount
  useEffect(() => {
    loadMyReports();
  }, []);

  async function loadMyReports() {
    setLoading(true);
    try {
      const signals = await getRecentSignals(10);
      setMyReports(signals);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setSubmitStatus(null);

    try {
      const result = await submitSignal(zone, activityType, timeWindow);
      
      if (result.success) {
        setSubmitStatus({
          type: 'success',
          message: result.message || 'Report submitted successfully!',
          signalId: result.signalId
        });
        
        // Reload reports after successful submission
        setTimeout(() => {
          loadMyReports();
        }, 1000);
        
      } else {
        setSubmitStatus({
          type: 'error',
          message: result.error || 'Failed to submit report. Please try again.'
        });
      }
    } catch (error) {
      setSubmitStatus({
        type: 'error',
        message: 'Network error. Please check your connection and try again.'
      });
    } finally {
      setSubmitting(false);
    }
  }

  const zones = ['EKWENDENI', 'MHUJU', 'BWENGU', 'RUMPHI', 'EUTHINI', 'MZUZU', 'MZIMBA'];
  const activities = [
    { value: 'irrigation', label: '💧 Irrigation' },
    { value: 'milling', label: '⚙️ Milling' },
    { value: 'storage', label: '📦 Cold Storage' },
    { value: 'welding', label: '🔧 Welding' },
    { value: 'trading', label: '🛒 Trading' },
    { value: 'transport', label: '🚚 Transport' }
  ];
  const timeWindows = [
    { value: 'morning', label: '🌅 Morning (6am-12pm)' },
    { value: 'afternoon', label: '☀️ Afternoon (12pm-6pm)' },
    { value: 'evening', label: '🌙 Evening (6pm-10pm)' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-green-600 text-white shadow-lg">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">🌾 Farmer Portal</h1>
              <p className="text-green-100 mt-1">Submit your coordination signals</p>
            </div>
            <button
              onClick={() => router.push('/')}
              className="bg-green-700 hover:bg-green-800 px-4 py-2 rounded-lg transition-colors"
            >
              ← Back
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Submit Report Form */}
        <section className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">📝 Submit New Report</h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Activity Type */}
            <div>
              <label className="block text-lg font-medium text-gray-700 mb-3">
                What activity do you need?
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {activities.map((activity) => (
                  <button
                    key={activity.value}
                    type="button"
                    onClick={() => setActivityType(activity.value)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      activityType === activity.value
                        ? 'border-green-600 bg-green-50 text-green-900'
                        : 'border-gray-200 hover:border-green-300'
                    }`}
                  >
                    <div className="text-2xl mb-1">{activity.label.split(' ')[0]}</div>
                    <div className="text-sm font-medium">{activity.label.split(' ').slice(1).join(' ')}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Time Window */}
            <div>
              <label className="block text-lg font-medium text-gray-700 mb-3">
                When do you need it?
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {timeWindows.map((window) => (
                  <button
                    key={window.value}
                    type="button"
                    onClick={() => setTimeWindow(window.value)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      timeWindow === window.value
                        ? 'border-green-600 bg-green-50 text-green-900'
                        : 'border-gray-200 hover:border-green-300'
                    }`}
                  >
                    <div className="font-medium">{window.label}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Zone */}
            <div>
              <label className="block text-lg font-medium text-gray-700 mb-3">
                Where are you located?
              </label>
              <select
                value={zone}
                onChange={(e) => setZone(e.target.value)}
                className="w-full p-4 border-2 border-gray-200 rounded-lg text-lg focus:border-green-600 focus:outline-none"
              >
                {zones.map((z) => (
                  <option key={z} value={z}>{z}</option>
                ))}
              </select>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={submitting}
              className={`w-full py-4 rounded-lg text-lg font-bold transition-all ${
                submitting
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 text-white shadow-lg hover:shadow-xl'
              }`}
            >
              {submitting ? '⏳ Submitting...' : '✅ Submit Report'}
            </button>
          </form>

          {/* Status Message */}
          {submitStatus && (
            <div className={`mt-6 p-4 rounded-lg ${
              submitStatus.type === 'success'
                ? 'bg-green-50 border-2 border-green-500'
                : 'bg-red-50 border-2 border-red-500'
            }`}>
              <div className="flex items-start">
                <div className="text-2xl mr-3">
                  {submitStatus.type === 'success' ? '✅' : '❌'}
                </div>
                <div className="flex-1">
                  <p className={`font-bold ${
                    submitStatus.type === 'success' ? 'text-green-900' : 'text-red-900'
                  }`}>
                    {submitStatus.type === 'success' ? 'Success!' : 'Error'}
                  </p>
                  <p className={`mt-1 ${
                    submitStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {submitStatus.message}
                  </p>
                  {submitStatus.signalId && (
                    <p className="text-sm text-green-700 mt-2">
                      Report ID: {submitStatus.signalId}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* My Reports */}
        <section className="bg-white rounded-xl shadow-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">📋 Recent Reports</h2>
            <button
              onClick={loadMyReports}
              disabled={loading}
              className="text-green-600 hover:text-green-700 font-medium"
            >
              {loading ? '⏳ Loading...' : '🔄 Refresh'}
            </button>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading your reports...</p>
            </div>
          ) : myReports.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-gray-600 text-lg">No reports yet</p>
              <p className="text-gray-500 mt-2">Submit your first report above</p>
            </div>
          ) : (
            <div className="space-y-3">
              {myReports.map((report, index) => (
                <div
                  key={report.id || index}
                  className="border-2 border-gray-200 rounded-lg p-4 hover:border-green-300 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl">
                          {report.activity_type === 'irrigation' ? '💧' :
                           report.activity_type === 'milling' ? '⚙️' :
                           report.activity_type === 'storage' ? '📦' :
                           report.activity_type === 'welding' ? '🔧' :
                           report.activity_type === 'trading' ? '🛒' :
                           report.activity_type === 'transport' ? '🚚' : '📝'}
                        </span>
                        <div>
                          <p className="font-bold text-gray-900 capitalize">
                            {report.activity_type || 'Activity'}
                          </p>
                          <p className="text-sm text-gray-600">
                            {report.zone} • {report.time_window || 'anytime'}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800">
                        ✅ Received
                      </span>
                      <p className="text-xs text-gray-500 mt-1">
                        {report.created_at ? new Date(report.created_at).toLocaleDateString() : 'Recently'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

// Made with Bob
