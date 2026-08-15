import crypto from "crypto";
import fs from "fs";
import path from "path";
import { BingXRestClient } from "../../../packages/bingx-client/src/rest";
import type { MarketEvent } from "../../../packages/bingx-client/src/websocket";

export interface Manifest {
  datasetId: string;
  venue: "BINGX";
  symbol: string;
  feedType: string;
  startTime: number | null;
  endTime: number | null;
  recordCount: number;
  gapCount: number;
  duplicateCount: number;
  checksumSha256: string;
  rawChecksumSha256: string;
  rawPath: string;
  normalizedPath: string;
  createdAt: string;
  closedRecordsOnly: boolean;
  completeHistory: boolean;
  request: Record<string, string | number | boolean>;
}

function findRepoRoot(start = process.cwd()): string {
  let current = path.resolve(start);
  while (true) {
    if (fs.existsSync(path.join(current, "REAL_ONLY_START_HERE.md"))) return current;
    const parent = path.dirname(current);
    if (parent === current) return path.resolve(start);
    current = parent;
  }
}

function resolveBaseDir(configured?: string): string {
  const repoRoot = findRepoRoot();
  const value = configured || process.env.DATA_DIR || "data";
  return path.isAbsolute(value) ? value : path.resolve(repoRoot, value);
}

function sha256(text: string): string {
  return crypto.createHash("sha256").update(text).digest("hex");
}

function intervalMilliseconds(interval: string): number {
  const match = /^(\d+)(m|h|d|w)$/.exec(interval);
  if (!match) throw new Error(`UNSUPPORTED_INTERVAL: ${interval}`);
  const amount = Number(match[1]);
  const unit = match[2];
  const factor = unit === "m" ? 60_000 : unit === "h" ? 3_600_000 : unit === "d" ? 86_400_000 : 604_800_000;
  return amount * factor;
}

function nullableNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export class DataIngestionService {
  private readonly restClient: BingXRestClient;
  private readonly baseDir: string;

  constructor(baseDir?: string, restClient = new BingXRestClient()) {
    this.restClient = restClient;
    this.baseDir = resolveBaseDir(baseDir);
    for (const name of ["raw", "normalized", "catalogs", "artifacts", "state"]) {
      fs.mkdirSync(path.join(this.baseDir, name), { recursive: true });
    }
  }

  private saveRawRest(
    feed: string,
    payload: unknown,
    request: Record<string, string | number | boolean>,
  ) {
    const capturedAt = new Date();
    const stamp = capturedAt.toISOString().replace(/[:.]/g, "-");
    const dir = path.join(this.baseDir, "raw", "rest", feed);
    fs.mkdirSync(dir, { recursive: true });
    const envelope = {
      venue: "BINGX",
      capturedAt: capturedAt.toISOString(),
      receiveTimestamp: capturedAt.getTime(),
      request,
      payload,
    };
    const text = JSON.stringify(envelope);
    const filePath = path.join(dir, `${stamp}.json`);
    fs.writeFileSync(filePath, text, { encoding: "utf8", flag: "wx" });
    return { filePath, checksum: sha256(text), capturedAt };
  }

  public async syncInstrumentCatalog() {
    const request = { endpoint: "/openApi/swap/v2/quote/contracts" };
    const rawContracts = await this.restClient.getContracts();
    const raw = this.saveRawRest("contracts", rawContracts, request);

    const normalized = rawContracts.map((contract: any) => ({
      contractId: contract.contractId ?? null,
      symbol: contract.symbol ?? null,
      asset: contract.asset ?? null,
      currency: contract.currency ?? null,
      makerFeeRate: nullableNumber(contract.makerFeeRate),
      takerFeeRate: nullableNumber(contract.takerFeeRate ?? contract.feeRate),
      pricePrecision: nullableNumber(contract.pricePrecision),
      quantityPrecision: nullableNumber(contract.quantityPrecision),
      tradeMinQuantity: nullableNumber(contract.tradeMinQuantity),
      tradeMinUSDT: nullableNumber(contract.tradeMinUSDT),
      status: contract.status ?? null,
      raw: contract,
    }));

    const normalizedText = JSON.stringify(normalized);
    const checksum = sha256(normalizedText);
    const catalogPath = path.join(this.baseDir, "catalogs", "bingx_instruments.json");
    fs.writeFileSync(catalogPath, normalizedText, "utf8");

    const manifest: Manifest = {
      datasetId: `catalog_bingx_${raw.capturedAt.getTime()}`,
      venue: "BINGX",
      symbol: "ALL",
      feedType: "instruments",
      startTime: raw.capturedAt.getTime(),
      endTime: raw.capturedAt.getTime(),
      recordCount: normalized.length,
      gapCount: 0,
      duplicateCount: 0,
      checksumSha256: checksum,
      rawChecksumSha256: raw.checksum,
      rawPath: path.relative(this.baseDir, raw.filePath),
      normalizedPath: path.relative(this.baseDir, catalogPath),
      createdAt: raw.capturedAt.toISOString(),
      closedRecordsOnly: true,
      completeHistory: false,
      request,
    };
    fs.writeFileSync(
      path.join(this.baseDir, "catalogs", "bingx_instruments_manifest.json"),
      JSON.stringify(manifest, null, 2),
      "utf8",
    );
    return { count: normalized.length, checksum, rawChecksum: raw.checksum, catalogPath };
  }

  public recordRawEvent(event: MarketEvent): void {
    const eventTime = event.exchangeTimestamp ?? event.receiveTimestamp;
    const day = new Date(eventTime).toISOString().slice(0, 10);
    const dir = path.join(this.baseDir, "raw", "ws", event.symbol, event.feedType);
    fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(path.join(dir, `${day}.jsonl`), `${JSON.stringify(event)}\n`, "utf8");
  }

  public async downloadKlines(
    symbol: string,
    interval: string,
    limit = 1000,
    startTime?: number,
    endTime?: number,
  ) {
    const request: Record<string, string | number | boolean> = {
      endpoint: "/openApi/swap/v3/quote/klines",
      symbol,
      interval,
      limit,
    };
    if (startTime !== undefined) request.startTime = startTime;
    if (endTime !== undefined) request.endTime = endTime;

    const rawKlines = await this.restClient.getKlines(symbol, interval, limit, startTime, endTime);
    if (!Array.isArray(rawKlines) || rawKlines.length === 0) {
      throw new Error(`NO_KLINES_RETURNED: ${symbol} ${interval}`);
    }
    const raw = this.saveRawRest(`klines/${symbol}/${interval}`, rawKlines, request);
    const stepMs = intervalMilliseconds(interval);
    const closedBefore = raw.capturedAt.getTime();

    const mapped = rawKlines
      .map((candle: any) => ({
        time: Number(candle.time),
        open: Number(candle.open),
        high: Number(candle.high),
        low: Number(candle.low),
        close: Number(candle.close),
        volume: Number(candle.volume),
      }))
      .filter((candle) => Number.isFinite(candle.time) && candle.time + stepMs <= closedBefore)
      .sort((a, b) => a.time - b.time);

    const seen = new Set<number>();
    let duplicateCount = 0;
    const normalized = mapped.filter((candle) => {
      if (seen.has(candle.time)) {
        duplicateCount += 1;
        return false;
      }
      seen.add(candle.time);
      return true;
    });
    if (normalized.length === 0) throw new Error(`NO_CLOSED_KLINES: ${symbol} ${interval}`);

    let gapCount = 0;
    for (let index = 1; index < normalized.length; index += 1) {
      if (normalized[index].time - normalized[index - 1].time !== stepMs) gapCount += 1;
    }

    const normalizedText = JSON.stringify(normalized);
    const checksum = sha256(normalizedText);
    const first = normalized[0].time;
    const last = normalized.at(-1)!.time;
    const datasetId = `ds_bingx_${symbol.replace("-", "_")}_${interval}_${first}_${last}`;
    const filePath = path.join(this.baseDir, "normalized", `${datasetId}.json`);
    fs.writeFileSync(filePath, normalizedText, "utf-8");

    const manifest: Manifest = {
      datasetId,
      venue: "BINGX",
      symbol,
      feedType: `kline_${interval}`,
      startTime: first,
      endTime: last,
      recordCount: normalized.length,
      gapCount,
      duplicateCount,
      checksumSha256: checksum,
      rawChecksumSha256: raw.checksum,
      rawPath: path.relative(this.baseDir, raw.filePath),
      normalizedPath: path.relative(this.baseDir, filePath),
      createdAt: raw.capturedAt.toISOString(),
      closedRecordsOnly: true,
      completeHistory: false,
      request,
    };
    fs.writeFileSync(
      path.join(this.baseDir, "normalized", `${datasetId}_manifest.json`),
      JSON.stringify(manifest, null, 2),
      "utf8",
    );
    return { datasetId, count: normalized.length, gapCount, duplicateCount, checksum, filePath };
  }
}
