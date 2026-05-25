/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Lint runs as a dedicated CI step; don't fail production builds on style.
  eslint: { ignoreDuringBuilds: true },
  // Proxy API calls to the backend in development so the browser can use
  // same-origin relative URLs (no CORS surprises). Overridable via env.
  async rewrites() {
    const target = process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${target}/api/:path*` }];
  },
};

export default nextConfig;
