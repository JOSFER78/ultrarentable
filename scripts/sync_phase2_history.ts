import crypto from "crypto";
import fs from "fs";
import path from "path";
import { BingXRestClient } from "../packages/bingx-client/src/rest";

const INTERVAL_MS: Record<string, number> = {
  "1m": 60_000,
  "3m": 180_000,
  "5m": 300_000,
  "15m": 900_000,
  "30m": 1_800_000,
  "1h": 3_600_000,
  "2h": 7_200_000,
  "4h": 14_400_000,
  "6h": 21_600_000,
  "8h": 28_800_000,
  "12h": 43_200_000,
  "1d": 86_400_000,
  "3d": 259_200_000,
  "1w": 604_800_000,
};

const DAYS = Math.max(30, Number(process.env.PHASE2_HISTORY_DAYS || 365));
const INTERVAL = process.env.PHASE2_INTERVAL || "1h";
const PAGE_LIMIT = Math.min(1000, Math.max(100, Number(process.env.PHASE2_PAGE_LIMIT || 1000)));
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

function mapCandle(raw: any): [number, number, number, number, number, number] | null {
  if (Array.isArray(raw)) {
    const [time, open, high, low, close, volume] = raw;
    return [Number(time), Number(open), Number(high), Number(low), Number(close), Number(volume)];
  }
  return [
    Number(raw?.time ?? raw?.openTime),
    Number(raw?.open),
    Number(raw?.high),
    Number(raw?.low),
    Number(raw?.close),
    Number(raw?.volume),
  ];
}

async function syncSymbol(client: BingXRestClient, symbol: string): Promise<void> {
  const stepMs = INTERVAL_MS[INTERVAL];
  if (!stepMs) throw new Error(`UNSUPPORTED_INTERVAL: ${INTERVAL}`);

  const now = Date.now();
  const requestedEnd = Math.floor(now / stepMs) * stepMs;
  const requestedStart = requestedEnd - DAYS * 86_400_000;
  let pageEndExclusive = requestedEnd;
  const candles = new Map<number, number[]>();
  const rawPages: unknown[] = [];
  let pages = 0;

  while (pageEndExclusive > requestedStart) {
    const windowStart = Math.max(requestedStart, pageEndExclusive - stepMs * PAGE_LIMIT);
    const page = await client.getKlines(symbol, INTERVAL, PAGE_LIMIT, windowStart, pageEndExclusive);
    pages += 1;
    rawPages.push({
      capturedAt: new Date().toISOString(),
      requestStartTime: windowStart,
      requestEndTimeExclusive: pageEndExclusive,
      limit: PAGE_LIMIT,
      payload: page,
    });
    if (!Array.isArray(page) || page.length === 0) break;

    let oldest = Number.POSITIVE_INFINITY;
    for (const raw of page) {
      const candle = mapCandle(raw);
      if (!candle) continue;
      const [timestamp, open, high, low, close, volume] = candle;
      if (!Number.isFinite(timestamp)) continue;
      if (timestamp < requestedStart || timestamp >= requestedEnd || timestamp + stepMs > requestedEnd) continue;
      assertPositiveFinite(open, "OPEN");
      assertPositiveFinite(high, "HIGH");
      assertPositiveFinite(low, "LOW");
      assertPositiveFinite(close, "CLOSE");
      if (!Number.isFinite(volume) || volume < 0) throw new Error(`INVALID_VOLUME: ${symbol} ${timestamp}`);
      if (high < Math.max(open, close) || low > Math.min(open, close)) {
        throw new Error(`INVALID_OHLC: ${symbol} ${timestamp}`);
      }
      candles.set(timestamp, [timestamp, open, high, low, close, volume]);
      oldest = Math.min(oldest, timestamp);
    }

    if (!Number.isFinite(oldest)) break;
    if (oldest >= pageEndExclusive) throw new Error(`PAGINATION_STALLED: ${symbol} ${pageEndExclusive}`);
    pageEndExclusive = oldest;
    if (page.length < PAGE_LIMIT && pageEndExclusive <= requestedStart) break;
    if (pages > 100) throw new Error(`PAGINATION_LIMIT_EXCEEDED: ${symbol}`);
  }

  const normalized = [...candles.values()].sort((a, b) => a[0] - b[0]);
  const expectedBars = Math.floor((requestedEnd - requestedStart) / stepMs);
  const minimumBars = Math.max(200, Math.floor(expectedBars * 0.95));
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
    requestedEndTime: requestedEnd,
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
    request: {
      endpoint: "/openApi/swap/v3/quote/klines",
      symbol,
      interval: INTERVAL,
      requestedDays: DAYS,
      pageLimit: PAGE_LIMIT,
      pagination: "backward_windowed",
    },
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
