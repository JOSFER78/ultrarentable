# PLAN MAESTRO — v2 (2026-08-31) — Auditoría del pivot de Auth + Saneamiento

> **Sustituye** a `archive/plan_maestro_2026-08-29_motor_sqx.md` (motor SQX/semillero — su Fase 0-4
> quedó ejecutada según `status.json.history`; se archiva sin borrar, doctrina "nunca borrar").
> **Motivo del plan nuevo:** entre el 2026-08-30 08:46 y el 2026-08-31 02:31, Antigravity ejecutó
> 5 commits / 258 archivos / +28.748 líneas (Firebase Auth + RTDB + ~25 scripts `mine_and_certify_*`
> + cambios en el motor de validación/gates) **fuera del loop formal** (sin `current_phase.md`, sin
> GO, sin review). El usuario confirmó: (1) la RTDB compartida con PECEMI (`pecemi-default-rtdb`)
> **no debe compartirse** — hay que separarla; (2) el changeset de 258 archivos se **audita primero**;
> (3) el método Hermes↔Antigravity **se refuerza** (ver `DOCTRINA_ORQUESTADOR.md §13`).

Doctrina transversal (invariante, de `.agents/AGENTS.md` + `DOCTRINA_ORQUESTADOR.md`): REAL-ONLY /
ZERO-MOCKS · cero datos inventados · **sin `git commit`/`git push` automático** · nunca `rm`.

---

## Fase 0 — Auditoría del changeset 258-archivos (2026-08-30 08:46 → 2026-08-31 02:31)

- **Objetivo:** verificar que el trabajo hecho fuera del loop (auth Firebase + ~25 scripts
  `mine_and_certify_*` + cambios en `event_backtest_engine.py`, `gate_09_novelty_antifit.py`,
  `discovery_validation_pipeline.py`, `strategy_search_registry.py`) **no violó la doctrina
  REAL-ONLY / 11 gates** ni introdujo mocks, datos fabricados o atajos de certificación.
- **Rango exacto a auditar:** `git diff 23c8733a9..245009fef` (5 commits, ver lista completa en
  `git log 23c8733a9..245009fef --oneline`).
- **Criterio de éxito verificable:**
  - [ ] Cada script nuevo `mine_and_certify_*` (25 archivos en `scripts/`) revisado: cero
        `random`/`seed`/datos sintéticos usados como si fueran reales; cualquier certificación que
        haya producido tiene sus 11 `EvidenceRecord` reales en `data/evidence/<sid>/gate_*.json`.
  - [ ] Diff de `gate_09_novelty_antifit.py`, `event_backtest_engine.py` (+255/-?),
        `discovery_validation_pipeline.py` (+114/-?) revisado línea a línea: ¿cambia el criterio de
        aprobación de algún gate? ¿en qué dirección (más estricto/más laxo)? Documentar explícito.
  - [ ] `pytest tests/ -q` corre limpio (0 collection errors) tras el changeset.
  - [ ] Cualquier estrategia certificada por estos scripts nuevos entre el 30-ago y hoy: listar
        `strategy_id` + sello SHA-256 + fecha, para que el usuario decida si se revalida.
  - [ ] Veredicto explícito: `LIMPIO` (no hay violación) | `VIOLACIÓN DETECTADA` (detallar cuál,
        dónde, y candidatas/certificaciones afectadas) | `NO_EVIDENCE` si algo no se puede verificar.
- **Reglas:** solo lectura/auditoría — prohibido modificar estos archivos en esta fase; si se
  encuentra una violación, se documenta y se abre una fase de corrección aparte con GO explícito.
- **Dependencias:** ninguna. Es la primera fase porque toca el corazón de la certificación (11 gates).
- **Estado:** preparada, **esperando GO del usuario** (no se dispatcha sola).

## Fase 1 — Separar la Firebase RTDB de Ultrarentable de la de PECEMI

- **Objetivo:** Ultrarentable deja de usar `pecemi-default-rtdb`; se aprovisiona una instancia
  Realtime Database propia bajo el proyecto Firebase `traderbot-josfer` (o uno dedicado si el
  usuario lo prefiere), se migran las reglas de seguridad y los nodos de usuarios/autorización
  actuales, y se elimina el fallback de `apiKey` hardcodeado en el código cliente (debe venir
  **solo** de variable de entorno, fallo explícito si falta — no un valor por defecto silencioso).
- **Criterio de éxito verificable:**
  - [ ] Nueva instancia RTDB creada y referenciada en `.env`/config (sin URL de `pecemi-default-rtdb`
        en ningún archivo de Ultrarentable).
  - [ ] `apiKey`, `databaseURL` y demás config de Firebase leídos exclusivamente de
        `process.env.*` — cero strings hardcodeados como fallback (grep de `AIzaSy` en el repo = 0
        resultados fuera de `.env*`).
  - [ ] Datos/usuarios existentes migrados con evidencia (conteo antes/después, sin pérdidas).
  - [ ] Login real end-to-end probado contra la nueva instancia (evidencia: captura/log de sesión
        real, no mock).
  - [ ] `rules.json` de la nueva RTDB documentado y commiteado (working tree) — reglas explícitas,
        no `.read: true / .write: true` abiertas.
- **Dependencias:** ninguna técnica; puede correr en paralelo a la Fase 0 (no toca el motor de
  validación). Requiere GO del usuario porque toca infraestructura Firebase compartida entre productos.
- **Estado:** preparada, esperando GO.

## Fase 2 — Resolver decisiones de negocio bloqueantes (SSOT §5)

- **Objetivo:** de las 7 decisiones abiertas en `docs/00_MASTER_IDEAS_Y_PLAN.md §5`, resolver con
  el usuario al menos las que bloquean avance técnico real: puerto web canónico (3000 vs 3005),
  destino del catálogo heredado (230 estrategias "certificadas" v5.4.0 vs regla "NO STRATEGY IS
  CERTIFIED BY ASSUMPTION"), y fuente de datos 5m CME/forex (pagar/reducir matriz/otra vía).
- **Criterio de éxito verificable:** cada decisión resuelta queda escrita en el propio §5 del SSOT
  con fecha y decisión explícita del usuario (no del agente).
- **Dependencias:** ninguna técnica — es conversación con el usuario, no ejecución de Antigravity.
- **Estado:** pendiente de agenda con el usuario (no es una fase para Antigravity).

## Fase 3 — Actualizar el SSOT con el estado real post-auditoría

- **Objetivo:** una vez cerradas Fases 0-2, actualizar `docs/00_MASTER_IDEAS_Y_PLAN.md` (único
  documento que se edita para reflejar realidad, por su propia regla de mantenimiento) incorporando:
  el pivot de Auth/RTDB ya gobernado, el veredicto de la auditoría del changeset, y las decisiones
  §5 resueltas.
- **Criterio de éxito verificable:** el SSOT no contiene ninguna afirmación que contradiga el
  estado físico verificado (puertos, servicios, certificaciones reales).
- **Dependencias:** Fases 0, 1 y 2.

## Fase 4 — Saneamiento general de organización

- **Objetivo:** limpieza de bajo riesgo, sin tocar motor ni datos:
  - `docs/ahorrotokens y orquestacion/`: mantener el doc de arquitectura como referencia (ya
    superado en la práctica por este `orchestration/`); **no instalar** el kit zip en este VPS —
    ya está superado por `~/.claude/settings.json` real (tiene hooks de seguridad + auto-fix ruff
    que el kit no trae; instalarlo sería un downgrade).
  - Consolidar los ~20 `.md` sueltos en `docs/` raíz según el índice de vigencia que ya define el
    propio SSOT §6 (mover los `SUPERSEDED` no listados aún a `docs/archive/`, sin borrar nada).
  - `.agents/informe&seguimiento/` (100+ ficheros de handoffs/reviews históricos): evaluar archivar
    los completados (con veredicto ya cerrado) a un subdirectorio `historico/`, dejar activos solo
    los abiertos.
- **Criterio de éxito verificable:** raíz del repo y `docs/` con solo documentos vigentes visibles
  a primer golpe de vista; nada borrado, todo trazable en `git mv`.
- **Dependencias:** ninguna dura; puede ir en paralelo, pero es la de menor prioridad.

---

## Reglas transversales (reforzadas — ver DOCTRINA_ORQUESTADOR.md §13)

1. Ninguna fase se dispatcha a Antigravity sin `GO` explícito del orquestador con el hash de
   `current_phase.md` (protocolo ya definido en `INSTRUCCIONES_ANTIGRAVITY.md`).
2. Cualquier trabajo que Antigravity haga **fuera** de este loop (sesión directa del usuario) debe
   reportarse a Hermes en la primera interacción siguiente — no se asume auditado solo por existir
   en `git log`.
3. Sin `git commit`/`git push` automático. Sin `rm`. Cero datos inventados.
4. 2-3 veredictos `repite` seguidos sobre la misma fase ⇒ `needs_user_input` automático.
