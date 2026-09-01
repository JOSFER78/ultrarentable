# `orchestration/` — dónde está cada cosa

Punto de entrada. Si sólo vas a leer un fichero de este directorio, que sea
`state/current_phase.md`.

## MANDATO ACTIVO — SOLO FONDEO

**El 100 % del trabajo va a FONDEO (futuros CME para prop firms) y a sus META-ESTRATEGIAS.**
Orden de Emilio del 2026-09-01.

**ULTRA y META-ULTRA quedan APARCADOS para próximamente.** Aparcado no es abandonado, y no es lo
mismo que pendiente:

- El estado completo de ULTRA está congelado en **`state/PUNTO_GUARDADO_ULTRA.md`**: lo hecho, lo
  que faltaba y por dónde se retoma.
- Las fases **F05** (envolvente ULTRA, el motor de balas) y **F06** (router de meta-estrategias
  ULTRA) conservan su contenido íntegro y llevan `aparcado: true` en su cabecera YAML. La web las
  pinta atenuadas con la etiqueta APARCADO, para que no se confundan con las fases del camino
  crítico.
- Su tesis sigue sellada y válida: la convexidad de los miles de % es una propiedad de la gestión
  de capital, no de la señal. Simplemente no es el trabajo de ahora.

Se retoma ULTRA cuando FONDEO tenga estrategias certificadas bajo el Criterio 1.1.

## Mapa del directorio

| Ruta | Qué es |
| :--- | :--- |
| **`OPERACION_VPS.md`** | **SSOT de recursos de la máquina. Leer ANTES de lanzar nada.** Por qué se colapsó tres veces, el mecanismo de turno único, y los comandos con sudo que sólo puede ejecutar Emilio |
| `ops/systemd/` | Drop-ins correctivos de systemd, listos para instalar con los comandos de `OPERACION_VPS.md` |
| **`state/current_phase.md`** | **La foto actual**: qué se hizo, con qué evidencia, y qué deuda queda abierta |
| `state/plan_maestro.md` | Índice del plan: tesis + tabla de estados. **No es la fuente de verdad de las fases** |
| **`state/plan/bloques/Fxx_*.md`** | **Fuente de verdad de cada fase.** Un fichero por fase con cabecera YAML. Al avanzar una fase se edita SU bloque y se refleja la fila del índice |
| `state/plan/bloques/REGLAS_INVARIANTES.md` | Las reglas selladas que no se relajan |
| `state/plan/bloques/RIESGOS.md` | Lo que puede salir mal y cómo se detecta |
| `state/PUNTO_GUARDADO_ULTRA.md` | Estado congelado del carril ULTRA |
| `state/archive/` | Planes sustituidos. **Nunca se borran**, se archivan |
| `results/` | Evidencia e informes con fecha: verificaciones del motor, forenses de campaña, viabilidad de carriles |
| `reviews/` | Diseños y revisiones técnicas (arquetipos, decisiones de motor) |
| `logs/` | Salida de servicios y campañas |

## Cómo se actualiza esto

1. Se edita **el bloque de la fase**, no el plan entero. Nunca se crean planes paralelos.
2. Se refleja la fila correspondiente en el índice `state/plan_maestro.md`.
3. Lo sustituido va a `state/archive/`, con manifiesto si procede. **Nunca se borra nada.**
4. La web (`/plan`) lee los bloques en vivo vía `/api/plan`: no hay que duplicar estados a mano,
   y si un bloque y la web discrepan, manda el bloque.

## Reglas invariantes, en una línea cada una

- **REAL-ONLY / zero-mocks**: nada sintético. Toda afirmación, con evidencia en disco y SHA-256.
- **Criterio 1.1 SELLADO**: ≥200 operaciones OOS, PF OOS ≥1,25, OOS/IS ≥0,5, 11 gates con
  evidencia, DSR positivo y persistencia por mitades OOS. No se relaja.
- **Regla #26**: todo cambio que altere las operaciones del motor sube `CURRENT_ENGINE_VERSION` y
  se verifica con `scripts/verificacion_f02.py` (15 celdas de referencia idénticas).
- **Nunca `rm`**: todo a `cuarentena/` con manifiesto SHA-256.
- **Un solo trabajo pesado a la vez**, a través de `services/ops/gobernanza_recursos.py`.
