"""services/api/app/api/config_router.py

Router para la gestión centralizada de configuración de motores (A52).
Permite consultar, editar y documentar todos los parámetros de StrategyQuant (M1),
sus bandas de extracción y el estado 'en_vigor' en el servidor físico.
"""

from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.api.app.config_motores_core import (
    leer_config_motores,
    guardar_config_motores,
    comprobar_en_vigor,
    DESCRIPCIONES_PARAMETROS,
    CONFIG_PATH,
)

router = APIRouter()


class ConfigMotoresUpdate(BaseModel):
    m1_strategyquant: dict[str, Any]
    usuario: str = "superadmin"


@router.get("/motores")
def obtener_configuracion_motores() -> dict[str, Any]:
    """Devuelve la configuración completa de motores, sus descripciones explicativas,

    el historial de cambios y el estado 'en_vigor' en el servidor.
    """
    try:
        cfg = leer_config_motores()
        en_vigor = comprobar_en_vigor(cfg)
        return {
            "config": cfg,
            "descripciones": DESCRIPCIONES_PARAMETROS,
            "en_vigor": en_vigor,
            "origen": str(CONFIG_PATH),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al leer configuración de motores: {exc}",
        )


@router.post("/motores")
def actualizar_configuracion_motores(body: ConfigMotoresUpdate) -> dict[str, Any]:
    """Actualiza la configuración de motores y registra la traza en el historial."""
    try:
        cfg_actualizada = guardar_config_motores(
            nuevos_valores={"m1_strategyquant": body.m1_strategyquant},
            usuario=body.usuario,
        )
        en_vigor = comprobar_en_vigor(cfg_actualizada)
        return {
            "ok": True,
            "mensaje": "Configuración guardada correctamente en ~/.ultrarentable/config_motores.json",
            "config": cfg_actualizada,
            "en_vigor": en_vigor,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al guardar configuración de motores: {exc}",
        )
