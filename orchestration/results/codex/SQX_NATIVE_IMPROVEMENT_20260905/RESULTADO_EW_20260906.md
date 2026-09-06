> Actualizacion 2026-09-06T11:47:50.850771+00:00: dos candidatas nativas E6 rechazadas en desarrollo; cero exportadas. El seguimiento de la busqueda continua falla y no se declara resuelto. [Resultado y evidencia E6](RESULTADO_E6_20260906.md). Las observaciones siguientes conservan sus fechas.

# Motor de mejora: resultado real del 6 de septiembre de 2026

Estado actualizado a las 10:26 UTC: motor de mejora nativa desplegado y probado en la VPS 88.99.210.167. Ninguna variante promovida y ninguna estrategia acreditada para fondeo. La validación completa del examen sigue pendiente.

## Comprobación de producto y despliegue a las 10:26 UTC

La [lista oficial de productos de Topstep](https://help.topstep.com/en/articles/8284206-when-and-what-products-can-i-trade), actualizada el 13 de julio de 2026 y consultada el 6 de septiembre, no incluye EW/EMD. La estrategia @EW conserva su valor como prueba del motor; no se admite para ese perfil de examen. No se sustituye su nombre por otro instrumento ni se equipara un CFD a un futuro.

Se añadió `funding-product` para examinar una sola estrategia y `prepare --funding-profile topstep` para rechazar un producto no listado antes de crear el experimento. Un símbolo listado sólo obtiene `PRODUCT_LISTED_IDENTITY_UNVERIFIED`: todavía exige comprobar sus datos y todas las reglas del examen. El filtro de sesiones también aplica esta comprobación. El perfil es una captura fechada de la lista, no una certificación ni un actualizador automático de normas.

Pasaron las 120 pruebas del conjunto `tests/sqx_runtime` en 37,706 segundos. Los dos fallos iniciales de las pruebas nuevas correspondían al nombre esperado: el archivo real contiene `@EW`, no `EW`; se corrigieron las expectativas sin transformar el instrumento. En la VPS se verificó sobre el archivo BASE real el rechazo del producto y de la preparación antes de crear archivos. El motor quedó con SHA-256 `59fc003b8b23dd0c246f879d5d1547d176277b193c1376556f6b3cb3994d07eb`, conservando respaldo de la versión anterior y sin reiniciar SQX.

Generador, SQX y temporizador de mejora estaban activos a las 10:26 UTC. MES M1 avanzó de 1.060 intentos y cero resultados guardados a las 10:01 a 3.129 intentos y 63 guardados a las 10:21. Permanecen en la VPS, son preliminares y siguen sujetos a la exclusión de datos CFD; este recuento no indica aprobación para fondeo.

Evidencia: [despliegue y avance](product_gate_20260906/deployment.json), [decisión del producto real](product_gate_20260906/product_check.json). La versión y observación de las secciones siguientes se conservan como registro del experimento anterior.

## Método y alcance

Se reutiliza StrategyQuant para generar, mejorar salidas y recalcular la estrategia con los mismos datos y condiciones. El controlador limita las variantes, compara con la original, conserva los fracasos y exige evidencia física antes de permitir un paso posterior. Se mantienen separados entrenamiento 2022–2024, comparación de desarrollo 2025 y datos finales 2026 sin utilizar. El resultado de desarrollo no equivale a una prueba final independiente.

La elección sigue los [modos de construcción](https://strategyquant.com/doc/strategyquant/different-build-modes/), el [flujo de trabajo](https://strategyquant.com/doc/strategyquant/workflow/) y las [pruebas de robustez](https://strategyquant.com/doc/strategyquant/cross-checks-automated-strategy-robustness-tests/) oficiales. Para fondeo, una lista de operaciones cerradas no basta: el [límite de pérdidas de Topstep](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit) también considera pérdidas no realizadas. Topstep es una referencia metodológica; no se ha certificado la compatibilidad de esta estrategia con su examen.

## Experimento ejecutado

Se generó una base real sobre @EW H1 (E-mini S&P MidCap 400), con un contrato, datos M1 y sesión Exchange. La generación duró 3 minutos y 36 segundos: 88 intentos, 9 aceptados y únicamente una estrategia exportada, Strategy 1.1.27. Comisión 5 y deslizamiento 2 son supuestos de configuración, pendientes de validar frente a ejecución real.

El Improver nativo produjo una variante que sólo cambiaba metadatos. Su recálculo reprodujo las mismas operaciones. Se corrigió el motor para detectar y rechazar este caso antes de gastar otro recálculo.

Después se ejecutó un experimento distinto: original y dos variantes del stop largo, con valores configurados 90, 81 y 99. SQX completó los tres recálculos en 24 segundos y se conciliaron las operaciones exportadas con sus métricas.

| Resultado de desarrollo | Original | Stop −10 % | Stop +10 % |
| --- | ---: | ---: | ---: |
| Beneficio neto 2022–2024 | 40.503 | 40.585 | 38.522 |
| Beneficio neto 2025 | 7.706 | 6.619 | 8.485 |
| Factor de beneficio 2025 | 1,32 | 1,27 | 1,37 |
| Rentabilidad/drawdown 2025 | 1,19 | 0,93 | 1,24 |
| Decisión | Base conservada | Descartada | Descartada |

Son resultados de simulación en la moneda de configuración, no ganancias realizadas. El stop menor empeora la muestra 2025; el mayor empeora entrenamiento y no alcanza el criterio configurado de mejora del 5 % en la peor relación rentabilidad/drawdown. Este criterio es una política inicial del motor, no una garantía científica universal. No se relajó después de ver los resultados.

## Correcciones verificadas

- Los proyectos copian los recursos de la estrategia original y eliminan recursos de plantilla no utilizados. Se corrigió una referencia residual a MNQ que impedía ejecutar EW.
- Los cambios que sólo modifican metadatos se rechazan antes del recálculo, conservando significativas fórmulas, valores y atributos desconocidos.
- Una variante descartada en desarrollo no intenta atravesar una puerta de fondeo incompatible: termina como DROP_VARIANT y conserva su motivo. Esto corrigió el bloqueo al evaluar EW con un perfil de sesiones limitado a otros instrumentos.
- La ejecución guarda manifiesto, estrategias, operaciones, métricas, comparación y evaluación con hashes; se reconcilió el trabajo anterior y se cerró su reclamación persistida.
- Pasaron 114 pruebas del conjunto de ejecución SQX. Además se comprobó el rechazo de la variante real sin cambios en la VPS y se completó allí el experimento de los dos stops.

Motor desplegado: `sqx_native_improvement.py`, SHA-256 `dc95ad85f8b0ae638cf1669ec93de4954b26b2e7a3bb6dc91ab30e0d42d808e6`. Se conservaron respaldos de las versiones anteriores.

## Continuidad y límites

A las 10:05 UTC estaban activos el generador, SQX y el temporizador de mejora. El generador terminó MCL M1, conservó su banco, liberó memoria e inició MES M1 a las 09:51. A las 10:01 llevaba 1.060 intentos y ninguna estrategia aceptada. Esto demuestra avance y encadenamiento en esta observación, no funcionamiento indefinido garantizado.

La campaña continua aún usa datos CFD como aproximaciones; su admisión al mejorador de futuros está bloqueada. El experimento EW utilizó datos de futuros y fue una ejecución acotada, todavía sin integrar en esa campaña. No hay un circuito autónomo completo de futuros a candidatas validadas.

Para evaluar de verdad un examen en 1–5 días faltan procedencia y política de contratos verificadas, reglas fechadas de una empresa/modalidad, calendario, reconstrucción independiente del saldo intradía con pérdidas abiertas, costes y ejecución contrastados y prueba final reservada. No se ha probado que una estrategia apruebe un examen. La siguiente fase debe resolver estos requisitos antes de emitir ese veredicto.

## Evidencia preservada

- [Paquete final](ew_improvement_final_20260906.zip): 29 entradas, 315.992 bytes; integridad ZIP y SHA-256 comprobadas tras descargar. Hash `1c30b798f446407497826aef142ad1b6a45dec9ca94c922b686bde866533a5a6`.
- Incluye el experimento de stops completo, la evaluación corregida del experimento previo, informes de despliegue y captura del estado de servicios y generador.
- [Generación y mejora nativa](ew_native_search_evidence_20260906.zip).
- [Recálculo previo](ew_native_retest_20260906_evidence.zip): conserva la evaluación histórica bloqueada; la evaluación corregida está en el paquete final, sin sobrescribir la evidencia anterior.
