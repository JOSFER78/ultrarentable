import { DataIngestionService } from "../services/data-ingestion/src/recorder";

async function main() {
  const ingestion = new DataIngestionService();
  const catalog = await ingestion.syncInstrumentCatalog();
  console.log(`Catalog: ${catalog.count} instruments; SHA-256 ${catalog.checksum}`);

  for (const symbol of ["BTC-USDT", "ETH-USDT", "SOL-USDT"]) {
    const dataset = await ingestion.downloadKlines(symbol, "1h", 1000);
    console.log(`${symbol}: ${dataset.count} closed candles; gaps=${dataset.gapCount}; SHA-256 ${dataset.checksum}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
