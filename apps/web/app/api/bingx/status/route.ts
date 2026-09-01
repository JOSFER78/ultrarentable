import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";
import { resolveDataDir } from "@/lib/projectPaths";

const BINGX_BASE = process.env.BINGX_BASE_URL || "https://open-api.bingx.com";

async function fetchContracts() {
  const response = await fetch(`${BINGX_BASE}/openApi/swap/v2/quote/contracts`, {
    cache: "no-store",
    headers: { "X-SOURCE-KEY": "BX-AI-SKILL" },
    signal: AbortSignal.timeout(8000),
  });
  const payload = await response.json();
  if (!response.ok || payload?.code !== 0 || !Array.isArray(payload?.data)) {
    throw new Error(`BINGX_CONTRACTS_ERROR: HTTP ${response.status}`);
  }
  return payload.data as unknown[];
}

export async function GET() {
  const started = Date.now();
  const dataDir = resolveDataDir();

  try {
    const contracts = await fetchContracts();
    const normalizedDir = path.join(dataDir, "normalized");
    const datasetsStored = fs.existsSync(normalizedDir)
      ? fs.readdirSync(normalizedDir).filter((name) => name.endsWith("_manifest.json")).length
      : 0;

    return NextResponse.json({
      status: "ONLINE",
      venue: "BINGX",
      timestamp: Date.now(),
      latencyMs: Date.now() - started,
      contractsCount: contracts.length,
      datasetsStored,
      accountStatus: process.env.BINGX_API_KEY && process.env.BINGX_SECRET_KEY
        ? "CREDENTIALS_PRESENT_NOT_QUERIED_BY_WEB"
        : "NOT_AUTHENTICATED",
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: "ERROR",
        venue: "BINGX",
        timestamp: Date.now(),
        error: String(error),
      },
      { status: 502 },
    );
  }
}
