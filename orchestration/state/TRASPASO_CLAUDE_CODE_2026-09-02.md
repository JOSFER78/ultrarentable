# TRASPASO — estado completo para seguir en Claude Code (2026-09-02, 18:40)

Orca se ha parado por orden de Emilio ("va terriblemente lento"). Este documento es la foto
completa: qué hay hecho, qué está a medias, qué queda, cómo arrancar cada pieza y qué reglas mandan.
Fuente de verdad del plan: `orchestration/state/plan_maestro.md` y `plan/bloques/Fxx_*.md`;
foto del ciclo: `orchestration/state/current_phase.md` (§3 bis = tabla de aterrizajes auditados).
Ventana de decisiones de Emilio: `orchestration/state/VENTANA_EMILIO.md` (issue #22).

## 0. Estado de las ramas y del repo

| Qué | Dónde |
| :--- | :--- |
| `main` (origin) | `c89b80b8f` + el commit de este traspaso; contiene TODO lo integrado hoy |
| Rama de trabajo del orquestador | `JOSFER78/orquesta-antigravity-max-10` (worktree `C:/Users/yo/orca/workspaces/ultrarentable/devilray`); `main` avanza por fast-forward desde ella |
| Checkout principal | `C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable` (rama `main`; `data/normalized` con 531 entradas; `node_modules` con 76) |
| Worktrees con trabajo SIN auditar (WIP commiteado en su rama) | `agy-B03` (rama `JOSFER78/agy-B03`, `435964850`), `agy-B20` (rama `agy-B20`, `79af47a16`), `agy-B22` (rama `agy-B22`, `97c2599e2`) |
| Worktrees ya integrados pendientes solo de retirar | `agy-B19`, `agy-B21` (sin junctions; `git worktree remove --force` desde el checkout principal) |
| Junctions vivas | ninguna en los worktrees que quedan (B03 tuvo `data/normalized` → la del checkout principal: comprobar con `Get-Item -Force | ? Attributes -match ReparsePoint` antes de borrar nada) |
| BD canónica del PC | `C:/Users/yo/.local/state/ultrarentable/ultrarentable.sqlite3` = instantánea del VPS de hoy (65,8 MB; 525 estrategias, 38.456 trials). La BD vacía anterior y la copia de la instantánea están en `cuarentena/bd_local_pc_20260902/` (fuera de git) |
| Push a main | autorizado; `ORQ_PUSH=1 git push origin main`; commits con `ORQ_COMMIT=1` (arnés en `C:/Users/yo/.orq-hooks`) |

## 1. Lo integrado hoy (ciclo 3, auditado por re-ejecución) — resumen

Ola A (A01-A12) completa (ver current_phase §3). Ola B: B02 (E1: 20/20 `sin_ventaja_bruta` ES 5m/15m →
D15), B05 (parser `.sqx`; solo 117 `.sqx` en el PC), B07 (`services/improvement`), B08 (`services/meta`),
B09 (catálogo prop firms v2 con `SourceRef`), B10 (`/prop-firms` sobre v2; `lib/prop-firms.ts` a
cuarentena), B11 (inventario datos PC+VPS; 165 datasets solo en VPS), B12 (vigía V0 solo lectura +
unit/timer systemd en seco), B13 (W4.2-bis), B14 (arnés v2: D16), B15 (higiene de agentes:
`scripts/orq/`), B16 (localhost: `scripts/orq/web_local.ps1`), B17 (`/estrategias` sobria, 566 líneas),
B18 (BD del VPS en el PC), B06 (SQX: PARCIAL; ver §4). Ola S: B19 (`agy_lanzar.sh` v2), B21
(`aceptar_agy.py` v3), B20 (código de `agy_cerrar.sh` integrado, PERO roto en uso real; ver §3).

Decisiones nuevas: D15 (familia `reversion` de ES es edge, no dato), D16 (bypass del arnés → arnés v2),
D17 (agentes agy sin MCP: vaciar `~/.gemini/config/mcp_config.json` y `~/.gemini/antigravity-ide/mcp_config.json`).

## 2. Herramientas que existen y cómo se usan (todas en `main`)

- **Localhost de ULTRARENTABLE** (mandato de Emilio: la web local, no una página del plan; todo para
  mejorar `/estrategias`): desde la raíz del repo (devilray o checkout principal):
  `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/web_local.ps1 -Arrancar` → API en
  `http://127.0.0.1:8100` y web de producción en `http://localhost:3100` (3000/8000 son un túnel `sshd`
  al VPS: no tocar). `-Estado`, `-Reconstruir`, `-Parar`. Doc: `orchestration/OPERACION_WEB_LOCAL.md`.
  **Ahora mismo está PARADO** (se paró con todo). Los procesos deben lanzarse desde un shell que no muera
  al terminar el comando (una consola persistente); si se lanzan desde un shell de fondo de Claude Code,
  mueren al cerrarse ese shell.
- **Arnés de aceptación**: `python scripts/aceptar_agy.py <ID> [--base <ref>] [--sin-comandos] [--informe] [--out x.json]`
  (v3: territorio multi-ruta y comodines, aceptación comando a comando, informe en
  `orchestration/results/auditorias/`). Contratos: `orchestration/agy/GO_<ID>.md` (plantilla
  `PLANTILLA_GO.md`); cierre del agente: `DONE_<ID>.md` e informe `orchestration/results/agy/<ID>.md`.
- **Higiene de agentes (solo si se vuelve a usar Orca/agy)**: `scripts/orq/mcp_vacio.ps1`, `agy_censo.ps1`,
  `agy_matar.ps1 -ProcesoId N`, `agy_limpiar.ps1 -Conservar <rutas>`, `agy_lanzar.sh <ID> "<título>" <spec>`
  (v2). `agy_cerrar.sh` (B20) está ROTO en uso real (§3). Doc: `orchestration/OPERACION_AGENTES.md`.
- **Gobernanza de recursos** (Windows, A03): `python -m services.ops.gobernanza_recursos estado|ejecutar --nombre X -- <cmd>`;
  un pesado a la vez; los pesados se lanzan desacoplados (`Start-Process`) para que sobrevivan al shell.
- Motor 5.18.0 (`services/engine_version.py`); registro de gates v1 (gate 10 = 40); regla #26 vigente.

## 3. Trabajo a medias (WIP guardado, sin auditar) — qué falta exactamente

| ID | Rama / commit WIP | Qué hay | Qué falta |
| :-- | :--- | :--- | :--- |
| **B20** `agy_cerrar.sh` CORRECCION_1 | `agy-B20` / `79af47a16` | El script integrado en main muere en el paso 4 (`$ErrorActionPreference`/`$wt` de PowerShell expandidos por bash con `set -u`) y su paso 3 (purga de "MCP huérfanos") **mató la web/API locales dos veces** (18:08 y 18:21). El agente empezó la corrección | Terminar: escapar/aislar TODOS los bloques PowerShell (heredoc `<<'PS'` a fichero temporal), paso 3 limitado a `agy.exe` del worktree y a comandos con `.gemini|mcp_serv|mcp-server|gbrain|tradingview-mcp|notebooklm-mcp|obsidian-mcp` (nunca uvicorn/next/node/python de la API/web), flag `--simular`, idempotencia, flag `--solo-junctions <ruta>` con test de punta a punta; luego cerrar de verdad B19/B20/B21 con él. Contrato: `orchestration/agy/GO_B20.md` §CORRECCION_1 |
| **B22** vigilante + plantilla | `agy-B22` / `97c2599e2` | `scripts/orq/agy_vigilar.sh`, `orchestration/agy/PLANTILLA_SPEC.txt`, informe y DONE escritos; el agente se quedó "esperando pytest" | Auditar con el arnés v3 y la ACEPTACIÓN de `GO_B22.md`; integrar si pasa |
| **B03** E2 (420 configs, 6 familias, ES 5m y 15m) | `JOSFER78/agy-B03` / `435964850` | La campaña 5m (PID 6564, ~80 min de CPU) fue **parada sin telemetría** al parar Orca; una campaña anterior también murió (13:58). Ninguna telemetría E2 escrita | Relanzar las dos campañas SECUENCIALES bajo gobernanza y desacopladas (ver `GO_B03.md` §CORRECCION_1 para el comando `Start-Process`), esperar horas, auditar la telemetría (`orchestration/results/telemetria/`, `cobertura_por_familia` con 6 familias, `truncado == False`) y escribir informe. Después **B04** (#24: refutador forense de E1/E2) |
| **S01** humo | `orchestration/agy/GO_S01.md` (sin lanzar) | Trabajo de humo cronometrado del bucle enviar→recibir→auditar→cerrar | Solo tiene sentido si se vuelve a Orca; en Claude Code no aplica |

## 4. Decisiones que esperan a Emilio (issue #22 = `VENTANA_EMILIO.md`)

1. Limpieza del VPS (parar `ultrarentable-discovery.service`, `sqx.service` y el cron `improve_cycle.sh`; instalar el vigía V0 de B12 con `deploy/vigia/INSTALAR.md`).
2. Licencia de StrategyQuant (Trial caduca 05-09-2026).
3. Firebase / `.env.local` de la web.
4. Pregunta 5.2 (ciclo 1).
5. **Carril SQX (§6)**: tres rondas de B06; la tercera fue real: build de 30 min, 19.924 candidatos, 0 aceptados bajo criterio 1.1, coherente con E1. APARCADO salvo que Emilio diga otra cosa. Vale: config B (`data/sqx_exports/config_B06_20260902.cfx`, fuera de git), tabla A→B, export ES 15m (83.377 barras).

## 5. Fases pendientes del plan (orden propuesto para Claude Code)

1. **Cerrar la ola S** (§3: B20 corrección, B22 auditoría). Si no se vuelve a Orca, lo único imprescindible es NO dejar `agy_cerrar.sh` roto en main sin aviso (ya lo dice `OPERACION_AGENTES.md`? No: añadir una nota o corregirlo).
2. **Arrancar el localhost** y comprobar `/estrategias` con los datos reales (525 estrategias; 5 certificadas vigentes; 184 datasets). Siguiente mejora de `/estrategias`: revisar sección por sección contra `docs/19_UI_STYLE_SPEC.md` y el mandato de Emilio (sobria, sin paneles ni colores); la versión anterior está en `cuarentena/web_estrategias_v1_20260902/`.
3. **E2 (B03) → B04 (forense)**: la lectura de E1 ("familia sin ventaja bruta") necesita E2 sobre el espacio completo y un refutador independiente antes de decidir si las familias de `arquetipos` están AGOTADAS (→ W3.4, diseño de familias nuevas) o no.
4. **FONDEO**: con E2/B04 cerrados, campaña TRADFI sobre los 184 datasets aprobados con el motor 5.18.0, censo criterio 1.1 (SELLADO: ≥200 trades OOS, PF OOS ≥1.25, OOS/IS ≥0.5, 11 gates, DSR+, persistencia por mitades), exámenes prop (F07) en paper/demo primero. META-FONDEO (`services/meta`, B08) sobre las certificadas. ULTRA siempre EN CONSTRUCCIÓN.
5. **VPS**: cuando Emilio autorice, limpieza + vigía V0.

## 6. Reglas que mandan (selladas)

REAL-ONLY / zero-mocks (evidencia en disco con SHA-256; `NO DATA` donde falte); criterio 1.1 intocable;
regla #26 (todo cambio de semántica del motor sube `CURRENT_ENGINE_VERSION`; LEGACY, nunca borrar);
nunca `rm` (todo a `cuarentena/` con `MANIFEST.sha256` + `MOTIVO.md`); telemetría persistida con
cobertura por familia (D2); paper/demo primero; carga de la máquina: un pesado a la vez vía gobernanza,
`nice`, web siempre en build de producción; commits temáticos con trailer de Claude; nunca árboles incoherentes.

## 7. Lo aprendido hoy sobre la orquestación (para no repetirlo)

- Orca + agy (Gemini 3.7 Flash): rápidos por llamada (<1 s la CLI; 17-75 s un despacho), pero
  el sistema completo salió caro: agentes que mueren (B03 ×2, B12), prompts que se quedan sin enviar,
  encuesta de la CLI que bloquea, informes con causas inventadas (B06 ×2), MCP que se cargan solos
  (18-20 procesos por agente hasta vaciar las dos configs), `worker-release` que no limpia el panel, y
  scripts de cierre que mataron el localhost. La regla de Emilio queda registrada: **primero un sistema
  estable y medido (enviar, recibir, auditar, corregir, cerrar), después muchos trabajos mini**, y el
  orquestador solo revisa, analiza, corrige y reenvía.
- En Claude Code no existe la separación orquestador/worker de Orca: quien siga puede ejecutar
  directamente, pero con las mismas reglas de evidencia (cada cifra sale de un comando y su salida cruda).
- Mediciones útiles: `next build` ~2 min; pytest de un fichero 20-50 s; `sqlite3 .backup` de 65 MB en el
  VPS + scp < 1 min; campaña E2 de 420 configs en ES 5m: horas (nunca terminó hoy).

## 8. Índice de ficheros clave

`orchestration/state/current_phase.md` · `plan_maestro.md` · `VENTANA_EMILIO.md` · `PLAN_ORCA_ANTIGRAVITY.md`
· `orchestration/agy/GO_*.md`, `DONE_*.md`, `PLANTILLA_GO.md` · `orchestration/results/agy/<ID>.md` ·
`orchestration/results/auditorias/` · `orchestration/OPERACION_AGENTES.md` · `orchestration/OPERACION_WEB_LOCAL.md`
· `orchestration/OPERACION_VPS.md` · `scripts/orq/` · `scripts/aceptar_agy.py` · `services/ops/gobernanza_recursos.py`
· `docs/19_UI_STYLE_SPEC.md` · GitHub: tablero #23, ventana #22, pendientes #16 (B03), #24 (B04), #35 (B20), #37 (B22).
