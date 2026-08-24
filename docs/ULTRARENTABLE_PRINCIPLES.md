# ULTRARENTABLE — PRINCIPIOS DEL SISTEMA

Documento obligatorio para humanos y agentes. Cualquier cambio que viole estos
principios debe considerarse un bug, independientemente de que compile o funcione.

Guardia automática: `python3 tests/test_zero_mocks.py` falla si reaparecen datos
falsos o patrones prohibidos.

---

## Los 15 principios

1. **ZERO MOCKS** — Nada de mocks, fakes ni simulaciones presentadas como reales.
2. **ZERO SYNTHETIC DATA** — Sin velas, curvas o trails sintéticos. Si el dataset
   está vacío, el backtest se cancela con `NO_DATA` (ver `services/backtest/fast_engine_adapter.py`).
3. **ZERO INVENTIONS** — Ninguna métrica, estado, contador o veredicto se inventa.
   El profit factor sin pérdidas se reporta como `null`, no como 99.0.
4. **ONE SOURCE OF TRUTH** — Cada entidad tiene UN sitio donde vive y manda.
   Hoy: SQLite WAL (`/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3`)
   es la fuente primaria; Firebase RTDB es réplica de solo-escritura (push one-way).
5. **IMMUTABLE STRATEGY VERSIONS** — Una estrategia certificada nunca se muta en
   silencio: cualquier refinamiento genera una versión nueva (`v1 → v2`).
   La FSM canónica vive en `contracts/canonical_strategy.py` + `services/validation/candidate_registry.py`.
6. **REAL EVIDENCE ONLY** — La evidencia (`data/evidence/...`) es la única base de
   certificación. `NO EVIDENCE → NO CERTIFICATION`.
7. **NO FORCED PASS** — Un gate sin datos NO se considera superado. El guarda de
   aprobación excluye candidatos sin DD/PF medidos (`apps/web/app/gates/page.tsx`).
8. **NO SILENT FALLBACKS** — Backend caído → la UI muestra `N/D`, nunca la última
   cifra ni un valor por defecto. Los `catch` silenciosos deben loguear.
9. **NO DUPLICATED BUSINESS LOGIC** — La clasificación TIER/estado/aprobación se
   calcula en un único sitio del dominio; las páginas presentan.
10. **SAME ENTITY = SAME STATE EVERYWHERE** — Catálogo, candidatos, gates,
    investigación, aprobadas y portfolio muestran la MISMA entidad con el MISMO estado.
11. **BACKEND IS AUTHORITATIVE FOR DOMAIN STATE** — La UI jamás deriva estados
    críticos por su cuenta ni se convierte en fuente de verdad.
12. **UI NEVER INVENTS DATA** — `NO DATA → UNKNOWN / N/A / NO DATA`. Prohibido
    `valor || inventado` para métricas.
13. **CERTIFICATION MUST BE EVIDENCE-GATED** — Aprobada ≠ `gates_passed == N` por
    sí solo: requiere el estado canónico CERTIFIED respaldado por evidencia
    (`services/validation/certification_registry.py`, TOTAL_REQUIRED_GATES = 11).
14. **EVERY MATERIAL CHANGE MUST BE TRACEABLE** — Todo resultado material lleva
    provenance (hash de motor+datos+costes+parámetros; ver `fast_engine_adapter.py`).
15. **REPRODUCIBILITY OVER APPEARANCE** — Ante duda entre verse bien y ser
    reproducible, gana la reproducibilidad.

## Catálogos canónicos (prohibido re-declarar)

| Entidad | Fuente única |
|---|---|
| Fases del pipeline (6) | `apps/web/lib/strategyPhases.ts` |
| Nº canónico de gates | `CANONICAL_GATES_COUNT = 11` (strategyPhases.ts) y `TOTAL_REQUIRED_GATES` (certification_registry) |
| Directorio de gates (slugs, umbrales) | `contracts/gate_directory.py` |
| Estados de ciclo de vida | `contracts/canonical_strategy.py` (`StrategyLifecycleStatus`) |
| Contratos de backtest | `contracts/backtest.py` |

## Métricas con definición única

- Profit factor, Sharpe, DD, R, sortino: se calculan en el motor/validación, jamás
  en React ni con atajos (`sharpe*1.15` está prohibido; el sortino se mide).
- El drawdown NO se recorta (`min(4.0, dd)` eliminado en FASE 1).

---

## Clarificación Doctrinal: Cero Datos Falsos vs Remuestreo Estadístico Real

### ❌ PROHIBIDO
- Simular u originar series de precios históricas inexistentes (velas falsas).
- Inventar trades o curvas de equity sintéticas sin ejecución del motor.
- Autocompletar métricas o perfiles de usuario con valores por defecto complacientes.
- Promocionar o sustituir datasets arbitrarios para forzar la ejecución del pipeline.

### ✅ PERMITIDO Y EXIGIDO (Robustez Cuantitativa)
- **Monte Carlo de Trades Reales**: Remuestreo y permutación bootstrap sobre la secuencia real de operaciones generada por el `CanonicalExecutionLedger`.
- **Stress Testing & Slippage Permutation**: Aplicación de multiplicadores de deslizamiento y fricción sobre observaciones de mercado reales.
- **Walk-Forward Efficiency (WFE)**: Particionado temporal estricto IS / OOS sobre datos físicos históricos.
- **Paper Trading Forward**: Simulación de ejecución en tiempo real sobre feeds de mercado en vivo etiquetada explícitamente como `INCUBATION_PAPER`.

- La anualización es compuesta sobre el retorno real del periodo; prohibido
  "velocity" con supuestos de sprint.

## Regla final

Si algo no está disponible: **NO INVENTAR. NO ESTIMAR SILENCIOSAMENTE. NO MOSTRAR
DATOS FICTICIOS. NO FORZAR ESTADO.**
