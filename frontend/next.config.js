/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    HELIOS_API_URL: process.env.HELIOS_API_URL || "http://localhost:8000",
  },
};

module.exports = nextConfig;
