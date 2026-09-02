"""services/validation/registry/gates/__init__.py
Módulos individuales de los 11 Gates Cuantitativos v1 (paridad suite B).
"""

from services.validation.registry.gates.gate_01 import Gate01DataIngest
from services.validation.registry.gates.gate_02 import Gate02CostBacktest
from services.validation.registry.gates.gate_03 import Gate03TradeSignificance
from services.validation.registry.gates.gate_04 import Gate04WalkForward
from services.validation.registry.gates.gate_05 import Gate05MonteCarlo
from services.validation.registry.gates.gate_06 import Gate06StressSlippage
from services.validation.registry.gates.gate_07 import Gate07RegimeCoverage
from services.validation.registry.gates.gate_08 import Gate08DSRRatio
from services.validation.registry.gates.gate_09 import Gate09NoveltyAntiFit
from services.validation.registry.gates.gate_10 import Gate10AgentDebate
from services.validation.registry.gates.gate_11 import Gate11NautilusEvent

__all__ = [
    "Gate01DataIngest",
    "Gate02CostBacktest",
    "Gate03TradeSignificance",
    "Gate04WalkForward",
    "Gate05MonteCarlo",
    "Gate06StressSlippage",
    "Gate07RegimeCoverage",
    "Gate08DSRRatio",
    "Gate09NoveltyAntiFit",
    "Gate10AgentDebate",
    "Gate11NautilusEvent",
]
