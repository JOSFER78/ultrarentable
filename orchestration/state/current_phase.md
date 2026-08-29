# Fase 1: Captura del semillero 'Last generation' → ToImprove + export CSV

## Objetivo
Con el proyecto PARADO, copiar el banco legacy `Last generation` (~91-95 estrategias CRUDAS reales,
H8) a `ToImprove` y exportar CSV de evidencia, ANTES de cualquier reinicio del proyecto (H13: los
bancos viven solo en RAM del motor).

## Contexto necesario
- Motor SQX vía API read-only en puerto 5050 (sqcli). Evidencia: `estrategias_um/docs/HECHOS_Y_DECISIONES.md`
  (H8, H10, H13) y `estrategias_um/docs/PLAN_PIPELINE.md` §2-§3.
- H10: el nombre con espacio NO es direccionable por `count name=` ("Databank 'Last' doesn't exist");
  solo vía `-databank action=list`.
- H13: disco `databanks/*` = 0 archivos; si el proyecto se reinicia sin export previo, se pierde.
- Decisión DD2 (orden estricto): capturar PRIMERO, recargar config DESPUÉS.
- NO tocar: `AutomaticDismissal` del project.cfx (H4-H5), ningún umbral (eso es Fase 2), el código
  del motor, ni hacer `git commit` (prohibido; la auditoría es este árbol orchestration/).

## Subagentes sugeridos
- Subagente 1 (API): verificar estado del proyecto = parado; si está corriendo, ABORTAR y
  reportar (guard duro).
- Subagente 2 (captura): `-databank action=list` antes; copy `Last generation`→`ToImprove`;
  `-databank action=list` después; export CSV completo a `/home/ubuntu/ORDENAR/semillas_<fecha>.csv`
  con columna `banco_origen`.
- Subagente 3 (verificación): contar filas del CSV, verificar que ningún registro se perdió
  (counts antes = counts después + fichero CSV).

## Criterio de éxito (verificable, no subjetivo)
- [ ] Guard previo: proyecto PARADO confirmado por API (si corre, no se ejecuta nada).
- [ ] `-databank action=list` tras la captura muestra ToImprove Records > 0 (esperado ≥91).
- [ ] CSV `/home/ubuntu/ORDENAR/semillas_*.csv` existe, no vacío, con columna `banco_origen` y
      ≥91 filas de estrategias reales (cero mocks, cero inventadas).
- [ ] Counts consistentes: estrategias en `Last generation` antes = dentro de ToImprove + CSV.
- [ ] No se tocan los archivos: project.cfx, improve_cycle.sh, cualquier umbral del embudo.

## Qué reportar al terminar
- Diff de los archivos modificados (si los hay; idealmente ninguno fuera de orchestration/).
- Output EXACTO de los comandos sqcli usados (action=list antes/después, export).
- Counts reales por banco antes y después, y nº de filas del CSV con su ruta exacta.
- Cualquier decisión que tomó el subagente que no estaba explícita acá.
