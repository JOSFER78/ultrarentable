import type { NextConfig } from "next";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "/pro/ultrarentable";

const nextConfig: NextConfig = {
  output: "standalone",
  basePath: basePath === "none" ? undefined : basePath,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
