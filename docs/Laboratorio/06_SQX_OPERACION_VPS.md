> Actualización 2026-09-06 15:15 CEST: ciclo completo del motor propio de mejora ejecutado con `Strategy 1.1.27` (@EW H1): contrato, diagnóstico, dos hipótesis pre-registradas, dos variantes reales recalculadas en SQX, comparación emparejada y entrega. Ambas variantes `INCONCLUSIVE`; la variante de metadatos del Improver rechazada antes de recalcular; 164 pruebas correctas. Incidencia: desde las 12:02:26 CEST la CLI de SQX no devuelve `Records:` ni nombres de proyecto (el motor cuenta exportando; el runner de búsqueda estuvo en bucle de fallo por ello). Guía en [07_MOTOR_MEJORA_CICLO.md](07_MOTOR_MEJORA_CICLO.md); resultado en [MOTOR_MEJORA_20260906/RESULTADO.md](../../orchestration/results/codex/MOTOR_MEJORA_20260906/RESULTADO.md). Cero estrategias acreditadas para fondeo.

> Actualizacion 2026-09-06T11:47:50.850771+00:00: motor de mejora desplegado, 120 pruebas previamente pasadas y dos variantes reales EW descartadas. El ensayo E6 produjo dos candidatas que perdieron en desarrollo: ninguna exportada ni acreditada para fondeo. SQX y el runner estan activos, pero la consulta nativa de estado falla; la continuidad actual NO esta demostrada. [Resultado actual, limites y evidencia](../../orchestration/results/codex/SQX_NATIVE_IMPROVEMENT_20260905/RESULTADO_E6_20260906.md).

> Actualización 2026-09-06, 07:21 UTC: motor de mejora v2 desplegado y probado; dos variantes mejoran el histórico, pero la prueba posterior de sesión las rechaza por muestra insuficiente y un incumplimiento horario. Ninguna acreditada para fondeo. 102 pruebas de implementación y 27 archivos de esta prueba verificados; comparación reproducida. El generador seleccionó cinco MNQ M5 y arrancó MYM M5. [Resultado actual y límites](../../orchestration/results/codex/SQX_NATIVE_IMPROVEMENT_20260905/native_session_v2_20260906_16utc/RESULTADO.md). Las secciones siguientes conservan estados históricos.

# SQX en la VPS alemana: procedimiento y pruebas pendientes

Actualizado: 2026-09-05. Guía operativa en verificación; no certifica estrategias ni declara completado el replay. Reutiliza `05_STRATEGYQUANT_COMO_USARLO.md`, el diagnóstico de 2026-09-03 y los artefactos de `SQX_NATIVE_REPLAY_01`. Los resultados históricos deben conservar su fecha y alcance.

## Instalación y responsabilidades

La instalación examinada es SQX **144.2953**, en `/opt/SQX-headless`, bajo `sqx-headless.service`, en Alemania. Es un servidor dedicado Hetzner Server Auction en FSN1-DC1 con un Intel Core i7-6700: 1 socket, 4 núcleos físicos, 2 hilos por núcleo (8 CPU lógicas), aproximadamente 62 GiB de RAM, 2 SSD SATA de 250 GB y red de 1 Gbit. El PC no es servidor; Oracle queda para Hermes futuro.

## Actualización de infraestructura aportada por Emilio — 2026-09-05

El servidor operativo indicado es Hetzner **#3063412**, `88.99.210.167`, en **FSN1-DC1**: Ubuntu 24.04, Intel i7-6700, 64 GB de RAM y 212 GB RAID1. Aloja la GUI en `/opt/StrategyQuantX` (5050) y SQX headless en `/opt/SQX-headless` (5051). El acceso SSH desde este PC usa la clave designada para ese host; no guardar ni reproducir material de autenticación en esta guía. Oracle solo proporciona el túnel hacia Hetzner, nunca un shell general contra la VPS.

La consola gráfica noVNC del servidor se expone en `https://88-99-210-167.sslip.io/novnc/vnc.html?autoconnect=true&resize=scale&path=novnc/websockify`; el usuario comunicado es `emilio`. No se guarda contraseña. UFW permite 22, 80 y 443; los puertos 5050--5052 no son públicos. Cualquier acceso a SQX fuera del servidor debe conservar ese límite y no abrir puertos adicionales.

También existe el servidor Hetzner **#3059952**, `195.201.207.225`, en **FSN1-DC4**, accesible por SSH pero sin web ni servicios visibles según el informe. No es parte del runtime descrito aquí y no hay autorización para cancelarlo, borrarlo o modificarlo.

### Estado comunicado, pendiente de comprobación independiente

Emilio informa de que `ultrarentable-sqx-tunnel` y `sqx-tunnel` están activas y que ambas listas de proyectos responden mediante el túnel. Los proyectos comunicados son `FONDEO_MES_M5`, `FONDEO_MNQ_M5`, `FONDEO_MNQ_M15`, `FONDEO_MNQ_M1`, `FONDEO_MYM_M1`, `FONDEO_MYM_M5`, `FONDEO_MYM_M15`, `FONDEO_MYM_H4`, `FONDEO_MGC_M5`, `FONDEO_MCL_M1`, `FONDEO_MCL_H4`, `FONDEO_M6E_M5` y `UR_SQX_NATIVE_REPLAY_01_VPS`.

El mismo informe atribuye a los commits `69bccd628` y `e7e0218ac` una cuarentena de diez ficheros del PC (7 PowerShell y 3 doctrinas), un manifiesto SHA-256 y la preservación del histórico de `results`. Esos objetos no están presentes en este clon local al consultar exclusivamente sus metadatos; por tanto, ni el contenido de la cuarentena ni el manifiesto se han comprobado aquí.

Una respuesta de lista de proyectos por túnel solo acredita conectividad/listado en el alcance informado. No demuestra que un Retest haya terminado, que existan resultados físicos exportados, ni que alguna estrategia esté aprobada. La ficha de frontend Estrategias sigue sin declarar despliegue: el build estaba pendiente por `lucide-react` y esta actualización no lo ejecuta.

`m1-runner.service` coordina las celdas; `ultrarentable-supervisor.service` publica observaciones. Una pausa del runner no demuestra por sí sola que todos los proyectos de SQX estén parados. Antes de mantenimiento hay que consultar cada proyecto relevante por nombre y verificar persistencia de sus bancos.

En esta instalación, el puerto 5051 redirige a 5050 mediante NAT; se contrastaron respuestas equivalentes. El envoltorio HTTP `/call?cmd=...` es infraestructura local, no se debe confundir con un contrato HTTP oficial de StrategyQuant. Los comandos se envían al proceso existente; ejecutar otro `sqcli` podría crear otra instancia. La ayuda incluida en 144.2953 prevalece ante diferencias con ejemplos antiguos de la web.

## Ciclo mínimo que debe quedar probado

| Paso | Acción y comprobación exigida |
| --- | --- |
| Identificar | Registrar versión, proyecto único, CFX, archivo SQX, datos, periodo, motor, costes y sizing efectivo. Conservar hashes. |
| Preparar | Aprovechar una frontera de campaña: celda terminada, archivos guardados, estado persistido y pausa del runner observada. |
| Cargar configuración | `-project action=loadconfig name=<proyecto> file=<cfx>`; volver a listar. Históricamente creó nombres con sufijo: no asumir sustitución por el mensaje de éxito. |
| Cargar entrada | `-databank action=load project=<proyecto> name=<banco> folder=<carpeta>`; exigir una entrada real y su identidad antes de arrancar. `Loading strategies` no demuestra carga. |
| Ejecutar | Usar exclusivamente la tarea de retest contrastada con la plantilla instalada; registrar estado anterior y posterior. No repetir un arranque por un timeout de la conexión. |
| Guardar | `-databank action=save ... folder=<salida>` conserva SQX; `action=export ... file=<csv>` obtiene la tabla. Comprobar archivos, ZIP/XML, resultados y huellas. CSV de métricas no sustituye reglas ni operaciones. |
| Reanudar | Retirar solo la pausa creada por esta operación. Verificar que el runner avanza y que no queda una segunda instancia o ayudante temporal. |

Sintaxis contrastada con [gestión de proyectos](https://strategyquant.com/doc/cli-command-line/project-manage-projects/) y [gestión de bancos](https://strategyquant.com/doc/cli-command-line/databank-manage-databanks/). La secuencia específica y sus artefactos están en `orchestration/results/codex/SQX_NATIVE_REPLAY_01/vps/`.

## Memoria, CPU y recuperación

No deducir capacidad disponible para SQX del porcentaje de RAM del proceso. Java tiene un máximo configurado; RAM libre del servidor no amplía automáticamente ese límite. La documentación exige reiniciar para aplicar cambios del máximo. En esta VPS también deben caber sistema, web y API; la recomendación del proveedor para un equipo dedicado no se aplica automáticamente. [Configuración de memoria](https://strategyquant.com/doc/strategyquant/starting-sq-with-more-memory/).

El proveedor documenta que acumular estrategias en bancos puede saturar memoria, incluso al cargar la aplicación. Por eso hay que medir máximo y ocupación del heap, bancos cargados, RAM disponible, CPU y avance útil. CPU alta sin nuevas operaciones puede indicar trabajo de recuperación de memoria; aún debe diagnosticarse, no contarse como generación. No ampliar bancos ni lanzar campañas simultáneas sin medir. [Memoria y estabilidad](https://strategyquant.com/blog/efficient-memory-management-and-fixing-stability-issues-for-strategyquant-x-sqx/).

Para una salida ordenada existe `-exit`. Antes de usarla: guardar y verificar bancos, aparcar el runner, conservar configuración y conocer la política real de reinicio del servicio. Después: comprobar PID, versión, hashes, proyectos y estado del runner. Un código HTTP no basta. [Salida de CLI](https://strategyquant.com/doc/cli-command-line/exit-exit/).

## Lecciones contrastadas de esta prueba

- El runner guardó MES_H1 con 1902 archivos SQX y quedó en frontera. La pausa persistente sobrevivió al reinicio automático producido por `needrestart` durante una instalación del sistema. No hacer instalaciones que puedan reiniciar servicios sin controlar ese comportamiento.
- El import de una sola candidata dejó el banco vacío. Dos ajustes de configuración no demostraron resolverlo. El log mostró `Memory usage limit reached` con 99,308591 % y `Confirmation in progress`. Se dejó de cambiar bancos por suposición; la recuperación de memoria y el replay siguen pendientes de comprobar.
- El histórico de este caso es XAUUSD spot de Dukascopy usado como proxy bajo la etiqueta MGC. No acredita comportamiento en futuros CME MGC.
- El sizing efectivo procede de la selección de resultado Main y su configuración de retest; la plantilla de martingala desactivada no describe el riesgo ejecutado.

## Recuperación intentada el 2026-09-05

Antes de solicitar la salida se comprobó la frontera: `celda_en_curso=null`, `runner_control.pause_requested=true` y `paused_at_boundary=true`. Se conservaron `estado.json` (SHA-256 `62c260b2a3adbc109a880c8ea8ed1888cd04f32bfe00be41a624f9cfbdc8eefc`) y `manifiesto.json` (`0933ef7976af9d4594e7680b7195eff46f98aa51407bdc6732399f38ba4d4230`). La copia TAR completa de `user/projects` contiene 31.696 entradas y tiene SHA-256 `d8565155ea3770e45e03d1b2161b74fd0368c1ed753f25e63907504796047a69`; está en `/opt/SQX-headless/import/fondeo/recovery_20260905_0826Z/`.

La lista devolvió 216 nombres únicos. La comprobación por `status` no pudo acreditar su inactividad: en proyectos como `Optimizer` y `Retester`, consultar el estado disparó sincronización de bancos y devolvió errores de carga/confirmación en vez de métricas. Se canceló la pasada masiva y no se volvió a usar como prueba de ausencia de actividad.

Con esos respaldos se envió una sola vez la salida oficial al proceso existente:

```text
curl -sS --max-time 120 "http://127.0.0.1:5051/call?cmd=-exit"
request_at=2026-09-05T08:26:51Z
curl: (28) Operation timed out after 120002 milliseconds with 0 bytes received
response_at=2026-09-05T08:28:51Z
```

La respuesta está en `recovery_20260905_0826Z/exit_response.txt`, SHA-256 `63cad6c16d71acc683be2b0f2387486611f8cbf6966fcd87df4e646213f95026`. Tras otros 180 segundos de observación, systemd seguía con PID `187498`, `NRestarts=0`; a las `08:32:07Z` consumía aproximadamente 714 % de CPU y 40.130.808 KiB de RSS. `jcmd 187498 VM.flags` tampoco pudo leer el máximo de heap: la VM rechazó el mecanismo de attach. Por tanto, la recuperación, el recuento `Input=1`, el retest, la exportación y la reanudación siguen pendientes. No se envió otra variante de salida, señal o reinicio.

Después se autorizó una única terminación normal del proceso principal mediante systemd, sin `stop`, SIGKILL ni una segunda instancia. A las `08:33:17Z`, tras volver a verificar que `MainPID=187498`, se ejecutó `systemctl kill --kill-who=main --signal=SIGTERM sqx-headless.service`. `Restart=always` inició el PID `217219` a las `08:33:45Z`; la evidencia tiene SHA-256 `a88cfdceb4ea1d495afdbc71e3c7e6c505f19789c4fbf5d1c0a6a83187dee5c3`. A las `08:35:06Z` la CLI ya respondía, había un solo `sqcli` y el listener 5050 pertenecía al PID nuevo. El RSS quedó en torno a 9,7 GiB y el sistema informó 51 GiB disponibles. La pausa, `estado.json`, `manifiesto.json` y los históricos MGC M1/M5 conservaron sus hashes.

Tras la recuperación se eliminó exclusivamente el proyecto de replay vacío, se cargó de nuevo el CFX R2 con SHA-256 `3b7b83ec0678a98e9e3d7897bbcfb2ce3ad56058f5b01beed8cba086d2d92c83` y se importó una vez `Strategy 2.3.125.sqx`, SHA-256 `0c904ea6d33ebf85fe44f9c0cabc5467dedc978273146d079b1daf20253da32d`. La carga es asíncrona: la respuesta inmediata fue `Loading strategies`; después el log registró `Strategies loaded`. A las `08:36:44Z`, `-databank action=count ... name=Input` devolvió exactamente `Records: 1` (evidencia SHA-256 `937d2c4d85a7e71554393d48cf4074d05d602d255edc1881f31445f1804b96da`). En este punto la recuperación y la entrada están comprobadas; aún faltan ejecutar una sola tarea, obtener el resultado físico, exportarlo y reanudar la campaña.

## Estado comprobado más reciente: 2026-09-06 10:26 UTC

Añadido y desplegado filtro fechado de productos Topstep: @EW queda excluido antes de preparar una mejora específica para ese examen. Verificado con el archivo BASE real en la VPS; 120 pruebas locales superadas. Un símbolo permitido no acredita la identidad de sus datos ni el examen. Motor SHA-256 `59fc003b8b23dd0c246f879d5d1547d176277b193c1376556f6b3cb3994d07eb`. A las 10:26 generador, SQX y temporizador estaban activos; MES M1 alcanzó 3.129 intentos y 63 resultados preliminares en la VPS a las 10:21. Se mantienen las limitaciones CFD/futuros y cero estrategias acreditadas. [Evidencia de actualización](../../orchestration/results/codex/SQX_NATIVE_IMPROVEMENT_20260905/product_gate_20260906/deployment.json).

Observación anterior, 10:05 UTC:

Motor de mejora nativa corregido, desplegado y probado con una estrategia real EW H1. Se rechazó una falsa variante que sólo cambiaba metadatos y se recalcularon original y dos stops distintos; ambas variantes quedaron descartadas por sus resultados de desarrollo. Pasaron 114 pruebas de ejecución SQX. Búsqueda activa y encadenamiento MCL M1 → MES M1 comprobado; a las 10:01 MES tenía 1.060 intentos y cero aceptadas. La campaña continua sigue usando aproximaciones CFD, excluidas del mejorador de futuros. El experimento EW fue acotado y todavía no constituye una campaña automática de futuros. Cero estrategias acreditadas para fondeo; falta validación independiente intradía y del examen. [Resultado, límites y evidencia](../../orchestration/results/codex/SQX_NATIVE_IMPROVEMENT_20260905/RESULTADO_EW_20260906.md).

## Después del caso mínimo

SQX distingue búsqueda aleatoria, evolución genética y proyectos con tareas encadenadas. Permite utilizar resultados de una búsqueda como población de otra; cada modo tiene costes y riesgo de sobreajuste distintos. Se elegirán mediante experimentos acotados después de conseguir reproducción y evaluación trazables, sin fijar un número universal de generaciones ni filtros de rentabilidad. [Modos de construcción](https://strategyquant.com/doc/strategyquant/different-build-modes/).

El aprendizaje quedará demostrado cuando una candidata recorra carga, retest, guardado y reanudación con evidencia. Leer esta guía o acumular estrategias no cumple ese criterio.

## Corrección de salida masiva, 2026-09-05 16:58 UTC

La búsqueda se reanudó a las 15:42 UTC y avanzó entre celdas. El runner anterior guardaba bancos enteros: MGC_H1 y MNQ_H1 exportaron 20.000 SQX cada uno en la ronda 6. Esto contradice el requisito vigente: de SQX solo sale una selección pequeña, con pruebas identificadas.

Se retiraron del runner remoto los comandos de guardado y exportación masiva. Al terminar una búsqueda, registra `RETENIDA_SELECCION_NATIVA_PENDIENTE`, `probada=false` y ninguna ruta de entrega; continúa con la siguiente celda. Esto bloquea una entrega incorrecta, pero todavía no implementa la selección robusta. Los archivos históricos se conservan. El extractor local `sqx_handoff.py` es un borrador retirado que dependía de aquellos volcados; no está desplegado y su unidad queda bloqueada por una condición explícita.

El runner se reinició de forma ordenada a las 16:58:43 UTC y conservó FONDEO_MYM_H1 en curso. Solo se reinició el coordinador, no StrategyQuant. Se evitó además consultar todos los bancos históricos cuando existe una celda pendiente, para no provocar cargas masivas durante la recuperación. SHA-256 del runner corregido: `6c056fe29c6db678bbed42d04c86bd580bbcc89355bad8e486e581d6117aba2c`; copia previa: `/opt/SQX-headless/import/m1_runner_sqx.py.before-selective-output.20260905T165532Z`.

La auditoría de los CFX en disco encontró 30 proyectos canónicos, bancos Builder de 20.000 y ningún cross-check Builder activo. Existe una excepción que exige evaluación separada: MGC_H4 incluye una tarea Retest con Monte Carlo. Su configuración no demuestra que haya terminado ni que valide las demás celdas. La evidencia está en `orchestration/results/codex/SQX_RESUME_20260905/sqx_configuration_audit.json`.

La CLI oficial permite guardar estrategias concretas mediante `strategies=...`. Antes de habilitar una entrega hay que verificar esa selección en la versión instalada y asociarla a los resultados de pruebas. Un puesto alto en el ranking histórico no basta. [Guardado selectivo oficial](https://strategyquant.com/doc/cli-command-line/databank-manage-databanks/).

Activación comprobada a las 17:00:17 UTC: runner PID 242157 activo, SQX conservó PID 217219 y su inicio de las 08:33:45 UTC. A las 16:59:43 el runner confirmó avance de MYM_H1 entre dos lecturas y la adoptó sin relanzarla. El código activo compila y contiene cero llamadas de guardado o exportación de bancos. Evidencia: `orchestration/results/codex/SQX_RESUME_20260905/selective_output_activation.json`. Queda por observar la primera finalización con salida retenida; todavía no hay entrega selectiva validada.


## Estado vigente — 2026-09-06, selección y mejora nativa

La selección pendiente de la anotación anterior ya está implementada: el buscador continuo conserva como máximo cinco preseleccionadas por lote. El lote MES M5 de las 05:32 UTC exportó cinco de un banco de 2.661. No se descargan bancos completos para la mejora.

Un temporizador horario activa una mejora nativa acotada sobre una base compatible de la preselección. Conserva sus entradas, busca salidas alternativas, exporta una o dos variantes y recalcula original y variantes con contratos enteros y precisión M1. Coteja métricas y operaciones, rechaza regresiones y anomalías de ejecución/sesión, registra identidades para evitar repeticiones y conserva evidencia antes de liberar sus proyectos. Se corrigió el rechazo accidental de búsquedas que devolvían una sola variante válida. La receta comprobada cubre estructuras concretas MYM/MNQ, no todos los proyectos.

La última comparación automática de Strategy 1.18.140 (MNQ M15) terminó con variante rechazada y cero candidatas para validación. La generación avanzó 7.266 intentos durante la intervención; buscador, SQX y temporizador seguían activos a las 06:28:47 UTC. Pasan 120 pruebas específicas; los cuatro archivos desplegados coinciden con los locales y se verificaron los 90 archivos del paquete, reproduciendo la decisión localmente.

Esto acredita generación, selección pequeña y ejecución de una receta de mejora; no acredita una estrategia apta para fondeo ni recuperación universal tras caídas. La validación final exige datos del instrumento real, reglas completas fechadas, reproducción intradía independiente y datos reservados. El diagnóstico de ventanas de 1–5 días es preliminar. Las anomalías de ejecución detectadas siguen sin resolver y bloquean la promoción.

Resultados, límites y evidencia: [informe vigente del motor](../../orchestration/results/codex/SQX_NATIVE_IMPROVEMENT_20260905/RESULTADO.md).


### Actualización 2026-09-06 08:16 UTC

Resuelto el bloqueo de evaluación por una orden pendiente cancelada. La ejecución MNQ M5 se concilió sin repetir el recálculo; su variante empeora y se descarta. Se conservan 25 archivos de evidencia y se cerró el bloqueo. El servicio inició otra base y alcanzó el recálculo nativo. Pasan 104 pruebas específicas. Esto no acredita una estrategia para fondeo ni recuperación automática universal. Los proyectos de generación previamente cargados todavía pueden conservar el objetivo porcentual problemático: corregir una plantilla no migra esos proyectos. [Detalle y evidencia](../../orchestration/results/codex/SQX_NATIVE_IMPROVEMENT_20260905/native_m5_20260906/RESULTADO.md).

Actualización de cierre, 08:17 UTC: la nueva base Strategy 4.8.127 completó el ciclo automático con dos variantes rechazadas, 27 archivos archivados y bloqueo liberado. Servicio terminado correctamente; temporizador horario activo. La generación MYM M5 avanzó otros 5.854 intentos durante la intervención. No hay ninguna estrategia acreditada para fondeo.

### Actualización 2026-09-06 08:52 UTC

Resuelta la limitación de configuraciones antiguas señalada a las 08:16: se migraron los 30 proyectos canónicos y sus 30 respaldos, cambiando únicamente PTPercent a false y conservando SLPercent. Dos exportaciones nativas tras arrancar confirman el cambio cargado. Se corrigió además el estado de pausa persistido tras retirar la solicitud durante un reinicio; pasaron 17 pruebas del runner. El trabajo MCL M1 fue adoptado sin relanzarlo, SQX mantuvo su proceso y se observaron 98 intentos adicionales en 52 segundos. Los cuatro servicios consultados seguían activos. Esto demuestra esa recuperación concreta, no tolerancia universal a caídas. Las estrategias antiguas con objetivos porcentuales siguen excluidas del mejorador. [Evidencia de migración y reanudación](../../orchestration/results/codex/SQX_NATIVE_IMPROVEMENT_20260905/pt_migration_20260906/RESULTADO.md).
