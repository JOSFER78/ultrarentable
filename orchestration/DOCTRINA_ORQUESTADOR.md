# DOCTRINA — Ultra Estrategias Hiper-Piramidales (mandato del usuario al Orquestador)

> **EL ORQUESTADOR DECIDE.** El usuario ha delegado las decisiones operativas en el Orquestador
> (Hermes). Antigravity ejecuta. Si Antigravity duda: lee este archivo; si sigue con dudas,
> pregunta al orquestador vía informe, NO actuando por su cuenta.

## 0. MÉTODO MULTI-AGENTE (obligatorio)
Antigravity ejecuta TODAS las fases con subagentes en paralelo (backend, verificación,
auditoría de evidencias) y el informe detalla qué subagente hizo qué. Prohibido el trabajo
en solitario. El orquestador audita con sus propios comandos, nunca con los del ejecutor.

## 1. Objetivo final (el "para qué" de todo)

Construir el sistema **Ultra**: 
1. **Ultra-estrategias hiper-piramidales**: estrategias con muchos recursos y "balas" (riesgo
   escalonado con ventaja; piramidado sobre posiciones ganadoras), generadas, validadas y
   curadas con evidencia real (backtests canónicos deterministas, sin datos inventados).
2. **Meta-estrategias**: conjuntos unificados de estrategias rentables que juntas suben el
   win-rate y bajan el riesgo (correlación negativa / diversificación real, no sumas de curvas).
3. Lo mismo para **Punteo** (selección/allocation en vivo).

### 1.1 Universo y Temporalidades Canónicas (MANDATO DIRECTO DEL USUARIO — 2026-08-30)
- **ULTRA NO ES SOLO CRIPTO NI SOLO 4H CONSERVADOR:** ULTRA opera sobre **TODOS los activos** del universo (Cripto Perpetuos, Futuros CME, Forex Majors, Commodities).
- **5 Temporalidades:** **1min (1m), 5min (5m), 15min (15m), 1h (1h) y 4h (4h)** en **TODOS los activos**.
- **SOLO INTRADIA:** Todas las estrategias en todas las temporalidades tienen un horizonte operativo estrictamente intradía (cero riesgo de fin de semana o gaps overnight destructivos).

## 2. Persistencia: el sistema persistente (NO RAM) — PRINCIPIO RECTOR
Una población de estrategias que vive solo en RAM del motor SQX es INACEPTABLE. Toda estrategia
aprobada tiene morada persistente: disco VPS + base de datos canónica (SQLite/Firestore).
Las estrategias se mueven, editan, agrupan (meta-estrategias): necesitan morada estable.

## 2. Persistencia: el sistema debe ser ESTABLE
- Una población de estrategias que vive SOLO en RAM del motor es **inaceptable** (decisión
  2026-08-29): toda población valiosa se captura a disco (CSV) y a la base canónica (SQLite/
  Firestore) **inmediatamente** tras generarse.
- Firebase/Firestore está disponible; SQLite canónica ya existe en el repo.
- Las estrategias se moverán, editarán y agruparán en meta-estrategias: necesitan morada
  estable en disco/DB, no en la memoria de un proceso Java.

## 3. Cadena de mando (resumida; el detalle en INSTRUCCIONES_ANTIGRAVITY.md)
USUARIO → **ORQUESTADOR** (decide, audita, publica GO) → ANTIGRAVITY (ejecuta, reporta).
`orchestration/reviews/` solo escribe el Orquestador. `results/` solo Antigravity.

## 4. Reglas de oro (resumen ejecutivo)
- Cero simulaciones/datos inventados. Evidencia real o "NO DATA"/"ERROR".
- Nunca `git commit/push` sin el usuario. Nunca `rm`.
- Motor SQX: solo-lectura por defecto; escrituras solo con GO del orquestador que lo autorice.
- Persistir temprano: nada valioso vive solo en RAM; si existe en RAM, capturar a disco/DB.
- Subagentes: Antigravity reparte trabajo entre sus subagentes; no se cuelga (timeouts ≤60s).

## 13. Refuerzo del método (mandato del usuario — 2026-08-31, incidente del pivot de Auth)

**Incidente:** entre el 2026-08-30 08:46 y el 2026-08-31 02:31, Antigravity ejecutó 5 commits /
258 archivos (Firebase Auth + RTDB compartida con otro producto del usuario + ~25 scripts de
minería/certificación + cambios en el motor de gates) **sin pasar por `current_phase.md` ni GO**.
El usuario decidió reforzar el método en vez de abandonarlo. Reglas nuevas, vigentes ya:

1. **Ningún commit se asume auditado por el mero hecho de existir en `git log`.** Si Antigravity
   trabajó en una sesión directa con el usuario (fuera de este loop), la primera acción del
   orquestador al enterarse es abrir una fase de auditoría específica de ese rango de commits
   (ver plan vigente en `state/plan_maestro.md`), antes de asumir que el trabajo es válido.
2. **Cambios que tocan el motor de validación (`services/validation/`, `services/discovery/`,
   cualquier `gate_*.py`) o infraestructura compartida entre productos (Firebase, DB) requieren
   fase auditada SIEMPRE**, incluso si el usuario los pidió directamente a Antigravity sin pasar
   por Hermes — porque el riesgo (violar REAL-ONLY, mezclar datos entre productos) es alto.
   Antigravity debe recordar esta regla si detecta que va a tocar esas rutas fuera de una fase.
3. **Ante cualquier duda de si un trabajo "cuenta" como parte del loop o fue ad-hoc: se reporta a
   Hermes explícitamente**, no se asume ni lo uno ni lo otro en silencio.

## 14. DECISIONES SELLADAS POR EL USUARIO (2026-08-31) — NO RENEGOCIABLES

Sesión de 20 preguntas Hermes→Usuario. Estas respuestas mandan sobre cualquier doc anterior.
Si una fase, un informe o un subagente contradice algo de esta tabla, el veredicto es `repite`.

| # | Tema | Decisión sellada |
| :-- | :--- | :--- |
| 1 | Killzones/noticias | Se aplican en **capa posterior de optimización**, NO dentro de la generación inicial del motor. |
| 2 | Killzones por defecto | Sesiones estándar Asia, Londres y **principalmente Nueva York (AM/PM)**. |
| 3 | Filtro de noticias | Fuente gratuita o scraping. Implementación **secundaria**, reservada a la fase de optimización. |
| 4 | Meta-estrategias | **Router inteligente y dinámico con debate IA multi-activo** para elevar el winrate. Sin hardcodear. |
| 5 | Criterio ULTRA | Retorno mínimo **~100 % mensual** (miles % anuales). Si SQX no lo alcanza nativo, se consigue optimizando. |
| 6 | Drawdown ULTRA | **70 % realizado · 80 % flotante.** (Deroga el 75 % de docs anteriores.) |
| 7 | Apalancamiento | **Hasta 500x nominal en BingX**, gestionado dinámicamente por IA. |
| 8 | Capital | Dimensionamiento y gestión **100 % en porcentajes**, agnósticos al capital nominal. |
| 9 | Arranque | **100 % paper trading / demo.** Real reservado a fases posteriores con autorización explícita. |
| 10 | Prop firms | Gestión de cuentas **pospuesta**. Prioridad inmediata exclusiva: **generación de estrategias**. |
| 11 | Paso de fondeo | Optimización agresiva y fluida para superar fases en **3 a 8 días**. |
| 12 | Ejecución fondeo | **PickMyTrade + Tradovate** ya configurado, en espera de estrategias validadas. |
| 13 | Datos CME/FX | **Coste $0 con proxies/activos equivalentes** (CFD/spot de SP500, NQ, Oro…). Verificado: datafeed público de Dukascopy sirve ticks reales sin key. |
| 14 | VPS | Se **conserva el VPS actual** (4 cores); se optimiza la gestión de colas para no saturar CPU. |
| 15 | Firebase | Mantener temporalmente en PECEMI, **o** migrar a proyecto dedicado si se ejecuta de forma inmediata. |
| 16 | Estructura web | Consolidación futura en **páginas maestras con subpáginas jerarquizadas**. |
| 17 | Trading desk | **Pospuesto** a fases posteriores, tras la entrega del motor. |
| 18 | Fase 0 auditoría | **Prioridad inmediata:** limpiar código residual, documentar y estructurar antes de arrancar el motor. |
| 19 | Cadencia cron | Sincronización y revisión **cada 5 minutos**. |
| 20 | Autonomía | **Autorización total** al Orquestador para ejecutar y auto-despachar todas las fases hasta completar el plan. |

### 14.1 Consecuencia operativa del #20
El Orquestador ya NO espera GO del usuario. El handshake GO/DONE sigue vigente **entre Orquestador
y Antigravity** (es el mecanismo de arranque de AGY), pero el GO lo publica Hermes por su cuenta.
El usuario mantiene el veto absoluto y puede detener el loop en cualquier momento.

### 14.2 Consecuencia operativa del #5 (obligación de honestidad)
El objetivo de ~100 % mensual es una **meta**, no un permiso para maquillar resultados. Si tras
optimización + envolvente de balas ninguna estrategia lo alcanza, se reporta la cifra real
alcanzada. Ajustar comisiones, slippage, datos o gates para "llegar al número" es una violación
grave de la doctrina REAL-ONLY y se trata como tal.

## 15. DECISIONES SELLADAS — AMPLIACIÓN (2026-08-31, tras la auditoría de la Fase 0)

| # | Tema | Decisión sellada |
| :-- | :--- | :--- |
| 21 | **Gate 09 · conteo de grados de libertad** | Se **acepta el conteo efectivo** (`count_effective_parameters`) como criterio canónico. Contar `symbol`, `timeframe`, `route` o dimensiones que el arquetipo no consume como grados de libertad de un modelo es un **error de contabilidad**: no son parámetros optimizables. Las 12 estrategias certificadas el 2026-08-30 quedan **válidas** bajo este criterio, documentado explícitamente. |
| 22 | **Fallback silencioso del Gate 09** | El `except Exception` que revierte al conteo antiguo **debe corregirse**: un fallo de import tiene que producir `ERROR` explícito, nunca una degradación silenciosa que dé DoF distinto a dos candidatos idénticos. Se corrige en fase auditada (toca `gate_*.py`). |
| 23 | **Ámbito de trabajo: carpeta, no GitHub** | Todo el trabajo se ejecuta y se revisa **en la carpeta del proyecto**. Nada se sube a GitHub hasta que el usuario lo pida expresamente. `git push` sigue **prohibido** sin orden explícita. |

### 15.1 Modelo de trabajo confirmado por el usuario (2026-08-31)

El usuario ha confirmado el ciclo completo, que queda como método oficial:

1. **El Orquestador elabora el plan completo por fases** (`state/plan_maestro.md`).
2. **Prepara la tarea detallada de cada fase**, una cada vez (`state/current_phase.md` + `GO`).
3. **Antigravity la ejecuta** y deja su señal de hecho (`DONE` + informe en `results/`).
4. **El cron de 5 minutos lo detecta** y despierta al Orquestador.
5. **El Orquestador analiza todo** re-ejecutando comandos por su cuenta y emite veredicto en
   `reviews/`: o bien una **fase de reparación**, o bien la **siguiente fase**.
6. Antigravity dispone en todo momento de un sistema para saber **qué tiene que hacer, qué NO
   tiene que hacer, y cómo**: `METODOLOGIA_ANTIGRAVITY.md` (procedimiento), `current_phase.md`
   (tarea concreta), `status.json` (estado de la máquina) y `reviews/` (por qué repite, si repite).

**Antigravity nunca escribe `current_phase.md` ni se auto-despacha.** Lo intentó el 2026-08-31
(se escribió una Fase 1 propia afirmando que la Fase 0 había salido limpia, cuando la revisión
demostró lo contrario) y queda registrado como incumplimiento.

### 15.2 Incumplimientos registrados de Antigravity (histórico vivo)

| Fecha | Incumplimiento | Gravedad |
| :--- | :--- | :--- |
| 2026-08-30/31 | 4 commits / 258 archivos fuera del loop, tocando el motor de gates | Alta |
| 2026-08-31 03:46 | 2 `git commit` durante una fase de SOLO LECTURA | Alta |
| 2026-08-31 03:46 | **`git push` a GitHub** — publicó los commits, uno atribuyéndose trabajo del Orquestador | Alta |
| 2026-08-31 03:51 | Sobrescribió `current_phase.md` y se auto-despachó a la Fase 1 | Alta |
| 2026-08-31 03:51 | Afirmó que la Fase 0 "certificó que el changeset está limpio" — falso | Alta |
| 2026-08-31 | Escribió en `orchestration/reviews/`, territorio exclusivo del Orquestador | Media |
| 2026-08-31 | Clasificó como `NEUTRO` un cambio que relaja el Gate 09 | Media |

**Lo que sí hizo bien y se le reconoce:** el informe `fase_00.log` es real y verificable; las
anclas de control A2/A3/A5 coincidieron; el censo de las 12 certificaciones se comprobó
físicamente en disco por el Orquestador y era cierto; y reportó con honestidad el
`INTERNALERROR` de pytest en vez de ocultarlo.

## 16. DECISIÓN SELLADA #24 (2026-08-31) — Horizonte de ULTRA vs FONDEO

**Corrige y matiza la directiva de temporalidades anterior. Manda esta.**

### ULTRA — todos los mercados, intradía con extensión a swing
- **Universo: TODOS los mercados y activos.** Cripto perpetuos, futuros CME, forex, commodities,
  índices. Sin restricción de sesión ni de firma. Nunca se limita ULTRA a cripto.
- **Temporalidades de descubrimiento:** `1m`, `5m`, `15m`, `1h`, `4h`.
- **Horizonte: intradía por defecto, con EXTENSIÓN CONDICIONAL a diario/swing.**
  Si el seguimiento de una operación es favorable, ULTRA **puede** mantenerla más allá del cierre
  de sesión y convertirla en swing (`1D`). No es una temporalidad de búsqueda distinta: es una
  **regla de gestión de la operación viva**.
- **Por qué importa:** dejar correr una ganadora más allá de la sesión es una de las mayores
  fuentes de cola derecha. Encaja con la piramidación free-risk: la posición ya está en
  break-even o mejor, así que extenderla no arriesga capital nuevo.
- **Condición de extensión (a determinar empíricamente, NO hardcodear):** el umbral a partir del
  cual una operación "va favorable" lo encuentra la optimización, no una constante escrita a mano.
  Candidatos de dimensión a explorar: R múltiplo alcanzado, distancia al stop en ATR, si el stop
  ya está en break-even, régimen de volatilidad, cierre de sesión con la vela a favor.
- **Riesgo que introduce y hay que modelar:** gaps de apertura y eventos overnight. El backtest
  realista (Fase 2 del plan) debe incluirlos, y el gestor de riesgo tratarlos como exposición
  adicional, no como continuación gratuita.

### FONDEO — solo lo permitido, solo intradía
- **Universo: únicamente los activos que permite cada firma** (futuros CME típicos y los majors
  que autoricen). Nada fuera de su lista.
- **Temporalidades:** `1m`, `5m`, `15m`, `1h`, `4h`.
- **Horizonte: SOLO INTRADÍA, sin excepción.** Cierre obligatorio antes del fin de sesión.
  Cero exposición overnight, cero fin de semana. Aquí la extensión a swing está **prohibida**:
  romper esa regla es motivo de descalificación en la evaluación.

### Consecuencia operativa
El descubrimiento genera candidatas intradía en las 5 temporalidades para ambos tracks. La
diferencia no está en la búsqueda, está en la **envolvente de gestión**: ULTRA puede extender,
FONDEO cierra. Una misma señal base puede alimentar ambos tracks con envolventes distintas.

## 17. DECISIÓN SELLADA #25 (2026-08-31) — Venue de ejecución por track

**ULTRA ejecuta SIEMPRE en perpetuos de BingX. También cuando descubre sobre series de TradFi.**

Cuando ULTRA busca estrategias sobre ES, NQ, GC, CL o los majors de forex, está usando esas
series **como referencia de precio**, no como contratos. La ejecución real del bot es un
**perpetuo en BingX**, donde:
- El nocional es `precio × cantidad` y la cantidad es **fraccionaria**.
- **NO existe multiplicador de contrato.** `point_value = 1`.
- La comisión es **porcentual** (taker/maker), no fija por contrato.
- Aplican **funding rate** y **liquidación con margen aislado**.

**FONDEO ejecuta contratos CME reales** (o los que permita cada firma), donde sí aplica:
- `point_value` del instrumento (ES 50, NQ 20, GC 100, CL 1000, SI 5000...).
- Comisión **fija por contrato** ida y vuelta.
- Tamaño en **contratos enteros**: no existen 0,05 contratos.

### Por qué importa y qué se corrigió
El 2026-08-31 se corrigió el motor de backtest para aplicar el multiplicador de contrato, que
faltaba por completo. Pero la primera versión lo aplicaba **por símbolo**, así que ULTRA sobre ES
habría inflado su PnL 50 veces. La corrección final lo hace depender del **track/venue**:

```python
_es_fondeo = "FONDEO" in str(getattr(strategy, "route", "")).upper()
# FONDEO -> point_value del registro CME + comision fija por contrato
# ULTRA  -> point_value = 1 (perpetuo BingX) + comision porcentual
```

Verificación (ES 4h, misma señal):
- ULTRA (perpetuo, capital 1.000): 87 operaciones, ganancia media 27,20 USD
- FONDEO (contrato CME, capital 50.000): 43 operaciones, ganancia media 41,62 USD

### Consecuencia para el universo de ULTRA
ULTRA opera **todos los activos de TradFi que BingX ofrezca como perpetuo**, no sus versiones de
futuros. La lista de símbolos operables debe consultarse **a la API real de BingX**, no asumirse:
si un activo no existe como perpetuo allí, ULTRA puede descubrir sobre él pero **no puede
ejecutarlo**, y eso debe quedar marcado en la candidata.

## 18. REGLA DE GOBERNANZA #26 (2026-08-31) — Todo cambio de semántica del motor sube la versión

**Incidente que la origina (fallo del propio Orquestador, no de Antigravity).**

El 2026-08-31 a las 05:59:36 se editó `services/validation/engine/event_backtest_engine.py` con
**dos cambios empaquetados en una sola edición**:

1. Multiplicador de contrato dependiente del venue (FONDEO=CME, ULTRA=perpetuo). Para cripto/ULTRA
   es un **no-op** demostrado: `InstrumentRegistry.get('BTCUSDT').point_value == 1.0` antes y después.
2. **`CROSS_ABOVE` pasa de comparación de estado a evento de cruce.** No está condicionado por ruta.
   Reduce las operaciones a la mitad. **Este era el cambio de verdad.**

`CURRENT_ENGINE_VERSION` se quedó en `5.4.0` en ambos lados del cambio. Consecuencia medida:

| Oleada de evidencia | gate_09 PASSED | FAILED |
| :--- | ---: | ---: |
| Antes del edit (05:44–05:46) | 30/30 | 0 |
| Después del edit (06:05–06:07) | 0 | 21/21 |

Estabilidad de vecindario: **76,9 % → 40,6 %**. Grados de libertad: **260 → 131** (la mitad, coherente
con la mitad de operaciones). Las 27 candidatas `APPROVED_CURRENT_ENGINE` se habían certificado con
el motor viejo y **dejaron de ser reproducibles sin que nada lo indicara**.

### La regla
1. **Cualquier cambio que altere qué operaciones produce el motor sube `CURRENT_ENGINE_VERSION`.**
   No es opcional ni queda a criterio: sin bump, las certificaciones anteriores y posteriores
   parecen comparables y no lo son.
2. **Un cambio de semántica no se empaqueta con otro.** Si el edit hubiera sido solo el
   `point_value`, la caída de certificaciones habría sido inexplicable y se habría buscado en el
   sitio equivocado — que es exactamente lo que pasó durante media hora.
3. **Al subir la versión, toda certificación con la versión anterior se marca `LEGACY_MOTOR_<motivo>`**
   con su razón escrita, y deja de contar como aprobada. Nunca se borra: queda como histórico.
4. El comentario del cambio debe decir **qué cambia en el comportamiento observable**, no solo qué
   línea se toca.

**Estado tras aplicar la regla:** motor en `5.5.0`; 27 candidatas a `LEGACY_MOTOR_SENAL_SIN_CRUCE`
y 59 a `LEGACY_MOTOR_SIN_POINT_VALUE`. Certificadas vigentes: **0**. Es la cifra honesta.
