# DESPACHO MULTIAGENTE — plan operativo de olas para el Orquestador (2026-09-01)

> Cómo ejecutar `PLAN_LOCAL_FONDEO.md` + `PLAN_INVESTIGACION_PROFUNDA.md` **con subagentes en
> paralelo**, ola a ola. Cada agente se despacha con el contrato del §4 de
> `DOCTRINA_ORQUESTADOR_LOCAL.md` (objetivo, territorio, entradas, aceptación, salida,
> prohibiciones). El Orquestador (Opus) NUNCA espera: entre aterrizajes trabaja su cola propia
> (§3 de la doctrina). Subagentes en Sonnet para lo mecánico; las conclusiones de los
> expedientes las firma siempre el Orquestador.

## Presupuesto de máquina (límites duros por ola)

- Máximo **4 subagentes** de código/documentación simultáneos + **2 procesos NOHUP** (backfill,
  campaña). Nada de pytest pesado en paralelo con una campaña.
- Los NOHUP se lanzan fuera del turno (`nohup ... >> log &`); un subagente solo supervisa.
- Si Emilio usa el PC: bajar a 2 subagentes + 1 NOHUP.

## Territorios (un escritor por zona, recordatorio)

`state/`+`reviews/`=ORQ · `results/`=cada agente su fichero · `services/<dominio>`=un agente
por dominio y ola · `apps/web/`=un agente · `data/`=solo procesos de datos · VPS=solo ORQ (ssh).

---

## OLA 0 — el ORQ en persona (D0, primera hora)

1. Leer los 6 documentos de arranque. 2. `W0.2` identidad del motor en el PC
(`verificacion_f02.py`, 15/15 idénticas o STOP). 3. Crear `state/VENTANA_EMILIO.md` e ir
acumulando allí todo lo que necesite a Emilio. 4. Despachar la Ola 1.

## OLA 1 — cimientos (paralela; D0)

| Agente | Contrato (resumen) | Aceptación |
| :--- | :--- | :--- |
| **AG-1 Entorno** | W0.1+W0.5: venv desde uv.lock, Node, BD local, `cola_mineria.py estado` | `python -c "import services"` OK; cola responde |
| **AG-2 Datos-rescate** | W0.4: rsync de datasets ya descargados del VPS (ES completo, NQ parcial); verificación hash==manifiesto. Sin ssh aún → arrancar W1.1 descarga directa de ES | ES 5m/15m consolidados en disco local con hash verificado |
| **AG-3 Examen-honesto** | W4.1: `fondeo_examen` decide con `reejecutar_examen_barra_a_barra()`; fail-closed | test: caso `prop_firm_busted=True` jamás imprime CUMPLE |
| **AG-4 Caza-hardcodes** | W4.2: fuera `engine_version '5.4.0'` (6 ficheros) y `except` mudos → `services/engine_version.py` + error explícito | grep limpio; fallo ruidoso verificado |
| **AG-5 Grafo-imports** (read-only) | I7 §5.1: grafo grimp/pydeps de `services/`+`scripts/` | grafo publicado en `results/grafo_imports_2026-09-01.*` |

**ORQ mientras**: contratos de la Ola 2 · spec del registro de gates (I7 mov.1) · forense de la
telemetría existente · VENTANA_EMILIO (sudo VPS sección A + claves Firebase + licencia SQX) ·
si Emilio aparece: ventana sudo por ssh y optimización corregida (§8 del informe externo).

## OLA 2 — motor de verdad (al aterrizar 1-2 y 5; D0 tarde-D1)

| Agente | Contrato | Aceptación |
| :--- | :--- | :--- |
| **AG-6 Registro-de-gates** | W4.3 = I7 movimiento 1: UNA suite (`services/validation/`) con registro plugin-style, gates versionados uno a uno; suite B a cuarentena/adaptador | test de sustitución nº1: cambiar un gate = diff de 2 ficheros; la web y el pipeline ven el MISMO veredicto |
| **AG-7 Campaña-ES** (NOHUP+supervisor) | W2.1: ES 5m+15m, perfiles `arquetipos`+`amplio`, `--dataset-source dukascopy`, telemetría por job | 0 celdas con dataset Yahoo; embudos completos en `results/telemetria/` |
| **AG-8 Backfill-resto** (NOHUP) | W1.1-W1.2: YM, GC, SI, CL, forex + completar NQ; consolidar+manifiesto+W1.3 correlación proxy | por símbolo: consolidado, hash reproducible, correlación ≥0,90 o NO APTO |
| **AG-9 I1-SQX** (investigación) | Inventario completo de SQX/QDM/QA, gap vs .cfx actual, fitness custom con proxy criterio 1.1, causa de esterilidad del Builder | expediente `reviews/investigacion_I1_sqx.md` con cada afirmación CONFIRMADA/REFUTADA + config candidata |
| **AG-10 I4-PropFirms** (investigación) | Reglas y economía 2026 firma a firma desde ToS oficiales (fecha de captura); matriz compatibilidad | expediente + `PROP_FIRM_CATALOG` propuesto con cita por parámetro |

**ORQ mientras**: auditar AG-3/4/5 · leer telemetría de ES según cae y aplicar las reglas
pre-selladas (sin_ventaja→W3 / pocas_operaciones→W1) · QA adversarial del registro de gates ·
sellar I7 cuando grafo + test nº1 estén verdes.

## OLA 3 — SQX, mejora y web (D1-D3)

| Agente | Contrato | Aceptación |
| :--- | :--- | :--- |
| **AG-11 Web-poda** | W5.1: cuarentena ~15 rutas + MotorBacktestView; Sidebar 8 entradas + "Ultra — EN CONSTRUCCIÓN" al final; `/ultra` con banner | manifiesto verificado; build sin imports rotos |
| **AG-12 Web-estrategias** | W5.2: reescritura de `/estrategias` como página maestra M1-M4 + home honesta, TODO con `docs/19_UI_STYLE_SPEC.md` | checklist de ambas specs; grep cero colores fuera de tokens |
| **AG-13 SQX-en-PC** | W3.1+W3.2 con la config candidata de I1; `[E]` si la licencia pide reactivación | Build de prueba con aceptación >0 % y databanks persistidos a disco |
| **AG-14 Parser-sqx** | W3.3 piloto: 20 de las 2.035 → AST → 11 gates | 20/20 con veredicto honesto + coste medido; luego escala en NOHUP |
| **AG-15 Improvement-esqueleto** | `services/improvement/` en frontera limpia (solo contracts + registro de gates); test de sustitución nº2 | swap de Improver por config sin tocar nada fuera |

**ORQ mientras**: censo 1.1 de la campaña ES (`censo_f01.py`) · veredicto data-vs-edge por
símbolo · si "sin_ventaja" domina: diseñar familia nueva (W3.4, estilo
`reviews/diseno_arquetipos_5_17_0.md`) y despacharla con regla #26 · preparar benchmark I2.

## OLA 4 — escala y explotación (D3+; según evidencia, no calendario)

- **Campañas** del resto de símbolos según AG-8 entregue (NOHUP rotativo, cola gobernada).
- **Benchmark I2** sobre near-misses reales (presupuesto CPU igual por sistema, holdout intacto).
- **W5.5-W5.7**: build de producción de la web en el PC + deploy + fix Firebase `[E claves]`.
- **Push a GitHub** desde el PC (W0.7 si no salió antes).
- **Vigía V0** en el VPS (SSH, tras ventana sudo): unit + informe diario a `results/vigia/`.
- Con ≥1 certificada: **M3 valoración completa** (ranking firma×estrategia×horarios con I4).
- Con ≥2: **M4 meta** (I3 → rehacer `services/meta/`) y examen F07 de la meta.

## Reglas de coordinación entre olas

1. Ningún agente arranca sin que el ORQ haya auditado lo que su territorio hereda.
2. Un agente que se atasca >30 min sin avance escribe informe parcial y devuelve el turno;
   el ORQ replanifica (nunca se queda "colgado" quemando contexto).
3. Todo aterrizaje → auditoría del ORQ con comandos propios → veredicto en el ciclo →
   checkpoint en `current_phase.md`.
4. Los commits los hace SOLO el ORQ, temáticos, tras auditar cada lote.
5. Si la telemetría o un expediente contradicen este despacho, **manda la evidencia**: se
   actualiza este fichero y `PLAN_LOCAL_FONDEO.md` en el mismo commit.
