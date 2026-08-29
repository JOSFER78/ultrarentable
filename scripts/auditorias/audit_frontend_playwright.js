const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://127.0.0.1:3000';
const OUT_DIR = path.join(__dirname, 'frontend_audit_screenshots');

if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

const PAGES_TO_AUDIT = [
  { name: '01_hub_dashboard', path: '/estrategias', title: 'Portada & Hub Cuantitativo' },
  { name: '02_motor_en_vivo', path: '/estrategias/1-motor-en-vivo', title: 'Motor 24/7 Autónomo & Telemetría' },
  { name: '03_explorador_catalogo', path: '/estrategias/2-explorador-excel', title: 'Catálogo de Estrategias' },
  { name: '04_pipeline_gates', path: '/estrategias/3-pipeline-11-gates', title: 'Pipeline 10 Gates & FSM' },
  { name: '05_panel_investigador', path: '/estrategias/4-panel-investigador', title: 'Panel Investigador Cuantitativo' },
  { name: '06_estrategias_aprobadas', path: '/estrategias/5-estrategias-aprobadas', title: 'Estrategias Aprobadas (10/10)' },
  { name: '07_meta_estrategia', path: '/estrategias/6-meta-estrategia', title: 'Meta-Estrategia Ensamblada' },
  { name: '08_sistema_telemetria', path: '/sistema', title: 'Telemetría de Infraestructura' },
  { name: '09_track_fondeo', path: '/fondeo', title: 'Track Fondeo (CME Guard)' },
  { name: '10_ultra_lab', path: '/ultra', title: 'Ultra Lab (BingX 500x)' }
];

async function runAudit() {
  console.log('🚀 Iniciando Auditoría Frontend Playwright en ' + BASE_URL);
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });

  const results = [];

  for (const p of PAGES_TO_AUDIT) {
    const page = await context.newPage();
    const url = `${BASE_URL}${p.path}`;
    console.log(`\n🔍 Auditando: ${p.title} (${url})`);

    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    const pageErrors = [];
    page.on('pageerror', err => {
      pageErrors.push(err.message);
    });

    try {
      const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
      const status = response ? response.status() : 0;
      await page.waitForTimeout(1000);

      const screenshotPath = path.join(OUT_DIR, `${p.name}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: true });

      const heading = await page.textContent('h1, h2').catch(() => 'N/A');
      const bodyText = await page.textContent('body');
      const hasMockText = bodyText ? /mock|synthetic|placeholder/i.test(bodyText) : false;

      results.push({
        name: p.name,
        title: p.title,
        path: p.path,
        http_status: status,
        heading: heading ? heading.trim().substring(0, 80) : 'N/A',
        screenshot: screenshotPath,
        console_errors_count: consoleErrors.length,
        page_errors_count: pageErrors.length,
        zero_mock_verified: !hasMockText,
        render_success: status === 200 && pageErrors.length === 0,
      });

      console.log(`  ✅ HTTP ${status} | Heading: "${heading ? heading.trim().substring(0, 40) : 'N/A'}..." | Screenshot guardado`);
    } catch (err) {
      console.error(`  ❌ Error auditando ${p.path}:`, err.message);
      results.push({
        name: p.name,
        title: p.title,
        path: p.path,
        http_status: 500,
        error: err.message,
        render_success: false,
      });
    } finally {
      await page.close();
    }
  }

  await browser.close();

  const reportFile = path.join(OUT_DIR, 'audit_report.json');
  fs.writeFileSync(reportFile, JSON.stringify(results, null, 2));
  console.log('\n📊 Auditoría Finalizada. Resumen guardado en ' + reportFile);
}

runAudit().catch(err => {
  console.error('Fatal audit error:', err);
  process.exit(1);
});
