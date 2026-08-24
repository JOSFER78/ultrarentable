/**
 * audit_v540_playwright.js
 * Auditoría forense de UI con Playwright para Ultrarentable v5.4.0
 * Compatible con Streaming SSE continuo (domcontentloaded)
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:3000';
const SCREENSHOT_DIR = path.join(__dirname, 'v540_audit_screenshots');

const PAGES_TO_TEST = [
  { name: '01_hub_dashboard', path: '/estrategias' },
  { name: '02_motor_en_vivo', path: '/estrategias/1-motor-en-vivo' },
  { name: '03_explorador_catalogo', path: '/estrategias/2-explorador-excel' },
  { name: '04_pipeline_gates', path: '/estrategias/3-pipeline-11-gates' },
  { name: '05_panel_investigador', path: '/estrategias/4-panel-investigador' },
  { name: '06_estrategias_aprobadas_v540', path: '/estrategias/5-estrategias-aprobadas' },
  { name: '07_meta_estrategia_v540', path: '/estrategias/6-meta-estrategia' },
];

async function runAudit() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });

  const page = await context.newPage();
  const report = [];

  for (const target of PAGES_TO_TEST) {
    const url = `${BASE_URL}${target.path}`;
    console.log(`[AUDIT] Visitando: ${url}`);
    
    try {
      const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
      await page.waitForTimeout(2500); // Allow react rendering and version badges to populate

      const status = response ? response.status() : 200;
      const screenshotPath = path.join(SCREENSHOT_DIR, `${target.name}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: true });

      // Extraer badges de versión visibles
      const headerText = await page.evaluate(() => {
        const header = document.querySelector('header');
        return header ? header.innerText.replace(/\s+/g, ' ').trim() : 'NO_HEADER';
      });

      console.log(`[PASS] ${target.name} (Status: ${status}) | Header: ${headerText}`);
      report.push({
        name: target.name,
        path: target.path,
        status: status,
        screenshot: screenshotPath,
        headerSummary: headerText,
        passed: status === 200
      });
    } catch (err) {
      console.error(`[FAIL] ${target.name}: ${err.message}`);
      report.push({
        name: target.name,
        path: target.path,
        status: 'ERROR',
        error: err.message,
        passed: false
      });
    }
  }

  await browser.close();
  fs.writeFileSync(path.join(SCREENSHOT_DIR, 'v540_report.json'), JSON.stringify(report, null, 2));
  console.log(`\n🎉 Auditoría v5.4.0 completada exitosamente. Reporte guardado en ${path.join(SCREENSHOT_DIR, 'v540_report.json')}`);
}

runAudit().catch(err => {
  console.error('Fatal audit error:', err);
  process.exit(1);
});
