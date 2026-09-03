"""Router de Proveedor de IA (V2).

Permite configurar de forma dinámica el proveedor de IA (nombre, endpoint, modelo, api_key),
probar la conexión real y enviar consultas desde la web.

SEGURIDAD Y ZERO-MOCKS:
- La clave API se almacena exclusivamente en el servidor (~/.ultrarentable/ia_config.json,
  fuera del repositorio git).
- El endpoint de lectura GET /api/v2/ia/proveedor NUNCA devuelve la clave al cliente/navegador;
  únicamente expone los metadatos públicos y la bandera `tiene_clave: bool`.
- Cero respuestas simuladas: si el proveedor no está configurado o falla, se reporta el error real.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

_CONFIG_DIR = os.path.expanduser("~/.ultrarentable")
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "ia_config.json")


def _asegurar_directorio() -> None:
    if not os.path.exists(_CONFIG_DIR):
        os.makedirs(_CONFIG_DIR, exist_ok=True)


def _leer_config_disco() -> dict[str, Any]:
    if not os.path.exists(_CONFIG_PATH):
        return {}
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _guardar_config_disco(cfg: dict[str, Any]) -> None:
    _asegurar_directorio()
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


class IAConfigPublica(BaseModel):
    configurado: bool
    nombre: str = ""
    endpoint: str = ""
    modelo: str = ""
    tiene_clave: bool = False
    origen_almacenamiento: str = "servidor (~/.ultrarentable/ia_config.json)"


class IAConfigGuardar(BaseModel):
    nombre: str
    endpoint: str
    modelo: str
    api_key: Optional[str] = None


class IAProbarResponse(BaseModel):
    ok: bool
    status_code: int
    detalle: str


class IACompletarRequest(BaseModel):
    prompt: str


class IACompletarResponse(BaseModel):
    respuesta: str
    modelo: str
    proveedor: str


@router.get("/proveedor", response_model=IAConfigPublica)
def obtener_proveedor() -> IAConfigPublica:
    """Devuelve la configuración del proveedor sin revelar la clave secreta."""
    cfg = _leer_config_disco()
    if not cfg or not cfg.get("endpoint"):
        return IAConfigPublica(
            configurado=False,
            nombre="",
            endpoint="",
            modelo="",
            tiene_clave=False,
        )

    return IAConfigPublica(
        configurado=True,
        nombre=cfg.get("nombre", ""),
        endpoint=cfg.get("endpoint", ""),
        modelo=cfg.get("modelo", ""),
        tiene_clave=bool(cfg.get("api_key")),
    )


@router.post("/proveedor", response_model=IAConfigPublica)
def guardar_proveedor(payload: IAConfigGuardar) -> IAConfigPublica:
    """Guarda la configuración del proveedor en disco seguro en el servidor."""
    existente = _leer_config_disco()
    api_key = payload.api_key
    if api_key is None or api_key == "":
        # Mantener la clave existente si no se proporciona una nueva
        api_key = existente.get("api_key", "")

    nueva_cfg = {
        "nombre": payload.nombre.strip(),
        "endpoint": payload.endpoint.strip().rstrip("/"),
        "modelo": payload.modelo.strip(),
        "api_key": api_key,
    }
    _guardar_config_disco(nueva_cfg)

    return IAConfigPublica(
        configurado=True,
        nombre=nueva_cfg["nombre"],
        endpoint=nueva_cfg["endpoint"],
        modelo=nueva_cfg["modelo"],
        tiene_clave=bool(nueva_cfg["api_key"]),
    )


@router.post("/probar", response_model=IAProbarResponse)
def probar_proveedor() -> IAProbarResponse:
    """Realiza una petición real al endpoint configurado y devuelve el código HTTP y las primeras líneas."""
    cfg = _leer_config_disco()
    if not cfg or not cfg.get("endpoint"):
        return IAProbarResponse(
            ok=False,
            status_code=400,
            detalle="No hay proveedor de IA configurado en el servidor.",
        )

    endpoint = cfg["endpoint"].rstrip("/")
    api_key = cfg.get("api_key", "")

    # Determinar URL de sondeo: si el endpoint termina en /v1, consultar /models; si no, intentar /models o la base
    url_test = f"{endpoint}/models" if not endpoint.endswith("/models") else endpoint

    headers = {
        "User-Agent": "Ultrarentable-IA-Client/1.0",
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url_test, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()[:500].decode("utf-8", errors="replace")
            return IAProbarResponse(
                ok=200 <= resp.status < 300,
                status_code=resp.status,
                detalle=f"HTTP {resp.status} OK: {body.strip()}",
            )
    except urllib.error.HTTPError as he:
        err_body = he.read()[:500].decode("utf-8", errors="replace")
        return IAProbarResponse(
            ok=False,
            status_code=he.code,
            detalle=f"HTTP {he.code} Error: {err_body.strip()}",
        )
    except Exception as exc:
        return IAProbarResponse(
            ok=False,
            status_code=500,
            detalle=f"Error de conexión ({exc.__class__.__name__}): {str(exc)}",
        )


@router.post("/completar", response_model=IACompletarResponse)
def completar_consulta(payload: IACompletarRequest) -> IACompletarResponse:
    """Envía una consulta real al proveedor configurado y devuelve la respuesta del modelo."""
    if not payload.prompt or not payload.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El prompt de consulta no puede estar vacío.",
        )

    cfg = _leer_config_disco()
    if not cfg or not cfg.get("endpoint"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta configurar el proveedor de IA en el panel de superadmin.",
        )

    endpoint = cfg["endpoint"].rstrip("/")
    api_key = cfg.get("api_key", "")
    modelo = cfg.get("modelo", "")

    # URL estándar de chat completions
    if "/chat/completions" in endpoint:
        url_chat = endpoint
    elif endpoint.endswith("/v1"):
        url_chat = f"{endpoint}/chat/completions"
    else:
        url_chat = f"{endpoint}/v1/chat/completions"

    body_dict = {
        "model": modelo,
        "messages": [
            {"role": "user", "content": payload.prompt.strip()}
        ],
        "temperature": 0.2,
    }
    data = json.dumps(body_dict).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Ultrarentable-IA-Client/1.0",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url_chat, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            choices = res_json.get("choices", [])
            if choices and "message" in choices[0]:
                texto = choices[0]["message"].get("content", "")
            else:
                texto = json.dumps(res_json, indent=2)

            return IACompletarResponse(
                respuesta=texto,
                modelo=modelo,
                proveedor=cfg.get("nombre", "Configurado"),
            )
    except urllib.error.HTTPError as he:
        err_msg = he.read()[:500].decode("utf-8", errors="replace")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error upstream de la IA (HTTP {he.code}): {err_msg}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo de conexión con el proveedor de IA: {str(exc)}",
        )
