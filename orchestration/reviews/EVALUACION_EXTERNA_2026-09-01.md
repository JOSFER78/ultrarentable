# EVALUACIÓN INDEPENDIENTE DEL PROYECTO ULTRARENTABLE

Fecha: 2026-09-01 · Analizada la copia local del repo (`ultrarentable/`, HEAD `7b7e7311e`).
Todo lo afirmado aquí está verificado contra código, informes y telemetría del propio repo.

---

## 1. Resumen ejecutivo

El proyecto **no está fallando por falta de máquina de búsqueda**: tiene un motor de backtest honesto (5.17.0), un pipeline de 11 gates, cola de minería gobernada y SQX headless. Está fallando por la combinación de cuatro cosas:

1. **Durante meses buscó sobre un motor deshonesto** que regalaba resultados (sin spread real, comisión forex de 11.692 $ por lado, sin point_value, sin latencia). Las 728 "certificadas" eran ilusión; al sincerar el motor, el censo honesto dio **0 de 728**. No se perdió nada real: nunca existió.
2. **Las familias de señales buscadas no tienen edge.** Con datos de sobra, 341–348 de 348 configuraciones mueren en su propia muestra de entrenamiento con un filtro trivial (PF ≥ 1,05). La última telemetría (ES 4h, 2026-09-01): 20/20 mueren por "sin_ventaja", 0 por falta de operaciones. **Más datos no arreglan esto; hacen falta reglas nuevas.**
3. **En futuros sí hay además un bloqueo de datos**: Yahoo 1h da 13.701 barras y el criterio 1.1 exige ≥200 operaciones OOS (necesitaría ~61.000–101.000 barras). La solución (proxies Dukascopy 5m) ya está validada (correlación 0,9747 con ES real) pero el backfill solo ha completado ES y ~47 % de NQ; YM, GC, SI, CL y forex están a cero.
4. **El VPS está saturado** y es el único eslabón roto que no depende de código: swap 100 %, carga 10–15 sobre 4 núcleos (con 4–9 % robado por el hipervisor), 713.626 frenazos de memoria por un límite de cgroup mal puesto, servicios que resucitan solos y mineros huérfanos. La campaña que respondería a todo lo demás **no se ha podido lanzar**.

A eso se suma un coste enorme de fricción de proceso: el ejecutor Antigravity incumplió el protocolo 5 de 5 veces, hubo sesiones de agentes compitiendo por la CPU, el push a GitHub lleva días atascado (HTTP 408 con packs de ~260 MB desde una máquina colapsada) y el login de la web está roto por claves Firebase de dos proyectos mezclados.

**Veredicto en una frase:** el proyecto ha pasado de "fábrica de ilusiones rápida" a "laboratorio honesto parado por hardware y por un espacio de búsqueda agotado". La honestidad se logró; ahora falta darle máquina y darle ideas nuevas que evaluar.

---

## 2. Estado objetivo hoy

| Métrica | Valor real |
| :--- | :--- |
| Estrategias FONDEO certificadas | **0** |
| Estrategias ULTRA certificadas vigentes | **0** (5 `APPROVED_CURRENT_ENGINE` con 25–68 trades OOS; el criterio pide 200) |
| Meta-estrategias | 0 (necesitan ≥2 certificadas) |
| Motor | 5.17.0, honesto, identidad verificada release a release (15/15) |
| Mandato activo | 100 % FONDEO; ULTRA aparcado con punto de guardado íntegro |
| Backtests recientes | ~14.352 configs (24 celdas, 1h) + campañas 4h/15m → 0 certificadas |
| Materia prima SQX | 2.035 estrategias .sqx materializadas + CSV de métricas, **sin explotar** |
| Bloqueo físico | VPS saturado; comandos sudo pendientes (`orchestration/OPERACION_VPS.md`) |

---

## 3. Por qué no consigue estrategias

### 3.1 La purga de la ilusión (lo que parecía funcionar no existía)

Entre 5.7.0 y 5.17.0 se corrigieron, con verificación ledger a ledger: fricción incoherente, contratos CME fraccionarios, ausencia de latencia (entrada en la misma barra), riesgo mal dimensionado, point_value ignorado en sizing, spread y funding reales de BingX, y el bug que clasificaba forex como futuro CME (un EURUSD con +32 $ brutos pagaba 11.692 $ de comisión **por lado**). Cada corrección mató una capa de falsas ganadoras. El censo F01 con criterio sellado dio **0 supervivientes de 728**. Esto no es un fallo del proyecto: es el proyecto funcionando por primera vez.

### 3.2 Las dos causas medidas del 0 actual (no son la misma)

- **Futuros = techo de datos.** Mejor caso observado en 1h: RTY 45 ops OOS, ES 27, NQ 1 (PF 99 con 1 operación — el espejismo clásico). Con 13.701 barras de Yahoo es aritméticamente imposible llegar a 200 ops OOS. Se desbloquea con Dukascopy 5m (ES ya tiene 250.009 barras consolidadas ≈ 495 ops OOS posibles).
- **Forex/cripto (y ES con datos ya profundos) = falta de señal.** Con 121–447 operaciones en IS, los embudos son `{'IS': 848}`: mueren contra PF ≥ 1,05 en su propio entrenamiento. Ampliar de 348 a 848 configs con 7 familias apenas movió nada. La familia EMA/RSI/Donchian/ATR está **agotada**; los 6 arquetipos nuevos (ORB, VWAP_REVERSION, etc.) tampoco han pasado aún.

La pregunta "¿es dato o es edge?" estuvo meses sin poder responderse porque **la telemetría del embudo se calculaba y se tiraba** (la cola solo guardaba 3 líneas de stdout: de 14.352 configs sobrevivían 20 puntos de datos). Eso se corrigió en el último commit (`7b7e7311e`): ahora cada job escribe su embudo completo a `orchestration/results/telemetria/`. La primera muestra ya dice "sin_ventaja: 20/20".

### 3.3 Por qué "le cuesta tanto" buscar

- El coste por certificada es enorme porque el barrido es **fuerza bruta sobre plantillas paramétricas** pobres, ejecutado en 4 núcleos compartidos con la API, la web, SQX (8 GB de Java) y sesiones de agentes corriendo pytest.
- El criterio 1.1 está sellado (bien) y exige 200 ops OOS: eso obliga a celdas intradía finas (5m/15m) con años de historia, justo los datos que faltaban.
- Cada campaña fallida no enseñaba nada (telemetría perdida), así que las iteraciones no acumulaban aprendizaje. Corregido ahora.

### 3.4 Por qué no las mejora

- **F04 (mejora inteligente) nunca ha arrancado**: depende de que F03 produzca supervivientes, y F03 lleva dando 0.
- **El lazo de mejora de SQX lleva meses roto** por una cadena documentada en `estrategias_um/docs/ESTADO.md`: el fusible Monte Carlo mataba al 100 % de candidatas (`MinTradesInRun>20` × `MaxTradesPerDay=1` → cualquier randomización deja el backtest sin trades); el gatillo `improve_cycle.sh` contaba el databank `LastGeneration` (siempre 0) mientras las estrategias reales caían en `Last generation` (con espacio, no direccionable por API); todo vivía solo en RAM del motor; y el ciclo nunca devolvía los resultados mejorados a la población inicial (lazo abierto). SQX generaba >100.000 estrategias/hora con **0 % de aceptación**: la mitad de la máquina consumida en producir nada.
- **El pipeline de meta-estrategias está muerto de fábrica**: filtra por `engine_version == '5.4.0'` escrito a mano (el motor va por 5.17.0) y el endpoint lo envuelve en un `except Exception: pass` mudo. Descartaría cualquier candidata nueva sin decir nada. Sigue pendiente (hay referencias en `fast_engine_adapter.py`, `funding_research_loop.py`, `strategy_research_loop.py`, `excel_master_catalog.py`).
- **Hay DOS pipelines de validación** con umbrales distintos (`services/api/app/validation/gates/` — el que certifica — y `services/validation/engines/` — el que ve la web). Unificarlos está en F00 y es previo a fiarse de lo que muestre la web.

---

## 4. La saturación del VPS: causas medidas y remedio

Diagnóstico del propio proyecto (2026-09-01), verificado y bien hecho:

1. **Thrashing de cgroup**: `ultrarentable-discovery.service` con `MemoryHigh=1.5G` y working set de 1,6 GB → 713.626 frenazos, proceso en estado D, 947 MB en swap. Un límite blando por debajo del uso estable no limita: genera presión de disco permanente.
2. **Swap agotada** (4/4 GB) y carga 10–15 en 4 núcleos con 4–9 % de steal del hipervisor de Oracle.
3. **Nada respetaba turnos**: SQX (Build al 82–90 % CPU produciendo 0 aceptadas), minero huérfano de 5,8–9 GB, discovery ciego a FONDEO por bug de enrutamiento (>24 h evaluando FONDEO como ULTRA), sesiones de Claude con pytest al 122 %. `nice` no salva: reparte CPU, no reduce demanda.
4. **Resurrección automática**: `discovery` y `sqx.service` están `enabled`, y el cron de `improve_cycle.sh` revive el bucle cada hora. Parar procesos no basta sin cortar las tres vías.

El remedio ya está construido (`services/ops/gobernanza_recursos.py`: turno único con flock + puerta de admisión que rechaza arrancar con swap <256 MB, RAM <1,5 GB o carga >1,5/núcleo), pero **los comandos de limpieza requieren sudo** y siguen pendientes de ejecutarse (sección A de `OPERACION_VPS.md`: stop+disable discovery, stop sqx, pkill de los huérfanos, comentar el cron). Hasta que se ejecuten, cualquier campaña nueva o push fracasará. Es la acción nº 1, cuesta 2 minutos.

---

## 5. Las velas de futuros: el problema y la solución ya elegida

Tenías razón en tu planteamiento: **no hacen falta las velas "oficiales" de CME; sirve cualquier vela compatible**. Eso es exactamente lo que el proyecto decidió y validó:

- No existe fuente gratuita de intradía CME profundo (Yahoo solo sirve 60 días de intradía fino; SQX no trae feed CME gratuito).
- Solución adoptada: **proxies CFD de Dukascopy** sin API key (`USA500IDXUSD`→ES, `USATECHIDXUSD`→NQ, `USA30IDXUSD`→YM, `XAUUSD`→GC, `XAGUSD`→SI, `LIGHTCMDUSD`→CL, + 6 majors forex), con ≥10 años de profundidad. Validación doctrinal hecha: correlación de retornos con ES real 0,9747 (peor subperiodo 0,9016). RTY no tiene proxy (confirmado): esa celda se cae o se paga dato.
- La ingesta se aceleró 40× (de 174 a 6.984 ficheros/hora) al reutilizar la sesión HTTP, y se corrigió una fusión destructiva que borraba el CSV entero en ingestas parciales.

**Estado real del backfill (2026-09-01):** ES completo y consolidado (1,23 M barras 1m / 250 K 5m / 83 K 15m, 2023→2026, huecos = festivos reales); NQ ~47 % (parado en 2024-09); **YM, GC, SI, CL y todo el forex Dukascopy a cero**, porque el script procesa los símbolos en serie en el orden del diccionario y el VPS está ahogado. Es I/O-bound (~3 % CPU): es la tarea perfecta para sacarla del VPS y correrla en tu PC esta misma noche.

Dos salvaguardas antes de minar con estos datos (ya identificadas en el repo): pasar `--dataset-source dukascopy` explícito (el modo `auto` puede resolver a los ficheros de Yahoo en silencio — la última telemetría de ES 4h usó `ds_trad_es_4h`, el dataset Yahoo remuestreado cuyo 4h está estructuralmente contaminado: 20,2 % de barras parciales) y no usar jamás el 4h remuestreado de Yahoo.

---

## 6. ¿Puede ayudar este PC? Sí, y mucho

El VPS son 4 núcleos con steal, 23 GB y tres servicios encima. Casi cualquier PC de escritorio moderno lo supera, y además tiene lo que el VPS nunca tendrá: **IP residencial**, imprescindible según tu propio corpus (`docs/conexiones_automatizar/`) porque las prop firms (Topstep/Apex vía Cloudflare/IPQS) marcan las IP de datacenter. Reparto recomendado:

| Carga | Dónde | Por qué |
| :--- | :--- | :--- |
| Backfill Dukascopy (YM/GC/SI/CL/forex) | **PC** (WSL2 recomendado: los scripts usan flock/paths Unix) | I/O-bound, horas en vez de días; no compite con nada |
| Campañas de minería (`cola_mineria.py` + `mine.py`) | **PC** | CPU-bound y paralelizable; 8–16 hilos sin contención ni steal |
| SQX / StrategyQuant X | **PC con GUI** (SQX es app Windows nativa) | Iterar la config del Builder (el fusible MC, MinTradesInRun…) es mucho más rápido con interfaz; libera 8–10 GB de RAM del VPS |
| API + web + BD canónica | VPS | Es servir, no calcular; con el VPS liberado va sobrado |
| Ejecución prop (NinjaTrader 8) | **PC** (runbook ya escrito: `NINJATRader8_DEMO_PROP_RUNBOOK.md`) | NT8 es Windows-only y necesita IP residencial |
| `git push` atascado | **PC** | El repo ya está aquí; el 408 era la CPU saturada del VPS |

Única disciplina necesaria: los resultados (datasets consolidados con manifiesto SHA-256, candidatas) se sincronizan de vuelta por git o rsync; la BD canónica sigue siendo una sola (la del VPS).

---

## 7. ¿Cloudflare, Firebase y otros terceros?

- **Firebase — sí, para lo que ya está montado.** El proyecto `traderbot-josfer` con target de hosting `ultrafondeo` (export estático de `apps/web`) y el sync one-way (`services/sync/firebase_sync_manager.py`) son el camino correcto para que el panel no dependa de que el VPS esté vivo. **Antes hay que arreglar el bug real del login**: `apps/web/lib/firebase.ts` mezcla dos proyectos (apiKey/authDomain de `goalskid-app` con databaseURL de `pecemi`); es la causa raíz del watchdog de 6 s. Es un fix de `.env.local` de 10 minutos.
- **Cloudflare — útil solo como accesorio, no como motor.** Pages podría hostear el panel estático (equivalente a Firebase Hosting: elige uno), R2 es un buen sitio barato para datasets/artefactos pesados (y sacaría el 1,3 GB de datos del repo git, que es lo que tiene el push atascado), y Tunnel serviría para exponer la web del VPS sin abrir puertos. **Workers no puede ejecutar nada de este proyecto** (backtests Python de minutos, Java de SQX): no es una plataforma de cómputo para esto.
- **Ningún tercero resuelve el cómputo pesado.** Las opciones reales de cómputo son: tu PC (gratis, ya disponible), otro VPS/instancia mejor dimensionada, o pagar datos (Databento/Polygon) si algún día los proxies se quedan cortos — hoy no hace falta.

---

## 8. Auditoría del plan de Antigravity (cloud gratuito + optimización VPS)

Revisado contra el repo el plan que te entregó Antigravity (`guia_maestra_cloud_gratuita_y_optimizacion_vps.md` / `informe_arquitectura_hibrida`). Veredicto: **la arquitectura de datos es buena y coincide con este informe; la parte de comandos tiene 4 errores que pueden costarte datos o tumbar la máquina.** No lo ejecutes tal cual.

**Adoptar (correcto y verificado):**

- La matriz R2/Firestore/Firebase Storage/Hosting es factualmente correcta (límites gratuitos reales) y R2 con egress 0 $ es exactamente el sitio para sacar los datasets de git (mi punto 9). Parquet+zstd para velas: bien. Supabase descartado: de acuerdo (pausa a los 7 días).
- Apagar SQX en el VPS y llevarlo al PC: coincide con §6 de este informe.
- zRAM zstd + `swappiness=10` + slices de systemd: técnica sólida para esta máquina, **como complemento** de la limpieza, no como sustituto.
- Confirma además que el PC tiene 32 GB de RAM: sobra para SQX y las campañas.

**Corregir antes de ejecutar:**

1. **El orden.** El plan hace `swapoff -a` en una máquina que hoy tiene la swap al 100 % y 1 MB libre: eso fuerza a devolver 4 GB a una RAM que no los tiene y puede provocar OOM-kills de la API en caliente. Primero la sección A de `OPERACION_VPS.md` (parar discovery/sqx/huérfanos/cron), verificar `free -h`, y **después** zRAM.
2. **`sudo rm -rf /tmp/*` destruiría evidencia real.** `estrategias_um` documenta ~80 MB de evidencia y diagnósticos viviendo en `/tmp` (`um_doors`, `um_mcprobe`…, riesgo D4) con solo copia parcial en `ORDENAR/`. Además viola la doctrina del proyecto (nada se borra: cuarentena con manifiesto). Copiar antes a disco permanente, luego limpiar.
3. **`vm.overcommit_memory = 1`** en una caja que acaba de morir por presión de memoria es apostar a que el OOM-killer elija bien. Dejar el valor por defecto (0).
4. **`apt purge x11-common`** puede arrastrar dependencias inesperadas. Purgar Xvfb/x11vnc es razonable (son restos de la automatización GUI de SQX, hoy legacy: el motor es sqcli headless), pero con `apt purge x11vnc xvfb` a secas y comprobando qué arrastra antes de confirmar.
5. **No duplicar mecanismos.** El repo ya tiene overrides preparados (`orchestration/ops/systemd/*.override.conf`, sección B de `OPERACION_VPS.md`) y la puerta de admisión `gobernanza_recursos.py`. Los slices `trading/batch` son compatibles, pero deben integrarse con eso (los servicios del proyecto asignados a su slice en sus units), no instalarse como capa paralela que nadie gobierna.
6. **Firestore no puede convertirse en segunda fuente de verdad.** La BD canónica es el SQLite del VPS (SSOT sellado); el repo ya tiene un push one-way a Firebase RTDB (`firebase_sync_manager.py`). Usar Firestore/RTDB solo como espejo de lectura para la web/móvil — elegir UNO de los dos, no ambos — y las escrituras siguen naciendo únicamente en el SQLite canónico.
7. Cifras de marketing: "~56 GB equivalentes" asume ratio 3,2× sostenido y "load <0,40" es aspiracional. La mejora será real pero no mágica; medir con `memory.events` y `free -h` como ya indica `OPERACION_VPS.md`.

## 9. Otros drenajes que explican "tantos problemas"

- **Agentes**: Antigravity incumplió el protocolo 5/5 (commits/pushes prohibidos, auto-despachos) y fue retirado; dos sesiones de Claude coincidieron en el repo; los pytest de subagentes saturaban la máquina. La gobernanza actual (Hermes + turno único + puerta de admisión) es la respuesta correcta; mantenerla.
- **Git**: el push lleva días muriendo con HTTP 408 porque el pack final (~260 MB) sale de una máquina colapsada; los blobs grandes ya están en `origin/tmp-sync` (no borrar esa rama). Solución: pushear desde el PC y, de fondo, dejar de versionar datasets en git (manifiestos sí, datos a R2/almacén).
- **Deudas selladas que morderán en cuanto haya una candidata**: el examen de fondeo calcula la verificación honesta barra a barra pero **no la usa para decidir** (el ranking sigue con el bootstrap optimista — podría imprimir "CUMPLE" sobre una cuenta reventada); el hardcode `5.4.0` del carril meta; los dos pipelines de gates. Ninguna es urgente hoy con 0 candidatas; las tres son obligatorias antes de certificar la primera.
- **Historial de datos fabricados ya corregido** (mérito del saneamiento): el repositorio de datasets fabricaba 100 velas en rampa ante fallos de lectura, el volumen de forex era un `or 100.0`, el 4h de Yahoo es remuestreo parcial, y la métrica de "cobertura 64–73 %" que bloqueó TRADFI medía un calendario 24/7 contra mercados que cierran. Lección permanente: cada bloqueo merece verificación independiente antes de aceptarlo.

---

## 10. Plan recomendado (en orden, sin adornos)

1. **Ejecutar los comandos sudo de `OPERACION_VPS.md` sección A** (parar/deshabilitar discovery, parar sqx, matar huérfanos, comentar el cron). 2 minutos. Nada avanza sin esto. Después, y solo después, aplicar la optimización de Antigravity con las correcciones del §8 (zRAM, sysctl sin overcommit, slices integrados, purga X11 con cuidado, `/tmp` copiado antes de limpiar).
2. **Lanzar esta noche en el PC el backfill Dukascopy** de YM, GC, SI, CL y forex (y completar NQ). Consolidar con manifiesto y llevar al VPS o minar en local.
3. **Push a GitHub desde el PC** (el repo local ya está al día hasta `7b7e7311e` según esta copia; verificar contra el VPS antes).
4. **Campaña FONDEO 5m/15m** sobre ES (y NQ al completarse) con `--dataset-source dukascopy` explícito y la telemetría nueva activa. Presupuesto de barras ya suficiente (250 K en 5m). Correrla en el PC si el VPS sigue justo.
5. **Leer la telemetría antes de ampliar nada**: si vuelve a salir "sin_ventaja" mayoritario con datos profundos, el problema es de reglas, no de datos, y el esfuerzo va al punto 6; si sale "pocas_operaciones", es de datos y se amplía el backfill.
6. **Abrir el carril de generación de reglas nuevas**: cruzar el CSV con los 2.035 .sqx (parser AST → validación con motor propio y 11 gates) y reparar la config del Builder de SQX en local (fusible MC, MinTradesInRun 20 vs MaxTradesPerDay 1 — incompatibles por diseño). Las plantillas paramétricas están agotadas; de aquí tiene que salir el edge.
7. **Antes de la primera certificación**: hacer que el examen de fondeo decida con la verificación barra a barra, quitar el hardcode 5.4.0 del carril meta, y unificar los dos pipelines de gates.
8. **Arreglar `firebase.ts`/.env.local** (proyectos mezclados) y decidir un solo hosting para el panel (Firebase Hosting ya configurado o Cloudflare Pages) con push de estado vía RTDB.
9. **Sacar los datasets pesados de git** (R2/almacén + manifiestos SHA-256 en el repo).
10. **Cuando FONDEO tenga sus primeras certificadas**, retomar ULTRA desde `PUNTO_GUARDADO_ULTRA.md` — está bien congelado y no pierde nada esperando.

---

## 11. Veredicto final

El proyecto no está podrido: está **en el valle que separa la ilusión de la realidad**. Todo lo que "funcionaba" antes era un motor que regalaba dinero ficticio, y el trabajo de las últimas semanas —sincerar el motor, purgar 728 falsas certificadas, medir el VPS, validar proxies, persistir la telemetría— es exactamente lo que había que hacer, aunque deje el marcador en 0. Los dos cuellos de botella reales hoy son físicos y conocidos: una máquina ahogada que solo se libera con sudo, y un backfill de datos a medias que tu PC puede terminar en horas. El tercer cuello es el de verdad difícil y conviene decirlo sin rodeos: **con las familias de reglas actuales, el edge no aparece ni con datos perfectos**. La apuesta con más probabilidad de romper el 0 no es más fuerza bruta sobre las mismas plantillas, sino el carril SQX (generación genética de reglas nuevas, validadas después por tu propio motor honesto) más el F04 de mejora — y ahora, con telemetría persistida, cada campaña por fin enseñará algo aunque falle.
