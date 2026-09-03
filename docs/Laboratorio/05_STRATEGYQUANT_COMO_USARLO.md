# Cómo se usa StrategyQuant X, y en qué nos estábamos equivocando

> Investigación del orquestador, 2026-09-04. Emilio: *"tienes que hacer una deep research de cómo
> usar SQX... qué porcentaje de CPU darle, en qué manera utilizar la cola para hacer estrategias.
> No puedes hacerlo a lo bruto, tienes que aprender primero"*.
>
> **Cómo leer este documento:** lo que viene de la documentación oficial y de los foros de
> StrategyQuant va marcado como **[fuente]**; lo medido en nuestra instalación, como **[medido]**.
> Nada aquí es suposición mía sin marcar.

---

## 1. El proceso que ellos recomiendan, y el que hacemos nosotros

**[fuente]** El proceso oficial de construcción va de mucho a muy poco, en seis pasos:

| Paso | Qué hace | Cuántas sobreviven |
| :--- | :--- | ---: |
| **Generación** | Evolución genética: población 200, 30 generaciones. Mínimo **100 operaciones**, retorno/caída **> 3**, beneficio mínimo **2.000 $** | **2.000** |
| **Filtro 1** | Beneficio fuera de muestra > 500 $ | ~1.500 |
| **Filtro 2** | Retest a precisión de 1 minuto sobre datos nuevos, mismo umbral | menos |
| **Filtro 3** | **Prueba en otros mercados** | **5 – 15** |
| **Filtro 4** | Robustez: al menos **20 simulaciones**, se juzga al 95 % de confianza | **1 – 3** |
| **Filtro 5** | Matriz walk-forward con distintos periodos de reoptimización | las finalistas |

**[medido] Lo que hacemos nosotros:**

| | Ellos | Nosotros |
| :--- | :--- | :--- |
| Estrategias por celda | 2.000 | **20.000** (tope del banco) |
| Mínimo de operaciones | **100** | 44 en 4 horas (1/mes × 3,7 años) |
| Retorno/caída mínimo | **3** | **0,5** |
| Beneficio mínimo | **2.000 $** | **ninguno** |
| Filtros posteriores | **cinco** | **ninguno** |
| Finalistas | 1 – 3 | 46.537 artefactos, **0 finalistas** |

**El embudo está invertido.** Generamos diez veces más con filtros seis veces más flojos, y luego no
filtramos. Por eso tenemos decenas de miles de estrategias y ninguna certificada.

## 2. La frase que más nos afecta

**[fuente]** *"La evolución genética debería poder mejorar cualquier población de estrategias, así
que no seas demasiado estricto con tu generación inicial; **el único filtro recomendado es el número
de operaciones**"*.

Esto encaja con lo que Emilio pidió (*"no te pongas tan exquisito con los filtros en SQX"*) **pero
matiza cuál**: el que hay que exigir es **operaciones**, no factor de beneficio ni retorno/caída. Hoy
tenemos los tres flojos y el de operaciones es el más flojo de todos en los marcos lentos (1 al mes
en 4 horas, frente a las 100 totales que ellos piden).

## 3. Aleatoria contra genética, y cómo se encadenan

**[fuente]**

- **Generación aleatoria**: crea y evalúa sin parar hasta que se la para. Más rápida, explora más
  ancho y **tiene menos riesgo de sobreajuste** porque no refina nada. *"Si la dejas correr unos
  días puede generar y evaluar millones de estrategias"*.
- **Evolución genética**: parte de candidatas aleatorias y las mejora por generaciones. Más lenta,
  **más riesgo de sobreajuste**, y puede estancarse si no se vigila.
- **Recomendación oficial**: **empezar ancho con aleatoria y luego estrechar con genética** usando
  las mejores como población inicial. Eso son dos tareas encadenadas dentro del mismo proyecto.
- **[fuente]** *"No suele aportar mucho usar demasiadas generaciones; es mejor reiniciar la
  evolución y empezar de cero"*.

**[medido] Nuestros proyectos usan `genetic-evolution` con `PopulationSize 100` y `MaxGenerations
100`.** Es decir: la modalidad más lenta y más propensa a sobreajuste, con **cien** generaciones
cuando la recomendación son **treinta** y la advertencia es que pasarse no aporta.

## 4. CPU, hilos y memoria

**[fuente]**

- Los hilos se configuran en **Tools / Performance**. Con procesadores Intel de núcleos P y E hay una
  opción para usar todos.
- **La CPU es lo que más pesa** en la velocidad de generación y backtest: más núcleos, más rápido.
- Java y Windows limitan a **64 núcleos por socket**; para máquinas muy grandes la vía es **lanzar
  varias instancias** de StrategyQuant.
- Un usuario con 24 hilos reportó **10-15 % de uso de CPU** aun poniendo los hilos al máximo: la
  utilización no sube sola.
- Memoria esperada: **~70 % de la RAM durante la construcción** y hasta **90-95 % en walk-forward**.
- Hardware recomendado: mínimo 8 GB y 4 núcleos; **óptimo 32 GB y 8 núcleos**; avanzado 64 GB y 20+.

**[medido] Nuestro servidor Hetzner:**

```
8 núcleos · 62 GB de RAM
sqcli usando 507 % de CPU (≈5 de los 8 núcleos) y 17,7 GB (27 % de la RAM)
carga media sostenida: 7,2 – 7,6 de 8
settings.xml NO define hilos ni memoria: usa los valores por defecto
```

**Conclusión:** estamos en el punto "óptimo" de su tabla (8 núcleos, y RAM de sobra), la CPU sí se
está aprovechando (5 de 8 núcleos por el proceso, carga total 7,5), pero **la memoria está
infrautilizada**: usamos el 27 % cuando ellos esperan el 70 % durante la construcción. Y **no hemos
configurado nada**: ni hilos ni memoria máxima. Ahí hay margen sin comprar nada.

## 5. Las trampas que ya hemos pagado

**[medido]** Cuatro cosas que descubrimos a base de golpes el 2026-09-03:

| Trampa | Qué pasa de verdad | Qué costó |
| :--- | :--- | :--- |
| `-project action=loadconfig` | **No sobrescribe: crea un proyecto duplicado con sufijo** (`FONDEO_MGC_M1(6)`) y responde "Project loaded" igual | 91 proyectos basura y 5 horas con los umbrales viejos |
| Volcar un banco a ficheros | **No es `synctofiles`, es `-databank action=save … folder=<ruta>`** | 40 minutos y darlo por imposible |
| La plantilla del proyecto | Trae **once tareas**: el constructor y **nueve pruebas de robustez** que nuestro generador tiraba | Meses usando una décima parte del programa |
| Generar una sola celda | **Reescribe el manifiesto entero con esa celda** | El bucle trabajó 25 minutos sobre 1 celda de 30, sin ninguna alarma |

**La regla que queda: un mensaje de éxito no es una comprobación.** Después de cada acción hay que
medir el efecto —contar ficheros, releer la configuración del proyecto— porque este programa dice
"hecho" cuando no ha hecho nada.

## 6. Lo que habría que cambiar, en orden de impacto

1. **Poner los cinco filtros posteriores**, que hoy no existen. Ahí está la diferencia entre 46.537
   artefactos y 1-3 finalistas. Las nueve pruebas de la plantilla (Monte Carlo, walk-forward,
   aleatorización, deslizamiento, diferencial, retest en otros mercados) son exactamente los filtros
   3, 4 y 5 del proceso oficial, y las tenemos ahí sin usar.
2. **Exigir número de operaciones de verdad**: 100 mínimas por estrategia, no 44.
3. **Bajar generaciones de 100 a 30** y reiniciar en vez de alargar, que es lo que recomiendan.
4. **Probar generación aleatoria** para la fase ancha: es más rápida y sobreajusta menos.
5. **Configurar hilos y memoria**, que hoy están por defecto, y ver si sube el caudal.

## Fuentes

- [Documentación de StrategyQuant](https://strategyquant.com/doc/)
- [Different build modes](https://strategyquant.com/doc/strategyquant/different-build-modes/)
- [Strategy Building Process (forex)](https://strategyquant.com/blog/strategy-building-process-forex/)
- [Efficient Memory Management and fixing stability issues](https://strategyquant.com/blog/efficient-memory-management-and-fixing-stability-issues-for-strategyquant-x-sqx/)
- [Foro: CPU Utilization](https://strategyquant.com/forum/topic/5010-cpu-utilization/)
- [Foro: Best settings for Genetic Evolution](https://strategyquant.com/forum/topic/best-settings-for-genetic-evolution/)
- [Starting StrategyQuantX with more memory](https://strategyquant.com/doc/strategyquant/starting-sq-with-more-memory)
