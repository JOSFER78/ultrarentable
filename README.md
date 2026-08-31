# ULTRARENTABLE — Índice del proyecto

> Laboratorio cuantitativo **real-only** que descubre, valida y explota estrategias de trading
> intradía bajo dos vías segregadas: **ULTRA** (crecimiento asimétrico) y **FONDEO** (prop firms).
>
> Este archivo es **solo un mapa de navegación**. No contiene estado ni especificación:
> para eso están los documentos canónicos de abajo.
> *(La versión anterior de este README, ya superada, está en `docs/archive/root/`.)*

---

## 🧭 Empieza aquí según quién seas

| Si eres… | Lee esto primero |
| :--- | :--- |
| **Antigravity (agente ejecutor)** | **`orchestration/METODOLOGIA_ANTIGRAVITY.md`** ← tu procedimiento operativo completo |
| **Hermes (agente orquestador)** | `orchestration/DOCTRINA_ORQUESTADOR.md` + `orchestration/state/plan_maestro.md` |
| **Persona / desarrollador nuevo** | `docs/00_MASTER_IDEAS_Y_PLAN.md` (SSOT: qué es el proyecto y en qué estado está) |
| **Quieres saber qué se está haciendo AHORA** | `orchestration/state/status.json` y `orchestration/state/current_phase.md` |

---

## 📜 Documentos canónicos (vigentes)

| Documento | Qué contiene |
| :--- | :--- |
| `docs/00_MASTER_IDEAS_Y_PLAN.md` | **SSOT.** Idea del proyecto, arquitectura real verificada, decisiones abiertas. Manda sobre cualquier otro doc. |
| `orchestration/state/plan_maestro.md` | **Plan v3 "El motor primero"** — 12 fases, de la auditoría al paper trading. |
| `orchestration/DOCTRINA_ORQUESTADOR.md` | Doctrina del loop + **§14: las 20 decisiones selladas por el usuario**. |
| `orchestration/METODOLOGIA_ANTIGRAVITY.md` | Procedimiento operativo del ejecutor: protocolo GO/DONE, formato de informe, lista negra. |
| `AUTHORITY_GRAPH.md` | Cadena de autoridad técnica de contratos. |
| `docs/VERSION_GOVERNANCE_AND_CONTROL.md` | Política de versionado y certificación. |
| `docs/ULTRARENTABLE_PRINCIPLES.md` | Los 15 principios del sistema. |
| `docs/ARCHITECTURE_CURRENT.md` | Cadena de verdad de la arquitectura. |
| `docs/18_STRATEGIES_PAGE_SPEC.md` | Spec de la página `/estrategias`. |
| `docs/Gestion de Capital — Balas y Estados.md` | Diseño del sistema de balas de ULTRA. |
| `docs/MULTIAGENTE_Y_SEGUIMIENTO.md` | Modelo de trabajo orquestador + subagentes. |
| `docs/NINJATRADER8_DEMO_PROP_RUNBOOK.md` | Runbook de la infraestructura de fondeo. |
| `GEMINI.md` | Directiva global de Antigravity (aplica a todos los proyectos del usuario). |

**Corpus de referencia (no son especificación de motor):** `docs/tradesfera/` (negocio de fondeo),
`docs/Fondeo/`, `docs/Investigacion/`, `docs/conexiones_automatizar/`, `docs/plan_implementacion/`.

**Histórico:** `docs/archive/` — 27+ documentos superados, conservados intactos y **nunca borrados**.
Reorganización del 2026-08-31 trazada en `docs/archive/MANIFIESTO_REORGANIZACION_2026-08-31.md`.

---

## 🗺️ Mapa del repositorio

```
orchestration/       Loop Hermes ↔ Antigravity (metodología, plan, estado, informes, veredictos)
services/            Motor: discovery · validation (11 gates) · optimization · portfolio ·
                     execution · exploitation_engines (ultra/prop) · data-ingestion · api
apps/web/            Frontend Next.js (:3005)
packages/            Clientes compartidos (bingx-client…)
scripts/             Utilidades y scripts de minería/certificación (pendiente de consolidar, Fase 1)
data/                Datos reales, evidencias y manifiestos SHA-256
tests/               Suite de tests
cuarentena/          Destino de todo lo retirado. Aquí no se borra nada, se aparca.
docs/                Documentación (canónica arriba, histórico en docs/archive/)
```

## ⚙️ Servicios en ejecución (realidad física verificada)

| Servicio | Puerto | Proceso |
| :--- | :---: | :--- |
| Motor SQX headless (`sqcli`) | **5050** | HTTP `/call?cmd=…`. Sin GUI, sin MCP. |
| API FastAPI | **8000** | `ultrarentable-api.service` |
| Web Next.js | **3005** | `ultrarentable-web.service` |

## 🚫 Reglas que no se negocian

1. **REAL-ONLY / ZERO-MOCKS.** Cero datos inventados. Sin dato → `NO DATA` / `ERROR`, nunca un valor por defecto.
2. **Sin `git commit` ni `git push` automáticos.** Todo se queda en working tree para inspección manual.
3. **Nunca `rm`.** Lo retirado se mueve a `cuarentena/` con manifiesto SHA-256.
4. **Nada valioso vive solo en RAM.** Toda población de estrategias se persiste a disco + BD de inmediato.
