# PLAN MAESTRO v5 — ULTRARENTABLE: qué tiene que hacer la aplicación y cómo, en principio, se consigue

> Escrito por el orquestador el 2026-09-03 a petición de Emilio: *"analiza todo lo que te he pedido
> para la app y prepara la mejor manera para conseguirlo; deja clarísimo y completo el plan en la
> página plan"*. Sustituye al índice v4 (archivado en `archive/plan_maestro_2026-09-01_v4_indice.md`).
> Todo lo que aquí se afirma sobre el estado actual está **medido** esta madrugada, con el fichero o
> el comando que lo prueba; lo que es propuesta se marca como **"en principio"** y queda pendiente de
> que lo evalúen las IAs y lo decida Emilio. Las fases F00-F10 (`plan/bloques/`) siguen siendo la
> fuente de verdad del **estado**; este documento es la fuente de verdad del **qué y el cómo**.

---

## 0. En una página

**Qué se persigue.** Estrategias de trading que aprueben el examen de una cuenta de fondeo (prop firm)
sobre futuros CME y que después aguanten operando. Objetivo sellado: **≥ 20 % mensual sostenible
(mediana), probabilidad de reventar la cuenta ≤ 20 % a seis meses, examen superado en 3-8 días**.

**Cómo se consigue, en cuatro pasos encadenados** (M1 → M2 → M3 → M4):

| Paso | Qué hace | Quién lo hace | Estado hoy |
| :--- | :--- | :--- | :--- |
| **M1 Generar** | StrategyQuant produce estrategias en bruto, **ancho**, sobre 25 celdas (5 activos × 5 marcos) | StrategyQuant en el servidor Hetzner | **Desbloqueado hoy**; datos cargándose |
| **M2 Mejorar** | Nuestro motor las prueba con el criterio 1.1, descarta con motivo y aprende de lo que muere | Motor propio | Diseño hecho; código a medias; aprendizaje vacío |
| **M3 Valorar** | Reproduce las reglas exactas de cada firma sobre las operaciones reales | Examen propio | Diseñado; sin candidatas que examinar |
| **M4 Combinar** | Junta varias válidas para bajar la varianza | Motor propio | Diseñado; sin material |
| **Operar** | Automático donde la firma lo permita; alerta con la orden exacta donde no | Trading Desk + alertas | Por construir |

**Dónde estamos.** Cero estrategias válidas. Y la causa, demostrada esta madrugada, no es el mercado:
**StrategyQuant nunca ha estado conectado a nuestro motor** (§3.1), su generador apuntaba a un mercado
equivocado con un filtro que aceptaba cero por construcción (§3.2), y las páginas de la web contaban
como vivos sistemas que estaban muertos (§7). Todo eso está identificado y en el tablero.

**Lo inmediato** (§9): cargar en StrategyQuant los 3,7 años de datos que ya tenemos, crear los 25
proyectos con filtros permisivos, medir cuántas estrategias salen por hora, y **solo entonces** pasar a
M2. Mientras, corregir el bug de la comisión del motor y vaciar de mentiras la web.

---

## 1. Las decisiones que ya están tomadas (no se vuelven a discutir)

| # | Decisión | Quién y cuándo |
| :--- | :--- | :--- |
| D1 | **Ejecución automática donde la firma lo permita; alertas con la orden exacta donde no.** | Emilio, 03-09 |
| D2 | **El sistema aprende de lo hecho, bueno y malo.** Antes de construirlo, investigar cómo se hace bien. | Emilio, 03-09 |
| D3 | **Datos primero**: la descarga se completa antes de generar en serio. *(Ya cumplida en el servidor: §5.2.)* | Emilio, 03-09 |
| D4 | **El mínimo de operaciones se escala según el marco temporal.** El listón se traduce, no se relaja. | Emilio, 03-09 |
| D5 | **Solo se enseña lo que funciona.** Ni estrategias fallidas ni páginas sin implementar en el menú. | Emilio, 02-09 |
| D6 | **Todo monocromo.** Color solo para dinero o estado crítico. | Emilio, 02-09 |
| D7 | **ULTRA (cripto) aparcado.** El 100 % del trabajo es FONDEO. | Emilio, 01-09 |
| D8 | **El sistema trabaja solo, 24 horas, en bucle**, aguanta caídas y guarda en el servidor y en Firebase. | Emilio, 03-09 |
| D9 | **M1 primero.** No se toca M2 ni M3 hasta que M1 entregue caudal medido. Filtros permisivos en StrategyQuant; el filtro duro es nuestro. | Emilio, 03-09 |
| D10 | **AGY (Antigravity) hace código y web; el servidor lo lleva el orquestador**, directo y sin esperas. Emilio no interviene en la ejecución. | Emilio, 03-09 |
| D11 | **Nombrar las cosas con sentido**: proyectos `FONDEO_<SÍMBOLO>_<TF>` con el símbolo del micro que se opera. | Emilio, 03-09 |

Y las reglas invariantes del proyecto, que van por encima de todo (`CLAUDE.md`): **REAL-ONLY** (nada
sintético, evidencia en disco), **criterio 1.1 sellado**, **regla #26** (si cambia lo que el motor
produce, sube la versión y lo viejo queda como antiguo, nunca se borra), **nunca `rm`** (cuarentena
con huella), **un pesado a la vez** por la puerta de admisión.

---

## 2. El objetivo, medido

**Estrategia válida para fondeo** es la que cumple **a la vez**: ruta FONDEO · certificada con el motor
vigente · mínimo de operaciones fuera de muestra según su marco temporal (D4) · factor de beneficio
fuera de muestra ≥ 1,25 · fuera de muestra ≥ la mitad de dentro de muestra · las once comprobaciones
con evidencia real · penalización por el número de intentos (Deflated Sharpe positivo).

Es la única definición que puede usar cualquier página o informe. Hoy la cumplen **cero** estrategias.
Las cinco que la base marca como aprobadas son del carril ULTRA, con motores antiguos y 25-68
operaciones: no cuentan y la web ya lo explica.

**Sobre D4, cómo se traduce el mínimo por marco temporal (en principio).** No se elige un número: se
calcula. El mínimo de operaciones es el que da, en cada marco, la misma potencia estadística que dan
200 operaciones en 5 minutos para distinguir un factor de beneficio de 1,25 del azar. Se computa sobre
la distribución real de operaciones por año de cada celda cuando M1 la entregue. **Pendiente de
evaluar**: la fórmula exacta y la tabla resultante; hasta entonces, 200 en todos los marcos.

---

## 3. Lo que hemos aprendido esta madrugada (y cambia el plan)

### 3.1 StrategyQuant nunca ha estado enchufado
`grep` de las estrategias de StrategyQuant sobre el motor y el generador propio: **cero resultados**.
267 estrategias extraídas, las 267 en "sin verificar". La función que debería leer las reglas de una
estrategia devuelve, escrito a mano, "no disponible". 59 filas marcadas como verificadas con **cero**
backtests en toda la base. Fuente: `DIAGNOSTICO_SQX_2026-09-03.md`.

### 3.2 El generador estaba estéril por construcción
En la tarea de **generación** el máximo de operaciones al día es 0 (sin límite); en la de **mejora**,
**1**. Y el ciclo automático lanzaba justo la de mejora: exigía varias operaciones por serie y una sola
al día. Resultado: 37 ciclos, cero aceptadas. Además apuntaba a **AUDUSD**, una divisa, no un activo de
fondeo. Fuente: `tablero/A10.md`, `sqx.service.d-override.conf`.

### 3.3 El modo automático estaba bloqueado, y ya no
StrategyQuant no admite dos instancias sobre la misma carpeta; la ventana tenía el bloqueo y el modo
de comandos respondía "CLI not ready". Hoy hay una **segunda instalación** (`/opt/SQX-headless`) que
responde en el puerto 5051 con la lista completa de proyectos. Ninguno de los dos puertos se ve desde
internet. Fuente: `tablero/A16.md`, medido por el orquestador.

### 3.4 Los datos: completos en el servidor, casi vacíos en StrategyQuant
La descarga está **completa** para los cinco activos en los cinco marcos (15 trimestres, 2023-Q1 →
2026-Q3). Los 25 ficheros en el formato que StrategyQuant importa existen, 3,7 años cada uno, 589 MB.
Pero StrategyQuant tenía cargados **72 días** de intradía. Los ficheros ya están copiados a la
instalación automática; falta importarlos. Fuente: `tablero/A15.md`, `A20.md`.

### 3.5 El sistema de aprendizaje existe en tres versiones, ninguna en el plan
Un diseño completo y bueno; un esqueleto limpio sin conectar; un mejorador antiguo que viola la
doctrina (usa el tramo ciego dentro del bucle); y un sistema "semántico" con la base de conocimiento a
**cero filas en once tablas**, presentado en la web como si analizara contra "5.000 estrategias
fallidas". Fuente: `plan/bloques/F04_mejora_inteligente.md`, actualización 03-09.

### 3.6 Lo que dice la investigación externa sobre usar bien StrategyQuant
Fuentes oficiales (documentación y blog de StrategyQuant), con lo que los escépticos tumbaron fuera:

- **El flujo correcto** es: datos → configurar el generador con pocos bloques y filtros → construir →
  evaluar y guardar candidatas → **revalidar robustez** (otros periodos, otros mercados, simulaciones
  aleatorias, tramos) → mejorar opcionalmente → ajuste final por tramos → cartera. La propia
  documentación dice que generar es "la mitad del trabajo"; la otra mitad es validar.
- **Ajustes con respaldo oficial**: restringir los bloques de construcción a un grupo pequeño; desfase
  entre señal y ejecución de 0 a 5 barras, mínimo 1; periodos de los indicadores por debajo de 100,
  idealmente de 50; stop y objetivo obligatorios; población por isla 10-100, generaciones 5-100, islas
  1-10; reparto de datos 33/33/33 o 60/20/20 con el último tramo ciego; en las pruebas por tramos,
  estabilidad del beneficio > 60 % y del drawdown < 200 %; filtro de correlación 0,5; y el módulo
  **Prop Firm Analysis** nuevo del Build 144, sin documentación pública todavía.
- **Sobre el terreno intradía**: la fuente oficial que lo llama "mucho más difícil" tiene ocho años, y
  hay usuarios que reportan éxito en 1 minuto y en 15 minutos a 4 horas. Conclusión honesta: **más
  difícil de validar, no imposible**. La rejilla de 25 celdas es correcta precisamente porque no
  apuesta todo al intradía.
- **Costes de los micros para el gestor de datos** (cálculo de la comunidad a partir de tarifas
  oficiales, no cifra oficial): comisión 0,58-1,70 USD por contrato y vuelta completa, diferencial de 1
  tick, deslizamiento de 2 ticks como mínimo realista.
- **Lo que se tumbó** y no se usa: el embudo "2.000 candidatas → 1-3 finales" (artículo de 2015 sobre
  una versión anterior), el estudio de Hudec (solo forex en 4 horas), y varias citas de foro que no se
  pudieron localizar.

---

## 4. M1 — GENERAR: exprimir StrategyQuant

**Qué debe hacer.** Producir el máximo caudal de estrategias en bruto sobre las 25 celdas. No tiene que
producir estrategias buenas: eso lo decide M2. Lo que sí tiene que dejar es **procedencia** (proyecto,
banco, fecha, huella) y **conteo** (cuántas se evaluaron en total, no solo las que quedan), porque sin
ese conteo la penalización por multiplicidad de M2 es mentira.

**La rejilla.**

| Activo | Ejecución (micro) | 1m | 5m | 15m | 1h | 4h |
| :--- | :--- | :-: | :-: | :-: | :-: | :-: |
| ES (S&P 500) | MES | ✓ | ✓ | ✓ | ✓ | ✓ |
| NQ (Nasdaq) | MNQ | ✓ | ✓ | ✓ | ✓ | ✓ |
| YM (Dow) | MYM | ✓ | ✓ | ✓ | ✓ | ✓ |
| GC (oro) | MGC | ✓ | ✓ | ✓ | ✓ | ✓ |
| CL (petróleo) | MCL | ✓ | ✓ | ✓ | ✓ | ✓ |

RTY (Russell) fuera hasta tener datos: no hay proxy en Dukascopy (W1.5).

**Cómo, en principio.**

1. **Cargar los datos** en la instalación automática por el modo de comandos: 25 importaciones desde
   `/opt/SQX-headless/import/` con `-data action=import`, en UTC. **Decisión previa** (pendiente de
   evaluar): cargarlos bajo instrumentos **micro** (MES, MNQ, MYM, MGC, MCL) creados con su valor del
   punto y sus costes reales, no bajo los contratos completos que hoy trae StrategyQuant. Es lo
   coherente con D11 y con la lección de la comisión (§3.2 del motor). *Tarea A20.*
2. **Crear los 25 proyectos** `FONDEO_<SÍMBOLO>_<TF>` por el modo de comandos, cada uno con su banco
   `__crudas` y su banco `__robustas`, y con **filtros permisivos** (D9): sin exigirle a StrategyQuant
   lo que exige el criterio 1.1. Como referencia de partida, y pendiente de evaluar: mínimo de
   operaciones bajo, sin límite de operaciones al día en ninguna tarea (la lección de §3.2), factor de
   beneficio de aceptación en torno a 1,1, y nada de pruebas de robustez dentro de M1.
3. **Configurar la búsqueda** dentro de los rangos oficiales (§3.6): pocos bloques elegidos a
   propósito, desfase 1-5 barras, periodos < 50, stop y objetivo obligatorios, población y generaciones
   en el rango documentado, reparto de datos con tramo ciego que la evolución no ve.
4. **Fijar los costes** por símbolo micro en el gestor de datos con las cifras de §3.6, y anotar de
   dónde salen.
5. **Ejecutar** las 25 construcciones en el servidor Hetzner, que tiene 57 GB libres y 8 hilos
   ociosos, **una celda pesada a la vez** por la puerta de admisión, empezando por las celdas de 1 y 4
   horas (menos ruido, menos coste relativo) y siguiendo por las intradía.
6. **Medir el caudal**: estrategias generadas por hora y por celda, y coste de máquina. Ese número es
   el criterio de "M1 listo".
7. **Exportar** cada banco a CSV con `-databank action=export` para que M2 lo consuma, y **resolver el
   puente** de las reglas (§3.1): hoy la interfaz automática no expone el código de la estrategia.
   Camino en principio: usar el formato `.sqx` guardado por `-databank action=save` y traducirlo a
   nuestro formato canónico (tarea W3.3 del plan de fondeo). **Pendiente de evaluar** frente a la
   alternativa de confiar el primer filtro a las pruebas de robustez del propio StrategyQuant.

**Estado hoy.** HECHO: modo automático (§3.3), datos en el servidor (§3.4), convención de nombres,
diagnóstico de la esterilidad. A MEDIAS: importación de datos (A20, ficheros ya copiados). POR HACER:
instrumentos micro, 25 proyectos, configuración permisiva, primera construcción, medida de caudal,
puente de reglas. **Licencia**: de prueba hasta el **17-09-2026**; decisión E01 de Emilio (comprar, no
comprar, o esperar a ver el caudal).

**Pendiente de evaluar por las IAs.** Instrumento micro vs. completo; valores exactos de los filtros
permisivos; orden de las celdas; si conviene una sola instalación automática con 25 proyectos o varias
en paralelo; cuánto rinde de verdad el servidor; y el camino del puente de reglas.

---

## 5. M2 — MEJORAR Y APRENDER: probar duro, descartar con motivo, no repetir

**Qué debe hacer.** Coger las crudas de M1 y pasarlas por nuestro motor con el criterio 1.1: tres
cribas seguidas (entrenamiento, validación, tramo ciego), siempre con costes reales descontados. Lo que
muere, muere **con motivo escrito** (sin ventaja, se la comió el coste, pocas operaciones) y ese motivo
se guarda. Lo que se queda cerca vuelve a M1/M2 **con una hipótesis**, nunca a fuerza bruta. Y cada
mejora aceptada suma la multiplicidad desde el origen, para que la penalización sea real.

**Cómo, en principio.**

1. **Antes de nada, el motor cobra la comisión correcta**: hoy cobra a los micros los 2,50 USD del
   contrato completo en vez de 0,60 (3,80 USD de más por operación). Corrección, test, versión 5.19.0
   por la regla #26 y baseline F02. *Tarea A07 / contrato GO_B23.* Después, repetir la última campaña
   (E2c) para ver si revive alguna de las 20 configuraciones que morían solo por ese sobrecoste.
2. **Conectar el esqueleto limpio** `services/improvement/` (respeta el tramo ciego, pasa sus siete
   pruebas, no lo llama nadie) con una fuente real de propuestas de mejora.
3. **Llenar la base de aprendizaje desde la telemetría** que ya producen las campañas (cada
   configuración deja escrito por qué murió; hoy eso se tira). Es la materia prima de D2 y no exige
   construir nada nuevo: exige volcar lo que ya existe.
4. **Apartar a cuarentena** el mejorador antiguo que usa el tramo ciego dentro del bucle, con
   manifiesto, cuando se decida.
5. **Cerrar la investigación I2** (qué sistema propone las mejoras: búsqueda de parámetros, mutación
   semántica o el propio StrategyQuant) con un banco de pruebas sobre casi-válidas reales antes de
   sellar nada.

**Estado hoy.** HECHO: diseño completo (`ARQUITECTURA_MODULAR_ESTRATEGIAS.md`); las tres cribas y la
telemetría de embudos funcionan en `scripts/mine.py`. A MEDIAS: corrección de la comisión (empezada);
esqueleto limpio sin conectar; sistema semántico hueco. POR HACER: base de aprendizaje (cero filas),
elección del mejorador, cuarentena del antiguo. **Bloqueado a propósito** por D9 hasta que M1 entregue.

**Pendiente de evaluar.** Cómo se mide que el aprendizaje sirve (tasa de supervivencia con y sin
memoria); qué mejorador; la tabla de mínimos por marco temporal (D4).

---

## 6. M3 y M4 — VALORAR Y COMBINAR, y cómo se opera

**M3, el examen.** Reproduce las reglas exactas de cada firma (pérdida diaria, pérdida total, días
mínimos, objetivo, tamaño) sobre las operaciones reales de la estrategia, con la cuenta en tiempo real,
y devuelve: probabilidad de aprobar, probabilidad de reventar la cuenta a seis meses, días esperados,
mejor horario y tamaño recomendado. Existe el guion (`scripts/fondeo_examen.py`) y el bloque F07; no
hay candidatas que examinar. El módulo **Prop Firm Analysis** del Build 144 de StrategyQuant es una
segunda opinión posible, pendiente de evaluar porque no tiene documentación pública.

**M4, la cartera.** Reparte capital entre varias válidas y examina la combinación como una estrategia
más. Regla: si no mejora a su mejor componente, se descarta. Necesita ≥ 2 válidas con solape de fechas
para medir correlación real. Diseñado; sin material.

**Operar (D1).** Dos modos, visibles por cuenta:
- **Automático** donde la firma permita bots: puente de ejecución, órdenes mandadas y su resultado.
- **Alerta** donde no: la web avisa y muestra la orden exacta y copiable (activo, dirección, entrada,
  stop, objetivo, contratos), con la hora de la señal y cuánto lleva viva. Emilio la mete a mano.
- **"¿Permite bots?"** pasa a ser dato de primera clase del catálogo de firmas.
- **Pendiente de evaluar**: por dónde llegan las alertas (web, móvil, correo, Telegram), cuántas
  cuentas a la vez, riesgo por operación, y qué se hace cuando una estrategia deja de funcionar en real.

---

## 7. La web: qué enseña y qué nunca enseña

Especificación completa en `ESPECIFICACION_WEB.md`. Lo esencial:

- **Portada**: ¿hay algo listo? ¿qué se ha hecho? ¿qué hace el bucle ahora? Tres cifras reales y un
  párrafo construido con ellas.
- **Estrategias**: solo las válidas, con todo para llevarlas al Trading Desk; los cuatro módulos como
  subpáginas con "qué hace / qué necesita / estado hoy / qué falta".
- **Plan**: este documento primero; después las fases con su estado, las tareas, el tablero de los
  agentes, el buzón y los comentarios de Emilio.
- **Trading Desk** con sus dos modos, **Prop Firms**, **Sistema** (¿funciona todo?), y el archivo
  técnico fuera del menú.
- **Cuenta**: un solo administrador, josferestudio@gmail.com, sesión permanente en el PC.

Las reglas que no se negocian: cada cifra con fuente; **una etiqueta es una afirmación** (si dice
"activo", alguien lo midió); una sola definición de "válida"; lo no implementado no está en el menú;
lenguaje llano. Esta madrugada se corrigieron cuatro etiquetas falsas (A13, A17, A18): el dato de al
lado era correcto y por eso colaban.

---

## 8. La máquina: 24 horas, tres servidores, datos y seguridad

**El bucle (D8).** Generar → probar → descartar con motivo → reintentar con hipótesis → examinar →
componer, y vuelta a empezar con lo aprendido. Un pesado a la vez por máquina por la puerta de admisión
(`services/ops/gobernanza_recursos.py`), que existe porque el servidor se cayó tres veces por procesos
compitiendo. Aguantar caídas exige tres cosas medibles: se relanza solo, **reanuda donde estaba** (cada
trabajo deja su estado en disco), y deja rastro de la caída. **Hoy el bucle no existe**: hay piezas
sueltas sin encadenar. Montarlo es F03/F04.

**Dónde se guarda.** La base canónica (SQLite, Oracle) es el **maestro único**; Firebase es el espejo
para lo que Emilio consulta desde cualquier sitio (estado del bucle, alertas, comentarios); los
ficheros pesados en disco con huella. Si discrepan, manda el servidor.

**Las tres máquinas.**

| Máquina | Qué hace | Por qué |
| :--- | :--- | :--- |
| **Hetzner** (i7, 8 hilos, 62 GB, x86-64) | StrategyQuant automático y, después, las campañas del motor | Vacío y dedicado; StrategyQuant pasa de 1,2 núcleos a 8 hilos |
| **Oracle** (ARM, 4 núcleos, 23 GB) | API, base canónica, web pública, descarga de datos, Hermes | Es la casa de la base y de Hermes; ya no lleva StrategyQuant (apagado 03-09) |
| **PC de Emilio** | Orquestación, desarrollo, build de la web, AGY | Donde trabaja él |

Hallazgo que condicionó todo: la instalación de StrategyQuant de Oracle era **ARM**; el Hetzner es
Intel. No se copia: se instala y se trasladan datos.

**Seguridad.** El Hetzner llegó sin cortafuegos y con el escritorio remoto público sin contraseña;
cerrado el 03-09 (cortafuegos, contraseña, fail2ban, que ya contaba 23 intentos de fuerza bruta).
StrategyQuant **no tiene autenticación**: sus puertos jamás se publican; Oracle lo alcanzará por túnel.

---

## 9. El orden de trabajo, de hoy en adelante

Cada línea es una tarea del tablero o lo será. Primero lo que desbloquea, después lo que produce.

**Ahora (M1, esta semana).**
1. A20 · Importar los 25 ficheros en StrategyQuant bajo instrumentos micro *(orquestador; decisión de instrumento pendiente de evaluar)*.
2. A18 · Vaciar de afirmaciones falsas la página de Mejora *(AGY, urgente)*.
3. A07 · Motor 5.19.0: comisión del contrato que se ejecuta *(AGY)*.
4. Nueva · Crear los 25 proyectos `FONDEO_*` con configuración permisiva por el modo de comandos *(orquestador)*.
5. Nueva · Primera construcción en una celda de 1 hora, medir caudal y coste *(orquestador)*.
6. Nueva · Exportar el primer banco de crudas y probar el puente de reglas sobre 20 estrategias (W3.3) *(AGY + orquestador)*.
7. E01 · Emilio decide la licencia antes del 17-09.

**Después (M2).** Repetir E2c con la comisión correcta; volcar la telemetría en la base de aprendizaje;
conectar el esqueleto de mejora; cerrar I2; calcular la tabla de mínimos por marco (D4).

**Después (M3, M4, operar).** Examen sobre las primeras válidas; cartera cuando haya dos; Trading
Desk con sus dos modos y la pantalla de alertas; catálogo de firmas con "permite bots".

**Transversal.** El bucle 24 horas con reanudación; espejo en Firebase; la web enseñando el estado
del bucle; el tablero y el buzón como sistema de orquestación (ya funcionan: 15 tareas verificadas
esta noche).

**Criterio de "M1 listo"**: para cada celda con datos, un banco de crudas con procedencia y conteo, y
un número medido de estrategias por hora. Solo entonces se pasa a M2.

---

## 10. Preguntas abiertas para Emilio

1. Licencia de StrategyQuant (E01): comprar, no comprar, o esperar al primer caudal. Fecha: 17-09.
2. Por dónde quiere las alertas de operación y cuántas cuentas de fondeo piensa llevar a la vez.
3. Riesgo por operación: fijo por estrategia o ajustable desde la web.
4. Qué hace el sistema cuando una estrategia deja de funcionar en real: parar sola o avisar.
5. Si quiere ver la evolución en el tiempo (certificadas por semana) o solo la foto de hoy.
6. Cuándo se retoma ULTRA y con qué señal.

## 11. Cómo se mide que avanzamos

Cada semana, tres números y nada más: **estrategias generadas por hora** (M1), **casi-válidas** (a ≤ 2
comprobaciones de pasar, M2) y **válidas** (la definición de §2). Hoy: en marcha / 0 / 0. Todo lo demás
es medio.

## 12. Fuentes

`ESPECIFICACION_WEB.md` (decisiones y web) · `ARQUITECTURA_MODULAR_ESTRATEGIAS.md` (M1-M4) ·
`DIAGNOSTICO_SQX_2026-09-03.md` · `plan/bloques/F00-F10` (estado por fase) · `PLAN_LOCAL_FONDEO.md`
(41 tareas W) · `PLAN_INVESTIGACION_PROFUNDA.md` (I1-I7) · `ARQUITECTURA_RECURSOS.md` (máquinas) ·
`tablero/` (A01-A20, E01, buzón) · investigación externa digerida del 03-09 (flujo de trabajo de
`wf_9940c479-c81`) · `CLAUDE.md` (reglas invariantes).
