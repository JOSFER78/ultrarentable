# 03_ESTRUCTURA_DOCS.md — Estructura documental definitiva del proyecto de estrategias Ultra_Matrix
Fecha: 2026-08-29. Carpeta raíz: `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/`
Principio rector: **un dato = un sitio** (cada hecho vive en un único archivo; el resto enlaza). Todo lo que hoy está en /tmp se migra a ubicación permanente. Sin duplicación: README = mapa, docs = verdad, evidencia/ = informes con fecha.

---

## 1. Árbol de carpetas y archivos (dentro de `01 Ultrarentable/estrategias_um/`)

Se crea un subdirectorio dedicado al proyecto de estrategias para NO mezclar con los docs del repo de apps que ya puebla la raíz (ARCHITECTURE.md, ESTADO.md, GEMINI.md, etc. pertenecen a la aplicación web, no al pipeline SQX).

```
01 Ultrarentable/
└── estrategias_um/                     ← RAÍZ del proyecto de estrategias SQX Ultra_Matrix
    ├── README.md                       ← Visión + mapa de toda la documentación (índice vivo)
    ├── docs/
    │   ├── 00_MASTER_IDEAS_Y_PLAN.md   ← (migrar) doc maestro ya existente en docs/ de la raíz
    │   ├── PLAN_PIPELINE.md            ← (migrar de /tmp/um_restruct/02_PLAN_PIPELINE.md)
    │   ├── ESTADO.md                   ← (migrar de /tmp/um_restruct/01_ESTADO.md) estado vivo
    │   ├── HECHOS_Y_DECISIONES.md      ← hechos verificados + decisiones tomadas (síntesis)
    │   ├── DECISIONES_LOG.md           ← registro APPEND-ONLY con fecha (nunca editar hacia atrás)
    │   ├── RUNBOOK_OPERACION.md        ← comandos API verificados, fases con candado, stop/copy/start
    │   ├── CONFIG_DOORS.md             ← (migrar de /tmp/um_doors/config_doors.md) puertas Build/Improve
    │   ├── META_PIPELINE.md            ← (migrar de /tmp/um_meta/meta_pipeline.md) diseño meta-ciclo
    │   ├── FUNNEL.md                   ← (migrar de /tmp/um_doors/funnel.md) embudo y mortalidad
    │   ├── FILTROS_ORGANICOS.md        ← (migrar de /tmp/um_doors/filtros_organicos.md)
    │   └── FACTORY_REFERENCE.md        ← (migrar de /tmp/um_doors/factory_reference.md) solo referencia, NO autoridad
    ├── evidencia/                      ← informes fechados, nunca sobrescritos
    │   ├── 2026-08-29/                 ← una carpeta por día
    │   │   ├── estado_API_1620.md      ← snapshots de API con hora
    │   │   ├── cfx_actual/             ← (migrar de /tmp/um_doors/cfx_actual/)
    │   │   ├── cfx_backup/             ← (migrar de /tmp/um_doors/cfx_backup/)
    │   │   ├── mcprobe/                ← (migrar de /tmp/um_mcprobe/: fusible, clases javap)
    │   │   ├── semillas_*.csv          ← exports de databanks (evidencia física del semillero)
    │   │   └── logs_motor/             ← copia de log_2026_08_29.log y improve_cycle.log
    │   └── backups_cfx/                ← (migrar de /home/ubuntu/ORDENAR/: los 7 backups project.cfx + project_backup_20260817)
    └── scripts/                        ← (migrar de /home/ubuntu/ y /home/ubuntu/ORDENAR/um_doors_20260829/)
        ├── improve_cycle.sh            ← (desde /home/ubuntu/improve_cycle.sh, tras parche del gatillo)
        ├── patcher.py                  ← (desde ORDENAR/um_doors_20260829/patcher.py)
        └── APLICAR.sh                  ← (desde ORDENAR/um_doors_20260829/APLICAR.sh)
```

### Qué NO se mueve
- `docs/00_MASTER_IDEAS_Y_PLAN.md` ya existe en `01 Ultrarentable/docs/`: se deja ahí y el README del subproyecto lo enlaza como doc maestro (o se copia a `estrategias_um/docs/` si se prefiere autocontención — elegir UNA y anotarlo en DECISIONES_LOG).
- Los archivos de la raíz (ARCHITECTURE.md, GEMINI.md, apps/, scripts/, etc.) pertenecen a la aplicación web: fuera de alcance.
- `node_modules`, `data/`, `database.sqlite`: no son del proyecto de estrategias.

## 2. Migración desde /tmp y ORDENAR (orden de ejecución, todo con `cp -a` conservando origen en /tmp como readOnly hasta verificar)

```bash
RAIZ="/home/ubuntu/workspace/pro/trading/01 Ultrarentable/estrategias_um"
mkdir -p "$RAIZ/docs" "$RAIZ/evidencia/2026-08-29" "$RAIZ/evidencia/backups_cfx" "$RAIZ/scripts"

# A) Docs de verdad (desde /tmp, volátil — prioridad máxima)
cp -a /tmp/um_restruct/01_ESTADO.md            "$RAIZ/docs/ESTADO.md"
cp -a /tmp/um_restruct/02_PLAN_PIPELINE.md     "$RAIZ/docs/PLAN_PIPELINE.md"
cp -a /tmp/um_meta/meta_pipeline.md            "$RAIZ/docs/META_PIPELINE.md"
cp -a /tmp/um_doors/config_doors.md            "$RAIZ/docs/CONFIG_DOORS.md"
cp -a /tmp/um_doors/funnel.md                  "$RAIZ/docs/FUNNEL.md"
cp -a /tmp/um_doors/filtros_organicos.md       "$RAIZ/docs/FILTROS_ORGANICOS.md"
cp -a /tmp/um_doors/factory_reference.md       "$RAIZ/docs/FACTORY_REFERENCE.md"

# B) Evidencia física
cp -a /tmp/um_doors/cfx_actual  "$RAIZ/evidencia/2026-08-29/cfx_actual"
cp -a /tmp/um_doors/cfx_backup  "$RAIZ/evidencia/2026-08-29/cfx_backup"
cp -a /tmp/um_mcprobe           "$RAIZ/evidencia/2026-08-29/mcprobe"
cp -a /home/ubuntu/ORDENAR/um_doors_20260829/config_doors.md "$RAIZ/evidencia/2026-08-29/"  # copia de control
cp -a /home/ubuntu/log_2026_08_29.log        "$RAIZ/evidencia/2026-08-29/logs_motor/" 2>/dev/null
cp -a /home/ubuntu/improve_cycle.log         "$RAIZ/evidencia/2026-08-29/logs_motor/" 2>/dev/null

# C) Backups de project.cfx (traza de cambios de configuración)
cp -a /home/ubuntu/ORDENAR/backup_Ultra_Matrix_*.cfx "$RAIZ/evidencia/backups_cfx/"
cp -a "/home/ubuntu/ORDENAR/user/projects/backups/project_backup_20260817_061012.cfx" "$RAIZ/evidencia/backups_cfx/"

# D) Scripts
cp -a /home/ubuntu/improve_cycle.sh                     "$RAIZ/scripts/improve_cycle.sh"
cp -a /home/ubuntu/ORDENAR/um_doors_20260829/patcher.py "$RAIZ/scripts/patcher.py"
cp -a /home/ubuntu/ORDENAR/um_doors_20260829/APLICAR.sh "$RAIZ/scripts/APLICAR.sh"

# E) Verificación de integridad (antes de borrar nada de /tmp)
diff -r /tmp/um_doors/cfx_actual "$RAIZ/evidencia/2026-08-29/cfx_actual" && echo OK_A
```
Regla: **no se borra ningún origen hasta que `diff` (o sha256sum) confirme copia íntegra**; /tmp es volátil, así que la verificación es el mismo día.

## 3. Convención de nombres
- Docs de verdad (`docs/`): `MAYÚSCULAS_CON_GUIONES_BAJOS.md` (PLAN_PIPELINE.md, ESTADO.md). Un tema = un archivo.
- Evidencia: `evidencia/YYYY-MM-DD/` + nombre descriptivo con hora UTC si es snapshot (`estado_API_1620.md`, `semillas_YYYYmmdd_HHMM.csv`). **Nunca sobrescribir evidencia**: nueva lectura = nuevo archivo con nueva hora.
- Backups cfx: nombre original tal cual (`backup_Ultra_Matrix_pre_window_20260829.cfx`) — el nombre ES el metadato.
- Scripts: `snake_case.sh/.py`.
- PROHIBIDO: `final`, `v2`, `nuevo`, `copy` en nombres; versionar es crear evidencia fechada o una línea en DECISIONES_LOG.

## 4. Qué va en cada archivo (sin duplicación)
| Archivo | Contenido EXCLUSIVO | Nunca contiene |
|---|---|---|
| README.md | Visión del proyecto, mapa/enlaces a todos los docs, estado en 1 línea con fecha | Datos técnicos, números que cambian |
| docs/ESTADO.md | Foto viva del sistema: qué existe, qué está roto (R1, R2…), números de hoy | Historia, decisiones justificadas |
| docs/PLAN_PIPELINE.md | Diseño objetivo: estados CRUDA→CANDIDATA→VALIDADA→META, correcciones C1–C4, lazo cerrado | Estado actual, evidencia |
| docs/META_PIPELINE.md | Diseño del meta-ciclo por fases (watchdog/captura/mejora/refiltro) y auditoría inicial | Estado vivo |
| docs/CONFIG_DOORS.md | Valores EXACTOS de las puertas Build/Improve (tablas cfx) | Interpretación, planes |
| docs/FUNNEL.md / FILTROS_ORGANICOS.md | Mortalidad medida y justificación de filtros | Comandos |
| docs/HECHOS_Y_DECISIONES.md | Lista compacta de hechos verificados (con enlace a su evidencia en evidencia/) y de decisiones D1, D2… con su justificación | Detalles largos (van en los docs temáticos) |
| docs/DECISIONES_LOG.md | APPEND-ONLY: `## YYYY-MM-DD HH:MM — D<N>: <decisión> — contexto, alternativas, quién` | Correcciones retroactivas (se añade nueva entrada que anula) |
| docs/RUNBOOK_OPERACION.md | Comandos API verificados, procedimientos de parada/copia/arranque, fases con candado | Análisis, diseño |
| evidencia/ | Informes y datos crudos con fecha, inmutables | Conclusiones (van en docs/) |

**Regla de oro:** si un mismo número necesita aparecer en dos sitios, uno de los dos es un ENLACE (`ver ESTADO.md §3`), nunca una copia.

## 5. ESQUELETO — README.md (proyecto de estrategias)

```markdown
# Ultra_Matrix — Proyecto de estrategias (SQX)
> Una línea de estado: [fecha] — motor en X estado, semillero N records, siguiente acción Y.
> (Actualizar SOLO esta línea al editar; el detalle va en docs/ESTADO.md)

## 1. Visión
2-3 frases: qué es "estrategias que buscan estrategias": Build genera crudas, puertas
validan, Improve mejora, el refiltro devuelve lo robusto a InitialPopulation y el
genético evoluciona sobre lo real. Objetivo: banco de VALIDADAS reproducible, no apuestas.

## 2. Principios operativos
- Real-only (cero datos inventados), motor intocable salvo ventana de parada con backup,
  toda modificación con candado y evidencia fechada.

## 3. Mapa de la documentación (qué leo cuando)
| Quiero… | Voy a… |
| saber cómo está HOY | docs/ESTADO.md |
| entender el plan completo | docs/PLAN_PIPELINE.md (+ META_PIPELINE.md) |
| saber qué puerta tiene qué valor | docs/CONFIG_DOORS.md |
| por qué se filtra así | docs/FILTROS_ORGANICOS.md, docs/FUNNEL.md |
| qué se decidió y cuándo | docs/DECISIONES_LOG.md (append-only) |
| hechos verificados + decisiones resumidas | docs/HECHOS_Y_DECISIONES.md |
| ejecutar algo contra el motor | docs/RUNBOOK_OPERACION.md |
| comprobar el dato original | evidencia/YYYY-MM-DD/ |
| doc maestro original | docs/00_MASTER_IDEAS_Y_PLAN.md |

## 4. Estructura de carpetas
(árbol de la sección 1, resumido)

## 5. Convención de nombres y regla "un dato = un sitio"
(resumen de secciones 3-4 de este documento)

## 6. Advertencias vigentes
2-3 bullets: semillero volátil en memoria (copiar antes de recargar), nombre legacy
"Last generation" no direccionable, gatillo improve_cycle.sh roto (R2).
```

## 6. ESQUELETO — RUNBOOK_OPERACION.md

```markdown
# RUNBOOK OPERACIÓN — Ultra_Matrix (API 5050)
> Solo comandos verificados en vivo. Regla: read-only libre; toda escritura requiere
> backup cfx + ventana de parada + candado (~/.improve_cycle_state o flock).

## 1. Estado del motor (read-only, seguro siempre)
- Estado del proyecto: `sqcli -project action=status name=Ultra_Matrix`
- Bancos y records: `sqcli -databank action=list project=Ultra_Matrix`
  (ÚNICA vía fiable para el banco legacy "Last generation": los espacios no son
  direccionables por `count name=` — devuelve "Databank 'Last' doesn't exist")

## 2. Fases con candado (toda mutación)
- Precondición: `cp project.cfx backups/pre_<motivo>_YYYYmmdd_HHMM.cfx`
- Candado: `flock /tmp/um_cycle.lock` o state-file `~/.improve_cycle_state`
  (running|stopped) — nunca dos mutaciones en paralelo.
- Fase A PARAR: `sqcli -project action=stop name=Ultra_Matrix`
- Fase B COPIAR banco (solo con motor parado):
  `sqcli -databank action=copy project=Ultra_Matrix name=LastGeneration name2=ToImprove`
  + guard: verificar records destino >0 antes de continuar; si 0 → revertir (start) y abortar.
- Fase C EXPORTAR evidencia:
  `sqcli -databank action=export project=Ultra_Matrix name=LastGeneration file=.../evidencia/YYYY-MM-DD/semillas_YYYYmmdd_HHMM.csv`
- Fase D MEJORAR: `sqcli -project action=startOnlyTask name=Ultra_Matrix task=2`
  (task 2 = Improve-Task1; task 1 = Build. Verificado índice: confirmar con status tras lanzar)
- Fase E REARRANCAR: `sqcli -project action=start name=Ultra_Matrix`
- Verificación post: `action=status` (motor corriendo) + `action=list` (bancos esperados).

## 3. Procedimiento STOP → COPY → START (plantilla literal)
```bash
set -euo pipefail
sqcli -project action=status name=Ultra_Matrix            # 1. pre-check
cp project.cfx evidencia/backups_cfx/pre_captura_$(date +%Y%m%d_%H%M).cfx
sqcli -project action=stop name=Ultra_Matrix              # 2. stop
sqcli -databank action=copy ... name=LastGeneration name2=ToImprove   # 3. copy
sqcli -databank action=list project=Ultra_Matrix          # 4. guard (ToImprove>0)
sqcli -databank action=export ... file=semillas_....csv   # 5. evidencia
sqcli -project action=startOnlyTask name=Ultra_Matrix task=2          # 6. improve
sqcli -project action=start name=Ultra_Matrix             # 7. start
sqcli -project action=status name=Ultra_Matrix            # 8. verificar
```

## 4. Errores conocidos y su significado
- "Databank 'Last' doesn't exist" → nombre con espacios; usar action=list.
- Mejora en curso ≠ colgada: comprobar records de Results_robust_20260809 creciendo.

## 5. Qué NO se hace desde aquí
- Tocar project.cfx sin backup ni ventana; editar config.xml con motor corriendo;
  lanzar dos mutaciones a la vez; borrar bancos.
```

## 7. Reglas de mantenimiento
1. ESTADO.md se reescribe (foto nueva), DECISIONES_LOG.md solo se añade, evidencia/ nunca se toca.
2. Cada entrada nueva en DECISIONES_LOG que cambie el plan debe reflejarse ese mismo día en PLAN_PIPELINE.md y dejar el estado previo como historial de la entrada de log, no editado.
3. El README solo cambia su línea de estado y el mapa si nace/mueve un doc.
4. Los CSV de semillas y los informes de API con hora son LA prueba; si docs y evidencia discrepan, gana evidencia y se abre entrada en DECISIONES_LOG.
