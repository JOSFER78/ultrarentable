const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  console.log('Navigating to prop-firms...');
  await page.goto('http://127.0.0.1:3000/prop-firms', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2000);
  const outPath = '/tmp/prop_firms_live.png';
  await page.screenshot({ path: outPath, fullPage: false });
  console.log('CAPTURED_OK:', outPath);
  await browser.close();
})();
