import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const symbol = process.argv[2];
if (!symbol || !/^[A-Z0-9]+-[A-Z]+$/.test(symbol)) {
  throw new Error("symbol must use BingX BASE-QUOTE format");
}

const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROMIUM_PATH || "/snap/bin/chromium",
  args: ["--no-sandbox"],
});

try {
  const page = await browser.newPage();
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/quote/contract/marginTiered/get") &&
      response.status() === 200,
    { timeout: 60_000 },
  );
  await page.goto(
    `https://bingx.com/en/tradeInfo/perpetual/maintenance-margin-ratio/${symbol}`,
    { waitUntil: "domcontentloaded", timeout: 60_000 },
  );
  const response = await responsePromise;
  process.stdout.write(await response.text());
} finally {
  await browser.close();
}
