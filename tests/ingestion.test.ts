import assert from "assert";
import { BingXRestClient } from "../packages/bingx-client/src/rest";
import { DataIngestionService } from "../services/data-ingestion/src/recorder";

async function runIngestionTests() {
  console.log("==========================================");
  console.log("  Running REAL-ONLY Ingestion Test Suite ");
  console.log("==========================================");

  const restClient = new BingXRestClient();

  console.log("\n[TEST 1] Fetching BingX Contracts...");
  const contracts: any[] = await restClient.getContracts();
  assert(Array.isArray(contracts), "Contracts must be an array");
  assert(contracts.length > 100, `Expected >100 contracts, got ${contracts.length}`);
  console.log(`✓ Passed: Received ${contracts.length} real contracts from BingX.`);

  console.log("\n[TEST 2] Fetching Real Klines for ETH-USDT...");
  const klines: any[] = await restClient.getKlines("ETH-USDT", "1h", 10);
  assert(Array.isArray(klines), "Klines must be an array");
  assert.strictEqual(klines.length, 10, "Should return 10 candles");
  assert(klines[0].open !== undefined, "Candle must contain open price");
  console.log(`✓ Passed: Received ${klines.length} real candles for ETH-USDT.`);

  console.log("\n[TEST 3] Testing Data Ingestion Service & Manifest Generation...");
  const ingestion = new DataIngestionService();
  const catalogRes = await ingestion.syncInstrumentCatalog();
  assert(catalogRes.count > 100, "Catalog count should be > 100");
  assert.strictEqual(catalogRes.checksum.length, 64, "Checksum must be 64-char SHA256 string");
  console.log(`✓ Passed: Catalog sync saved ${catalogRes.count} contracts. Checksum: ${catalogRes.checksum.slice(0, 16)}...`);

  console.log("\n[TEST 4] Testing Historical Kline Dataset Ingestion & Checksum...");
  const datasetRes = await ingestion.downloadKlines("ETH-USDT", "1h", 50);
  assert(datasetRes.count >= 48 && datasetRes.count <= 50, `Dataset count should be near limit, got ${datasetRes.count}`);
  assert.strictEqual(datasetRes.checksum.length, 64, "Dataset checksum must be valid SHA256");
  console.log(`✓ Passed: Dataset saved. Checksum: ${datasetRes.checksum.slice(0, 16)}...`);

  console.log("\n==========================================");
  console.log(" ALL REAL-ONLY TESTS PASSED SUCCESSFULLY! ");
  console.log("==========================================");
}

runIngestionTests().catch((err) => {
  console.error("TEST_FAILURE:", err);
  process.exit(1);
});
