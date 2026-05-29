import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export so Tauri bundles the SPA from `out/` (frontendDist: ../out).
  // The app is a single "use client" page with no server routes/actions/images,
  // so none of the static-export unsupported features apply.
  output: "export",
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  devIndicators: false,
};

export default nextConfig;
