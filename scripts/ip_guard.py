#!/usr/bin/env python3
"""
IP Guard — Vigilante de identidad de red para Ultrarentable (VPS ARM64).

Función única y estable:
  1. Comprueba la IP pública de salida del tráfico de TRADING.
  2. Si NO es la esperada → estado ERROR (fail-closed): el runner de trading
     debe leer este estado y cancelar órdenes / no operar.
  3. Imprime un informe claro apto para cron de Hermes.

Diseño REAL-ONLY:
  - No inventa nada: consulta https://ipinfo.io/json real.
  - Sin dependencias externas (solo stdlib).
  - Exit codes: 0=OK, 1=MISMATCH, 2=SIN DATOS (red caída) → fail-closed también.

Uso:
  python3 ip_guard.py                       # compara contra EXPECTED_IP del propio archivo
  EXPECTED_IP=1.2.3.4 python3 ip_guard.py   # override por entorno

Instalación como cron Hermes (propuesta):
  cada 5 min → python3 .../ip_guard.py  (deliver al chat solo si exit != 0)
"""
import json
import os
import sys
import urllib.request

# ── Configuración (editar aquí cuando cambie la IP contratada) ──────────
# Escenario A (IP Oracle directa): dejar la estática actual.
# Escenario B (proxy ISP residencial): poner aquí la IP residencial contratada
#   y hacer que el proceso de trading salga POR EL PROXY (ver doc 09).
EXPECTED_IP = os.environ.get("EXPECTED_IP", "143.47.35.167")
# Proxy opcional para la comprobación (el mismo que usará el trading):
PROXY = os.environ.get("TRADING_PROXY")  # ej. "socks5h://user:pass@host:port" vía PySocks
TIMEOUT = 10


def fetch_ip() -> dict | None:
    try:
        req = urllib.request.Request(
            "https://ipinfo.io/json", headers={"User-Agent": "ultrarentable-ipguard/1.0"}
        )
        if PROXY:
            handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(handler)
        else:
            opener = urllib.request.build_opener()
        with opener.open(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"SIN_DATOS error={e}", file=sys.stderr)
        return None


def main() -> int:
    data = fetch_ip()
    if not data or "ip" not in data:
        print("🔴 IP-GUARD: SIN DATOS — red no responde → FAIL-CLOSED (no operar)")
        return 2

    ip = data["ip"]
    org = data.get("org", "?")
    city = f'{data.get("city","?")},{data.get("country","?")}'

    print(f"IP actual : {ip}")
    print(f"ASN       : {org}")
    print(f"Geo       : {city}")
    print(f"Esperada  : {EXPECTED_IP}")

    if ip != EXPECTED_IP:
        print("🔴 IP-GUARD: MISMATCH — la IP de salida CAMBIÓ → FAIL-CLOSED (cancelar/no abrir órdenes)")
        return 1

    print("🟢 IP-GUARD: OK — identidad de red estable, se puede operar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
