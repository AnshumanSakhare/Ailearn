/** @type {import('next').NextConfig} */
const nextConfig = {
  // 'standalone' is for Docker; remove for Vercel
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001",
  },
};

module.exports = nextConfig;
