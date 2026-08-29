> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: plan maestro 12 fases (2026-08-08) sustituido por docs/00_MASTER_IDEAS_Y_PLAN.md §4. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

# 🎯 PLAN MAESTRO ULTRARRENTABLE — CONSTRUCCIÓN MODULAR BOTTOM-UP

**Fecha:** 2026-08-08 (reestructurado)
**Fuente de verdad:** informe modular del usuario + 6 informes de investigación (`plan_implementacion/`) + verificación directa VPS
**Método:** REAL-ONLY · construcción **de abajo hacia arriba** · plataforma modular (NO wizard secuencial) · cada capa depende de la anterior y termina ejecutable/verificable

---

## 🦴 EL PRINCIPIO RECTOR (lo que el usuario quiere)

> **No es una secuencia cerrada de pantallas — es una APLICACIÓN MODULAR en la que puedes saltar en cualquier momento entre módulos, manteniendo siempre el contexto y la navegación global permanente.**

1. **Acceso global permanente** a los módulos (la navegación nunca desaparece).
2. **Ultra y Fondeo separados**: NO comparten la misma lógica de riesgo.
3. **Fondeo = zona de seguridad reforzada**: permisos, reglas, límites y alertas propios, con niveles (VER → CONFIGURAR → AUTORIZAR → ACTIVAR → EJECUTAR).
4. **Robots = capa de ejecución** (pueden ser Ultra, Fondeo u otros).
5. **Estrategias independientes de las cuentas**: una estrategia puede desplegarse en varias cuentas/exchanges.
6. **El sistema puede crecer sin rehacer la navegación.**

## Construcción en 2 tiempos
- **Primero: 8 VISTAS MAESTRAS** (el esqueleto). No 16 pantallas.
- **Después: cada módulo se desarrolla HACIA DENTRO**, capa por capa, SOLO cuando su dependencia inferior funciona.

---

## 🗺️ EL MAPA MODULAR (8 vistas maestras — el esqueleto permanente)

```
                         ┌─────────────────────┐
                         │      DASHBOARD      │
                         └──────────┬──────────┘
                                    │
        ┌──────────────┬────────────┼────────────┬──────────────┐
        ↓              ↓            ↓            ↓              ↓
   ESTRATEGIAS       ULTRA        FONDEO       ROBOTS       PORTFOLIO
        │              │            │             │              │
        └──────────────┴────────────┴─────────────┴──────────────┘
                                    │
                              ALERTAS / LOGS
                                    │
                              AJUSTES / SEGURIDAD
```

**Dentro de cada zona (se desarrolla hacia dentro, en fases posteriores):**

- **Buscar Estrategias:** Buscar → Resultados → Ficha → Validación → Estrategia aprobada
- **Ultra:** Cuentas · Exchanges · Estrategias · Simulaciones · Robots · Portfolio Ultra
- **Fondeo:** Firmas · Cuentas · Reglas · Simulaciones · Robots · Control de riesgo · Auditoría
- **Robots:** Todos · Ultra · Fondeo · Otros → Robot → Cuenta → Exchange → Estrategia → Estado/ejecución

---

## 📊 RESUMEN DE FASES — DE ABAJO HACIA ARRIBA

| # | Capa | Depende de | Entregable | Estado |
|---|---|---|---|---|
| **0** | 🦴 Esqueleto modular (8 vistas + nav global) | — | Build OK + mapa de 8 vistas con navegación permanente | 🔄 se rehace |
| **1** | 🔌 Conexión StrategyQuant (fábrica) | 0 | SQX MCP ONLINE + generar estrategias reales | ✅ VALIDADO |
| **1B** | 🧲 Conexión NautilusTrader (motor canónico) | 1 | Adapter + replay/backtest correcto | 🔴 pendiente |
| **2** | 🔎 Búsqueda de estrategias perfeccionada | 1 | Config + proceso en vivo + herramientas de búsqueda | ✅ F2/F2B |
| **3** | 🧪 Ficha + validación de estrategia | 1, 2 | Ficha completa · fast engine · 2º motor → CANONICAL | ⚠️ parcial |
| **4** | 🟣 Módulo ULTRA | 3 | Cuentas/exchanges/simulaciones/portfolio ultra | 🔴 pendiente |
| **5** | 🟠 Módulo FONDEO (zona restringida) | 3 | Firmas/reglas/simulaciones + permisos VER→EJECUTAR | 🔴 pendiente |
| **6** | 🤖 Módulo ROBOTS (capa de ejecución) | 4, 5 | Robots Ultra/Fondeo → cuenta → exchange → estado | 🔴 pendiente |
| **7** | 📊 PORTFOLIO | 4, 5, 6 | Estrategias × cuentas/exchanges agregadas | 🔴 pendiente |
| **8** | 🛡️ ALERTAS/LOGS + AJUSTES/SEGURIDAD | 6, 7 | Alertas, logs, permisos, kill switch, auditoría | 🔴 pendiente |
| **9** | 🏠 DASHBOARD unificado | 8 | Todo en 1 pantalla con 1 botón | 🔴 pendiente |

> **Regla de oro:** NUNCA se construye una capa sin que su(s) dependencia(s) inferior(es) estén verificadas con ejecución real + tests.

---

# FASE 0 — ESQUELETO MODULAR (8 VISTAS MAESTRAS + NAVEGACIÓN GLOBAL) 🔄 REHACER
**Objetivo:** convertir la web en una **plataforma modular** con 8 vistas maestras y navegación global **siempre disponible**, NO en un wizard secuencial.

**Dependencia inferior:** ninguna (es el cimiento de la navegación).

**Entregable:**
- [ ] Mapa de 8 vistas maestras: **Dashboard · Estrategias · Ultra · Fondeo · Robots · Portfolio · Alertas/Logs · Ajustes/Seguridad**
- [ ] Sidebar/menú global **permanente**: el usuario puede saltar de cualquier módulo a otro sin perder contexto
- [ ] Migas de pan (breadcrumb) por zona
- [ ] Separación de zonas: 🟣 Ultra y 🟠 Fondeo como **módulos independientes** (no comparten riesgo)
- [ ] Estado visual: indicador por zona (Ej. Fondeo → "⚠ CONTROL ESTRICTO ACTIVO")
- [ ] `npm run web:build` compila + render real verificado (screenshot)

> ⚠️ **Pitfall build (Next.js 16 / Turbopack):** valores CSS sin comillas en inline styles (`letterSpacing: 0.05em` → `"0.05em"`) rompen el build; handlers en Server Components rompen prerender (→ `"use client"`). Tras el build reiniciar `systemctl --user restart ultrarentable-web`.

---

# FASE 1 — CONEXIÓN STRATEGYQUANT (LA FÁBRICA) ✅ VALIDADA (2026-08-08)
**Dependencia inferior:** Fase 0 (la vista Estrategias existe y puede mostrar candidatos).

**Verificado con ejecución real:**
1. ✅ Handshake MCP (`initialize` → `Mcp-Session-Id`; reenviar en cada llamada; protocolVersion `2025-03-26`)
2. ✅ 6 tools: `list_projects`, `list_databanks`, `list_strategies`, `get_strategy_stats`, `run_project`, `stop_project`
3. ✅ SQX corre 24/7 en el VPS (`systemctl --user status strategyquantx`, `127.0.0.1:8080/mcp`, DISPLAY=:99)
4. ✅ `POST /api/v1/sqx/projects/Ultra_Auto_Pilot/run` → generó 24 estrategias reales
5. ✅ `POST .../ingest` → 24 `SQX_CANDIDATE` + 24 `SQX_BUILTIN`, 0 duplicados
6. ✅ API proxy: `GET /api/v1/sqx/status|tools|projects`, `GET .../databanks/{db}/strategies[/{strat}]`

**Pitfall crítico (verificado):** `get_strategy_stats` → fila `[name, group, ...42 columnas]` → **offset = 2**. NO `len(values)-len(columns)` (da 3 y desalinea todo: net=0.00, trades=0 en todas). Síntoma: todas las filas idénticas. Hardcode `offset = 2`.

**Datos:** SQX trae su propio histórico (`user/data/History`) → **NO descargar velas** para generar.

**Criterio:** ✅ estrategias SQX conectadas y generando candidatos con stats reales visibles.

---

# FASE 1B — CONEXIÓN NAUTILUSTRADER (MOTOR CANÓNICO) 🔴 PENDIENTE
**Dependencia inferior:** Fase 1 (necesita candidatos StrategySpec que re-ejecutar).

**Objetivo:** el motor canónico independiente que repite el backtest para detectar resultados falsos (2º motor / doctrina REAL-ONLY).

**Entregable:**
- [ ] Adapter NautilusTrader (DSL/StrategySpec → Nautilus strategy)
- [ ] Replay/backtest correcto sobre datasets aprobados
- [ ] Reglas de riesgo BingX frescas (snapshot ≤24h) como input
- [ ] Etiquetado: `CANONICAL` solo cuando Nautilus confirma el resultado del fast engine
- [ ] Tests de reproducibilidad

**Criterio:** ✅ una estrategia etiquetada `CANONICAL` tras repetirse en NautilusTrader.

---

# FASE 2 — BÚSQUEDA DE ESTRATEGIAS PERFECCIONADA ✅ F2/F2B VALIDADA (2026-08-08)
**Dependencia inferior:** Fase 1 (SQX funcional) — conecta la búsqueda a la fábrica.

**Entregable (mucho de esto ya validado):**
- ✅ **Consola de búsqueda en la home**: configuración visible (proyecto `Ultra_Auto_Pilot`, databank Results, BTC/ETH 1h, población), proceso en vivo "cómo busca" (run SQX + log en tiempo real), decisiones reales, candidatos apareciendo en vivo.
- ✅ **Herramientas para buscar estrategias ultrarentables**: `POST .../run` → espera → `ingest` → `GET /api/v1/sqx/rentable` (une strategies con backtests, ordena por **profit factor**).
- ✅ **Resultados con detalle real**: Strategy 1.1.43 (+37.17% · PF 1.56 · 61 trades), 1.1.28 (PF 2.13)… con bifurcación ⚡Ultra/🏛️Fondeo.

**Perfeccionar (siguiente iteración):**
- [ ] Más herramientas de búsqueda (filtros por familia, IS/OOS, régimen, walk-forward)
- [ ] Historia de búsquedas + reutilización de configs
- [ ] Exportar a las vistas Ultra/Fondeo (bifurcación en la navegación)

**Criterio:** ✅ el usuario ve cómo busca SQX con su configuración y las estrategias rentables reales.

---

# FASE 3 — FICHA DE ESTRATEGIA + VALIDACIÓN ⚠️ PARCIAL
**Dependencia inferior:** Fase 1B (2º motor) para CANONICAL; Fase 2 para los resultados.

**Flujo:** candidato → StrategySpec (neutral) → fast engine determinista (sin look-ahead, fees reales) → `FAST_APPROXIMATE` → (con Fase 1B) 2º motor → `CANONICAL`.

**Entregable:**
- ✅ Ficha de estrategia con métricas reales (net, PF, DD, trades, ret%, etiqueta de validación)
- ✅ Fast engine desbloqueado (reglas de riesgo recapturadas con `refresh_bingx_risk_rules.py`; backtest real `FAST_APPROXIMATE` +5.79% · PF 1.42 · 118 trades · fees reales 302.64 USDT · suite 112 pass)
- 🔴 Falta: validador independiente (2º motor) para etiquetar CANONICAL
- 🔴 Nunca mezclar `FAST_APPROXIMATE` con `CANONICAL` en la UI

**Criterio:** ✅ N candidatos pasan el fast engine y se etiquetan correctamente; **nunca CANONICAL sin 2º motor**.

---

# FASE 4 — MÓDULO ULTRA 🟣 🔴 PENDIENTE
**Dependencia inferior:** Fase 3 (estrategias validadas).

**Dentro:** Cuentas · Exchanges · Estrategias · Simulaciones · Robots · **Portfolio Ultra**
- [ ] Zona flexible: "probar, multiplicar, experimentar, construir carteras"
- [ ] Doctrina Kamikaze aplicada (no filtrar por DD/Sharpe; invalida solo liquidación/equity≤0)
- [ ] Cuentas y exchanges paramétricos (MVP BingX)
- [ ] Simulaciones de carteras de "balas"
- [ ] Pre-requisito ejecución: API key BingX + autorización explícita (NUNCA automática)

**Criterio:** ✅ el módulo Ultra muestra cuentas/exchanges/estrategias y simula carteras reales.

---

# FASE 5 — MÓDULO FONDEO 🟠 ZONA RESTRINGIDA 🔴 PENDIENTE
**Dependencia inferior:** Fase 3 (estrategias validadas). **NO comparte lógica de riesgo con Ultra.**

**Dentro:** Firmas · Cuentas · Reglas · Simulaciones · Robots · **Control de riesgo** · **Auditoría**
- [ ] Pantalla con **"⚠ CONTROL ESTRICTO ACTIVO"** (riesgo permitido: daily loss %, max DD %, profit target %, reglas bloqueadas, límites activos, kill switch, auditoría)
- [ ] **Niveles de permiso**: VER → CONFIGURAR → AUTORIZAR → ACTIVAR → EJECUTAR
  - No permitir que desde una pantalla normal se cambien las reglas alegremente (incluso admin)
  - Base para un sistema de permisos serio
- [ ] Prop-Firm Constraint Engine (1 firma MVP): **FundedNext Rapid Pro** (bots ✅, ~$150, 90% split, sin daily loss) o **Bulenox free trial 14d**
- [ ] Motor de veto: daily loss lock, trailing drawdown/HWM, tamaño máx, sesiones, noticias, consistencia, kill switch
- [ ] Simulación de cuentas funded con reglas reales

**Criterio:** ✅ constraint engine probado con reglas reales + niveles de permiso funcionando.

---

# FASE 6 — MÓDULO ROBOTS 🤖 (CAPA DE EJECUCIÓN) 🔴 PENDIENTE
**Dependencia inferior:** Fases 4 y 5 (Ultra y Fondeo definen sus robots).

**Dentro:** Todos · Ultra · Fondeo · Otros → **Robot → Cuenta → Exchange → Estrategia → Estado/ejecución**
- [ ] Robot genérico desacoplado: un robot puede ser Ultra, Fondeo u otro tipo
- [ ] Un robot asocia: estrategia + cuenta + exchange
- [ ] Estados: configurado → simulación → deploy → monitor → logs
- [ ] Una estrategia puede desplegarse en varios robots/cuentas

**Criterio:** ✅ un robot real (Ultra o Fondeo) simula con una estrategia y muestra estado/ejecución.

---

# FASE 7 — MÓDULO PORTFOLIO 📊 🔴 PENDIENTE
**Dependencia inferior:** Fases 4, 5, 6 (cuentas + estrategias + robots).

- [ ] Agregación: **estrategias × cuentas/exchanges** (una estrategia en varias cuentas)
- [ ] Vista de cartera Ultra + cartera Fondeo
- [ ] Rendimiento agregado con trazabilidad

**Criterio:** ✅ el usuario ve sus estrategias desplegadas y su rendimiento agregado por cuenta/exchange.

---

# FASE 8 — ALERTAS/LOGS + AJUSTES/SEGURIDAD 🛡️ 🔴 PENDIENTE
**Dependencia inferior:** Fases 6 y 7 (hay ejecución que vigilar).

- [ ] **Alertas/Logs**: equity, DD diario, distancia al límite, días ganadores, trades/día, alertas (Telegram/correo) al 80% del límite
- [ ] **Ajustes/Seguridad**: permisos por nivel (VER→EJECUTAR), kill switch global, auditoría, límites
- [ ] Cron diario de seguimiento de cuentas fondadas

**Criterio:** ✅ alerta de prueba real + log de auditoría + kill switch operable.

---

# FASE 9 — DASHBOARD UNIFICADO 🏠 🔴 PENDIENTE
**Dependencia inferior:** Fase 8 (solo cuando todo lo demás funciona).

- [ ] Panel unificado: estado BingX + estado fondeo + estrategias + robots + portfolio + alertas
- [ ] Premium dark/glass (estilo existente)
- [ ] Servicios systemd 24/7 (strategyquantx, ultrarentable-api, ultrarentable-web)

**Criterio:** ✅ el usuario no técnico abre la web y ve TODO en una pantalla con 1 botón.

---

## 🛡️ REGLAS INQUEBRANTABLES
1. **REAL-ONLY:** nada de valores inventados; cada fase se cierra con ejecución real + tests.
2. **Sin Docker** (venv + systemd).
3. **Micro-live NUNCA automático:** requiere confirmación explícita del usuario.
4. **No mezclar FAST_APPROXIMATE con CANONICAL** en la UI.
5. **No bajar velas** para el flujo principal — SQX trae sus datos.
6. **Bottom-up:** cada capa se construye HACIA DENTRO y SOLO cuando su dependencia inferior está verificada.
7. **Fondeo = zona restringida**: niveles de permiso VER→CONFIGURAR→AUTORIZAR→ACTIVAR→EJECUTAR; nadie cambia las reglas alegremente.
8. **Navegación global permanente**: el usuario nunca pierde la capacidad de saltar entre módulos.

---

## 🔧 HALLAZGOS CLAVE (para no repetir)

| Tema | Hallazgo verificado |
|---|---|
| SQX MCP | ✅ Handshake + 6 tools + 7 proyectos; API proxy OK |
| Datos | ✅ SQX trae sus datos (BTCUSDT H1). NO bajar velas para generar |
| Parser SQX | ⚠️ `get_strategy_stats` offset = 2 (no len(vals)-len(cols)) |
| SQX código | ⚠️ SQX NO exporta código → candidatos quedan `SQX_CANDIDATE`, nunca CANONICAL sin 2º motor |
| BingX REST | ✅ F3 completo: signed POST/PUT/DELETE, VST, 16 tests |
| BingX VST | Entorno simulado gratis: open-api-vst.bingx.com, 100k VST |
| Fast engine | ✅ Desbloqueado con reglas de riesgo frescas (caducan 24h) |
| Prop firm MVP | FundedNext Rapid Pro (bots ✅, ~$150) o Bulenox trial 14d |
| Topstep | ❌ Prohíbe VPS/VPN (IP residencial) |
| TPT | ❌ Banea bots de terceros |
| Tests | ✅ 112 passed / 5 skipped (services/api/tests/) |
| Bug | /api/v1/prop-firms montado pero 404 (colisión de ruta `/`) |
| Bug | Rutas viejas pro/03-trading en backtests (trazabilidad) — corregir path en BD |
