# M3 — Plan de aterrizaje del catálogo de prop firms re-verificado

**Subagente:** carril FONDEO · **Fecha:** 2026-09-01 · **Tipo:** SOLO LECTURA (plan, cero código escrito)

> Este documento responde a las 4 preguntas del contrato. No se ha creado ningún fichero en
> `services/fondeo/`, ningún router nuevo, ni ningún test: la tarea, tal como cierra su propio
> contrato ("SALIDA: ... SOLO LECTURA"), es investigar y planear, no implementar. Todo lo que
> sigue son **propuestas** con evidencia — la implementación es trabajo de una fase M3
> siguiente, ya prevista en `orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md` línea 87.

---

## 0. Resumen ejecutivo

La pregunta del contrato ya tenía una respuesta parcial escrita en el propio repo, antes de que
yo tocara nada:

> `orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md:87` — *"Código | `services/fondeo/`
> consolidando `fondeo_examen` + `prop_firms` + el simulador barra a barra del motor 5.15.0. El
> catálogo de firmas (`PROP_FIRM_CATALOG`) vive AQUÍ con test contra ToS citado — y se sirve a
> la web por API (muere `lib/prop-firms.ts` de 4.307 LOC en cliente)"*

Mi investigación (`grep -rn "PROP_FIRM\|prop_firm" services/ scripts/ contracts/`) confirma que
el "fallo histórico nº1" que pide documentar el contrato es real y **peor de lo que sugiere el
enunciado**: no hay dos catálogos duplicados, hay **cinco**, ninguno de acuerdo con los otros
cuatro, y solo uno de ellos alimenta de verdad al motor de backtest:

| # | Fichero | LOC | Consumidor real | ¿Tiene fuente/cita por dato? |
|---|---|---|---|---|
| 1 | `services/exploitation_engines/prop_firm_engine.py::PROP_FIRM_CATALOG` | 417 (fichero completo) | **El motor**, vía `PropFirmRules.to_engine_profile()` → `PropFirmProfile` → `run_backtest(prop_profile=...)`. También `scripts/fondeo_examen.py` (Monte Carlo del examen) | **No.** Ni una URL, ni una fecha, ni una cita en todo el fichero |
| 2 | `services/api/app/api/prop_firms.py::PROP_FIRMS_DATABASE` | 2.635 | `GET /api/v1/prop-firms` — **cero consumidores** (verificado, ver §1.3) | No (`"last_verified": "2026-08-02"` como único metadato, sin URL por parámetro) |
| 3 | `services/api/app/db/seed_prop_firms.py::PROP_FIRMS_CATALOG` | 1.718 | `GET /api/v1/providers` (auto-seed en SQLite) | Parcial: cada entrada trae `source_url` + `verified_at="2026-08-21"`, pero sin cita textual ni por-parámetro (una URL para ~30 campos) |
| 4 | `apps/web/lib/prop-firms.ts::ALL_PROP_FIRM_ACCOUNTS` | 4.307 (fichero completo) | La página `/prop-firms` completa (8 componentes React), en el **cliente**, cero backend | No |
| 5 | `contracts/portfolio.py::PropChallengeConfig` | — | Solo tests (`test_p5_fondeo_evaluator.py`, `test_canonical_contracts.py`); no está cableado al motor | No — son valores `Field(default=...)` genéricos |

Los números **no coinciden entre sí**, y donde los pude contrastar contra la re-verificación de
fuente primaria de `I4_prop_firms_hallazgos.md` (2026-09-01), varios están **directamente
equivocados** frente a la cita oficial más reciente (detalle en §4).

**Plan en una frase:** el catálogo re-verificado de I4 §7 se aterriza en un módulo nuevo,
`services/fondeo/prop_firm_catalog.py`, con dataclasses/BaseModel `SourceRef`-tipadas; un router
nuevo `services/api/app/api/prop_firms_router.py` lo sirve tal cual en
`GET /api/v2/prop-firms` y `GET /api/v2/prop-firms/{id}`; y **el catálogo que alimenta al motor
(#1 de la tabla) NO se toca en esta fase** porque hacerlo altera las operaciones que produce
`event_backtest_engine.py` y dispara la Regla #26 — eso es una petición al orquestador, con
`ruta:línea` exactas de cada valor sin fuente, no algo que yo ejecute.

---

## 1. Pregunta 1 — Dónde vive el catálogo y cómo se convierte en fuente única

### 1.1 Ubicación propuesta

`services/fondeo/prop_firm_catalog.py` (módulo nuevo, `services/fondeo/` no existe hoy —
confirmado: `ls services/fondeo/` → `No such file or directory`). Encaja exactamente con el
plan ya escrito en `ARQUITECTURA_MODULAR_ESTRATEGIAS.md:87` citado arriba, que ya reserva ese
paquete para consolidar `fondeo_examen` + `prop_firms` + el catálogo. Esta tarea (M3, catálogo)
es el primer ladrillo de esa consolidación — **no** la consolidación completa (mover
`scripts/fondeo_examen.py` entero a `services/fondeo/` es una tarea propia, fuera de mi
territorio de escritura hoy, que solo toca `services/fondeo/**` (nuevo), el router y tests).

Estructura de módulo propuesta:

```
services/fondeo/
  __init__.py                  # exporta PROP_FIRM_CATALOG, PropFirm, SourceRef, get_firm()
  prop_firm_catalog.py         # el catálogo re-verificado (adaptación de I4 §7)
```

### 1.2 Forma de los datos: adaptación de I4 §7, no copia literal

I4 §7 propone `@dataclass` puro. Para servir el catálogo por FastAPI sin una capa de traducción
adicional (y para no reinventar lo que ya hace el resto del repo:
`services/api/app/api/prop_firms.py` y `services/exploitation_engines/prop_firm_engine.py`
usan ambos `pydantic.BaseModel`), la propuesta es portar las mismas clases de I4 §7 a
`pydantic.BaseModel` en vez de `@dataclass` — mismos campos, misma semántica de
`Optional[...] = None` para "no verificable", mismo `Confidence = Literal["fetch",
"ws_official", "unverified"]`, pero con `model_config = ConfigDict(frozen=True, extra="forbid")`
(mismo patrón que `contracts/portfolio.py:100` `PropChallengeConfig`) para que el catálogo sea
inmutable en runtime y FastAPI lo sirva como `response_model` sin capa extra de serialización.

Diferencia deliberada frente a I4 §7: **no se copian los 6 `PropFirm(...)` literales de I4 tal
cual** sin revisión — hay que decidir, dato a dato, si `confidence="unverified"` con `source=
SourceRef(url="", ...)` (como aparecen Apex-DLL, TradeDay-DLL, TPT-drawdown, Tradeify entero)
se sirve como `None` puro (mi recomendación: si no hay URL, el campo raíz es `None`, sin
`SourceRef` fantasma con `url=""`) o como un `SourceRef` explícito con `confidence="unverified"`
para que la API pueda mostrar "buscado y no encontrado" en vez de "nunca se buscó". Esta es una
decisión de producto (qué le enseña la web al usuario cuando un dato no existe) que dejo
señalada, no resuelta — es una `PETICIÓN AL ORQUESTADOR` menor, ver §5.

### 1.3 Cómo se convierte en la ÚNICA fuente — plan por consumidor

| Consumidor actual | Qué pasa |
|---|---|
| **API `/api/v2/prop-firms`** (nuevo) | Lee directamente `services.fondeo.prop_firm_catalog.PROP_FIRM_CATALOG`. Es la ÚNICA fuente desde el día 1 porque no existe hoy — no hay migración, es creación. |
| **Web `/prop-firms`** (`apps/web/lib/prop-firms.ts`, 4.307 LOC, `apps/web/app/prop-firms/page.tsx` + 7 componentes) | **No lo toco** (fuera de mi territorio). Verificado con `grep -rln "lib/prop-firms" apps/web/app apps/web/components`: 8 ficheros importan `ALL_PROP_FIRM_ACCOUNTS` directamente, cero `fetch` a ningún endpoint. `ARQUITECTURA_MODULAR_ESTRATEGIAS.md:87` ya decreta que este fichero "muere". Propuesta para el carril WEB (petición, no ejecución): sustituir el `import` estático por un `fetch("/api/v2/prop-firms")` (o un hook `useSWR`/`useEffect`), mapear `PropFirm` (nuevo, con `SourceRef`) al `PropFirmAccount` que ya consumen los 7 componentes, y solo entonces mover `lib/prop-firms.ts` a `cuarentena/`. Es un cambio de forma de datos no trivial (el TS actual tiene 36 atributos "físicos" por cuenta con cupones/afiliados que el catálogo re-verificado de I4 no cubre — ver §1.4) — **no es un simple `s/import/fetch/`**. |
| **`/api/v1/prop-firms`** (`services/api/app/api/prop_firms.py::PROP_FIRMS_DATABASE`) | Verificado sin consumidores: `grep -rln "/prop-firms\|api/v1/prop\|api/v2/prop" apps/web --include=*.ts --include=*.tsx` solo encuentra `href="/prop-firms"` (navegación de página, no llamada a API) en `apps/web/app/fondeo/page.tsx:94`, `apps/web/app/ultra/page.tsx:349`, `Header.tsx:30`, `Sidebar.tsx:43` — ninguno hace `fetch` al endpoint. Además el endpoint `GET /prop-firms/research-doc` (línea 2620) lee una ruta Linux hardcodeada (`/home/ubuntu/workspace/pro/trading/...`) que no existe en este PC Windows: ya está roto hoy. Propuesta: **candidato a cuarentena completa** (fichero + su registro en `routes.py:41,45`), pero como no puedo descartar un consumidor externo al repo (un script de Emilio, un bookmark), lo dejo como petición al orquestador, no como ejecución mía — `services/api/app/api/prop_firms.py` no está en mi territorio de escritura. |
| **`/api/v1/providers`** (`services/api/app/db/seed_prop_firms.py::PROP_FIRMS_CATALOG`, 1.718 LOC) | Mismo problema conceptual (reglas de firma + economía, otra vez, con otra forma), pero con un consumidor real parcial: `apps/web/app/prop-firms/components/AISyncStatusBar.tsx:28` llama a `POST /api/v1/providers/ai-update` (no al `GET /providers` que sirve el catálogo — ese widget solo muestra un texto de estado con cupones, no lista cuentas). Además `POST /providers/sync` (`providers_router.py:189-215`) reescribe `verified_at` a la fecha de HOY en cada llamada **sin volver a consultar ninguna fuente** — repinta la fecha de "verificado" sin re-verificar nada, y responde `"Sincronización completada exitosamente"`. Es un patrón de falsa frescura que vale la pena que el orquestador conozca aunque no sea literalmente un dato inventado (los números no cambian, solo la fecha que dice que se comprobaron). Fuera de mi territorio (`services/api/app/db/`, `services/api/app/api/providers_router.py`). |
| **`services/exploitation_engines/prop_firm_engine.py::PROP_FIRM_CATALOG`** (el que alimenta el motor) | **Deliberadamente NO se toca en esta fase.** Ver §4 — Regla #26. |
| **`contracts/portfolio.py::PropChallengeConfig`** | Sin acción propuesta: no está cableado a ningún consumidor de producción (`grep -rln "PropChallengeConfig"` solo devuelve `contracts/portfolio.py`, `contracts/__init__.py` y dos ficheros de test). Es un contrato Pydantic con valores por defecto genéricos usados para construir objetos de prueba explícitos — eso es legítimo per regla #1 del contrato ("un test unitario con un objeto construido explícitamente SÍ es legítimo"), no reclama ser "el catálogo". Sin cambios. |

### 1.4 Aviso honesto: el catálogo de I4 (6 firmas, reglas de riesgo/ToS) **no cubre** lo que
`lib/prop-firms.ts` necesita para reemplazar la página web tal cual está hoy

`apps/web/lib/prop-firms.ts:48-107` define `PropFirmAccount` con 36 campos por **cuenta**
individual (no por firma): `affiliate_url`, `active_coupon_code`, `discount_percentage`,
`exam_price_promo_usd`, `reset_fee_usd`, `monthly_renewal_usd`, etc. — datos comerciales de
afiliación y cupones que **I4 explícitamente no investigó** (el contrato de I4 pedía reglas de
riesgo/ToS/automatización desde fuente primaria oficial, no páginas de afiliados ni cupones
promocionales activos). `ALL_PROP_FIRM_ACCOUNTS` tiene 65+ cuentas (múltiples tamaños por firma:
25K/50K/100K/150K/etc.); el catálogo de I4 §7 solo tiene **una entrada por firma** (6 firmas),
sin desglose por tamaño de cuenta salvo en los diccionarios `amount_by_size`/
`max_contracts_by_size`.

Consecuencia para el plan: el nuevo `services/fondeo/prop_firm_catalog.py` **no es un
reemplazo 1:1** de `lib/prop-firms.ts` — es la fuente de verdad de **reglas de riesgo y
compatibilidad de automatización**, que es exactamente lo que necesita el motor y el examen
(M3 tal como lo define la arquitectura: "con qué firma, en qué horarios, con qué tamaño y con
qué probabilidad real de pasar"). La parte comercial (cupones, afiliados, landing de venta) es
un catálogo *distinto*, de otro dominio, que si se necesita debería re-verificarse aparte y
vivir en otro módulo — no meterlo a presión dentro de `PROP_FIRM_CATALOG` para no ensuciar la
trazabilidad de fuente por parámetro que es la razón de ser de este catálogo. Esto es una
petición/aviso al orquestador, no algo que yo resuelva aquí.

---

## 2. Pregunta 2 — Forma del endpoint

### 2.1 Contrato propuesto

```
GET /api/v2/prop-firms
GET /api/v2/prop-firms/{firm_id}
```

Router nuevo: `services/api/app/api/prop_firms_router.py`, exportando `router = APIRouter(
prefix="/prop-firms", tags=["v2-prop-firms"])` (mismo patrón interno de `prefix=` dentro del
propio router que ya usa el `prop_firms_router` legacy en `services/api/app/api/prop_firms.py:6`
— así el `include_router` en `main.py` solo necesita aportar `/api/v2`, igual que el resto del
bloque `# V2` de `services/api/app/main.py:165-181`).

**Las 2 líneas exactas de `main.py`** (mi único territorio de escritura dentro de ese fichero):

```python
# junto al bloque de imports v2, p.ej. tras la línea 41 (gateways_router):
from services.api.app.api.prop_firms_router import router as prop_firms_router_v2

# junto al bloque "# V2" (main.py:165), p.ej. tras la línea 181 (real_data_router alias):
app.include_router(prop_firms_router_v2, prefix="/api/v2", tags=["v2-prop-firms"])
```

Nombre `prop_firms_router_v2` deliberado (no `prop_firms_router` a secas): el módulo legacy
`services/api/app/api/prop_firms.py:6` ya define una variable module-level llamada
`prop_firms_router`. Aunque hoy no colisionan (ninguno de los dos se importa hoy en el mismo
namespace — `main.py` no importa el legacy, solo `routes.py` lo hace), usar un alias distinto
en el `import` de `main.py` es la única forma de que un futuro `grep "prop_firms_router"` no
tenga que adivinar cuál de los dos routers es cada aparición. El nombre exportado por el módulo
nuevo en sí puede seguir siendo `router` (convención mayoritaria del repo: revisar
`strategy_binding_router.py`, `discovery_router.py`, etc. exportan `router`, no un nombre
propio) — el alias se resuelve en el `import`, no en el módulo.

### 2.2 Modelos de respuesta

Reutilizan tal cual las clases de `services.fondeo.prop_firm_catalog` (§1.2) como
`response_model`, sin capa de traducción intermedia — exactamente lo que pide la pregunta del
contrato: *"devolviendo valores CON su SourceRef y confidence"*. Ejemplo de forma (no de
fichero, ilustrativo):

```python
from fastapi import APIRouter, HTTPException
from services.fondeo.prop_firm_catalog import PROP_FIRM_CATALOG, PropFirm

router = APIRouter(prefix="/prop-firms", tags=["v2-prop-firms"])

@router.get("", response_model=list[PropFirm])
def list_prop_firms() -> list[PropFirm]:
    return list(PROP_FIRM_CATALOG.values())

@router.get("/{firm_id}", response_model=PropFirm)
def get_prop_firm(firm_id: str) -> PropFirm:
    firm = PROP_FIRM_CATALOG.get(firm_id)
    if firm is None:
        # REAL-ONLY / fail-closed: 404 explícito, nunca la primera firma del dict
        # ni un objeto vacío con campos None a modo de "firma no encontrada".
        raise HTTPException(
            status_code=404,
            detail=f"'{firm_id}' no está en el catálogo. Disponibles: "
                   f"{', '.join(sorted(PROP_FIRM_CATALOG))}",
        )
    return firm
```

Nótese el `HTTPException(404, ...)` con la lista de claves válidas en el mensaje —mismo patrón
fail-closed que ya usa `find_prop_firm()` en
`services/exploitation_engines/prop_firm_engine.py:277-314` para el catálogo del motor. No hay
`GET /prop-firms/research-doc` ni `POST /prop-firms/refresh-database` en el diseño nuevo: el
primero lee una ruta de fichero que no existe en este PC (`prop_firms.py:2619`) y el segundo es
un endpoint que finge sincronizar sin sincronizar nada (`prop_firms.py:2627-2633`, siempre
`"status": "success"`, nunca vuelve a tocar ninguna fuente) — ninguno de los dos patrones se
replica en v2.

### 2.3 Claves del catálogo (`firm_id`)

`topstep`, `apex`, `mffu`, `tradeday`, `take_profit_trader`, `tradeify` — literalmente las
claves que ya usa `I4_prop_firms_hallazgos.md:7` sección 7 en su diccionario
`PROP_FIRM_CATALOG`. Se mantienen tal cual para no introducir una tercera convención de nombres
(el catálogo del motor usa `TOPSTEP_50K`, `APEX_25K`, etc. — por tamaño de cuenta, mayúsculas;
el de `seed_prop_firms.py` usa `mffu_rapid_25k` — por cuenta también). El catálogo de M3 es
**por firma**, no por cuenta (ver aviso §1.4), así que sus claves son solo el nombre de la
firma en minúsculas con guión bajo.

---

## 3. Pregunta 3 — Estrategia de tests

Territorio: `tests/test_prop_firm_*.py`. Ya existe `tests/test_prop_firm_risk_and_hard_gates.py`
(otro carril/tarea, sobre `services/validation/prop_firm_risk_engine.py` — no lo toco ni lo
sustituyo). Propongo dos ficheros nuevos, sin colisión de nombre:

### 3.1 `tests/test_prop_firm_catalog.py` — invariantes del catálogo en sí

1. **Cada valor no-`None` tiene fuente.** Recorrer recursivamente cada instancia `PropFirm` del
   catálogo: para cada campo hoja no-`None` que representa un dato investigado (no un
   `firm_id`/`name` literal), su `SourceRef.confidence` está en
   `{"fetch", "ws_official"}` y `SourceRef.url` no está vacía. Esto es la traducción directa a
   test de la regla de método de I4 (`I4_prop_firms_hallazgos.md` sección 0, punto 3): un dato
   con `confidence="unverified"` **debe** tener su valor raíz en `None`, nunca un número.
2. **Ningún `None` sustituido por el corpus 08-2026.** Lista explícita de `(firm_id, ruta de
   campo)` que I4 §8 marca como `NO VERIFICABLE` y que por tanto deben seguir siendo `None` en
   el catálogo de M3 — comparando contra `docs/Fondeo/BASE_DATOS_EMPRESAS_FONDEO_FUTUROS_2026-08-02.md`
   para asegurar que el valor del corpus antiguo no se coló por descuido de copy-paste:
   - `apex.drawdown.amount_by_size is None` (I4 §1.2, tabla, fila "Importes de drawdown por
     tamaño") — el corpus SÍ tiene esta cifra (`docs/Fondeo/...` sección 10.6: "Drawdown EOD:
     2.000 USD"); el test falla si alguien la copia sin re-verificarla.
   - `apex.economics.eval_price_50k is None` (I4 §2, fila Apex, celda "Precio evaluación 50K")
   - `tradeday.economics.eval_price_50k is None` (I4 §2, fila TradeDay)
   - `take_profit_trader.daily_loss_limit.amount_by_size is None` — I4 explícita: *"Corpus
     interno menciona $1,100 en 50K — no lo reproduzco como propio porque no lo verifiqué yo
     mismo"* (`I4_prop_firms_hallazgos.md`, sección 1.5, fila "Daily Loss Limit"). Test
     específico: este valor NO puede ser `1100.0` en el catálogo.
3. **Topstep y TradeDay con `automation.vps_allowed=False`** (pedido explícitamente por el
   contrato de esta tarea, y confirmado por fetch directo en I4 §7:
   `PROP_FIRM_CATALOG["topstep"].automation.vps_allowed=False` y
   `PROP_FIRM_CATALOG["tradeday"].automation.vps_allowed=False`, ambos citando el ToS oficial
   textual — *"The use of VPS, VPNs, and remote servers is prohibited by Topstep's Terms of
   Use"* y *"TradeDay does not allow the use of virtual private servers (VPS)"*). Este es el
   hallazgo más importante de I4 (sección 3, "hallazgo más importante de todo el informe") y el
   único que el contrato pide verificar por test explícito nombrando las dos firmas.
4. **`PROP_FIRM_CATALOG` tiene exactamente las 6 claves esperadas**, ni una firma fantasma ni
   una desaparecida (`{"topstep", "apex", "mffu", "tradeday", "take_profit_trader",
   "tradeify"}` == `set(PROP_FIRM_CATALOG)`).
5. **Inmutabilidad**: si se implementa con `model_config = ConfigDict(frozen=True)` (§1.2), un
   test que intenta mutar un campo del catálogo importado debe lanzar (evita que un consumidor
   corrompa el catálogo global en memoria compartida entre requests de FastAPI).

### 3.2 `tests/test_prop_firm_catalog_api.py` — contrato HTTP

Usando `TestClient` de FastAPI sobre la `app` real (patrón ya usado en
`services/api/tests/test_autopilot.py:20`, que importa `services.api.app.api.routes` — mismo
estilo de test de integración de router):

1. `GET /api/v2/prop-firms` → `200`, longitud de la lista == `len(PROP_FIRM_CATALOG)` == 6.
2. `GET /api/v2/prop-firms/{firm_id}` → `200` para cada una de las 6 claves reales, y el
   `firm_id` del cuerpo de respuesta coincide con el de la URL.
3. `GET /api/v2/prop-firms/no-existe-esta-firma` → `404`, con el listado de firmas válidas en
   el `detail` (fail-closed, no un objeto vacío ni una lista con la primera firma por defecto).
4. Cada firma devuelta por `GET /api/v2/prop-firms/{firm_id}` conserva, en JSON, el mismo
   invariante fuente-por-valor del test 3.1.1 — asegura que la serialización Pydantic no
   "aplana" ni descarta el campo `source` en el camino HTTP (riesgo real si alguien usa
   `response_model` con un modelo distinto al de almacenamiento sin darse cuenta).

Todos estos tests usan **datos reales** del catálogo importado (no fixtures inventadas) — es
exactamente el caso que la regla #1 del contrato permite explícitamente para código de
infraestructura, pero aquí ni siquiera hace falta la excepción: se está probando la fuente de
verdad real, no un objeto de prueba construido a mano.

---

## 4. Pregunta 4 — Qué pasa con el catálogo previo (el que de verdad importa: el del motor)

Esta es la pregunta más delicada del contrato porque toca la Regla #26, y la respuesta correcta
es **no tocarlo yo**, con evidencia de por qué.

### 4.1 Cadena de consumo verificada

```
services/exploitation_engines/prop_firm_engine.py:108  PROP_FIRM_CATALOG (18 entradas, por cuenta)
        │  PropFirmRules.to_engine_profile()  (prop_firm_engine.py:73-101)
        ▼
services/validation/engine/event_backtest_engine.py:82  PropFirmProfile
        │  run_backtest(..., prop_profile=PropFirmProfile(...))
        ▼
        altera prop_firm_busted / prop_firm_violations / qué operaciones se cierran y cuándo
```

Y en paralelo, el mismo catálogo alimenta el simulador Monte Carlo del examen:

```
services/exploitation_engines/prop_firm_engine.py:108  PROP_FIRM_CATALOG
        │  scripts/fondeo_examen.py:47  _reglas_base_desde_firma()  — "Fuente ÚNICA"
        │  (docstring literal: "evita que las dos fases (examen y vida fondeada) deriven
        │   la misma firma con fórmulas distintas")
        ▼
scripts/fondeo_examen.py:100  ReglasExamen.desde_firma()  →  simular_examen()
scripts/fondeo_examen.py:741  rules_efectivas = PropFirmRules(...)  →  .to_engine_profile()
        │  (usado en reejecutar_examen_barra_a_barra(), que sí llama al motor real)
```

`services/exploitation_engines/prop_firm_engine.py:11-16` lo dice explícitamente en su propio
comentario: *"PropFirmProfile es el DTO OPT-IN que run_backtest(..., prop_profile=...) consume
para evaluar reglas prop SOBRE EQUITY FLOTANTE"*. Los campos concretos que viajan sin
transformar desde `PropFirmRules` hasta `PropFirmProfile` (`prop_firm_engine.py:95-101`) son:
`max_total_drawdown_usd`, `drawdown_type`, `daily_loss_limit_usd`, `session_cutoff_utc`
(derivado de `session_cutoff_time`), `account_size_usd`.

**Conclusión: corregir cualquiera de esos 5 campos en `PROP_FIRM_CATALOG`
(`prop_firm_engine.py`) es, literalmente, "alimentar sus señales"** — cambia cuándo el motor
considera reventada una cuenta prop, lo cual cambia qué operaciones produce
`event_backtest_engine.py` para cualquier backtest que se ejecute con `prop_profile` activado.
Eso es exactamente el supuesto que dispara la Regla #26 (*"cualquier cambio que altere las
operaciones que produce el motor de backtest ... y lo que alimenta sus señales exige subir la
versión del motor + verificación de identidad 15/15"*). **PARO aquí, no lo aplico.**

### 4.2 Evidencia de que hace falta corregirlo (para quien sí tenga mandato de motor)

Contrastando `services/exploitation_engines/prop_firm_engine.py` (sin fuente, sin fecha) contra
`I4_prop_firms_hallazgos.md` (fuente primaria, 2026-09-01), en las 4 firmas de 50K que se
solapan entre ambos catálogos:

| Campo | `prop_firm_engine.py` (ruta:línea) | Valor sin fuente | I4 §7 (re-verificado, con cita) | Discrepancia |
|---|---|---|---|---|
| Topstep 50K · `daily_loss_limit_usd` | `prop_firm_engine.py:142` | `1000.0` | `daily_loss_limit.amount_by_size=None` — I4 confirma que el DLL *existe* pero la cifra exacta es `NO VERIFICABLE` (`I4_prop_firms_hallazgos.md` sección 1.1, fila DLL: *"no se especifica textualmente si es solo realizado o incluye flotante"*, sin cifra en USD citada) | **Sin respaldo** — el motor usa un número que I4 no pudo confirmar por fuente oficial |
| MFFU 50K · `consistency_pct` | `prop_firm_engine.py:155` | `40.0` | `50.0`, `applies_to="eval_only_lifts_when_funded"` (I4 §7, fuente `myfundedfutures.com/plans/rapid`, `[FETCH]`) | **Contradicción directa**, fuente `[FETCH]` de máxima confianza |
| Tradeify 50K · `consistency_pct` | `prop_firm_engine.py:167` | `30.0` | `40.0` (I4 §7, `[WS-OFICIAL]`) | **Contradicción directa** |
| Tradeify 50K · `daily_loss_limit_usd` | `prop_firm_engine.py:178` (bloque `FUNDEDNEXT_FUTURES_50K`, no Tradeify — ver nota) | — | Tradeify SÍ tiene DLL en su plan "Growth" (I4 §1.6, fila DLL: *"Existe en Growth, Lightning y Select Daily Funded"*) pero la entrada `TRADEIFY_50K` del motor (`prop_firm_engine.py:160-171`, `firm_name="Tradeify 50K Growth"`) trae `daily_loss_limit_usd=None` | **Contradicción**: el motor llama a la cuenta "Growth" (que sí tiene DLL según I4) pero le pone `None` |
| Apex 50K · `max_total_drawdown_usd` | `prop_firm_engine.py:188` | `2500.0` | `amount_by_size=None` — I4 marca el importe de drawdown de Apex por tamaño explícitamente `NO VERIFICABLE` (bloqueo 403 de Cloudflare en todo el dominio, ver I4 sección 1.2 y sección 8) | **Sin respaldo** — Apex es la firma peor documentada de las 6 en I4, y el motor tiene una cifra igualmente sin fuente |
| Todas las firmas · `session_cutoff_time` | p.ej. `prop_firm_engine.py:119,131,145,157,169,181,193` | `"16:59 EST"` / `"16:10 EST"` fijos, sin cita | Solo Topstep (15:10 CT = 16:10 EST, coincide) y TradeDay (10 min antes del cierre de cada sesión — no es una hora fija "HH:MM", el motor lo modela como si lo fuera) tienen fuente `[FETCH]` en I4; MFFU, Apex, Take Profit Trader y Tradeify están marcados `NO VERIFICABLE` en I4 (sección 8: *"Flat time obligatorio solo se confirmó por fetch directo para Topstep y TradeDay... Para Apex, MFFU, Take Profit Trader y Tradeify queda NO VERIFICABLE"*) | El motor tiene una hora exacta para las 4 firmas que I4 no pudo verificar — ese número salió de algún sitio (probablemente el corpus del 2 de agosto), pero no lleva cita |

Nota sobre la fila Tradeify/DLL: **la propia estructura del catálogo del motor mezcla firmas y
planes sin dejarlo explícito** — `TRADEIFY_50K` no distingue entre "Growth" (con DLL, según I4)
y "Select Flex" (sin DLL, según I4) a pesar de que `firm_name` dice literalmente "Tradeify 50K
Growth". Esto no es solo un dato sin fuente, es una **ambigüedad de producto** que ya causó una
discrepancia real.

### 4.3 Lo que NO propongo

No propongo que el catálogo del motor use directamente los campos `drawdown.amount_by_size`,
etc. del nuevo `services/fondeo/prop_firm_catalog.py` en esta fase, aunque estructuralmente
sería la solución más limpia (una sola fuente para ambos catálogos) — porque **la conversión
en sí, aunque el dato de origen sea mejor, sigue siendo un cambio que altera las operaciones del
motor** para cualquier firma cuyo valor efectivo cambie. Eso exige el mismo trámite de la Regla
#26 sea cual sea el origen del número nuevo.

### 4.4 Petición concreta al orquestador (no ejecutada por mí)

1. Asignar a un carril con mandato sobre `services/validation/engine/event_backtest_engine.py`
   y `services/exploitation_engines/prop_firm_engine.py` la tarea de: (a) decidir, campo a
   campo, qué valores de `PROP_FIRM_CATALOG` (motor) se corrigen con los de
   `services/fondeo/prop_firm_catalog.py` (nuevo, una vez exista) y cuáles quedan
   deliberadamente como aproximación documentada (con un comentario que ya no diga "sin
   fuente" sino "aproximación X, ver discusión Y"); (b) subir `CURRENT_ENGINE_VERSION` en
   `services/engine_version.py:93` (hoy `5.17.0`); (c) re-ejecutar
   `scripts/verificacion_f02.py` y confirmar 15/15 idénticas donde deban serlo (la doctrina del
   propio fichero, `engine_version.py:74`, ya covers el patrón: *"15/15 celdas ... idénticas...
   ninguna es forex"* — aquí en cambio SÍ cambiarán las celdas de perfil `prop_profile`, así que
   probablemente el criterio de "15/15 idénticas" no aplica literalmente a este cambio y hay que
   definir el criterio de verificación de identidad correcto para un cambio que SÍ pretende
   alterar el resultado de las celdas con perfil prop — es una decisión de diseño de la
   verificación, no solo de ejecutarla).
2. Decidir qué hacer con la ambigüedad Growth/Select Flex de Tradeify (§4.2) antes de tocar el
   motor — si el catálogo del motor va a seguir teniendo una sola entrada por firma en vez de
   por plan, hay que documentar explícitamente qué plan representa cada entrada.

---

## 5. Peticiones al orquestador — resumen

1. **Quarantine candidato**: `services/api/app/api/prop_firms.py` completo (2.635 LOC,
   `PROP_FIRMS_DATABASE`) — cero consumidores internos verificados, endpoint
   `/research-doc` roto en este PC. Fuera de mi territorio de escritura.
2. **Revisión de duplicidad**: `services/api/app/db/seed_prop_firms.py::PROP_FIRMS_CATALOG`
   (1.718 LOC) + `providers_router.py` — mismo dominio conceptual que el catálogo M3, con el
   patrón de falsa frescura de `POST /providers/sync` (reescribe `verified_at` a hoy sin
   re-consultar ninguna fuente, `providers_router.py:189-215`). Fuera de mi territorio.
3. **Migración de la web**: `apps/web/lib/prop-firms.ts` (4.307 LOC) + los 8 ficheros que lo
   importan (`page.tsx` + 7 componentes en `apps/web/app/prop-firms/components/`) deben pasar a
   consumir `GET /api/v2/prop-firms` — pero el catálogo de M3 (reglas de riesgo/ToS, 6 firmas)
   **no cubre** los 36 campos comerciales por cuenta (cupones, afiliados, 65+ cuentas por
   tamaño) que la página actual muestra (§1.4). Es una migración de producto, no un
   `find-and-replace`, y pertenece al carril WEB (posible continuación de AG-11, que hizo la
   poda de `apps/web` hoy mismo — `cuarentena/web_poda_20260901/MOTIVO.md` confirma que
   `/prop-firms` sobrevivió esa poda por estar dentro de la misión FONDEO actual).
4. **Motor** (§4.4): reconciliar `services/exploitation_engines/prop_firm_engine.py::
   PROP_FIRM_CATALOG` con los datos re-verificados de I4, con subida de versión de motor +
   15/15, para el carril que tenga mandato sobre `event_backtest_engine.py`.
5. **Decisión de producto menor** (§1.2): si un campo `NO VERIFICABLE` de I4 se sirve como
   `None` puro o como un objeto `SourceRef(confidence="unverified")` explícito en la API — no
   bloquea la implementación, pero conviene decidirlo antes de escribir el módulo para no
   tener que romper el contrato de la API después de que la web ya lo consuma.

---

## 6. Evidencia — comandos ejecutados (resumen, salida literal en el cuerpo del informe)

- `ls services/fondeo/` → `No such file or directory` (el módulo no existe hoy).
- `grep -rn "PROP_FIRM\|prop_firm\|PropFirm\|PropChallenge" services/ scripts/ contracts/` →
  localiza los 5 catálogos de la tabla §0 (salida completa citada en el cuerpo del documento).
- `sed -n '1,90p' services/api/app/api/prop_firms.py` y `sed -n '2600,2635p' ...` → confirma
  `PROP_FIRMS_DATABASE`, `research-doc` (ruta Linux hardcodeada) y `refresh-database` (no hace
  nada real).
- `grep -n "api.routes\b" services/` + lectura de `legacy_compat_router.py:12,31` → confirma que
  `/api/v1/prop-firms` SÍ está montado hoy (vía `legacy_routes` en `main.py:143`), no es código
  muerto en el sentido de "no se ejecuta", solo "nadie lo llama".
- `grep -rln "lib/prop-firms" apps/web/app apps/web/components` → 8 ficheros.
- `grep -rln "/prop-firms\|api/v1/prop\|api/v2/prop" apps/web --include=*.ts --include=*.tsx` +
  lectura de cada línea encontrada → confirma que son todos `href` de navegación, cero `fetch`.
- `cat -n services/exploitation_engines/prop_firm_engine.py` (fichero completo, 417 líneas) →
  base de la cadena de consumo del motor (§4.1) y de la tabla de discrepancias (§4.2).
- `sed -n '75,180p' services/validation/engine/event_backtest_engine.py` → definición exacta de
  `PropFirmProfile` y sus 5 campos, y el comentario que documenta por qué `consistency_pct`
  queda fuera del motor a propósito.
- `sed -n '1,130p' scripts/fondeo_examen.py` → `_reglas_base_desde_firma` como "Fuente ÚNICA"
  documentada en el propio código.
- `grep -n "^CURRENT_ENGINE_VERSION" services/engine_version.py` → `5.17.0`.
- `grep -n "M3\|prop.firm\|catalogo\|catálogo" orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md`
  y `sed -n '75,95p'` del mismo fichero → confirma que la arquitectura M3 ya decreta
  `services/fondeo/` + muerte de `lib/prop-firms.ts`, antes de que yo escribiera nada de este
  plan.
- `cat cuarentena/web_poda_20260901/MOTIVO.md` → confirma que `/prop-firms` sobrevivió a la poda
  de la web del mismo día por pertenecer a la misión FONDEO vigente.
