# LA WEB DE ULTRARENTABLE — qué es, qué hace cada página y cómo se decide que está lista

> Documento maestro de la web. Se lee en `/plan`, pestaña **Especificación Web**. Manda sobre
> cualquier decisión de producto: si algo no está aquí, no se construye; si se construye algo, se
> escribe aquí el mismo día. Última revisión: **2026-09-03**, con las cuatro decisiones que tomó
> Emilio esa madrugada (§2).
>
> Estilo visual: `docs/19_UI_STYLE_SPEC.md`. Reparto de máquinas: `orchestration/ARQUITECTURA_RECURSOS.md`.
> Plan por fases: `orchestration/state/plan/bloques/F*.md`.

---

## 1. Qué es esto y para quién

Es el **panel de mando de una fábrica de estrategias de trading**. La fábrica busca una cosa
concreta: estrategias que aprueben el examen de una cuenta de fondeo (prop firm) y que después
aguanten operando.

La usa **una persona que no programa** y que necesita responder, sin abrir una terminal:

1. ¿Hay alguna estrategia lista para llevar a una cuenta? ¿Cuáles y con qué números?
2. ¿Qué está haciendo el sistema ahora y qué ha encontrado en la última búsqueda?
3. ¿En qué punto del plan estamos, qué falta y quién lo está haciendo?
4. ¿Funciona todo, o hay algo caído?
5. Cuando llegue el momento: ¿qué orden tengo que meter, en qué cuenta y con qué tamaño?

Lo que **no** es: un escaparate, un panel de vanidad, ni un explorador técnico. Lo técnico existe,
pero vive un clic más allá y se llama archivo técnico.

## 2. Decisiones tomadas (con fecha, para no volver a discutirlas)

| # | Decisión | Fecha | Consecuencia para la web |
| :--- | :--- | :--- | :--- |
| D1 | **Ejecución: automático donde se pueda, alertas donde no.** Las firmas que permiten bots se operan solas; las que los prohíben mandan aviso y Emilio mete la orden a mano. | 03-09 | El Trading Desk necesita **dos modos** visibles, y cada estrategia lista debe decir en cuál está. Hace falta una pantalla de **alertas** con la orden exacta y copiable. |
| D2 | **El sistema tiene que aprender de lo hecho**, bueno y malo, para las siguientes búsquedas. Emilio pide investigar cómo se construye eso antes de decidir la forma. | 03-09 | Habrá una página o sección de **memoria**: qué se probó, qué murió y por qué, para no repetirlo. Pendiente de la investigación. |
| D3 | **Datos primero: se completa la descarga antes de generar en serio.** | 03-09 | La página de Generación debe enseñar el **estado de la descarga por celda** (activo × marco temporal), no solo lo que hay. |
| D4 | **El mínimo de operaciones se escala según el marco temporal.** 200 operaciones fuera de muestra en 4 horas son años de historia; el listón se traduce, no se relaja. | 03-09 | Donde se diga "válida", hay que poder ver **qué mínimo se le aplicó y por qué**. |
| D5 | **Solo se enseña lo que funciona.** Las estrategias fallidas y las páginas no implementadas no se muestran al usuario. | 02-09 | Regla de entrada al menú (§5). |
| D6 | **Todo monocromo.** Grises, negro, blanco. Color solo para dinero (verde/rojo) o estado crítico. | 02-09 | Sin badges de colores, sin animaciones, sin texto claro sobre fondo claro. |
| D7 | **ULTRA (cripto) está aparcado.** El 100 % del trabajo es FONDEO. | 01-09 | Lo de ULTRA se muestra en gris y etiquetado como aparcado, nunca como trabajo en curso. |
| D8 | **El sistema trabaja solo, 24 horas al día, en bucle**, de forma organizada: aguanta caídas y reinicios, y guarda su estado en el servidor **y** en Firebase. | 03-09 | La web tiene que enseñar **qué está haciendo el bucle ahora mismo**, desde cuándo, y si se ha caído y reanudado. Ver §8. |

## 3. Las cinco reglas que no se negocian

1. **Cada cifra tiene una fuente.** Sale de la API, de la base canónica o de un fichero del
   repositorio. Sin dato ⇒ `sin evidencia`, en gris. Nunca un cero inventado ni una unidad supuesta.
2. **Una etiqueta es una afirmación.** Si pone "activo", alguien ha medido que está activo. Si no se
   ha medido, la etiqueta miente aunque el número de al lado sea correcto.
3. **Una sola definición de "válida"** (§4.2). Ninguna página puede tener la suya.
4. **Lo que no está implementado no está en el menú.** Ni en gris, ni "próximamente".
5. **Lenguaje llano.** Las siglas se explican o no se usan. Nada de "OOS", "PF" o "DSR" sueltos en
   la vista principal.

## 4. Mapa del sitio: qué hace cada página

### 4.1 Portada `/`
- **Responde a**: ¿hay algo listo y qué se ha hecho últimamente?
- **Muestra**: estado de la API y versión del motor; tres cifras (estrategias listas para fondeo,
  configuraciones probadas en la última búsqueda y cuántas pasaron la primera criba, candidatas
  evaluadas en total); un párrafo construido con esas cifras; enlaces solo a páginas que existen.
- **Nunca**: tarjetas grandilocuentes, cifras a mano, ni aprobaciones antiguas presentadas como
  válidas.
- **Estado**: implementada (02-09).

### 4.2 Estrategias `/estrategias` — la página maestra
- **Responde a**: ¿qué tengo listo para llevar a una cuenta?
- **La definición sellada de "válida para fondeo"**, que es la única que puede usar la web:
  ruta FONDEO · certificada con el motor vigente · **mínimo de operaciones fuera de muestra según su
  marco temporal** (D4) · factor de beneficio fuera de muestra ≥ 1,25 · las once comprobaciones con
  evidencia real, no deducidas del estado.
- **Muestra por estrategia**: nombre, mercado y marco temporal, factor de beneficio, operaciones,
  caída máxima, rendimiento mensual y anual (solo si la API confirma de dónde salen), verificación
  del registro de operaciones, comprobaciones superadas, motor, identificador y huella de datos
  copiables, y el botón para llevarla al Trading Desk.
- **Si no hay ninguna**: lo dice y explica por qué las certificaciones antiguas no cuentan.
- **Nunca**: estrategias fallidas, paneles técnicos, comprobaciones deducidas del estado.
- **Estado**: implementada (02-09). Hoy: cero válidas, y es la cifra real.

### 4.3 Los cuatro módulos, subpáginas de Estrategias

Cada uno con la misma estructura: **qué hace · qué necesita · estado hoy · qué falta**.

| Módulo | Qué es | Qué debe mostrar |
| :--- | :--- | :--- |
| **1. Generación** `/estrategias/generacion` | La fábrica: StrategyQuant produce estrategias en bruto | Conexión con StrategyQuant y **en qué máquina** corre; proyectos **nuestros** separados de las herramientas de fábrica del programa; estado de la descarga de datos por celda (D3); estrategias crudas producidas y a qué ritmo |
| **2. Mejora** `/estrategias/mejora` | El filtro: nuestro motor prueba cada una y descarta con motivo | Últimas campañas con cuántas se probaron, cuántas pasaron y por qué murieron las demás; el detalle por familia |
| **3. Valoración** `/estrategias/valoracion` | El examen: ¿aprobaría las reglas de una prop firm? | Reglas de cada firma, probabilidad de aprobar, probabilidad de reventar la cuenta, días esperados, tamaño recomendado |
| **4. Meta** `/estrategias/meta` | La cartera: combinar varias para bajar el riesgo | Composiciones, correlación real entre componentes y si la combinación mejora a su mejor pieza suelta |

### 4.4 Trading Desk `/trading-desk` — donde se opera
Con la decisión D1, esta página tiene **dos modos** y debe dejar clarísimo en cuál está cada cuenta:

- **Modo automático**: la firma permite bots. Se muestra la conexión, las órdenes que ha mandado el
  sistema y el resultado de cada una.
- **Modo alerta**: la firma prohíbe bots. La web **avisa** y muestra la orden exacta para copiar:
  activo, dirección, precio de entrada, stop, objetivo y número de contratos. Con hora de la señal y
  cuánto tiempo lleva viva. Emilio la mete a mano en la plataforma de la firma.
- Debe existir una **pantalla de alertas** propia, que es la que él tendrá abierta cuando opere.
- **Estado**: parcial. Hoy sin motor conectado, y la cabecera debe decirlo.

### 4.5 Prop Firms `/prop-firms`
- Catálogo de firmas con sus reglas reales: pérdida diaria, pérdida total, días mínimos, objetivo,
  y **si permiten operar con bots** (dato que ahora es de primera clase por D1).
- **Estado**: por verificar contra su fuente.

### 4.6 Plan `/plan`
- El plan completo: las once fases con su estado, las tareas de ejecución, las investigaciones, el
  plan maestro original, esta especificación, el tablero de tareas de los agentes y el buzón.
- **Se actualiza sola**: lee los ficheros del repositorio cada treinta segundos.
- **Estado**: implementada (03-09). Le falta la pantalla de comentarios (§6).

### 4.7 Sistema `/sistema`
- ¿Funciona todo? API, motor, servicios de las tres máquinas, datos, últimos errores.
- **Estado**: por verificar.

### 4.8 Archivo técnico `/candidatos`
- Todo lo evaluado, incluido lo fallido. Uso interno. **Fuera del menú**: se llega desde el pie de
  Estrategias.
- **Estado**: implementada.

### 4.9 Cuenta `/login`, `/registro`, `/perfil`
- Acceso con Google. Un solo administrador: **josferestudio@gmail.com**, el único registrado.
- En el ordenador de Emilio la sesión es permanente y no pide login; en el servidor público, sí.
- **Estado**: implementada.

### 4.10 Aparcado
- `/ultra`: carril cripto, aparcado por decisión D7. Enlace en gris desde la portada, no en el menú.
- `/tradesfera`: tratado de referencia. En el menú solo si Emilio lo quiere.

## 5. Cuándo una página entra en el menú

Solo cuando cumple las cinco: carga sin error contra la API real, cada cifra tiene fuente, sin dato
dice `sin evidencia`, cumple el estilo monocromo, y pasan la comprobación de tipos y el build de
producción. Mientras no, existe pero no se enlaza.

## 6. La pantalla de comentarios (pedida el 03-09)

Emilio necesita poder decir "esto está raro" o "aquí falta algo" **sin salir de la web** y sin que se
pierda. Requisitos:

- Un botón visible en `/plan` que abre una caja de texto.
- Al guardar, el comentario se **escribe en el repositorio**, en
  `orchestration/tablero/COMENTARIOS_EMILIO.md`, con la fecha y la página desde la que se escribió.
- La misma pantalla muestra los comentarios anteriores y si el orquestador ya los ha atendido.
- No hace falta base de datos: un fichero de texto es suficiente, se versiona solo y el orquestador
  lo lee igual que lee el tablero.

## 8. El sistema trabaja solo (decisión D8)

Esto no es una página: es cómo funciona la fábrica, y condiciona lo que la web tiene que enseñar.

**El bucle.** El sistema no espera a que nadie le dé al botón. Encadena solo: generar en
StrategyQuant → probar con nuestro motor → descartar con motivo → reintentar lo que se queda cerca →
examinar lo que sobrevive → componer carteras. Cuando termina una vuelta, empieza la siguiente con lo
aprendido (decisión D2), no desde cero.

**Organizado, no a lo loco.** Un solo trabajo pesado a la vez por máquina y una puerta de admisión
que lo rechaza si la máquina no está en condiciones. Esa puerta ya existe
(`services/ops/gobernanza_recursos.py`) y es de obligado paso. Nada de procesos compitiendo entre
ellos, que es lo que tumbó el servidor tres veces.

**Aguanta caídas.** Tres condiciones, y las tres son medibles:
1. **Se relanza solo.** Los servicios arrancan con la máquina y se reinician si mueren.
2. **Reanuda donde estaba, no desde el principio.** Cada trabajo deja su estado en disco antes de
   empezar, así que un reinicio a mitad de una campaña de doce horas no tira doce horas.
3. **Deja rastro de la caída.** Cuándo se cayó, qué estaba haciendo y en qué punto reanudó. Sin eso
   no se puede distinguir "va lento" de "lleva seis horas muerto".

**Dónde se guarda, y por qué en dos sitios.**

| Qué | Dónde | Por qué ahí |
| :--- | :--- | :--- |
| Estrategias, candidatas, certificaciones, operaciones | Base canónica en el servidor (SQLite) | Es la fuente de verdad, es local a quien la escribe y no depende de internet. **Maestro único: no se replica ni se parte.** |
| Estado del bucle, progreso, avisos, alertas de operación, comentarios | Firebase | Es lo que Emilio consulta desde el móvil o desde cualquier sitio, y lo que permite que la web reaccione al instante sin estar dentro del servidor |
| Ficheros pesados: datos de mercado, telemetría, informes | Disco del servidor, con huella SHA-256 | No caben ni pintan nada en una base de datos |

La regla que evita el desastre clásico de tener dos verdades: **Firebase es un espejo, no un
maestro.** Lo que se escribe allí se puede reconstruir desde el servidor. Si los dos discrepan, manda
el servidor.

**Qué tiene que enseñar la web de todo esto:**
- En la portada, una línea honesta: qué está haciendo el bucle ahora y desde cuándo.
- En Sistema, el detalle: servicios vivos, última vuelta completada, cuántas caídas ha habido hoy y
  si reanudó bien.
- En Estrategias, el ritmo: cuántas se generan y cuántas sobreviven por hora, que es lo que dice si
  el bucle está produciendo o solo girando.
- Y una regla de honestidad: si el bucle lleva parado más de una hora, **la web lo dice en la
  portada**. Un sistema 24/7 que se cae en silencio es peor que uno que se sabe apagado.

**Estado hoy**: el bucle **no existe como tal**. Hay piezas sueltas (un servicio de descubrimiento,
un ciclo de mejora por cron en el servidor viejo, la puerta de admisión) pero nadie las encadena, y
lo que había apuntaba a un mercado equivocado sin producir nada. Montarlo bien es trabajo de las
fases F03 y F04 del plan, y esta especificación fija a qué tiene que parecerse cuando esté.

## 9. Preguntas abiertas (las que faltan por decidir)

Se anotan aquí según aparecen. Emilio las responde cuando quiera y entonces pasan a §2.

1. **Alertas**: ¿por dónde quiere recibirlas? ¿La web abierta, el móvil, el correo, Telegram?
2. **Cuántas cuentas de fondeo** piensa llevar a la vez, y de qué firmas. Cambia el diseño del
   Trading Desk.
3. **Riesgo por operación** y si quiere poder cambiarlo desde la web o queda fijado por estrategia.
4. **Qué hacer cuando una estrategia deja de funcionar en real**: ¿la para el sistema solo, o avisa?
5. **Histórico**: ¿quiere ver la evolución en el tiempo (cuántas certificadas por semana) o solo la
   foto de hoy?
6. **ULTRA**: cuándo se retoma y con qué señal.
