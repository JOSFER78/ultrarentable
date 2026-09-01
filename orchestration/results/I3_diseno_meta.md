---
expediente: I3
modulo: M4 — Metaestrategias
estado: DISEÑO CERRADO (implementación pendiente, bloqueada por ≥2 certificadas)
fecha: 2026-09-01
autor: subagente carril META
territorio_escritura: services/meta/** (no existe hoy), tests/test_meta_*.py, orchestration/results/I3_*.md
---

# I3 — Diseño de meta-estrategias (M4)

## 0. Resumen ejecutivo

1. El pipeline meta **no está "muerto de fábrica" de una sola pieza**: hay **cuatro implementaciones
   paralelas e inconsistentes** en `services/portfolio/`. Dos ya están arregladas y REAL-ONLY
   (`meta_strategy_pipeline.py` + `meta_ensemble_service.py`, vivas y montadas en la API). Dos
   siguen fabricando datos hoy mismo (`portfolio_engine.py` + `portfolio_combiner.py`, y el
   huérfano `portfolio_sprint_engine.py`), y una tercera vía (`meta_strategy_engine.py`, usada
   solo por CLIs) ya corrigió la fabricación de correlación 0,15 y PF 5,0 que menciona el
   contrato, pero conserva un bug de alineación temporal no documentado hasta este informe.
   Además, **`autonomous_meta_daemon.py` está vivo y roto**: arranca 24/7 en cada `main.py` y
   revienta con `KeyError` en cada ciclo porque llama a un contrato que ya cambió — ver §2.
2. Hoy la base canónica tiene **0 candidatos, 0 portafolios, 0 meta-portafolios** (verificado en
   vivo, no es una cifra de un documento — ver §2.6). El bloqueante "≥2 certificadas" del plan es
   real y actual, no hipotético.
3. Respuestas a las 5 preguntas (desarrolladas en §3): (1) ensamblado **HRP como base numérica +
   búsqueda de mínima varianza del examen como árbitro final**, Kelly fraccional **rechazado**
   como método de pesos entre componentes (objetivo equivocado: crecimiento, no ruina) pero su
   lección de fraccionar se reutiliza en el multiplicador de apalancamiento agregado; (2)
   correlación **por PnL agregado por día calendario real** (nunca por índice de operación, nunca
   por nivel de equity — ambos son errores estadísticos activos hoy en el código, ver §2); (3)
   router con protocolo de debate persistido dentro de límites deterministas heredados
   literalmente de `F06_meta_router.md` (aparcado pero con la forma correcta), con una lista
   explícita de lo que un LLM nunca decide; (4) MFFU prohíbe coordinar/copiar entre cuentas
   propias — la meta por defecto es **una sola cuenta, multi-activo**, nunca multi-cuenta salvo
   confirmación explícita por firma; (5) la meta se examina reutilizando literalmente
   `scripts/fondeo_examen.py` sobre un ledger combinado, con un hueco real declarado: no existe
   hoy un motor de verificación barra a barra a nivel de **portafolio** — construirlo toca
   `event_backtest_engine.py` y cae bajo Regla #26, **fuera de mi territorio**.
4. Software SQX: la instalación local es licencia **Professional Trial** (caduca 05-09-2026),
   no Ultimate → Portfolio Master/Composer limitado a 4 estrategias (por debajo de nuestro propio
   tope de 6) y QuantAnalyzer Pro **no instalado**. El único proyecto SQX de portafolio con
   configuración real es `PortfolioMaster` (plantilla de fábrica, nunca ejecutada con datos
   propios); `PortfolioComposer` está vacío. Matriz completa en §4.

---

## 1. Método y fuentes primarias consultadas

| Fuente | Tipo | Fecha consulta | Uso |
|---|---|---|---|
| `orchestration/state/PLAN_INVESTIGACION_PROFUNDA.md` (I3, líneas 100-129) | interno | leído hoy | preguntas del contrato |
| `orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md` (M4, líneas 96-107) | interno | leído hoy | contrato de entrada/salida del módulo |
| `orchestration/state/plan/bloques/F06_meta_router.md` | interno | leído hoy | forma del router (aparcado, ULTRA) — precedente de diseño para §3.3 |
| `orchestration/state/plan/bloques/F07_fondeo_examenes.md` | interno | leído hoy | objetivo sellado, "la varianza mata más que la media baja" |
| `orchestration/state/plan/bloques/REGLAS_INVARIANTES.md` | interno | leído hoy | Regla #26, REAL-ONLY |
| `orchestration/results/I4_prop_firms_hallazgos.md` §3 y §6 | interno (ya verificado por I4 con fetch directo) | leído hoy | ToS de copy-trading MFFU/otras firmas |
| `orchestration/results/I1_sqx_hallazgos.md` §1 | interno (ya verificado por I1 con `sqcli.exe`) | leído hoy | nivel de licencia SQX real de esta instalación |
| `services/portfolio/*.py` (7 ficheros, 1.462 LOC) | código propio | leído íntegro hoy | inventario del pipeline meta actual |
| `services/api/app/factory/portfolio_sprint_engine.py`, `ultra_portfolio_engine.py` | código propio | leído hoy | código meta huérfano fuera de `services/portfolio/` |
| `scripts/fondeo_examen.py` (1.039 líneas) | código propio | leído íntegro hoy | mecanismo real de examen y veredicto sellado |
| `scripts/meta.py` | código propio | leído hoy | lección ya aprendida sobre Kelly/fracción de DD |
| `contracts/portfolio.py`, `contracts/snapshots/portfolio_snapshot.py` | código propio | leído hoy | contratos ya existentes que anticipan ERC/HRP |
| `tests/test_meta_*.py`, `tests/test_portfolio_*.py` (5 ficheros, 571 líneas) | código propio | nombres de test leídos hoy | qué comportamiento ya está fijado por tests |
| BD canónica `C:\Users\yo\.local\state\ultrarentable\ultrarentable.sqlite3` | dato en vivo | consultada hoy con `sqlite3` | conteo real de candidatos/portafolios |
| `C:\StrategyQuantX144\user\projects\PortfolioMaster\project.cfx` (ZIP→XML) | software local | descomprimido y leído hoy | configuración real del Automatic Portfolio Builder |
| `C:\StrategyQuantX144\user\projects\PortfolioComposer\project.cfx` (ZIP→XML) | software local | descomprimido y leído hoy | confirmar que está vacío |
| `strategyquant.com/doc/quantanalyzer/portfolio-correlation-explained/` | doc oficial | WebFetch 2026-09-01 | series y ventanas de correlación de QuantAnalyzer |
| `strategyquant.com/blog/portfolio-master-automatic-portfolio-builder/` | doc oficial | WebFetch 2026-09-01 | qué hace el Automatic Portfolio Builder |
| `strategyquant.com/quantanalyzer/portfolio-master/` | doc oficial | WebFetch 2026-09-01 | qué es Portfolio Master, licencia |
| `strategyquant.com/doc/strategyquant/results-strategy-correlation/` | doc oficial | WebFetch 2026-09-01 | correlación en resultados del Builder (poco detalle técnico expuesto) |

Todo lo que sigue cita ruta:línea del código real leído en esta sesión, o URL+fecha para fuente
externa. Ningún número de este informe procede de memoria del modelo ni de un documento del
repo sin re-verificar contra el código o una fuente primaria.

---

## 2. Hallazgo central: inventario real del código meta (vivo / muerto / roto)

### 2.1 Cuatro implementaciones paralelas, no una

| Fichero | LOC | ¿Quién lo importa de verdad? | Estado |
|---|---|---|---|
| `services/portfolio/meta_strategy_pipeline.py` | 296 | `certified_summary_router.py:309` (`GET /meta-strategies`) | **VIVO, REAL-ONLY** |
| `services/portfolio/meta_ensemble_service.py` | 199 | `portfolio_router.py:13` (`POST /assemble`), `meta_strategy_pipeline.py:105`, `autonomous_meta_daemon.py:15` | **VIVO, REAL-ONLY** (pero con contrato de salida distinto al que espera el daemon — ver 2.3) |
| `services/portfolio/meta_strategy_engine.py` | 475 | `scripts/meta.py:32`, `scripts/mine.py`, `scripts/fondeo_examen.py:32` — **ningún router de la API lo importa** | Huérfano de la API (solo CLI offline). Ya corregido de la fabricación 0,15/5,0 (ver 2.2), pero con bug de alineación no documentado (ver §3.2) |
| `services/portfolio/portfolio_engine.py` + `portfolio_combiner.py` | 154+126 | solo `services/api/app/factory/ultra_portfolio_engine.py`, que a su vez **no lo importa nadie** (`grep -rln ultra_portfolio_engine services/` solo devuelve el propio fichero) | **Huérfano total**, y sigue fabricando datos hoy (ver 2.4) |
| `services/api/app/factory/portfolio_sprint_engine.py` | 96 | nadie (`grep -rln build_fondeo_sprint_portfolios services/` solo devuelve el propio fichero; el único caller es su propio test) | **Huérfano total**, hardcodea `correlation_score=0.18` |

Verificado con:
```
grep -rln "autonomous_meta_daemon\|start_autonomous" services/ --include="*.py"
grep -rln "portfolio_engine\|PortfolioEngine\|portfolio_combiner\|PortfolioCombiner" services/ scripts/ --include="*.py"
grep -rln "meta_strategy_engine\|MetaStrategyEngine" services/ scripts/ --include="*.py"
grep -rln "ultra_portfolio_engine" services/ --include="*.py"
```
(salidas literales recogidas durante esta sesión, resumidas en la tabla).

### 2.2 La fabricación que cita el contrato (correlación 0,15 y PF 5,0) — CONFIRMADA y ya corregida en un fichero, viva en otro

`services/portfolio/meta_strategy_engine.py:276-285`:
```python
# Regla Invariante #1 (REAL-ONLY): "Sin dato ⇒ NO DATA/ERROR, nunca un valor por
# defecto". Con <=2 pasos alineados una correlación muestral no es estimable de forma
# fiable; antes se fabricaba c_val=0.15, una meta-estrategia fantasma con evidencia
# inventada. Fail-closed explícito en su lugar.
if min_steps <= 2:
    raise ValueError("INSUFFICIENT_OVERLAP: ...")
```
`services/portfolio/meta_strategy_engine.py:347-353`:
```python
# Si no hubo ningún paso perdedor en la ventana OOS alineada, el profit factor no tiene
# un valor finito bien definido (división por pérdidas nulas). Antes se fabricaba un
# techo arbitrario (5.0); ahora se representa como infinito explícito y se marca con
# `no_losing_periods_oos=True` ...
no_losing_periods_oos = bool(comb_losses <= 0.0)
comb_pf = float("inf") if no_losing_periods_oos else round(float(comb_gains / comb_losses), 2)
```
Esto confirma **literalmente** la afirmación del contrato ("correlación 0,15 con ≤2 pasos y PF
5,0 sin perdedoras") como cierta en el pasado de este fichero, y confirma que ya fue reparada
(el propio comentario documenta el fix). Test que la fija: `tests/test_meta_strategy_engine.py:72`
`test_assemble_meta_portfolio_never_fabricates_correlation_with_thin_overlap`.

**Pero el mismo patrón sigue vivo, sin corregir, en el fichero paralelo**:

`services/portfolio/portfolio_combiner.py:107`:
```python
comb_pf = (all_gains / all_losses) if all_losses > 0 else (99.0 if all_gains > 0 else 0.0)
```
Techo arbitrario **99.0** (mismo antipatrón que el 5.0 ya corregido en otro fichero, aquí intacto).

`services/portfolio/portfolio_combiner.py:83-86`:
```python
c = float(np.corrcoef(eq_matrix[i], eq_matrix[j])[0, 1])
...
corr_matrix[r_i.strategy_id][r_j.strategy_id] = round(0.0 if math.isnan(c) else c, 4)
```
Correlación NaN → **0.0 fabricado en silencio** (ningún `raise`), y además —hallazgo nuevo, no
documentado en el repo hasta este informe— la correlación se calcula sobre **niveles de equity**
(`eq_matrix`), no sobre retornos/PnL: dos curvas de equity con tendencia al alza producen
correlación espuriamente alta aunque las señales subyacentes sean independientes (artefacto
estadístico clásico de correlacionar series no estacionarias). Ver §3.2.

`services/portfolio/portfolio_engine.py:116-118`:
```python
if min_len < 2:
    # Fallback a matriz identidad si pocos trades
    return np.ones((10, n)) * 0.01, np.eye(n)
```
**Fabricación explícita**: 10 periodos de retorno 0,01 inventados + matriz de correlación
identidad inventada cuando hay pocos trades, en vez de fallar cerrado. Y en `portfolio_engine.py:126-127`:
```python
if np.isnan(corr_matrix).any():
    corr_matrix = np.eye(n)
```
Correlación NaN → identidad (0,0) silenciada, mismo patrón que en `portfolio_combiner.py`.

`services/api/app/factory/portfolio_sprint_engine.py:38,93`:
```python
correlation_score: float = 0.0          # línea 38, default de la dataclass
...
correlation_score=0.18,                 # línea 93, CONSTANTE LITERAL, nunca calculada
```
`tests/test_portfolio_provenance_and_zero_mock.py:23-30` (`test_fondeo_sprint_no_artificial_clamping`)
existe y pasa hoy, pero **no comprueba `correlation_score` en absoluto** — el hardcode pasa sin
que ningún test lo detecte. Verificado leyendo el test completo.

**Conclusión de este punto**: la caracterización "correlación fabricada" del contrato es
CONFIRMADA como hecho histórico y sigue siendo un hecho VIGENTE hoy, pero en ficheros distintos
a los que ya se repararon — la reparación fue parcial, no sistémica.

### 2.3 `autonomous_meta_daemon.py` — vivo, arrancado 24/7, y roto por un cambio de contrato

`services/api/app/main.py:98-101` (arranque, dentro del `lifespan` de FastAPI, condicionado solo
a `ULTRARENTABLE_AUTONOMOUS_RUNTIME`):
```python
from services.portfolio.autonomous_meta_daemon import autonomous_meta_daemon
autonomous_meta_daemon.start_autonomous(interval_seconds=60)
logger.info("AutonomousMetaDaemon iniciado autónomamente 24/7.")
```
`services/portfolio/autonomous_meta_daemon.py:77-101` construye el registro `PortfolioModel` leyendo
del dict que devuelve `MetaEnsembleService.assemble_meta_portfolio(...)`:
```python
meta = MetaEnsembleService.assemble_meta_portfolio(...)
if meta:
    ...
    db_port = PortfolioModel(
        ...,
        current_equity_usd=meta["current_equity_usd"],       # <- no existe en el dict
        annualized_roi_pct=meta["annualized_roi_pct"],        # <- no existe
        monthly_roi_pct=meta["monthly_roi_pct"],               # <- no existe
        max_drawdown_pct=meta["max_drawdown_pct"],             # <- no existe (es weighted_max_drawdown_oos_pct)
        profit_factor=meta["profit_factor"],                   # <- no existe
        ...
    )
```
Pero el contrato REAL que devuelve hoy `assemble_meta_portfolio` (`meta_ensemble_service.py:182-196`)
es:
```python
return {
    "portfolio_id": ..., "name": ..., "target_route": ..., "base_capital_usd": ...,
    "components": ..., "weights": ..., "correlation_matrix": ...,
    "weighted_net_profit_oos_usd": ..., "weighted_max_drawdown_oos_pct": ...,
    "canonical_hash": ..., "status": ..., "engine_version": ..., "created_at_utc": ...,
}
```
Ninguna de las cinco claves que lee el daemon existe en este dict → **`KeyError` garantizado**
cada vez que haya ≥2 candidatos ULTRA en las primeras 20 filas de `candidates` (línea 71-76 del
daemon). El `except Exception` de `_run_meta_assembly_cycle` (líneas 106-109) lo atrapa y lo
deja solo en `self.last_error`, visible únicamente en `GET /api/v1/portfolio/status` — nadie lo
ve salvo que consulte ese endpoint a propósito. **Hoy no revienta porque hay 0 candidatos** (ver
§2.6: el `len(candidates) < 2` en la línea 72 corta antes de llegar al `KeyError`), pero en el
instante en que existan 2 candidatos ULTRA reales, este daemon empezará a fallar en bucle cada
60 segundos, en silencio, 24/7, sin ensamblar nunca nada.

**No es una hipótesis: es un bug reproducible por inspección de contrato**, no necesita datos
para confirmarse (el desajuste de claves es estático). Petición al orquestador en §7.

### 2.4 El "HRP" del contrato ya existente no es HRP

`contracts/portfolio.py:12-16` ya declara los cuatro métodos que pide la pregunta 1 del
contrato:
```python
class AllocationMethod(str, Enum):
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    INVERSE_VOLATILITY = "INVERSE_VOLATILITY"
    RISK_PARITY_ERC = "RISK_PARITY_ERC"
    HIERARCHICAL_RISK_PARITY = "HIERARCHICAL_RISK_PARITY"
```
Pero `services/portfolio/portfolio_engine.py:149-152` implementa **la misma fórmula** para
`RISK_PARITY_ERC` y `HIERARCHICAL_RISK_PARITY`:
```python
if method in (AllocationMethod.RISK_PARITY_ERC, AllocationMethod.HIERARCHICAL_RISK_PARITY):
    # Equal Risk Contribution aproximado
    inv_var = 1.0 / (vols ** 2)
    return inv_var / np.sum(inv_var)
```
Es inversa de varianza (ni siquiera inversa de volatilidad como en los otros ficheros), sin
clustering jerárquico, sin cuasi-diagonalización, sin bisección recursiva — no es HRP de López
de Prado bajo ningún criterio. La etiqueta existe en el contrato pero el cálculo no. (Este
fichero es huérfano — §2.1 — así que el impacto práctico hoy es cero, pero si se reutilizara tal
cual en `services/meta/` sería un error real, no solo cosmético.)

### 2.5 `W4.2` (hardcode `engine_version 5.4.0`) — parcialmente CONFIRMADO como ya resuelto para meta

`orchestration/state/PLAN_LOCAL_FONDEO.md:108` lista `meta_ensemble, meta_strategy_pipeline`
entre los ficheros con hardcode `5.4.0` pendiente de quitar. Verificado con
`grep -rln "5\.4\.0" services/ scripts/ contracts/` (excluyendo `__pycache__`): **ningún hit**
en `services/portfolio/`. Los dos ficheros usan `CURRENT_ENGINE_VERSION`
(`meta_strategy_pipeline.py:44,70`) e `is_version_stale` (`meta_ensemble_service.py:14,133-137`),
ambos importados desde `services/engine_version.py` (SSOT). **Veredicto: la parte de W4.2 que
toca a meta ya está hecha** — la lista de W4.2 en el plan queda desactualizada en ese punto
concreto (afecta a los otros ficheros que sí siguen citados: `fast_engine_adapter.py`,
`funding_research_loop.py`, `strategy_research_loop.py`, `excel_master_catalog.py` — fuera de mi
territorio, no verificados aquí).

### 2.6 Cero candidatos, cero portafolios — verificado en vivo, no en un documento

```
$ ./.venv/Scripts/python.exe -c "... SELECT COUNT(*) FROM candidates ..."
total candidates: (0,)
```
Consulta completa a las 32 tablas de `C:\Users\yo\.local\state\ultrarentable\ultrarentable.sqlite3`
(532.480 bytes, modificada hoy 19:13): `candidates=0`, `portfolios=0`, `meta_portfolios=0`,
`backtests=0`, `strategies=0`. Coincide con `orchestration/results/meta_resultados.json` =
`{"ULTRA": null, "FONDEO": null}`. Y con el test ya existente
`tests/test_meta_strategy_engine.py:43` `test_assembly_readiness_is_no_evaluable_for_fondeo_today`.
**El bloqueante "≥2 certificadas" no es una advertencia teórica del plan: es el estado real de
la base ahora mismo.**

### 2.7 `determinar_veredicto_sellado` — el hueco que `F07_fondeo_examenes.md` dice abierto YA está cerrado en el código

`orchestration/state/plan/bloques/F07_fondeo_examenes.md` (actualizado 2026-09-01, mismo día)
afirma: *"el resultado [de `reejecutar_examen_barra_a_barra`] no gatea nada... en cuanto exista
la primera [candidata], el script podrá declarar 'CUMPLE' para una cuenta que la propia
verificación honesta marca como `prop_firm_busted=True`"*.

Leído el código real (`scripts/fondeo_examen.py:595-624` y su uso en `899-900`):
```python
def determinar_veredicto_sellado(cumple_bootstrap, verif_flotante) -> str:
    if verif_flotante is None:
        return "NO_EVALUABLE"
    if verif_flotante.get("prop_firm_busted"):
        return "NO_CUMPLE"
    return "CUMPLE" if cumple_bootstrap else "NO_CUMPLE"
...
veredicto_sellado = determinar_veredicto_sellado(cumple_sellado_bootstrap, verif_flotante)  # línea 899
cumple_sellado = veredicto_sellado == "CUMPLE"                                               # línea 900
```
Esto **SÍ gatea**: una cuenta con `prop_firm_busted=True` nunca puede salir "CUMPLE", y sin
verificación barra a barra el veredicto es siempre `NO_EVALUABLE`, nunca un `CUMPLE` optimista
por defecto. **Veredicto sobre la afirmación previa: REFUTADA por el código actual** — la nota
de `F07_fondeo_examenes.md` quedó desactualizada el mismo día en que se corrigió (el fix llegó
después de esa nota, o la nota no se actualizó tras el fix). Esto importa para M4 porque §3.5
reutiliza exactamente esta función: **confirmo que la pieza que voy a reutilizar funciona como
digo que funciona, no como dice el documento que la describe.**

---

## 3. Respuestas a las cinco preguntas del contrato

### 3.1 Pregunta 1 — Ensamblado para FONDEO: ERC vs HRP vs Kelly fraccional vs mínima varianza del examen

**Objetivo real, citado literalmente de `F07_fondeo_examenes.md`**: *"combinar estrategias poco
correlacionadas para bajar la varianza del examen. En fondeo, la varianza mata más que la media
baja."* No es Sharpe, no es retorno esperado: es minimizar P(romper cuenta) y la varianza de un
resultado en 3-8 días medido bajo reglas asimétricas y dependientes de la trayectoria (trailing
drawdown), no bajo un supuesto gaussiano de retornos.

**ERC (Equal Risk Contribution)** — cada componente aporta la misma contribución de riesgo a la
varianza del portafolio: resolver `w` tal que `w_i·(Σw)_i = w_j·(Σw)_j ∀i,j`, sujeto a `Σw=1`,
donde `Σ` es la matriz de covarianza. La aproximación diagonal (sin correlación, `w_i ∝ 1/σ_i²`
o `1/σ_i`) es exactamente lo que ya implementan `meta_strategy_engine.py` (`1/σ_i`,
`compute_risk_parity_weights` en `meta_ensemble_service.py:23-30`) y `portfolio_engine.py`
(`1/σ_i²`). Con matriz completa (no diagonal), ERC requiere invertir `Σ` — con N=2-6 componentes
y solapes temporales cortos (§3.2), `Σ` puede ser casi singular y la inversión se vuelve
numéricamente inestable.

**HRP (Hierarchical Risk Parity, López de Prado 2016)** — tres pasos: (1) clustering jerárquico
sobre la matriz de distancia `d_ij = sqrt(0.5·(1-ρ_ij))`; (2) cuasi-diagonalización (reordenar
activos para que los similares queden contiguos); (3) bisección recursiva asignando pesos
inversos a la varianza de cada clúster, bajando por el árbol, **sin invertir nunca la matriz de
covarianza completa**. Esta última propiedad es la que importa aquí: con pocos componentes y
poca historia solapada (justo nuestro caso realista, N=2-6), HRP degrada con gracia donde ERC/
mínima-varianza clásica se vuelve inestable. Con N=2 (el caso inmediato en cuanto exista la
segunda certificada), el paso de clustering es trivial y HRP colapsa a la misma inversa de
varianza que ya está implementada — es decir, **adoptar HRP no rompe nada hoy y solo se
diferencia cuando N crece a 3+**.

**Kelly fraccional** — óptimo multi-activo `f* = Σ⁻¹μ` (vector), maximiza la tasa de crecimiento
geométrico a largo plazo (`E[log(1+f·r)]`), no minimiza varianza ni ruina en un horizonte corto.
Dos problemas concretos para FONDEO: (a) requiere `Σ⁻¹` igual que ERC, con el mismo problema de
estabilidad, pero además es sensible a la estimación de `μ` (la media), que con series OOS
cortas es mucho más ruidosa que la varianza — el "full Kelly" clásico sobre-apuesta cuando `μ`
está mal estimada; (b) el objetivo mismo está mal alineado: Kelly acepta drawdowns grandes con
tal de maximizar el crecimiento a infinito, exactamente lo contrario de "minimizar P(romper
cuenta) en 3-8 días". **La propia lección ya aprendida el 31-08-2026 en `scripts/meta.py:11-16`
confirma esto empíricamente**: *"NO se dimensiona al drawdown máximo admisible. La k que roza el
70% en el pasado se sale al 72% en el futuro. Se dimensiona a una FRACCIÓN del presupuesto
(`--fraccion`, 0.5 por defecto)"* — es la versión de sizing-agregado de exactamente el fallo que
Kelly comete al pleno: optimizar al límite histórico revienta la cuenta en el futuro.
**Kelly fraccional se rechaza como método de reparto de pesos entre componentes.**

**Mínima varianza del examen** — no es una técnica de cartera "con nombre" en el sentido
académico de las tres anteriores: es optimizar directamente la métrica objetivo (`p_romper_cuenta`,
varianza de `días-a-pasar`) calculada por Monte Carlo bajo las reglas EXACTAS de la firma
(trailing DD, pérdida diaria, consistencia — no gaussianas, no simétricas, dependientes de
trayectoria), en vez de una proxy (varianza de retornos bajo supuesto gaussiano). Es la única de
las cuatro que optimiza literalmente lo que F07 pide, no una aproximación.

**Decisión propuesta (con razón)**: método en dos fases, no una elección única:

1. **HRP como base numérica** — inicialización robusta de pesos, nunca invierte una covarianza
   casi singular, colapsa de forma segura a la implementación actual cuando N=2. Nunca ERC puro
   (mismo resultado a N=2, peor estabilidad a N≥4), nunca Kelly (objetivo equivocado).
2. **Búsqueda de mínima varianza del examen como árbitro final** — sobre el ledger combinado
   (§3.5) con los pesos de HRP como punto de partida, explorar una rejilla pequeña alrededor
   (viable con N≤6 componentes — el tope ya fijado en `meta_strategy_pipeline.py:120`) usando
   el **mismo** Monte Carlo de `scripts/fondeo_examen.py::evaluar()`, y quedarse con el vector de
   pesos que minimice `p_romper_cuenta` (empate: menor varianza de `días-a-pasar`). Nunca
   confiar en la proxy de varianza de retornos cuando se puede medir el objetivo real
   directamente — el coste computacional es asumible (N≤6, `evaluar()` ya vectorizado con numpy,
   8 núcleos disponibles, sin necesitar reintentos).
3. La lección de Kelly (fraccionar, no maximizar al límite histórico) se reutiliza en una capa
   distinta: el multiplicador de apalancamiento agregado sobre el ledger YA combinado se acota a
   una **fracción del presupuesto de drawdown de la firma** (mismo patrón que `--fraccion=0.5`
   de `scripts/meta.py`), nunca al máximo consistente con el DD observado en el pasado.

### 3.2 Pregunta 2 — Correlación honesta

**¿Retornos de operación o equity diaria? Ninguno de los dos — PnL agregado por día calendario
real.** Tres motivos, con evidencia de que las dos alternativas ya están rotas en el código
actual:

- **Correlacionar niveles de equity es un error estadístico**, no solo un estilo distinto:
  `portfolio_combiner.py:83` hace `np.corrcoef(eq_matrix[i], eq_matrix[j])` sobre las curvas de
  equity acumuladas. Dos curvas de equity con tendencia al alza (ambas rentables) producen
  correlación espuriamente alta aunque las señales subyacentes sean independientes — es el
  motivo textbook por el que en finanzas cuantitativas siempre se correlacionan retornos/PnL, no
  niveles de series no estacionarias. **Hallazgo nuevo de este informe**, no documentado antes en
  el repo.
- **Correlacionar por índice secuencial de operación (no por tiempo real) es otro error**, más
  sutil: `meta_strategy_engine.py:286` construye `aligned_returns = np.array([r[:min_steps] for
  r in returns_series])` — toma las primeras `min_steps` operaciones de CADA serie en su propio
  orden cronológico, sin comprobar que el "paso 5" de la estrategia A ocurra en el mismo
  intervalo de calendario que el "paso 5" de la estrategia B. Si A opera 1h y hace 40
  operaciones/mes y B opera diario con 2 operaciones/mes, "paso 5" de A puede ser 3 días dentro
  del OOS y "paso 5" de B puede ser 2,5 meses dentro — no es el mismo tiempo real, y el número de
  correlación resultante, aunque ya no se fabrica cuando hay ≤2 pasos (§2.2), sigue siendo
  **numéricamente válido pero conceptualmente sin sentido** cuando las frecuencias difieren.
  **Hallazgo nuevo de este informe.**
- El propio `meta_strategy_pipeline.py::_weekly_aligned` (líneas 126-169) ya construye la
  alternativa correcta: agrega PnL real por semana ISO desde `entry_time_ms`, con cero explícito
  en semanas sin operación, y descarta componentes sin varianza. Es el patrón a generalizar, no a
  reinventar — solo cambio propuesto: **granularidad diaria en vez de semanal**, porque las
  reglas de la firma (pérdida diaria, consistencia) operan sobre el día calendario, no la
  semana, y porque un examen de 3-8 días necesita más resolución temporal que semanas para tener
  observaciones suficientes.
- Confirmado contra fuente oficial (WebFetch `strategyquant.com/doc/quantanalyzer/portfolio-correlation-explained/`,
  2026-09-01): SQX correlaciona por **Profit/Loss agregado por período**, con "el período más
  usual es diario" — coincide con la recomendación de este informe, no con la implementación
  actual de `meta_strategy_engine.py` ni `portfolio_combiner.py`.

**Solape temporal mínimo**: se propone exigir **≥20 días calendario con actividad real
simultánea** (no 20 días de ventana total: 20 días donde AMBOS componentes tengan al menos una
operación cada uno), más estricto que el `≥4 semanas` actual de `meta_strategy_pipeline.py:162`
(equivalente a ~20-28 días, pero contado en periodos con o sin actividad, no en días con
actividad doble confirmada). Motivo: una correlación de Pearson con menos de ~20-30 observaciones
pareadas tiene un intervalo de confianza demasiado ancho para ser útil como filtro de portafolio;
el umbral actual `min_steps<=2` de `meta_strategy_engine.py:280` evita la división por casi-cero
pero no garantiza que la correlación sea *fiable*, solo que es *calculable*. Además, se debe
comprobar **solape de calendario real** (intersección de ventanas OOS por timestamp), no solo
longitud de secuencia — el caso patológico de dos componentes con OOS en fechas completamente
distintas (cero solape real) hoy pasaría sin aviso por `meta_strategy_engine.py` si ambas series
tienen ≥3 operaciones, porque solo compara longitudes, nunca fechas.

**Ventanas**: agregación por día calendario UTC (desde `entry_time_ms` real, igual que ya hace
`_weekly_aligned`) para la correlación **estática** de certificación (una sola matriz, calculada
una vez sobre todo el solape disponible — así es como opera Portfolio Master de SQX también,
confirmado por WebFetch). Para el router en vivo (§3.3) se necesita además una correlación
**rodante** (ventana de 20 días, recalculada periódicamente) para detectar cambios de régimen —
son dos usos distintos con dos ventanas distintas, ambos explícitos, nunca la misma ventana para
ambos propósitos.

**Cuándo NO_EVALUABLE** (fail-closed en cada paso, sin excepción por fichero — a diferencia de
hoy, donde `meta_strategy_engine.py` falla cerrado pero `portfolio_engine.py`/`portfolio_combiner.py`
no):
- Menos de 2 componentes certificados con `oos_returns` reales (ya implementado).
- Menos de 20 días calendario de solape de actividad real simultánea (nuevo, propuesto).
- Varianza cero en cualquier componente durante el solape (ya implementado como
  `ZERO_VARIANCE_RETURNS`).
- Correlación NaN tras el cálculo pese a pasar los filtros anteriores (ya implementado como
  `NAN_CORRELATION` en un fichero — debe ser universal, nunca `0.0`/identidad por defecto).

### 3.3 Pregunta 3 — Router dinámico: protocolo, evidencia, límites deterministas, línea roja del LLM

`orchestration/state/plan/bloques/F06_meta_router.md` ya define la FORMA correcta para la
versión ULTRA (aparcada, no descartada — `aparcado: true`, `motivo_aparcado: "Foco 100% en
FONDEO"`), y esa forma se hereda literalmente para M4/FONDEO cambiando solo el objetivo:

**Qué evidencia ven los agentes** (todo pre-calculado por código determinista; el LLM nunca ve
datos crudos de mercado sin procesar ni parámetros de ejecución):
1. Régimen por componente: volatilidad realizada reciente, tendencia, sesión horaria activa.
2. Correlación rodante entre componentes (ventana de 20 días, §3.2) con su nº de observaciones —
   para que el agente sepa si la correlación es fiable o está al borde de `NO_EVALUABLE`.
3. Telemetría en vivo del vigía: equity actual, drawdown corriente, violaciones detectadas hoy,
   distancia al límite de pérdida diaria y al trailing DD, en % del presupuesto restante.
4. Estado del ciclo de examen (`CicloFondeado`/`ReglasExamen` de `fondeo_examen.py`): fase
   (examen vs fondeada), días transcurridos, días mínimos restantes, consistencia pendiente.
5. Historial de decisiones previas del propio router, para evitar oscilación ciega.

**Cómo la salida del debate se convierte en pesos dentro de límites deterministas**: cada agente
propone un **ajuste relativo acotado** (nunca un peso absoluto en USD, nunca una orden), los
agentes se critican con la misma evidencia y el transcript completo se persiste (mandato literal
de F06: *"la decisión y su razonamiento quedan persistidos y son auditables a posteriori"*). Sin
consenso, el ajuste es 0 (fail-closed también aquí). La salida pasa por una función determinista
versionada (código puro, testeado) que: (a) aplica el ajuste sobre los pesos base de HRP/mínima-
varianza-del-examen — nunca los sustituye; (b) clampa dentro de límites duros pre-declarados
(peso mín/máx por componente, variación máxima por ciclo de rebalanceo); (c) verifica contra el
presupuesto de riesgo de la firma en el **peor caso**, no en expectativa — si el peso propuesto
podría violar el trailing DD o la pérdida diaria de la firma combinado con lo ya consumido hoy,
se recorta, pase lo que pase el debate; (d) solo entonces se traduce a tamaño de posición real.

**Qué JAMÁS puede decidir un LLM** (línea roja explícita, no implícita):
- Los límites duros en sí (peso mín/máx, variación máxima por ciclo, % de presupuesto de riesgo
  consumible) — constantes de código versionadas, cambiarlas es trabajo humano/orquestador.
- Si una cuenta reventó o no (`prop_firm_busted`) — lo decide el motor determinista
  (`EventBacktestEngine`/`reejecutar_examen_barra_a_barra`), nunca el LLM interpretando telemetría.
- El cierre mecánico de una posición por violación de regla de riesgo.
- Certificar una estrategia o meta-estrategia (11 gates + criterio 1.1 + DSR) — puro código.
- El multiplicador de apalancamiento global (`k` de `scripts/meta.py`) — fracción fija de diseño,
  no una decisión del debate en tiempo real.
- Coordinar/copiar operaciones entre cuentas cuando el ToS de la firma lo prohíbe (§3.4) — tabla
  dura por firma, nunca a discreción del debate.

**Cómo se valida**: walk-forward de cartera con holdout ciego — el mismo patrón que M2 y que ya
usa `scripts/meta.py:5-6` para el multiplicador `k` (*"el multiplicador de riesgo se elige SOLO
con la primera mitad de la serie y se aplica a ciegas a la segunda"*). Criterio de éxito heredado
literal de F06, adaptado al objetivo FONDEO: el router debe reducir `P(romper cuenta)` **y** la
varianza del examen frente a la mejor asignación estática (HRP/mínima-varianza fija, sin router)
en el holdout ciego; si no lo consigue, `SIN MEJORA` explícito (igual que M2) y no se despliega
— se sigue usando la asignación estática. Esto reutiliza literalmente el motor de mejora de M2,
tal como exige `ARQUITECTURA_MODULAR_ESTRATEGIAS.md` línea 102: *"El motor de mejora dinámico-
semántico se aplica también a la META como unidad."*

### 3.4 Pregunta 4 — Multi-cuenta: consecuencia de la prohibición MFFU

Cita literal de `orchestration/results/I4_prop_firms_hallazgos.md` §3 (fila MFFU, fuente FETCH
`https://myfundedfutures.com/terms`, 2026-09-01): *"Prohibido usar múltiples cuentas propias para
'hedge, mirror, copy, or coordinate trades in a manner that provides an unfair advantage or
manipulates simulated results'"* y *"explícitamente prohibido atribuir/transferir el rendimiento
de una cuenta a otra"* (`"you may not transfer, combine, or otherwise attribute your Account
performance... to or with any other Account or User"`). §6, ítem 6 del mismo informe marca esto
como **matiz nuevo sobre el corpus interno**, que era más optimista.

**Consecuencia directa para M4**: la meta-estrategia en su forma "varias señales, varios
activos, un solo login" es perfectamente legal — no es "copiar/coordinar entre cuentas", es
cómo opera cualquier cuenta con varias señales simultáneas. Lo que la meta **no puede hacer con
MFFU** es la variante horizontal: abrir 2+ cuentas MFFU propias y usar el router para decidir en
cuál ejecutar cada señal, replicar la misma señal en varias cuentas, o sumar el rendimiento de
varias cuentas MFFU como si fuera una sola unidad de negocio (el propio ToS prohíbe también
"atribuir/combinar" resultados entre cuentas, lo que invalida incluso una meta puramente de
reporting que trate 2 cuentas MFFU como una).

Esto **no es universal** — el mismo informe I4 documenta que TradeDay tolera "escalar
estrategia" copiando en la misma dirección (con riesgo real de falso positivo de su detector),
Take Profit Trader permite copiar hasta 5 cuentas propias, y Tradeify permite copy solo entre
cuentas propias del mismo titular en la misma dirección. **Diseño propuesto**: `services/meta/`
debe leer un campo explícito por firma (extensión de `PROP_FIRM_CATALOG`, propuesto por I4 §7,
p.ej. `allows_own_account_copy_trading: bool | "CONDITIONAL"`) antes de habilitar el modo
multi-cuenta. Dado que MFFU es la firma recomendada nº1 por I4 (mejor coste/facilidad/ausencia
de DLL) y cae en la rama restrictiva, **el modo por defecto de M4 debe ser "una sola cuenta,
multi-activo"**, y el modo "varias cuentas" debe quedar explícitamente desactivado por código
(no solo por convención) salvo confirmación por escrito de la firma concreta, tal como recomienda
I4: *"antes de escalar a multi-cuenta con MFFU, habría que confirmar por escrito con soporte que
el patrón de copia previsto no cae en su cláusula"*. El router (§3.3), si algún día opera en modo
multi-cuenta, debe llevar este chequeo de firma como uno de los límites deterministas que un LLM
nunca puede saltarse.

### 3.5 Pregunta 5 — Cómo se examina la meta como una estrategia (F07)

La meta debe pasar por el **mismo** camino que una estrategia individual, sin ramas especiales:

1. **Ledger combinado**: fusionar los ledgers reales de cada componente (ponderados por los
   pesos de M4, §3.1) en un único ledger de eventos de PnL en $, ordenado cronológicamente, sobre
   una **única cuenta compartida** (no pools de capital independientes — una cuenta prop real
   tiene una sola curva de equity).
2. **Bootstrap Monte Carlo**: pasar este ledger combinado por `scripts/fondeo_examen.py::evaluar()`
   sin ningún caso especial — la meta es, para esta función, simplemente una estrategia cuyas
   "operaciones reales" resultan de combinar varias fuentes. Obtiene `p_pasar`, `p_romper_cuenta`,
   `días-mediana/p90`, exactamente igual que hoy con una estrategia sola.
3. **Verificación honesta barra a barra — el hueco real**: `reejecutar_examen_barra_a_barra`
   (línea 477) reconstruye el blueprint de **una** estrategia sobre **una** serie de velas y
   corre `EventBacktestEngine.run_backtest()` con `prop_profile` para marcar `prop_firm_busted`
   sobre equity flotante. Hoy **no existe un equivalente a nivel de portafolio**: el motor no
   camina simultáneamente varias series de velas sincronizadas de varios instrumentos evaluando
   el drawdown trailing/pérdida diaria de la firma sobre la equity FLOTANTE COMBINADA. Dos
   caminos:
   - **(a) Correcto**: extender/envolver el motor para que camine N series de velas en paralelo y
     acumule equity flotante conjunta bar a bar contra el mismo `PropFirmProfile`. Esto toca
     `services/validation/engine/event_backtest_engine.py` o su envolvente directa — **cae bajo
     Regla #26 (sube `CURRENT_ENGINE_VERSION` + verificación de identidad 15/15)**. No lo hago
     yo: lo dejo declarado con ruta:línea exacta (`event_backtest_engine.py`, clase
     `PropFirmProfile` en línea 82, uso de `drawdown_type` en 1078-1091) como petición al
     orquestador (§7).
   - **(b) Interino, más débil, honestamente etiquetado**: correr `reejecutar_examen_barra_a_barra`
     por componente por separado y combinar solo si NINGÚN componente individualmente reporta
     `prop_firm_busted=True` en el periodo solapado. Esto **subestima el riesgo real** (no puede
     ver un drawdown combinado que excede el límite de la firma aunque ningún componente solo lo
     hubiera reventado) — debe marcarse explícitamente como cota más débil, y el veredicto
     sellado de la meta debe quedar limitado a `NO_EVALUABLE` (nunca `CUMPLE`) mientras no exista
     el motor (a) real. Esto es coherente con la propia doctrina de `determinar_veredicto_sellado`
     (§2.7): sin verificación barra a barra fiable, el veredicto es siempre `NO_EVALUABLE`.
4. **Veredicto sellado**: reutilizar `determinar_veredicto_sellado` sin modificar su lógica —
   confirmado en §2.7 que ya funciona fail-closed como se necesita.
5. **Objetivo F07 sellado** (`≥20% mensual mediana`, `P(ruina)≤20%` a 6 meses) se mide sobre el
   MISMO ledger combinado vía `evaluar_rendimiento_mensual`/`evaluar_negocio`, sin caso especial.

Esto cierra el contrato de salida que exige `ARQUITECTURA_MODULAR_ESTRATEGIAS.md` línea 107:
*"examen F07 propio (la meta se examina como una estrategia más)"* — con la salvedad honesta de
que hoy solo se puede certificar hasta el nivel (b), nunca (a), hasta que exista el motor de
portafolio bar-by-bar.

---

## 4. Software: SQX (PortfolioMaster/Composer/QuantAnalyzer) vs `services/portfolio/` propio

### 4.1 Estado real de la instalación local (no genérico, esta máquina)

Confirmado en `orchestration/results/I1_sqx_hallazgos.md:52-84` (con `sqcli.exe -license
action=info`, 2026-09-01): licencia **`StrategyQuant X Pro Build 144 (Trial)` — vence
05.09.2026**, nivel **Professional**, no Ultimate. Tabla oficial (`strategyquant.com/pricing/`,
citada en I1): **Portfolio Master/Composer limitado a 4 estrategias** en Starter y Professional,
**ilimitado solo en Ultimate** ($2.900); **QuantAnalyzer Pro license: solo Ultimate**. Confirmado
en disco por I1: no existe `QuantAnalyzer.exe` en `C:\StrategyQuantX144`, solo
`StrategyQuantX.exe`/`sqcli.exe`/`CodeEditor.exe`/`SQ_Installer.exe` — **QuantAnalyzer como
aplicación independiente no está instalado hoy en esta máquina.**

Verificado directamente en esta sesión (descomprimiendo los `.cfx`, que son ZIP):
- `C:\StrategyQuantX144\user\projects\PortfolioMaster\project.cfx` → una tarea real
  `AutomaticPortfolioBuilder`, pero con **valores de plantilla de fábrica nunca ejecutados con
  datos propios**: `DateRangeFrom=DateRangeTo=2023.11.14` (mismo día, rango nulo) y
  `<SelectedStrategies />` vacío.
- `C:\StrategyQuantX144\user\projects\PortfolioComposer\project.cfx` → `<Tasks />` completamente
  vacío. **Nunca configurado.**

### 4.2 Configuración real del Automatic Portfolio Builder (lo que SÍ hace, verificado en el XML)

```xml
<SearchType>bruteforce</SearchType>
<MinStrategies>2</MinStrategies>  <MaxStrategies>7</MaxStrategies>
<MaxStrategiesDatabank>100</MaxStrategiesDatabank>  <MaxStrategiesSector>3</MaxStrategiesSector>
<FitnessType>NetProfitIS</FitnessType>
<CorrMax>0.3</CorrMax>  <CorrType>ProfitLoss</CorrType>
<CorrSampleType>10</CorrSampleType>  <CorrPeriod>10</CorrPeriod>  <CorrAllowNegative>true</CorrAllowNegative>
<FilterOverlappingTrades>true</FilterOverlappingTrades>
<Method type="RiskFixedBalancePct"><Param key="Risk">50</Param><Param key="MaxLots">5</Param></Method>
```
Lectura crítica: `FitnessType=NetProfitIS` — el fitness por defecto de SQX para elegir el mejor
portafolio es **ganancia neta IN-SAMPLE**, no OOS ni ajustada a riesgo; esto es exactamente lo
que nuestra doctrina prohíbe usar como criterio único (sobreajuste garantizado si se usa tal
cual). `Method=RiskFixedBalancePct` — el money management de SQX es **% de riesgo fijo por
estrategia**, no ERC/HRP/mínima-varianza: SQX filtra por correlación máxima (`CorrMax=0.3`,
`CorrType=ProfitLoss` — confirma vía dato local que SQX también correlaciona por P&L, no por
equity) pero **no calcula pesos de riesgo compartido entre componentes**, cada estrategia arriesga
su propio % fijo independientemente de las demás.

Confirmado con la documentación oficial (WebFetch, 2026-09-01):
- `strategyquant.com/doc/quantanalyzer/portfolio-correlation-explained/`: series disponibles
  Profit/Loss, nº de posiciones/operaciones abiertas/cerradas; período más usual **diario**,
  seleccionable hora/día/semana/mes; función "Overlapping trades" para detectar solape; "Add
  empty periods" rellena con 0 los periodos sin operar (decisión de diseño distinta a nuestro
  fail-closed: SQX opta por completar, no por fallar).
- `strategyquant.com/blog/portfolio-master-automatic-portfolio-builder/`: evalúa "every
  combination of strategies/markets"; ranking functions personalizables vía Snippets; límite de
  estrategias por sector; la documentación oficial **no especifica** el money management —
  confirmado solo por el `.cfx` local (`RiskFixedBalancePct`).
- `strategyquant.com/quantanalyzer/portfolio-master/`: reserva datos OOS fuera de la evolución
  genética (property que nuestro propio holdout ya exige); licencia gratis limitada a 4
  estrategias, Pro ilimitado.

### 4.3 Matriz: qué certifica cada uno, qué no

| Capacidad | SQX Portfolio Master (Pro local) | `services/portfolio/` propio hoy | `services/meta/` propuesto |
|---|---|---|---|
| Búsqueda de combinación óptima | Sí, bruteforce/genético sobre `MinStrategies..MaxStrategies` | No (solo ensambla lo que se le pasa, no busca combinaciones) | Sí — grid/Nelder-Mead sobre pesos con N≤6 fijo, ver §3.1 |
| Fitness por defecto | `NetProfitIS` (IN-SAMPLE — riesgo de sobreajuste si se usa tal cual) | OOS únicamente (criterio 1.1 ya exige esto en los componentes) | OOS + Monte Carlo del examen (§3.1) |
| Correlación | Por P&L, período configurable (día por defecto), filtro `CorrMax` | Inconsistente: 2 de 4 ficheros correlacionan bien (PnL semanal), 2 mal (equity levels o índice de operación) | Unificado: PnL diario real, solape mínimo 20 días (§3.2) |
| Money management / pesos | % de riesgo fijo por estrategia (no ERC/HRP) | Inversa de volatilidad (aprox. ERC diagonal); "HRP" etiquetado pero no implementado | HRP real + mínima-varianza del examen (§3.1) |
| Verificación barra a barra de reglas prop a nivel portafolio | No documentado / no verificable sin GUI | No existe | No existe — gap declarado, requiere Regla #26 (§3.5) |
| Licencia disponible hoy | Trial Pro, caduca 05-09-2026, tope de 4 estrategias | N/A (código propio) | N/A |
| Auditoría/hash inmutable de la combinación | No documentado | Sí (`canonical_hash` SHA-256 en los 3 ficheros vivos) | Sí, obligatorio (REAL-ONLY) |

**Conclusión de software**: SQX Portfolio Master aporta una búsqueda combinatoria más rica
(bruteforce/genético sobre qué SUBCONJUNTO de estrategias combinar, no solo qué pesos) que hoy no
tenemos, y confirma por fuente independiente que correlacionar por P&L diario es el estándar de
la industria (refuerza §3.2). Pero su money management (% fijo) es más pobre que lo que ya
tenemos (inversa de volatilidad), su fitness por defecto es IN-SAMPLE (peligroso sin
reconfigurar), y no puede evaluar las reglas EXACTAS de cada prop firm sobre equity flotante
(eso es propietario nuestro, vía `EventBacktestEngine`). No sustituye a `services/meta/`; en
todo caso, la búsqueda combinatoria de SQX podría usarse en el futuro como generador de
candidatos de SUBCONJUNTO previo al ensamblado propio — pero **no es viable hoy**: la licencia
Trial caduca en ~4 días desde el informe de I1, y el tope de 4 estrategias en tier Professional
ya es más bajo que nuestro propio `MAX_COMPONENTES=6` (`meta_strategy_pipeline.py:120`).

---

## 5. Diseño propuesto de `services/meta/` (contrato, no código)

No he escrito código (mi objetivo es el diseño; además `services/meta/` no existe y el
bloqueante real de §2.6 impide validarlo con datos reales hoy). Contrato propuesto para cuando
se implemente:

```
services/meta/
  correlation.py     # PnL diario real, solape≥20 días, fail-closed universal (§3.2)
  weighting.py        # HRP (López de Prado completo) + búsqueda de mínima varianza del examen (§3.1)
  ledger_merge.py      # fusión cronológica de ledgers reales ponderados (§3.5.1)
  exam.py              # wrapper delgado sobre scripts/fondeo_examen.py — NUNCA reimplementa evaluar()
  router/
    evidence.py        # régimen, correlación rodante, telemetría del vigía (§3.3, entrada)
    debate.py           # protocolo de debate multi-agente + persistencia del razonamiento
    limits.py            # límites deterministas puros — código sin LLM, versionado, testeado
  firm_gate.py          # chequeo por firma de copy-trading multi-cuenta (§3.4) contra PROP_FIRM_CATALOG
```

Reemplaza a: `services/portfolio/{meta_strategy_engine.py, portfolio_engine.py,
portfolio_combiner.py}` y `services/api/app/factory/{portfolio_sprint_engine.py,
ultra_portfolio_engine.py}` → cuarentena (huérfanos o con fabricación activa, §2). Migra/reutiliza
la parte sana de `services/portfolio/{meta_strategy_pipeline.py, meta_ensemble_service.py}`
(alineación temporal por PnL semanal, fail-closed de correlación, hash canónico) como base,
corrigiendo la granularidad a diaria y unificando el conjunto de `certified_statuses` (hoy
`meta_ensemble_service.py:138-145` acepta 6 valores legacy que `meta_strategy_pipeline.py:48`
no reconoce — un candidato con `status="CERTIFIED_PASS"` sería visible por `POST /assemble` pero
invisible para `GET /meta-strategies`; **hallazgo nuevo, no documentado antes**). No decido yo
este reemplazo (está fuera de mi territorio de escritura hoy — es trabajo de implementación,
W6.1) pero lo dejo especificado para quien lo ejecute.

---

## 6. Lo que queda abierto, sin disimular

1. **Bloqueante real, no hipotético**: 0 candidatas certificadas hoy (§2.6). Nada de esto se
   puede validar con datos reales hasta que exista al menos una segunda certificación FONDEO.
2. **Motor de portafolio bar-by-bar**: no existe (§3.5); construirlo cae bajo Regla #26 y no es
   mi territorio — declarado como petición en §7.
3. **HRP real** (clustering + bisección recursiva) no está implementado en ningún fichero vivo
   hoy — solo la aproximación diagonal. Falta implementarlo en `services/meta/weighting.py`.
4. **Router con debate IA**: el diseño (§3.3) hereda la forma de `F06_meta_router.md`, que está
   `aparcado: true` para ULTRA por orden de Emilio. No verifiqué con Emilio si el mismo aparcado
   aplica a la versión FONDEO del router (M4) — lo trato como diseño listo para cuando se
   priorice, no como trabajo autorizado para ejecutar ya.
5. **Umbral de 20 días de solape** (§3.2) es una propuesta razonada de este informe, no un
   número ya sellado por Emilio ni por un experimento con datos reales (no hay datos reales con
   los que probarlo hoy — §2.6). Debe validarse en cuanto existan ≥2 certificadas reales.
6. **Prototipo exploratorio**: el plan permite "prototipo sobre las mejores candidatas reales NO
   certificadas, etiquetado EXPLORATORIO" mientras no haya 2 certificadas. No lo ejecuté en este
   turno porque mi objetivo era el diseño, no la implementación, y porque tocar
   `services/portfolio/` está fuera de mi territorio de escritura.

---

## 7. Peticiones al orquestador (fuera de mi territorio)

1. **Bug activo, no solo deuda de diseño**: `services/portfolio/autonomous_meta_daemon.py:91-98`
   llama a un contrato de `MetaEnsembleService.assemble_meta_portfolio()` que ya no existe
   (`meta_ensemble_service.py:182-196`) — `KeyError` garantizado en cuanto haya ≥2 candidatos
   ULTRA en las primeras 20 filas de `candidates`. Está arrancado 24/7 desde
   `services/api/app/main.py:99-100`. Recomiendo: o arreglar el mapeo de claves, o detener el
   daemon hasta que `services/meta/` lo sustituya (evita gastar ciclos en un bucle de error
   silencioso en cuanto empiece a haber candidatos).
2. **Fabricación activa hoy, no solo histórica**: `services/portfolio/portfolio_combiner.py:83-86,107`
   (correlación de niveles de equity + NaN→0.0 silencioso + techo PF=99.0) y
   `services/portfolio/portfolio_engine.py:116-118,126-127` (fallback a 10 periodos de 0,01 y
   matriz identidad fabricados) siguen violando REAL-ONLY hoy mismo, aunque el impacto práctico
   es bajo porque ambos ficheros son huérfanos (§2.1) — recomiendo cuarentena directa junto con
   `services/api/app/factory/{portfolio_sprint_engine.py, ultra_portfolio_engine.py}`
   (`correlation_score=0.18` hardcodeado en `portfolio_sprint_engine.py:93`, no cubierto por
   ningún test).
3. **Regla #26**: construir el motor de verificación barra a barra a nivel de portafolio (§3.5,
   punto 3a) toca `services/validation/engine/event_backtest_engine.py` (clase `PropFirmProfile`,
   línea 82). No lo aplico yo — lo reporto para que el carril del motor lo priorice cuando W6
   se active, con sube de `CURRENT_ENGINE_VERSION` + verificación de identidad 15/15.
4. **Documentos desactualizados detectados** (por si el orquestador quiere corregirlos en el
   mismo commit que cierre este expediente): `orchestration/state/plan/bloques/F07_fondeo_examenes.md`
   afirma que la verificación barra a barra "no gatea nada" — REFUTADO por el código actual
   (§2.7); `orchestration/state/PLAN_LOCAL_FONDEO.md:108` (W4.2) sigue listando
   `meta_ensemble`/`meta_strategy_pipeline` como pendientes de quitar hardcode `5.4.0` —
   CONFIRMADO como ya resuelto para esos dos ficheros (§2.5).
5. **Confirmación pendiente con Emilio** (no la decido yo): si el aparcamiento de F06 (ULTRA)
   también aplica al router FONDEO/M4, o si M4 puede avanzar su implementación real antes de
   que ULTRA se retome.
