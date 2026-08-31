# PLAN MAESTRO v4 — DE LA MALEZA A LOS MILES DE %

> **Sustituye a v3** (`archive/plan_maestro_2026-08-31_v3_motor_primero.md`).
> **Ejecutor: Hermes (Orquestador).** Antigravity queda fuera del camino crítico (decisión del
> usuario 2026-08-31, tras 5 incumplimientos de protocolo sobre 5 oportunidades).
> **Subagentes operativos desde el 2026-08-31 06:20.** La causa del fallo estaba en el PC del
> usuario: `CLAUDE_CODE_SUBAGENT_MODEL=openrouter/free` en el registro de Windows
> (`HKCU:\Environment`) y en el perfil de PowerShell, inyectada al lanzar cada sesión. Retirada y
> verificada. Reparto: **lo mecánico y verificable en un comando va a subagentes** (mapear
> imports, contar, recalcular hashes, ejecutar campañas); **el diseño del motor, los criterios de
> los gates y el modelo de fricción los hace el orquestador**, que es donde inventar cuesta dinero.
> Decisiones selladas: `DOCTRINA_ORQUESTADOR.md §14 y §15`.

---

## LA TESIS DEL PLAN (leer esto antes que las fases)

**Los miles de % no salen de encontrar una señal de entrada mágica.** No existe. Salen de esto:

```
       edge real y robusto          envolvente de balas          resultado
   (PF 1,3-1,6, verificado)   ×   (pirámide + reciclaje +   =   convexidad
    repetible, no espectacular      apalancamiento aislado)      asimétrica
```

Una estrategia con PF 1,4 y 30 % anual es aburrida. Esa misma estrategia, ejecutada con balas
sacrificables de 1R que piramidan sobre las ganadoras, reciclan el capital cosechado y toleran
80 % de DD flotante, produce colas derechas de tres cifras. **La convexidad es una propiedad de
la gestión de capital, no de la señal.**

De ahí el orden del plan, que es innegociable:

1. Primero **limpiar**, porque no se puede construir sobre 505 candidatos donde los "aprobados"
   incluyen uno con PF 0,77.
2. Después **backtest realista**, porque minar con costes irreales fabrica basura convincente.
3. Después **descubrir edges robustos** en volumen.
4. Después **doparlos con inteligencia** (semántica → programática → prueba).
5. Y solo entonces **la envolvente ULTRA**, que es donde nacen los miles de %.
6. En paralelo desde el paso 3, **FONDEO**, que es el problema inverso: no maximizar, sino
   sobrevivir a un examen en 3-8 días.

**Lo que hoy hay en el catálogo NO sirve de materia prima.** Los 15 `APPROVED_CURRENT_ENGINE`
tienen 9-120 operaciones OOS, PF entre 0,77 y 2,18, y P&L de 0 en todos los ULTRA. Pasan los 11
gates —verificado en disco— pero pasar los gates con 22 operaciones no demuestra nada.

---

## FASE 0 — LIMPIEZA DEL CÓDIGO

> Petición explícita del usuario: *"primero deberías limpiar el proyecto de ruido y dejarlo claro,
> en código y luego en front"*. Front va en la Fase 10.

### 0.1 Resolver los dos árboles de validación
Existen `services/validation/` y `services/api/app/validation/`. `gate_09` vive en el segundo.
Hay que determinar cuál está vivo (quién lo importa desde `main.py`, `mine.py` y los tests),
comparar los gates duplicados fichero a fichero, y **dejar uno solo**. El otro a `cuarentena/`.
- **Verificación:** `grep -rn "from services.*validation"` da un único árbol. Los 11 gates existen
  una sola vez. `pytest` no empeora respecto al estado actual.
- **Riesgo si no se hace:** dos pipelines de certificación distintos ⇒ una estrategia puede estar
  "certificada" por el árbol muerto. Es el fallo más grave que puede tener este repo.

### 0.2 Cuarentena de servicios muertos
`services/` tiene ~25 subdirectorios. Determinar cuáles son alcanzables desde los puntos de
entrada vivos (`services/api/app/main.py`, `scripts/mine.py`, `services/background_searcher.py`,
`tests/`). Lo no alcanzable va a `cuarentena/services_muertos/` con manifiesto SHA-256.
- **Verificación:** el árbol de imports desde los 4 puntos de entrada cubre el 100 % de lo que
  queda en `services/`. Cero borrados.

### 0.3 Una sola base de datos canónica
Hoy hay 5 ficheros de BD y **3 están vacíos** (`data/sqlite.db`, `data/candidates.db`,
`data/state.db`: 0 bytes, 0 tablas). La real es
`~/.local/state/ultrarentable/ultrarentable.sqlite3` (62 MB, 33 tablas).
- Las vacías a cuarentena. `learning_store.sqlite` (280 KB, 11 tablas): determinar si vive.
- **Verificación:** un solo `DB_PATH` en todo el código; `grep -rn "sqlite" --include=*.py` no
  apunta a ninguna ruta muerta.

### 0.4 Un solo punto de entrada de minería
`scripts/mine.py` ya consolida los 26 legacy (hecho, manifiesto 26/26 verificado). Falta cerrar:
`services/background_searcher.py` y `mine.py` no pueden ser dos caminos distintos hacia SQX.
- **Verificación:** `mine.py --dry-run` funciona en los dos tracks; el searcher lo invoca a él
  o queda documentado por qué son dos cosas distintas.

**Salida de la Fase 0:** un mapa de una página de qué es el sistema, sin ambigüedad.

---

## FASE 1 — SANEAMIENTO DEL CATÁLOGO

El catálogo tiene 505 candidatos en 10 estados distintos. Hay que separar el grano de la paja
con un criterio explícito, no heredado.

### 1.1 Criterio de "base válida para ULTRA" (se sella aquí y no se toca después)
Una estrategia solo entra al corpus base si cumple **todo**:
- **≥ 200 operaciones OOS.** Con 22 operaciones no hay estadística, hay anécdota.
- **PF OOS ≥ 1,25** con costes realistas (Fase 2).
- **Ratio OOS/IS ≥ 0,5**: si fuera de muestra rinde menos de la mitad que dentro, está sobreajustada.
- **Los 11 gates en PASSED**, con evidencia física en `data/evidence/<sid>/`.
- **DSR positivo** tras penalizar por el número de intentos de la campaña que la produjo.

### 1.2 Reclasificación
Aplicar el criterio a los 505. Los que no lo cumplan pasan a `LEGACY_NO_CERTIFICADO` —**no se
borran**, quedan como histórico. El estado `APPROVED_CURRENT_ENGINE` se vacía y se repuebla solo
con lo que sobreviva.
- **Verificación:** informe con el censo antes/después y la razón de descarte de cada uno.
- **Expectativa honesta:** es probable que sobrevivan **pocos o ninguno**. Eso no es un fracaso:
  es saber de dónde partimos de verdad.

### 1.3 Cerrar la contradicción histórica
`STATE_OF_TRUTH` declaraba 230 certificadas; la gobernanza posterior dice "NO STRATEGY IS
CERTIFIED BY ASSUMPTION". Este censo la cierra con datos.

---

## FASE 2 — MOTOR DE BACKTEST REALISTA

> **Va antes de minar, no después.** Minar con costes irreales produce estrategias preciosas que
> mueren en real, y encima consume el presupuesto de CPU del VPS.

Es la respuesta técnica al requisito del usuario: *"que se parezcan lo máximo posible cuando se
ejecuten en real"*.

### 2.1 Fricción medida, no asumida
- **Spread real por barra.** Ya lo capturo: el ingestor Dukascopy guarda `spread_mean` medido
  tick a tick en cada vela (0,50 pts en el S&P). Para cripto, spread real de BingX.
- **Ejecución asimétrica:** compras al ask, vendes al bid. El OHLC está en bid + spread guardado,
  así que se reconstruye sin inventar.
- **Latencia:** la entrada no ocurre al cierre de la vela de señal sino N ticks después,
  parametrizable y por defecto conservador.
- **Comisiones reales** por instrumento (ya en `canonical_instrument_aliases.json`).

### 2.2 Fricción específica de ULTRA
- **Funding real de BingX** (se consulta a su API, no se asume).
- **Cap de apalancamiento real por par.** No sirve asumir 500x: se pregunta al exchange cuánto da
  en ese símbolo y ese es el techo duro.
- **Precio de liquidación real** con margen aislado. Una bala que se liquida es una bala perdida,
  y el backtest tiene que verlo.

### 2.3 Fricción específica de FONDEO
- **Trailing DD intradiario**, no de cierre. Es la regla que mata las cuentas.
- Pérdida diaria, regla de consistencia, cierre obligatorio intradía.

- **Verificación de la fase:** re-ejecutar el backtest de una estrategia conocida con el motor
  viejo y el nuevo, y publicar la diferencia. **Si el P&L no baja, el motor nuevo no está
  modelando fricción de verdad.**

---

## FASE 3 — CAMPAÑA DE DESCUBRIMIENTO MASIVA

### 3.1 Datos (corre en segundo plano desde ya, no bloquea)
- Backfill Dukascopy de los proxies verificados: `USA500IDXUSD`, `USATECHIDXUSD`, `USA30IDXUSD`,
  `XAUUSD`, `XAGUSD`, `LIGHTCMDUSD` + majors forex. **`USARUSSIDXUSD` (RTY) está SIN VERIFICAR**:
  el feed devuelve el mismo tamaño para símbolos inválidos, así que no se da por bueno.
- Backfill M1 cripto (Binance Vision, ya en marcha).
- **Verificación:** conteo real de celdas con cobertura suficiente. No se declara "110 celdas"
  hasta que las 110 existan en disco con su manifiesto.

### 3.2 Cola de minería gobernada para 4 cores
El VPS tiene 4 cores y sostiene además la API y la web. Cola persistente en SQLite, 2 celdas
concurrentes, `nice`/`ionice`, reanudable tras reinicio, progreso real visible.

### 3.3 La campaña
Barrer las celdas con dos perfiles de fitness distintos:
- **ULTRA:** asimetría. Payoff alto, cola derecha, tolerancia a DD. No se busca winrate.
- **FONDEO:** consistencia. DD bajo, sin rachas, cierre intradía.

**Nada se declara certificado aquí.** Esta fase produce materia prima, y se mide por volumen de
candidatos que superan el criterio 1.1, no por lo bonitas que sean las curvas.

---

## FASE 4 — MOTOR DE MEJORA INTELIGENTE

> Requisito literal del usuario: mejora *dinámica, semántica y programática*, **sin hardcodear**
> "ATR +2" ni "subir el SL un 2 %".

### 4.1 Capa semántica — el *por qué*
El sistema no mira los parámetros: mira **las operaciones**. Agrupa las perdedoras y busca qué
comparten (hora, régimen de volatilidad, spread del momento, duración, rachas previas...).
Produce una **hipótesis sobre el mecanismo**, en lenguaje natural:
*"pierde sistemáticamente cuando entra con el spread por encima de su mediana"*.
Aquí la IA aporta hipótesis, **nunca números**.

### 4.2 Capa programática — el *qué*
Cada hipótesis se compila en un **experimento parametrizado**, jamás en una regla fija.
"Bloquea Asia" está prohibido; lo correcto es *una máscara de sesión cuyos límites se buscan*.

> **La regla de oro: la inteligencia elige la DIMENSIÓN, la búsqueda encuentra el VALOR.**

### 4.3 Capa de prueba — el *¿es real?*
Una IA dopando estrategias es una máquina de sobreajustar: si propone 200 mejoras, ~10 funcionarán
por azar. Defensas obligatorias:
- **Blind holdout intocable** durante toda la fase de hipótesis. Ni para mirar.
- **Penalización por multiplicidad** (DSR): cuantas más hipótesis, más alto el listón.
- **Walk-forward:** la mejora aguanta en varias ventanas o no existe.
- Si ninguna mejora sobrevive, se reporta `SIN MEJORA`. No se fuerza.

*(Las killzones son **una** de las dimensiones que esta capa puede proponer. El usuario pide
tenerlas en cuenta más adelante, no como fase propia.)*

---

## FASE 5 — ENVOLVENTE ULTRA: EL MOTOR DE BALAS

> **Aquí nacen los miles de %.** Todo lo anterior era para tener bases que merezcan la pena.

Parámetros sellados: DD realizado **70 %** · flotante **80 %** · apalancamiento **hasta 500x**
gestionado por IA con cap real del exchange · dimensionamiento **100 % en porcentajes** ·
arranque **100 % paper**.

- **Máquina de estados de la bala:** INICIO → CONFIRMACIÓN → CRECIMIENTO → COSECHA → PROTECCIÓN →
  CIERRE. Todo en % del capital, nunca en cifras absolutas.
- **Piramidación free-risk:** se añade sobre ganadoras, break-even tras +1,5R.
- **Extensión a swing (decisión #24):** una operación intradía que va favorable **puede**
  mantenerse más allá del cierre de sesión y convertirse en swing (`1D`). El umbral de "va
  favorable" lo encuentra la optimización — **jamás una constante hardcodeada**. Exige modelar
  gaps de apertura y riesgo overnight en el backtest. En FONDEO esta extensión está PROHIBIDA.
- **Reciclaje:** el capital de balas cerradas realimenta balas nuevas.
- **Autoinversión de margen flotante:** la ganancia no realizada financia exposición adicional,
  con la liquidación real como límite duro.
- **Bóveda ratchet:** 50-85 % de lo cosechado sale a spot y **no vuelve a entrar jamás**.
- **Gestor dinámico de apalancamiento:** decide el multiplicador por operación según régimen,
  volatilidad y estado de la bala, con techo en el máximo real del par.

**Verificación, y es la fase más importante de todo el plan:**
- Backtest de la envolvente sobre las bases de la Fase 4, con la fricción de la Fase 2.
- Reportar la **distribución completa** de resultados, no la media: mediana, percentil 5,
  percentil 95, y **probabilidad de ruina**. Un sistema que da 3.000 % de media con 40 % de
  probabilidad de perderlo todo hay que decirlo así.
- **Si ninguna base alcanza el objetivo, se reporta la cifra real alcanzada.** Ajustar costes,
  datos o gates para llegar al número es violación grave de la doctrina.

---

## FASE 6 — META-ESTRATEGIAS ULTRA: EL ROUTER

Que un conjunto funcione **como una sola estrategia**, con router dinámico multi-activo y debate
IA, **sin reglas hardcodeadas**.

- Decide asignación por ventana según: régimen detectado, correlación viva entre componentes y
  estado de cada bala.
- **Debate IA:** varios agentes proponen asignación y se critican; la decisión **y su
  razonamiento** quedan persistidos y son auditables a posteriori.
- **Criterio de éxito duro:** la curva del router debe batir a la media de sus componentes en
  winrate **y** en drawdown. Si no lo hace, se declara fracaso explícito y se descarta.
- El router **nunca** puede saltarse los límites 70 %/80 %.

---

## FASE 7 — FONDEO: PASAR EXÁMENES EN 3-8 DÍAS

El problema inverso al de ULTRA: no maximizar, **sobrevivir a un examen**.

- **Simulador exacto de reglas prop:** trailing DD intradiario, pérdida diaria, consistencia,
  cierre obligatorio.
- **Optimizador:** maximizar `P(pasar en ≤ 8 días)` sujeto a `P(violación) < umbral`. La
  distribución se obtiene por Monte Carlo **remuestreando operaciones reales del backtest**,
  nunca retornos sintéticos.
- **Meta-fondeo:** combinar estrategias poco correlacionadas para bajar la varianza del examen.
  En fondeo, la varianza mata más que la media baja.
- **Salida:** ranking con días esperados hasta pasar y probabilidad de quiebre por estrategia.
- Export a **PickMyTrade + Tradovate** (ya configurado, esperando estrategias).
- La gestión de cuentas prop sigue **pospuesta** (decisión #10).

---

## FASE 8 — VERIFICACIÓN END-TO-END Y PAPER

- ULTRA en paper BingX con el motor de balas real; FONDEO en demo Tradovate.
- **Reconciliación paper vs backtest:** los fills reales vuelven al sistema y se mide la
  divergencia contra lo que el backtest predijo. **Esto es lo único que demuestra que el backtest
  se parece al real.** No se garantiza a priori: se mide y se realimenta.
- Estrategia que diverja por encima del umbral ⇒ se marca y sale de producción.
- **Ni un euro real sin autorización explícita del usuario.**

---

## FASE 9 — FRONT LIMPIO

> *"y luego en front"*.

- Consolidar las 33 páginas actuales en **páginas maestras con subpáginas jerarquizadas**.
- Cero datos inventados: si no hay dato, `SIN DATOS`, nunca un valor de relleno.
- Landing sin autenticar; acceso solo para autorizados por `josferestudio@gmail.com`.
- Firebase se mantiene en PECEMI de momento, pero el `apiKey` sale del código a variable de
  entorno con fallo explícito si falta.
- Trading desk (BingX para ULTRA, gestión de cuentas para FONDEO) **al final**, cuando haya
  algo real que mostrar.

---

## LO QUE PUEDE SALIR MAL (y cómo se detecta)

| Riesgo | Cómo se detecta | Qué se hace |
| :--- | :--- | :--- |
| Ninguna base supera el criterio 1.1 | Censo de la Fase 1 | Ampliar la campaña, no relajar el criterio |
| El motor realista mata todas las estrategias | El P&L cae a negativo en Fase 2 | Es la respuesta correcta: eran ilusiones |
| El motor de mejora sobreajusta | El holdout ciego no confirma | La mejora se descarta, se reporta `SIN MEJORA` |
| La envolvente da miles de % con ruina alta | Percentil 5 y prob. de ruina en Fase 5 | Se presentan ambos números, decide el usuario |
| Paper diverge del backtest | Reconciliación de la Fase 8 | Se corrige el modelo de fricción, no el backtest |
| 4 cores no dan abasto | Cola de la Fase 3 se atasca | Reducir matriz o ampliar VPS, decide el usuario |

---

## REGLAS INVARIANTES

1. **REAL-ONLY.** Cero datos inventados. Sin dato ⇒ `NO DATA`/`ERROR`, nunca un valor por defecto.
2. **Nunca `rm`.** Todo lo retirado va a `cuarentena/` con manifiesto SHA-256.
3. **Se trabaja en la carpeta, no en GitHub.** Nada se sube sin orden expresa (decisión #23).
4. **Nada valioso vive solo en RAM.** Toda población se persiste a disco y BD inmediatamente.
5. **El objetivo no autoriza a maquillar.** Si el número real es peor que la meta, se reporta el
   número real.
