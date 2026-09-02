"""services/validation/registry/registro.py
Registro explícito de los 11 Gates Cuantitativos v1 (paridad suite B).
Prohibido el escaneo dinámico / importlib.
"""

from typing import Dict, Type

from services.validation.registry.contratos import GateBase
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

GATE_REGISTRY: Dict[int, Type[GateBase]] = {
    1: Gate01DataIngest,
    2: Gate02CostBacktest,
    3: Gate03TradeSignificance,
    4: Gate04WalkForward,
    5: Gate05MonteCarlo,
    6: Gate06StressSlippage,
    7: Gate07RegimeCoverage,
    8: Gate08DSRRatio,
    9: Gate09NoveltyAntiFit,
    10: Gate10AgentDebate,
    11: Gate11NautilusEvent,
}
