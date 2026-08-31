# CENSO F01 — criterio 1.1 sellado

Fecha: 2026-08-31T13:38:59.360997+00:00 · Motor vigente: 5.11.0 · Modo: APLICADO

Total candidatos: 728

**Supervivientes del criterio 1.1: 0**

En estados terminales (conservan etiqueta): 723
Reclasificados a LEGACY_NO_CERTIFICADO: 5

## Censo por estado (antes)
| Estado | n |
| :--- | ---: |
| LEGACY_NO_CERTIFICADO | 210 |
| LEGACY_MOTOR_VERSION_OBSOLETA | 120 |
| REJECTED_ESTRUCTURAL | 104 |
| LEGACY_MOTOR_SIN_POINT_VALUE | 55 |
| REJECTED_BAJO_PF | 51 |
| BLOCKED_NO_EVIDENCE | 47 |
| REJECTED | 41 |
| REJECTED_ALTO_DRAWDOWN | 31 |
| RECHAZADA_MUESTRA_DEGENERADA | 30 |
| LEGACY_MOTOR_SENAL_SIN_CRUCE | 27 |
| REJECTED_GATES_INCOMPLETE | 7 |
| APPROVED_CURRENT_ENGINE | 4 |
| INCUBADORA_REPROGRAMACION | 1 |

## Censo por estado (después)
| Estado | n |
| :--- | ---: |
| LEGACY_NO_CERTIFICADO | 215 |
| LEGACY_MOTOR_VERSION_OBSOLETA | 120 |
| REJECTED_ESTRUCTURAL | 104 |
| LEGACY_MOTOR_SIN_POINT_VALUE | 55 |
| REJECTED_BAJO_PF | 51 |
| BLOCKED_NO_EVIDENCE | 47 |
| REJECTED | 41 |
| REJECTED_ALTO_DRAWDOWN | 31 |
| RECHAZADA_MUESTRA_DEGENERADA | 30 |
| LEGACY_MOTOR_SENAL_SIN_CRUCE | 27 |
| REJECTED_GATES_INCOMPLETE | 7 |

## Razones de descarte (muestra de 20)

- `UR-CANON-NQ-001` (INCUBADORA_REPROGRAMACION): c1: trades_oos=80 < 200; c3: ratio_oos_is=0.01 < 0.5; c4: gates_passed=0 < 11 ...
- `UR_ULTRA_BNB_USDT_15M` (APPROVED_CURRENT_ENGINE): c1: trades_oos=15 < 200; c4: sin evidencia física (data/evidence/UR_ULTRA_BNB_USDT_15M/evidence_bundle.json); c5: DSR NO_EVALUABLE desde BD (fail-closed) ...
- `UR_ULTRA_XRP_USDT_4H` (APPROVED_CURRENT_ENGINE): c1: trades_oos=20 < 200; c4: sin evidencia física (data/evidence/UR_ULTRA_XRP_USDT_4H/evidence_bundle.json); c5: DSR NO_EVALUABLE desde BD (fail-closed) ...
- `UR_ULTRA_GC_1H` (APPROVED_CURRENT_ENGINE): c1: trades_oos=24 < 200; c2: pf_oos=1.14 < 1.25; c4: sin evidencia física (data/evidence/UR_ULTRA_GC_1H/evidence_bundle.json) ...
- `UR_ULTRA_NQ_1H` (APPROVED_CURRENT_ENGINE): c1: trades_oos=23 < 200; c4: sin evidencia física (data/evidence/UR_ULTRA_NQ_1H/evidence_bundle.json); c5: DSR NO_EVALUABLE desde BD (fail-closed) ...

## Notas
- c5 (DSR) y c6 (persistencia OOS) no son computables desde las columnas de la BD: se aplican fail-closed. El pipeline 5.6.0 debe computarlos para candidatas nuevas (F03).
- Expectativa honesta del plan: pocos o ningún superviviente. El corpus base se construye en F03 con el motor realista, no rescatando el catálogo viejo.