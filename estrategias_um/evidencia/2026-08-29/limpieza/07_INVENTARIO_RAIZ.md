# 07 — INVENTARIO RAÍZ + docs/ (solo informe, nada movido ni borrado)

Fecha: 2026-08-29 17:25 UTC · Repo: `01 Ultrarentable/` · Fuente de verdad: `docs/00_MASTER_IDEAS_Y_PLAN.md` §6.
Clases: **VIGENTE** (en master §6 o infraestructura activa) · **SUPERSEDED** (banner, ya indexado en §6) · **HUÉRFANO** (ni vigente ni superseded → candidato cuarentena) · **DATO-VIVO** (sqlite/datos — no se toca jamás).

## 1. RAÍZ (33 ficheros)

| Fichero | Tamaño | Mtime | Tipo | Clase | Nota |
|---|---|---|---|---|---|
| 03_HANDOFF_AG2-P02-005.md | 8.8K | 08-25 17:05 | md | HUÉRFANO | handoff antiguo P02-005, no en §6 |
| 17_PHASE2_EXECUTION_STATUS.md | 4.2K | 08-28 10:17 | md | VIGENTE | estado fase 2 reciente/activo |
| 18_STRATEGIES_PAGE_SPEC.md | 2.4K | 08-28 15:44 | md | VIGENTE | citado en §6 como spec vigente |
| ARCHITECTURE.md | 6.9K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| AUDIT_FINAL_REAL_ONLY.md | 5.3K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| AUTHORITY_GRAPH.md | 5.5K | 08-20 21:09 | md | VIGENTE | citado en §6 |
| ESTADO.md | 4.5K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| GEMINI.md | 3.4K | 08-23 22:32 | md | HUÉRFANO | config agente, no en §6 (bajo: infra de tooling) |
| P02-005_AGENT_LEDGER.md | 5.6K | 08-25 17:05 | md | HUÉRFANO | ledger antiguo P02-005 |
| P02-005_RECON_REPORT.md | 3.4K | 08-25 17:05 | md | HUÉRFANO | informe recon antiguo |
| P02-005_RUNTIME_SEMANTIC_MATRIX.md | 5.4K | 08-25 17:05 | md | HUÉRFANO | matriz antigua P02-005 |
| Plan 10 Fases.md | 3.5K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| README.md | 8.4K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| SPEC_MASTER_ULTRA_VS_FONDEO.md | 10.8K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| SYSTEM_DOCTRINE.md | 13.2K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| walkthrough.md | 6.7K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| __init__.py | 772B | 08-25 11:55 | py | VIGENTE | paquete python del repo |
| audit_frontend_playwright.js | 4.0K | 08-24 18:51 | js | HUÉRFANO | script auditoría ad-hoc |
| audit_v540_playwright.js | 3.1K | 08-24 19:18 | js | HUÉRFANO | script auditoría ad-hoc v540 |
| canonical_instrument_aliases.json | 2.3K | 08-25 13:18 | json | VIGENTE | config runtime canónica (usada por adapter) |
| canonical_runtime_adapter.py | 25.6K | 08-25 17:03 | py | VIGENTE | código runtime activo (P02-005) |
| canonical_strategy.py | 15.3K | 08-25 16:13 | py | VIGENTE | código runtime activo (P02-005) |
| database.sqlite | 1.6M | 08-29 02:09 | sqlite | DATO-VIVO | BD operacional — NO TOCAR |
| learning_store.sqlite | 28.7M | 08-29 02:06 | sqlite | DATO-VIVO | BD learning — NO TOCAR |
| package-lock.json | 69.4K | 08-26 21:13 | json | VIGENTE | lockfile npm |
| package.json | 539B | 08-28 16:00 | json | VIGENTE | manifiesto npm activo |
| pyproject.toml | 889B | 08-19 22:38 | toml | VIGENTE | build python |
| test_phase01_dataset_chain_of_custody.py | 5.4K | 08-25 13:18 | py | VIGENTE | test activo |
| test_phase02_canonical_strategy.py | 34.5K | 08-25 17:03 | py | VIGENTE | test activo P02-005 |
| uv.lock | 241.6K | 08-20 00:35 | lock | VIGENTE | lockfile uv |
| uvicorn.log | 1.2K | 08-22 02:07 | log | HUÉRFANO | log antiguo de servidor |
| version_control_manager.py | 11.8K | 08-25 11:48 | py | HUÉRFANO | script suelto, no referenciado |
| version_manifest.json | 1.3K | 08-25 11:37 | json | HUÉRFANO | manifiesto del script anterior |

## 2. docs/ (nivel superior, 19 ficheros — subcarpetas no inventariadas aquí)

| Fichero | Tamaño | Mtime | Tipo | Clase | Nota |
|---|---|---|---|---|---|
| 00_MASTER_IDEAS_Y_PLAN.md | 23.7K | 08-29 16:27 | md | VIGENTE | doc maestro, fuente de verdad |
| ARCHITECTURE.md | 7.8K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| ARCHITECTURE_CURRENT.md | 3.5K | 08-27 10:55 | md | VIGENTE | citado en §6 (cadena de verdad) |
| AUDIT_2026-08-25_APPROVED_METRICS.md | 2.7K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| AUDIT_BASELINE_2026-08-19.md | 2.6K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| Dashboard Web.md | 1.9K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| FIX_RECORD_20260809.md | 7.1K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| Gestion de Capital — Balas y Estados.md | 1.6K | 08-17 20:14 | md | VIGENTE | citado en §6 (negocio) |
| MULTIAGENTE_Y_SEGUIMIENTO.md | 7.4K | 08-17 20:15 | md | VIGENTE | citado en §6 |
| Motor StrategyQuant X.md | 2.5K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| Motor de Fondeo y Prop Firms.md | 4.4K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| NINJATRADER8_DEMO_PROP_RUNBOOK.md | 6.8K | 08-22 03:53 | md | HUÉRFANO | runbook NT8, no en §6 (referencia prop firms) |
| PLAN_DE_EJECUCION_MAESTRO_ADAPTATIVO.md | 3.8K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| STATE_OF_TRUTH.md | 4.1K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| ULTRARENTABLE_PRINCIPLES.md | 5.0K | 08-24 16:56 | md | VIGENTE | citado en §6 |
| Ultrarentable - Ficha anterior 2026-08-03.md | 3.0K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| Ultrarentable_Residuales.md | 2.5K | 08-29 05:08 | md | SUPERSEDED | banner + indexado §6 |
| VERSION_GOVERNANCE_AND_CONTROL.md | 6.1K | 08-24 19:18 | md | VIGENTE | citado en §6 |
| arquitectura-orquestacion-orquestador-antigravity.md | 8.6K | 08-29 17:21 | md | VIGENTE | muy reciente (activo hoy) |

Subcarpetas docs/ (no inventariadas fichero a fichero): Estado, Fondeo, Investigacion, Laboratorio, Ultrarentable, archive, conexiones_automatizar, plan_implementacion, pruebas, tradesfera — todas referenciadas en §6 (material de referencia / corpus / archive).

## 3. Otros (directorios raíz — solo superficial, sin entrar)

| Directorio | Clase | Nota |
|---|---|---|
| .agents, .github, .kilo, .phase2, .ruff_cache, .vscode | VIGENTE | config tooling |
| .git, .venv, node_modules | VIGENTE | excluidos (solo presencia) |
| apps, packages, services, scripts, tests, contracts | VIGENTE | código estructurado activo |
| estrategias_um | VIGENTE | subproyecto ULTRA_MATRIX (§7 master) |
| data | DATO-VIVO | datasets — NO TOCAR |
| backups | VIGENTE | copias — no tocar |
| informes, scratch, bingx_ultra_strategy_lab.egg-info | HUÉRFANO* | informes antiguos / scratch / artefacto build |
| v540_audit_screenshots | HUÉRFANO* | capturas auditoría ad-hoc 08-29 02:13 |

## CUARENTENA-CANDIDATOS (solo propuesta, NADA movido)

| Candidato | Justificación |
|---|---|
| raíz/03_HANDOFF_AG2-P02-005.md | handoff puntual de fase antigua, no indexado en §6 |
| raíz/P02-005_AGENT_LEDGER.md | ledger de fase cerrada P02-005, fuera del índice |
| raíz/P02-005_RECON_REPORT.md | informe recon puntual, fuera del índice |
| raíz/P02-005_RUNTIME_SEMANTIC_MATRIX.md | matriz de fase cerrada, fuera del índice |
| raíz/GEMINI.md | config de agente externo, sin referencia en §6 |
| raíz/audit_frontend_playwright.js | script auditoría one-shot (08-24), ya ejecutado |
| raíz/audit_v540_playwright.js | script auditoría one-shot v540, ya ejecutado |
| raíz/uvicorn.log | log de servidor residual (08-22) |
| raíz/version_control_manager.py | script suelto no referenciado en ninguna doc |
| raíz/version_manifest.json | dato del script anterior, pareja de cuarentena |
| docs/NINJATRADER8_DEMO_PROP_RUNBOOK.md | runbook fuera de §6 (duda: podría ser referencia prop firms) |
| informes/ | contenido antiguo sin referenciar (requeriría inventario interno antes) |
| scratch/ | zona de trabajo temporal |
| v540_audit_screenshots/ | capturas de auditoría ya concluida |
| bingx_ultra_strategy_lab.egg-info/ | artefacto de build regenerable |

Verificación: conteos raíz = 33 ficheros, docs/ superior = 19 → total 52. Sin modificaciones al árbol (solo lectura + este informe).
