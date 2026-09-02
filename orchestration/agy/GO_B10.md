# GO_B10 — W5.8 (D7): `/prop-firms` consume el catálogo v2 con `SourceRef`; `lib/prop-firms.ts` a cuarentena

## Identidad
- ID: B10 · Ola: B · Rama/worktree: JOSFER78/agy-B10 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B10. Node: `node_modules/` y `apps/web/node_modules/` de tu worktree son junctions al worktree del orquestador; NO ejecutes `npm install`/`npm ci`. Comandos desde `apps/web/`.
- Python (para la API en local, si la necesitas): `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
La página `apps/web/app/prop-firms/` muestra el catálogo v2 servido por `GET /api/v1/prop-firms/v2` (B09): una fila por firma y, por cada dato de riesgo/economía, el valor y su `SourceRef` (confidence + url + fecha) o `NO EVIDENCE` en `--text-3` cuando es `None`/unverified; cero cupones/afiliados/enlaces comerciales (D7); `apps/web/lib/prop-firms.ts` (4.307 LOC de catálogo hardcodeado en cliente) deja de importarse y se aparca en `cuarentena/web_prop_firms_ts_<fecha>/` con `MANIFEST.sha256` y `MOTIVO.md`; estética docs/19 (grises; verde/rojo solo PnL, que aquí no hay); `tsc` limpio.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- apps/web/app/prop-firms/ (existente; reescritura)
- apps/web/lib/prop-firms.ts (SOLO para moverlo a cuarentena; `git mv` PROHIBIDO: copia + MANIFEST y deja el original tal cual hasta que el ORQ lo retire en la integración; el import se elimina de la página)
- cuarentena/web_prop_firms_ts_<fecha>/ (nuevo: copia del .ts + MANIFEST.sha256 + MOTIVO.md)
- apps/web/lib/ (SOLO tipos/helpers nuevos: `propFirmsV2.ts` con el fetch tipado fail-closed, siguiendo el patrón de `lib/api.ts`)
- orchestration/results/agy/B10.md (nuevo) · orchestration/agy/DONE_B10.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- services/fondeo/catalogo_firmas_v2.py y el handler `GET /api/v1/prop-firms/v2` en services/api/app/api/providers_router.py (B09): forma exacta del JSON.
- orchestration/results/M3_plan_catalogo_firmas.md §1.3-1.4 y current_phase.md D6/D7.
- docs/19_UI_STYLE_SPEC.md (tokens y reglas; `NO EVIDENCE` nunca 0).
- apps/web/app/prop-firms/ (lo que hay hoy) y `grep -rn "lib/prop-firms" apps/web --include=*.ts --include=*.tsx -l --exclude-dir=node_modules` (quién importa el catálogo viejo: TODOS esos imports deben desaparecer o apuntar al v2).
- apps/web/lib/api.ts (patrón de fetch fail-closed y base URL de la API).

## PASOS (numerados, cortos, en orden)
1. Comprobar: `git status --porcelain` vacío; desde `apps/web`: `npx tsc --noEmit -p . ; echo rc=$?` (baseline). Lista los importadores de `lib/prop-firms`.
2. `lib/propFirmsV2.ts`: tipos `SourceRef`, `FirmaV2`, `getPropFirmsV2()` (fail-closed: error explícito, sin datos de relleno).
3. Página: tabla firma × campo con valor + fuente (confidence en gris, url como enlace gris, fecha); `NO EVIDENCE` donde no hay dato; línea de estado arriba ("Catálogo v2 · N firmas · fuentes verificadas: X de Y datos"); banner gris "cupones y afiliados retirados hasta re-verificación (D7)". Nada de amarillos/azules.
4. Cuarentena: `mkdir cuarentena/web_prop_firms_ts_<YYYYMMDD>`; copia `apps/web/lib/prop-firms.ts` allí; `sha256sum` a `MANIFEST.sha256`; `MOTIVO.md` (D7, 4.307 LOC de datos comerciales sin fuente en cliente). Elimina TODOS los imports de `lib/prop-firms` en apps/web (si otro componente lo usa, migra ese uso a v2 o a `NO EVIDENCE`; lista los ficheros tocados fuera de `app/prop-firms/` como HALLAZGO si están fuera de tu territorio y NO los toques: en ese caso deja el import y repórtalo).
5. `npx tsc --noEmit -p .` ⇒ rc=0; greps de estilo (docs/19 §5) sobre los ficheros tocados ⇒ 0. PESADO: `next build` solo con `orca orchestration ask`; si no hay hueco, el ORQ lo ejecuta tras integrar.
6. Informe con la tabla firma×campo×confidence, los importadores eliminados y los hallazgos; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
cd apps/web && npx tsc --noEmit -p . ; echo "rc=$?"; cd ../..                                        # esperado: rc=0
grep -rn "lib/prop-firms'" apps/web --include=*.ts --include=*.tsx --exclude-dir=node_modules | grep -v "propFirmsV2" | wc -l   # esperado: 0 (o los HALLAZGOS listados, fuera de territorio)
grep -c "prop-firms/v2" apps/web/lib/propFirmsV2.ts                                                   # esperado: >= 1
grep -rnE "#[0-9a-fA-F]{3,8}\b|\b(blue|amber|purple|yellow|indigo|emerald|rose|sky|violet|orange|teal|cyan|lime|pink)-" apps/web/app/prop-firms apps/web/lib/propFirmsV2.ts | wc -l   # esperado: 0
grep -c "NO EVIDENCE" apps/web/app/prop-firms/page.tsx                                                # esperado: >= 1
grep -rniE "cup[oó]n|afiliad|affiliate|discount" apps/web/app/prop-firms | wc -l                       # esperado: 0 (salvo el banner que dice que se retiraron)
ls cuarentena/web_prop_firms_ts_*/MANIFEST.sha256 cuarentena/web_prop_firms_ts_*/MOTIVO.md            # existen
sha256sum -c cuarentena/web_prop_firms_ts_*/MANIFEST.sha256                                            # OK
git diff --name-only   # ⊆ TERRITORIO (más GO_B10.md si el ORQ añadió CORRECCION_n)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? `next build` solo con admisión. `tsc` permitido.
- `.env.local`/Firebase NO se tocan aquí (dependen de Emilio, issue #22 punto 3).
- REAL-ONLY: ningún dato de firma inventado; lo que el endpoint no trae es `NO EVIDENCE`.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura (incluido `git mv`) · rm · `npm install` · datos de ejemplo · colores fuera de tokens · escribir fuera del TERRITORIO · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B10.md. 3. orchestration/agy/DONE_B10.md.
4. Cierre: orca orchestration send --type worker_done --subject "B10 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
