import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {source: '/api/ns/:path*', destination: 'http://localhost:9011/api/v1/:path*'},
      {source: '/api/violet/:path*', destination: 'http://localhost:9000/violet/:path*'},
    ]
  }
};

export default nextConfig;
