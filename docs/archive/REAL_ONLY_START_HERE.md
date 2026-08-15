# EMPIEZA AQUÍ — LOCAL REAL-ONLY V2

Este paquete procede de una nueva auditoría de `ultrarentable_real_only_v1.zip`.

## Decisiones obligatorias

- Cero resultados inventados.
- Cero campañas aleatorias.
- Cero rankings hardcodeados.
- Cero backtests en el navegador.
- Cero Docker obligatorio.
- SQLite y filesystem local para el MVP.
- BingX como único venue.

## Orden de lectura para el IDE

1. `AUDITORIA_V2_LOCAL_REAL_ONLY.md`
2. `PROMPT_MODIFICACIONES_IDE_LOCAL_REAL_ONLY.md`
3. `docs/CURRENT_IMPLEMENTATION_STATUS.md`
4. `docs/REAL_ONLY_ACCEPTANCE_GATE.md`
5. `ESPECIFICACION_COMPLETA_BINGX_ULTRARENTABLE.md`

## Estado honesto

La ingesta está parcialmente construida, pero aún no se considera aprobada. Los datos incluidos en la versión anterior se han movido a cuarentena por falta de cadena de custodia RAW completa.

Las páginas de la aplicación ya no usan todas la misma tarjeta de bloqueo: cada módulo consulta el estado real local y muestra sus propios artefactos y requisitos.

## Arranque

```bat
INSTALL_LOCAL.bat
START_LOCAL.bat
```
