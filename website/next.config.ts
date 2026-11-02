import type { NextConfig } from 'next';
// Bound static-export concurrency for the full locale matrix on 16 GB workstations.
const config: NextConfig = { output: 'export', trailingSlash: true, images: { unoptimized: true }, poweredByHeader: false, experimental: {cpus:2} };
export default config;
