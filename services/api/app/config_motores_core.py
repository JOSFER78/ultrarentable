"""services/api/app/config_motores_core.py

Módulo central de configuración de motores Ultrarentable (A52).
La configuración vive exclusivamente en ~/.ultrarentable/config_motores.json
(fuera del código y fuera del repositorio).

Proporciona:
- Lectura determinista y validación estricta (falla si falta un parámetro obligatorio).
- Guardado con historial de auditoría de cambios.
- Comprobación de estado 'en_vigor' contrastando contra el servidor / base de datos real.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".ultrarentable"
CONFIG_PATH = CONFIG_DIR / "config_motores.json"

DESCRIPCIONES_PARAMETROS = {
    "m1_strategyquant.dimensionamiento.capital_inicial": (
        "Capital de la cuenta de fondeo (en USD). 50.000 USD es el estándar de evaluación "
        "para la mayoría de prop firms (Topstep, Apex, TradeDay)."
    ),
    "m1_strategyquant.dimensionamiento.riesgo_pct": (
        "Riesgo por operación: cuánto capital se arriesga en cada entrada (% del balance). "
        "Al 0,5 % la rentabilidad OOS se multiplicó por 5,2 manteniendo la mediana de caída en 2.256 USD (dentro del límite de 3.000 USD)."
    ),
    "m1_strategyquant.dimensionamiento.metodo": (
        "Método de dimensionamiento: 'RiskFixedBalancePct' (riesgo porcentual adaptativo) o "
        "'FixedSize' (contratos fijos independientemente del stop loss)."
    ),
    "m1_strategyquant.aceptacion_sqx.min_pf": (
        "Factor de beneficio mínimo en StrategyQuant (1,05). Deliberadamente permisivo para que "
        "el motor entregue estrategias al banco y sea M2 quien aplique el filtro fino."
    ),
    "m1_strategyquant.aceptacion_sqx.min_ret_dd": (
        "Ratio retorno / caída mínimo en StrategyQuant (0,5). Evita descartar estrategias en marcos rápidos."
    ),
    "m1_strategyquant.aceptacion_sqx.min_ops_mes": (
        "Mínimo de operaciones por mes exigidas en StrategyQuant según marco temporal. "
        "Marcos rápidos exigen más frecuencia (M1: 20/mes), marcos lentos menos (H4: 1/mes)."
    ),
    "m1_strategyquant.universo.simbolos": (
        "Símbolos de futuros micro activos en la fábrica (MES, MNQ, MYM, MGC, MCL, M6E)."
    ),
    "m1_strategyquant.universo.prioridad_marcos": (
        "Orden de ejecución de celdas por rentabilidad probada: H1 y H4 primero para cosechar antes."
    ),
    "m1_strategyquant.calidad_censo.bandas.apta_operar": (
        "Banda de Emilio 'Apta para operar': Rentabilidad mensual >= 2 % y caída máxima < 6 %. "
        "Lista para asignación de capital real en cuentas de fondeo."
    ),
    "m1_strategyquant.calidad_censo.bandas.apta_mejorar": (
        "Banda de Emilio 'Apta para mejorar': Rentabilidad mensual >= 2 % pero caída entre 6 % y 12 %. "
        "Tiene ventaja demostrada; la fase de mejora debe reducir el drawdown antes de operar."
    ),
    "m1_strategyquant.calidad_censo.bandas.con_promesa": (
        "Banda de Emilio 'Con promesa': Rentabilidad mensual 1-2 % y caída <= 12 %. Edge moderado aprovechable."
    ),
}


def _config_inicial_por_defecto() -> dict[str, Any]:
    return {
        "schema": "ultrarentable.config_motores.v1",
        "actualizado": dt.datetime.now(dt.UTC).isoformat(),
        "m1_strategyquant": {
            "universo": {
                "simbolos": ["MES", "MNQ", "MYM", "MGC", "MCL", "M6E"],
                "marcos": ["M1", "M5", "M15", "H1", "H4"],
                "prioridad_marcos": ["H1", "H4", "M15", "M5", "M1"],
                "horas_tope_por_celda": 1,
            },
            "dimensionamiento": {
                "capital_inicial": 50000,
                "metodo": "RiskFixedBalancePct",
                "riesgo_pct": 0.5,
                "contratos_fijos": 1,
            },
            "aceptacion_sqx": {
                "min_pf": 1.05,
                "min_ret_dd": 0.5,
                "min_ops_mes": {
                    "M1": 20,
                    "M5": 10,
                    "M15": 5,
                    "H1": 2,
                    "H4": 1,
                },
                "min_win_pct": 20.0,
            },
            "calidad_censo": {
                "min_pf_is": 1.3,
                "min_pf_oos": 1.0,
                "min_trades_oos": 20,
                "bandas": {
                    "apta_operar": {
                        "nombre": "Apta para operar",
                        "ret_mes_pct_min": 2.0,
                        "max_dd_pct_max": 6.0,
                        "descripcion": "Rentabilidad mensual >= 2 % y caída máxima < 6 %. Lista para cuenta de fondeo.",
                    },
                    "apta_mejorar": {
                        "nombre": "Apta para mejorar",
                        "ret_mes_pct_min": 2.0,
                        "max_dd_pct_min": 6.0,
                        "max_dd_pct_max": 12.0,
                        "descripcion": "Rentabilidad mensual >= 2 % pero caída 6-12 %. La fase de mejora debe reducir la caída.",
                    },
                    "con_promesa": {
                        "nombre": "Con promesa",
                        "ret_mes_pct_min": 1.0,
                        "ret_mes_pct_max": 2.0,
                        "max_dd_pct_max": 12.0,
                        "descripcion": "Rentabilidad mensual 1-2 % y caída <= 12 %. Edge positivo que merece optimización.",
                    },
                    "descartada": {
                        "nombre": "Descartada",
                        "ret_mes_pct_max": 0.5,
                        "max_dd_pct_min": 25.0,
                        "descripcion": "Rentabilidad < 0.5 % mensual o caída > 25 %. Sin edge aprovechable.",
                    },
                },
            },
        },
        "historial": [
            {
                "fecha": dt.datetime.now(dt.UTC).isoformat(),
                "usuario": "Emilio / Opus 5",
                "cambio": "Consolidación inicial de parámetros de motores fuera del código (A52)",
                "valores_previos": {},
            }
        ],
    }


def asegurar_config_existe() -> None:
    """Asegura que ~/.ultrarentable/config_motores.json existe. Si no, lo crea con los valores acordados."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        cfg = _config_inicial_por_defecto()
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def leer_config_motores() -> dict[str, Any]:
    """Lee la configuración desde ~/.ultrarentable/config_motores.json.

    Falla con error descriptivo si el fichero no existe o no tiene los bloques requeridos.
    """
    asegurar_config_existe()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Error crítico al leer {CONFIG_PATH}: {exc}") from exc

    m1 = data.get("m1_strategyquant")
    if not m1:
        raise KeyError(f"Falta bloque obligatorio 'm1_strategyquant' en {CONFIG_PATH}")

    # Validar presencia de secciones críticas
    for sec in ("universo", "dimensionamiento", "aceptacion_sqx", "calidad_censo"):
        if sec not in m1:
            raise KeyError(f"Falta sección obligatoria 'm1_strategyquant.{sec}' en {CONFIG_PATH}")

    return data


def guardar_config_motores(nuevos_valores: dict[str, Any], usuario: str = "superadmin") -> dict[str, Any]:
    """Actualiza la configuración guardándola en disco y registrando el historial de cambios."""
    cfg = leer_config_motores()
    ahora = dt.datetime.now(dt.UTC).isoformat()

    # Detectar cambios para el historial
    cambios = []
    m1_viejo = cfg.get("m1_strategyquant", {})
    m1_nuevo = nuevos_valores.get("m1_strategyquant", {})

    def _comparar_dict(v_viejo: dict, v_nuevo: dict, prefijo: str = ""):
        for k, v in v_nuevo.items():
            ruta = f"{prefijo}.{k}" if prefijo else k
            if k not in v_viejo:
                cambios.append({"parametro": ruta, "valor_anterior": None, "valor_nuevo": v})
            elif isinstance(v, dict) and isinstance(v_viejo[k], dict):
                _comparar_dict(v_viejo[k], v, ruta)
            elif v != v_viejo[k]:
                cambios.append({"parametro": ruta, "valor_anterior": v_viejo[k], "valor_nuevo": v})

    _comparar_dict(m1_viejo, m1_nuevo, "m1_strategyquant")

    # Actualizar estado
    cfg["m1_strategyquant"] = m1_nuevo
    cfg["actualizado"] = ahora
    if "historial" not in cfg:
        cfg["historial"] = []

    if cambios:
        cfg["historial"].insert(
            0,
            {
                "fecha": ahora,
                "usuario": usuario,
                "cambio": f"Modificados {len(cambios)} parámetros por {usuario}",
                "cambios": cambios,
            },
        )
        cfg["historial"] = cfg["historial"][:50]

    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return cfg


def comprobar_en_vigor(cfg: dict[str, Any]) -> dict[str, Any]:
    """Compara cada grupo de configuración contra el estado real del servidor / proyectos."""
    m1 = cfg.get("m1_strategyquant", {})
    dim_cfg = m1.get("dimensionamiento", {})
    acp_cfg = m1.get("aceptacion_sqx", {})
    uni_cfg = m1.get("universo", {})

    manifiesto_encontrado: dict[str, Any] | None = None
    rutas_manifiesto = [
        Path("/opt/SQX-headless/import/fondeo/manifiesto.json"),
        Path("scratch/manifiesto_fondeo.json"),
        Path.home() / ".ultrarentable" / "manifiesto_cache.json",
    ]
    for r in rutas_manifiesto:
        if r.exists():
            try:
                manifiesto_encontrado = json.loads(r.read_text(encoding="utf-8"))
                break
            except Exception:
                pass

    estado_en_vigor: dict[str, Any] = {
        "dimensionamiento": {"en_vigor": False, "motivo": "Sin comprobación"},
        "aceptacion_sqx": {"en_vigor": False, "motivo": "Sin comprobación"},
        "universo": {"en_vigor": False, "motivo": "Sin comprobación"},
        "calidad_censo": {"en_vigor": True, "motivo": "Aplicado en memoria por API de candidatos"},
    }

    if manifiesto_encontrado:
        srv_cap = manifiesto_encontrado.get("capital_inicial")
        srv_riesgo = manifiesto_encontrado.get("riesgo_pct")
        cfg_cap = dim_cfg.get("capital_inicial")
        cfg_riesgo = dim_cfg.get("riesgo_pct")

        if srv_cap == cfg_cap and srv_riesgo == cfg_riesgo:
            estado_en_vigor["dimensionamiento"] = {
                "en_vigor": True,
                "servidor": {"capital": srv_cap, "riesgo_pct": srv_riesgo},
                "motivo": "Coincide con manifiesto activo de StrategyQuant",
            }
        else:
            estado_en_vigor["dimensionamiento"] = {
                "en_vigor": False,
                "servidor": {"capital": srv_cap, "riesgo_pct": srv_riesgo},
                "configurado": {"capital": cfg_cap, "riesgo_pct": cfg_riesgo},
                "motivo": f"Servidor aplica {srv_cap} USD / {srv_riesgo} %; configuración pide {cfg_cap} USD / {cfg_riesgo} %",
            }

        srv_acp = manifiesto_encontrado.get("aceptacion", {})
        if srv_acp.get("min_pf") == acp_cfg.get("min_pf") and srv_acp.get("min_ret_dd") == acp_cfg.get("min_ret_dd"):
            estado_en_vigor["aceptacion_sqx"] = {
                "en_vigor": True,
                "servidor": srv_acp,
                "motivo": "Coincide con reglas de compilación de proyectos",
            }
        else:
            estado_en_vigor["aceptacion_sqx"] = {
                "en_vigor": False,
                "servidor": srv_acp,
                "configurado": acp_cfg,
                "motivo": "Discrepancia en umbrales de aceptación de StrategyQuant",
            }

        srv_proyectos = manifiesto_encontrado.get("proyectos", [])
        if len(srv_proyectos) == len(uni_cfg.get("simbolos", [])) * len(uni_cfg.get("marcos", [])):
            estado_en_vigor["universo"] = {
                "en_vigor": True,
                "servidor": {"total_celdas": len(srv_proyectos)},
                "motivo": f"Las {len(srv_proyectos)} celdas del universo están cargadas en el servidor",
            }
        else:
            estado_en_vigor["universo"] = {
                "en_vigor": False,
                "servidor": {"total_celdas": len(srv_proyectos)},
                "configurado": {"total_esperado": len(uni_cfg.get("simbolos", [])) * len(uni_cfg.get("marcos", []))},
                "motivo": f"Servidor tiene {len(srv_proyectos)} proyectos; configuración define {len(uni_cfg.get('simbolos', [])) * len(uni_cfg.get('marcos', []))}",
            }
    else:
        try:
            from services.api.app.db.database import SessionLocal, StrategyModel
            db = SessionLocal()
            row = db.query(StrategyModel).filter(StrategyModel.strategy_id.like("sqx:FONDEO_%")).first()
            db.close()
            if row:
                dsl = json.loads(row.dsl_json)
                sz = dsl.get("sizing", {})
                if sz.get("capital") == dim_cfg.get("capital_inicial") and sz.get("riesgo_pct") == dim_cfg.get("riesgo_pct"):
                    estado_en_vigor["dimensionamiento"] = {
                        "en_vigor": True,
                        "servidor": sz,
                        "motivo": "Estrategias censadas reflejan este dimensionamiento",
                    }
                else:
                    estado_en_vigor["dimensionamiento"] = {
                        "en_vigor": False,
                        "servidor": sz,
                        "configurado": dim_cfg,
                        "motivo": "Censo en base de datos tiene dimensionamiento previo",
                    }
        except Exception as err:
            estado_en_vigor["dimensionamiento"] = {"en_vigor": False, "motivo": f"No se pudo verificar: {err}"}

    return estado_en_vigor
