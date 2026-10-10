/** @type {import('next').NextConfig} */
const path = require("path");

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@vidiforge/shared"],
  experimental: {
    externalDir: true,
  },
};

module.exports = nextConfig;