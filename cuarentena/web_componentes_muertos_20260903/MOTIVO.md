# MOTIVO — dos componentes muertos de `apps/web/components` (2026-09-03)

Retirados durante la poda del menú lateral que pidió Emilio ("hay páginas antiguas mezcladas
con nuevas, deja solo lo nuevo y funcional"). Nunca se usó `rm`: los dos ficheros viven aquí
íntegros, con su ruta original preservada y su SHA-256 en `MANIFEST.sha256`, comprobado
**después** del movimiento (`sha256sum -c` → OK en los dos).

## Verificación previa al movimiento

Medición sobre todo `apps/web` (excluido `node_modules`), incluida la parte del árbol de
trabajo que aún no está commiteada, y repetida justo antes de mover porque un tercer agente
estaba editando ficheros en paralelo:

```
grep -rn "EstrategiasHeaderNav\|CANONICAL_PHASES" --include=*.tsx --include=*.ts .   -> 0 fuera de su propio fichero
grep -rn "RealOnlyGate"                            --include=*.tsx --include=*.ts .   -> 0 fuera de su propio fichero
```

Cero importadores en ambos casos. Ninguna página deja de compilar por esto.

## Por qué se retira cada uno

| Fichero | Motivo |
| :--- | :--- |
| `components/EstrategiasHeaderNav.tsx` | Barra de "fases cuantitativas" de la versión anterior de `/estrategias`. La página nueva usa `app/estrategias/_bloques/NavBloques.tsx` en su lugar. Además enlazaba a `/research` y `/portfolio`, dos de las 14 rutas que siguen en `cuarentena/web_poda_20260901` y que por tanto no existen: era una puerta a un 404. |
| `components/system/RealOnlyGate.tsx` | Cartel "REAL_ONLY_BLOCKED" del diseño anterior. Contenía el **único `href` roto de toda la web**: `/data` (línea 37), otra ruta en cuarentena. Usaba además clases y variables CSS del tema viejo (`badge-danger`, `--text-muted`, `--text-secondary`) que ya no existen en la paleta gris de `docs/19_UI_STYLE_SPEC.md`, así que ni siquiera se habría pintado bien. Su texto ofrecía "ver datos públicos reales de BingX", fuera de la misión FONDEO. |

Tras el movimiento, `grep` de `href="/(research|portfolio|data|...)"` sobre `app/` y
`components/` no encuentra ya **ningún** enlace a rutas en cuarentena.

## Lo que NO se tocó

Hay otros cuatro componentes con cero importadores medidos el mismo día —
`components/EvidenceLink.tsx`, `components/strategy/CertifiedStrategiesTable.tsx`,
`components/system/LocalModuleConsole.tsx` y `components/system/MetricWithTooltip.tsx`—.
No se mueven: el mandato de Emilio era sobre el menú, no una purga de componentes, y a
diferencia de los dos de arriba ninguno apunta a rutas inexistentes ni usa el tema viejo.
Quedan anotados aquí para que la próxima sesión decida con el dato ya medido, no de memoria.
