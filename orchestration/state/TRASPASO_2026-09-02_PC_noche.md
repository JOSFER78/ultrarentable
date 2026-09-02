# TRASPASO — sesión Claude Code en el PC (orquestador), 2026-09-02 noche (~20:10 UTC)

Sucede a `TRASPASO_2026-09-02_VPS.md` (que sigue valiendo para la operación del VPS y la web) y a
`TRASPASO_CLAUDE_CODE_2026-09-02.md` (detalle del PC). Léelos en ese orden cuando necesites el detalle.
Este documento cuenta lo hecho esta noche, lo que queda y cómo seguir.

---

## 0. Lo primero

1. `git fetch origin main && git log --oneline HEAD..origin/main`. **Dos sesiones de Claude Code trabajan
   sobre el mismo checkout de `main` en el PC** (esta, `ultrarentablepc-ed`, y `ultrarentablepc-30`); cada
   una commitea con `ORQ_COMMIT=1` y publica con `ORQ_PUSH=1` (arnés en `C:/Users/yo/.orq-hooks`; sin esas
   variables el commit y el push se bloquean). Antes de commitear: `git pull --ff-only origin main`.
2. Reparto de ficheros acordado por mensaje: esta sesión = `apps/web/app/page.tsx`,
   `apps/web/app/estrategias/**`, `apps/web/context/AuthContext.tsx`, `apps/web/lib/firebase.ts`,
   `services/`, `orchestration/`. La otra = resto de `apps/web/app/*`, `apps/web/components/`,
   `apps/web/lib/api.ts`, `apps/web/lib/status-map.ts`. Su web local: API `:8100`, web de producción `:3100`.
3. Inventario del VPS (`ssh oracle-vps`): `uptime; free -h; .venv/bin/python -m services.ops.gobernanza_recursos estado`.
   Ver §4: esta noche la máquina estaba saturada por herramientas de Emilio ajenas al proyecto.

---

## 1. Hecho esta noche (todo en `main`)

| Commit | Qué |
| :--- | :--- |
| `04bcc9427` | Telemetría de E2 15m y de la re-ejecución de determinismo (commiteado desde el VPS) |
| `c0f800e56` | WIP de Firebase recuperado del PC (lazyProxy con prototipo real; AuthContext con getters). En el VPS la misma edición estaba con la codificación rota (`??` por acentos, CRLF) y baked en el build de las 18:35; copia en `cuarentena/web_wip_mojibake_vps_2026-09-02/` (VPS, fuera de git) |
| `6e664c091` | La API publica `current_engine_version` en `/api/v1/discovery/status` (la web marcaba "API NO DISPONIBLE" y "MOTOR: NO DISPONIBLE" por ese campo inexistente) + tarjetas honestas en la portada |
| `af28646ef` | **B03 y B04 cerrados** (informes, DONE, script `B04_leer_embudos.py`), plan F03 actualizado, D1 levantada, VENTANA_EMILIO §0 |

- **E2 (B03)**: 840/840 configuraciones muertas en IS (ES 5m y 15m, 6 familias, motor 5.18.0). AGOTADA en
  ambas celdas y en las 6 familias por las reglas preselladas, con matiz en SESSION_MOMENTUM 5m (20/72 con PF
  bruto ≥ 1,05 hundidas por el coste). La hipótesis "bajar a 15m ayuda a SESSION_MOMENTUM" queda refutada.
- **B04**: `D15 CONFIRMADA`; 0 anomalías; determinismo 3/3 PC vs VPS.
- **Hallazgo verificado en código**: el motor cobra a MES la comisión de ES (2,50 USD/lado en vez de 0,60):
  `event_backtest_engine.py:296` y `:972`, `instrument_registry.py:80`, `mine.py:1039`. Además
  `max_leverage_ceiling=1.0` degenera `risk_pct` (157/420 y 182/420 configs repetidas). **Issue #38** (motor
  5.19.0 + E2c) es el siguiente paso de FONDEO; W3.4 espera a E2c.
- **VPS**: API reiniciada dos veces (19:30 y 19:34 UTC) y ahora corre HEAD (`6e664c091`+); antes llevaba
  desde el 31-08 con código 141 commits atrás. El import de la API tarda ~114 s: cada reinicio son 2 minutos
  de corte. La web del VPS (`:3005` systemd y `:3000` del túnel) sigue con el build de las 18:35 (mojibake
  incluido): **pendiente de reconstruir** (ver §3).
- **Censo criterio 1.1 (en seco, VPS, 19:41 UTC)**: 728 candidatas, 0 supervivientes, 5 reclasificables
  (las 5 `APPROVED_CURRENT_ENGINE`: ULTRA, motor 5.13.0/5.16.0, 25-68 ops OOS). Aplicarlo escribe en la
  base canónica y el guardián de esta sesión lo bloqueó: pendiente de Emilio (VENTANA §0.1).
- **Unidad de `net_profit_oos`**: para esas 5 es una FRACCIÓN del capital (NQ: 123,96 USD sobre 1.000 =
  0,124 → 0,13), no USD. `candidates_router.py:118` lo suma como USD y la web lo etiquetaba "USD". Avisado a
  la otra sesión (dueña de ese router); la nueva `/estrategias` no imprime esa cifra como USD.
- **Memoria de doctrina de producto** (mandato de Emilio, 02-09): la web solo enseña lo que funciona: páginas
  implementadas y estrategias que pasan el criterio 1.1 con motor vigente; las fallidas se quedan en el
  backend; los 4 bloques M1-M4 explicados en llano; nada de paneles técnicos en la vista principal.

## 2. En vuelo al escribir esto

- **Workflow `wfug8t0qo` (rediseño web)**: agente E reescribe `apps/web/app/estrategias/**` (página maestra
  con solo estrategias válidas, 4 subpáginas `generacion/mejora/valoracion/meta`, componentes en
  `_bloques/`, ruta `api-telemetria/route.ts` que lee `orchestration/results/telemetria/`); agente D
  reescribe la portada. Después dos verificadores (tsc, rutas, prohibiciones REAL-ONLY, copia en llano) con
  una ronda de corrección. Sin `next build` (el `.next` del PC lo sirve la otra sesión en `:3100`).
- Al terminar: revisar con `tsc`, leer las páginas, commitear (`ORQ_COMMIT=1`), publicar, y **desplegar** (§3).

## 3. Cómo desplegar la web (PC y VPS)

1. PC: avisar a `ultrarentablepc-30` (sirve `apps/web/.next` en `:3100`); reconstruir con el mecanismo
   documentado `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/web_local.ps1 -Reconstruir`
   (o parar `:3100`, `next build`, arrancar). Verificar `grep -rl "traderbot-josfer" apps/web/.next/static`.
2. VPS (mientras la gobernanza no admita un build allí: swap < 256 MB libres): copiar el `.next` del PC sin
   `cache/` (≈4 MB): `tar -C apps/web -czf - --exclude=cache .next | ssh oracle-vps 'cd ".../01 Ultrarentable/apps/web" && mv .next .next.prev_$(date -u +%H%M) && tar -xzf -'`;
   antes `systemctl --user stop ultrarentable-web.service` y matar el `next start -p 3000`; después
   `systemctl --user start ultrarentable-web.service` y relanzar `:3000` con `setsid nohup` (comando en
   `TRASPASO_2026-09-02_VPS.md` §4). Comprobar `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3005/` y
   que el bundle no contiene `Configuraci??n`. Si falla, restaurar `.next.prev_*`.
3. `git pull --ff-only` en el VPS antes de copiar, para que `apps/web` en disco coincida con el build.

## 4. Estado de la máquina del VPS (19:36-19:38 UTC) y lo que espera a Emilio

Carga 13 sobre 4 núcleos, swap 63 MB libres de 4 GB. Consumidores: `hermes serve`/`tirith`/`fetch_cloud.py`
(agente Hermes), Chromium de Playwright bajo `node dist/api.js`, Brave headless con depuración remota,
`cleanlinux_gui.py`/`cleanlinux-daemon.py`, cuatro `agy` zombis de `antigravity_bridge.py`. Del proyecto:
`sqcli` (~4 GB), `ultrarentable-discovery.service` (estrangulado por su cgroup: 6,3 → 6,7 millones de
frenazos en 15 min; lo recicla `RuntimeMaxSec=12h` a ~01:50 UTC), backfill de Dukascopy (I/O). La API tiene
dos daemons internos (`ContinuousResearchDaemon`, `AutonomousMetaDaemon`) que fallan en bucle cada 30-60 s
(`RiskModel base_risk_pct=0.015 < 0.1`; `STALE_CANDIDATE`): ruido en el journal y CPU sin producto; no se
ha tocado. Decisiones de Emilio: `VENTANA_EMILIO.md` §0 (censo, saturación, dos sesiones, identidad git) y
§1-§4 (limpieza con sudo, nginx, licencia SQX que caduca el 05-09).

## 5. Qué queda, en orden

1. Terminar y desplegar el rediseño web (§2-§3); pedir a la otra sesión la poda del menú lateral.
2. Con permiso de Emilio: `censo_f01.py --aplicar` en el VPS (deja 0 certificadas, que es lo real).
3. **Issue #38**: motor 5.19.0 (comisión por símbolo desde el registro) + E2c SESSION_MOMENTUM ES 5m bajo
   gobernanza. Solo después, W3.4.
4. FONDEO TRADFI sobre los 184 datasets aprobados y censo tras cada tanda; META-FONDEO cuando haya ≥ 2.
5. Corregir la unidad de `net_profit_oos` en `candidates_router.py` (otra sesión) y los daemons de la API.

## 6. Reglas que mandan (sin cambios)

REAL-ONLY / zero-mocks; criterio 1.1 sellado; regla #26; nunca `rm` (cuarentena con SHA-256); un pesado a la
vez vía `gobernanza_recursos`; web siempre en build de producción; máximo 2 agentes en el PC de Emilio;
nada se da por sentado sin comprobarlo; comunicación con Emilio breve y en llano.
