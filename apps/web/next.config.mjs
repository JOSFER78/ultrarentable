const backendUrl = process.env.BACKEND_URL || process.env.ULTRARENTABLE_API_URL || "http://127.0.0.1:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: process.env.BASE_PATH || "",
  poweredByHeader: false,
  compress: true,
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${backendUrl}/api/:path*` },
      { source: "/pro/ultrarentable/api/:path*", destination: `${backendUrl}/api/:path*` },
      { source: "/pro/ultrarentable", destination: "/" },
      { source: "/pro/ultrarentable/:path*", destination: "/:path*" },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Cache-Control", value: "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" },
          { key: "Pragma", value: "no-cache" },
          { key: "Expires", value: "0" },
        ],
      },
    ];
  },
};

export default nextConfig;
