"""Andamio de hipótesis fijas (SOLO para pruebas del mecanismo).

Emilio (2026-09-06): las hipótesis las proponen agentes que analizan cada
estrategia; una biblioteca fija no es el diseño del motor. Este módulo conserva
las tres reglas usadas en la entrega 1 para reproducir aquel experimento y para
probar el ciclo sin red. El servicio autónomo no lo usa.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sqx_variant_mutations as mutations  # noqa: E402


HYPOTHESIS_LIBRARY = {
    'H_PT_NEAR': {
        'title': 'Acercar el objetivo de beneficio',
        'problem': 'El objetivo casi nunca se alcanza y se devuelve gran parte del recorrido favorable.',
        'change': 'Multiplicador ATR del objetivo × 0.6 en ambas direcciones.',
        'expected': 'Más salidas por objetivo, menor devolución, mayor tasa de acierto; riesgo de recortar las operaciones grandes.',
        'destination_expectation': {'fondeo': 'sube la tasa de objetivo a 5 días', 'ultra': 'probablemente reduce la convexidad'},
        'requires': ['PT_RARELY_HIT'],
        'supporting': ['HIGH_GIVEBACK_FROM_MFE', 'LOSERS_AFTER_FAVOURABLE_EXCURSION'],
    },
    'H_TS_TIGHT': {
        'title': 'Activar antes y ceñir el stop dinámico',
        'problem': 'Las operaciones ganadoras devuelven una parte grande de su máximo recorrido favorable.',
        'change': 'Nivel de activación del trailing × 0.5 y distancia del trailing × 0.5 en ambas direcciones.',
        'expected': 'Menor devolución desde el MFE conservando las operaciones largas cuando la tendencia continúa.',
        'destination_expectation': {'fondeo': 'menos días perdedores tras un recorrido favorable', 'ultra': 'conserva cola derecha con menor devolución'},
        'requires': [],
        'requires_any': ['HIGH_GIVEBACK_FROM_MFE', 'LOSERS_AFTER_FAVOURABLE_EXCURSION'],
    },
    'H_SL_TIGHT': {
        'title': 'Reducir el stop inicial',
        'problem': 'Una parte alta de las salidas es por stop y concentra las pérdidas.',
        'change': 'Stop inicial × 0.7 en ambas direcciones.',
        'expected': 'Pérdidas medias menores; riesgo de más stops tocados por ruido.',
        'destination_expectation': {'fondeo': 'menor ruptura de límites', 'ultra': 'mayor R por operación si la entrada es precisa'},
        'requires': ['SL_HIT_SHARE_HIGH'],
    },
}


def hypothesis_changes(hid: str, rules: bytes) -> list[dict]:
    changes = []
    for direction in ('long', 'short'):
        if hid == 'H_PT_NEAR':
            current = mutations.read_exit(rules, direction, 'profit_target')
            if not current or 'Value' not in current:
                raise ValueError(f'Sin objetivo con valor en {direction}')
            changes.append({'direction': direction, 'exit': 'profit_target', 'value': mutations.scaled(current['Value'], 0.6, 2)})
        elif hid == 'H_TS_TIGHT':
            for exit_name in ('trailing_activation', 'trailing_stop'):
                current = mutations.read_exit(rules, direction, exit_name)
                if not current or 'Value' not in current or current['formula'] is None or current['formula'].endswith('.None'):
                    raise ValueError(f'Sin {exit_name} configurado en {direction}')
                changes.append({'direction': direction, 'exit': exit_name, 'value': mutations.scaled(current['Value'], 0.5, 2)})
        elif hid == 'H_SL_TIGHT':
            current = mutations.read_exit(rules, direction, 'stop_loss')
            if not current or 'Value' not in current:
                raise ValueError(f'Sin stop con valor en {direction}')
            changes.append({'direction': direction, 'exit': 'stop_loss', 'value': mutations.scaled(current['Value'], 0.7, 1)})
        else:
            raise ValueError('Hipótesis desconocida')
    return changes


