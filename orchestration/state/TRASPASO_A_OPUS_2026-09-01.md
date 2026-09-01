# TRASPASO A OPUS — todo lo hecho, dónde está y qué hacer con ello (2026-09-01)

> **ACTUALIZACIÓN 2026-09-02 — este traspaso fue EJECUTADO por Opus en los ciclos 1-2** (9 commits
> en `main`, W0.2 cerrado 15/15, I1/I4/I7 avanzados, decisiones D1-D10). Su auditoría y el plan del
> **ciclo 3 (orquestador en Orca + ≥10 agentes Antigravity atados)** están en
> **`PLAN_ORCA_ANTIGRAVITY.md`**, que es ahora el punto de entrada. Lo de abajo queda como
> histórico del arranque; varios de sus "10 hechos" ya cambiaron (sudo sin contraseña, datos
> rescatados, licencia SQX trial hasta el 05-09) — manda `current_phase.md`.

> Escrito por la sesión de análisis externa (Cowork) que auditó el proyecto completo el
> 2026-09-01. **Tú (Opus, orquestador local) ejecutas, pruebas y analizas a partir de aquí.**
> Regla de la casa aplicada a mí también: **no te fíes de este traspaso — re-verifica** cada
> afirmación con tus propios comandos antes de apoyarte en ella.

## 1. Jerarquía documental de la era local (qué manda sobre qué)

1. `orchestration/DOCTRINA_ORQUESTADOR_LOCAL.md` — tu constitución (loop no bloqueante,
   contratos de subagente, territorios, papel mínimo de Emilio). Las decisiones selladas
   §14-§18 de `DOCTRINA_ORQUESTADOR.md` siguen vigentes.
2. `orchestration/state/PLAN_INVESTIGACION_PROFUNDA.md` — investigar sin dar nada por sentado
   (I1-I7). **Manda sobre la ejecución**: sus expedientes modifican el plan.
3. `orchestration/state/PLAN_LOCAL_FONDEO.md` — la ejecución por carriles W0-W7.
4. `orchestration/state/DESPACHO_MULTIAGENTE.md` — tu plan operativo de olas: qué agente
   despachar, con qué contrato, y qué haces TÚ mientras corren.
5. `orchestration/OPERACION_LOCAL.md` — recursos y topología PC+VPS (qué corre dónde).
6. `orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md` — las 4 partes M1-M4
   (HIPÓTESIS hasta sellar I7) + ULTRA presente EN CONSTRUCCIÓN en todo.
7. `docs/19_UI_STYLE_SPEC.md` — estética de la web (grises, verde/rojo solo P&L).
8. `orchestration/HERMES_VPS_VIGIA.md` — el vigía de trades del VPS (V0→V1→V2).

Expedientes ya trabajados en `orchestration/reviews/`:
`investigacion_I5_web.md` (**CERRADO**: la web se PODA y REPARA, no se hace de cero; plan de
obra en 5 pasos) · `investigacion_I7_arquitectura_codigo.md` (**ABIERTO**: análisis preliminar
hecho; te faltan grafo de imports + 2 tests de sustitución para sellarlo).

Fuera del repo, para Emilio: `../EVALUACION_ULTRARENTABLE_2026-09-01.md` (el diagnóstico
completo del proyecto, léelo entero) y `../PLAN_AGENTES_OPUS5.md` (su guía de arranque).

## 2. Estado del proyecto en 10 hechos (verificados hoy; re-verifícalos)

1. **0 estrategias certificadas** (FONDEO y ULTRA). Censo honesto: 0 de 728. Motor 5.17.0.
2. Mandato: **SOLO FONDEO + META-FONDEO + página /estrategias**. ULTRA presente pero EN
   CONSTRUCCIÓN (`state/PUNTO_GUARDADO_ULTRA.md`), nunca borrado.
3. Causa doble del 0: futuros sin barras (Yahoo 1h insuficiente) **y** familias de señales sin
   edge (mueren en IS con datos de sobra — telemetría `results/telemetria/`, ahora persistida).
4. **El VPS sigue saturado y pendiente de sudo** (`OPERACION_VPS.md` sección A). No lances nada
   pesado allí. La optimización de Antigravity NO se ejecuta tal cual (correcciones en §8 de la
   EVALUACION: orden, /tmp, overcommit, x11-common).
5. **Los datasets pesados NO están en esta copia local** (solo manifiestos en
   `data/normalized/`). Primero rsync del VPS o re-descarga Dukascopy (W0.4/W1.1).
6. Dukascopy: ES completo en el VPS (250.009 barras 5m), NQ ~47 %, YM/GC/SI/CL/forex a cero.
7. **2.035 estrategias SQX** esperando: `data/sqx_exports/toimprove_2026-08-31.csv` + .sqx en
   el VPS. "Strategy One" = StrategyQuant X (verificado; no existe otro producto). QDM y
   QuantAnalyzer de la misma suite, sin explotar (I1).
8. Medido en código: `services/api/` es un monolito de 29.478 LOC y las DOS suites de gates
   están entrelazadas (un router importa ambas) → hoy no se puede "tocar solo las puertas";
   por eso I7 y el registro de gates (Ola 2, AG-6).
9. Deudas que bloquean certificar (W4): examen fondeo decide con bootstrap optimista;
   hardcode `5.4.0` en 6 ficheros; `gates_passed=0` no se escribe; meta-correlación fabricada.
10. Web: veredicto I5 cerrado — podar ~15 rutas, reescribir `/estrategias` (374 LOC) y la home
    contra las specs 18+19; `firebase.ts` mezcla dos proyectos (fix por `.env.local`, claves
    las pone Emilio); `git push` pendiente se hace desde el PC.

## 3. Qué ejecutar, probar y analizar (en este orden)

1. **OLA 0 del DESPACHO**: lee los docs de §1, re-verifica los hechos de §2, corre
   `scripts/verificacion_f02.py` en el PC (15/15 idénticas o STOP) y abre
   `state/VENTANA_EMILIO.md`.
2. **OLA 1**: despacha AG-1..AG-5 (entorno, datos-rescate, examen honesto, hardcodes, grafo
   de imports). Tú: contratos de Ola 2 + spec del registro de gates + forense de telemetría.
3. **OLA 2**: registro de gates (sella I7), campaña ES 5m/15m con telemetría, backfill resto,
   expedientes I1 (SQX) e I4 (prop firms).
4. **OLA 3**: web (poda + reescritura con UI spec), SQX en el PC, parser piloto, esqueleto de
   `services/improvement/`.
5. **OLA 4**: escala según evidencia (censo 1.1 manda, no el calendario).

## 4. Reglas que no se negocian (recordatorio de 1 línea cada una)

REAL-ONLY (sin dato ⇒ NO DATA) · criterio 1.1 SELLADO · regla #26 (bump+identidad) · nunca
`rm` (cuarentena+manifiesto) · telemetría siempre persistida · un escritor por territorio ·
commits solo tuyos, temáticos, tras auditar · paper/demo primero · Emilio solo: contraseñas,
claves, dinero, veto.
