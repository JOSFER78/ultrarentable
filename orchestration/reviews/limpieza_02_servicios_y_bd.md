# LIMPIEZA 0.2 y 0.3 — Servicios muertos y bases de datos

**Auditor:** Hermes · **2026-08-31** · Solo lectura, todo con evidencia de grep

## Mapa completo de `services/` (24 subdirectorios)

Importaciones contadas desde fuera del propio módulo, excluyendo `cuarentena/`.

| Servicio | Ficheros | Líneas | Importadores | Estado |
| :--- | ---: | ---: | ---: | :--- |
| api | 132 | 29.868 | 383 | ✅ VIVO (núcleo) |
| validation | 28 | 5.198 | 155 | ✅ VIVO (ver limpieza_01: su subcarpeta `engines/` sí es zombi) |
| discovery | 15 | 3.059 | 102 | ✅ VIVO |
| data | 11 | 1.812 | 38 | ✅ VIVO |
| semantic_ai | 10 | 2.851 | 35 | ✅ VIVO |
| portfolio | 9 | 1.557 | 30 | ⚠️ VIVO pero DESCONECTADO (ver abajo) |
| engine, optimization | 6+5 | 3.179 | 17+17 | ✅ VIVO |
| monitoring | 5 | 676 | 16 | ✅ VIVO |
| sqx_bridge | 7 | 800 | 13 | ✅ VIVO |
| core, exploitation_engines, strategy_core | 3+4+6 | 2.458 | 11 c/u | ✅ VIVO |
| backtest | 3 | 418 | 9 | ✅ VIVO |
| paper | 6 | 540 | 8 | ✅ VIVO |
| queue, lineage, sync, policy | 1 c/u | 1.184 | 3-5 | ✅ VIVO (routers montados) |
| export | 2 | 327 | 2 | ✅ VIVO (`certified_summary_router`, montado) |
| **research** | 1 | **428** | 2 | ❌ **MUERTO** (solo tests) |
| **execution** | 3 | **993** | 2 | ❌ **MUERTO** (solo su `__init__` + 1 test) |
| **ai_updater** | 5 | **291** | 1 | ❌ **MUERTO** (cadena rota, ver abajo) |
| **data-ingestion** (guion) | 0 .py | 0 | 0 | ❌ **MUERTO** (solo `src/recorder.ts`) |
| data_ingestion (guion bajo) | 2 | 456 | 0 | ✅ VIVO — es el ingestor Dukascopy nuevo, se usa por CLI, no por import |

## Los tres muertos, con su prueba

### 1. `services/ai_updater` (291 líneas) — cadena rota
Su único importador es `services/api/app/routes/providers_ai.py`.
Ese fichero **no lo importa nadie y su router NO está montado** en `main.py`
(`grep -c providers_ai services/api/app/main.py` = **0**, frente a 37 `include_router`).
⇒ Muere el router y muere el servicio con él. Se retiran los dos.

### 2. `services/execution` (993 líneas)
Contiene `canonical_runtime_adapter.py` y `hermes_watchdog.py`. Sus únicos importadores son
su propio `__init__.py` y un test. **La API no lo usa**:
`grep -rn "services.execution\|canonical_runtime_adapter" services/api/` → sin resultados.
⚠️ **Cautela:** por el nombre, `canonical_runtime_adapter` puede ser infraestructura prevista para
la ejecución real (Fase 5/8 del plan). **Se revisa antes de retirarlo**, no se aparca a ciegas.

### 3. `services/research` (428 líneas)
Solo lo importan dos tests. `research_router` sí está montado, pero **no importa este módulo**:
`grep -rn "services.research" services/api/` → sin resultados. Es otro fichero distinto.

**Total código muerto confirmado: ~1.712 líneas + un stub TypeScript.**

## Bases de datos: 5 ficheros, 1 canónica

| Fichero | Tamaño | Tablas | Referencias en código | Estado |
| :--- | ---: | ---: | ---: | :--- |
| `~/.local/state/ultrarentable/ultrarentable.sqlite3` | 62 MB | 33 | **71** | ✅ **LA CANÓNICA** |
| `learning_store.sqlite` | 280 KB | 11 | 4 | ✅ VIVA (`semantic_ai`, `research_lab_router`) |
| `data/sqlite.db` | **0 B** | 0 | **0** | ❌ Cascarón vacío, nadie la nombra |
| `data/candidates.db` | **0 B** | 0 | 0 directas | ❌ Cascarón vacío |
| `data/state.db` | **0 B** | 0 | 0 directas | ❌ Cascarón vacío |
| `data/sqlite/candidates.db` | 12 KB | — | 1 (por defecto) | ⚠️ **Rancia** (20-ago), ver abajo |

## ⚠️ EL HALLAZGO QUE MÁS IMPORTA: el motor de meta-estrategias está desconectado

`services/portfolio/meta_strategy_engine.py:35`:

```python
def __init__(self, db_path: str = "data/sqlite/candidates.db") -> None:
```

- Apunta por defecto a `data/sqlite/candidates.db`: **12 KB, sin tocar desde el 20 de agosto**.
- **No a la base canónica** de 62 MB donde viven los 505 candidatos reales.
- Y lo único que lo instancia en todo el repo es un test:
  `tests/discovery/test_adaptive_hypothesis_and_meta.py:29 → MetaStrategyEngine()`, con la ruta
  por defecto.

**Traducción:** el motor de meta-estrategias existe, pero nunca ha visto los candidatos reales.
No está roto — está **desenchufado**. Y las meta-estrategias (ULTRA y FONDEO) son prioridad
declarada del usuario, así que esto pasa a ser trabajo de primera línea, no limpieza.

## Acciones propuestas (ninguna ejecutada)

1. A `cuarentena/servicios_muertos/` con manifiesto SHA-256: `services/research/`,
   `services/ai_updater/`, `services/api/app/routes/providers_ai.py`, `services/data-ingestion/`.
2. `services/execution/`: **revisar antes**. Si `canonical_runtime_adapter` sirve para la Fase 5,
   se conserva y se documenta como infraestructura futura en vez de aparcarlo.
3. Las 3 BD de 0 bytes a `cuarentena/bd_vacias/`.
4. **`meta_strategy_engine`: conectarlo a la BD canónica.** No es limpieza: es habilitar una
   pieza que el usuario necesita.
