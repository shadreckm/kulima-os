'use client';

import Dashboard from '@/components/Dashboard';
import SignalForm from '@/components/SignalForm';
import ProspectusButton from '@/components/ProspectusButton';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Kulima OS – Real Activity, Real Decisions
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-6">
            This system helps understand how farming and trading actually happen before making investments.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Why this matters</h2>
          <p className="text-gray-600 mb-2">
            Many investments fail because they are based on assumptions.
          </p>
          <p className="text-gray-600">
            Kulima OS uses real activity to guide better decisions.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">How to use</h2>
          <ol className="list-decimal list-inside text-gray-600 space-y-2">
            <li>Submit activity</li>
            <li>View summary</li>
            <li>Generate report</li>
          </ol>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-8">
            <Dashboard />
            <SignalForm />
          </div>
          <div>
            <ProspectusButton />
          </div>
        </div>

        <footer className="mt-12 text-center text-gray-500 text-sm">
          <p>Kulima OS – Understanding real economic activity before planning</p>
        </footer>
      </div>
    </main>
  );
}
