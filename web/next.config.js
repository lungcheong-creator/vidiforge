/** @type {import('next').NextConfig} */

const nextConfig = {
  output: "export",
  reactStrictMode: true,
  trailingSlash: true,
  images: { unoptimized: true },
  // Static export friendly: don't try to use SSR/ISR
  // No server actions, no API routes — all in FastAPI
};

module.exports = nextConfig;