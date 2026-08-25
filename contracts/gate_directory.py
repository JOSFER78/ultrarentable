"""contracts/gate_directory.py
Directorio Canónico de los 11 Quality Gates de Ultrarentable.
Especificación oficial según Sección 5 y 8 del Informe Maestro v5.3.0.
"""

from typing import Any, Dict, List

GATES_DIRECTORY: List[Dict[str, Any]] = [
    {
        "id": 1,
        "slug": "gate-1-data-ingest",
        "name": "Integridad de Datos OHLCV",
        "description": "Verificación de continuidad temporal, cero velas corruptas y gaps <= 2%.",
        "default_params": {"max_gap_pct": 2.0, "min_bars": 1000},
    },
    {
        "id": 2,
        "slug": "gate-2-cost-backtest",
        "name": "Backtest con Comisiones y Slippage",
        "description": "Deducción de comisiones taker/maker institucionales y slippage adverso.",
        "default_params": {"min_profit_factor": 1.25, "fee_multiplier": 1.0},
    },
    {
        "id": 3,
        "slug": "gate-3-trade-significance",
        "name": "Significancia Estadística de Trades",
        "description": "Mínimo de operaciones en In-Sample y Out-of-Sample para representatividad.",
        "default_params": {"min_trades_is": 30, "min_trades_oos": 15},
    },
    {
        "id": 4,
        "slug": "gate-4-walk-forward",
        "name": "Walk-Forward Optimization (WFO)",
        "description": "Evaluación rodante sobre ventanas de validación sin lookahead.",
        "default_params": {"windows": 5, "min_wfo_efficiency": 0.60},
    },
    {
        "id": 5,
        "slug": "gate-5-monte-carlo",
        "name": "Remuestreo Monte Carlo (0% Ruina)",
        "description": "Bootstrap sobre trades OOS reales asegurando riesgo de ruina = 0%.",
        "default_params": {"simulations": 1000, "confidence_pct": 95.0},
    },
    {
        "id": 6,
        "slug": "gate-6-stress-slippage",
        "name": "Estrés de Fricción 3x",
        "description": "Resistencia de la ventaja estadística bajo comisiones y slippage triplicados.",
        "default_params": {"stress_factor": 3.0, "min_stressed_pf": 1.05},
    },
    {
        "id": 7,
        "slug": "gate-7-regime-coverage",
        "name": "Cobertura Multirégimen",
        "description": "Rendimiento comprobado en tendencias alcistas, bajistas y rangos de volatilidad.",
        "default_params": {"min_profitable_regimes": 2},
    },
    {
        "id": 8,
        "slug": "gate-8-dsr-ratio",
        "name": "Deflated Sharpe Ratio (DSR)",
        "description": "Ajuste del ratio Sharpe penalizando el sesgo de selección y número de trials.",
        "default_params": {"min_dsr": 2.0},
    },
    {
        "id": 9,
        "slug": "gate-9-novelty-antifit",
        "name": "Novedad y Anti-Overfitting",
        "description": "Distancia sintáctica AST respecto a estrategias previamente aprobadas.",
        "default_params": {"min_ast_distance": 0.15},
    },
    {
        "id": 10,
        "slug": "gate-10-debate-agentes",
        "name": "Consenso de Debate Multi-Agente",
        "description": "Evaluación dialéctica adversarial entre 5 roles cuantitativos independientes.",
        "default_params": {"min_consensus_score": 75.0},
    },
    {
        "id": 11,
        "slug": "gate-11-nautilus-event",
        "name": "Reconciliación de Eventos NautilusCore",
        "description": "Modelado exacto de margen, distancia a liquidación y Bóveda Ratchet.",
        "default_params": {"min_liquidation_buffer_pct": 5.0},
    },
]
