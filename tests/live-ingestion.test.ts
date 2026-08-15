import assert from "node:assert/strict";
import os from "node:os";
import path from "node:path";
import fs from "node:fs";
import { BingXRestClient } from "../packages/bingx-client/src/rest";
import { DataIngestionService } from "../services/data-ingestion/src/recorder";

async function main() {
  if (process.env.RUN_LIVE_BINGX_TESTS !== "1") {
    console.log("SKIPPED: set RUN_LIVE_BINGX_TESTS=1 to run BingX network tests.");
    return;
  }
  const temporaryDir = fs.mkdtempSync(path.join(os.tmpdir(), "bingx-ultra-test-"));
  const client = new BingXRestClient();
  const contracts = await client.getContracts();
  assert.ok(Array.isArray(contracts) && contracts.length > 0);

  const ingestion = new DataIngestionService(temporaryDir, client);
  const dataset = await ingestion.downloadKlines("ETH-USDT", "1h", 20);
  assert.ok(dataset.count > 0);
  assert.equal(dataset.checksum.length, 64);
  console.log(JSON.stringify({ temporaryDir, dataset }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
