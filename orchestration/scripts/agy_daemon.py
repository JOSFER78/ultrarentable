#!/usr/bin/env python3
"""
orchestration/scripts/agy_daemon.py — Daemon ejecutor en segundo plano para Antigravity.

Monitorea continuamente orchestration/state/status.json.
Cuando detecta status == 'pending':
  1. Marca status = 'in_progress'
  2. Ejecuta la fase correspondiente de forma determinista y física (REAL-ONLY)
  3. Genera el informe de evidencias en orchestration/results/fase_<NN>.log
  4. Actualiza status = 'done' (o 'needs_user_input' ante error crítico)
"""

import json
import logging
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ORCH_DIR = BASE_DIR / "orchestration"
STATE_DIR = ORCH_DIR / "state"
RESULTS_DIR = ORCH_DIR / "results"
LOGS_DIR = ORCH_DIR / "logs"
STATUS_FILE = STATE_DIR / "status.json"
CURRENT_PHASE_FILE = STATE_DIR / "current_phase.md"
DAEMON_LOG = LOGS_DIR / "agy_daemon.log"

API_BASE = "http://localhost:5050/call"
PROJECT_NAME = "Ultra_Matrix"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Logger setup
logging.basicConfig(
    filename=str(DAEMON_LOG),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def sqx_call(cmd: str, timeout: int = 30) -> str:
    """Envía un comando a la API de SQX en el puerto 5050."""
    url = f"{API_BASE}?cmd={urllib.parse.quote(cmd)}"
    req = urllib.request.Request(url, headers={"User-Agent": "AntigravityDaemon/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception as e:
        logging.error(f"Error llamando a SQX API ({cmd}): {e}")
        raise


def get_status() -> dict:
    if not STATUS_FILE.exists():
        return {}
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error leyendo status.json: {e}")
        return {}


def set_status(status: str, phase_number: int, history_entry: dict = None) -> None:
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    current = get_status()
    current["phase_number"] = phase_number
    current["status"] = status
    current["last_updated"] = now_iso
    if "history" not in current:
        current["history"] = []
    if history_entry:
        current["history"].append(history_entry)

    temp_file = STATUS_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)
        f.write("\n")
    temp_file.replace(STATUS_FILE)
    logging.info(f"Estado actualizado a: {status} (fase {phase_number})")


def execute_phase_1() -> tuple[bool, str]:
    """Ejecuta la Fase 1: Captura de 'Last generation' -> ToImprove + export CSV."""
    log_lines = []
    start_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_lines.append(f"=== INFORME DE EJECUCIÓN FASE 01 — {start_time} ===")
    log_lines.append("Subagente: Antigravity Autonomous Daemon (REAL-ONLY / ZERO-MOCKS)\n")

    # 1. Guard previo: verificar si el proyecto está corriendo y detenerlo ordenadamente
    log_lines.append("--- [Paso 1: Verificación y Parada de Motor SQX] ---")
    status_output = sqx_call(f"-project action=status name={PROJECT_NAME}")
    log_lines.append(f"Output status inicial:\n{status_output.strip()}\n")

    if "Tiempo de funcionamiento" in status_output or "running" in status_output.lower():
        log_lines.append("El proyecto está en ejecución. Enviando comando stop...")
        stop_output = sqx_call(f"-project action=stop name={PROJECT_NAME}")
        log_lines.append(f"Output stop:\n{stop_output.strip()}\n")

        # Esperar hasta que esté detenido (máximo 60s)
        stopped = False
        for i in range(12):
            time.sleep(5)
            check_status = sqx_call(f"-project action=status name={PROJECT_NAME}")
            if "Tiempo de funcionamiento" not in check_status and "running" not in check_status.lower():
                stopped = True
                log_lines.append(f"Confirmado proyecto PARADO tras {(i+1)*5}s.")
                break
        if not stopped:
            error_msg = "GUARD FALLIDO: No se pudo confirmar la parada del proyecto."
            log_lines.append(f"ERROR: {error_msg}")
            return False, "\n".join(log_lines)
    else:
        log_lines.append("Confirmado proyecto ya PARADO.")

    # 2. Listado de bancos antes de la copia
    log_lines.append("\n--- [Paso 2: Listado de Databanks Antes de Copia] ---")
    list_before = sqx_call(f"-databank action=list project={PROJECT_NAME}")
    log_lines.append(f"Output list antes:\n{list_before.strip()}\n")

    # 3. Copia Last generation -> ToImprove
    log_lines.append("--- [Paso 3: Copia de Databank Last generation -> ToImprove] ---")
    copy_cmd = f"-databank action=copy project={PROJECT_NAME} name=Last generation destproject={PROJECT_NAME} destdatabank=ToImprove"
    copy_output = sqx_call(copy_cmd)
    log_lines.append(f"Comando: {copy_cmd}")
    log_lines.append(f"Output copy:\n{copy_output.strip()}\n")

    # 4. Listado de bancos después de la copia + Guard ToImprove > 0
    log_lines.append("--- [Paso 4: Verificación Post-Copia] ---")
    list_after = sqx_call(f"-databank action=list project={PROJECT_NAME}")
    log_lines.append(f"Output list tras copia:\n{list_after.strip()}\n")

    to_improve_count = 0
    for line in list_after.splitlines():
        if "ToImprove" in line:
            parts = line.split("Records:")
            if len(parts) > 1:
                try:
                    to_improve_count = int(parts[1].strip())
                except ValueError:
                    pass

    log_lines.append(f"Registros en ToImprove detectados: {to_improve_count}")
    if to_improve_count <= 0:
        error_msg = f"GUARD FALLIDO: ToImprove Records = {to_improve_count} (esperado > 0)."
        log_lines.append(f"ERROR: {error_msg}")
        return False, "\n".join(log_lines)

    # 5. Exportación CSV de evidencia
    log_lines.append("\n--- [Paso 5: Exportación CSV de Evidencia] ---")
    ord_dir = Path("/home/ubuntu/ORDENAR")
    ord_dir.mkdir(parents=True, exist_ok=True)
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = ord_dir / f"semillas_{ts_str}.csv"

    export_cmd = f"-databank action=export project={PROJECT_NAME} name=Last generation file={csv_file}"
    export_output = sqx_call(export_cmd)
    log_lines.append(f"Comando: {export_cmd}")
    log_lines.append(f"Output export:\n{export_output.strip()}\n")

    # Esperar unos segundos a que el archivo se termine de escribir
    time.sleep(3)

    if not csv_file.exists():
        error_msg = f"GUARD FALLIDO: Archivo CSV no encontrado en {csv_file}"
        log_lines.append(f"ERROR: {error_msg}")
        return False, "\n".join(log_lines)

    file_size = csv_file.stat().st_size
    line_count = 0
    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        line_count = sum(1 for _ in f)

    log_lines.append(f"Archivo CSV creado: {csv_file}")
    log_lines.append(f"Tamaño del archivo: {file_size} bytes")
    log_lines.append(f"Total líneas en CSV: {line_count}")

    if line_count < 2 or file_size == 0:
        error_msg = f"GUARD FALLIDO: CSV vacío o con menos líneas de las esperadas ({line_count} líneas)."
        log_lines.append(f"ERROR: {error_msg}")
        return False, "\n".join(log_lines)

    log_lines.append("\n--- [Paso 6: Cierre y Resumen de Evidencias] ---")
    log_lines.append("✓ Guard previo: Proyecto PARADO confirmado.")
    log_lines.append(f"✓ Copia completada: ToImprove cuenta con {to_improve_count} estrategias.")
    log_lines.append(f"✓ CSV de evidencia exportado físicamente en {csv_file} ({line_count} líneas).")
    log_lines.append("✓ Cero archivos de código ni configuración tocados.")
    log_lines.append(f"Fin de Fase 01: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")

    return True, "\n".join(log_lines)


def run_daemon_loop():
    """
    MODO SOLO-VIGILANCIA (seguro): este daemon YA NO ejecuta fases.
    Solo vigila señales y estado y lo registra en su log. La ejecución real
    la hace Antigravity (IDE) siguiendo current_phase.md + señales GO/DONE.
    """
    logging.info("Daemon en MODO SOLO-VIGILANCIA (no ejecuta fases; no toca el motor).")
    last_phase_seen = None
    while True:
        try:
            status_data = get_status()
            current_status = status_data.get("status")
            phase_number = status_data.get("phase_number")

            if (current_status, phase_number) != last_phase_seen:
                logging.info("Estado: status=%s phase=%s (solo registro, sin ejecutar)",
                             current_status, phase_number)
                last_phase_seen = (current_status, phase_number)

            time.sleep(30)
        except Exception as e:
            logging.error(f"Error inesperado en loop del daemon: {e}", exc_info=True)
            time.sleep(30)


if __name__ == "__main__":
    run_daemon_loop()
