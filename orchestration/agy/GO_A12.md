# GO_A12 — W5.2: `/estrategias` como página maestra M1-M4 + home honesta (estética docs/19)

## Identidad
- ID: A12 · Ola: A · Rama/worktree: JOSFER78/agy-A12 (Orca; la rama real lleva el prefijo del usuario) · Timebox: 45 min (si no llega: PARCIAL con la página maestra completa y la home sin tocar; nunca a medias las dos)
- Variables ya puestas en tu terminal: AGY_AGENT=A12.
- Node: `node_modules/` y `apps/web/node_modules/` de tu worktree son junctions al worktree del orquestador. NO ejecutes `npm install`/`npm ci`. Comandos desde `apps/web/`.

## OBJETIVO (una frase verificable)
`apps/web/app/estrategias/page.tsx` reescrita como página MAESTRA con cuatro secciones (Generación · Mejora · Valoración Fondeo · Meta) según el diseño sellado, los estados y reglas de `docs/18` y los tokens de `docs/19`; `apps/web/app/page.tsx` como panel FONDEO honesto; "Ultra — EN CONSTRUCCIÓN" visible al final del Sidebar; cero colores fuera de tokens en los ficheros tocados; `tsc` sin errores y `next build` verde.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- apps/web/app/estrategias/ (page.tsx y componentes nuevos de la página; `verificacion.ts` se CONSERVA y se usa)
- apps/web/app/page.tsx
- apps/web/components/ (componentes nuevos de la página maestra; `components/layout/Sidebar.tsx` SOLO para la entrada "Ultra — EN CONSTRUCCIÓN" si no existe ya)
- apps/web/lib/ (SOLO ficheros nuevos de tipos/helpers; `lib/api.ts` y `verificacion.ts` NO se reescriben; si necesitas un endpoint nuevo en `lib/api.ts`, añade funciones, no cambies las existentes)
- apps/web/app/globals.css (SOLO añadir las variables CSS de docs/19 §2 si no existen)
- orchestration/results/agy/A12.md (nuevo) · orchestration/agy/DONE_A12.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/reviews/diseno_pagina_estrategias_2026-09-01.md ENTERO (el diseño sellado: secciones, tablas, estados).
- docs/18_STRATEGIES_PAGE_SPEC.md (identidad hash/dataset_hash/procedencia; estados EXTRACTED → STRUCTURALLY_VERIFIED → BACKTEST_VERIFIED → CERTIFIED_CURRENT; `NO EVIDENCE` nunca 0; sin venue/capital).
- docs/19_UI_STYLE_SPEC.md (tokens §2, reglas por componente §3, checklist §5).
- orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md, sección "La web refleja los módulos".
- apps/web/app/estrategias/page.tsx (374 líneas, la actual), README_STRATEGIES_PAGE.md, verificacion.ts, SQXToolsPanel.tsx (se absorbe en la sección Generación); apps/web/lib/api.ts (endpoints reales y fetch fail-closed); apps/web/components/layout/Sidebar.tsx, Header.tsx, AppShell.tsx.

## PASOS (numerados, cortos, en orden)
1. Comprobar: `git status --porcelain` vacío · `ls node_modules/.bin/next apps/web/node_modules 2>&1 | head -2` (junctions vivas) · desde `apps/web`: `npx tsc --noEmit -p . ; echo rc=$?` (baseline; pega el resultado).
2. Inventario de datos reales disponibles: lee `lib/api.ts` y lista los endpoints que sirven candidatos/estrategias/gates/motor. Todo lo que la página muestre viene de ahí; lo que no exista se muestra como `NO EVIDENCE` en `--text-3`, JAMÁS un 0, un guion o un dato inventado.
3. Tokens: si `globals.css` no tiene `--bg`, `--surface-1/2/3`, `--border`, `--text-1/2/3`, `--profit`, `--loss` (+ `-dim`), añádelos con los valores EXACTOS de docs/19 §2.
4. Página maestra: línea de estado honesta arriba ("Certificadas: N · Motor <versión real de la API> · Última campaña: <fecha real o NO EVIDENCE>"); secciones Generación (absorbe el panel SQX existente), Mejora, Valoración Fondeo, Meta; tabla de catálogo con estados como texto plano (verde solo CERTIFIED_CURRENT; rojo solo REJECTED_*/BUSTED; resto gris), PnL/PF coloreados por signo, todo lo demás gris; identidad (hash, dataset_hash, procedencia) en monoespaciada. Sin animaciones, sin badges multicolor.
5. Home `app/page.tsx`: panel FONDEO honesto con los mismos tokens (marcador real, motor real, enlaces a las secciones); ULTRA presente como bloque atenuado "EN CONSTRUCCIÓN", nunca borrado.
6. Sidebar: si no existe, entrada final atenuada "Ultra — EN CONSTRUCCIÓN" (`--text-3`) que enlaza a `/ultra`.
7. Verificación de estilo (checklist docs/19 §5): `grep -nE "#[0-9a-fA-F]{3,8}\b|\b(blue|amber|purple|yellow|indigo|emerald|rose|sky|violet|orange|teal|cyan|lime|pink)-" <cada fichero tocado excepto globals.css>` ⇒ 0 líneas. Badge de versión: nada de `5.4.0` literal.
8. `npx tsc --noEmit -p .` desde `apps/web` ⇒ rc=0. Luego PESADO: `orca orchestration ask --question "A12 pide admisión para: next build en apps/web" --json`; con el OK, `npx next build` ⇒ rc=0 (pega las últimas 30 líneas).
9. Informe con salida cruda; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
cd apps/web && npx tsc --noEmit -p . ; echo "rc=$?"; cd ../..                      # esperado: rc=0
git diff --name-only -- apps/web | grep -v globals.css | xargs grep -nE "#[0-9a-fA-F]{3,8}\b|\b(blue|amber|purple|yellow|indigo|emerald|rose|sky|violet|orange|teal|cyan|lime|pink)-" | wc -l   # esperado: 0
git ls-files --others --exclude-standard -- apps/web | xargs grep -nE "#[0-9a-fA-F]{3,8}\b|\b(blue|amber|purple|yellow|indigo|emerald|rose|sky|violet|orange|teal|cyan|lime|pink)-" | wc -l   # esperado: 0
grep -rn "5\.4\.0" apps/web/app/estrategias apps/web/app/page.tsx | wc -l          # esperado: 0
grep -rln "EN CONSTRUCCI" apps/web/components/layout/Sidebar.tsx apps/web/app/page.tsx | wc -l   # esperado: 2
grep -c "NO EVIDENCE" apps/web/app/estrategias/page.tsx                            # esperado: >= 1
grep -cE "Generaci|Mejora|Valoraci|Meta" apps/web/app/estrategias/page.tsx         # esperado: >= 4
git diff --name-only   # ⊆ TERRITORIO (más GO_A12.md si el ORQ añadió CORRECCION_n)
# next build: lo re-ejecuta el ORQ en su worktree tras integrar (pesado); tú lo ejecutas UNA vez con admisión
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO (solo web) · ¿Ejecuta algo pesado? SÍ: `next build`, una vez, tras `orca orchestration ask`. `tsc --noEmit` permitido.
- Fail-closed en datos: `lib/api.ts` ya falla explícitamente; conserva ese comportamiento y muestra el error literal en una franja con borde `--loss`.
- No tocar `.env.local`, `firebase.ts`, ni rutas fuera del territorio (la poda W5.1 ya está hecha; `/ultra` se conserva).
- Si algún endpoint no existe para una sección, la sección se pinta con `NO EVIDENCE` y lo anotas como HALLAZGO: no inventes datos ni "mock data".

## PROHIBIDO (lista negra, sin excepciones)
git add/commit/push/reset/checkout/merge/stash · rm · datos de ejemplo/mock/fixtures inventados en la UI · colores fuera de tokens · escribir fuera del TERRITORIO · `npm install`/`npm ci`/cambiar package.json · `next build` sin admisión · inventar una salida que no se ejecutó · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit).
2. orchestration/results/agy/A12.md: endpoints usados por sección, comandos y salida CRUDA (tsc, greps, build), lo que quedó `NO EVIDENCE` y por qué, hallazgos, veredicto propio.
3. orchestration/agy/DONE_A12.md (plantilla: orchestration/agy/PLANTILLA_DONE.md).
4. Cierre: orca orchestration send --type worker_done --subject "A12 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
