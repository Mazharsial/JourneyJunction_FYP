import type { NextConfig } from "next";

// Hosts (besides localhost) that the dev server may serve its internal assets
// (JS chunks, fonts, HMR) to. Required when the dev server is reached through a
// tunnel such as ngrok, otherwise Next.js blocks those requests cross-origin and
// the page never hydrates. Comma-separated, set via DEV_ALLOWED_ORIGINS.
const devAllowedOrigins = (process.env.DEV_ALLOWED_ORIGINS ?? "")
  .split(",")
  .map((h) => h.trim())
  .filter(Boolean);

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle for the Docker runtime image.
  // Only in standalone mode does `next start` NOT apply rewrites(), so we gate
  // it behind NEXT_STANDALONE (set it in the Docker build) and leave it off for
  // local `next start`, which must keep the /api/* proxy working.
  ...(process.env.NEXT_STANDALONE ? { output: "standalone" as const } : {}),
  reactStrictMode: true,
  // Preserve trailing slashes when proxying /api/* so the backend receives the
  // exact path (e.g. /api/v1/chat/). Without this, Next normalizes the slash
  // away, the backend 307-redirects to its own internal host, and the browser
  // cannot follow the redirect across origins.
  skipTrailingSlashRedirect: true,
  ...(devAllowedOrigins.length ? { allowedDevOrigins: devAllowedOrigins } : {}),
  // Optional same-origin API proxy: when API_PROXY_TARGET is set, `/api/*` is
  // forwarded to the backend. Lets a single public origin (e.g. an ngrok tunnel
  // or a combined deployment) serve both the frontend and the API.
  async rewrites() {
    const target = process.env.API_PROXY_TARGET;
    return target
      ? [{ source: "/api/:path*", destination: `${target}/api/:path*` }]
      : [];
  },
};

export default nextConfig;
