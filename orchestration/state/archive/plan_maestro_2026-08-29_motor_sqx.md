# PLAN MAESTRO — Orquestación Orquestador (Auditor) + Antigravity (Ejecutor)

Fuente de evidencia: `estrategias_um/docs/PLAN_PIPELINE.md` + `estrategias_um/docs/HECHOS_Y_DECISIONES.md`
(2026-08-29). Doctrina: REAL-ONLY / ZERO-MOCKS; motor en modo lectura; toda modificación solo
por ventanas de parada controladas. **Sin git commit automático** — el registro de auditoría son
los propios archivos de `orchestration/` (results/, reviews/, history en status.json).

> [!IMPORTANT]
> **DIRECTIVA MAESTRA DE ACTIVOS Y TEMPORALIDADES (MANDATO INVIOLABLE 2026-08-30):**
> 1. **ULTRA NO ES SOLO CRIPTO NI SOLO 4H CONSERVADOR:** ULTRA opera sobre el 100% de activos (Cripto Perpetuos, Futuros CME, Forex Majors, Commodities).
> 2. **5 TEMPORALIDADES INTRADÍA EN TODOS LOS ACTIVOS:** `1min` (`1m`), `5min` (`5m`), `15min` (`15m`), `1h` (`1h`) y `4h` (`4h`) — **SOLO INTRADIA** en ambos tracks (ULTRA y FONDEO).
> 3. **SOLO INTRADIA:** Cero carryover multi-día descontrolado; cierre al término de sesión/jornada en todas las temporalidades.

## Modelo de operación (AUTOMÁTICO — nadie pega tareas a mano)

1. El orquestador escribe la tarea en `state/current_phase.md` y pone `status.json: pending`.
2. **Antigravity** (en el PC del usuario, con orden permanente de leer
   `orchestration/INSTRUCCIONES_ANTIGRAVITY.md`) detecta `pending`, ejecuta la fase en modo
   multi-agente, deja informe en `results/fase_NN.log` y marca `done`.
3. El **orquestador** tiene un reloj (cron de Hermes) que cada pocos minutos comprueba el estado
   (script determinista `orch_status.sh`). Cuando ve `done`: analiza el informe, audita el repo,
   escribe veredicto en `reviews/fase_NN_review.md` y — según el veredicto — escribe la siguiente
   fase en `current_phase.md` y vuelve a `pending`, o repite la fase con correcciones, o para con
   `needs_user_input` y avisa al usuario.
4. El usuario solo interviene en `needs_user_input` (decisiones de negocio/vistos buenos).

---

## Fase 0 — Limpieza y reorganización del repo (independiente, ya diseñada)

- **Objetivo:** mover los huérfanos (11 ficheros raíz + carpetas históricas) a `cuarentena/` con
  manifiesto (hash + origen), y reorganizar según `estrategias_um/evidencia/2026-08-29/limpieza/09_ESTRUCTURA_DESTINO.md`.
  NADA se borra. Scripts en dry-run ya probados (cuarentename.sh, migrate_limpieza.sh).
- **Criterio de éxito verificable:** manifest.csv completo (sha256 de cada elemento movido),
  diff de git muestra solo renames/moves, raíz reducida a ~20 elementos vivos, cero borrados.
- **Dependencias:** aprobación del usuario (visto bueno de limpieza). Ejecutable en paralelo con
  la Fase 1 (no toca el motor ni orchestration/).
- **Estado:** pendiente de aprobación — se encola tras el visto bueno.

---

## Fase 1 — Capturar el semillero 'Last generation' (CRUDAS) antes de perderlo

- **Objetivo:** preservar el semillero legacy (~91-95 estrategias CRUDAS reales, H8) en
  ToImprove + export CSV de evidencia, ANTES de cualquier reinicio del proyecto (H13: todo vive
  en RAM; un reinicio pierde lo no exportado).
- **Criterio de éxito verificable:**
  - [ ] Guard previo: proyecto PARADO (API 5050 confirma estado no-running).
  - [ ] Copy `Last generation` → `ToImprove` ejecutado; `-databank action=list` muestra
        ToImprove Records > 0.
  - [ ] CSV exportado en `/home/ubuntu/ORDENAR/semillas_*.csv` con columna `banco_origen`,
        no vacío, con ≥91 filas de estrategias.
  - [ ] Informe de Agy en `results/fase_01.log` con los counts reales por banco (antes/después).
- **Dependencias:** ninguna (es la PRIMERA acción — riesgo máximo de reciclado del banco legacy).
- **Estado:** `needs_user_input` — requiere visto bueno del usuario para la ventana de parada.

## Fase 2 — Ventana de parada: correcciones del embudo (fusible MC + umbrales + proyecto limpio)

- **Objetivo:** aplicar en UNA sola ventana de parada las correcciones C1/C2/C3 de
  PLAN_PIPELINE.md §1 (DD1-a: apagar RandomizeStartingBar con fallbacks ordenados; C2 umbrales
  orgánicos WF 70/8, Retest ≥50%, MC suavizado; C3 unificar WF Build/Improve), con backup del
  project.cfx y del banco ya capturado en Fase 1.
- **Criterio de éxito verificable:**
  - [ ] Backup previo del cfx con timestamp, verificable en disco.
  - [ ] Tras re-arranque: motivos de rechazo en log DIFERENTES de "sin transacciones" (resolución
        de la contradicción H12).
  - [ ] `En la base de datos > 0` en alguna línea de status dentro de las primeras horas.
  - [ ] Parche de improve_cycle.sh (C4: parsear count vía `action=list`, soporta nombre con
        espacio) aplicado y crontab `*/15` activo.
- **Dependencias:** Fase 1 completada y revisada (semillero seguro en CSV + ToImprove).

## Fase 3 — Modo 24/7: lazo automático con guards

- **Objetivo:** lazo banco→mejora→refiltro→InitialPopulation en producción continua: cron
  `*/15` con watchdog de semillero (≥umbral y estable ≥2 ticks), guards ToImprove>0 antes de
  Improve y InitialPopulation>0 antes de re-arrancar, auto-arranque del motor (sqx_autostart) y
  backend autónomo bajo systemd.
- **Criterio de éxito verificable:**
  - [ ] ≥5 ciclos completos del lazo sin intervención manual de emergencia.
  - [ ] Logs de bitácora por ciclo con counts reales por banco (timestamp + counts + cambios).
  - [ ] `systemctl status` del servicio muestra uptime estable y reinicio automático tras stop
        manual de prueba.
  - [ ] Cero "fabricación de semillas": si semillero=0 real, el watchdog espera y registra.
- **Dependencias:** Fase 2 (umbrales corregidos + crontab ya parcheado).

## Fase 4 — Página web DATABANK correcto + build final

- **Objetivo:** página web de consulta del databank con datos REALES (snapshots CSV de
  `/home/ubuntu/ORDENAR/` + counts por API), sin mocks; build final del proyecto con el embudo
  calibrado.
- **Criterio de éxito verificable:**
  - [ ] La web muestra counts que coinciden 1:1 con `-databank action=list` y con el CSV más
        reciente (spot-check de ≥5 registros).
  - [ ] Snapshot CSV diario 04:00 presente y no vacío (cinturón anti-reciclado).
  - [ ] Build final ejecutado y su log archivado en `results/`.
- **Dependencias:** Fase 3 (lazo estable que genera datos reales que mostrar).

## Fase 5 — Debate de agentes: meta-estrategias

- **Objetivo:** usando las VALIDADAS más longevas (sobrevivieron ≥N refiltros) como semilla
  preferente del genético, cerrar "estrategias que buscan estrategias" en su forma fuerte; debate
  de agentes sobre qué atributos de las VALIDADAS predicen supervivencia al refiltro siguiente.
- **Criterio de éxito verificable:**
  - [ ] `InitialPopulation Records > 0` poblado por descendientes de VALIDADAS (peso por longevidad).
  - [ ] Al menos un "Project started" del Build arrancando con InitialPopulation poblado
        (lazo cerrado, verificado por API).
  - [ ] Acta del debate (posturas + veredicto + cambios aplicados) en `reviews/`.
- **Dependencias:** Fase 4 (banco validado suficiente y estable para alimentar el genético).

---

## Reglas transversales

1. NADA de `git commit` automático por scripts; el árbol de `orchestration/` ES la auditoría.
2. Solo ventanas de parada para tocar config; captura del semillero SIEMPRE antes de reiniciar.
3. Nunca fabricar datos: sin semillero real, se espera y se registra (watchdog pasivo).
4. 2-3 veredictos `repite` seguidos sobre la misma fase ⇒ `needs_user_input` automático.
