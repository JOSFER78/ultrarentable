# Ultra / "UltraPiramidal": qué dicen los documentos del repositorio

Recuperación documental de solo lectura, 2026-09-06, hecha para el motor de mejora. No inventa
criterios: cuando un umbral no aparece en un documento vigente, se dice.

## 1. Definición operativa y vigencia de cada fuente

El término literal "UltraPiramidal" no aparece en ningún fichero del repositorio. Lo más cercano es
el título de `orchestration/DOCTRINA_ORQUESTADOR.md` ("Ultra Estrategias Hiper-Piramidales") y la
cadena "Hiperpiramidación Free-Risk" en un documento archivado y un módulo en cuarentena.

| Fuente | Fecha | Estado | Qué aporta |
| --- | --- | --- | --- |
| `docs/00_MASTER_IDEAS_Y_PLAN.md` §1 | 2026-08-29 (commit 2026-08-31) | Fuente única declarada | Tabla TRACK_ULTRA vs TRACK_FONDEO: objetivo "crecimiento asimétrico/convexo", DD flotante ~80 % y realizado ~75 %, bala 1R (100–1 000 $), balas y estados + bóveda ratchet 50–85 %, métrica reina "payoff ≥ 3R–10R". |
| `orchestration/DOCTRINA_ORQUESTADOR.md` | 2026-08-30/31 | Vigente ("no renegociable") | "Estrategias con muchos recursos y 'balas' (riesgo escalonado con ventaja; piramidado sobre posiciones ganadoras)". Decisiones #5–#9, #24, #25. |
| `orchestration/state/PUNTO_GUARDADO_ULTRA.md` y `orchestration/README.md` | 2026-09-01 | Vigente: **ULTRA APARCADO** | "La convexidad de los miles de % es una propiedad de la gestión de capital, no de la señal. Simplemente no es el trabajo de ahora". Se retoma cuando FONDEO tenga estrategias certificadas. |
| `orchestration/state/archive/bloques_v4_2026-09-05/F05_envolvente_ultra.md` | 2026-09-01, archivado 2026-09-05 | Archivado | Máquina de estados, piramidación free-risk (BE tras +1,5R), reciclaje, bóveda 50–85 %, verificación por mediana/p5/p95/P(ruina). |
| `docs/Gestion de Capital — Balas y Estados.md` | 2026-08-03 | Diseño "pendiente de simulación" | Seis estados INICIO→CONFIRMACIÓN→CRECIMIENTO→COSECHA→PROTECCIÓN→CIERRE; "el dinero cosechado es intocable". Sin números. |
| `docs/Laboratorio/05_GESTION_DINAMICA_Y_PROTECCION.md` | 2026-08-15 | Referencia | Ratchet adaptativo (2x→50 %, 3x→65 %, 5x→75 %), "parámetros experimentales, no reglas finales". |
| `docs/archive/root/SPEC_MASTER_ULTRA_VS_FONDEO.md`, `SYSTEM_DOCTRINE.md` | — | Sustituidos el 2026-08-29 | Únicos lugares con umbrales R por estado (+1,0/1,5R BE; +2–3R piramidar 40 %; +3R cosecha; SL free-risk ≥ +0,5R) y gates Ultra 8–11. |
| `docs/OBJETIVO_ESTRATEGIAS_20260905.md` | 2026-09-05 | Dirección vigente | Solo fondeo (exámenes ≤ 1 semana); no menciona Ultra. |

Definición consolidada con lo vigente: Ultra es una **envolvente de gestión de capital** aplicada sobre
una señal base ya validada, no una familia de señales: balas aisladas con riesgo 1R sellado,
piramidación solo sobre ganadoras financiada con beneficio flotante, extensión condicional a swing y
cosecha irrevocable a bóveda. Doctrina §16: "una misma señal base puede alimentar ambos tracks;
ULTRA puede extender, FONDEO cierra".

## 2. Qué comportamiento necesita de una estrategia

- Activos: todos (cripto perpetuos, CME, forex, materias primas, índices); ejecución en perpetuos BingX.
- Temporalidades de descubrimiento: 1m, 5m, 15m, 1h, 4h; `PUNTO_GUARDADO_ULTRA` descarta 1m por falta de barras y sitúa el óptimo en 15m.
- Horizonte: intradía por defecto, con extensión condicional a swing como regla de gestión de la operación viva; el umbral "va favorable" está explícitamente "a determinar empíricamente, NO hardcodear" (dimensiones: R alcanzado, distancia al stop en ATR, stop en break-even, régimen de volatilidad, cierre de sesión a favor). Exige modelar gaps.
- Entradas y salidas: sin requisito de forma; la base debe ser "materia prima legítima" que pase el criterio 1.1 y después alcance el objetivo con la envolvente ("ojo al orden causal").
- Tamaño: "100 % en porcentajes, agnóstico al capital nominal".

## 3. Criterios cuantitativos realmente definidos

Sellados en la doctrina (2026-08-31): retorno ~100 % mensual verificado sobre la mediana de la envolvente con p5/p95/P(ruina); DD 70 % realizado y 80 % flotante (deroga el 75 % anterior); apalancamiento hasta 500x con el tope real del exchange.

Definidos solo en código, sin refrendo documental vigente (`contracts/validation_contracts.py`, `UltraValidationCriteria`): payoff ≥ 2,5; E[R] por bala ≥ 0,20R; cola ≥ 3R con ≥ 40 % del beneficio; asimetría ≥ 0,50; tasa de cosecha OOS ≥ 10 %; P(ruina de ráfaga de 10 balas) ≤ 25 %; DD realizado ≤ 75 % (contradice el 70 % sellado). Gate 03 Ultra: ≥ 15 IS / ≥ 10 OOS operaciones y outliers top-2 ≤ 85 %.

Pendientes o experimentales: umbral de extensión a swing, porcentajes del ratchet, todo el diseño de balas y estados, y "el criterio 1.1 mide robustez pero no rentabilidad".

## 4. Lo que está sin definir y la pregunta mínima

1. Qué significa "mejorada" para Ultra (¿mejora la señal desnuda o el conjunto señal × envolvente?).
2. Umbrales R de los estados de la bala: solo existen en documentos sustituidos y en `ultra_engine.py` (2026-08-18). ¿Siguen vigentes?
3. Conflicto 70 % vs 75 % de DD realizado entre doctrina y código.
4. Umbral de extensión a swing: ¿se explora ya o queda fuera hasta retomar Ultra?
5. Payoff mínimo: 3R (plan maestro), 2,5 (código) o 3,0 (pruebas).
6. ¿"En construcción" significa reactivar Ultra ahora o solo no cerrar puertas? El estado vigente dice aparcado.
7. El motor propio de backtest no registra MAE ni MFE por operación (`TradeRecord`); SQX sí los exporta, y es lo que usa el ciclo de mejora.

## 5. Qué mide el ciclo de mejora para Ultra, y por qué es exploratorio

Se calculan desde las órdenes nativas de SQX: múltiplos R respecto al riesgo inicial (distancia al stop × valor del punto), E[R], payoff en R, cuota de beneficio de operaciones ≥ 3R, asimetría, fracción de operaciones con MFE ≥ 1R/2R/3R y dependencia de los mejores tres resultados. Coinciden con la "métrica reina" del plan maestro y con las dimensiones que la doctrina pide explorar. No se aplica ningún umbral como veredicto: no hay ninguno sellado. Y no se traslada el criterio de fondeo (DD ≤ 4 %, cierre al final del día) a Ultra, que lo prohíbe expresamente.
