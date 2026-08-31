> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: registro puntual de fix del 2026-08-09; histórico. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

# ULTRA — Fix OFFLINE SQX en preview Hermes + quality gates del motor

> Fecha: 2026-08-09 · Estado: RESUELTO y verificado

---

## 1) Proyecto ubicable: preview Hermes Desktop

**Proyecto:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`
Web: puerto 3000 (Next.js) · API: puerto 8000 (FastAPI) · SQX MCP: puerto 8080.
Acceso desde PC: `http://100.104.148.117:3000/strategyquant` (IP Tailscale del VPS).

### Síntoma
El panel de búsqueda mostraba `🔴 OFFLINE` para el SQX MCP **en el preview del browser de Hermes Desktop**, aunque en la VPS (localhost) el API respondía `ONLINE`.
Error en consola del browser:
```
Access to fetch at 'http://100.104.148.117:8000/api/v1/sqx/status' from origin
'http://100.104.148.117:3000' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present...
```

### Causa raíz
El frontend (`apps/web/lib/api.ts`) construía `BASE_URL = http://${window.location.hostname}:8000`.
El navegador (en origen `:3000`) hacía un fetch cross-origin a `:8000` (otro puerto = otro origen) y el API en 8000 **no mandaba `Access-Control-Allow-Origin`** → CORS bloqueaba → OFFLINE. El puerto 8000 además no está expuesto hacia fuera (solo 80/443); por eso "en la VPS sí, en el PC no".

### Solución definitiva (proxy same-origin en el propio Next.js — NO túnel, NO abrir 8000)
1. **`apps/web/next.config.ts`:**
```ts
const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" }];
  },
};
```
2. **`apps/web/lib/api.ts`:** el navegador usa ruta relativa (mismo origen → `:3000/api/...`),
   SSR usa `127.0.0.1:8000`, y `NEXT_PUBLIC_API_URL` puede sobrescribir.
```ts
const explicitUrl = process.env.NEXT_PUBLIC_API_URL;
const BASE_URL = explicitUrl
  ? explicitUrl.replace(/\/$/, "")
  : typeof window === "undefined"
    ? `http://127.0.0.1:8000`
    : ""; // mismo origen :3000 -> Next proxea a 8000
```
3. Reconstruir y reiniciar el servicio:
```bash
cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/apps/web"
export NEXT_TELEMETRY_DISABLED=1
node "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/node_modules/.bin/next" build
systemctl --user restart ultrarentable-web
```
4. **Verificación:** el fetch del navegador va a `http://100.104.148.117:3000/api/v1/sqx/status` (mismo origen → sin CORS) y Next proxea al 8000.
   Comprobado con:
```bash
curl -H "Origin: http://100.104.148.117:3000" http://100.104.148.117:3000/api/v1/sqx/status
# -> {"status":"ONLINE",...}  HTTP 200
```
5. Para que el preview coja el cambio: reabrir la URL con `open_preview` / recarga.

> Nota: NordVPN está instalado en la VPS pero **NO conectado** (sin interfaz nordlynx/tun) → no es la causa.
> Nota 2: el subagente que propuso cambiar Nginx (`/etc/nginx`) fue bloqueado por permisos; la solución por proxy de Next es la correcta y no toca Nginx.

---

## 2) Motor: validaba basura (20% profit / 260% DD)

El motor de búsqueda daba por válidas estrategias ruinosas porque **ninguna capa penalizaba/gateaba el drawdown**.

### Fix
- Nuevo `services/api/app/factory/quality_gates.py` (política drawdown central):
  - `is_ruinous(dd)` → `True` si dd >= 100% (ruina).
  - `calmar_ratio(ret, dd)` y `MIN_CALMAR_RATIO = 0.5`.
  - `rentable(...)`, `drawdown_penalty_factor(...)`, `risk_adjusted_fitness(...)`.
- Cableado en: `optimization_loop.py` (fitness/breeding_fitness matan ruina y penalizan DD),
  `strategy_evidence.py` (gates `RUINOUS_DRAWDOWN` y `RETURN_TO_DRAWDOWN_RATIO_TOO_WEAK`),
  `adversarial_validation.py` (`RUINOUS_DRAWDOWN_IN_ADVERSARIAL_WINDOW`),
  `fast_engine_campaign.py` (pasa `max_drawdown_pct`/`net_return_pct` a CandidateResult),
  `sqx_router.py` (`/ingest` marca `SQX_REJECTED_RISK`; `/rentable` filtra DD ruinoso y Calmar).
- Test de regresión: `services/api/tests/test_quality_gates_regression.py` (6 tests verdes)
  que prueban que una estrategia 20%/260% ya NO se valida ni se rankea.

### Pitfall (importante)
En `drawdown_penalty_factor` / `risk_adjusted_fitness`, el drawdown **desconocido (None) debe ser NEUTRO (factor 1.0), no 0.0**. Si devuelve 0.0, aniquila el fitness de cualquier `CandidateResult` sin DD explícito y rompe la evolución (fix del subagente A; la suite completa pasa: **118 passed, 5 skipped**).

---

## Verificación actual
- `python -m pytest services/api/tests/ -q` → **118 passed, 5 skipped, 0 failed**.
- `/api/v1/sqx/status` vía `:3000` mismo origen → **ONLINE (HTTP 200)**.
- Endpoint `/api/v1/sqx/rentable` devuelve solo estrategias que pasan gates (2 de 24 hoy), con DD bajos.

---

## 3) DOCTRINA ULTRA vs FONDEO (usuario, 2026-08-09) — CRÍTICA

> "No es lo mismo buscar una estrategia para ultrarentable que para fondeo... busca cosas diferentes. Debe tener un configurador auto-asistido por IA para buscar, y DEBE saber todas las técnicas de StrategyQuant, lanzar todo tipo de investigación para aprender a usarlo y utilizar todo tipo de estrategias para lograr rentabilidad extraordinaria, aunque se queme la cuenta 8 de 10."

- **MODO ULTRA (kamikaze):** buscar MULTIPLICADOR EXTREMO aunque se queme la cuenta 8/10.
  → **NO filtrar por drawdown / Sharpe / curva poco estable.**
  → SOLO se invalida la RUINA REAL: liquidación / equity <= 0 (max_drawdown >= 100%).
- **MODO FONDEO (conservador):** pasar evaluaciones de prop firms.
  → SÍ exige DD bajo, consistencia, sin daily loss, ratio retorno/DD sano.
- **Fuente (Ultrarentable.md, Obsidian):** "El modo extremo NO descarta una estrategia por Sharpe, drawdown o curva poco estable. Sí exige datos reales, contabilidad correcta, costes, margen, liquidaciones y resultados reproducibles."
- **Consecuencia en el código:** el gate de drawdown debe ser POR MODO. `is_ruinous` (dd>=100) aplica SIEMPRE. El gate de Calmar / DD-sostenible (85%) aplica SOLO en modo 'fondeo'. En 'ultra', un candidato con DD alto no-ruinoso (p.ej. 90%) pero que no se liquidó y tiene retorno real puede rankearse.
- **Configurador de búsqueda auto-asistido por IA:** define mode ('ultra'|'fondeo'), project SQX (Ultra_Auto_Pilot), databank (Results), instrument/timeframe, population, objetivo de multiplicador (ultra) / max DD-consistencia (fondeo), y las técnicas de StrategyQuant a aplicar. Los resultados SIEMPRE vienen de SQX real (nada inventado).
- **Catálogo de técnicas StrategyQuant:** documento `docs ayuda/tecnicas estrategias ultrarentables/06_CATALOGO_TECNICAS_STRATEGYQUANT.md` (generado por subagente de investigación).

### Implementación en curso (2026-08-09)
- Subagente B: reconcilia quality_gates por MODO + configura configurador de búsqueda IA (endpoint + UI).
- Subagente A: documenta catálogo de técnicas de StrategyQuant (desde Obsidian REST + web).
