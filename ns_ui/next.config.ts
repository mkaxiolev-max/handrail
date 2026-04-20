import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    const nsApi = process.env.NEXT_PUBLIC_NS_API_URL || 'http://localhost:9011'
    const nsUrl = process.env.NEXT_PUBLIC_NS_URL || 'http://localhost:9000'
    return [
      {source: '/api/ns/:path*', destination: `${nsApi}/api/v1/:path*`},
      {source: '/api/violet/:path*', destination: `${nsUrl}/violet/:path*`},
    ]
  }
};

export default nextConfig;
