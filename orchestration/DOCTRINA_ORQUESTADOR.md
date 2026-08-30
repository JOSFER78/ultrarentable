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
