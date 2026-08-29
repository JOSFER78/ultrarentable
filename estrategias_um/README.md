# Ultra_Matrix — Proyecto de estrategias (SQX headless)

> **Línea de estado (única que se edita aquí):** [2026-08-29 16:30 UTC] — Motor corriendo (config en memoria de 13:15), embudo con caudal 0 validadas (fusible MC por trades=0), semillero legacy con ~91-93 crudas reales en memoria, siguiente acción: **FASE 1 del plan — ejecutar el primer ciclo del lazo con el semillero capturado** (esperando aprobación del usuario).
> El detalle vivo está en `docs/ESTADO.md`.

## 1. Visión
"Estrategias que buscan estrategias": el Build genera estrategias crudas (materia prima), unas "puertas" (Walk-Forward, Retest, Monte Carlo) las examinan, Improve las mejora, y un refiltro devuelve lo robusto a InitialPopulation para que el genético evolucione sobre lo ya conseguido. Objetivo: un banco de estrategias validadas reproducible — no apuestas, proceso.

**Autosuficiencia total (mandato del usuario):** nada de valores de fábrica ni docs oficiales como autoridad — solo evidencia propia medida en nuestro sistema. StrategyQuant es el medio, no la dependencia.

## 2. Principios operativos
- **Real-only:** cero datos inventados; cada afirmación con evidencia citada (fichero+línea, log+hora, o API+hora).
- **Motor intocable salvo ventana de parada** con backup del project.cfx y candado (nunca dos mutaciones a la vez).
- **Un dato = un sitio:** un hecho vive en un único doc; el resto enlaza. Evidencia fechada nunca se sobrescribe.
- **No rechazar el 100%:** siempre bancar candidatas para investigar/mejorar/evolucionar (mandato permanente).

## 3. Mapa de la documentación (qué leo cuando)
| Quiero… | Voy a… |
|---|---|
| saber cómo está HOY el sistema | `docs/ESTADO.md` |
| entender el plan completo por fases | `docs/PLAN_PIPELINE.md` |
| el diseño del ciclo banco→mejora→refiltro | `docs/META_PIPELINE.md` |
| saber qué puerta tiene qué valor | `docs/CONFIG_DOORS.md` |
| por qué se filtra así | `docs/FILTROS_ORGANICOS.md` + `docs/FUNNEL.md` |
| separar hecho verificado de hipótesis | `docs/HECHOS_Y_DECISIONES.md` |
| qué se decidió y cuándo | `docs/DECISIONES_LOG.md` (append-only) |
| ejecutar algo contra el motor | `docs/RUNBOOK_OPERACION.md` |
| comprobar el dato original | `evidencia/YYYY-MM-DD/` |
| doc maestro general de Ultrarentable | `../docs/00_MASTER_IDEAS_Y_PLAN.md` |

##  estrategias_um/ — estructura
```
estrategias_um/
├── README.md                 ← este mapa (visión + índice + 1 línea de estado)
├── docs/                     ← verdad del proyecto (un tema = un archivo)
│   ├── ESTADO.md             ← foto viva: qué existe, qué está roto, números
│   ├── PLAN_PIPELINE.md      ← plan por fases: CRUDA→CANDIDATA→VALIDADA→META
│   ├── META_PIPELINE.md      ← diseño del lazo banco→mejora→refiltro→re-siembra
│   ├── CONFIG_DOORS.md       ← las 24 puertas con valores exactos
│   ├── FUNNEL.md             ← forense del embudo (62.942 generadas → 0 guardadas)
│   ├── FILTROS_ORGANICOS.md  ← rediseño de puertas para caudal natural
│   ├── ESTRUCTURA_DOCS_DISENO.md ← diseño que originó esta estructura
│   └── FACTORY_REFERENCE.md  ← (solo referencia, NO autoridad)
├── evidencia/                ← informes y datos crudos fechados, inmutables
│   ├── 2026-08-29/           ← cfx_actual, cfx_backup, mcprobe, logs_motor
│   └── backups_cfx/          ← 7 backups del project.cfx
└── scripts/                  ← improve_cycle.sh, patcher.py, APLICAR.sh
```

## 4. Advertencias vigentes
- **Semillero volátil en memoria:** el banco legacy "Last generation" (~91-93 crudas) solo vive en RAM del motor; sin export CSV previo, un reinicio lo borra. Capturar ANTES de cualquier recarga.
- **Nombre con espacio no direccionable:** "Last generation" solo se ve vía `-databank action=list` (el `count name=` falla con espacios).
- **Gatillo roto:** improve_cycle.sh cuenta el banco renombrado (0 eterno) → el meta-ciclo está muerto hasta parchear (PLAN_PIPELINE C4).
- **Config en memoria:** los parches de configuración no surten efecto hasta recargar/reiniciar el proyecto — por eso las "ventanas de parada" del plan.
- **/tmp es volátil:** toda la evidencia ya está migrada a esta carpeta permanente; /tmp es solo copia de trabajo.
