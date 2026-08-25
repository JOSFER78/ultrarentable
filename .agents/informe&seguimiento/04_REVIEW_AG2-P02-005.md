# REVIEW AG2-P02-005 — DECISIÓN EXTERNA

## Resultado
`REWORK`

## Auditoría de `origin/main`

La entrega P02-005 ha mejorado de forma sustancial el runtime, pero **no puede aprobarse todavía** bajo ZERO-SIMULATION / ZERO-FORCING / REAL-ONLY.

### R01 — Inconsistencia de identidad del dispatch
`00_DISPATCH.md` publica `AG2-DISPATCH-20260825-1930-P02-005`, mientras `03_HANDOFF_AG2-P02-005.md` declara `AG2-DISPATCH-20260825-1900-P02-005`. La evidencia de una orden no puede usar un dispatch diferente del que realmente autorizó la ejecución.

### R02 — `BOTH` no está probado como comportamiento bidireccional real
El test de `BOTH` comprueba que `instruction.direction == BOTH`, pero no demuestra que el motor produzca ejecuciones LONG y SHORT reales desde datos físicos. Con el código actual, `pos_dir = LONG if direction in [LONG, BOTH] else SHORT`, por lo que `BOTH` selecciona LONG y no demuestra bidireccionalidad.

### R03 — `account_equity_usd` sigue siendo un default cuantitativo
`execute_backtest(... account_equity_usd: float = 100000.0)` introduce una cantidad monetaria por defecto dentro del runtime. Esto contradice el requisito de que el capital de cuenta sea explícito y procedente de una política/track/account contract verificable.

### R04 — `max_open_positions` no está realmente ejecutado
El código lee `max_open_positions`, pero mantiene un único booleano `in_pos`. No hay una estructura de posiciones que permita demostrar la semántica de `max_open_positions > 1`, ni rechazo explícito de valores incompatibles.

### R05 — Sizing no demuestra toda la semántica declarada
`FIXED_CONTRACTS`, `RISK_PCT_EQUITY` y `FIXED_USD` se calculan, pero no está demostrado que las unidades, multiplicadores, tick value/point value o reglas del instrumento estén tomadas de un contrato de ejecución real. Una división USD/precio no demuestra sizing correcto de futuros/CFD/otros instrumentos.

### R06 — Session `close_at_eod` y sesiones cruzando medianoche necesitan pruebas de comportamiento real
La función `_is_within_session()` soporta ventanas cruzadas, pero la evidencia debe demostrar aperturas/cierres reales y que una sesión fuera de ventana no genera entradas ni mantiene posiciones indebidamente.

### R07 — Política de fill sigue siendo una decisión interna del adaptador
La prioridad pesimista SL ante conflicto SL/TP puede ser una política válida, pero no está demostrado que coincida con la política del engine universal existente. Si el engine real ya define fills, esta capa no puede sustituirlo silenciosamente. Si no existe política universal, debe documentarse como contrato de ejecución explícito, no como verdad histórica del motor.

### R08 — Pruebas pueden ser estructurales en vez de comportamentales
La matriz de 24 tests es útil, pero varios casos comprueban campos, compilación o propiedades aisladas. Para declarar una semántica ejecutada se necesitan pruebas de comportamiento sobre resultados de ejecución, no únicamente sobre la representación interna.

### R09 — Ledger de subagentes demuestra registro, pero no prueba independencia material suficiente
El ledger es mucho mejor, pero algunos comandos son globales (`pytest`, `git log`, `ls-tree`) y varias conclusiones son declaraciones. La siguiente orden debe exigir evidencia cruzada: cada agente debe aportar al menos un artefacto o contradicción que otro agente valide/rechace.

## Decisión
**NO liberar Fase 02.**

La siguiente orden es:

`AG2-P02-006 — Behavioral Runtime Proof & Execution-Boundary Verification`

El nuevo trabajo debe demostrar comportamiento real, no sólo estructura, y debe cerrar primero los R01-R09 anteriores.

## Reglas
- SOLO Fase 02 / rework.
- ZERO-SIMULATION.
- ZERO-FORCING.
- REAL-ONLY.
- ZERO-LOOKAHEAD.
- Un dato monetario o de sizing no puede tener un default cuantitativo oculto.
- `BOTH` sólo puede declararse soportado con evidencia real LONG + SHORT.
- Si la política de fills del engine real no está disponible, FAIL-CLOSED / BLOCKED; no inventarla.
- No tocar Fase 03, Discovery Factory, Genome, Meta-Strategy, ULTRA ni FONDEO.

## Criterio de salida P02-006
Sólo `READY_FOR_REVIEW` cuando:
1. dispatch/order/handoff IDs coinciden exactamente;
2. `BOTH` produce LONG y SHORT reales en casos físicos controlados;
3. capital de cuenta es explícito y trazable;
4. `max_open_positions` está realmente implementado o se rechaza cualquier valor no soportado;
5. sizing está ligado a la semántica del instrumento/contrato real;
6. sesiones y EOD tienen pruebas de comportamiento;
7. política intrabar/fill está vinculada al engine real o queda explícitamente BLOCKED;
8. tests prueban resultados, no sólo estructuras;
9. subagentes independientes aportan evidencia verificable y reconciliada;
10. remote SHA + handoff + `origin/main` son consistentes.

Después de entregar: STOP. Antigravity no crea otra orden.
