# 🏛️ ARQUITECTURA DEL SISTEMA ULTRARENTABLE V2
## *Clean Architecture, Microservicios Desacoplados, Contratos Inmutables y Telemetría Reactiva*

---

## 1. Principios de Diseño y Capas del Sistema

Ultrarentable está diseñado bajo el patrón **Ports & Adapters (Hexagonal / Clean Architecture)** para garantizar que la lógica cuantitativa central sea 100% independiente de bases de datos, plataformas de brokers y frameworks web.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                              │
│         Next.js 14 Web App (`apps/web`)  ◄──  SSE Stream (`/telemetry`)      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ HTTP / REST / SSE
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                                APPLICATION LAYER                             │
│       FastAPI Routes  •  SystemSupervisor (8 Workers)  •  AsyncEventBus      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ Invoca
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                                  DOMAIN LAYER                                │
│   CanonicalStrategy  •  QuantValidationFabric  •  UltraExploitationEngine   │
│                 (Modelos Pydantic v2 Inmutables en `contracts/`)              │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ Implementa
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                             INFRASTRUCTURE LAYER                             │
│   FastEngineCore (Backtest)  •  SQLite WAL Storage  •  SQX MCP Bridge Client │
│       BingX Swap v2 REST Gateway  •  Tradovate / Rithmic CME Connector       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Los 11 Módulos Core (`services/`)

1. **`services/api/`:** Servidor FastAPI, middleware CORS, autenticación y emisor SSE.
2. **`services/backtest/`:** `FastEngineCore`, cálculo vectorial de curvas de equidad y métricas DSR/Sortino.
3. **`services/discovery/`:** Orquestación de mutaciones genéticas y cliente MCP para SQX.
4. **`services/evidence/`:** `CandidateRegistry` con control de estados FSM y hashes SHA-256.
5. **`services/execution/`:** Adaptadores de órdenes para BingX Perpetuals y brokers CME.
6. **`services/exploitation_engines/`:** Lógica de `UltraExploitationEngine` (Balas/Bóveda) y `PropFirmEngine`.
7. **`services/monitoring/`:** `SystemSupervisor`, gestión de ciclo de vida de procesos y heartbeat.
8. **`services/paper/`:** Sandbox de ejecución simulada con datos de mercado reales (14 días).
9. **`services/portfolio/`:** Sincronización temporal Epoch UTC (ms), correlación y sizing.
10. **`services/semantic_ai/`:** 8 agentes especializados y memoria de autopsias `FailureKnowledgeDB`.
11. **`services/validation/`:** Compuertas `FondeoEvidenceGate` y `UltraEvidenceGate`.

---

## 3. Contratos Canónicos Pydantic v2 (`contracts/`)

### Modelo Canónico de Estrategia (`contracts/canonical_strategy.py`)
```python
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

class ExecutionTrack(str, Enum):
    FONDEO = "TRACK_FONDEO"
    ULTRA = "TRACK_ULTRA"

class StrategyStatus(str, Enum):
    GENERATED = "GENERATED"
    FAST_FILTERED = "FAST_FILTERED"
    VALIDATED_QVF = "VALIDATED_QVF"
    EVIDENCE_APPROVED = "EVIDENCE_APPROVED"
    INCUBATION_PAPER = "INCUBATION_PAPER"
    LIVE = "LIVE"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"
```

### Contratos de Validación y Compuertas (`contracts/validation_contracts.py`)
```python
class FondeoValidationCriteria(BaseModel):
    model_config = ConfigDict(frozen=True)
    min_deflated_sharpe: float = 2.00
    max_realized_drawdown_pct: float = 4.50
    max_floating_drawdown_pct: float = 80.0
    max_daily_loss_limit_usd: float = 1000.0
    allowed_account_sizes: List[int] = [25000, 50000, 100000, 150000, 250000, 300000]

class UltraValidationCriteria(BaseModel):
    model_config = ConfigDict(frozen=True)
    min_payoff_ratio: float = 2.50
    min_tail_gain_ratio: float = 0.40
    min_expected_r_per_bala: float = 0.20
    max_realized_drawdown_pct: float = 75.0
    max_floating_drawdown_pct: float = 80.0
    max_leverage: float = 500.0
```

---

## 4. Arquitectura de Streaming y UI Pasiva

1. **Backend Emisor:** Endpoint `GET /api/v2/real/search-telemetry` emite telemetría inmutable precalculada en tiempo real.
2. **Frontend Receptor (`apps/web`):** Hook `useTelemetryStream` en React suscribe a los eventos y actualiza los stores de Zustand/React State.
3. **Regla de Oro:** El cliente web jamás ejecuta cálculos de rentabilidad, drawdown o métricas de riesgo; consume exclusivamente datos precalculados y firmados criptográficamente desde SQLite WAL.
