const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 950 },
    deviceScaleFactor: 2
  });
  const page = await context.newPage();

  console.log('Navigating to http://127.0.0.1:3000/prop-firms...');
  await page.goto('http://127.0.0.1:3000/prop-firms', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(1500);

  // Tab 1: Mega-Catálogo
  await page.screenshot({ path: '/tmp/tab1_catalog_final.png' });
  console.log('Tab 1 captured');

  // Tab 2: Mega-Comparador
  await page.locator('button:has-text("2. Mega-Comparador")').first().click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/tmp/tab2_comparator_final.png' });
  console.log('Tab 2 captured');

  // Tab 3: Cupones
  await page.locator('button:has-text("3. Cupones")').first().click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/tmp/tab3_deals_final.png' });
  console.log('Tab 3 captured');

  // Tab 5: Calculadora ROI
  await page.locator('button:has-text("5. Calculadora")').first().click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/tmp/tab5_roi_final.png' });
  console.log('Tab 5 captured');

  console.log('ALL_FINAL_TABS_CAPTURED');
  await browser.close();
})();
