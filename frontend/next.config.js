/** @type {import('next').NextConfig} */
module.exports = {
  // Disable static optimization for pages that need client-side data
  experimental: {
    appDir: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_PROXY_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
  // Prevent build-time API calls
  generateBuildId: async () => {
    return 'kulima-os-build'
  },
};
