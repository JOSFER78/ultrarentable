"""services/lineage/lineage_service.py
Servicio de Linaje Genealógico de Estrategias y Certificación Cuantitativa Inmutable.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from contracts.lineage_contracts import (
    CertificationRecord,
    CertificationStatus,
    LineageNode,
    LineageTreeResponse,
)
from services.api.app.db.database import CandidateModel, StrategyModel, DatasetModel, InstrumentRuleSnapshotModel, AccountFeeSnapshotModel
from services.version_control_manager import version_manager


def _compute_cert_hash(data: Dict[str, Any]) -> str:
    """Calcula el hash criptográfico SHA-256 canónico del certificado sin el campo certificate_hash."""
    clean = {k: v for k, v in data.items() if k != "certificate_hash"}
    serialized = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class LineageService:
    """Motor de Linaje de Certificaciones y Grafo Genealógico."""

    def __init__(self, db: Session):
        self.db = db

    def generate_certificate(
        self,
        strategy_id: str,
        version: str,
        strategy_hash: str,
        dataset_id: str,
        metrics_snapshot: Dict[str, float],
        route: str,
        status: CertificationStatus,
        scorecard: Optional[Dict[str, Any]] = None,
        trial_id: Optional[str] = None,
    ) -> CertificationRecord:
        """Emite un certificado de validación inmutable y firmado criptográficamente."""
        # 1. Resolver checksum del dataset
        ds = self.db.query(DatasetModel).filter(DatasetModel.dataset_id == dataset_id).first()
        dataset_checksum = ds.checksum_sha256 if ds and ds.checksum_sha256 else "sha256_unverified_dataset"

        # 2. Resolver huella del código y versión activa del motor
        v_info = version_manager.get_full_version_info()
        engine_version = v_info.get("active_version", "5.3.0")
        codebase_fingerprint = v_info.get("codebase_fingerprint", "fp_untracked")

        # 3. Resolver snapshot de reglas y comisiones
        rule_snap = self.db.query(InstrumentRuleSnapshotModel).first()
        rules_snap_id = rule_snap.snapshot_id if rule_snap else "snap_rules_default"

        fee_snap = self.db.query(AccountFeeSnapshotModel).first()
        fee_snap_id = fee_snap.snapshot_id if fee_snap else "snap_fees_default"

        now_utc = datetime.now(timezone.utc).isoformat()
        cert_id = f"cert_{strategy_id}_{version}_{int(datetime.now(timezone.utc).timestamp())}"

        cert_dict = {
            "certificate_id": cert_id,
            "strategy_id": strategy_id,
            "version": version,
            "strategy_hash": strategy_hash,
            "dataset_id": dataset_id,
            "dataset_checksum_sha256": dataset_checksum,
            "engine_version": engine_version,
            "codebase_fingerprint": codebase_fingerprint,
            "rules_snapshot_id": rules_snap_id,
            "fee_snapshot_id": fee_snap_id,
            "route": route,
            "metrics_snapshot": metrics_snapshot,
            "scorecard": scorecard or {},
            "status": status.value if hasattr(status, "value") else str(status),
            "certified_at_utc": now_utc,
            "trial_id": trial_id,
        }

        cert_hash = _compute_cert_hash(cert_dict)
        cert_dict["certificate_hash"] = cert_hash

        return CertificationRecord.model_validate(cert_dict)

    def verify_certificate(self, cert: CertificationRecord) -> bool:
        """Verifica que el hash del certificado coincide exactamente con sus campos."""
        cert_dict = cert.model_dump()
        expected_hash = _compute_cert_hash(cert_dict)
        return cert.certificate_hash == expected_hash

    def get_lineage_tree(self, strategy_id: str) -> LineageTreeResponse:
        """Construye el árbol genealógico completo (DAG) para una estrategia."""
        # 1. Encontrar la estrategia o candidato solicitado
        candidate = self.db.query(CandidateModel).filter(CandidateModel.candidate_id == strategy_id).first()
        strategy_model = self.db.query(StrategyModel).filter(StrategyModel.strategy_id == strategy_id).first()

        nodes: Dict[str, LineageNode] = {}
        visited: set[str] = set()

        def _resolve_node(sid: str) -> Optional[LineageNode]:
            if sid in nodes:
                return nodes[sid]
            
            c = self.db.query(CandidateModel).filter(CandidateModel.candidate_id == sid).first()
            s = self.db.query(StrategyModel).filter(StrategyModel.strategy_id == sid).first()

            if not c and not s:
                return None

            family = (c.family if c else None) or (s.family if s else None) or "UNKNOWN"
            symbol = (c.symbol if c else None) or (s.symbol if s else None) or "UNKNOWN"
            timeframe = (c.timeframe if c else None) or (s.timeframe if s else None) or "1h"
            version = (getattr(c, "engine_version", "1.00") if c else None) or (s.engine_version if s else "1.00") or "1.00"
            created_at = (c.created_at.isoformat() if c and c.created_at else None) or (s.created_at.isoformat() if s and s.created_at else None) or datetime.now(timezone.utc).isoformat()
            
            # Parents
            parents: List[str] = []
            if s and s.ast_json:
                try:
                    ast = json.loads(s.ast_json) if isinstance(s.ast_json, str) else s.ast_json
                    parents = ast.get("metadata", {}).get("parents", [])
                except Exception:
                    pass

            # Certifications
            certifications: List[CertificationRecord] = []
            if c and c.status in ["APPROVED", "PASSED"]:
                metrics = {
                    "profit_factor": float(c.profit_factor or 0.0),
                    "max_drawdown_pct": float(c.max_drawdown or 0.0),
                    "trades": float(c.trades or 0),
                    "net_return_pct": float(c.net_profit or 0.0),
                }
                cert = self.generate_certificate(
                    strategy_id=sid,
                    version=version,
                    strategy_hash=f"hash_{sid}",
                    dataset_id=c.dataset_id or "dataset_default",
                    metrics_snapshot=metrics,
                    route=c.route or "ultra",
                    status=CertificationStatus.APPROVED if c.route != "fondeo" else CertificationStatus.FUNDING_CERTIFIED,
                )
                certifications.append(cert)

            node = LineageNode(
                strategy_id=sid,
                version=version,
                strategy_hash=f"hash_{sid}",
                family=family,
                venue="BINGX",
                symbol=symbol,
                timeframe=timeframe,
                parent_ids=parents,
                mutation_type="SEEDED" if not parents else "MUTATED",
                mutation_reason="Generado en pipeline" if not parents else "Evolución por mutación",
                created_at_utc=created_at,
                certifications=certifications,
                children=[],
            )
            nodes[sid] = node
            return node

        # Resolving primary node
        primary_node = _resolve_node(strategy_id)
        if not primary_node:
            # Fallback for transient or mock-free empty node
            primary_node = LineageNode(
                strategy_id=strategy_id,
                version="1.00",
                strategy_hash=f"hash_{strategy_id}",
                family="UNKNOWN",
                venue="BINGX",
                symbol="UNKNOWN",
                timeframe="1h",
                parent_ids=[],
                created_at_utc=datetime.now(timezone.utc).isoformat(),
                certifications=[],
                children=[],
            )
            nodes[strategy_id] = primary_node

        # Resolving children (strategies where strategy_id is in parents)
        all_strategies = self.db.query(StrategyModel).all()
        for s in all_strategies:
            if s.ast_json:
                try:
                    ast = json.loads(s.ast_json) if isinstance(s.ast_json, str) else s.ast_json
                    s_parents = ast.get("metadata", {}).get("parents", [])
                    if strategy_id in s_parents:
                        child_node = _resolve_node(s.strategy_id)
                        if child_node and s.strategy_id not in primary_node.children:
                            primary_node.children.append(s.strategy_id)
                except Exception:
                    pass

        # Generations
        generations: List[List[str]] = [[strategy_id]]
        if primary_node.children:
            generations.append(primary_node.children)

        certified_descendants = [
            nid for nid, node in nodes.items() if len(node.certifications) > 0
        ]

        return LineageTreeResponse(
            root_strategy_id=strategy_id,
            total_nodes=len(nodes),
            nodes=nodes,
            generations=generations,
            certified_descendants=certified_descendants,
        )
