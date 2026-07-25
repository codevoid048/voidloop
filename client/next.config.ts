import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";

const baseImageRemotePatterns = [
  { protocol: "https" as const, hostname: "images.unsplash.com" },
];

const devImageRemotePatterns = [
  { protocol: "http" as const, hostname: "localhost", port: "8000" },
  { protocol: "http" as const, hostname: "127.0.0.1", port: "8000" },
];

const imageRemotePatterns: NonNullable<NextConfig["images"]>["remotePatterns"] = [
  ...baseImageRemotePatterns,
  ...(!isProd ? devImageRemotePatterns : []),
];

/** Server-only backend base (includes /api/v1). Never use NEXT_PUBLIC_ for this. */
const apiUrl = (process.env.API_URL || "http://127.0.0.1:8000/api/v1").replace(
  /\/$/,
  "",
);

const csp = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  `script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com`,
  "worker-src 'self' blob:",
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self' data:",
  `img-src 'self' data: blob: https://images.unsplash.com https://www.googletagmanager.com https://www.google-analytics.com ${
    !isProd ? "http://localhost:8000 http://127.0.0.1:8000" : ""
  }`,
  `connect-src 'self' https://www.googletagmanager.com https://www.google-analytics.com ${
    !isProd ? "http://localhost:8000 http://127.0.0.1:8000" : ""
  }`,
  "frame-src 'self' https://www.googletagmanager.com https://www.google.com",
  ...(isProd ? ["upgrade-insecure-requests"] : []),
]
  .join("; ")
  .trim();

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: imageRemotePatterns,
    formats: ["image/avif", "image/webp"],
    minimumCacheTTL: isProd ? 2678400 : 60,
    deviceSizes: [320, 420, 640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 24, 32, 48, 64, 96, 128, 256, 384],
    qualities: [50, 60, 70, 75, 80, 90, 100],
    dangerouslyAllowSVG: false,
    contentDispositionType: "attachment",
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
  reactCompiler: true,
  experimental: {
    optimizePackageImports: ["lucide-react", "framer-motion", "gsap"],
    optimizeServerReact: true,
    staleTimes: {
      dynamic: 30,
      static: 180,
    },
    parallelServerCompiles: true,
    parallelServerBuildTraces: true,
  },

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: csp,
          },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "X-API-Version", value: "1.0.0" },
        ],
      },
    ];
  },

  async redirects() {
    return [
      {
        source: "/:path*",
        has: [{ type: "host", value: "www.voidloop.williamkeri.com" }],
        destination: "https://voidloop.williamkeri.com/:path*",
        permanent: true,
      },
      {
        source: "/register",
        destination: "/login",
        permanent: false,
      },
    ];
  },

  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
