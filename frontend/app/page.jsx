'use client';

import { useRouter } from 'next/navigation';

/**
 * KULIMA OS - Role Selector Landing Page
 * 
 * Two roles:
 * 1. Farmer - Submit reports and view status
 * 2. Program Manager - Make infrastructure decisions
 */
export default function RoleSelector() {
  const router = useRouter();

  const roles = [
    {
      id: 'farmer',
      title: 'Farmer',
      description: 'Submit coordination signals and view your reports',
      icon: '🌾',
      color: 'bg-green-500',
      hoverColor: 'hover:bg-green-600',
      path: '/farmer'
    },
    {
      id: 'manager',
      title: 'Program Manager',
      description: 'Make infrastructure investment decisions',
      icon: '📊',
      color: 'bg-blue-500',
      hoverColor: 'hover:bg-blue-600',
      path: '/program-manager'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">KULIMA OS</h1>
          <p className="text-xl text-gray-600">
            Coordination Intelligence for Infrastructure Planning
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Select your role to continue
          </p>
        </div>

        {/* Role Cards */}
        <div className="grid md:grid-cols-2 gap-8">
          {roles.map((role) => (
            <button
              key={role.id}
              onClick={() => router.push(role.path)}
              className={`${role.color} ${role.hoverColor} text-white rounded-2xl p-8 shadow-xl transform transition-all duration-200 hover:scale-105 hover:shadow-2xl focus:outline-none focus:ring-4 focus:ring-offset-2 focus:ring-${role.color.split('-')[1]}-400`}
            >
              <div className="text-6xl mb-4">{role.icon}</div>
              <h2 className="text-3xl font-bold mb-3">{role.title}</h2>
              <p className="text-lg opacity-90">{role.description}</p>
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-sm text-gray-500">
          <p>Digital Public Infrastructure for Rural Economies</p>
          <p className="mt-1">Zero-PII • Coordination-First • Decision-Grade Intelligence</p>
        </div>
      </div>
    </div>
  );
}

// Made with Bob
