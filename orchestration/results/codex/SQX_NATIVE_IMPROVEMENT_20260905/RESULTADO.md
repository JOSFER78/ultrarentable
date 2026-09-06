> Actualización 2026-09-06, 07:11 UTC: receta de mejora corregida y desplegada; dos variantes mejoran los criterios de desarrollo y quedan bloqueadas por sesiones incompatibles. 102 pruebas correctas, 40 archivos verificados y comparación reproducida. Búsqueda continua activa. [Resultado y límites](safe_pt_v2_20260906/RESULTADO.md). Ninguna estrategia acreditada para fondeo. Las secciones siguientes conservan estados históricos.

# SQX: mejora nativa y comprobación preliminar de fondeo

Última comprobación: 6 de septiembre de 2026, 05:55 de Madrid. VPS: 88.99.210.167. Las secciones posteriores conservan los experimentos históricos; este resumen y la actualización automática final describen el estado vigente.

## Entrega y límite

Implementado y desplegado un motor acotado que toma una estrategia preseleccionada, conserva el control, prepara dos variantes de salida, las recalcula realmente en SQX y compara órdenes y métricas con evidencia verificable. La selección ya está conectada automáticamente: un temporizador revisa nuevas seleccionadas cada hora y ejecuta como máximo una estrategia por revisión, sin repetir los experimentos registrados.

La prueba automática con Strategy 3.3.135 (MNQ H4) terminó en 19 segundos. Recalculó BASE y dos variantes; ambas fueron rechazadas por empeorar métricas. Se verificaron localmente los 27 archivos de evidencia y se reprodujeron las decisiones. No se aceptó ninguna mejora ni se acreditó ninguna estrategia para fondeo.

La receta automática actual admite MYM y MNQ con objetivos de beneficio fijos; prueba un cambio acotado en una salida. Es una primera capacidad comprobada, no un optimizador general. El filtro de sesiones y el diagnóstico histórico de ventanas de 1–5 días están implementados, pero falta una evaluación final reservada con trayectoria intradía, costes y reglas completas del examen para afirmar utilidad acreditada para fondeo.

La búsqueda sigue avanzando y exporta un máximo de cinco estrategias preseleccionadas por trabajo. A las 05:37 de Madrid, MCL M5 había pasado de 5.313 a 10.352 estrategias generadas en diez minutos, sin aceptadas en su banco. Esta cifra mide actividad del generador, no calidad ni estrategias listas.

## Procedencia: límite confirmado el 6 de septiembre a las 05:52 de Madrid

El importador instalado asigna datos USA500IDXUSD a MES, USATECHIDXUSD a MNQ, USA30IDXUSD a MYM, XAUUSD a MGC y LIGHTCMDUSD a MCL. Esos nombres importados no acreditan datos de los contratos de futuros correspondientes. La base actual contiene históricos bajo dichos símbolos; no se encontró en esta comprobación una cadena de procedencia de futuros que justifique tratarlos como tales. M6E no aparece en ese importador y su procedencia sigue sin verificar. Los recálculos anteriores son ejecuciones reales de SQX sobre los datos instalados, **no una validación del mercado de futuros de fondeo**.

La evaluación exige ahora explícitamente proveedor, instrumento realmente cotizado, zona horaria, hashes del conjunto probado y política de contratos/rollover. Es una aclaración de la evidencia que falta: no se ha añadido una certificación de procedencia ni se ha cambiado NO_EVALUABLE. No se descargaron miles de estrategias ni se compraron datos. Los archivos originales y los resultados anteriores se conservan.

La documentación oficial de [suscripción de datos de SQX](https://strategyquant.com/data-subscription) ofrece históricos continuos de futuros y señala ejemplos para pruebas (6E, AAPL y EW); también limita la suscripción a versiones completas. La instalación consultada es de prueba. Queda por comprobar el acceso efectivo a un histórico de futuros adecuado antes de repetir una evaluación para fondeo; no basta cambiar el nombre del símbolo.

Evidencia de solo lectura: [auditoría de procedencia](data_provenance_audit.json). El motor actualizado pasó **53 pruebas en 26,093 segundos** y se desplegó con hash SHA-256 `b28ac17c0530774b921fb37fc3d21afc3a166e46eb921b544d94746c10d4807b`. [Verificación del despliegue](provenance_deployment_verified.json): SQX, generador y temporizador activos; el último registro de generación pasó de 10.352 a 15.611 estrategias entre las 03:37 y las 03:48 UTC, con 63 en banco. Son candidatos internos, no 63 estrategias probadas para fondeo.

## Experimentos reales

Se mantuvieron las condiciones de entrada SuperTrend/MACD y se probaron cambios explícitos en las salidas. Los experimentos 05 y 06 usaron recálculo nativo sobre M1 (precisión 2), contratos enteros y control original. Los hashes de entradas, configuración y resultados, la finalización del recálculo y la conciliación entre órdenes y métricas quedan registrados. El OOS es de desarrollo y ya se ha consultado: no es una prueba final reservada.

| Experimento / variante | Beneficio IS | Beneficio OOS | Retorno/caída IS | Retorno/caída OOS | Resultado |
|---|---:|---:|---:|---:|---|
| Original | 7640,69 | 3601,16 | 6,82 | 10,27 | Base de investigación |
| 05: objetivo largo 536 | 7650,69 | 3848,66 | 6,83 | 10,97 | Rechazada |
| 05: objetivo largo 654 | 7692,69 | 3896,16 | 6,86 | 11,11 | Rechazada |
| 06: objetivo corto fijo 270 | 11874,98 | 431,70 | 8,89 | 0,13 | Rechazada |
| 06: objetivo corto fijo 330 | 10897,77 | 71,70 | 6,61 | 0,02 | Rechazada |

Son resultados históricos de varios años, no resultados de un examen de cinco días. La política experimental exige 100/30 operaciones IS/OOS, ausencia de regresión en beneficio, profit factor y retorno/caída en ambas muestras, y al menos un 5 % de mejora del menor retorno/caída. Es una decisión conservadora de este experimento, no un criterio universal. En 05 la mejora máxima de ese último indicador es aproximadamente 0,59 %. En 06 el OOS empeora severamente y cae a 27 operaciones.

Evidencia: [campaña 05](campaign_05/comparison.json), [campaña 06](campaign_06/comparison.json), archivos originales y recalculados, órdenes y registros en ambas carpetas. Los manifiestos conservan su estado inicial de preparación; las comparaciones contienen la ejecución posterior.

### Cierres cortos inmediatos

La original produjo 145 operaciones, de las que 93 eran cortas, cerradas inmediatamente, todas perdedoras y con resultado conjunto de −1040. Se contrastaron órdenes reales con el código de salidas de la versión instalada de SQX: el objetivo porcentual inicial de la orden pendiente se evalúa con precio cero en este recorrido, dejando el objetivo al precio de entrada. El problema ya tiene una explicación reproducible en la instalación; no se modificó el código del proveedor.

Evidencia: [fuente instalada y hashes](campaign_05/installed_exit_source_proof.json), [detalle nativo de salidas](campaign_05/native_exit_details.csv). El experimento 06 sustituyó explícitamente ese objetivo porcentual por distancias fijas de 270 y 330; no se trató como una conversión equivalente. Los cierres cortos inmediatos bajaron a tres por variante, pero los resultados OOS se deterioraron. Corregir un comportamiento de ejecución no implica mejorar la estrategia. Excluir retrospectivamente todos los cortos dejaría solo 42/10 operaciones largas IS/OOS: muestra insuficiente.

## Experimento 07: recálculo con horario restringido

Se añadió un experimento explícito con horario UTC conservador 00:00–19:00, cierre al terminar el intervalo y restricciones de fin de semana. Se verificó que SQX aplicó los diez parámetros solicitados y la zona horaria en sus resultados efectivos. También cambia el control BASE: **no es la original sin restricciones**. Las reglas de entrada se conservan; se vuelve a probar el objetivo corto fijo 270/330 frente al porcentual original.

| Variante | Beneficio IS | Beneficio OOS | Operaciones IS/OOS | Decisión |
|---|---:|---:|---:|---|
| Control con horario | 5233,40 | 964,67 | 108/35 | Requiere revisión de ejecución |
| Corto 270 con horario | 7759,47 | −2618,21 | 100/33 | Rechazada |
| Corto 330 con horario | 6203,25 | −2466,15 | 99/33 | Rechazada |

Las incompatibilidades de cierre bajaron de 30/49/49 a **1/1/2**, pero no desaparecieron. Las tres conservan una posición desde el 24 de diciembre de 2025 hasta el día 26; la variante 330 también mantiene una posición durante un cierre del 19 de junio. La configuración de horario no basta para acreditar cierres reales. La evaluación al llegar una barra y los huecos de cotización son una explicación posible; falta contrastar el calendario y los datos exactos de esos intervalos. Todas mantienen NO_EVALUABLE para fondeo.

Evidencia: [comparación 07](campaign_07/comparison.json), [órdenes incompatibles](campaign_07/funding_session_screen.json). Dos pruebas nuevas reproducen estos rechazos y comprueban que se rechace un resultado alterado que no aplicó el cierre solicitado. No se justifica seguir ajustando estas mismas variantes después de seis rechazos.

## Filtro preliminar de fondeo implementado

El comando funding-screen verifica la evidencia nativa y los hashes de órdenes, confirma instrumento MYM y zona horaria UTC del archivo, convierte las marcas de tiempo a Chicago con cambio estacional y comprueba aperturas o posiciones mantenidas durante los cierres regulares y el fin de semana.

Se usó Topstep únicamente como ejemplo versionado, no como empresa elegida por el usuario. Sus [horarios oficiales](https://help.topstep.com/en/articles/8284206-when-and-what-products-can-i-trade), consultados el 5 de septiembre de 2026, exigen estar sin posiciones a las 15:10 de Chicago y permiten reabrir a las 17:00, con cierre de fin de semana. Aplicar esas reglas actuales a operaciones históricas es una comprobación retrospectiva explícita, no una reconstrucción de las normas históricas.

| Estrategia | Órdenes totales | Incompatibles IS | Incompatibles OOS | Total incompatible |
|---|---:|---:|---:|---:|
| Original | 145 | 24 | 6 | 30 |
| Objetivo corto 270 | 130 | 38 | 11 | 49 |
| Objetivo corto 330 | 128 | 38 | 11 | 49 |

[Resultado completo con ejemplos, procedencia y perfil](campaign_06/funding_session_screen.json). Las tres reciben INCOMPATIBLE_RECORDED_SESSIONS y mantienen NO_EVALUABLE para aprobación. Añadir un cierre obligatorio cambiaría las operaciones: exigiría un nuevo recálculo, no borrar las incompatibles del historial.

Para medir aprobación en ventanas de 1–5 días falta reproducir equity intradía, costes, límites y perfil completo de un examen concreto, incluidos festivos y una muestra final reservada. El [límite máximo de pérdida de Topstep](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit) también se controla con pérdidas no realizadas; sus [parámetros](https://help.topstep.com/en/articles/8284197-trading-combine-parameters) añaden restricciones de consistencia y tamaño. No basta sumar operaciones cerradas. El simulador canónico existente no representa todavía estas reglas SQX completas; no se sustituyeron por una estrategia aproximada para producir una aprobación aparente.

## Búsqueda continua y correcciones de recuperación

El selector exporta como máximo cinco estrategias por trabajo, etiquetadas PRESELECCION_NO_VALIDADA. Filtra beneficio positivo, profit factor ≥1,2, retorno/caída ≥1 y 100/30 operaciones IS/OOS; ordena por el peor retorno/caída y después profit factor. La deduplicación es métrica, no por correlación. El reparto entre activos y temporalidades sigue siendo fijo.

El relevo automático de MCL H4 a MES H4 quedó probado: 271.286 generadas en MCL, 880 elegibles, exactamente cinco archivos nativos exportados; después MES empezó a generar. [Prueba del relevo](automatic_handoff.json). Se descargan métricas para seleccionar, no miles de archivos de estrategias.

Se corrigió el runner para conservar el tiempo nativo consumido al reanudar, adoptar una ejecución ya viva y evitar reintentar ciegamente cargas/inicios no idempotentes. También distingue ausencia de respuesta de un cero real y ya no cuenta como trabajo realizado una búsqueda que generó cero estrategias, aunque tuviera un banco antiguo. Se comprobó mediante reinicio controlado que adoptó MNQ H4 sin relanzarla y siguió avanzando.

[Verificación a las 20:19:15 UTC](engine_delivery_status.json): ambos servicios activos, hashes desplegados iguales a los locales y registro de MNQ H4 a las 20:13:15 con 20.976 generadas, 4.646 en banco y 18 min 38 s de ejecución. La [verificación anterior](runner_resume_verified.json), a las 20:05:34, mostraba 12.923 generadas y 3.922 en banco: existe avance real, además del estado del servicio.

Sigue pendiente un fallo nativo de carga/recursos de MGC H4, que terminó con cero generación. El registro antiguo lo había marcado erróneamente HECHA; la corrección impide repetir esa clasificación, pero no resuelve la causa nativa. No se afirma estabilidad durante varios días ni recuperación de todos los tipos de fallo.

## Implementación y verificación

Se reutilizó la documentación del laboratorio de búsqueda/evolución, uso de SQX/VPS, backtester, procedencia y prevención de falsos resultados. Se contrastó con el [flujo oficial de SQX](https://strategyquant.com/doc/strategyquant/workflow/) y sus comandos de [proyectos](https://strategyquant.com/doc/cli-command-line/project-manage-projects/) y [bancos](https://strategyquant.com/doc/cli-command-line/databank-manage-databanks/).

Archivos principales: scripts/herramientas/sqx_native_improvement.py, ExportNativeOrders.java, sqx_selective_stage.py y m1_runner_sqx.py. Despliegue en /opt/SQX-headless/import/.

El motor admite prepare, run, compare, orders, diagnose y funding-screen. Cada nuevo experimento requiere directorio y proyecto únicos, fuente y plantilla verificadas, cambio de salida revisado y bancos inicialmente vacíos. La precisión efectiva se comprueba contra la solicitada. No cargar repetidamente la misma configuración: SQX puede crear proyectos duplicados.

Han pasado **31 pruebas**: 22 de evidencia/mejora/filtro de sesiones, seis de fallos del runner y tres de reanudación. Incluyen evidencia real y copias alteradas para comprobar rechazo, hashes, precisión efectiva, conciliación, contratos enteros, horarios de invierno/verano, fin de semana y límites horarios. [Salida de pruebas](test_results_verified.txt). Las salidas de pruebas anteriores se conservan como antecedentes.

Hashes locales comprobados contra el despliegue:

- Motor: a14f480a3d1e26273e00d34f9c5984208ef19375a003a5a8ac26a2cd232fc38e
- Runner: b7206eb78f4718479dc5dd3e87f3fd9365f1556611b782683e00cb6145d7817a

Resultado de esta fase: motor acotado ejecutado con datos reales, seis variantes rechazadas, incompatibilidad de horarios detectada y búsqueda con progreso comprobado. No hay aprobación de fondeo ni enlace automático completo entre búsqueda, mejora y validación.

## Cierre verificado a las 23:08 de Madrid

La [comprobación de despliegue](campaign_07/delivery_status.json) confirma ambos servicios activos y los hashes indicados arriba iguales a los archivos locales. MNQ H4 terminó con 14.702 estrategias en banco, 2.016 elegibles por el filtro preliminar y **cinco** seleccionadas. El siguiente trabajo, MYM H4, registra a las 23:07:41 **7.370 generadas y 2.736 en banco**, con seis minutos de ejecución. Esto acredita otro relevo con generación real; no acredita funcionamiento ininterrumpido durante días.

El intento inicial de la campaña 07 quedó bloqueado por la protección de memoria de SQX. Se guardó y verificó íntegramente un banco inactivo de MES H4 antes de vaciarlo de memoria. El archivo queda en la VPS, bajo `/opt/SQX-headless/import/memory_archive_20260905/FONDEO_MES_H4`; no se descargó como selección de candidatas. Su manifiesto está en el directorio superior, `verified_manifest.json`, con SHA-256 `ce554c1564a27123700801748283e3eb3d9e6a7962860810e162ea403ac617fc`. Conserva 20.000 archivos nativos, 854.618.165 bytes, verificados antes de liberar el banco. Tras ello se completó el recálculo 07. Esta recuperación fue manual: el runner aún necesita una política automática de retención y liberación de bancos para que el consumo no vuelva a crecer.

Pendientes en ese corte: recuperación automática de memoria, fallo nativo MGC H4, enlace selectivo hacia mejora, asignación adaptativa y evaluación completa de examen sobre reglas fieles a la estrategia y equity intradía. La actualización siguiente sustituye el estado de recuperación de memoria. No se declara alcanzado el objetivo general ni se presenta ninguna variante rechazada como candidata aprobada.

## Actualización verificada a las 23:39 de Madrid: retención desplegada

Se implementó `sqx_bank_retention.py` y se conectó al cierre persistente del runner. Tras la selección, guarda el banco inactivo en la VPS, comprueba inventario exacto, identidad interna, integridad de los archivos y hashes, sincroniza la copia a disco y vuelve a contrastar las métricas nativas antes de liberar el banco de memoria. No borra archivos históricos ni amplía la entrega de cinco estrategias. La operación se recupera mediante un registro persistente; una respuesta perdida no autoriza repetir el guardado o vaciar una copia incompleta. Exige reserva de disco; si esta se agota, bloquea el archivado. Si falla la selección, conserva el banco en memoria, por lo que aún no garantiza consumo acotado ante todos los fallos.

La prueba real con el banco finalizado de MNQ H4 verificó **14.702 archivos, 648.892.074 bytes**, confirmó después el banco nativo vacío y terminó en `RELEASED` a las 21:39:08 UTC. La llamada inicial de guardado agotó su tiempo mientras SQX seguía escribiendo; se recuperó la misma transacción cuando terminó, sin repetir el guardado. Las **cinco** preseleccionadas conservan sus hashes. Esta prueba invocó directamente el módulo sobre un banco ya finalizado; la próxima clausura automática completa del runner todavía no se ha observado.

El runner actualizado se desplegó con copia previa y se reinició conservando el trabajo nativo. A las 21:39:30 reconoció MYM H4 vivo y lo adoptó sin relanzarlo. Los hashes locales y desplegados coinciden:

- Runner: `183f9d3e9abf301a239af6b7d6fb7a192b574952895fc81832c2d5e90d9636b8`.
- Retención: `56f76d8534dfa3b586461027a320239c4b230a8e4c538ac2b0ea2fcd089c878c`.
- Motor de mejora: sin cambio respecto al hash anterior.

[Evidencia de despliegue, liberación y selección](retention_delivery_status.json). Manifiesto íntegro conservado en la VPS bajo `fondeo/preseleccion/FONDEO_MNQ_H4_r6_20260905T210137067625Z/recovery_bank/transaction.json`, SHA-256 `3417ae9b2f14358102165cf547e285bb2f26758b1d2c40faf899a81cddc113f4`.

Han pasado **47 pruebas específicas**: 22 de mejora/evidencia/sesiones, 12 del runner y 13 de retención. Incluyen respuestas perdidas, guardado incompleto, corrupción, cambios de banco con igual número de registros y recuperación del cierre sin duplicar el historial. Las pruebas de fallos usan transporte simulado y archivos nativos preservados; no son estrategias sintéticas ni resultados financieros. [Salida completa](test_results_retention.txt). No se declara pasada la suite general: tres módulos adicionales necesitan `pytest`, ausente en el entorno usado.

Continúan pendientes el fallo nativo MGC H4, la conexión automática selección–mejora, el reparto adaptativo, la observación del cierre automático con retención y la evaluación completa de examen. Las seis variantes reales siguen rechazadas. Ninguna queda acreditada para superar fondeo en 1–5 días.

## Actualización final: 6 de septiembre, 00:23 de Madrid

### Cuarto experimento real y filtro de horarios

La campaña 08 parte de `Strategy 3.3.135`, MNQ H4, seleccionada previamente entre cinco archivos. Conserva el control con objetivo largo 315 y prueba 285 y 345. Los tres se recalcularon realmente en SQX con precisión M1, contratos enteros y configuración efectiva verificada. No se sustituyeron las reglas por las de otra estrategia ni se aceptaron métricas anteriores al recálculo.

| Resultado nativo | Beneficio IS | Beneficio OOS | Retorno/caída IS | Retorno/caída OOS |
|---|---:|---:|---:|---:|
| Control 315 | 24.261,77 | 11.555,19 | 5,62 | 7,50 |
| Variante 285 | 23.970,76 | 11.917,69 | 5,55 | 7,73 |
| Variante 345 | 28.813,12 | 9.930,18 | 6,68 | 5,54 |

La primera empeora el beneficio y retorno/caída IS; la segunda empeora beneficio, profit factor y retorno/caída OOS. Ambas se rechazan. Estos criterios son una decisión conservadora de investigación, no una demostración de que ninguna otra modificación pueda funcionar. El OOS utilizado para desarrollar variantes no equivale a una muestra final intacta.

El filtro de sesiones ahora comprueba el instrumento nativo MYM o MNQ y su zona UTC; rechaza instrumentos y zonas no soportados. Usando las [sesiones regulares oficiales de Topstep](https://help.topstep.com/en/articles/8284206-when-and-what-products-can-i-trade), detecta respectivamente **43, 41 y 46 operaciones incompatibles** en el control y las dos variantes MNQ. Ver [filtro y ejemplos](campaign_08/funding_session_screen.json), [comparación](campaign_08/comparison.json) y [diagnóstico de órdenes](campaign_08/orders_diagnostic.json). Los festivos y el perfil completo de examen siguen pendientes. `NO_EVALUABLE` y `probada_para_fondeo=false` se mantienen.

Métricas de campaña SHA-256: `cd49f28d8bf0fc5f3dfb9ff3d09463e21c48cc4a6d4f92137dab8416f5df7a1f`. Los archivos nativos, órdenes, configuración efectiva y manifiesto de este experimento pequeño se preservan en `campaign_08/`.

### Recuperación de memoria y siguiente generación comprobadas

Una nueva protección de memoria nativa bloqueó inicialmente la carga del experimento; el motor detectó el error nuevo y no repitió la carga. Se comprobó una copia de recuperación ya existente del banco inactivo MNQ H1: 20.000 archivos íntegros, 1.061.720.116 bytes y métricas iguales al banco vivo. Tras verificarla y sincronizarla se liberó el banco, sin descargarlo ni volver a guardarlo. La transacción queda en la VPS en `/opt/SQX-headless/import/fondeo/retention_existing_MNQ_H1_20260905/transaction.json`, SHA-256 `d41bc7f66b4b1c72d0deffcdb787fecb700939b858cdc47f18fb507433236899`. La campaña 08 pudo completarse después.

El cierre automático posterior del runner ya está demostrado: MYM H4 terminó con 83.880 generadas, 20.000 en banco, 249 elegibles preliminares y **cinco preseleccionadas**. A las 22:14:33 UTC terminó el archivado verificado y la liberación de memoria (`RELEASED`), y arrancó M6E M15. A las 22:23:07 UTC, el estado nativo de M6E M15 mostraba **10.603 generadas en 8 min 33 s, cero aceptadas y cero en banco**. Se acredita generación real, no selección de calidad en esa nueva celda.

[Prueba del despliegue, transacción y estado nativo](campaign_08/delivery_status.json). Transacción automática SHA-256: `e52c338743a7bc6ba225ad98296c3dfb94456f98af7757d7c22ce4e2dfc51b2f`. La copia completa de recuperación permanece en la VPS; no es una entrega masiva al siguiente paso. El archivado consume disco y tiempo: la reserva de espacio bloquea si falta capacidad, pero aún no existe una política que limite el crecimiento histórico indefinido.

### Verificación y límite vigente

Las **27 pruebas del motor nativo** pasan tras el último cambio; incluyen las órdenes reales MNQ, sus tres rechazos por horario y el rechazo de instrumento/zona no soportados. [Salida de esta ejecución](test_results_native_final.txt). Las 12 pruebas del runner y 13 de retención habían pasado en la ejecución anterior; esos módulos no cambiaron después. No se presenta esto como una ejecución de la suite general.

Los tres servicios comprobados están activos. Hashes desplegados iguales a los locales:

- Motor: `f2a8d14c6b9d940cfa8042f9bd31db3b7b4dba65a46ae832da149c80f07152d4`.
- Runner: `183f9d3e9abf301a239af6b7d6fb7a192b574952895fc81832c2d5e90d9636b8`.
- Retención: `56f76d8534dfa3b586461027a320239c4b230a8e4c538ac2b0ea2fcd089c878c`.

**Base comprobada:** comparación nativa de mejoras acotadas, ocho variantes rechazadas, filtro de incompatibilidades horarias, selección máxima de cinco por trabajo y cierre automático con recuperación de memoria. **No completado:** optimización general, conexión automática selección–mejora, reparto adaptativo, fallo MGC H4 y evaluación de examen en 1–5 días con equity intradía, calendario completo y evidencia final reservada. No hay estrategia acreditada para fondeo ni se declara terminado el objetivo general.

## Actualización: 6 de septiembre, 00:57 de Madrid

### Motor instalado: mejora y decisión posterior al recálculo

`sqx_native_improvement.py run` ahora termina automáticamente con una evaluación persistente: vuelve a comprobar procedencia, reglas, configuración efectiva, métricas y órdenes nativas; compara las dos variantes con su control; aplica el filtro de sesiones; y deja una decisión y su siguiente acción. Una mejora de desarrollo incompatible con las sesiones queda en `NEEDS_SESSION_REPAIR`. Un error de evidencia revoca cualquier resultado anterior y deja la evaluación bloqueada. Una variante que llegue a `READY_FOR_INDEPENDENT_VALIDATION` tampoco está certificada para fondeo.

El despliegue conserva copia previa en la VPS. El SHA-256 local y remoto del motor coincide: `370eb1cb86ee59346b97c86cb7d52c91edec79a2869afc1b2e90756639ddacc8`. Pasan **31 pruebas del motor**, incluida la imposibilidad de promover una mejora que incumple sesiones y la revocación de una evaluación anterior ante evidencia inválida. [Salida de pruebas](test_results_assessment.txt). Runner y retención no han cambiado en esta actualización.

### Campaña 09: mejora medible, todavía incompatible

MNQ H4, control 315 y variantes 285/345, todos recalculados con horario experimental UTC 00–19. La variante 345 mejora el beneficio IS de 15.959,28 a 16.892,34 y OOS de 4.745,23 a 5.270,23; el retorno/caída pasa de 2,48/1,13 a 2,85/1,25. Cumple el filtro de mejora de desarrollo, pero conserva **33 operaciones incompatibles** con el cierre regular. Resultado automático: `NEEDS_SESSION_REPAIR`, cero candidatas al siguiente paso. La variante 285 se rechaza por deterioro de métricas. [Decisión y hashes](campaign_09/assessment.json).

### Campaña 10: prueba de cierre a las 16 UTC

La documentación de [opciones de negociación SQX](https://strategyquant.com/doc/strategyquant/trading-options/) describe el cierre al terminar el intervalo. La inspección del código nativo instalado indica dependencia del cierre de barra en el motor TS; que una hora esté configurada no prueba que todas las operaciones la respeten. Se ensayó 16 UTC, alineado con las barras H4, sin modificar código del proveedor ni eliminar operaciones retrospectivamente. Esta es una hipótesis experimental, no una atribución causal demostrada de todos los fallos anteriores.

Los tres archivos se recalcularon y evaluaron automáticamente. Resultados de desarrollo:

| Resultado nativo | Beneficio IS | Beneficio OOS | Retorno/caída IS | Retorno/caída OOS | Operaciones IS/OOS |
|---|---:|---:|---:|---:|---:|
| Control 315 | 9.844,98 | 8.520,23 | 1,26 | 4,84 | 154/26 |
| Variante 285 | 9.751,83 | 8.070,23 | 1,63 | 4,59 | 156/26 |
| Variante 345 | 9.945,49 | 8.970,23 | 1,33 | 5,10 | 153/26 |

La variante 345 mantiene mejoras frente a su nuevo control, pero las **26 operaciones OOS** quedan por debajo del mínimo de investigación fijado antes de la prueba (30). Además, queda una operación incompatible en los tres archivos: 19 de junio de 2024, 05:50–22:07 UTC. En la variante 345 se reducen los incumplimientos observados de 33 a uno, a costa de cambiar también el conjunto de operaciones y sus resultados. No equivale a reparar por completo las sesiones ni a demostrar robustez. No se reduce el umbral ni se excluye ese día para obtener un aprobado.

La campaña termina con ambas variantes bloqueadas para promoción, cero candidatas y `probada_para_fondeo=false`. [Evaluación](campaign_10/assessment.json), [órdenes y sesiones](campaign_10/funding_session_screen.json), [comparación nativa](campaign_10/comparison.json). Se preservan únicamente el control y dos variantes de este experimento, con sus entradas, salidas nativas y archivos de prueba.

### Búsqueda continua y alcance real

A las 22:57 UTC se comprobaron activos `m1-runner`, `sqx-headless` y `ultrarentable-supervisor`. M6E M15 avanzó de 40.123 generadas a las 22:45 a **53.498 generadas y 801 en banco** a las 22:55. Esto demuestra progreso durante los experimentos; no acredita calidad de esas 801 estrategias. La entrega sigue limitada a cinco preseleccionadas por trabajo y el archivo de recuperación permanece en la VPS. [Comprobación de despliegue y búsqueda](campaign_10/delivery_status.json).

El motor de mejora acotada y descarte está implementado y ejecutado. **No se ha implementado la certificación completa de un examen**, ni el enlace automático desde cada selección. Para la siguiente fase faltan calendario completo, ejecución fiel con equity intradía y reglas del examen fechadas, así como evaluación final reservada de ventanas de 1–5 días que incluya los intentos fallidos. Los datos OOS ya utilizados para seleccionar cambios son datos de desarrollo. La [regla oficial de pérdida máxima](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit) considera pérdidas intradía no realizadas: sumar beneficios de operaciones cerradas no basta. Los [parámetros de Trading Combine](https://help.topstep.com/en/articles/8284197-trading-combine-parameters) requieren al menos dos días; el objetivo de un día no se aplicaría a ese perfil.


## Actualización: 6 de septiembre, 01:22 de Madrid

### Ventanas de 1–5 días implementadas y desplegadas

La evaluación posterior al recálculo ahora recorre todas las ventanas completas de uno a cinco días laborables, incluyendo inactividad, y registra el objetivo, consistencia, límites de contratos, pérdida máxima al cierre y posibles incumplimientos mientras la operación permanece abierta. Los cruces de sesión, operaciones superpuestas y evidencias no soportadas impiden interpretar una ventana como válida. Un error revoca el informe anterior.

Se utiliza un perfil explícito de ejemplo Topstep 50k: objetivo 3.000, pérdida móvil al cierre de 2.000 y consistencia del mejor día del 50 %, con DLL opcional desactivado. No representa todas las empresas. Fuentes oficiales: [pérdida máxima](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit), [consistencia](https://help.topstep.com/en/articles/8284208-consistency-at-topstep), [parámetros](https://help.topstep.com/en/articles/8284197-trading-combine-parameters) y [sesiones](https://help.topstep.com/en/articles/8284206-when-and-what-products-can-i-trade).

### Resultado que orienta la siguiente decisión

En la campaña 10, las tres versiones tienen 186 ventanas OOS de cinco días: **152 sin operaciones, 17 sin alcanzar objetivo, 15 no soportadas y dos que alcanzan el objetivo en este diagnóstico**. Las dos últimas comparten las mismas operaciones de mayo de 2026; no son dos exámenes independientes. La baja frecuencia y concentración temporal no justifican presentar esta base H4 como una solución habitual de aprobación rápida.

Además, SQX dimensiona estas operaciones usando el saldo acumulado del historial. Su código nativo instalado utiliza el saldo actual para `RiskFixedBalancePct`. Recortar esas operaciones por fechas no reproduce un examen que comienza con saldo nuevo. Por ello el resultado mantiene `fresh_account_sizing=NOT_RETESTED`, `funding_verdict=NO_EVALUABLE` y `probada_para_fondeo=false`. El cálculo con MAE solo señala posibles pérdidas intradía; faltan trayectoria exacta, calendario de cierres especiales y evaluación final reservada. Los datos OOS usados aquí son de desarrollo.

Decisión: no seguir ajustando esta estrategia contra las mismas ventanas para fabricar un aprobado. La mejora nativa existe y produce decisiones reproducibles; una futura prueba de examen necesita reiniciar tamaño y estado de entradas por intento y verificar ejecución y datos. La conexión automática desde cada selección hacia la mejora sigue pendiente.

### Verificación del entregable y continuidad

Pasan **41 pruebas en 19,870 segundos**, incluidas aritmética de límites, consistencia, días sin operaciones, órdenes fuera de horario y revocación ante alteraciones de evidencia real. [Salida](test_results_funding_windows.txt). No se ha ejecutado de nuevo la suite general.

El motor desplegado tiene SHA-256 `f16a95bfd525ee97286b6b5fad725d71d2a8f0199aff74879150cbc052e71b4b`, igual al local. Se conserva el anterior en `/opt/SQX-headless/import/sqx_native_improvement.before_windows_20260906.py`. La evaluación real en la VPS finalizó correctamente y produjo contenido idéntico al informe local; sus bytes difieren solo por finales de línea entre sistemas. Se guarda [el informe remoto original](campaign_10/funding_windows_deployed.json), cuyo hash `acb429491c2f5dfed1a0f684c6b34967efac05431ecbd33e382327297ff68ab2` coincide con [la evidencia de despliegue](campaign_10/delivery_windows.json).

A las 23:20:53 UTC, M6E M15 cerró con 1.711 en banco, ocho que superaban el filtro preliminar y **solo cinco preseleccionadas**. Verificó su copia de recuperación, liberó memoria y arrancó MCL M15 automáticamente. A las 23:22 UTC estaban activos runner, SQX y supervisor. La selección preliminar no demuestra que esas cinco estén probadas para fondeo.

## Actualización: 6 de septiembre, 01:54 de Madrid

### Intento desde capital inicial: bloqueo concreto, no resultado de fondeo

La campaña 11 recalculó en SQX las tres versiones de MNQ H4 de la campaña 10, sin cambiar sus archivos de entrada, con capital inicial de 50.000 y rango 4–8 de mayo de 2026. El recálculo nativo terminó correctamente: tres resultados, cero operaciones en los tres. Esa semana se eligió porque había alcanzado el objetivo en el diagnóstico del historial continuo; es una muestra de desarrollo conocida, no una prueba final independiente.

La inspección de las reglas efectivas encontró Highest/Lowest con periodo **455 velas H4**, además de MACD con periodo lento 190. Los cinco días solicitados contienen como máximo **30 velas H4**. No está verificado que este recorrido de SQX haya cargado historia anterior suficiente para inicializar los indicadores. Por ello, las cero operaciones no demuestran que la estrategia carezca de utilidad, ni que la prueba reproduzca correctamente una cuenta nueva.

El motor registra ahora `BLOCKED_UNVERIFIED_INDICATOR_INITIALIZATION`, conserva los resultados nativos y mantiene `NO_EVALUABLE`, `probada_para_fondeo=false` y cero candidatas. El diagnóstico del periodo es un límite inferior extraído de las reglas; no es un cálculo completo de calentamiento para todos los indicadores.

La corrección pendiente consiste en separar la historia de inicialización del intervalo negociable, impedir operaciones antes del comienzo del intento y verificar que el capital y las posiciones arrancan limpios. No se ha implementado ni acreditado todavía esa separación. También siguen pendientes la trayectoria intradía, procedencia exacta de datos, calendario y prueba final reservada. La búsqueda de fuentes instaladas encontró un bloque nativo CurrentDate que podría servir para ensayar una restricción explícita de entradas, pero no se ha incorporado ni probado.

Evidencia: [evaluación de cuenta nueva](campaign_11/fresh_attempt_assessment.json), [registro nativo](campaign_11/native_retest.log), [manifiesto de entradas y configuración](campaign_11/manifest.json).

### Verificación y búsqueda continua

Pasan **46 pruebas en 27,847 segundos**, incluyendo reproducción del bloqueo con los archivos reales de la campaña 11 y revocación del informe ante métricas alteradas. [Salida de pruebas](test_results_fresh_attempt.txt). La reevaluación en la VPS terminó correctamente sin repetir el recálculo nativo. El motor remoto y el local tienen el mismo SHA-256: `37acec92400888a32fc2c2c95c3750f13bf6bea3074887d6f06bf0e8c65d4594`. También se verificó el hash del informe recuperado. [Comprobación de despliegue](campaign_11/delivery_status.json).

A las 23:54 UTC estaban activos runner, SQX y supervisor. MCL M15 pasó de 30.000 generadas a las 23:41 a **43.651 generadas y 587 en banco** a las 23:51. La búsqueda sigue avanzando; esas cantidades no son estrategias aprobadas. La entrega continúa limitada a cinco preseleccionadas por trabajo. La conexión automática selección → mejora permanece pendiente.


## Actualización histórica: 6 de septiembre, 02:30 de Madrid

### Resultado y decisión

El motor de mejora acotada está desplegado y ejecuta recálculos nativos, comparación con un control, verificación de órdenes y descarte. La evaluación para fondeo sigue siendo preliminar. No hay una estrategia aprobada ni se ha conectado automáticamente selección y mejora.

Las campañas 12 y 13 configuran historia desde enero de 2023 y restringen las entradas a la semana diagnóstica del 4–8 de mayo de 2026. La 13 usa el bloque nativo GetDate. SQX finalizó los tres recálculos, pero todos produjeron cero operaciones. Cambiar la representación de fechas no resolvió el síntoma. La configuración guardada no prueba que los indicadores se inicializaran correctamente ni que el filtro de entradas se ejecutara como se esperaba; tampoco permite concluir que faltaran señales. No se atribuye una causa que aún no está demostrada.

El informe vigente registra **BLOCKED_UNVERIFIED_FRESH_ACCOUNT_EXECUTION**, **NO_EVALUABLE**, **probada_para_fondeo=false** y ninguna candidata para el siguiente paso. Se conserva cada entrada, resultado y orden nativa. No se rebajan criterios para obtener un aprobado. Quedan pendientes la ejecución verificada desde cuenta nueva, datos fieles al instrumento, calendario completo, equity intradía y evaluación final reservada.

Evidencia: [informe nativo de campaña 13](campaign_13/fresh_attempt_assessment.json), [recálculo nativo](campaign_13/native_retest.log) y [verificación de entrega](delivery_status_latest.json).

### Verificación y continuidad

Pasan **48 pruebas específicas en 25,766 segundos**, incluida la reproducción de las cero operaciones reales y su bloqueo. [Salida completa](test_results_improvement_final.txt). Una búsqueda más amplia con unittest ejecutó 73 pruebas correctamente, pero encontró tres errores de importación por ausencia de pytest; esa comprobación general queda incompleta y no se presenta como aprobada.

El archivo local y el desplegado coinciden en SHA-256 `c860ed4c8b76ff56fea55df16ac0c7e6bcd0a5759bb8004fa47b4ceace01605b`. La reevaluación remota coincide con el informe recuperado. A las 00:30 UTC estaban activos m1-runner y sqx-headless. A las 00:27 UTC, MCL M15 terminó con 1.174 en banco, 104 que superaron el filtro preliminar y **solo cinco preseleccionadas**; conservó la copia de recuperación en la VPS, liberó memoria y arrancó MES M15. Es prueba de continuidad y selección limitada, no de rentabilidad ni aprobación de examen.

## Actualización histórica: 6 de septiembre, 03:23 de Madrid

El motor desplegado ya recalcula una estrategia y dos variantes con historia previa, capital inicial limpio y entradas restringidas al intervalo solicitado. En este recorrido, usar la fecha de la vela (`BarDate`) resolvió las cero operaciones observadas con `CurrentDate`. La campaña 16 reprodujo las ocho operaciones del control en la semana elegida; la campaña 17 reprodujo esas mismas operaciones para la base y ejecutó ambas variantes. Esto acredita la ejecución nativa del intervalo, sin demostrar todavía la convergencia completa de los indicadores.

Las tres versiones produjeron ocho operaciones cada una. Sus resultados netos diagnósticos fueron 8.173,38 para la base, 7.948,38 para EXIT90 y 8.398,38 para EXIT110, sobre capital inicial 50.000. La semana del 4–8 de mayo se seleccionó porque ya era favorable en el historial de desarrollo: estos resultados no son evidencia independiente, ni una probabilidad de aprobar. Una ganancia mayor en esa semana no acepta una mejora.

**Resultado: cero mejoras aceptadas y cero estrategias aprobadas para fondeo.** Se conserva el rechazo previo de las variantes: solo 26 operaciones fuera de muestra frente al mínimo fijado de 30, datos proxy cuya fidelidad al instrumento no está verificada, trayectoria intradía exacta y calendario incompletos, y ausencia de prueba final reservada. El estado pasa a `NATIVE_WINDOW_EXECUTED_FUNDING_UNVERIFIED`, manteniendo `NO_EVALUABLE`, `probada_para_fondeo=false` y ninguna candidata para la fase siguiente.

Pasan **50 pruebas específicas en 27,256 segundos**, incluidas reproducción de órdenes reales contra el control, capital inicial, integridad de evidencia y ausencia de promoción indebida. La reevaluación local coincide exactamente con el informe remoto. Motor y runner desplegados coinciden con los archivos locales; SHA-256 del motor: `3319511e0b08180210959c5484a14ec035ca60f0879183d03fe4202e417dd27b`. La comprobación general anterior sigue incompleta por tres errores de importación de pytest; no se presenta como aprobada.

También se desplegó el cierre anticipado de lotes cuando el banco supera el umbral de memoria, con selección, copia verificada en la VPS y liberación antes de continuar. El umbral se comprueba periódicamente y puede sobrepasarse entre comprobaciones. El último lote MES entregó solo cinco preseleccionadas, conservó su copia en la VPS y dio paso a MGC M15, que mostraba avance real a las 01:20 UTC. Ambos servicios estaban activos a las 01:23 UTC. Esto demuestra continuidad observada, no garantiza ausencia futura de caídas. La conexión automática de cada selección con este motor de mejora sigue pendiente.

Evidencia vigente: [pruebas](test_results_bar_date_final.txt), [informe nativo](native_improvement_20260906_17/fresh_attempt_assessment.json), [verificación de despliegue y continuidad](delivery_status_latest.json).

## Actualización histórica: 6 de septiembre, 04:36 de Madrid

### Entrega y resultado

Está implementado y desplegado el motor acotado: prepara una estrategia real y dos variantes, las recalcula en SQX, verifica sus archivos y operaciones, compara resultados y registra aceptación para investigación o rechazo. También ejecuta un diagnóstico de ventanas de 1–5 días y pruebas nativas de un intento desde capital inicial. **No constituye una validación completa para fondeo y aún no está conectado automáticamente a cada lote de preselección.**

La campaña 18 utilizó la estrategia MNQ M15 `Strategy 1.18.140`, seleccionada del lote real de 5.502 estrategias. Ensayó cambios del objetivo de beneficio de las compras de 545 a 490,5 y 599,5, manteniendo iguales las demás condiciones del experimento. Los tres recálculos nativos finalizaron; se conservaron tres resultados, no miles de estrategias descargadas.

| Resultado nativo | Beneficio IS | Beneficio OOS | Factor de beneficio IS/OOS | Retorno/caída IS/OOS | Operaciones IS/OOS |
|---|---:|---:|---|---|---|
| Base | 36.702,00 | 20.066,85 | 1,89 / 3,14 | 13,74 / 15,20 | 320 / 74 |
| Objetivo −10 % | 35.583,89 | 19.291,83 | 1,84 / 2,99 | 13,22 / 15,98 | 326 / 76 |
| Objetivo +10 % | 39.592,34 | 20.458,20 | 2,01 / 3,18 | 16,68 / 13,48 | 313 / 71 |

**Ambas variantes quedan descartadas.** La primera empeora varias métricas; la segunda aumenta el beneficio pero empeora el retorno/caída fuera de muestra. Además existen incumplimientos de sesión y un problema de ejecución que bloquea cualquier promoción. Estas cifras son resultados históricos de desarrollo, no ganancias obtenidas ni probabilidad de aprobar un examen.

### Problema de ejecución localizado

Las 79 operaciones cortas cierran inmediatamente por el motivo nativo de objetivo de beneficio y resultan negativas después de costes. Al leer los precios originales, **27 tienen el objetivo en el lado desfavorable, 19 exactamente en la entrada y 33 ligeramente a favor**: son 46 objetivos con distancia no positiva, no 79. Las distancias de las ventas abarcan de −0,121 a 0,12 unidades de precio. El motor registra esta anomalía e impide promover la estrategia. La causa exacta del cálculo del objetivo porcentual sigue sin demostrarse; este diagnóstico no la repara.

El lector de órdenes y el motor se actualizaron y desplegaron con copia previa. Se volvió a evaluar una copia de los resultados nativos existentes, sin repetir el recálculo ni modificar la evidencia original de la campaña 18. El informe resultante conserva `NO_EVALUABLE`, `probada_para_fondeo=false` y ninguna candidata para la fase siguiente.

### Verificación y búsqueda

Pasan **51 pruebas específicas en 28,458 segundos**. Una evaluación local aislada reproduce exactamente las decisiones de la VPS y se verificaron los hashes de archivos e informe. Motor desplegado: `a759c3b887ca7dfcc97243404e6935bedad21fa3ba962f352074f074d928c73a`. Lector desplegado: `f9da4580b0bbe555d9504a63e199881597903a3d426a47fd4cd1d1e2a1c9fb7c`. La comprobación general anterior sigue incompleta por ausencia de pytest; no se presenta como aprobada.

A las 02:36 UTC seguían activos SQX y el runner. M6E M5 pasó de 4.349 generadas a las 02:21 a 8.911 a las 02:31, todavía sin resultados en banco. Los lotes MNQ M15 y MYM M15 terminaron con 5.502 y 5.173 en banco, respectivamente, entregaron **cinco preseleccionadas cada uno**, verificaron su copia de recuperación en la VPS, liberaron memoria y continuaron con el siguiente trabajo. La preselección no equivale a estrategias probadas para fondeo.

**Pendiente:** resolver la ejecución anómala de esta base o descartarla; conectar selección y mejora con control de recursos y reintentos; verificar datos, trayectoria intradía, calendario y reglas completas del examen, y evaluar en datos finales reservados. Resultado acumulado de esta entrega: cero mejoras aceptadas y cero estrategias aprobadas para fondeo.

Evidencia: [evaluación vigente](native_improvement_20260906_18_exit_review_20260906T023129Z/assessment.json), [órdenes y diagnóstico](native_improvement_20260906_18_exit_review_20260906T023129Z/orders_diagnostic.json), [verificación local](native_improvement_20260906_18_exit_review_20260906T023129Z/local_verification.json), [51 pruebas](test_results_native_pt_final.txt), [despliegue y avance observado](delivery_status_latest.json).


## Actualización vigente: 6 de septiembre, 05:02 de Madrid

El motor añade `run-reviewed`: ejecuta una receta revisada de una base y dos variantes, comprueba integridad y memoria disponible, recalcula en SQX y conserva la evaluación. Registra la identidad del experimento para impedir repeticiones aunque cambie el nombre del proyecto. Una ejecución incierta bloquea otro trabajo hasta reconciliar su estado; no reintenta a ciegas. Se verificó en la VPS que un segundo lanzamiento del experimento 19 fue rechazado antes de ejecutar SQX. Esto automatiza un experimento preparado, no conecta todavía toda la selección con la mejora.

La campaña 19 ensayó dos objetivos fijos para las ventas de la misma base MNQ M15: 297 y 363 puntos. Son hipótesis nuevas, no una conversión equivalente del objetivo porcentual original. Ambas eliminan los objetivos de beneficio con distancia no positiva observados en sus operaciones cortas. No queda demostrada una reparación general de StrategyQuant.

| Comparación de desarrollo | Base | Objetivo 297 | Objetivo 363 |
|---|---:|---:|---:|
| Beneficio fuera de muestra | 20.066,85 | 17.128,93 | 17.458,93 |
| Factor de beneficio fuera de muestra | 3,14 | 1,91 | 1,93 |
| Caída máxima fuera de muestra | 1.320,16 | 3.505,60 | 3.340,60 |

Las dos variantes empeoran rendimiento y riesgo fuera del periodo de ajuste; además mantienen incompatibilidades de sesión. **Ambas rechazadas, cero mejoras aceptadas y cero estrategias acreditadas para fondeo.** La prueba final reservada no se consume para rescatar estas variantes. Estos resultados son históricos de desarrollo.

Pasan 53 pruebas específicas en 27,248 segundos. Se comprobaron localmente los 27 archivos copiados contra sus hashes remotos y la coincidencia del motor local con el desplegado. La comprobación general anterior permanece incompleta por tres errores de importación; no se declara aprobada. El detalle de esta verificación se conserva junto al experimento.

SQX y el buscador seguían activos a las 03:02:54 UTC. El lote M6E M5 pasó de 8.911 intentos a las 02:31 a 22.624 a las 03:01, con tres estrategias en banco. La búsqueda sigue independiente de este motor; solo la preselección limitada de cada lote se destina al siguiente paso. No se ha demostrado todavía el ciclo automático completo ni una candidata apta para aprobar en 1–5 días.

Evidencia: [evaluación](native_improvement_20260906_19/assessment.json), [órdenes y diagnóstico](native_improvement_20260906_19/orders_diagnostic.json), [verificación local](native_improvement_20260906_19/local_verification.json), [despliegue, bloqueo de repetición y avance](native_improvement_20260906_19/delivery_verification.json).


## Conexión automática comprobada — 6 de septiembre, 05:38 de Madrid

La receta `fixed_pt_first_exit_inward_10pct_integer_m1_v1` seleccionó Strategy 3.3.135 del manifiesto de MNQ H4. Recalculó el objetivo original 315 y las variantes 284 y 346, con contratos enteros y precisión M1. Los límites se redondean hacia dentro para no exceder el cambio del 10 %. La campaña anterior sobre esta estrategia usó otros valores: esta ejecución demuestra la conexión automática y no se presenta como el descubrimiento de una estrategia nueva.

Ambas variantes recibieron `DROP_VARIANT`: la primera empeoró métricas IS y la segunda métricas OOS. Además conservaron operaciones incompatibles con las sesiones comprobadas. `next_stage_candidates` quedó vacío y `probada_para_fondeo` permanece falso. Tras conservar y verificar la evidencia, se eliminó únicamente el proyecto temporal de este experimento para liberar recursos.

El servicio `sqx-improvement.service` y su temporizador están instalados. La revisión posterior terminó correctamente en `WAITING_FOR_SUPPORTED_SELECTED_STRATEGY`, sin volver a ejecutar la receta completada. Los cuatro archivos desplegados coinciden por SHA-256 con los locales. La siguiente revisión estaba programada para las 06:34 de Madrid.

Si hay una ejecución interrumpida o incierta, el motor bloquea nuevos experimentos hasta conciliar su estado; no se atribuye recuperación autónoma completa. Se mantienen los resultados y el registro de identidad para evitar reintentos ciegos. Los tipos de estrategia fuera de esta receta se omiten hasta incorporar una receta comprobada.

Evidencia actual: [estado del despliegue y avance de búsqueda](delivery_status_latest.json), [verificación local de 27 archivos y decisiones](auto_improvement_b3759bbecb952595a437/local_verification.json), [evaluación automática](auto_improvement_b3759bbecb952595a437/assessment.json), [paquete de evidencia](automatic_improvement_verified.zip).

## Estado vigente — 6 de septiembre, 06:49 de Madrid

El motor de mejora limitado está desplegado y conectado a la preselección: toma una base compatible, prepara dos variantes del objetivo de beneficio, ejecuta los tres recálculos nativos y compara operaciones y métricas de desarrollo. La selección por lote conserva como máximo cinco preseleccionadas. La receta automática actual admite bases MYM/MNQ con objetivo fijo compatible; no cubre aún todas las formas de estrategia. Rechazar una variante es un resultado útil del motor, pero no demuestra que se haya encontrado una mejora.

Se corrigió un bloqueo concreto de ejecución: SQX rechazaba un experimento por una sesión `regular` ausente de sus recursos registrados. El motor ahora guarda ese rechazo y falla inmediatamente, en lugar de esperar a una tarea que no arrancó. El experimento rechazado quedó reconciliado y conservado. No se modificaron las sesiones de los proyectos de generación.

Para comprobar datos de futuros disponibles en SQX, se hizo un experimento separado con `@EW`, un contrato y la sesión registrada `US_Index_Futures` (08:30–15:00, hora del mercado). Cambiar instrumento y sesión constituye una hipótesis nueva: no equivale a validar la estrategia original MNQ. Comisión 5 y deslizamiento 2 son supuestos del experimento, pendientes de contraste. Los tres recálculos finalizaron y sus órdenes cuadran con las métricas exportadas.

| Resultado de desarrollo en @EW | Base | Objetivo −10 % | Objetivo +10 % |
|---|---:|---:|---:|
| Beneficio IS | −10.080 | −9.770 | −8.131 |
| Beneficio OOS | −1.069 | −1.069 | −1.069 |
| Operaciones IS / OOS | 40 / 1 | 40 / 1 | 39 / 1 |

Las dos variantes se rechazan por pérdidas y muestra insuficiente. **Resultado acumulado: cero mejoras aceptadas y cero estrategias acreditadas para fondeo.** No procede optimizar repetidamente esta base para rescatarla. El diagnóstico de fondeo sigue incompleto: faltan datos y ejecución verificados para cada instrumento, trayectoria intradía independiente, calendario y perfil completo del examen y una prueba final reservada. Los diagnósticos de ventanas de 1–5 días existentes no certifican aprobación.

Pasan **55 pruebas específicas del motor en 26,128 segundos**, incluidas detección del rechazo nativo y aceptación de la respuesta real de un arranque correcto. Las siete pruebas del programador automático pasaron anteriormente. La comprobación general histórica con tres errores por falta de pytest permanece incompleta. Se verificaron los 48 archivos del paquete @EW contra sus hashes remotos y se reprodujo localmente la comparación, que coincide exactamente. Solo se recuperó un paquete de 608.352 bytes de este experimento, no el banco masivo de estrategias ni las barras históricas.

SHA-256 del motor local y remoto: `996ec9ff2a177b6168e0a87aa859e34527f64573d240eafee1027c536dee6140`. A las 04:48:51 UTC estaban activos SQX, el buscador y el temporizador de mejora, restaurado tras la prueba. La ejecución automática terminó correctamente esperando otra base compatible, sin duplicar una receta completada. MES M5 avanzó de 5.208 intentos a las 04:36 UTC a 10.343 a las 04:46 UTC. Esto acredita búsqueda en curso; una incidencia anterior requirió recuperación manual, por lo que no se declara recuperación autónoma completa.

Evidencia vigente: [comparación @EW](ew_real_transfer_20260906/cash_session_experiment/comparison.json), [proveniencia de la sesión](ew_real_transfer_20260906/cash_session_experiment/session_provenance.json), [recálculo nativo](ew_real_transfer_20260906/cash_session_experiment/native_retest.log), [verificación local](ew_real_transfer_20260906/local_verification.json), [despliegue y búsqueda](delivery_status_latest.json), [paquete verificado](ew_real_transfer_verified.zip).


## Estado vigente — 6 de septiembre, motor de mejora nativa comprobado

Se amplía la receta anterior de cambiar un objetivo fijo con una búsqueda nativa acotada de salidas en SQX. Se conservan las reglas de entrada y la estrategia original; el mejorador explora parámetros de salida y exporta como máximo dos variantes distintas. La búsqueda general continúa y entrega como máximo cinco preseleccionadas por lote. Preseleccionada no significa probada para fondeo. El método aprovecha proyectos, evolución y operaciones selectivas de bancos documentadas por SQX: [flujo oficial](https://strategyquant.com/doc/strategyquant/workflow/), [Builder](https://strategyquant.com/doc/strategyquant/builder/), [gestión de bancos](https://strategyquant.com/doc/cli-command-line/databank-manage-databanks/).

El motor automático elige una base compatible, registra su identidad y procedencia, ejecuta una búsqueda pequeña, recalcula original y variantes con contratos enteros y precisión M1, y coteja las operaciones exportadas con las métricas nativas. Impide ejecuciones solapadas y repetir la misma receta sobre la misma fuente. Exige memoria y disco disponibles y conserva la evidencia antes de liberar el proyecto temporal. La receta actual está limitada a las estructuras de entrada MYM/MNQ comprobadas; no se presenta como un mejorador universal.

Se corrigió un defecto concreto: cuando la búsqueda devolvía una sola variante válida, la etapa la descartaba porque esperaba exactamente dos. Ahora admite una o dos, conserva siempre la base y exige que el número de resultados nativos coincida. Se recuperó la variante ya obtenida sin repetir la búsqueda.

La ejecución automática real del 06/09 a las 06:23 UTC comparó Strategy 1.18.140 (MNQ M15) con su variante nativa:

| Métrica nativa | Original | Variante |
|---|---:|---:|
| Beneficio IS | 36.702,00 | 35.459,93 |
| Beneficio OOS | 20.066,85 | 19.248,28 |
| Profit factor IS / OOS | 1,89 / 3,14 | 1,86 / 3,13 |
| Retorno / caída IS | 13,74 | 11,32 |
| Retorno / caída OOS | 15,20 | 17,71 |
| Operaciones IS / OOS | 320 / 74 | 321 / 74 |

**Variante rechazada automáticamente.** Mejorar un único indicador OOS no compensa las regresiones de beneficio, profit factor y retorno/caída IS. Además, original y variante requieren revisión de ejecución; la variante tiene 41 operaciones IS y 9 OOS incompatibles con las sesiones comprobadas. La causa de las anomalías de cierre no está resuelta. El resultado conserva cero candidatas para la siguiente validación y `probada_para_fondeo=false`.

El criterio de promoción de esta receta exige ausencia de regresión en beneficio, profit factor y retorno/caída de desarrollo, una mejora mínima del 5 % en el peor retorno/caída y ausencia de bloqueos de ejecución y sesiones. Es una regla de desarrollo revisable, no una garantía estadística ni una certificación de fondeo. Los bloques IS/OOS usados para seleccionar variantes dejan de ser una prueba final reservada.

La evaluación preliminar conserva ventanas históricas de 1–5 días. Para acreditar un examen siguen faltando procedencia verificada de los datos del instrumento realmente negociado, reglas fechadas del examen concreto, reproducción intradía independiente con costes y contratos, festivos y cierres excepcionales, y datos finales intactos. Las bases proxy importadas con nombres de futuros no prueban comportamiento en futuros. **No se ha obtenido una estrategia acreditada para fondeo.**

Verificación: **120 pruebas pasadas en 36 segundos**. Se comprobaron los hashes de los 90 archivos del paquete de evidencia de 967.358 bytes y se reprodujeron localmente las decisiones, con coincidencia exacta. Los cuatro archivos finales desplegados coinciden con los locales. La última modificación de la interfaz de comandos admite una o dos variantes; el evaluador utilizado en la ejecución y el final producen la misma decisión. La extracción completa encontró el límite de longitud de rutas de Windows; la verificación de todos los archivos se hizo directamente sobre el ZIP y la reproducción en una carpeta temporal corta.

La generación MGC M5 pasó de 20.263 a 27.529 intentos entre las muestras de las 06:10 y 06:23 UTC: 7.266 intentos adicionales mientras se probaba la mejora. En el lote MES anterior solo se exportaron cinco preseleccionadas de un banco de 2.661. Son cifras de actividad y selección, no pruebas de calidad futura. A las 06:28:47 UTC seguían activos el buscador, SQX y el temporizador horario de mejora. Se ha comprobado actividad continua durante esta intervención; no recuperación autónoma completa frente a cualquier caída. Una ejecución incierta bloquea nuevos experimentos hasta conciliarla.

Evidencia: [evaluación nativa](native_automatic_motor_20260906/auto_improvement_c262e95c77f6bad106bf/assessment.json), [verificación local y despliegue](native_automatic_motor_20260906/local_verification.json), [paquete completo verificado](native_automatic_motor_verified_20260906.zip), [120 pruebas](test_results_automatic_native.txt).


## Actualización 2026-09-06 08:16 UTC — bloqueo de órdenes canceladas resuelto

Se recuperó la evaluación de Strategy 1.17.118 (MNQ M5) sin repetir el cálculo nativo: variante rechazada, cero candidatas. El evaluador distingue órdenes pendientes canceladas de operaciones ejecutadas y conserva ambas como evidencia. Pasan 104 pruebas específicas. La mejora automática ya seleccionó Strategy 4.8.127 y pasó de búsqueda a recálculo nativo. [Resultado, evidencia y límites vigentes](native_m5_20260906/RESULTADO.md).

Actualización de cierre, 08:17 UTC: Strategy 4.8.127 completó búsqueda, recálculo y evaluación de dos variantes, archivo de 27 archivos y liberación del proyecto temporal. Ambas variantes fueron rechazadas; cero candidatas para fondeo. Servicio terminado correctamente y temporizador horario activo. La generación siguió avanzando durante la comprobación. El informe enlazado recoge hashes, motivos y límites.

## Actualización 2026-09-06 08:52 UTC — configuraciones activas y reanudación

Se migraron los 30 proyectos canónicos y sus 30 respaldos para desactivar objetivos porcentuales incompatibles con la receta de mejora, conservando la protección inicial. Dos exportaciones nativas posteriores al arranque confirman la configuración cargada. Se corrigió también la pausa persistida tras retirar su solicitud durante un reinicio; pasaron 17 pruebas del runner. El runner adoptó MCL M1 sin reiniciar SQX ni duplicar el trabajo, y el contador avanzó de 689 a 787 intentos en 52 segundos. Buscador, SQX, supervisor y temporizador de mejora estaban activos. [Informe y evidencia](pt_migration_20260906/RESULTADO.md).

El último ciclo completo de mejora tardó 2 minutos y 19 segundos y descartó sus dos variantes. Continúan los límites de cinco exportaciones por lote y dos variantes por comparación. Hay generación, selección y mejora nativa acotada comprobadas; todavía no hay ninguna estrategia acreditada para fondeo. Permanecen pendientes los datos del futuro real, las incompatibilidades de sesión y la validación final independiente.
