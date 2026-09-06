# E6: prueba de generacion y admision del 6 de septiembre de 2026

Captura UTC: 2026-09-06T11:47:50.850771+00:00.

Se reutilizo la investigacion y el motor de mejora ya desplegado. Este experimento no cambia sus umbrales ni acredita una estrategia de fondeo.

## Resultado nativo

Proyecto `UR_E6_RANDOM_20260906`: inicio 13:31:26 y fin 13:37:23 CEST, aproximadamente 5 minutos y 58 segundos. SQX registro 61 generadas, 2 aceptadas en su banco y 59 rechazadas. De los rechazos nativos, 47 correspondieron al filtro de operaciones mensuales y 12 al factor de beneficio. Las dos aceptadas por el Builder no superaron la admision posterior.

| Estrategia | Operaciones entrenamiento | Neto entrenamiento | Operaciones desarrollo | Neto desarrollo | Factor beneficio desarrollo | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Strategy 0.0 | 96 | 1848,50 | 46 | -2720,25 | 0,56 | Rechazada |
| Strategy 0.31 | 73 | 1824,25 | 13 | -767,00 | 0,57 | Rechazada |

Ambas incumplen el minimo configurado de 100 operaciones de entrenamiento y el beneficio positivo en desarrollo. La segunda tampoco alcanza 30 operaciones de desarrollo. Son criterios de admision iniciales, no garantias de rentabilidad. No se exporto ningun archivo de estrategia y no se promovio ninguna al mejorador. La decision usa metricas nativas; no equivale a una reproduccion independiente de reglas y operaciones.

Datos: @E6 H1, instrumento nativo E6-CME, historial M1, entrenamiento 2022-2024 y desarrollo 2025. Los datos finales 2026 permanecen reservados. Un contrato, comision configurada 5 y deslizamiento 2; estos supuestos no estan contrastados con ejecucion real. No se exportaron barras de precios.

## Ajustes y aprendizaje

El primer ensayo genetico genero 29 y no acepto ninguna. El aumento de ReservedBars de 500 a 1000 resolvio el error observado de barras reservadas en el ensayo siguiente, que tampoco completo su poblacion inicial. El ensayo aleatorio mantuvo los filtros y produjo las dos candidatas anteriores. No demuestra que el modo aleatorio sea universalmente mejor: solo que esta configuracion pudo producir candidatas sin completar antes una poblacion genetica. No se bajaron los filtros tras observar las perdidas.

## Limite operativo actual

`sqx-headless.service` y `m1-runner.service` figuran activos, pero la consulta de estado del proyecto devuelve `Not implemented` o una salida sin contadores. El runner reintenta; no esta demostrado el avance actual ni el relevo continuo entre trabajos. El ultimo avance acreditado de MES M1 fue a las 10:21 UTC. El estado activo del servicio no resuelve este fallo. La campana continua mantiene aproximaciones CFD y sigue excluida de la admision como futuros.

El temporizador del mejorador esta activo. Su ultima ejecucion observada rechazo una entrada por `INITIAL_PERCENT_PT_PENDING_ENTRY`: calculo de objetivo porcentual inicial con entrada pendiente, pendiente de correccion y recalculo. No se retiro esa proteccion ni se presento el rechazo como trabajo completado.

El motor de mejora tiene 120 pruebas pasadas en la version previamente desplegada y un experimento real EW con dos variantes descartadas. Este cierre solo preserva evidencia y actualiza documentacion; no corrige el seguimiento continuo ni modifica codigo ejecutable.

## Evidencia

[e6_evidence_20260906.zip](e6_evidence_20260906.zip): 18 entradas, 181055 bytes, SHA-256 `1eddcb2dbc7dd424fa0d823d4c1e186eccea8ce1957aa2a0912dbf9d7b29ab39`.

Incluye configuraciones, procedencia, metricas, registro nativo, decision de admision y captura de estado. Se comprobo la integridad ZIP y cada hash del manifiesto tras descargar. No contiene barras de mercado ni una exportacion masiva de estrategias.
