import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    return [
      {
        source: '/generate',
        destination: 'http://127.0.0.1:8000/generate',
      },
      {
        source: '/status/:path*',
        destination: 'http://127.0.0.1:8000/status/:path*',
      },
      {
        source: '/download/:path*',
        destination: 'http://127.0.0.1:8000/download/:path*',
      },
    ];
  },
};

export default nextConfig;
