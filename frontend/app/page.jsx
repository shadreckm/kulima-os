'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/**
 * KULIMA OS - Landing Page
 * Redirects to Program Manager Dashboard
 */
export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard immediately
    router.push('/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">KULIMA OS</h1>
        <p className="text-gray-600">Loading dashboard...</p>
      </div>
    </div>
  );
}

// Made with Bob
