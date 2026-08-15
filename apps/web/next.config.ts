import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // Serve the FastAPI backend through the SAME origin/port as the web app
    // (Next.js :3000). This removes any dependency on exposing the external
    // API port :8000. The browser calls /api/v1/... on :3000 (which works from
    // the PC over Tailscale / the preview) and Next proxies it to the local
    // backend at 127.0.0.1:8000. Fixes the SQX MCP showing OFFLINE in the
    // Hermes preview when :8000 was unreachable from the user's machine.
    return [{ source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" }];
  },
};

export default nextConfig;
