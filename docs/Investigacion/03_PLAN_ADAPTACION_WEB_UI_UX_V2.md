# 🏛️ INFORME FORENSE Y PLAN MAESTRO DE ADAPTACIÓN WEB UI/UX — ULTRARENTABLE V2

**Fecha:** 18/08/2026  
**Auditoría Multi-Agente:** Comité de 7 Subagentes Especializados  
**Ubicación de Documentación:** `docs/Investigacion/03_PLAN_ADAPTACION_WEB_UI_UX_V2.md`  
**Estado:** `🟢 DIAGNÓSTICO FÍSICO COMPLETADO · PLAN DE INTEGRACIÓN DEFINIDO`

---

## 🔍 1. DIAGNÓSTICO FORENSE: ¿POR QUÉ LA WEB SE VE IDÉNTICA?

Tras la inspección profunda de `apps/web/` y `services/api/app/main.py`, el comité de subagentes ha identificado con precisión quirúrgica las **3 causas exactas** por las que la web en `localhost:3000` no muestra los cambios implementados:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DIAGNÓSTICO DEL DESCONECTE BACKEND / FRONTEND                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌───────────────────────────────┐
│ 1. ROUTERS V2 NO MONTADOS     │ │ 2. FRONTEND ANCLADO A V1      │ │ 3. COMPONENTES V2 AUSENTES    │
├───────────────────────────────┤ ├───────────────────────────────┤ ├───────────────────────────────┤
│ services/api/app/main.py solo │ │ apps/web/app/page.tsx sigue   │ │ Las nuevas pantallas:         │
│ incluía /api/v1 (legacy).     │ │ haciendo fetch a /api/v1 con  │ │ • Bóveda Ratchet              │
│ Los routers de Telemetría,    │ │ datos estáticos y el 'Embudo  │ │ • FSM 10 Estados              │
│ QVF, Semantic y Paper no      │ │ de 5 Gates' obsoleto.         │ │ • FailureKnowledgeDB          │
│ estaban expuestos al cliente. │ │                               │ │ • HUD de los 8 Workers        │
│                               │ │                               │ │ no están cableadas a la ruta. │
└───────────────────────────────┘ └───────────────────────────────┘ └───────────────────────────────┘
```

### Causas Concretas:
1. **Desconexión en FastAPI (`services/api/app/main.py`):**
   - El servidor FastAPI únicamente tenía montados los routers `/api/v1` de la versión anterior (`providers_router`, `candidates_router`, etc.).
   - Los nuevos módulos (`services/monitoring/telemetry_router.py`, `services/validation/`, `services/semantic_ai/`, `services/portfolio/`, `services/exploitation_engines/ultra_engine.py`, `services/paper/`) operan en memoria con sus propios contratos tipados, pero no estaban registrados en el `main.py` de la API pública.
2. **Componente Principal Obsoleto (`apps/web/app/page.tsx`):**
   - La página inicial de Next.js (`localhost:3000`) estaba renderizando el componente legacy `ControlCenterPage` que lee `/api/v1/system/health` y `/api/v1/providers`, mostrando la tabla estática de estrategias SOL-USDT con drawdowns viejos del 62.3%.
3. **Navegación Desactualizada (`Sidebar.tsx` & `Header.tsx`):**
   - Los menús laterales y superiores no tenían enlaces activos directos hacia el **Centro de IA Semántica & Failure-DB**, el **HUD de 8 Workers con SSE**, el **Visualizador de FSM de 10 Estados** ni el **Simulador Interactivo de la Bóveda Ratchet**.

---

## 🗺️ 2. MAPA DE INTEGRACIÓN WEB V2 (LOS 6 MÓDULOS DE LA UI)

Para reflejar el 100% de la potencia construida en las Fases 0 a 8, la interfaz web se actualizará con una arquitectura moderna **Dark Glassmorphism** (Next.js 14 App Router + Tailwind / CSS Vanilla + Server-Sent Events):

| Módulo Web | Ruta Frontend | Router Backend | Funcionalidad Clave |
| :--- | :--- | :--- | :--- |
| **1. Command Center V2** | `apps/web/app/page.tsx` | `/api/v2/telemetry/health` | Dashboard principal unificado con selector dual `TRACK_FONDEO` vs `TRACK_ULTRA` y métricas reales. |
| **2. HUD 8 Workers (SSE)** | `apps/web/components/layout/Header.tsx` | `/api/v2/telemetry/stream` | Barra superior viva con estado, heartbeats, rendimiento por segundo y alertas de Self-Healing en tiempo real. |
| **3. QVF & FSM 10 Estados** | `apps/web/app/candidatos/` & `/bifurcacion/` | `/api/v2/validation/` | Visualizador del ciclo de vida de la estrategia (`GENERATED` $\to$ `LIVE_ACTIVE`) y compuertas DSR / Fat Tails. |
| **4. Ultra Hub & Bóveda Ratchet** | `apps/web/app/ultra/` | `/api/v2/ultra/` | HUD de la Bala (6 estados), piramidación House Money ($40\%$), Stop Loss Free-Risk y visualizador 3D de la Bóveda. |
| **5. IA Semántica & Failure-DB** | `apps/web/app/research/` | `/api/v2/semantic/` | Explorador de las 11 categorías de fallos, radar de patrones en lista negra y estudio de mutación con Interpreter/Critic/Improver. |
| **6. Paper Sandbox 14 Días** | `apps/web/app/ejecucion/` | `/api/v2/paper/` | Simulador de microestructura con latencia de 50ms, slippage, cronómetro regresivo de 14 días y autopsias de degradación. |

---

## 🛠️ 3. PLAN DE EJECUCIÓN PASO A PASO PARA LA ADAPTACIÓN WEB

El plan se divide en **4 fases de despliegue frontend/backend**:

### 🔹 PASO 1: Exposición de la API V2 en FastAPI (`services/api/app/main.py`)
- Crear los routers de FastAPI que conectan `contracts/`, `event_bus`, `quant_validation_fabric`, `semantic_engine`, `portfolio_engine`, `ultra_engine` y `paper_sandbox_engine`.
- Montar los routers bajo el prefijo `/api/v2/` y habilitar CORS para `localhost:3000`.

### 🔹 PASO 2: Rediseño del Header y TopBar con Telemetría SSE en Vivo
- Actualizar `apps/web/components/layout/Header.tsx` con un cliente `EventSource` a `/api/v2/telemetry/stream`.
- Mostrar badges de estado en vivo para los **8 Workers Especializados** (`DataWorker`, `SQXWorker`, `FastBacktestWorker`, `ValidationWorker`, `MonteCarloWorker`, `SemanticAIWorker`, `PortfolioWorker`, `PaperTradingWorker`).

### 🔹 PASO 3: Renovación de la Página Principal (`apps/web/app/page.tsx`)
- Sustituir el 'Embudo de 5 Gates' por el **Panel de Control Dual 2026**:
  - Selector interactivo entre `TRACK_FONDEO (CME / Prop 50K)` y `TRACK_ULTRA (BingX Perpetuals)`.
  - Tarjetas de estado del sistema conectadas al `SystemSupervisor`.
  - Tabla canónica de estrategias que consume `CanonicalStrategy` y muestra hashes SHA-256 inmutables de procedencia.

### 🔹 PASO 4: Implementación de las Vistas Especializadas
- **`apps/web/app/ultra/page.tsx`:** HUD interactivo de los 6 estados de la Bala y Bóveda Ratchet.
- **`apps/web/app/research/page.tsx`:** Explorador de `FailureKnowledgeDB` y Semantic AI Studio.
- **`apps/web/app/candidatos/page.tsx`:** Visualizador de la FSM de 10 estados y Evidence Gate Decision.
- **`apps/web/app/ejecucion/page.tsx`:** Sandbox de Paper Trading con contador regresivo de 14 días y fills de microestructura en tiempo real.

---

## 🚀 4. CONCLUSIÓN Y VERIFICACIÓN

Con este plan, **cada línea de código, contrato y lógica matemática implementada en el backend quedará visualmente viva, interactiva y operable desde el navegador en `localhost:3000`**.
