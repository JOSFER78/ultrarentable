# Plan de Arquitectura — Fase F: Fábrica Autónoma de Estrategias & Campaigns Autopilot

## 1. Módulo y Estructura

```text
services/api/app/factory/
  ├── __init__.py
  ├── grammar.py        # Gramática tipada (generación de árboles DSL válidos por construcción)
  ├── seed_factory.py   # Generador de población inicial (plantillas, aleatorio gramatical, linajes)
  ├── genetic.py        # Operadores genéticos (mutaciones estructurales, cruces de bloques)
  ├── optimizer.py      # Integración con Optuna (búsqueda paramétrica QMC/TPE/CMA-ES)
  ├── repairer.py       # Reparador dirigido según códigos de error del FAST Engine
  ├── selection.py      # Selección Kamikaze + Novelty Archive (60% fitness, 20% novelty, 10% semillas, 10% reparaciones)
  └── orchestrator.py   # Orquestador de campaña local con ProcessPoolExecutor y checkpoints
```

## 2. Flujo de Trabajo Autónomo (Modo Autopilot)

1. **Configuración de Campaña**:
   - El usuario indica en la interfaz web `/campaigns`:
     - Símbolos (`AUTO` o lista).
     - Timeframes (`AUTO` o lista).
     - Rango de fechas histórico.
     - Capital inicial ($10,000 USD por defecto).
     - Presupuesto de pruebas (ej. 500 candidatos) o duración máxima.
     - Objetivo neto (por defecto `1000%` net / multiplicador $11\times$).
     - Modo de campaña (`EXPLORE`, `IMPROVE`, `REGIME_SEARCH`).
2. **Generación e Invocación de la Fábrica**:
   - `SeedFactory`: Genera candidatos iniciales combinando plantillas cuantitativas y árboles gramaticales aleatorios.
   - Cada candidato se valida estructuralmente con Pydantic y semánticamente con `validate_semantics()`.
   - Si es válido, se compila a IR determinista.
3. **Evaluación de Evaluación Rápida**:
   - El `Orchestrator` distribuye las ejecuciones en el `FastEngine` utilizando un pool local de procesos (`ProcessPoolExecutor`).
   - Los candidatos fallidos (ej. `LIQUIDATED`, `NO_TRADES`, `FEES_DOMINATE`) se envían al `DirectedRepairer` para generar descendientes adaptados.
4. **Optimización de Parámetros**:
   - Los candidatos prometedores pasan a `OptunaOptimizer` para afinamiento de periodos y umbrales numéricos.
5. **Selección Kamikaze & Diversidad**:
   - Se descartar estrictamente las estrategias liquidadas, no reproducibles o con equity $\le 0$.
   - La métrica primaria es $\text{fitness} = \log(\text{final\_equity} / \text{initial\_equity})$.
   - `NoveltyArchive` protege la diversidad estructural de la población reservando nichos para candidatos novedosos y reparados.

## 3. Endpoints API

- `POST /api/v1/campaigns/autonomous`
- `POST /api/v1/campaigns/{id}/start`
- `POST /api/v1/campaigns/{id}/pause`
- `POST /api/v1/campaigns/{id}/resume`
- `POST /api/v1/campaigns/{id}/stop`
- `GET /api/v1/campaigns/{id}`
- `GET /api/v1/campaigns/{id}/population`
- `GET /api/v1/campaigns/{id}/lineage`
- `GET /api/v1/campaigns/{id}/trials`
- `GET /api/v1/campaigns/{id}/events`

## 4. Frontend Autopilot (`apps/web/app/campaigns/page.tsx`)

- Formulario mínimo con defaults inteligentes (sin necesidad de escribir JSON ni conocer indicadores).
- Botón principal: `🚀 INICIAR BÚSQUEDA AUTÓNOMA`.
- Feed interactivo en tiempo real escuchando eventos del backend: candidatos probados, compilados, liquidados, supervivientes, mejor multiplicador y uso de CPU/memoria.
