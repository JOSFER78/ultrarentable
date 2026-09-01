# PUNTO DE GUARDADO — track ULTRA (pausado 2026-08-31)

> **Motivo de la pausa:** orden de Emilio de centrar el 100 % del esfuerzo en FONDEO.
> Nada de lo de abajo está perdido ni a medias de forma incoherente: todo el trabajo está
> aplicado en el árbol y verificado. Este documento es lo único que hace falta leer para
> retomar ULTRA donde se dejó.

## Lo que quedó LISTO y verificado (no hay que rehacerlo)

| Pieza | Estado | Evidencia |
| :--- | :--- | :--- |
| Motor honesto **5.14.0** con las 4 familias de arquetipos | cerrado | identidad 15/15 vs 5.13.0; smoke de las 4 familias |
| **Gate 9 corregido** (DoF + vecindario) | cerrado y verificado por el orquestador | `9 passed` en `tests/test_red_team_adversarial.py` |
| **`risk_pct` cuenta como DoF** (ambos alias) | cerrado | conteos: REVERSION_ATR 3→4, SQUEEZE_BREAKOUT 5→6, SESSION_MOMENTUM 5→6, STREAK_EDGE 4→5, TREND_FOLLOWING 4→5, MOMENTUM_BREAKOUT 7→8 |
| **Perfil `arquetipos` encolable** | cerrado | `scripts/cola_mineria.py:253`; dry-run: 18 celdas, 0 omitidas |
| Análisis **TF vs coste vs trades OOS** | cerrado | `orchestration/results/analisis_tf_coste_vs_trades.md` |
| Objetivo ULTRA **sellado y verificable** | cerrado | F05 + índice del plan: ~100 %/mes sobre la MEDIANA, con p5/p95/P(ruina) |

## Lo que estaba A PUNTO DE LANZARSE (el siguiente paso exacto)

La re-campaña de descubrimiento, **todos los activos × todas las temporalidades** (decisión de
Emilio). Bloqueada únicamente porque la máquina estaba saturada. Comandos exactos:

```bash
# Encolar en este orden: primero donde hay evidencia de que se puede certificar.
.venv/bin/python scripts/cola_mineria.py encolar --perfil arquetipos --solo-cripto --tfs 15m --ver
.venv/bin/python scripts/cola_mineria.py encolar --perfil arquetipos --solo-cripto --tfs 15m
.venv/bin/python scripts/cola_mineria.py encolar --perfil arquetipos --solo-cripto --tfs 4h,1h
.venv/bin/python scripts/cola_mineria.py encolar --perfil arquetipos --solo-cripto --tfs 5m
# Trabajar (el perfil viaja en el payload de cada celda; `trabajar` NO tiene --profile):
nice -n 19 ionice -c 3 .venv/bin/python scripts/cola_mineria.py trabajar --concurrencia 2
# Después: censo del criterio 1.1 (SELLADO, no se relaja)
.venv/bin/python scripts/censo_f01.py
```

Dimensionado con tiempos REALES de campañas anteriores (`orchestration/results/cola_mineria.jsonl`,
15m con perfil `amplio` tardó 7.193 s y 7.403 s por celda; `arquetipos` son 420 configs frente a
~2.000, factor 0,21):

| TF | Barras | min/celda | 9 celdas |
| :--- | ---: | ---: | ---: |
| 4h | 10.500 | ~1,7 | 15 min |
| 1h | 25.500 | ~4 | 37 min |
| 15m | 198.528 | ~26 | 3,8 h |
| 5m | 595.584 | ~78 | 11,7 h |

Total ~16 h secuencial · **~8 h con concurrencia 2**. 36 celdas × 420 configs = 15.120 backtests.
**1m se descarta**: sólo tiene 10.500 barras (7 días), el OOS serían 1,5 días — falta de datos,
no criterio.

## Conclusión técnica que NO hay que volver a derivar

Con el criterio 1.1 sellado (≥200 trades OOS) y el split real IS 60 / Val 20 / **Blind OOS 20 %**:

- **4h**: coste irrelevante (98 % de un TP de 4 ATR sobrevive) pero sólo 2.100 barras OOS →
  harían falta trades de ~10 barras para llegar a 200. Estéril salvo caso extremo.
- **15m**: el punto óptimo. 39.706 barras OOS y el coste se come sólo el 6-10 %.
- **5m**: 119.117 barras OOS pero el coste se lleva el 11-18 % — hunde por sí solo un PF bruto
  de 1,40 hasta ~1,15-1,25. Marginal, y sólo en BTC/ETH/SOL (DOGE y XRP son sangría).

## Carril SQX para ULTRA (investigado, pendiente de ejecutar)

- Export existente `data/sqx_exports/toimprove_2026-08-31.csv`: **0 de 2.035 pasan el criterio 1.1**.
  Motivo: OOS del **0,3 %** (mediana 1 trade) y las 2.035 son de **AUDUSD_H1**, un símbolo
  irrelevante para ULTRA. No es culpa de SQX: está mal configurado.
- `services/sqx_bridge/converter.py` está **deshabilitado a propósito** (fail-closed) porque el
  conversor antiguo sintetizaba la lógica de la estrategia a partir de estadísticas. Correcto.
- **Los `.sqx` son ZIP con XML** (`strategy_Portfolio.xml`) y contienen la lógica COMPLETA:
  `Rule: Long entry/Short entry/Long exit/Short exit` de tipo `IfThen`, con `Item key=ATRLower
  display='ATR(@Chart@#Period#)[#Shift#] < #Level#'`, `OpenD`, `MTATR`, `EnterAtStop`, `AND`...
  El campo `display` da la expresión exacta. **Un parser puede reconstruirla sin inventar nada.**
- Proyecto SQX: `/home/ubuntu/StrategyQuantX144/user/projects/Ultra_Matrix/databanks/ToImprove/`
  (2.035 ficheros). Datos ya exportados: 97 CSVs en `data/sqx_imports/`.
- **Trabajo pendiente del carril**: (1) parser XML→canónico, (2) reconfigurar SQX sobre cripto con
  split OOS decente y la fricción real de BingX.

## Riesgos vivos al pausar

1. `sqx.service` y el minero huérfano (`run_continuous_pipeline`) seguían saturando la máquina;
   requieren `sudo` de Emilio. A `sqx.service` sólo `stop` (hace falta más adelante); el
   `disable` es sólo para `ultrarentable-discovery.service`.
2. **Push a GitHub pendiente**: causa raíz diagnosticada (ver `PUNTO_GUARDADO_ULTRA` no aplica —
   está en el informe de traspaso y en el análisis del pack). `.gitignore` ya preparado,
   `git-filter-repo` instalado, rama `backup-pre-filter-repo` creada. Falta ejecutar con el
   árbol limpio. **NO borrar `origin/tmp-sync`** hasta que `origin/main == main`.
3. F02.2 sigue bloqueado: cap de apalancamiento real BingX requiere API key de Emilio.
