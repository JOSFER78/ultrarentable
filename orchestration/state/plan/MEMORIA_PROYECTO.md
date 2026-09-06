# Memoria operativa del proyecto

## Lectura vigente posterior — 2026-09-05

El objetivo autorizado es completar la página Estrategias en la única VPS `88.99.210.167`. Web/API ya están desplegadas; consultar el recibo `orchestration/results/codex/GERMANY_RUNTIME_01/release-prep/ACTIVATION_VERIFIED_20260905.md` y sus límites antes de utilizar los inventarios históricos inferiores. Basic Auth usa `emilio`, en minúsculas; la credencial DPAPI quedó corregida y HTTPS de Estrategias, noVNC y overview respondió 200. Esto no acredita por sí solo la interacción completa de la UI ni una estrategia aprobada para fondeo.

Astra orquesta y revisa con un máximo de dos subagentes ligeros, sin delegación anidada; Emilio permite que el principal resuelva cambios pequeños. AGY/Orca y sus monitores históricos siguen aparcados. Las reglas antiguas de 3–10 agentes y preparación previa no sustituyen este objetivo posterior.

Identidad confirmada por Emilio: aquí sólo existe el usuario superadmin `josferestudio@gmail.com`. Pepe y Ana corresponden a otro proyecto y no son cuentas ni escenarios de aceptación de éste. La identidad de la aplicación es distinta del usuario Basic Auth `emilio`.

Verificación posterior: flujo HTTPS completo persistido con seis variantes y un HOLDOUT real, sin aprobación en el modelo. Firebase recompilado con siete valores públicos válidos; navegador muestra la página pública de acceso. Falta verificar el panel con identidad Firebase autorizada. Corregido el dominio autorizado de Google: añadido únicamente `88-99-210-167.sslip.io`, con GET oficial antes/después y conservación de los ocho dominios previos. La decisión histórica `selection` se conserva anterior al HOLDOUT; el recibo y estado del candidato describen la ejecución posterior.

## Prioridad arquitectónica posterior — runtime solo en Alemania

Emilio aclara: «este pc no pinta nada de nada de nada en el proyecto, solo la vps
de alemania y la vps oracle para uso de hermes en el futuro». Se cancela la petición
de ejecutar `scripts/local/start_api.ps1`: no volver a pedir arranques locales ni
tratar el PC como servidor del producto. El objetivo operativo es web/API/datos y
trabajos en Alemania; Oracle queda para Hermes futuro, sin cambios allí ahora.

Inventario alemán contrastado: SQX y servicios de campaña existen; web/API todavía
no estaban instaladas. Se prepara una release aislada en /opt/ultrarentable/releases
y estado persistente en /var/lib/ultrarentable, preservando el supervisor existente.
No trasladar la SQLite local como si fuera automáticamente canónica.
Los cambios de código y artefactos conservados siguen siendo material revisable,
no despliegue remoto probado. Los intentos locales rechazados quedan como historia.
Se observó después un listener8100 PID1424 con cmdline no accesible; no se le
atribuye un arranque de Codex ni se detiene sin identificarlo.

El trabajo SQX transcurre en Alemania. La celda MES_H1 terminó y guardó 1902
estrategias antes de aparcar el runner en frontera. A las 08:12:45 UTC, needrestart
reinició automáticamente runner y supervisor durante la instalación de python3.12-venv;
SQX no se reinició. Se comprobó después PID207291, celda=null y pausa persistente
activa: sin pérdida observada ni retest concurrente. Se suspendieron instalaciones
de sistema adicionales. El primer proyecto Retest seguía vacío y no ejecutado;
se corrige únicamente su configuración de bancos contra el Retester remoto 144.2953.
Aún deben verificarse resultado y reanudación. La ficha genérica no está desplegada
y no declara rendimiento ni certificación.

## Vigente: autonomía delegada y siguiente prueba de Estrategias

Emilio respondió a las autorizaciones pendientes: «debes decidir tu que es lo mejor para conseguir el objetivo». Codex elige recuperar API sin workers, desplegar las correcciones y ejecutar la fase00 concreta de una candidata SQX trazable. Esta respuesta sustituye la espera de aprobación anterior; no volver a pedirla. /plan revisión16 está confirmado, conserva preparación abierta y ninguna fase cerrada sin pruebas.

El nuevo intento de Start-Process para API8100 fue rechazado otra vez por la revisión automática (`blocked by policy`) antes de ejecutar Python. No se conocen más motivos. No eludir el rechazo ni reiniciar por otro mecanismo. Script manual preparado y sintaxis comprobada: `scripts/local/start_api.ps1`; se pidió al usuario ejecutarlo en su consola. La copia coherente previa en `ESTRATEGIAS_RUNTIME_01/api-recovery-authorized` mantiene735candidatas,7686estrategias,40perfiles,0sesiones y1689eventos.

Mientras tanto continúa el caso SQX autorizado. Agente align_gate_consumers tiene la instalación del control mínimo de pausa al terminar celda y el único retest; transición sujeta a PID/StartTime/ronda/celda/log reciente y copia de seguridad. No basta un parche en disco para actualizar el proceso vivo. Root autorizó la secuencia tras revisar código y8pruebas de control; todavía debe comprobarse el resultado remoto. review_sqx_evidence prepara ficha lectora genérica y root registra su router en main.py. Hay0coincidencias de catálogo por SHA: no enlazar M15/H4 por nombre parecido.


## Actualización — preparación API/frontend cerrada en código, despliegue pendiente

`docs/PLAN_ACTUAL.json` revisión15 conserva PREPARACION, ninguna fase activa y
`plan_confirmado=false`. La fase00 y el arranque de API8100 rechazado por revisión
automática siguen pendientes de autorización; no reiniciar por otra vía ni dar
por aprobada una fase por una continuación automática.

Se corrigió otro consumidor legado en `certified_summary_router.py`: contrato
compartido de diez IDs exactos, payload por ID y sin campo `gates_verified_11`.
Su tabla frontend usa el nuevo contrato. Suite aislada7 + regresiones anteriores3
aprobadas; Codex comprobó6 casos Python→TypeScript sin DB ni servidor. Build final
aislado aprobado y211 archivos contrastados con originales/copia, sin diferencias.
Evidencia: `orchestration/results/codex/ESTRATEGIAS_RUNTIME_01/VERIFICACION.md` y
`frontend-build/independent-verification.json`. Esto no acredita estrategias ni
aptitud para exámenes. El README de Estrategias está alineado con el objetivo actual.

No desplegado: web3100 PID26464 aún sirve build `d6CcO7oFiYxqxUvW8p_Sm`; el nuevo
build aislado es `-SW915cQ7BwpZ6AP2PfRv`. API8100 sin listener al cierre. No se
tocó SQX, su runner, el túnel necesario ni las bases operativas. AGY sigue aparcado.

## Objetivo vigente: Estrategias y exámenes de una semana

Leer `docs/OBJETIVO_ESTRATEGIAS_20260905.md`, copia íntegra del objetivo actualizado por Emilio. Reemplaza el mínimo mensual: el20% sobre saldo nominal es orientativo. Alcance: solo Estrategias y sus procesos, sin operación de cuentas ni otras páginas. `PROYECTO.md` y `/plan` revisión14 reflejan cuatro fases propuestas; la fase00 se ha sometido a aprobación y todavía no hay respuesta. No asumir aprobación.

Comprobación actual del panel: API8100 ausente y proxies502. Código de arranque corregido para no sembrar, sobrescribir catálogo ni purgar registros;3pruebas temporales pasan. Frontend exige10IDs explícitos y rechaza11históricos/contradicciones;6pruebas pasan. Sigue pendiente build/despliegue. Evidencia, hashes y copiaSQLite coherente en `orchestration/results/codex/ESTRATEGIAS_RUNTIME_01/VERIFICACION.md`.

La revisión automática RECHAZÓ iniciar API8100 con workers desactivados (`blocked by policy`, sin más detalle). No hay procesoAPI iniciado. Se pidió autorización explícita junto con aprobar fase00; no repetir por otra vía mientras no cambie la autorización o exista una alternativa realmente más segura. Web3100 sigue sirviendo el build anterior. El rechazo ya se explicó al usuario.

Túnel SSH necesario para SQX Alemania restaurado, PID23932, inicio09:24:56Madrid;5050y5052 responden200. Conservarlo mientras sea la dependencia del panel; no duplicarlo. No es cron ni puenteAGY. La campañaVPS no fue pausada ni modificada.

Evaluación de examen existente: filtro20% y default8d siguen pendientes de alinear en fase01; minTradingDays/noticias no llegan al evaluador.15pruebas pasan y3reales fallan por datasetLinux ausente. CFXVPS84871b0f...e2970 revisado con recursos fuente; falta ventana segura del runner y retest. No sustituir trayectoria real por PnL agregado para afirmar aptitud.

## Actualización posterior — SQX_SOURCE_RUNTIME_01

Comprobación posterior VPS Alemania: SQX144.2953, PID187498 en5050,8cores y~64GiBRAM; campaña FONDEO_MES_H1 consumía~720%CPU. Los hashes MGC_M1/M5 remotos siguen coincidiendo con dataset/manifest.json. Usar histórico existente en lectura, sin alias ni nueva importación. PaqueteVPS en preparación con Resources/ATMs originales y chartMGC; revisión completa pendiente. No iniciar segunda instancia SQX ni duplicar carga; siguiente paso identificar pausa/reanudación o ventana del supervisor actual para UN retest conservando la campaña. Ese control aún no se ha modificado. Las horas de top no se presumen UTC.

Emilio confirma SQX operativo en la VPS alemana `sqx-hetzner:/opt/SQX-headless`; usar esa instalación para el retest, no la local. Codex cerró su preflight local PID9772 con cero procesos SQX restantes, sin importar ni ejecutar. Preparación de retest único en `orchestration/results/codex/SQX_NATIVE_REPLAY_01/vps` en curso; no iniciar campañas históricas. Revisar recursos completos del CFX, no solo las seis secciones copiadas.

Importación corregida: sizing efectivo vs plantilla, Main vs CrossCheck, árboles stop y clasificación común sin defaults/redondeos ni heurísticas de riesgo. 34 pruebas independientes pasan; 3 pilotos fuera de alcance excluidos. Archivo de evidencia `orchestration/results/codex/SQX_SOURCE_RUNTIME_01/VERIFICACION.md` y hashes finales. Histórico físico exacto copiado y trazado: XAUUSD spot proxy, NO futuros MGC, 1.295.202 barras M1; manifiesto en dataset/. Los dos SQX reales usan RiskFixedBalancePct0.5% sobre50.000. El método sigue no ejecutable en adaptador universal hasta reproducción fiel. /plan rev13 EN_CURSO, sin fases iniciadas. API no reiniciada. Objetivo20% no demostrado; pregunta de firma/cuenta/denominador sigue pendiente. No repetir inventarios o pruebas sin cambio/fallo nuevo; continuar con el retest nativo alemán aislado.

## Actualización posterior — GATES_BASELINE_01

Emilio aclara: los controles actuales son diez, pero nada del sistema es inamovible ni se presume comprobado; se cambia, quita o incorpora con el único propósito del objetivo de estrategias de examen >=20% mensual. Objetivo no alcanzado. Codex utilizó tres agentes Sol en ámbitos separados y revisó/integró el resultado; AGY sigue aparcado.

Selector corregido: pasa baseline real a ejecutar_loop y conserva métricas del ganador. Contrato compartido de diez resultados explícitos en contracts/gate_policy.py; consumidores actualizados. Hallazgo real: dos rutas del control 10 aprobaban 536 PnL SQX sin ejecutar Nautilus. Retirado ese aprobado; ahora NO_EVIDENCE/NOT_EXECUTED. Esto deja pendiente implementar el replay, no prueba su funcionamiento. 22 pruebas de contratos/evidencia y regresión independiente del selector aprobadas. Evidencia: orchestration/results/codex/GATES_BASELINE_01/VERIFICACION.md. API no reiniciada: no atribuirle aún el código nuevo. /plan rev11 distingue código verificado de despliegue pendiente.

Próximo paso sin repetir auditorías: candidata física fondeo_fuentes_20260905/MGC_M5_r5_Strategy_2.3.125.sqx (hash 0c904ea6d33ebf85fe44f9c0cabc5467dedc978273146d079b1daf20253da32d). Resolver sizing efectivo de settings/lastSettings, órdenes stop, unidades y dataset exacto; después replay independiente. Corpus y 536 cierres reales ya conservados. Pendientes además hash de velas en resumen M2, objetivo2% heredado y definición empresa/cuenta/denominador20%; pregunta al usuario enviada, seguir trabajo técnico independiente.

Las fotografías y reglas antiguas que siguen debajo no revocan estas aclaraciones ni autorizan reanudar AGY.

## Vigente desde el 5 de septiembre de 2026, 08:10 — Codex directo

Actualización posterior: CENSO_CONEXION_01 comprobado. Resumen y M2 usan lib/censo.ts y la misma población; cabeceras sin mediciones estáticas; actualización/error/recuperación verificados en navegador, 7 pruebas y build correcto. Servidor actual PID26464, inicio08:29:02, puerto3100. Evidencia en orchestration/results/codex/CENSO_CONEXION_01/VERIFICACION.md. No se han usado agentes; el usuario ha preguntado qué conviene y se ha recomendado repartir únicamente tareas independientes, manteniendo revisión e integración de Codex.

Regla posterior de Emilio: antes de utilizar SQX, Nautilus o cualquier otra herramienta, aprender su uso adecuado a partir del corpus existente y documentación oficial, y demostrar un recorrido mínimo real antes de escalar. Registrar procedimiento, configuración, evidencia, errores y límites. Guía vigente: docs/APRENDIZAJE_HERRAMIENTAS.md. No confundir horas de actividad con funcionamiento correcto.

Emilio aparca la orquestación Astra–AGY y encarga a Codex analizar, programar y comprobar directamente. No reactivar AGY, crons ni encargos antiguos. El contenido posterior a esta actualización conserva historia y no autoriza reanudar ese sistema.

Seguimiento actual: docs/PLAN_ACTUAL.json, servido en /api/plan-actual y visible en /plan. Preparación antes de 00; seis fases de producto propuestas y ninguna iniciada. La interfaz ya separa nueve secciones y el historial /plan/historial. Compilación y 21 pruebas aprobadas, navegación comprobada; evidencia en orchestration/results/codex/PLAN_ACTUAL_01/VERIFICACION.md. No equivale a preparación completa ni a motores funcionales.

Archivo externo: C:\Users\yo\Pictures\Descargaspc\pro\ASTRA&AGY\archivo-20260905-080057. Copia comprobada de 4.426 archivos y anexo de adaptadores, con manifiestos SHA256. PARADA_VERIFICADA.json contiene cancelación nativa del cron y cero subagentes. Los originales se conservan por dependencias de la web. Servidor 3100 ahora iniciado por Codex, PID2980, registro server.log.

Primera corrección de Estrategias ya comprobada: retiradas cifras/éxitos fijos del resumen y navegación; distingue consulta fallida de registro vacío. Ver ESTRATEGIAS_DATOS_01.md junto a la verificación del plan. Servidor actual PID4200, 08:14:11, puerto3100. Queda preparar mapa y contratos de fuentes/módulos; comprobar herramientas antes de usarlas. No afirmar cierre global ni activar campañas/trading.

---

Actualizada por Codex: 2026-09-05, 01:13 Europe/Madrid. Es una fotografía de continuidad, no una autorización ni una aceptación. Antes de actuar releer control.json, A60 y sus contratos; prevalecen los hechos posteriores y las instrucciones de Emilio.

## Acuerdo vigente

- Primero preparación fuera de las fases: analizar, sanear inconsistencias demostradas, organizar código y front. Después plan ordenado 00..X. No comenzar módulos de producto ahora.
- Sistema de plan, web y orquestación universal y extraíble: packages/project-plan, configuración y adaptadores del anfitrión fuera del núcleo. Jarvis solo referencia; Orca excluido.
- Codex analiza, encarga, verifica y devuelve. AGY implementa e integra. Emilio observa /plan y comunica cambios; autonomía dentro del alcance aprobado, sin pedir aprobaciones rutinarias.
- Cada encargo/corrección exige 3–10 especialistas AGY realmente concurrentes, principal excluido, con operaciones originales e intervalos acreditados. Recuperar concurrencia después de reinicios; una lista de agentes idle no vale. No añadir agentes Codex para repetir análisis.
- Cuatro ceros: invención, mocks de aceptación, cambios fuera de alcance y autoaceptación. Más agentes no garantiza aceleración lineal.
- Aislamiento, un escritor por archivo y entrega congelada. Cerrar solo recursos temporales propios con identidad/propiedad probadas y evidencia preservada; mantener principal, cron y servicios persistentes autorizados.
- Coste y tiempo: revisar la entrega concreta, no repetir investigaciones ni pruebas sin cambios o fallos nuevos. Mientras no hay cambio accionable, evitar sondeos costosos.

## Estado comprobado en esta actualización

- control.json: revisión 9, etapa PREPARACION, solo A60 autorizada, recibo_cierre null. F11 es vínculo técnico heredado; no es la fase oficial activa del futuro plan.
- A60: EN_CURSO. Contrato PREP-BASE-01 + adenda PORTABLE-01, mismo intento y receptor aac7108e-cb7a-42d6-a082-b02571ba293c.
- Copia editable: ../.agy-work/PREP-BASE-01/work/. Paquete previsto: ../.agy-work/PREP-BASE-01/delivery/, vacío al comprobarlo a01:12. Evidencia AGY en orchestration/results/agy/A60/PREP_BASE_01/ solo contenía agentes.md, cron_ticks.log y recepcion.json.
- Hay implementación parcial en packages/project-plan de la copia. composition.ts modificado a01:10:12; contratos y tipos también recientes. No es entrega congelada, aceptada ni integrada.
- Heartbeat Codex supervisar-sistema-de-plan: configuración local ACTIVE, cada 3 minutos, tarea 01a06ded-a5d0-7150-bf48-c00128188510. Configuración no prueba ejecución de cada tick.
- cron_ticks.log de AGY declara sustitución de task-884 por task-1266 a01:07:54, cada 3 minutos por petición del usuario, y ticks a01:09/01:12. Es declaración del trabajador; identidad/cadencia actuales no contrastadas aquí con retorno nativo. No recrear cron ni revertir esa declaración por referencias antiguas a task-499/1 minuto; comprobar la instrucción posterior antes de cambiar configuración.
- Recuperación de concurrencia MULTI-REC-01 y limpieza PROC-01 exigidas; cumplimiento final pendiente. Antes del reinicio hubo cuatro especialistas trabajando; últimas observaciones previas al aviso mostraron todos idle. No extrapolar actividad actual.
- Estado global: sistema todavía NO aceptado como funcional. Web servida, integración y circuito completo no verificados en esta actualización. A61–A63 no autorizadas.

## Evidencia y riesgos pendientes

- Base seleccionada de 276 archivos: C:/Users/yo/.codex/visualizations/2026/09/04/01a06ded-a5d0-7150-bf48-c00128188510/plan-f11/preparacion-base-01/manifest.json; SHA256 0BA62BE873F027F6D4E25089A8ADC24B31B79247E627B0449AE1A34547DF2D1A. No es copia ni certificación completa del proyecto.
- Prueba preliminar de Codex conservada en orchestration/results/codex/A60/PREP_BASE_01/preliminary.cjs y preliminary.result.json: sobre fuente de00:45 detectó cierre histórico sin recibo y ENTREGADO representado como en marcha. Fuente cambió después; correcciones aún no comprobadas. No sobrescribir esa evidencia ni atribuir esos fallos al código final sin repetir sobre su entrega.
- Baseline R3 anterior: 34/34 tests y typecheck correctos; no cubrían todos los defectos y no certifican PREP actual.
- Revisar en entrega: parsers únicos/estrictos, snapshot coherente, cierre con recibo, estados de entrega/revisión separados, contención realpath, eliminación de customRepoRoot público y telemetría inventada, preparación fuera de fases, portabilidad con dos proyectos y consumidor aislado, empaquetado e imports/dependencias de UI.
- Git principal contiene trabajo previo ajeno: solo lectura. No reset/clean/commit/push. No .env, credenciales, datos operacionales ni servicios de trading. No pytest global: conftest puede leer BD operacional.

## Próximo paso exacto

1. Esperar ENTREGADO con paquete congelado; no revisar aceptación contra fuentes activamente editadas ni reiniciar el encargo.
2. Preservar paquete y comprobar manifiesto, hashes, alcance, resultados, concurrencia real y cierre de recursos propios. Separar afirmaciones AGY de prueba independiente.
3. Ejecutar una aceptación independiente pertinente sobre esa versión. Devolver defectos precisos si falla; si pasa, encargar a AGY integración de hashes exactos con base principal intacta.
4. Comprobar lo integrado y el circuito real de /plan sin arrancar trading. Continuar saneamiento acotado antes de declarar cerrada preparación; después plan00..X y elección del módulo por Emilio.

## Pendiente de producto, para después

OBS-M2-DATOS-FIJOS-20260905 en orchestration/tablero/COMENTARIOS_EMILIO.md. Emilio informa datos de M2 fijos durante días. Captura conservada en orchestration/results/codex/observaciones/2026-09-05-m2-datos-fijos.png: discrepancias 157/160 promesa y 6748/6753. No prueba que toda la tabla sea hardcoded. Trazar constantes/API/cache/BD después; no autoriza tocar M2 ahora.

Idea de producto declarada: búsqueda y mejora autónoma continua de estrategias; separar evaluación de fondeo y conservación de cuentas financiadas. Objetivos de rendimiento del usuario son requisitos a estudiar, no resultados ni rentabilidad verificada. No empezar ese desarrollo durante la preparación.

## Fuentes de continuidad

SISTEMA_PLAN.md, ARQUITECTURA_Y_ORDEN.md, PROYECTO.md, SEGUIMIENTO_CODEX.md, control.json, ../../tablero/A60.md, ENCARGO_PREPARACION_BASE_01.md y ADENDA_PREPARACION_PORTABLE_01.md. Protocolo compartido ../../tablero/PROMPT_SEGUIMIENTO_AGY.md y avisos ../../tablero/BUZON.md. Historia preservada en historial/2026-09-05-antes-preparacion/. El canal operativo es la carpeta compartida; CLI agentapi sin entorno ANTIGRAVITY_LS_ADDRESS no funcionó, no hay puente CLI nuevo.

## Última actualización comprobada — 2026-09-05 01:14 Europe/Madrid

Esta observación sustituye el estado EN_CURSO descrito en la fotografía de01:12: A60 acaba de pasar a ENTREGADO. Aparecieron procesos.json (01:13:23) y limpieza.md (01:13:27) en results/agy/A60/PREP_BASE_01. La carpeta delivery seguía sin entradas en la comprobación de01:14. ENTREGADO es declaración AGY, no aceptación ni prueba de paquete completo. Próximo paso: localizar/preservar artefactos de entrega, comprobar integridad/completitud y ejecutar revisión independiente; si faltan piezas, devolver faltantes concretos por el canal compartido. No integrar ni avanzar de fase por el cambio de etiqueta. No se han ejecutado pruebas de aceptación nuevas en esta actualización de memoria.

## Revisión posterior de la entrega — PREP-COR-01
A60 DEVUELTO tras revisión independiente: 23/23 hashes, 48/48 tests y typecheck correctos, pero sonda real API reproduce parser divergente, dependencia omitida y conteo ficticio de una tarea. Vista universal aún sin consumidor real; portabilidad externa y recuperación concurrente no acreditadas. Ver results/codex/A60/PREP_BASE_01/REVISION_01/veredicto.md y nueva devolución PREP-COR-01 en A60. Próximo paso: AGY corrige dentro del ámbito autorizado, 3–10 especialistas concurrentes, entrega nueva en results/agy/A60/PREP_COR_01. No integrar ni avanzar de fase. Esto sustituye el estado ENTREGADO pendiente descrito arriba.

## Continuidad posterior
A60/PREP-COR-01 observada EN_CURSO. Durante su ejecución se contrastó código actual de comentarios y se amplió borrador A61 con identidad/contexto, preservación y concurrencia de escrituras, consumidor y pruebas. A61 sigue BORRADOR, dependiente de aceptación A60; no hay ampliación del encargo activo. Revisar nueva entrega A60 y activar siguiente contrato con base exacta cuando corresponda.

Captura de Emilio01:24 confirma web aún con F11 activa y cierres históricos. Preservada en results/codex/observaciones/2026-09-05-plan-f11-visible.png y vinculada a A60/PREP-COR-01 EN_CURSO. No estaba resuelto en web: priorizar consumidor, revisión, integración y comprobación servida antes de A61. Preparación fuera de fases; historia sin recibo no es cierre aceptado.

## Estrategias VPS — activación y estabilidad verificadas (2026-09-05)

El candidato `/opt/ultrarentable/releases/estrategias-prep-20260905` quedó activado en el único VPS autorizado `88.99.210.167`; `current` apunta a esa release y existe backup recuperable `/var/lib/ultrarentable/deploy-backups/20260905T130411Z`. La evidencia remota es `/opt/ultrarentable/evidence/estrategias-activation-20260905T153000Z/`.

API y web quedaron `enabled` y `active` bajo `ultrarentable`; overview interno, `/estrategias` y proxy API respondieron 200 en tres muestras sin cambios de PID ni reinicios (`NRestarts=0`). HTTPS sin credenciales conserva 401 en `/estrategias`, `/m1/` y `/novnc/`. El estado persistente workbench pertenece a `ultrarentable`, modo 750.

SQX se comprobó sólo en lectura. La forma válida es `GET /call?cmd=-project%20action=list`; la variante `--data-urlencode` usada inicialmente era rechazada por SQX. Los puertos 5050 y 5051 respondieron la misma lista real (3815 bytes, hash `7344c5f9…a1aa5ad6`). Esto acredita que ambos puertos responden al mismo resultado, no dos instancias SQX independientes.

Límites vigentes: XAU/MGC continúa proxy experimental no soportado como resultado MGC/firma válido; no hay estrategia aprobada. El flujo real verificado usa BTC y HOLDOUT técnico/idempotente, sin certificación de rentabilidad ni fondeo. Queda pendiente la verificación visual de navegador; este hecho no cierra ningún goal ni fase ajena.

## Motor propio de mejora — primera entrega comprobada (2026-09-06 15:30 CEST)

Ciclo completo ejecutado en la VPS con `Strategy 1.1.27` (@EW H1, datos de futuros continuos de SQX): contrato de entrada, diagnóstico determinista de las órdenes, hipótesis pre-registradas con criterios por destino (Fondeo con escenarios provisionales de examen; Ultra exploratorio), dos variantes reales (objetivo × 0,6; trailing × 0,5) recalculadas en SQX en 66 s, comparación emparejada por día y entrega `entrega_ciclo_01.json`. Ambas `INCONCLUSIVE` (peor en construcción, mejor en desarrollo, intervalo que incluye el cero); la variante de metadatos del Improver se rechazó antes de recalcular; el experimento previo de stops ±10 % quedó `HISTORICAL_FIT_ONLY` / `INCONCLUSIVE`; el control se reprodujo exactamente. Revisión adversarial con doce hallazgos corregidos antes de cerrar (marcas de tiempo de bolsa, riesgo del control en múltiplos R, devolución sobre ganadoras, evidencia OOS obligatoria). 164 pruebas correctas. Incidencia: la CLI de SQX no devuelve `Records:` ni nombres de proyecto desde las 12:02 CEST; el motor cuenta exportando; el runner de búsqueda estuvo en bucle de fallo por ello y se recuperó solo a las 14:48. Cero estrategias acreditadas; sin muestra final reservada (@EW termina el 2025-12-31). Resultado: `orchestration/results/codex/MOTOR_MEJORA_20260906/RESULTADO.md`; guía: `docs/Laboratorio/07_MOTOR_MEJORA_CICLO.md`; Ultra: `ULTRA_REQUISITOS_20260906.md` (Ultra figura aparcado desde el 2026-09-01). Siguiente paso propuesto: ciclo 02 con hipótesis de frecuencia del lado de entrada y exposición medida conjuntamente; pregunta a Emilio sobre datos 2026 de @EW para reservar prueba final.
