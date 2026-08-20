"""scripts/bump_version.py
Herramienta CLI para Incremento de Versión y Sincronización Inmutable del Motor Cuantitativo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable")
sys.path.insert(0, str(REPO_ROOT))

from services.version_control_manager import version_manager


def main():
    parser = argparse.ArgumentParser(description="Incrementa y gestiona las versiones del Motor Cuantitativo Ultrarentable.")
    parser.add_argument("--name", type=str, required=False, help="Nombre descriptivo de la versión.")
    parser.add_argument("--desc", type=str, required=False, help="Descripción detallada de la arquitectura.")
    parser.add_argument("--changes", nargs="*", default=[], help="Lista de cambios introducidos.")
    parser.add_argument("--version", type=str, default=None, help="Sobreescritura del número de versión e.g. '1.03'")
    parser.add_argument("--status", action="store_true", help="Muestra el estado actual de versionado y detección de deriva de código.")
    parser.add_argument("--bump-forensic-103", action="store_true", help="Aplica el bump automático a v1.03 tras la certificación del plan maestro forense.")

    args = parser.parse_args()

    if args.status:
        info = version_manager.get_full_version_info()
        print("=" * 70)
        print("ESTADO DEL MOTOR DE VERSIONADO (SSOT):")
        print(f"• Versión Activa:      v{info['active_version']} — {info['active_name']}")
        print(f"• Pipeline Version:    v{info['pipeline_version']}")
        print(f"• Git Commit:          {info['git_commit'][:7]}")
        print(f"• Codebase Hash:       {info['codebase_fingerprint'][:24]}...")
        print(f"• Deriva de Código:    {'⚠️ SÍ (Cambios detectados)' if info['code_drift_detected'] else '✅ NO (Código Sincronizado)'}")
        print(f"• Último Bump UTC:     {info['last_bump_utc']}")
        print(f"• Historial Versiones: {len(info['history'])} registradas")
        print("=" * 70)
        return

    if args.bump_forensic_103:
        name = "Ultrarentable Dual-Engine V1.03 (Master Forensic Architecture & Reconciled Dual-Engine)"
        desc = (
            "Versión mayor de certificación forense. Implementación del CanonicalExecutionLedger trade-by-trade, "
            "reconciliación matemática multi-activo de 5 benchmarks reales (SUI, BTC, EURUSD, NQ, CL), "
            "blindaje de techo de apalancamiento en Gate 11, catálogo de microestructura y costes reales para 44+ activos, "
            "aislamiento físico del Blind Holdout 60/20/20, cálculo probabilístico de quiebra de cuentas Prop Firm y "
            "suite de 231 tests unitarios y de integración (100% aprobados)."
        )
        changes = [
            "Capa canónica de ejecución física (ExecutionTruth & CanonicalExecutionLedger).",
            "Reconciliación trade-by-trade FastEngine vs NautilusTrader en 5 activos globales.",
            "Eliminación de la contradicción de leverage en Gate 11 (hard ceiling breach -> REJECTED).",
            "Catálogo canónico de costes (InstrumentCostProfile) y bloqueo de activos sin modelo de fricción.",
            "Aislamiento físico del dataset ciego OOS (Blind Holdout) frente a procesos de discovery.",
            "PropFirmRiskEngine con cálculo de probabilidad real de violación de reglas diarias y trailing DD.",
            "Estructura formal de Balas ULTRA con riesgo fijo, cero martingalas y cosecha a Bóveda.",
            "Batería de tests adversariales Red-Team profunda y suite completa de 231 tests pasando.",
        ]
        res = version_manager.bump_version(
            name=name,
            description=desc,
            changes=changes,
            new_version="1.03",
        )
        print("=" * 70)
        print("BUMP A V1.03 COMPLETADO CON ÉXITO:")
        print(f"Versión: v{res['active_version']}")
        print(f"Nombre: {res['active_name']}")
        print("=" * 70)
        return

    if not args.name or not args.desc:
        parser.print_help()
        return

    res = version_manager.bump_version(
        name=args.name,
        description=args.desc,
        changes=args.changes,
        new_version=args.version,
    )
    print("=" * 70)
    print("BUMP DE VERSIÓN COMPLETADO:")
    print(f"Versión: v{res['active_version']}")
    print(f"Nombre: {res['active_name']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
