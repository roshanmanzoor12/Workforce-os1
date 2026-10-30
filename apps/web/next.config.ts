import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  productionBrowserSourceMaps: false,

  outputFileTracingRoot: path.join(
    __dirname,
    "../..",
  ),

  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "date-fns",
    ],
  },

  async rewrites() {
    return [
      {
        source: "/backend/:path*",

        destination:
          "http://127.0.0.1:8001/api/v1/:path*",
      },
    ];
  },

  async headers() {
    return [
      {
        source: "/:path*",

        headers: [
          {
            key:
              "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key:
              "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key:
              "Referrer-Policy",
            value:
              "strict-origin-when-cross-origin",
          },
          {
            key:
              "Permissions-Policy",
            value:
              "camera=(self), microphone=(self), geolocation=(), payment=(), usb=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;