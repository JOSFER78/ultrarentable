#!/usr/bin/env python3
"""
SQX GUI Automation Tool via xdotool & ImageMagick import on Xvfb :99.
Provides reliable window discovery, click navigation, and screenshot capturing for StrategyQuant X.
"""

import os
import sys
import time
import subprocess
import logging
from typing import Optional, Tuple, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DISPLAY = os.environ.get("DISPLAY", ":99")
XAUTHORITY = os.environ.get("XAUTHORITY", "/home/ubuntu/.Xauthority")
DEFAULT_IMG_DIR = "/home/ubuntu/.hermes/profiles/default/images"

NAV_COORDINATES: Dict[str, Tuple[int, int]] = {
    "data_manager": (150, 115),
    "builder": (280, 115),
    "retester": (400, 115),
    "optimizer": (520, 115),
    "algowizard": (650, 115),
    "custom_indicators": (780, 115),
}

def setup_env():
    os.environ["DISPLAY"] = DISPLAY
    os.environ["XAUTHORITY"] = XAUTHORITY

def find_sqx_window() -> Optional[str]:
    """Find SQX main window ID using xdotool."""
    setup_env()
    try:
        cmd = ["xdotool", "search", "--onlyvisible", "--name", "StrategyQuant"]
        res = subprocess.check_output(cmd).decode().strip().split()
        if res:
            return res[0]
        # Fallback to any window matching StrategyQuant
        cmd = ["xdotool", "search", "--name", "StrategyQuant"]
        res = subprocess.check_output(cmd).decode().strip().split()
        for w in res:
            geom = subprocess.check_output(["xdotool", "getwindowgeometry", w]).decode()
            if "1920x" in geom or "1800x" in geom:
                return w
        return res[0] if res else None
    except Exception as e:
        logging.error(f"Failed to find SQX window: {e}")
        return None

def capture_window(wid: str, filename: str, output_dir: str = DEFAULT_IMG_DIR) -> str:
    """Capture screenshot of the specified window ID and save with 644 permissions."""
    setup_env()
    os.makedirs(output_dir, exist_ok=True)
    tmp_path = f"/tmp/{filename}"
    dst_path = os.path.join(output_dir, filename)
    
    subprocess.run(["import", "-window", wid, tmp_path], check=True)
    subprocess.run(["cp", tmp_path, dst_path], check=True)
    os.chmod(dst_path, 0o644)
    logging.info(f"Captured window {wid} -> {dst_path}")
    return dst_path

def click_nav_tab(tab_name: str, wait_sec: float = 1.0) -> Optional[str]:
    """Click on a navigation tab by name and take a screenshot."""
    if tab_name not in NAV_COORDINATES:
        raise ValueError(f"Unknown tab '{tab_name}'. Valid tabs: {list(NAV_COORDINATES.keys())}")
    
    wid = find_sqx_window()
    if not wid:
        logging.error("SQX Window not found!")
        return None
    
    x, y = NAV_COORDINATES[tab_name]
    setup_env()
    logging.info(f"Clicking tab '{tab_name}' at ({x}, {y}) on window {wid}...")
    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], check=True)
    time.sleep(wait_sec)
    
    img_name = f"sqx_click_{tab_name}.png"
    return capture_window(wid, img_name)

if __name__ == "__main__":
    logging.info("Testing SQX GUI Automation module...")
    w_id = find_sqx_window()
    if w_id:
        logging.info(f"Found SQX Window ID: {w_id}")
        cap = capture_window(w_id, "sqx_gui_module_test.png")
        print(f"Captured: {cap}")
    else:
        logging.error("SQX window not found.")
