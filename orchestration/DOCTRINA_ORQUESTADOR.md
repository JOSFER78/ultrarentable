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
