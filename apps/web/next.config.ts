import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  basePath: "/pro/ultrarentable",
  turbopack: {
    root: path.resolve(__dirname, "../.."),
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
        basePath: false,
      },
      {
        source: "/pro/ultrarentable/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
        basePath: false,
      },
    ];
  },
};

export default nextConfig;
