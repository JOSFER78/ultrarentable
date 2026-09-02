# GO_B17 — `/estrategias` sobria: la página maestra M1-M4 al estilo terminal de Orca / Claude Code (sin paneles, sin color, sin adornos)

## Identidad
- ID: B17 · Ola: B · Rama/worktree: JOSFER78/agy-B17 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B17. Node: `node_modules/` y `apps/web/node_modules/` de tu worktree son junctions al worktree del orquestador; NO ejecutes `npm install`/`npm ci`. Comandos desde `apps/web/`.

## OBJETIVO (una frase verificable)
`apps/web/app/estrategias/page.tsx` (hoy 1.909 líneas, inline styles, tarjetas y rejillas) queda reescrita como una página **densa, monocroma y sin adornos**, con la estética de una terminal de Orca / Claude Code (mandato de Emilio, 2026-09-02: "sin paneles enormes ni colorines ni nada de hecho con IA"): fuente del sistema a 13-14 px, una sola columna de ≤ 1100 px, **una línea de estado honesta arriba** ("Certificadas: N · Motor <versión de la API> · Última campaña: <fecha o NO DATA>"), y las cuatro secciones M1-M4 (Generación · Mejora · Valoración · Meta) como **encabezado + tabla o lista plana**, cada dato real del endpoint que ya usa la página (mismos endpoints de `lib/api.ts` que hoy, ni uno nuevo) o `NO DATA`/`NO EVIDENCE` en `--text-3`; ULTRA aparece como **EN CONSTRUCCIÓN** en texto gris; cero tarjetas, cero `borderRadius` > 4 px, cero `boxShadow`, cero gradientes, cero emojis/iconos, cero animaciones, cero colores salvo los tokens de docs/19 (verde/rojo solo en P&L real); ≤ 700 líneas; `tsc` limpio.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- apps/web/app/estrategias/ (page.tsx, SQXToolsPanel.tsx, verificacion.ts, README_STRATEGIES_PAGE.md; puedes reducir o retirar componentes: lo retirado se COPIA a `cuarentena/web_estrategias_v1_<fecha>/` con `MANIFEST.sha256` y `MOTIVO.md`, sin `git mv`)
- cuarentena/web_estrategias_v1_<fecha>/ (nuevo)
- orchestration/results/agy/B17.md (nuevo) · orchestration/agy/DONE_B17.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- apps/web/app/estrategias/page.tsx (lo que hay: inventario de endpoints y secciones; conserva TODOS los endpoints que ya consume y su manejo fail-closed).
- orchestration/results/agy/A12.md §2 (inventario endpoint → sección) y orchestration/reviews/diseno_pagina_estrategias_2026-09-01.md (qué pregunta responde cada sección).
- docs/19_UI_STYLE_SPEC.md (tokens y §5 verificación) y orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md (M1-M4).
- apps/web/app/prop-firms/page.tsx (B10: ejemplo ya aceptado de tabla sobria con `NO EVIDENCE`).
- Referencia visual: la interfaz de Orca y de Claude Code que Emilio usa a diario: texto, tablas, líneas de 1 px, gris; nada más.

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío; `npx tsc --noEmit -p .` (baseline rc); inventario de endpoints usados hoy (`grep -n "from \"@/lib/api\"\|get[A-Z][A-Za-z]*(" page.tsx`) y pégalo: la nueva página debe usar exactamente esos.
2. Copia a cuarentena la page.tsx actual (+ SQXToolsPanel.tsx si lo retiras) con MANIFEST y MOTIVO.
3. Reescribe page.tsx: cabecera = título en texto + línea de estado; M1 Generación = tabla (campaña/embudo, familia, configs, supervivientes, fecha) o `NO DATA`; M2 Mejora = tabla o lista; M3 Valoración = tabla de gates 1-11 por estrategia certificada/candidata con `PASA/FALLA/NO DATA`; M4 Meta = `NO DATA` + frase honesta si no hay portafolio; pie con motor y hora de la API. Un solo componente de tabla propio de ≤ 40 líneas; sin librerías nuevas.
4. `npx tsc --noEmit -p .` ⇒ rc=0; greps de aceptación ⇒ 0. PESADO: `next build` solo con `orca orchestration ask`; si no hay hueco, el ORQ lo ejecuta tras integrar.
5. Informe: inventario de endpoints antes/después (idéntico), líneas antes/después, greps; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
cd apps/web && npx tsc --noEmit -p . ; echo "rc=$?"; cd ../..                                        # esperado: rc=0
wc -l apps/web/app/estrategias/page.tsx | awk '{print ($1<=700)?"OK "$1:"DEMASIADO "$1}'              # esperado: OK N
grep -cE "boxShadow|gradient|animation|borderRadius: *\"?(6|8|10|12|16|20|24)" apps/web/app/estrategias/page.tsx || true   # esperado: 0
grep -rnE "#[0-9a-fA-F]{3,8}\b|\b(blue|amber|purple|yellow|indigo|emerald|rose|sky|violet|orange|teal|cyan|lime|pink)-" apps/web/app/estrategias | wc -l   # esperado: 0
grep -cP "[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]" apps/web/app/estrategias/page.tsx || true          # esperado: 0 (sin emojis)
grep -c "EN CONSTRUCCI" apps/web/app/estrategias/page.tsx                                             # esperado: >= 1
grep -cE "NO DATA|NO EVIDENCE" apps/web/app/estrategias/page.tsx                                      # esperado: >= 4
grep -c "<table" apps/web/app/estrategias/page.tsx                                                    # esperado: >= 3 (o el componente de tabla usado >= 3 veces)
ls cuarentena/web_estrategias_v1_*/MANIFEST.sha256 && sha256sum -c cuarentena/web_estrategias_v1_*/MANIFEST.sha256   # OK
git diff --name-only   # ⊆ TERRITORIO
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? `next build` solo con admisión. `tsc` permitido.
- REAL-ONLY: ningún dato inventado ni de ejemplo; los endpoints son los mismos que hoy; lo que no llega es `NO DATA`.
- No cambies `lib/api.ts` ni `next.config` (B16 los toca en paralelo): si necesitas algo de ahí, HALLAZGO.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura (incluido `git mv`) · rm · `npm install` · librerías nuevas · datos de ejemplo · colores fuera de tokens · tarjetas/paneles/gradientes/sombras/emojis · escribir fuera del TERRITORIO · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B17.md. 3. orchestration/agy/DONE_B17.md.
4. Cierre: orca orchestration send --type worker_done --subject "B17 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
