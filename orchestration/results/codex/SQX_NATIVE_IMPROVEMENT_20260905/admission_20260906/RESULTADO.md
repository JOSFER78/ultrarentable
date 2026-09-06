# Motor de mejora: corrección de admisión, 6 septiembre 2026

Se desplegó el filtro de procedencia antes de la búsqueda nativa automática. En esta instalación, MNQ y MYM contienen históricos CFD importados como USATECHIDXUSD y USA30IDXUSD (véase ../data_provenance_audit.json). La exclusión es específica de esta instalación; no describe esos contratos en otros proveedores. Solo debe revisarse tras una migración de datos documentada. Quitar la exclusión no certifica un histórico.

## Comprobación

- 12 pruebas de `test_automatic_improvement_stage.py`: correctas, incluidas dos nuevas sobre archivos SQX reales. Una plantilla inexistente permite detectar que ninguna ejecución alcanza la preparación nativa al excluir la candidata.
- Inspección en VPS con registro temporal vacío: tres candidatas reales excluidas, cero admitidas y cero trabajos nativos iniciados. No se consumen sus identidades ni se alteran los registros históricos.
- Hash local y remoto de sqx_improvement_stage.py: `3199201e56488c1f7808f4d1a1f9043b5a643c23419199ef042154ad1212aee8`.
- Servicio automático ejecutado: `WAITING_FOR_SUPPORTED_SELECTED_STRATEGY`. Las selecciones actuales ya tenían registros históricos; por eso ese estado difiere de la inspección con registro vacío.
- SQX, generador, supervisor y temporizador de mejora: activos.
- FONDEO_MCL_M1: 3.670 estrategias generadas, cero aceptadas, 6.614 por hora. El registro anterior de las 09:05 UTC mostraba 2.223: hay avance real, no solo un servicio activo.

## Límite operativo

El motor automático admite actualmente recetas MYM/MNQ y ambos históricos están en cuarentena. Por tanto, no ejecutará nuevas mejoras sobre esos datos. El generador continúa, pero también utiliza los históricos anteriores: sus resultados no acreditan futuros reales. La migración a históricos adecuados sigue pendiente; este cambio evita gastar mejoras en entradas ya conocidas como inadecuadas, no resuelve esa migración.

La prueba previa de Strategy 3.3.135 mejoró resultados de desarrollo mediante salidas nativas, pero fue rechazada para fondeo por sesiones y procedencia. El ensayo transferido a @EW tampoco produjo una candidata admisible. No hay estrategias certificadas para aprobar en 1–5 días.

Los módulos de comparación, selección de hasta dos variantes, persistencia y evaluación preliminar ya existen. Falta demostrar una candidata con datos adecuados, reglas completas del examen, trayectoria intradía y una prueba final reservada. No está completado el objetivo global.

Referencias consultadas: [flujo nativo de SQX](https://strategyquant.com/doc/strategyquant/workflow/), [pruebas de robustez](https://strategyquant.com/doc/strategyquant/cross-checks-automated-strategy-robustness-tests/), [límite de pérdida de Topstep](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit). El límite incluye pérdidas no realizadas: las operaciones cerradas por sí solas no acreditan supervivencia al examen.
