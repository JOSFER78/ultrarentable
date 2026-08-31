---
id: F01
titulo: "Saneamiento del catálogo"
estado: HECHO
depende_de: ["F00"]
desbloquea: ["F03"]
verificacion_global: "Informe con el censo antes/después y la razón de descarte de cada candidato."
actualizado: "2026-08-31"
---

# FASE 1 — SANEAMIENTO DEL CATÁLOGO

El catálogo tiene 728 candidatos en ~19 combinaciones estado×motor. Hay que separar el grano de
la paja con un criterio explícito, no heredado.

## 1.1 Criterio de "base válida para ULTRA" (SELLADO — no se toca después)

Una estrategia solo entra al corpus base si cumple **todo**:

- **≥ 200 operaciones OOS.** Con 22 operaciones no hay estadística, hay anécdota.
- **PF OOS ≥ 1,25** con costes realistas (Fase 2).
- **Ratio OOS/IS ≥ 0,5**: si fuera de muestra rinde menos de la mitad que dentro, está sobreajustada.
- **Los 11 gates en PASSED**, con evidencia física en `data/evidence/<sid>/`.
- **DSR positivo** tras penalizar por el número de intentos de la campaña que la produjo.
- **Persistencia del edge entre mitades del OOS** (exigencia añadida por el hallazgo 01).

## 1.2 Reclasificación

**Estado:** PENDIENTE (ejecutable en cuanto F00 fije el árbol de validación único).

Aplicar el criterio a todos los candidatos. Los que no lo cumplan pasan a `LEGACY_NO_CERTIFICADO`
—**no se borran**, quedan como histórico. El estado `APPROVED_CURRENT_ENGINE` se vacía y se
repuebla solo con lo que sobreviva.

Casos especiales detectados el 2026-08-31:
- 120 filas `APPROVED_CURRENT_ENGINE` con `engine_version=5.5.0` y `gates_passed=0` (producidas
  por el servicio de discovery con código viejo en memoria). Por la regla #26 de la doctrina,
  ninguna certificación de motor anterior cuenta como aprobada: van a legacy/reclasificación.
- `version_manifest.json` sigue en 5.4.0 y `VERSION_HISTORY` de `services/engine_version.py`
  no tiene entradas 5.5.0/5.6.0: sincronizar al cerrar el censo.

- **Verificación:** informe con el censo antes/después y la razón de descarte de cada uno.
- **Expectativa honesta:** es probable que sobrevivan **pocos o ninguno**. Eso no es un fracaso:
  es saber de dónde partimos de verdad.

## 1.3 Cerrar la contradicción histórica

`STATE_OF_TRUTH` declaraba 230 certificadas; la gobernanza posterior dice "NO STRATEGY IS
CERTIFIED BY ASSUMPTION". Este censo la cierra con datos.

## RESULTADO (2026-08-31, ejecutado)

- **Regla #26 aplicada** (`scripts/gobernanza_regla26.py --aplicar`): las 120 filas
  `APPROVED_CURRENT_ENGINE@5.5.0` con `gates_passed=0` → `LEGACY_MOTOR_VERSION_OBSOLETA`,
  con evento de auditoría por fila en `audit_events`.
- **Censo 1.1 aplicado** (`scripts/censo_f01.py --aplicar`, informe en
  `orchestration/results/censo_f01.md`): **0 supervivientes** de 728. Los 211 estados no
  terminales (REVALIDATION_REQUIRED, INCUBADORA_REPROGRAMACION, REFINADO_TIER_2,
  IN_RESEARCH_MUTATION) → `LEGACY_NO_CERTIFICADO` con la lista de criterios incumplidos.
  Los 517 terminales conservan su etiqueta granular. c5 (DSR) y c6 (persistencia OOS) se
  aplicaron fail-closed por no ser computables desde la BD.
- **Gobernanza sincronizada:** `services/engine_version.py` (VERSION_HISTORY con 5.5.0 y 5.6.0,
  nombre y fecha), `version_manifest.json` bumped 5.4.0→5.5.0→5.6.0 por el manager oficial,
  tests `tests/test_version_governance_v540.py` reescritos a las invariantes reales
  (11/11 en verde).
- **Cifra honesta confirmada: certificadas vigentes = 0.** El corpus base para ULTRA/FONDEO se
  construye en F03 con el motor realista; el catálogo viejo es historial, no materia prima.
