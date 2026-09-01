# FORENSE DE TELEMETRÍA — el "20/20 sin_ventaja" no dice lo que creíamos (2026-09-01)

> Autor: ORQUESTADOR LOCAL (Opus 5), ciclo 1 de la era local. Territorio `reviews/` (ORQ).
> Método: re-verificación con comandos propios, sin fiarse de ningún documento del repo —
> incluidos el `TRASPASO_A_OPUS`, `current_phase.md` y la `EVALUACION_ULTRARENTABLE` externa.
> **Toda cifra de aquí se ha reproducido en este PC.** Lo que no se ha podido reproducir se
> declara como tal.

## 0. Resumen en tres líneas

La única telemetría de embudo persistida (`embudo_FONDEO_ES_4h_arquetipos_20260901T101102Z.json`)
evaluó **20 de las 420 configuraciones** del perfil `arquetipos`, y esas 20 son **todas de la
misma familia (`REVERSION_ATR`)**, porque `mine.py` trunca el espacio de búsqueda por **prefijo**
con `--max-candidates`, que vale **20 por defecto**. Por tanto **NO es evidencia de que "los
arquetipos no tienen ventaja"**: es evidencia sobre UNA familia, en un timeframe (4h) para el
que las dos familias nuevas ni siquiera fueron diseñadas, y sobre el dataset Yahoo 4h ya
declarado contaminado. La afirmación que `current_phase.md` §3 y la evaluación externa elevan a
"la pregunta que puede invalidar el plan" **queda REFUTADA tal como está formulada**.

## 1. Afirmaciones previas examinadas

| # | Afirmación previa | Fuente | Veredicto |
| :-- | :--- | :--- | :--- |
| A1 | "La última telemetría (ES 4h, 2026-09-01): 20/20 mueren por sin_ventaja, 0 por falta de operaciones" | `EVALUACION_ULTRARENTABLE_2026-09-01.md` §1.2 | **CONFIRMADA en el dato, REFUTADA en la conclusión** — el dato es correcto, pero las 20 son de una sola familia (§2) |
| A2 | "los 6 arquetipos nuevos (ORB, VWAP_REVERSION, etc.) tampoco han pasado aún" | `EVALUACION` §3.2 | **REFUTADA**: ORB y VWAP_REVERSION **no se han ejecutado nunca** en esa telemetría — quedan fuera del prefijo truncado |
| A3 | "casi ninguna combinación de EMA-cross / RSI / ATR alcanza un PF de 1,05 en su propia muestra de entrenamiento" | `current_phase.md` §3 | **NO VERIFICABLE hoy**: se apoya en celdas 1h de `cola_mineria.jsonl` cuyo embudo completo nunca se persistió (la telemetría aún no existía) |
| A4 | "la telemetría del embudo se calcula y se tira" | `current_phase.md` §3 | **CONFIRMADA para las campañas históricas**; corregido en `7b7e7311e` — pero la telemetría nueva tiene el hueco del §4 |
| A5 | "un sistema sin ventaja da PF ~0,8-1,0 con fricción honesta" (implícito en el censo) | `verificacion_f02_5.17.0.json` | **CONFIRMADA**: las celdas champions de BTCUSDT 4h dan PF 0,97 / 0,97 / 0,82. Contrasta con los PF 0,03-0,19 del embudo ES 4h (§3b) |

## 2. La prueba: las 20 configuraciones son todas REVERSION_ATR

`scripts/mine.py:1285-1289` define el límite y `scripts/mine.py:852-854` lo aplica:

```python
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=20,
        help="Límite máximo de configuraciones a evaluar (default: 20)",
    )
...
    search_space = build_candidate_search_configs(track_norm, sym_norm, tf_norm, profile)
    if max_candidates > 0:
        search_space = search_space[:max_candidates]
```

El recorte es un **prefijo sobre el orden de generación**, no un muestreo. Y el perfil
`arquetipos` emite primero, entera, la familia `REVERSION_ATR`. Reproducido en este PC
(`.venv/Scripts/python.exe`, motor 5.17.0):

```
--- ES 4h perfil arquetipos: 420 configs
   familias: {'REVERSION_ATR': 108, 'SQUEEZE_BREAKOUT': 96, 'SESSION_MOMENTUM': 72,
              'STREAK_EDGE': 72, 'OPENING_RANGE_BREAKOUT': 36, 'VWAP_REVERSION': 36}
   PRIMERAS 20 (las que evaluó la telemetría):
    {'REVERSION_ATR': 20}
```

Idéntico en 5m y en 15m. Es decir: **cualquier invocación de `mine.py` sin `--max-candidates`
explícito prueba solo `REVERSION_ATR` y nunca llega a las otras cinco familias**, incluidas las
dos que se construyeron expresamente para FONDEO en la release 5.17.0.

Cobertura real de esa telemetría: **20/420 = 4,8 % del espacio, 1 de 6 familias.**

Nota adicional: las familias `OPENING_RANGE_BREAKOUT` y `VWAP_REVERSION` están documentadas en el
propio código (`scripts/mine.py:416-423`) como diseñadas para **futuros intradía de índice en
5m/15m**, ancladas a la sesión RTH 13:30-20:00 UTC. Ejecutarlas en 4h no es su caso de uso: en
velas de 4 horas el "rango de los primeros 15/30/60 minutos" no es representable. Aunque el
prefijo no las hubiera excluido, la celda 4h no habría sido una prueba justa de esas dos familias.

## 3. Dos anomalías secundarias: una descartada, otra abierta

**(a) DESCARTADA — "hay configuraciones duplicadas".** En el embudo, siete configuraciones
comparten `trades=24 pf=0.180` exactos. No es un bug: dentro de una familia, `risk_pct`
(0,005 / 0,01 / 0,02 / 0,04) escala el tamaño de posición pero **no cambia ni el número de
operaciones ni el profit factor** (PF es un cociente de brutos). Verificado además que las 420
configuraciones son criptográficamente distintas entre sí (420 firmas únicas de 420). Sin
hallazgo.

**(b) ABIERTA — un PF de 0,03 a 0,19 es anormalmente bajo.** Los 20 resultados van de `pf=0.000`
a `pf=0.190`. Un sistema sin ventaja, tras fricción honesta, aterriza cerca de 0,8-1,0 — es justo
lo que dan las celdas de referencia del propio motor (0,97 / 0,97 / 0,82). Un PF de 0,04 significa
que las ganancias brutas son el 4 % de las pérdidas brutas: eso no es "no hay ventaja", es "algo
está sistemáticamente al revés" (asimetría SL/TP invertida, TP dinámico inalcanzable, o coste
desproporcionado sobre MES). **No se puede cerrar hoy**: exige re-ejecutar el backtest, y ese
dataset no existe en esta copia (§5). Queda como experimento E1 (§6).

## 4. El defecto de diseño que esto destapa (más importante que el caso concreto)

La telemetría del embudo registra `configuraciones_evaluadas: 20` pero **no registra**:
`max_candidates`, el tamaño total del espacio de búsqueda, ni **qué familias** cubrió la muestra.

Sin esos tres campos, un embudo es indiagnosticable en el mismo sentido que denunciaba
`current_phase.md` §3: dice "20/20 sin_ventaja" sin decir "de una familia de seis". Y engancha
directamente con una **regla de decisión PRE-SELLADA** de `PLAN_LOCAL_FONDEO.md` W2:

> "Celda con ≥80 % de muertes IS por `sin_ventaja` (con ≥50k barras) ⇒ familia agotada en esa
> celda: no se re-barre con más configs; pasa a W3 (edge nuevo)."

Aplicada sobre un embudo truncado por prefijo, esa regla **declararía "familia agotada" y
abandonaría la celda habiendo probado una sola de las seis familias**. Es un fallo de plan, no
solo de código: la regla y el instrumento que la alimenta son incompatibles tal como están.

## 5. Estado de la verificación de identidad del motor (W0.2) — BLOQUEADA, no fallida

`scripts/verificacion_f02.py` ejecutado en este PC con el motor 5.17.0:

```
Baseline motor 5.17.0: orchestration/results/verificacion_f02_5.17.0.json
   ultra  BTCUSDT  4h -> SIN DATOS
   ultra  ETHUSDT  4h -> SIN DATOS
   ultra LINKUSDT  1h -> SIN DATOS
  fondeo       ES  4h -> SIN DATOS
  fondeo       GC  4h -> SIN DATOS
```

Las 5 celdas (15 configuraciones) salen `SIN DATOS`: en esta copia solo hay **manifiestos**
(`data/` son 4,4 MB de JSON), no velas. **W0.2 no ha fallado: no ha podido ejecutarse.** El
veredicto "15/15 idénticas o STOP" sigue pendiente y ninguna campaña local es válida hasta que se
resuelva. La recuperación de datos está despachada (agente AG-D).

### 5.1 Defecto encontrado al ejecutarlo: el script destruye su propio baseline

`verificacion_f02.py` escribe **siempre** en `orchestration/results/verificacion_f02_<version>.json`,
que para la versión vigente **es el fichero de referencia sellado**. Al ejecutarlo sin datos,
sobrescribió el baseline de 5.17.0 (6.553 bytes, 15 celdas) con un fichero de 678 bytes y cinco
`SIN DATOS`. Es decir: **una ejecución fallida borra la referencia contra la que compara la regla
#26**. Recuperado desde git (`git restore`); la salida mala quedó en
`cuarentena/verificacion_f02_sobrescritura_2026-09-01/` con manifiesto SHA-256, según doctrina
(nunca `rm`). Baseline restaurado y verificado:

```
-rw-r--r-- 1 yo 197609 6553 orchestration/results/verificacion_f02_5.17.0.json
c1c3a7bbff230922302d8ff42d47cf73e58ff2a912a97fa685198e714ffe15c8
celdas: 15 · generado 2026-09-01T09:26:12Z
```

Riesgo real: si esto ocurre con el árbol sucio, la referencia se pierde sin aviso.
Corrección requerida (W4.6, §6).

## 6. Decisiones y trabajo que esto genera

| id | Acción | Dueño | Por qué |
| :-- | :--- | :--- | :--- |
| **D1** | La regla pre-sellada de "familia agotada" (W2) **queda suspendida** hasta que el embudo registre cobertura por familia. Una celda solo puede declararse agotada con las **6 familias** representadas | ORQ (aplicado en `PLAN_LOCAL_FONDEO.md` W2) | §4 |
| **D2** | Toda campaña se lanza con `--max-candidates 0` (espacio completo) o con muestreo **estratificado por familia**; nunca con el default 20 | ORQ | §2 |
| **W2.6** | La telemetría del embudo debe persistir `max_candidates`, `espacio_total` e histograma de familias evaluadas y muertas | SUB (código) | §4 |
| **W4.6** | `verificacion_f02.py`: no sobrescribir un baseline existente de la misma versión sin `--force`; salida por `--out`; y **abortar con error explícito** si alguna celda sale `SIN DATOS` (hoy escribe un JSON "válido" con el motor sin verificar) | SUB (código) | §5.1 |
| **E1** | Re-ejecutar las 20 configs `REVERSION_ATR` de ES sobre el consolidado Dukascopy 5m/15m y comparar el PF con el 0,03-0,19 de Yahoo 4h. Distingue "familia mala" de "dataset contaminado" de "bug de coste" | ORQ, al aterrizar AG-D | §3b |
| **E2** | Primera campaña ES 5m/15m con las **6 familias** completas y telemetría con cobertura. Solo entonces la pregunta "¿dato o edge?" tiene respuesta | ORQ + NOHUP | §0 |

## 6.b RESULTADO DE E1 (ejecutado el mismo día, 17:14-17:21 UTC) — la fricción, no la señal

Re-ejecutadas **las mismas 20 configuraciones `REVERSION_ATR`** sobre el consolidado Dukascopy de
ES 5m (`--dataset-source dukascopy` explícito, `FUENTE=DUKASCOPY` confirmado en el log), con
IS = 150.005 barras en vez de 2.228. Coste: 7,5 min para 20 configs ≈ **22 s/config**.

| | Yahoo 4h (contaminado) | Dukascopy 5m (limpio) |
| :--- | ---: | ---: |
| barras IS | 2.228 | **150.005** |
| operaciones (mín/mediana/máx) | 5 / 17 / 24 | **1.341 / 1.990 / 2.323** |
| PF (mín/mediana/máx) | 0,000 / **0,170** / 0,190 | 0,470 / **0,535** / 0,610 |
| causa IS | 20/20 `sin_ventaja` | 20/20 `sin_ventaja` |

Dos lecturas, ambas importantes:

1. **El PF sube de 0,17 a 0,535 solo por cambiar el dato.** Buena parte del "desastre" de la
   telemetría vieja era el dataset, no la familia. Confirma que el 4h de Yahoo no servía para
   concluir nada.
2. **Pero 0,535 con ~2.000 operaciones sigue sin ser "sin ventaja normal".** La referencia del
   propio motor para un sistema sin ventaja con fricción honesta es 0,82-0,98. Con esa muestra,
   0,535 no es ruido: es una señal sistemáticamente perdedora... **o una señal neutra a la que la
   fricción se come entera.**

### La fila que faltaba: coste por operación de MES, medido

El análisis previo `results/analisis_tf_coste_vs_trades.md` (2026-08-31) concluía que **15m es el
único TF que satisface las dos restricciones a la vez**, pero su tabla es de CRIPTO (fricción en
% del precio). En futuros CME la comisión es un **importe FIJO por contrato**, así que al bajar de
timeframe castiga mucho más. Calculado ahora sobre nuestros datos reales de ES:

```
Coste round-trip MES: comision 1,00 pt + spread 0,25 + slippage 0,50 = 1,75 puntos de indice
   (comision medida del propio motor: 250 USD / 50 operaciones = 5,00 USD RT; MES = 5 USD/punto)

TF      barras   ATR14 mediano   coste/ATR   TP de 4·ATR: % que sobrevive
5m      250009           2,710       64,6%                         83,9%
15m      83377           5,053       34,6%                         91,3%
```

MES en 5m (**64,6 %**) cae justo en el mismo rango que BTCUSDT 5m (72,8 %) y XRPUSDT 5m (65,9 %)
del análisis anterior — los TF que aquel documento ya declaraba inviables. En 15m baja a 34,6 %,
equivalente a los que sí pasaban.

**Modelo que reproduce el número observado**: con ganancia media ≈ pérdida media ≈ 2·ATR y acierto
del 50 % (PF bruto = 1,00), restar 1,75 pts (0,65 ATR) a cada operación deja
`(2,00−0,65)/(2,00+0,65) = 0,51`. El PF medido es **0,535**. La coincidencia es notable y sostiene
la hipótesis de **dominación por coste**, no de señal catastrófica.

> **Cuidado con lo que esto NO demuestra.** El modelo es consistente con lo observado, no lo
> prueba: no se ha medido el PF BRUTO. Podría ser que la señal sea además mala. La medición que
> lo zanja está abajo (W2.7) y es barata.

### Lo que se decide con esto

| id | Decisión | Fundamento |
| :-- | :--- | :--- |
| **D3** | **La campaña ES prioriza 15m sobre 5m.** 5m no se abandona (se ejecuta para tener la evidencia), pero deja de ser el caballo ganador. El presupuesto de operaciones en 15m sigue siendo holgado: 16.675 barras OOS ⇒ 200 operaciones exigen 1 cada 83 barras | coste/ATR 34,6 % vs 64,6 % |
| **W2.7** | **La telemetría debe registrar PF BRUTO y PF NETO** (y coste total) por configuración. Sin eso, la etiqueta `sin_ventaja` mezcla dos diagnósticos opuestos —"la señal no vale" y "la señal vale pero se la come el coste"— que llevan a acciones contrarias: uno manda cambiar de familia (W3), el otro manda cambiar de timeframe o de fricción | E1 |
| **D4** | La etiqueta `sin_ventaja` **no se usará como prueba de "familia agotada"** hasta que W2.7 exista. Suspendida junto con D1 | ídem |

Esto reordena la conclusión del análisis externo. Su tesis —*"con las familias de reglas actuales
el edge no aparece ni con datos perfectos"*— sigue sin refutarse, pero **tampoco está demostrada**:
la única medición profunda que tenemos es compatible con una señal neutra ahogada por la fricción
de operar a 5 minutos un contrato con comisión fija.

## 7. Lo que queda abierto, sin disimular

- No se ha demostrado que las familias **sí** tengan ventaja. Se ha demostrado que **la evidencia
  que decía que no la tienen no lo demuestra**. Son cosas distintas, y la segunda no consuela: el
  0 certificadas sigue intacto.
- A3 (las celdas 1h con 348 configs) no se puede re-verificar: esos embudos nunca se guardaron. Se
  regenerará con la campaña E2; no se discute con el histórico.
- El PF 0,03-0,19 (§3b) puede seguir siendo real y malo. Hasta E1 es una anomalía, no un bug.
