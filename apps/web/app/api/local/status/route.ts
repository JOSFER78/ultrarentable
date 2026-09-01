import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";
import { findRepoRoot, resolveDataDir } from "@/lib/projectPaths";

function countFiles(dir: string, predicate: (name: string) => boolean = () => true): number {
  if (!fs.existsSync(dir)) return 0;
  let total = 0;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const target = path.join(dir, entry.name);
    if (entry.isDirectory()) total += countFiles(target, predicate);
    else if (predicate(entry.name)) total += 1;
  }
  return total;
}

async function pingLocalBackend() {
  const base = process.env.LOCAL_API_URL || "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${base}/api/v1/status`, {
      cache: "no-store",
      signal: AbortSignal.timeout(2500),
    });
    if (!response.ok) {
      return { status: "ERROR", httpStatus: response.status, base };
    }
    return { status: "ONLINE", base, data: await response.json() };
  } catch (error) {
    return { status: "OFFLINE", base, error: String(error) };
  }
}

async function pingBingX() {
  const base = process.env.BINGX_BASE_URL || "https://open-api.bingx.com";
  const started = Date.now();
  try {
    const response = await fetch(`${base}/openApi/swap/v2/quote/contracts`, {
      cache: "no-store",
      headers: { "X-SOURCE-KEY": "BX-AI-SKILL" },
      signal: AbortSignal.timeout(8000),
    });
    const payload = await response.json();
    if (!response.ok || payload?.code !== 0 || !Array.isArray(payload?.data)) {
      return { status: "ERROR", latencyMs: Date.now() - started };
    }
    return {
      status: "ONLINE",
      latencyMs: Date.now() - started,
      contractsCount: payload.data.length,
    };
  } catch (error) {
    return { status: "OFFLINE", error: String(error) };
  }
}

export async function GET() {
  const repoRoot = findRepoRoot();
  const dataDir = resolveDataDir();
  const [backend, bingx] = await Promise.all([pingLocalBackend(), pingBingX()]);

  const normalizedDir = path.join(dataDir, "normalized");
  const rawDir = path.join(dataDir, "raw");
  const artifactsDir = path.join(dataDir, "artifacts");
  const quarantineDir = path.join(dataDir, "quarantine");

  return NextResponse.json({
    generatedAt: new Date().toISOString(),
    mode: "LOCAL_REAL_ONLY",
    repoRoot,
    dataDir,
    backend,
    bingx,
    storage: {
      rawFiles: countFiles(rawDir),
      datasetManifests: countFiles(normalizedDir, (name) => name.endsWith("_manifest.json")),
      quarantinedFiles: countFiles(quarantineDir),
      strategies: countFiles(path.join(dataDir, "strategies"), (name) => name.endsWith(".json") || name.endsWith(".yaml")),
      backtests: countFiles(path.join(artifactsDir, "backtests"), (name) => name.endsWith("manifest.json")),
      campaigns: countFiles(path.join(artifactsDir, "campaigns"), (name) => name.endsWith("manifest.json")),
      canonicalResults: countFiles(path.join(artifactsDir, "canonical"), (name) => name.endsWith("manifest.json")),
      researchSources: countFiles(path.join(dataDir, "research"), (name) => name.endsWith("manifest.json")),
    },
  });
}
