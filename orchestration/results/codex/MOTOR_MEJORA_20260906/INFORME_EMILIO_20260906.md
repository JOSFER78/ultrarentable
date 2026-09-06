# Informe para Emilio: motor propio de mejora de estrategias (2026-09-06)

Estado al cierre del informe: 21:44 CEST. Todo lo descrito está en la VPS `88.99.210.167` y en el
repositorio `ultrarentable` (rama `motor-mejora-entrega-1`, seis commits de hoy, empujados a `origin`).
Nada de lo que sigue acredita rentabilidad ni aptitud para un examen: son mecanismos comprobados y
resultados de desarrollo, con sus límites escritos.

## 1. Resumen en diez líneas

1. Existe un motor propio de mejora que recibe una estrategia de SQX, la reproduce, la diagnostica, deja
   que agentes de IA propongan hipótesis, construye variantes verificadas, las recalcula en SQX, las evalúa
   con criterios registrados de antemano y entrega un paquete con la clase de cada variante.
2. Son nueve programas independientes con contrato de ficheros; cada uno se modifica y prueba por separado.
3. Los agentes piensan (dos proponentes ciegos, un crítico, un árbitro); los programas ejecutan y miden.
   La IA del sistema es el omnirouter de tu VPS de Oracle; para pruebas he usado la IA de Claude.
4. El vocabulario de cambios cubre salidas, parámetros numéricos y filtros de hora, día y dirección; la
   semántica de los filtros está medida con recálculos reales en SQX.
5. Un servicio autónomo en la VPS (temporizador cada 15 minutos) recorre todas las estrategias extraídas
   de SQX: 126 admitidas hoy (125 de la preselección del generador de fondeo y de la entrega de fase 5, más
   la de referencia), reparte el trabajo entre ellas, mide el presupuesto en experimentos sin progreso y
   continúa desde cada variante aceptada como estrategia hija con evidencia exigida creciente.
6. En vivo: 127 estrategias en cola, 23 experimentos del servicio (29 con los de la mañana), 35 variantes
   evaluadas, cero fallos técnicos, una variante aceptada y un linaje en curso.
7. La variante aceptada (`Strategy 1.19.157`, MNQ M15: desactivar cortos) es una mejora pequeña, relevante
   solo por el criterio Ultra, sobre datos que son un alias CFD; no es una candidata de fondeo ni está validada.
8. 205 pruebas automáticas correctas; una revisión adversarial con siete defectos corregidos.
9. Lo no demostrado: ninguna estrategia mejorada de forma útil para un examen; ninguna validación con datos
   no consultados (no existen todavía).
10. Decisiones tuyas pendientes: combos del omnirouter, datos posteriores o de futuros reales, y si entra el
    `ToImprove` de Ultra_Matrix.

## 2. Qué se construyó, módulo a módulo (carpeta `scripts/herramientas/`)

| Módulo (ruta en el repositorio) | Líneas | Qué hace | Cuándo tocarlo |
| --- | --- | --- | --- |
| `scripts/herramientas/sqx_strategy_contract.py` | 449 | Contrato de entrada de un `.sqx`: identidad, hash semántico de reglas (ignora metadatos de editor), mercado, periodo y OOS, costes, opciones, filtros visibles; `compare_rules` clasifica dos archivos como idénticos, solo metadatos o cambio real | cambie el formato de SQX o qué se considera metadato |
| `scripts/herramientas/sqx_trade_diagnosis.py` | 575 | Diagnóstico determinista de las órdenes: tipos de cierre, devolución de beneficio, concentración, múltiplos R con el riesgo del control, tablas por hora/día/dirección, cribado provisional de examen en ventanas de 1 a 5 días, estudio de exposición, hallazgos con código | se añadan análisis o escenarios de examen |
| `scripts/herramientas/sqx_variant_mutations.py` | 601 | Vocabulario de cambios (salidas por dirección, parámetros por ruta del catálogo, filtros `hour_range`, `exclude_weekdays`, `disable_direction` como bloques nativos de SQX) y verificación de que la variante cambia exactamente lo declarado y nada más | los agentes pidan una palanca nueva |
| `scripts/herramientas/sqx_hypothesis_debate.py` | 599 | Debate de agentes: dosier determinista, dos proponentes ciegos con lentes distintas, validación de cada propuesta con el motor de mutaciones, crítico, árbitro sin consenso forzado; proveedores `omniroute` (sistema), `anthropic`, `claude-cli`, `replay` | cambien roles, prompts o el endpoint de IA |
| `scripts/herramientas/sqx_native_improvement.py` | 1650 | Motor de recálculo nativo (ya existía): proyecto `Retest` dedicado, reclamación, evidencia con hashes, exportación de órdenes | cambie SQX o su CLI |
| `scripts/herramientas/sqx_variant_evaluation.py` | 309 | Política de evaluación: comparación emparejada por día con bootstrap, tolerancias, relevancia por destino, siete clases; evidencia OOS exigida según profundidad del linaje | cambien los criterios de aceptación |
| `scripts/herramientas/sqx_improvement_cycle.py` | 419 | Orquestación de un experimento: `dossier`, `prepare-local`, `run`, `evaluate`; entrega `entrega.json`; registro por estrategia | cambie el formato de entrega o el registro |
| `scripts/herramientas/sqx_improvement_service.py` | 534 | Servicio autónomo v2: admisión desde fuentes, cola persistente, reparto, presupuesto por falta de progreso, linaje, reintentos limitados | cambien fuentes, prioridad, presupuesto o linaje |
| `scripts/herramientas/sqx_fixed_hypotheses_scaffold.py` | 70 | Hipótesis fijas SOLO para pruebas del mecanismo | nunca en producción |

Unidades de systemd (en el repositorio y en la VPS): `scripts/herramientas/sqx-mejora-agentes.timer`
y `scripts/herramientas/sqx-mejora-agentes.service`.

Pruebas (carpeta `tests/sqx_runtime/`): `test_improvement_cycle.py` (15), `test_hypothesis_debate.py` (5),
`test_improvement_service.py` (13), `test_variant_filters.py` (16). Suite completa de `tests/sqx_runtime`:
205 correctas. Orden para ejecutarlas desde la carpeta `ultrarentable`:

```
.venv\Scripts\python.exe -m pytest tests\sqx_runtime -q
```

Guía de uso y mapa de módulos: `docs/Laboratorio/07_MOTOR_MEJORA_CICLO.md`.

## 3. Cómo funciona el flujo (lo que hace el servicio con cada estrategia)

1. **Admisión.** Copia al `inbox` los `.sqx` nuevos de las fuentes configuradas, con un `.json` de
   procedencia (origen, celda, ronda, métricas de la selección). No toca los archivos de origen; un archivo ya
   visto (mismo SHA-256) no vuelve a entrar.
2. **Contrato.** Extrae identidad, reglas, mercado, periodo, OOS, costes y opciones. Si falta algo esencial,
   la estrategia queda `REJECTED_INPUT` con el motivo.
3. **Órdenes base.** Las del último recálculo si existe; si es una hija, las frescas de la variante aceptada;
   si no, las heredadas del archivo (exportadas con Java desde `orders.bin`).
4. **Diagnóstico.** Perfil IS y OOS, hallazgos con código, cribado provisional de examen, exposición.
5. **Debate.** Dosier con contrato, diagnóstico (tablas por segmento solo de la muestra de construcción),
   vocabulario de cambios, variantes ya probadas (también las de sus antecesoras) y criterios. Dos proponentes
   ciegos, validación determinista, crítico, árbitro. Como máximo dos variantes por experimento.
6. **Variantes.** Cada cambio se aplica y se verifica: exactamente lo declarado y nada más.
7. **Recálculo.** Proyecto `Retest` dedicado en SQX con control y variantes en condiciones idénticas.
8. **Evaluación.** Comparación emparejada por día (IS y OOS) con intervalos bootstrap, tolerancias y
   relevancia por destino. Clases: `NO_CHANGE_RULES`, `NO_EFFECT_IN_SAMPLE`, `REJECTED_WORSE`,
   `HISTORICAL_FIT_ONLY`, `DEV_FAVORABLE_RELEVANT`, `DEV_FAVORABLE_NOT_RELEVANT`, `INCONCLUSIVE`.
9. **Registro y entrega.** Todo lo probado queda en el registro de la estrategia (nunca se repite una
   variante); `entrega.json` resume el experimento.
10. **Decisión.** Una variante `DEV_FAVORABLE_RELEVANT` se copia a `outbox/` y pasa a ser estrategia hija
    (linaje); tres experimentos seguidos sin progreso agotan la estrategia; dos debates vacíos también; dos
    fallos técnicos la dejan en `NEEDS_ATTENTION` con diagnóstico.

Protecciones contra el sobreajuste: criterios registrados antes de recalcular (con hash atado al
experimento), OOS de desarrollo consultado solo por el programa, tablas OOS por segmento ocultas a los
agentes, registro de todo lo probado, evidencia exigida creciente con la profundidad del linaje (moderada en
las dos primeras generaciones, fuerte después; tope de tres), y ninguna clase equivale a validado.

## 4. Qué se probó y qué salió (cronología)

| Hora CEST | Fase | Qué | Resultado |
| --- | --- | --- | --- |
| 13:00–15:35 | 1 | Ciclo completo con `Strategy 1.1.27` (@EW H1, futuros continuos de SQX): dos variantes de salida | Referencia reproducida exactamente; ambas `INCONCLUSIVE`; la variante de metadatos del Improver rechazada antes de recalcular |
| 16:00–16:35 | 2 | Debate real con Claude (CLI) y ciclo 02 | `NO_EFFECT_IN_SAMPLE`, `HISTORICAL_FIT_ONLY` |
| 16:40–17:10 | 2 | Debate por el omnirouter (Gemini 3 Flash por respaldo) y ciclo 03 | Dos `INCONCLUSIVE` |
| 17:10–17:36 | 3 | Módulos independientes y servicio autónomo; dos ejecuciones (manual y por temporizador) | `NO_HYPOTHESES` sin gasto; dos `INCONCLUSIVE`; clase demasiado benévola corregida |
| 19:30–19:41 | 4 | Filtros de hora, día y dirección: cuatro recálculos de mecanismo | SQX acepta los bloques; semántica medida (barra de señal, relleno en la hora siguiente; el filtro de día no acota órdenes de la víspera) |
| 19:44–19:53 | 4 | Ciclo 04 con Claude sobre el vocabulario nuevo | `REJECTED_WORSE`, `INCONCLUSIVE`; ningún agente usó filtros; dos propuestas murieron por un hueco (`move_sl_to_be` en `None`) |
| 19:47–19:59 | 4 | Revisión adversarial del vocabulario | Nueve hallazgos, siete defectos corregidos con prueba |
| 20:05–20:43 | 5 | Inventario de las extraídas y servicio v2 | 125 admitidas; primera ejecución: seis experimentos en 531 s sin fallos |
| 20:43–21:44 | 5 | Servicio corriendo solo | 23 experimentos; primera variante aceptada; primer linaje |

Resultados acumulados sobre `Strategy 1.1.27` (nueve experimentos, trece variantes): cero candidatas; la
estrategia está agotada con el vocabulario actual.

## 5. Estado en vivo (21:44 CEST)

| Magnitud | Valor |
| --- | --- |
| Estrategias en cola | 127: 105 en espera, 21 en curso, 1 con linaje continuado |
| Experimentos del servicio | 23 (más los seis de la mañana y del PC: 29) |
| Variantes evaluadas por el servicio | 35: 21 rechazadas, 8 inconclusas, 2 sin efecto en la muestra, 2 ajuste histórico, 1 mejora sin relevancia, 1 aceptada |
| Ritmo | 88 s por experimento, unos 24 por hora (el generador de fondeo ocupa SQX al 440 % de CPU) |
| Fallos técnicos, reconciliaciones | 0 |
| Registro | 17 estrategias con historial |
| Entregas en `outbox/` | 1 |

**La variante aceptada.** `Strategy 1.19.157` (MNQ M15, preselección del generador): desactivar los cortos.
Construcción +825 (sobre 32 310), desarrollo +224 (sobre 18 859); ratio retorno/caída +0,83 y +0,85; 14 días
OOS cambian con intervalo del 90 % entre +140 y +322 (evidencia fuerte). Relevante solo por el criterio Ultra
(expectativa R): los datos son un alias CFD y el cribado de examen no aplica. Su hija (`…_H1_EST1`, profundidad
1) ya hizo un experimento: dos rechazos. Es una mejora pequeña por quitar un lado perdedor, no una
estrategia validada.

## 6. Direcciones de todo

### 6.1 En la carpeta `ultrarentable` (repositorio)

- `orchestration/results/codex/MOTOR_MEJORA_20260906/` — carpeta de evidencia de hoy:
  - `INFORME_EMILIO_20260906.md` — este informe.
  - `RESULTADO.md` — el resultado técnico completo por fases (§1 a §12), con las siete preguntas del encargo.
  - `INVESTIGACION_DEBATE_SEMANTICO.md` — por qué y cómo el debate de agentes (literatura y guardas).
  - `ULTRA_REQUISITOS_20260906.md` — qué se sabe de Ultra y de "UltraPiramidal" (criterios solo exploratorios).
  - `ciclo_ew_20260906_01.zip` … `_04.zip` — los cuatro ciclos completos del PC (dosier, debate, proyecto,
    recálculo, órdenes, evaluación, entrega).
  - `mecanismo_filtros_20260906.zip` y `.manifest.json` — los cuatro recálculos que miden la semántica de los filtros.
  - `debate_ciclo_02/`, `debate_ciclo_03_omniroute/`, `debate_ciclo_04_claude/` — los debates completos (dosier,
    respuestas de cada agente, resumen, registro de llamadas, intervenciones).
  - `servicio_mejora_20260906/` — las dos primeras ejecuciones del servicio (fase 3).
  - `improvement_registry/` — instantánea del registro de la estrategia de referencia (13 variantes, 9 experimentos).
  - `entrega_ciclo_0N.json`, `evaluacion_ciclo_0N.json`, `plan_ciclo_01.json`, `criterios_ciclo_01.json`.
  - `MANIFIESTO.json` — SHA-256 de todos los archivos de la carpeta.
- `docs/Laboratorio/07_MOTOR_MEJORA_CICLO.md` — guía: mapa de módulos, servicio v2, filtros, recorrido
  manual, clases, reglas aprendidas.
- `docs/Laboratorio/06_SQX_OPERACION_VPS.md` — operación de SQX en la VPS (nota de estado).
- `docs/PLAN_ACTUAL.json` — bitácora que lee la página `/plan` (cinco entradas de hoy).
- `orchestration/state/plan/MEMORIA_PROYECTO.md` — memoria del proyecto (cinco secciones de hoy).
- `scripts/herramientas/sqx_*.py` — los nueve módulos (tabla del apartado 2).
- `scripts/herramientas/sqx-mejora-agentes.timer` y `.service` — unidades de systemd.
- `tests/sqx_runtime/test_improvement_cycle.py`, `test_hypothesis_debate.py`, `test_improvement_service.py`,
  `test_variant_filters.py` — pruebas.

Commits de hoy en la rama `motor-mejora-entrega-1` (todos en `origin`):

| Commit | Hora | Contenido |
| --- | --- | --- |
| `38a4dc363` | 15:37 | Fase 1: ciclo completo comprobado |
| `7a99be8c2` | 16:42 | Fase 2: debate de agentes integrado y dos ciclos más |
| `5657207c6` | 17:36 | Fase 3: módulos independientes y servicio autónomo |
| `ea186437a` | 19:59 | Fase 4: filtros comprobados en SQX y ciclo 04 |
| `f635e88b4` | 20:06 | Correcciones de la revisión adversarial |
| `d920b0c1a` | 20:43 | Fase 5: todas las extraídas, mejoradas todo lo posible |

### 6.2 En la VPS `88.99.210.167` (usuario `root`, clave `C:\Users\yo\.ssh\id_rsa_moltbot`)

- `/opt/SQX-headless/import/sqx_*.py` — los nueve módulos, con los mismos hashes que el repositorio.
- `/etc/systemd/system/sqx-mejora-agentes.timer` y `.service` — cada 15 minutos, hasta 6 experimentos en 12 minutos.
- `/opt/SQX-headless/import/mejora/` — estado del servicio (39 MB hoy):
  - `queue.json` — la cola: una entrada por estrategia con estado, presupuesto, experimentos, linaje, errores.
  - `status.json` — la última ejecución (experimentos hechos, resumen de la cola).
  - `strategies/<slug>/` — carpeta de cada estrategia: `source/` (archivo original y procedencia),
    `contract.json`, `orders_inherited.csv` u `orders_fresh.csv`, y `ciclo_NN/` por experimento con `debate/`,
    `experiment/` (proyecto, recálculo, órdenes, variantes recalculadas en `retested/`), `evaluation.json`, `entrega.json`.
  - `outbox/` — entregas de las variantes aceptadas.
  - `inbox/` — entrada manual: dejar un `.sqx` (y un `.json` opcional) y el servicio lo admite.
  - `service.lock` — cerrojo; `manual_v2_20260906.log` — intento manual de hoy (quedó `SKIPPED`, correcto).
- `/opt/SQX-headless/import/improvement_registry/<hash>.json` — registro de todo lo probado por estrategia.
- Fuentes admitidas: `/opt/SQX-headless/import/fondeo/entrega_fase5/strategies/*.sqx` (prioridad 0) y
  `/opt/SQX-headless/import/fondeo/preseleccion/*/selected/*.sqx` (prioridad 1).
- `/opt/SQX-headless/import/reviewed_improvement_jobs/active.json` — reclamación del recálculo (si existe,
  hay un recálculo en curso o pendiente de reconciliación).
- Ciclos del PC subidos hoy: `/opt/SQX-headless/import/ciclo_ew_20260906_01` … `_04`; mecanismo:
  `/opt/SQX-headless/import/mecanismo_filtros_20260906` y `_b`.

Órdenes útiles en la VPS:

```
python3 /opt/SQX-headless/import/sqx_improvement_service.py --inspect
systemctl list-timers sqx-mejora-agentes.timer
journalctl -u sqx-mejora-agentes.service --since today
cat /opt/SQX-headless/import/mejora/status.json
```

### 6.3 IA del sistema

Omnirouter de tu VPS de Oracle: `https://omniroute.143-47-35-167.sslip.io/pro/omniroute/api/v1` (la ruta
`/v1` del proxy no funciona). El motor pide los alias `ultrarentable-mejora-proponente`, `-critico` y
`-arbitro`; no existen aún en el panel y cae a `auto/best-reasoning` (hoy Gemini 3 Flash), con constancia en
`debate/log.json` de cada ciclo. El certificado sslip no está en el almacén del sistema: se degrada a
conexión sin verificar y queda anotado.

## 7. Qué no está demostrado

- Ninguna estrategia ha mejorado de forma útil para un examen de fondeo. La única variante aceptada es
  pequeña y relevante solo por el criterio Ultra.
- Ninguna validación independiente: no hay datos posteriores no consultados (@EW termina el 2025-12-31; las
  celdas de fondeo terminan el 2026-08-30 y su OOS es de desarrollo).
- Casi todas las celdas usan alias CFD en lugar de futuros reales: el cribado provisional de examen no aplica.
- Ultra: solo criterios exploratorios (no hay documento sellado de "UltraPiramidal").
- Los agentes aún no han propuesto un filtro real con el vocabulario nuevo en un ciclo del servicio; la
  variante aceptada sí usó `disable_direction`.

## 8. Decisiones que solo tú puedes tomar

1. Panel del omnirouter: definir los tres combos de mejora y reponer créditos o cambiar el destino de `auto`.
2. Datos: traer @EW de 2026 y, para las celdas de fondeo, datos de futuros reales; sin ellos nada pasa de
   candidata a validada ni entra en el cribado de examen.
3. Si el `ToImprove` de Ultra_Matrix (2 034 estrategias AUDUSD H1 con OOS de tres días) debe entrar aunque
   no sea evaluable con su partición actual (el motor podría imponer una partición propia y anotarla).
4. Si mantengo el temporizador antiguo `sqx-improvement.timer` (recetas MYM/MNQ, hoy ocioso) o lo retiro.

## 9. Avisos de hoy

- El árbol de trabajo del PC está en la rama ajena `feature/sqx-alpha-pretensiones` con 112 ficheros
  preparados por otro proceso (cambio de rama a las 17:53). Mi primer commit de la fase 4 los arrastró; lo
  deshice sin tocar su índice y desde entonces mis commits van por un worktree aparte a `motor-mejora-entrega-1`.
- Otro proceso modificó `scripts/herramientas/sqx_trade_diagnosis.py` a las 18:07 (calendario hasta la sesión
  de la tarde del último día) y lo desplegó en la VPS; lo conservé, adapté dos pruebas y lo incluí en el commit
  para que el árbol sea coherente.
- Existe un pipeline paralelo de otro proceso (`fase2_retest_e6.py` … `fase5_entrega_lote.py`, sin commit) cuya
  fase 5 entrega candidatas al motor; el servicio ya las admite con prioridad.
