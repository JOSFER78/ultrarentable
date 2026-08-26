import crypto from "crypto";
import fs from "fs";
import path from "path";
import { BingXRestClient } from "../packages/bingx-client/src/rest";

const INTERVAL_MS: Record<string, number> = {
  "1m": 60_000,
  "5m": 300_000,
  "15m": 900_000,
  "1h": 3_600_000,
  "4h": 14_400_000,
  "1d": 86_400_000,
};

const DAYS = Math.max(30, Number(process.env.PHASE2_HISTORY_DAYS || 365));
const INTERVAL = process.env.PHASE2_INTERVAL || "1h";
const SYMBOLS = (process.env.PHASE2_SYMBOLS || "BTC-USDT,ETH-USDT,SOL-USDT")
  .split(",")
  .map((value) => value.trim().toUpperCase())
  .filter(Boolean);
const DATA_ROOT = path.resolve(process.env.DATA_DIR || path.join(process.cwd(), "data"));
const NORMALIZED_DIR = path.join(DATA_ROOT, "normalized");
const RAW_DIR = path.join(DATA_ROOT, "raw", "rest", "phase2-history");

function sha256(text: string): string {
  return crypto.createHash("sha256").update(text).digest("hex");
}

function sha256Bytes(filePath: string): string {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function assertPositiveFinite(value: number, label: string): void {
  if (!Number.isFinite(value) || value <= 0) throw new Error(`INVALID_${label}`);
}

async function syncSymbol(client: BingXRestClient, symbol: string): Promise<void> {
  const stepMs = INTERVAL_MS[INTERVAL];
  if (!stepMs) throw new Error(`UNSUPPORTED_INTERVAL: ${INTERVAL}`);

  const endTime = Date.now() - stepMs;
  const requestedStart = endTime - DAYS * 86_400_000;
  let cursor = requestedStart;
  const candles = new Map<number, number[]>();
  const rawPages: unknown[] = [];
  let pages = 0;

  while (cursor <= endTime) {
    const page = await client.getKlines(symbol, INTERVAL, 1000, cursor, endTime);
    pages += 1;
    rawPages.push({ capturedAt: new Date().toISOString(), requestStartTime: cursor, requestEndTime: endTime, payload: page });
    if (!Array.isArray(page) || page.length === 0) break;

    let maxTimestamp = cursor - stepMs;
    for (const candle of page) {
      const timestamp = Number(candle?.time);
      const open = Number(candle?.open);
      const high = Number(candle?.high);
      const low = Number(candle?.low);
      const close = Number(candle?.close);
      const volume = Number(candle?.volume);
      if (!Number.isFinite(timestamp)) continue;
      if (timestamp + stepMs > endTime) continue;
      assertPositiveFinite(open, "OPEN");
      assertPositiveFinite(high, "HIGH");
      assertPositiveFinite(low, "LOW");
      assertPositiveFinite(close, "CLOSE");
      if (high < Math.max(open, close) || low > Math.min(open, close)) {
        throw new Error(`INVALID_OHLC: ${symbol} ${timestamp}`);
      }
      candles.set(timestamp, [timestamp, open, high, low, close, volume]);
      maxTimestamp = Math.max(maxTimestamp, timestamp);
    }

    if (maxTimestamp < cursor) break;
    const nextCursor = maxTimestamp + stepMs;
    if (nextCursor <= cursor) throw new Error(`PAGINATION_STALLED: ${symbol} ${cursor}`);
    cursor = nextCursor;
    if (page.length < 1000) break;
    if (pages > 500) throw new Error(`PAGINATION_LIMIT_EXCEEDED: ${symbol}`);
  }

  const normalized = [...candles.values()].sort((a, b) => a[0] - b[0]);
  const minimumBars = Math.max(200, Math.floor(DAYS * 24 * 0.95));
  if (normalized.length < minimumBars) {
    throw new Error(`INSUFFICIENT_HISTORY: ${symbol} got=${normalized.length} required>=${minimumBars}`);
  }

  for (let index = 1; index < normalized.length; index += 1) {
    const diff = normalized[index][0] - normalized[index - 1][0];
    if (diff !== stepMs) throw new Error(`HISTORY_GAP: ${symbol} at ${normalized[index - 1][0]} diff=${diff}`);
  }

  const canonicalText = JSON.stringify(normalized, null, 2);
  const contentChecksum = sha256(JSON.stringify(normalized));
  const first = normalized[0][0];
  const last = normalized[normalized.length - 1][0];
  const datasetId = `ds_bingx_${symbol.replace("-", "_")}_${INTERVAL}_${first}_${last}_${contentChecksum.slice(0, 12)}`;
  const normalizedPath = path.join(NORMALIZED_DIR, `${datasetId}.json`);
  const manifestPath = path.join(NORMALIZED_DIR, `${datasetId}_manifest.json`);
  const rawPath = path.join(RAW_DIR, symbol, `${datasetId}.json`);
  fs.mkdirSync(path.dirname(rawPath), { recursive: true });
  fs.mkdirSync(NORMALIZED_DIR, { recursive: true });

  fs.writeFileSync(rawPath, JSON.stringify(rawPages, null, 2), "utf8");
  fs.writeFileSync(normalizedPath, canonicalText, "utf8");

  const physicalFileSha256 = sha256Bytes(normalizedPath);
  const manifest = {
    datasetId,
    venue: "BINGX",
    symbol,
    interval: INTERVAL,
    startTime: first,
    endTime: last,
    requestedStartTime: requestedStart,
    requestedEndTime: endTime,
    recordCount: normalized.length,
    pageCount: pages,
    gapCount: 0,
    duplicateCount: 0,
    closedRecordsOnly: true,
    completeHistory: normalized.length >= minimumBars,
    contentChecksumSha256: contentChecksum,
    physicalFileSha256,
    rawPath: path.relative(DATA_ROOT, rawPath),
    normalizedPath: path.relative(DATA_ROOT, normalizedPath),
    createdAt: new Date().toISOString(),
    request: { endpoint: "/openApi/swap/v3/quote/klines", symbol, interval: INTERVAL, requestedDays: DAYS, pageLimit: 1000 },
  };
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf8");
  console.log(JSON.stringify({ symbol, interval: INTERVAL, daysRequested: DAYS, bars: normalized.length, pages, datasetId, physicalFileSha256 }, null, 2));
}

async function main(): Promise<void> {
  if (!SYMBOLS.length) throw new Error("NO_PHASE2_SYMBOLS");
  const client = new BingXRestClient();
  for (const symbol of SYMBOLS) await syncSymbol(client, symbol);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
