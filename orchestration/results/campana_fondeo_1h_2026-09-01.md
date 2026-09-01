# CAMPAÑA FONDEO 1h — resultado: 0 certificadas de ~13.504 backtests

Fecha: 2026-09-01 · Track: FONDEO · Motor: 5.15.0 → 5.16.0 (corregido a mitad, ver abajo)
Perfiles: `arquetipos` (348 configs, 4 familias) y `amplio` (848 configs, 7 familias)
Universo: 6 futuros CME (ES, NQ, YM, RTY, GC, CL vía micros MES/MNQ/MYM/M2K/MGC/MCL)
+ 6 divisas (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF), timeframe **1h**.

## Resultado

**23 celdas · 78 min de CPU · ~13.504 backtests · CERTIFICADAS: 0.**

Se reporta la cifra real, como exige la doctrina. No se ha relajado ningún umbral: el criterio
1.1 sigue SELLADO (≥200 operaciones OOS, PF OOS ≥1,25, OOS/IS ≥0,5, 11 gates, DSR, persistencia).

## Por qué 0 — son DOS causas distintas, no una

### Futuros: no acumulan operaciones suficientes (límite de datos)

| Símbolo | Mejor caso en OOS |
| :--- | :--- |
| RTY | 45 operaciones, PF 0,62 |
| USDJPY | 40 operaciones, PF 0,89 |
| ES | 27 operaciones, PF 0,65 |
| CL | 24 operaciones, PF 0,82 |
| YM | 4 operaciones, PF 3,68 |
| NQ | 1 operación, PF 99,00 |

El suelo del pipeline son **100 operaciones** (`MIN_OPERACIONES_OOS`) y el criterio 1.1 pide
**200**. Ninguna celda se acerca. Y no es un problema de espacio de búsqueda: pasar de 348 a
**848 configuraciones con 7 familias** subió el mejor caso de 24 a 27 operaciones.

Aritmética del bloqueo:

```
criterio 1.1:            >=200 operaciones OOS
ritmo observado:         ~1 operacion cada 101 barras (mejor caso por PF)
barras OOS necesarias:   ~20.200   ->  dataset de ~101.000 barras
disponible (Yahoo 1h):     13.701 barras  ->  2.740 OOS   (7,3x por debajo)
```

El 5m de Yahoo **no es alternativa**: tiene 13.813 barras, casi las mismas que 1h, porque su
API sólo sirve 60 días de intradía fino. La única vía es Dukascopy (5m desde 2023 ≈ 250.000
barras ≈ 495 operaciones OOS).

**Los PF altos con pocas operaciones son la trampa clásica**: NQ con `PF 99,00` y **1 sola
operación**, YM con `PF 3,68` y 4. Es exactamente el espejismo que generó las 728 "certificadas"
falsas que hubo que sanear: estrategias que certificaban por **no operar**, no por tener edge.
El filtro de 100 operaciones hace bien su trabajo al descartarlas.

### Divisas: operan de sobra, pero no tienen edge

Con el motor 5.16.0 (comisión corregida), el forex sí opera: 121-447 operaciones en IS.
Aun así, embudos como `{'IS': 848}` en AUDUSD/USDCAD y `{'IS': 840, 'VAL': 8}` en EURUSD
muestran que mueren contra un filtro laxísimo (≥5 operaciones y **PF ≥1,05**). No es falta de
barras: es falta de señal. Más datos no lo arreglan; hacen falta **mejores reglas**.

## Aviso: la primera tanda de divisas es INVÁLIDA

Las 6 celdas de forex del perfil `arquetipos` se ejecutaron con el motor ≤5.15.0, que clasificaba
las divisas como futuros CME y les cobraba `2,50 $ × qty` = **11.692 $ por lado** (ver
`orchestration/results/bug_comision_forex_5_16_0.md`). Sus embudos `{'IS': 348}` son artefacto,
no veredicto. Quedan sustituidas por las del perfil `amplio`, ya con el motor corregido.
Las celdas de **futuros son válidas en ambas tandas**: su clasificación no cambia entre 5.15.0 y
5.16.0, como confirma la verificación de identidad 15/15.

## Conclusión y siguiente paso

1. **FONDEO en futuros está bloqueado por DATOS, no por falta de edge.** Se desbloquea con el
   backfill de Dukascopy, cuyo ritmo pasó de 174 a **6.984 ficheros/hora** (medido en producción)
   tras corregir que abría una conexión TCP+TLS nueva por cada una de las ~32.000 peticiones.
   ETA: ~4,6 h para ES, ~14 h para los tres índices.
2. **FONDEO en divisas no se arregla con datos.** Las plantillas paramétricas (7 familias, 848
   combinaciones) están agotadas. El camino es generación de reglas nuevas (SQX) validadas
   después con el motor propio y los 11 gates.
3. **Antes de minar con Dukascopy** hay dos requisitos previos documentados en
   `orchestration/state/current_phase.md`: el mapeo símbolo→dataset (hoy `ES` resolvería al
   fichero de Yahoo en silencio) y la validación de correlación CFD-proxy vs. futuro real.
