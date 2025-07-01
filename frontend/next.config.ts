import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://api-five-sage.vercel.app/api/:path*',
      },
    ];
  },
};

export default nextConfig;
