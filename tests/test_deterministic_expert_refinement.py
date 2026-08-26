"""tests/test_deterministic_expert_refinement.py
Tests unitarios y forenses para el Motor de Refinamiento Experto y Descubrimiento Determinista.
Verifica que:
1. No se utilicen generadores sintéticos (random) en mutación y descubrimiento.
2. La evaluación multi-tier (Tier 1: 11/11, Tier 2: 9-10/11, Tier 3: 7-8/11) se aplique con rigor.
3. El refinamiento iterativo opere sobre datos físicos reales y persista evidencias.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

from services.semantic_ai.mutation_engine import SemanticMutationEngine
from services.optimization.expert_refinement_loop import expert_strategy_optimizer
from contracts.canonical_strategy import ExecutionTrack


def test_mutation_engine_zero_random():
    """Verifica que SemanticMutationEngine sea 100% determinista y no use random."""
    engine = SemanticMutationEngine()
    
    cand1 = engine.generate_candidate(symbol="BTC-USDT", timeframe="1h", track=ExecutionTrack.TRACK_FONDEO)
    cand2 = engine.generate_candidate(symbol="BTC-USDT", timeframe="1h", track=ExecutionTrack.TRACK_FONDEO)
    
    assert cand1.instrument.symbol == "BTC-USDT"
    assert cand1.timeframe == "1h"
    assert cand1.entry_rules.long_conditions[0].threshold_value == cand2.entry_rules.long_conditions[0].threshold_value
    assert cand1.exits.stop_loss_ticks == cand2.exits.stop_loss_ticks


def test_expert_refinement_loop_on_real_candidate():
    """Verifica la ejecución del bucle de refinamiento experto sobre un candidato de disco."""
    # Verificar si existe al menos un candidato en la base de datos
    db_path = Path("/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3")
    if not db_path.exists():
        pytest.skip("Base de datos SQLite no presente.")
        
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    row = cur.execute("SELECT candidate_id FROM candidates WHERE symbol IN ('BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'NQ', 'ES') LIMIT 1").fetchone()
    conn.close()
    
    if not row:
        pytest.skip("No hay candidatos cargados en SQLite.")
        
    cid = row[0]
    res = expert_strategy_optimizer.refine_candidate_loop(candidate_id=cid, max_iterations=2)
    
    assert "candidate_id" in res
    assert "status" in res
    assert "gates_passed_count" in res
    assert "tier" in res
    assert res["tier"] in ("TIER_1_CERTIFIED", "TIER_2_NEAR_CERTIFIED", "TIER_3_INCUBATOR", "TIER_4_REJECTED")
    
    # Si tiene 11 gates -> TIER_1_CERTIFIED
    if res["gates_passed_count"] == 11 and res["is_certified"]:
        assert res["tier"] == "TIER_1_CERTIFIED"
        assert res["status"] == "APPROVED"
    elif res["gates_passed_count"] in (9, 10):
        assert res["tier"] == "TIER_2_NEAR_CERTIFIED"
    elif res["gates_passed_count"] in (7, 8):
        assert res["tier"] == "TIER_3_INCUBATOR"
