"""services/portfolio/__init__.py
Módulo Autónomo de Meta-Estrategias, Ensamblado de Portafolios y Paridad de Riesgo 24/7.
"""
from services.portfolio.autonomous_meta_daemon import autonomous_meta_daemon, AutonomousMetaDaemon
from services.portfolio.meta_ensemble_service import MetaEnsembleService
from services.portfolio.portfolio_router import router

__all__ = ["autonomous_meta_daemon", "AutonomousMetaDaemon", "MetaEnsembleService", "router"]
# 2026-09-01 (W6.0/D8): portfolio_engine.py a cuarentena (fabricaba retornos y matriz identidad).
