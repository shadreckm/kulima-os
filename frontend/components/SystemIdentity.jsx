/**
 * KULIMA OS Pilot - System Identity Component
 * ==========================================
 * 
 * System Identity component for displaying system philosophy and invariants.
 * 
 * INVARIANT ENFORCEMENT:
 * - Zero-PII: Displays system philosophy, not individual data
 * - Coordination > Identity: Emphasizes collective patterns, not individual tracking
 * - Semantic Guard: Designed for planning, not surveillance or profiling
 */

'use client';

import React, { useState, useEffect } from 'react';

export default function SystemIdentity() {
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSystemInfo();
  }, []);

  const fetchSystemInfo = async () => {
    try {
      const response = await fetch('/api/system/info');
      const data = await response.json();
      setSystemInfo(data.data);
    } catch (error) {
      console.error('Error fetching system info:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center">Loading system identity...</div>
      </div>
    );
  }

  if (!systemInfo) {
    return (
      <div className="p-6">
        <div className="text-center text-red-600">Error loading system identity</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        {/* Header */}
        <div className="mb-8 border-b pb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">{systemInfo.name}</h1>
          <p className="text-lg text-gray-600 mb-2">{systemInfo.description}</p>
          <div className="flex gap-2 mt-4">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              v{systemInfo.version}
            </span>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
              {systemInfo.type}
            </span>
          </div>
        </div>

        {/* Positioning */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Positioning</h2>
          <p className="text-gray-700 bg-gray-50 p-4 rounded-lg">
            {systemInfo.positioning}
          </p>
        </div>

        {/* Architectural Philosophy */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Architectural Philosophy</h2>
          <p className="text-gray-700 bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
            {systemInfo.architectural_philosophy}
          </p>
        </div>

        {/* Core Principles */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Core Principles</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {systemInfo.core_principles.map((principle, index) => (
              <div key={index} className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                <p className="text-gray-700 font-medium">{principle}</p>
              </div>
            ))}
          </div>
        </div>

        {/* System Invariants */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">System Invariants</h2>
          <div className="bg-red-50 p-6 rounded-lg border border-red-200">
            <p className="text-sm text-red-600 font-semibold mb-4">CRITICAL - These invariants must never be violated</p>
            <div className="space-y-3">
              {Object.entries(systemInfo.invariants).map(([key, value]) => (
                <div key={key} className="flex items-start">
                  <span className="text-red-600 mr-2">✓</span>
                  <div>
                    <span className="font-semibold text-gray-800">{key.replace(/_/g, ' ').toUpperCase()}:</span>
                    <span className="text-gray-700 ml-2">{value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Forbidden Operations */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Forbidden Operations</h2>
          <div className="bg-gray-100 p-6 rounded-lg border border-gray-300">
            <p className="text-sm text-gray-600 mb-4">The system will NEVER perform these operations</p>
            <ul className="space-y-2">
              {systemInfo.forbidden_operations.map((operation, index) => (
                <li key={index} className="flex items-center text-gray-700">
                  <span className="text-red-600 mr-2">✗</span>
                  {operation}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* System Objective */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-3">System Objective</h2>
          <p className="text-gray-700 bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
            {systemInfo.system_objective}
          </p>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t text-center text-sm text-gray-500">
          <p>KULIMA OS — Coordination-First Infrastructure Planning System</p>
          <p className="mt-1">Epistemic Digital Public Infrastructure</p>
        </div>
      </div>
    </div>
  );
}
