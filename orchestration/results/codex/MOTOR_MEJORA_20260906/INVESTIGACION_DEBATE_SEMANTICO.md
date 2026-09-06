# ¿Tiene sentido un debate semántico de agentes para proponer mejoras? Investigación y decisión

Fecha: 2026-09-06. Pregunta de Emilio: si conviene que agentes debatan cada estrategia en lugar de
dejar la mejora a programas con reglas fijas, y en caso afirmativo, implementarlo e integrarlo.

## Respuesta corta

Sí, para **proponer y criticar hipótesis**; no, para **medir ni aceptar**. Los programas con reglas
fijas no pueden razonar sobre una estrategia concreta (el propio proyecto lo demuestra dos veces,
ver §2), y la práctica publicada muestra que los agentes aportan cuando se les obliga a razonar
sobre evidencia real y se corrigen sus fallos conocidos (adulación, consenso vacío, minería de
datos). Por eso el diseño es: agentes ciegos entre sí que proponen, un crítico que refuta, un
árbitro que selecciona sin forzar consenso, y programas deterministas que validan cada cambio,
recalculan en SQX, comparan con criterios registrados antes y llevan la cuenta del presupuesto
de búsqueda. Implementado en `scripts/herramientas/sqx_hypothesis_debate.py` e integrado en el
ciclo (`dossier` → debate → `prepare-local --hypotheses` → `run` → `evaluate`).

## 1. Qué dice la práctica publicada (consultado 2026-09-06)

- **La adulación entre agentes degrada el debate.** Los agentes tienden a plegarse a la opinión
  ajena; forzar consenso homogeneiza posturas y pierde hechos. Se mitiga con propuestas
  independientes (ciegas), estimación explícita de la adulación y agregación por votación en vez
  de consenso obligado ([CONSENSAGENT, ACL Findings 2025](https://aclanthology.org/2025.findings-acl.1141/);
  ["Too Polite to Disagree"](https://arxiv.org/html/2604.02668v2);
  ["The Deliberative Illusion"](https://arxiv.org/pdf/2606.03032);
  ["Social Dynamics as Critical Vulnerabilities"](https://arxiv.org/pdf/2604.06091)).
- **Un solo agente bien instruido iguala a menudo a un debate**, y buena parte de la ganancia
  atribuida al debate procede de la votación ([L-MAD](https://arxiv.org/html/2607.09099);
  ["Who Flips?"](https://arxiv.org/pdf/2606.16011)). Conclusión práctica: pocas llamadas, roles
  con lentes distintas y un árbitro con reglas explícitas, no rondas interminables.
- **En investigación de estrategias, el riesgo dominante es la minería de datos.** Evaluar
  muchas hipótesis sobre datos ruidosos encuentra ganadoras por azar; los marcos de
  agentes de trading reconocen que sus hipótesis pueden ser racionalizaciones a posteriori y
  exigen declarar el presupuesto de búsqueda y congelar el plan antes de los datos de
  validación ([TradingAgents](https://arxiv.org/html/2412.20138v6);
  [Agentic Trading](https://arxiv.org/html/2605.19337v1);
  [MadEvolve](https://arxiv.org/html/2605.23007v1)).

## 2. Qué muestra el propio proyecto

- **El "debate de agentes" que ya existe en la API no piensa.** `services/api/app/validation/gates/gate_10_agent_debate.py`
  y `services/validation/registry/consejo_debate_11.py` (que alimenta `/api/v2/improvement/debate/{id}`
  y la página `/estrategias/mejora/debate`) no llaman a ningún modelo: son fórmulas sobre cuatro
  métricas y frases pregrabadas ("Ajustar multiplicador ATR de Stop Loss", "Refinar filtro de
  régimen con EMA/RSI", "Activar trailing ATR dinámico"), idénticas para cualquier estrategia.
  Es la versión más extrema de lo que Emilio rechaza y contradice la doctrina de cero datos
  falsos que la propia página proclama. Queda señalado; retirarlo o sustituirlo es una decisión
  aparte de esta fase.
- **La biblioteca fija de hipótesis de la entrega 1 produjo una hipótesis mal justificada.**
  `H_TS_TIGHT` se planificó porque una métrica (devolución de MFE) mezclaba perdedoras; con la
  métrica corregida no tenía apoyo en ambas muestras. Un programa fijo no puede detectar que su
  propia premisa es dudosa; un crítico con el dosier delante, sí.
- **El debate multiagente de agosto (normalización de fondeo) funcionó** porque cada agente
  aportó evidencia concreta y el resultado se implementó y verificó (docs/Fondeo/DEBATE_MULTIAGENTE…).

## 3. Diseño adoptado (agentes piensan, programas ejecutan)

| Paso | Quién | Qué | Guarda |
| --- | --- | --- | --- |
| Dosier | programa | contrato, diagnóstico corregido, catálogo de parámetros mutables con valores actuales, variantes ya exploradas, criterios | única fuente de cifras para los agentes |
| Propuesta | 2 agentes ciegos entre sí (lente salidas/riesgo; lente estructura/frecuencia/destino) | ≤3 hipótesis cada uno: problema con códigos de hallazgo, mecanismo, cambio en el vocabulario de mutaciones, efecto esperado por destino, criterio de aceptación, riesgos | esquema JSON obligatorio; nada fuera del vocabulario |
| Validación | programa | construye cada cambio sobre las reglas reales; marca no aplicable, nulo o ya explorado | lo que no se puede construir no se debate como ejecutable |
| Crítica | 1 agente | refuta o acepta cada propuesta: sobreajuste, muestra, mecanismo incoherente, irrelevancia para el destino | debe citar cifras del dosier |
| Arbitraje | 1 agente | ≤2 seleccionadas, mecanismos distintos, sin consenso forzado: el desacuerdo se registra | solo aplicables y no refutadas |
| Ejecución y decisión | programas | mutación verificada, recálculo en SQX, comparación emparejada, clasificación con criterios pre-registrados, registro por estrategia | el presupuesto de búsqueda (propuestas consideradas, ya probadas) queda contabilizado |

Proveedor del sistema (decisión de Emilio al cierre): el **omnirouter de su VPS de Oracle**
(`https://omniroute.143-47-35-167.sslip.io/pro/omniroute/api/v1`, API compatible con OpenAI). El
código no fija un modelo: pide los alias de tarea `ultrarentable-mejora-proponente|critico|arbitro`
y en el panel de superadmin se decide qué IA sirve cada uno; mientras no existan, cae a
`auto/best-reasoning` y lo deja anotado en el registro de la llamada. Respaldos solo para pruebas y
demostración: SDK oficial de Anthropic, `claude -p` de Claude Code desde el PC y respuestas
grabadas. Hetzner alcanza el omnirouter por HTTPS (certificado sslip no reconocido: la conexión se
degrada a no verificada dejando constancia).

## 3 bis. Lo que enseñó el primer debate real (EW, 16:17–16:23 CEST, Claude Opus 5 vía Claude Code)

- Cuatro llamadas, 342 s, 2,07 USD de uso de Claude Code. Cinco propuestas: dos del lente de
  salidas (adelantar la activación del trailing largo 1,4→0,9 ATR; objetivo largo 2,0→1,5 ATR),
  tres del lente de estructura (disparo del breakout 45→25 barras; validez de la orden larga
  4→8 barras; filtro de régimen 188→100). Ninguna era una regla de biblioteca: todas citaban
  las cifras del dosier (59 % de cierres por reloj, 7,5 %/8,9 % de objetivos, 1,1 op/semana,
  19 % de días con operación, MFE ≥1R en el 38 %/46 %).
- **El validador determinista era demasiado estricto y el debate lo puso en evidencia**: dos
  propuestas de un solo cambio quedaron "no aplicables" porque el agente repetía el periodo ATR
  sin variarlo y el programa lo contaba como cambio previsto. Corregido (los campos que no varían
  se ignoran; prueba añadida) y debate repetido con el validador corregido.
- Los agentes pidieron, con razón, que el dosier incluya los cambios concretos de las variantes ya
  exploradas y no solo su etiqueta (corregido: el registro guarda los cambios y su resultado).
- El árbitro dejó constancia de un desacuerdo útil: 5 puntos de tasa de objetivo a 5 días sobre
  52 ventanas disjuntas OOS son ~2,6 ventanas, es decir, ruido; propone leer la relevancia sobre
  ventanas disjuntas. Es una objeción legítima al criterio registrado que se traslada a la
  siguiente revisión de criterios (no se cambia en caliente).
- Carencias de capacidad señaladas por los agentes (roadmap real, no inventado): filtros de hora
  y de día de la semana, filtro o desactivación por dirección, salidas parciales, hora de cierre
  forzado (opción de proyecto, no de la estrategia) y relajar entradas. Son las palancas que el
  vocabulario actual no expresa.

## 4. Coste y límites

- Coste por debate: cuatro llamadas. Con Claude Code (suscripción) cada llamada arrastra el
  contexto del propio Claude Code (~30k tokens de caché); con el SDK y un prompt propio el
  dosier son ~7k tokens: unos céntimos por debate con Opus 5.
- Lo que el debate NO hace: no mide, no acepta, no ajusta sobre el OOS, no propone cambios
  fuera del vocabulario (filtros de horario o día, nuevas condiciones y tamaño de posición
  quedan como "capability_gaps" registradas, no como cambios forzados).
- Riesgo residual: cuantas más hipótesis se prueben por estrategia, mayor la probabilidad de
  una falsa mejora; el contador `search_budget` existe para aplicar una corrección por pruebas
  múltiples (el proyecto ya tiene `gate_08_deflated_sharpe.py`) en la validación final.
