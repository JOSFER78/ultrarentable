# HALLAZGO DECISIVO — El catálogo actual no tiene edge persistente

**Hermes · 2026-08-31 · Todo con datos reales de la BD canónica, cero simulación**

## Qué se hizo

1. Se conectó `MetaStrategyEngine` a la base canónica (antes apuntaba a una BD rancia de 12 KB).
2. Se eliminó una violación REAL-ONLY: el motor **fabricaba curvas de equity sintéticas**
   (recta lineal desde un ROI del 20 % asumido) cuando una estrategia no traía curva, y calculaba
   volatilidad, drawdown y correlaciones sobre ese invento. Ahora reconstruye desde `oos_returns`
   reales o falla con `NO DATA`.
3. Se ensamblaron dos meta-portafolios **con candidatos reales**.
4. Se escaló el riesgo hasta el presupuesto de DD y se validó **walk-forward**.

## Los meta-portafolios funcionan estructuralmente

| | META_ULTRA_REAL_01 | META_FONDEO_REAL_01 |
| :--- | ---: | ---: |
| Estrategias (activos ortogonales) | 5 | 8 |
| Correlación cruzada media | 0,106 | 0,077 |
| Reducción de drawdown | **99,5 %** | **81,8 %** |
| Sharpe combinado | 9,41 | 6,10 |
| Profit factor | 4,68 | 2,54 |
| Beneficio neto | 0,44 % | 0,28 % |

La diversificación ortogonal **hace exactamente lo que promete**: correlaciones casi nulas y
drawdowns aplastados. El mecanismo es correcto.

## El escalado de riesgo, en muestra completa

| Track | k máximo | Retorno | DD | Presupuesto |
| :--- | ---: | ---: | ---: | ---: |
| ULTRA | 400 | +106,2 % | 61,4 % | 70 % |
| FONDEO | 25 | +36,8 % | 3,99 % | 4 % |

Prometedor... pero la `k` se eligió mirando la misma serie con la que se evalúa. Eso es
sobreajuste, y la prueba honesta lo desmonta.

## Walk-forward: la prueba que importa

`k` elegida **solo con la primera mitad**, aplicada a ciegas a la segunda:

| Track | k entreno | k óptimo real | Retorno ciego | DD ciego | Veredicto |
| :--- | ---: | ---: | ---: | ---: | :--- |
| ULTRA | 760 | 723 | **−42,7 %** | 72,1 % | ❌ pierde y excede presupuesto |
| FONDEO | 25 | 29 | +3,4 % | 3,42 % | ✅ dentro de presupuesto |

## ⛔ Lo importante: ULTRA pierde a CUALQUIER apalancamiento

| Fracción de k | k | Retorno fuera de muestra | DD |
| ---: | ---: | ---: | ---: |
| 1,00 | 760 | −42,7 % | 72,1 % |
| 0,50 | 380 | −15,2 % | 44,1 % |
| 0,25 | 190 | −5,2 % | 24,3 % |
| 0,10 | 76 | **−1,4 %** | 10,3 % |

**Todos negativos.** Bajar el riesgo solo reduce la pérdida; nunca la convierte en ganancia.

**Diagnóstico:** no es un problema de dimensionamiento. El edge de las estrategias ULTRA del
catálogo **no persiste**: ganaron en la primera mitad de su propio periodo OOS y perdieron en la
segunda. Una envolvente de balas **amplifica lo que haya**. Si la esperanza es negativa, amplifica
pérdidas. No hay ingeniería de gestión de capital que arregle un edge inexistente.

## Segunda lección, válida y reutilizable

Aunque el edge fuera bueno, **no se puede dimensionar al DD máximo admisible**: la `k` que roza el
70 % en el pasado se sale al 72,1 % en el futuro. El drawdown futuro siempre supera al pasado.
Hay que dimensionar a una **fracción** del presupuesto. Esto se sella como regla del motor de balas.

## Consecuencia para el plan

- Las Fases 5 (envolvente) y 6 (router) están **desbloqueadas técnicamente** — el mecanismo
  funciona y está probado— pero **no tienen materia prima**.
- La ruta a los miles de % pasa **obligatoriamente** por la Fase 3: campaña de descubrimiento
  masiva con el criterio duro de la Fase 1 (≥200 operaciones OOS, PF ≥ 1,25, ratio OOS/IS ≥ 0,5)
  y **exigencia añadida: el edge debe persistir entre mitades del periodo OOS**.
- Los 15 candidatos `APPROVED_CURRENT_ENGINE` no son base válida. Con 9-120 operaciones no hay
  estadística, y la validación por mitades lo confirma.
