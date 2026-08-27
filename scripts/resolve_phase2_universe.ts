import { BingXRestClient } from "../packages/bingx-client/src/rest";

const EXPLICIT = (process.env.PHASE2_SYMBOLS || "AUTO").trim();
const ULTRA_PREFERRED = [
  "BTC-USDT",
  "ETH-USDT",
  "SOL-USDT",
  "XRP-USDT",
  "BNB-USDT",
  "DOGE-USDT",
  "ADA-USDT",
  "AVAX-USDT",
];
const FONDEO_PREFERRED = [
  "EUR-USDT",
  "GBP-USDT",
  "JPY-USDT",
  "NQ-USDT",
  "ES-USDT",
  "YM-USDT",
  "GC-USDT",
  "CL-USDT",
];

function normalizeSymbol(value: unknown): string {
  return String(value || "").trim().toUpperCase().replace(/\//g, "-");
}

function contractSymbol(contract: any): string {
  return normalizeSymbol(contract?.symbol ?? contract?.contractName ?? contract?.name);
}

function isTradable(contract: any): boolean {
  const symbol = contractSymbol(contract);
  const status = String(contract?.status ?? contract?.state ?? "").toUpperCase();
  if (!symbol) return false;
  if (status && !["1", "TRADING", "NORMAL", "ACTIVE"].includes(status)) return false;
  return true;
}

function classify(symbol: string): "ULTRA" | "FONDEO" {
  const normalized = symbol.replace(/[-_]/g, "");
  if (/^(EUR|GBP|JPY|NQ|ES|YM|GC|CL)USDT$/.test(normalized)) return "FONDEO";
  return "ULTRA";
}

async function main(): Promise<void> {
  const client = new BingXRestClient();
  const contracts = await client.getContracts();
  if (!Array.isArray(contracts) || contracts.length === 0) {
    throw new Error("PHASE2_UNIVERSE_EMPTY_CONTRACTS");
  }

  const available = new Set(
    contracts.filter(isTradable).map(contractSymbol).filter(Boolean),
  );

  let selected: string[];
  if (EXPLICIT.toUpperCase() !== "AUTO") {
    const requested = EXPLICIT.split(",").map(normalizeSymbol).filter(Boolean);
    const missing = requested.filter((symbol) => !available.has(symbol));
    if (missing.length) {
      throw new Error(`PHASE2_REQUESTED_SYMBOLS_UNAVAILABLE: ${missing.join(",")}`);
    }
    selected = [...new Set(requested)];
  } else {
    const ultra = ULTRA_PREFERRED.filter((symbol) => available.has(symbol));
    const fondeo = FONDEO_PREFERRED.filter((symbol) => available.has(symbol));
    selected = [...ultra, ...fondeo];
  }

  if (!selected.length) {
    throw new Error("PHASE2_UNIVERSE_EMPTY_AFTER_CONTRACT_FILTER");
  }

  const classified = selected.map((symbol) => ({ symbol, track: classify(symbol) }));
  const summary = {
    resolverVersion: "phase2-universe-v1",
    source: "BINGX_CONTRACTS",
    discoveredContracts: available.size,
    selectedSymbols: selected,
    tracks: {
      ULTRA: classified.filter((item) => item.track === "ULTRA").map((item) => item.symbol),
      FONDEO: classified.filter((item) => item.track === "FONDEO").map((item) => item.symbol),
    },
  };

  console.log(JSON.stringify(summary, null, 2));
  const output = process.env.GITHUB_OUTPUT;
  if (output) {
    const fs = await import("fs");
    fs.appendFileSync(output, `symbols<<EOF\n${selected.join(",")}\nEOF\n`);
    fs.appendFileSync(output, `universe_json<<EOF\n${JSON.stringify(summary)}\nEOF\n`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
