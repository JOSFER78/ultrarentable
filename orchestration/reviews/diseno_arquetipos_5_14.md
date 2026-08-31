# DISEÑO 5.14.0 — Ampliación de familias de arquetipos (F03.3)

**Autor:** Hermes (orquestador) · **Fecha:** 2026-08-31 · **Estado:** DISEÑO CERRADO, implementación
tras terminar la campaña 15m (para no mezclar versiones de motor en celdas en vuelo).

## Por qué

Evidencia de las dos campañas con motor honesto (5.11.0/5.13.0):
- 4h/1h: los cruces EMA producen 15-120 trades OOS — nunca llegan a los ≥200 del criterio 1.1.
- 15m: TODAS las configs mueren en IS (PF<1,05) — el coste por operación domina al arquetipo
  (BTCUSDT 15m: embudo {'IS': 2000}).
- SQX rechaza 4.193/4.193 en su propio Build y aparca 2.035 en ToImprove (inventario en curso).

**Conclusión: la familia de señales está agotada, no los datos ni el criterio.** La expansión
es de ARQUETIPOS, con la regla de oro de F04: la inteligencia elige la DIMENSIÓN, la búsqueda
encuentra el VALOR (cero constantes mágicas hardcodeadas).

## Las 4 familias nuevas (todas como EVENTO, sin lookahead, vía `pending_entry`)

### A. `reversion_atr` — reversión a la media con bandas ATR
- Señal LONG: el cierre estuvo ≥ `banda_atr_mult`×ATR POR DEBAJO de la EMA(`ema_ancla`) en la
  vela previa Y la vela actual cierra de vuelta por encima de ese nivel de banda (evento de
  re-entrada, no estado). SHORT simétrico.
- TP natural: la propia EMA ancla (target amplio relativo al coste). SL: `sl_atr_mult`×ATR.
- Dimensiones de búsqueda: `ema_ancla` {20,50,100}, `banda_atr_mult` {1.5,2.0,3.0},
  `sl_atr_mult`, `risk_pct` (fracción canónica).

### B. `squeeze_breakout` — compresión de volatilidad → ruptura
- Estado de squeeze: ATR(14) actual ≤ percentil `squeeze_pct` {20,30} del ATR en ventana
  `squeeze_lookback` {50,100}. Señal: PRIMERA ruptura Donchian(`breakout_lookback` {10,20})
  ocurrida DURANTE squeeze (evento: vela previa sin ruptura, actual con ruptura y squeeze activo).
- Filtra los cruces en rango lateral que hoy mueren en fricción.

### C. `session_momentum` — momentum de sesión anclado
- Ancla: dirección del tramo inicial del día UTC (primeras `ancla_horas` {1,2,4} horas).
- Señal: pullback a EMA(`ema_pull` {20,50}) en la dirección del ancla y giro (evento: cruce de
  vuelta del cierre sobre la EMA en dirección del ancla). Solo una entrada por día y dirección.
- Usa la infraestructura `session_window`/`_is_session_end` existente; cierre EOD opcional
  como dimensión (`cierre_eod` {sí,no}) — en FONDEO siempre sí (decisión #24).

### D. `streak_edge` — persistencia de rachas
- Señal: `n_racha` {3,4,5} cierres consecutivos en la misma dirección → entrada en la apertura
  siguiente con `modo` {continuación, reversión} COMO DIMENSIÓN DE BÚSQUEDA (no se presupone
  cuál funciona: lo decide la evidencia por celda).
- SL/TP en múltiplos ATR como el resto.

## Reglas de implementación

1. **Aditivo estricto:** las familias existentes (cruce EMA, RSI, Donchian puro) NO cambian ni
   una línea de su semántica. Un snapshot antiguo produce EXACTAMENTE las mismas operaciones en
   5.14.0 que en 5.13.0 (verificable con `verificacion_f02.py --comparar 5.13.0 5.14.0`: las 15
   celdas de referencia deben salir IDÉNTICAS — es el criterio de aceptación de la release).
2. El generador (`ultra_discovery`/`funding_discovery`) etiqueta el arquetipo en el snapshot de
   forma que el intérprete lo despache limpiamente (campo/condición explícita, no inferencia
   frágil por nombres de indicador).
3. `build_candidate_search_configs` (mine.py) añade las 4 familias al perfil `amplio` con las
   rejillas de arriba, y un perfil nuevo `arquetipos` que mina SOLO las familias nuevas (para
   re-campaña sin re-evaluar lo ya barrido).
4. Todo en fracción canónica de riesgo; latencia y fricción heredadas del motor sin tocar.
5. Regla #26: bump a 5.14.0 con nota "aditivo: no invalida certificaciones 5.13.0" (no las hay:
   0 certificadas). VERSION_HISTORY + manifiesto + pin de test.

## Secuencia

1. Esperar fin de campaña 15m (9 celdas, motor 5.13.0).
2. Implementar 5.14.0 (agente, con esta spec) + verificación de identidad 5.13.0→5.14.0.
3. Re-campaña perfil `arquetipos`: cripto 15m y 4h (las celdas con datos profundos).
4. Censo 1.1 sobre el resultado. Si sobreviven bases → F04/F05/F06; FONDEO al llegar Dukascopy.
