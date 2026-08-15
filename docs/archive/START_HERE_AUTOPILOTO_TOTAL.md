# EMPEZAR AQUÍ — AUTOPILOTO TOTAL BINGX

Este paquete parte de la última versión REAL-ONLY local auditada.

## Misión inmediata

Transformar la aplicación actual en un producto de **un solo botón**, donde el usuario no tenga que conocer ni configurar:

- estrategias;
- indicadores;
- parámetros;
- símbolos;
- temporalidades;
- apalancamiento;
- piramidación;
- población;
- generaciones;
- presupuesto de cómputo.

## Orden obligatorio de lectura

1. `START_HERE_AUTOPILOTO_TOTAL.md`
2. `AUDITORIA_FASES_EF_V4.md`
3. `PROMPT_IDE_CORRECCIONES_E2_F2.md`
4. `PROMPT_IDE_AUTOPILOTO_TOTAL_BINGX.md`
5. `docs/CURRENT_IMPLEMENTATION_STATUS.md`

## Prioridad de ejecución

1. No revertir las correcciones E2/F2 descritas por la auditoría.
2. Corregir primero cualquier test fallido desde un checkout y SQLite limpios.
3. Aplicar íntegramente `PROMPT_IDE_AUTOPILOTO_TOTAL_BINGX.md`.
4. Convertir Campaigns en un autopiloto sin parámetros técnicos.
5. Convertir Strategy Lab en inspector de solo lectura.
6. Implementar selección automática de universo, datos, estrategias, parámetros y leverage.
7. Mantener ejecución local sin Docker.
8. No iniciar NautilusTrader hasta superar completamente la puerta F2.

## Prohibiciones

- No usar mocks, demos ni resultados hardcodeados.
- No usar valores financieros predeterminados.
- No hacer que `AUTO` signifique un símbolo/timeframe fijo.
- No ejecutar campañas largas dentro de una petición HTTP.
- No pedir al usuario conocimientos de trading cuantitativo.
- No declarar una estrategia como canónica antes de la validación correspondiente.

## Primera respuesta que debe dar el IDE

Antes de modificar código, debe mostrar:

- resumen de la arquitectura encontrada;
- tests reproducidos desde una base limpia;
- lista de fallos actuales;
- plan de commits para E2/F2 + Autopiloto Total;
- archivos que modificará en el primer bloque.
