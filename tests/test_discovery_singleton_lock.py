"""tests/test_discovery_singleton_lock.py — Auditoría del candado de proceso singleton en discovery.

Verifica que `_acquire_singleton_lock()` en `services/discovery/discovery_validation_pipeline.py`:
1. No falla en silencio ni traga excepciones con `pass`.
2. En entornos sin `fcntl` (como Windows), emite un aviso explícito por stdout:
   `[DISCOVERY] AVISO: candado de instancia única no disponible en este sistema (sin fcntl); ejecución sin protección de instancia`
3. En el código fuente no queda ningún patrón `except (ImportError, OSError): pass`.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from services.discovery.discovery_validation_pipeline import _acquire_singleton_lock


def test_acquire_singleton_lock_emits_warning_without_fcntl(capsys):
    """En sistemas sin fcntl (como Windows nativo), _acquire_singleton_lock emite un aviso explícito."""
    _acquire_singleton_lock()
    captured = capsys.readouterr()

    if os.name == "nt":
        assert "AVISO: candado de instancia única no disponible" in captured.out
        assert "[DISCOVERY]" in captured.out


def test_no_silent_pass_in_discovery_pipeline_source():
    """El fichero services/discovery/discovery_validation_pipeline.py no debe silenciar errores con pass."""
    pipeline_file = (
        Path(__file__).resolve().parent.parent
        / "services"
        / "discovery"
        / "discovery_validation_pipeline.py"
    )
    source = pipeline_file.read_text(encoding="utf-8")

    assert "except (ImportError, OSError): pass" not in source
    assert "AVISO: candado de instancia" in source
