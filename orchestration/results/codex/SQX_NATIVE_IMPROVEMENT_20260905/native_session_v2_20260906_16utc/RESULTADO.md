# Motor de mejora: resultado y límite para fondeo

Comprobación nativa final: 2026-09-06, 07:21 UTC. Servidor 88.99.210.167.

Actualización de operación: 07:45 UTC. Búsqueda sin pausa en MYM M5; el registro avanzó de 5273 a 10780 generadas entre 07:28 y 07:38. Servicio de búsqueda y temporizador de mejora activos. No cambia el rechazo de las variantes ni acredita recuperación completa ante caídas.

Se corrigió también el generador de proyectos futuros: excluye PTPercent conservando la protección inicial y resuelve dos valores por defecto que apuntaban a constantes inexistentes. Comprobado con la plantilla nativa NQ_TS.cfx: el XML resultante solo cambia PTPercent respecto al generador anterior con sus valores por defecto corregidos; plantillas sin ese campo o con duplicados se rechazan. Se generó un CFX aislado sin cargarlo en SQX. Script desplegado con copia anterior y SHA-256 verificado. Esta corrección **no modifica los proyectos ya cargados**; su migración requiere un cierre controlado que preserve todos sus bancos. [Evidencia de comprobación](../generator_safe_pt_v2_20260906/verification.json) y [despliegue](../generator_safe_pt_v2_20260906/deployment.json).

## Implementado y comprobado

El motor toma una preseleccionada real, conserva sus reglas de entrada y busca mejoras de salida en SQX. Exporta como máximo dos variantes; recalcula original y variantes con contratos enteros y precisión de un minuto; compara beneficio, factor de beneficio, caída y tamaño de muestra. Conserva los resultados fallidos y no repite automáticamente una combinación ya procesada de estrategia y receta. La ejecución está instalada con temporizador; la búsqueda general continúa por separado y exporta como máximo cinco preseleccionadas por lote.

La receta v2 excluye objetivos porcentuales incompatibles con la combinación comprobada de entrada pendiente y protección inicial. Mantiene la protección inicial. La implementación pasó 102 pruebas; esta comprobación adicional verifica 27 archivos por SHA-256 y reproduce localmente la comparación nativa. No se ha probado la recuperación completa del conjunto tras una caída.

## Una estrategia real mejorada

Strategy 3.3.135 produjo dos variantes que mejoraron los criterios históricos de desarrollo. El beneficio de la muestra OOS de desarrollo pasó de 11555,19 a 12550,18; el factor de beneficio, de 2,50 a 2,93. Ambas incumplían sesiones. Véase [prueba original](../safe_pt_v2_20260906/RESULTADO.md).

La prueba posterior modificó las reglas de todas las versiones a sesión UTC 00:00–16:00 y volvió a ejecutar SQX; no eliminó operaciones después de calcularlas.

| Resultado con sesión restringida | Original | Variante 1 | Variante 2 |
|---|---:|---:|---:|
| Beneficio IS | 9844,98 | 13239,62 | 13050,26 |
| Beneficio OOS de desarrollo | 8520,23 | 8902,73 | 8902,73 |
| Factor de beneficio OOS | 2,85 | 3,11 | 3,11 |
| Operaciones OOS | 26 | 26 | 26 |
| Operaciones incompatibles con horario | 1 | 1 | 1 |

Las variantes se rechazan: la muestra OOS no alcanza el mínimo de desarrollo de 30 operaciones y persiste una posición durante el cierre regular el 19 de junio de 2024. Adelantar el cierre de sesión no garantiza el cierre efectivo: la implementación instalada de LimitTimeRange ejecuta el cierre TS/MC en cierre de barra. No se modificó código interno de SQX. No se sigue ajustando esta misma base contra los mismos datos para forzar una aprobación.

## Qué falta para pasar una a fondeo

No hay ninguna estrategia acreditada ni candidata enviada a la siguiente etapa. El motor devuelve `NO_EVALUABLE`, `probada_para_fondeo=false` y una lista vacía de candidatas. Es una evaluación preliminar, no un simulador completo de examen.

Los datos instalados bajo el alias MNQ proceden de un índice CFD; no acreditan comportamiento del futuro MNQ. Antes de un veredicto de examen hacen falta datos verificables del instrumento real, reglas fechadas de una modalidad concreta, costes y calendario, cálculo intradía de pérdidas y una muestra final reservada con intentos de 1–5 días. El OOS utilizado para comparar mejoras ya es parte del desarrollo. No se prometen plazos de aprobación.

## Continuidad y evidencia

A las 07:17 UTC el generador seleccionó cinco de 5076 estrategias MNQ M5; 88 habían superado su filtro preliminar. A las 07:18 UTC liberó la memoria de ese lote y arrancó MYM M5. El servicio de búsqueda y el temporizador de mejora estaban activos. Son preseleccionadas, no estrategias aprobadas.

El proyecto temporal de esta prueba se retiró de SQX únicamente después de guardar los archivos nativos, comprobar sus hashes y reproducir localmente el resultado. Los archivos permanecen en la VPS y en esta carpeta. Ver `assessment.json`, `comparison.json`, `funding_session_screen.json` y `local_verification.json`.

Fuentes recuperadas: [opciones de negociación de StrategyQuant](https://strategyquant.com/doc/strategyquant/trading-options/) y [horarios de Topstep](https://help.topstep.com/en/articles/8284206-when-and-what-products-can-i-trade). El perfil horario es un ejemplo parcial; no representa todas las empresas ni todas las reglas de examen.
