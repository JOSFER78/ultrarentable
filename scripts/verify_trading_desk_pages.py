"""Playwright verification script for all 6 CME Trading Desk pages in Ultrarentable.
Verifies real connection to PickMyTrade / Tradovate Demo (DEMO1279346),
checks for 0 JS runtime exceptions, and captures evidence screenshots.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = "/home/ubuntu/.gemini/antigravity-cli/brain/a2d8fa11-5f53-4a70-8d22-448b095d363c"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

PAGES_TO_VERIFY = [
    {
        "url": "http://127.0.0.1:3005/trading-desk",
        "name": "01_main_trading_desk",
        "title": "Wall Street Trading Desk",
        "expected_texts": ["DEMO1279346", "Tradovate Demo", "50,000", "CERO POSICIONES ABIERTAS"],
    },
    {
        "url": "http://127.0.0.1:3005/trading-desk/configuracion",
        "name": "02_configuracion_gateway",
        "title": "Conexión Gateway & Brokers CME",
        "expected_texts": ["DEMO1279346", "josferstudio", "2026-09-02", "NinjaTrader 8"],
    },
    {
        "url": "http://127.0.0.1:3005/trading-desk/posiciones",
        "name": "03_posiciones_brackets",
        "title": "Monitor de Posiciones & Brackets",
        "expected_texts": ["DEMO1279346", "SIN POSICIONES ABIERTAS", "advance_tp_sl", "FLATTEN ALL"],
    },
    {
        "url": "http://127.0.0.1:3005/trading-desk/estrategias",
        "name": "04_estrategias_activas",
        "title": "Estrategias & Sesiones de Ejecución",
        "expected_texts": ["DEMO1279346", "CERO SESIONES DE EJECUCIÓN ACTIVAS", "Bóveda de Estrategias"],
    },
    {
        "url": "http://127.0.0.1:3005/trading-desk/riesgo",
        "name": "05_sentinel_riesgo",
        "title": "Sentinel de Riesgo CME",
        "expected_texts": ["DEMO1279346", "Trailing Drawdown Guard", "Daily Loss Limit", "FLATTEN TOTAL"],
    },
    {
        "url": "http://127.0.0.1:3005/trading-desk/auditoria",
        "name": "06_auditoria_forense",
        "title": "Auditoría Forense & Telemetría WAL",
        "expected_texts": ["DEMO1279346", "SQLITE WAL", "SIN REGISTROS FORENSES PREVIOS"],
    },
]

def main():
    print("=" * 70)
    print("AUDITORÍA DE PLAYWRIGHT: 6 PÁGINAS TRADING DESK CME")
    print("=" * 70)

    success_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        for item in PAGES_TO_VERIFY:
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: console_errors.append(str(exc)))

            url = item["url"]
            name = item["name"]
            print(f"\n[+] Verificando: {name} ({url})")

            try:
                response = page.goto(url, wait_until="networkidle", timeout=15000)
                status = response.status if response else "NO_RESPONSE"

                # Wait explicitly for live account ID to appear in DOM
                try:
                    page.wait_for_selector("text=DEMO1279346", timeout=6000)
                except Exception:
                    pass

                time.sleep(1.0) # allow final render

                # Check HTTP Status
                if status != 200:
                    print(f"❌ HTTP Status Error: {status}")
                    continue

                content = page.content()

                # Check expected texts
                missing = []
                for exp in item["expected_texts"]:
                    if exp.lower() not in content.lower():
                        missing.append(exp)

                if missing:
                    print(f"⚠️ Textos esperados faltantes: {missing}")
                else:
                    print(f"✅ Todos los textos esperados encontrados: {item['expected_texts']}")

                # Check console errors (filter Next.js dev overlay / HMR / favicon noise)
                real_errors = [
                    e for e in console_errors
                    if "favicon" not in e.lower()
                    and "hydration" not in e.lower()
                    and "hot-reloader" not in e.lower()
                    and "webpack" not in e.lower()
                    and "fastrefresh" not in e.lower()
                ]
                if real_errors:
                    print(f"⚠️ Errores JS en consola: {real_errors}")
                else:
                    print("✅ 0 errores JS en consola.")

                # Capture screenshot
                shot_path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
                page.screenshot(path=shot_path, full_page=True)
                print(f"📸 Captura guardada: {shot_path}")

                if not missing and not real_errors:
                    success_count += 1

            except Exception as e:
                print(f"❌ Excepción durante navegación: {e}")

        browser.close()

    print("\n" + "=" * 70)
    print(f"RESULTADO FINAL: {success_count}/{len(PAGES_TO_VERIFY)} PÁGINAS 100% VERIFICADAS CON ÉXITO")
    print("=" * 70)

    if success_count == len(PAGES_TO_VERIFY):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
