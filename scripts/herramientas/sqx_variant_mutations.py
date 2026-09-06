"""Mutaciones verificadas sobre las reglas de una estrategia SQX.

Cada variante es una lista de cambios explícitos (dirección, parámetro de
salida, valor nuevo). Tras aplicar los cambios se comprueba que las reglas
resultantes difieren del original exactamente en los parámetros previstos y en
nada más, y que el cambio no es solo de metadatos. No ejecuta backtests.

Solo biblioteca estándar.
"""
from __future__ import annotations

import copy
import json
import xml.etree.ElementTree as ET
from decimal import Decimal

from sqx_strategy_contract import compare_rules, semantic_rules_sha256

ENTRY_RULES = {'long': 'Long entry', 'short': 'Short entry'}
EXIT_KEYS = {
    'profit_target': '#ProfitTarget.ProfitTarget#',
    'stop_loss': '#StopLoss.StopLoss#',
    'trailing_stop': '#TrailingStop.TrailingStop#',
    'trailing_activation': '#TrailingStop.TrailingActivation#',
    'move_sl_to_be': '#MoveSL2BE.MoveSL2BE#',
    'exit_after_bars': '#ExitAfterBars.ExitAfterBars#',
}
FORMULA_VALUE_KEYS = {
    'SQ.Formulas.SLPT.FixedValue': ('#Value#',),
    'SQ.Formulas.SLPT.ATRBasedValue': ('#Value#', '#AtrPeriod#'),
    'SQ.Formulas.SLPT.PctValue': ('#Value#',),
    'SQ.Formulas.RangeLevel.FixedValue': ('#Value#',),
    'SQ.Formulas.RangeLevel.ATRBasedValue': ('#Value#', '#AtrPeriod#'),
    'SQ.Formulas.Range.FixedValue': ('#Value#',),
    'SQ.Formulas.Range.ATRBasedValue': ('#Value#', '#AtrPeriod#'),
}


def _entry_action(root: ET.Element, direction: str) -> ET.Element:
    rule_name = ENTRY_RULES[direction]
    rules = root.findall(f"Strategy/Rules/Events/Event[@key='OnBarUpdate']/Rule[@name='{rule_name}']")
    if len(rules) != 1:
        raise ValueError(f'Se esperaba exactamente una regla "{rule_name}"; hay {len(rules)}')
    actions = rules[0].findall('Then/Item')
    if len(actions) != 1 or not (actions[0].get('key') or '').startswith('Enter'):
        raise ValueError(f'La regla "{rule_name}" no tiene una única acción de entrada')
    return actions[0]


def read_exit(rules_xml: bytes, direction: str, exit_name: str) -> dict:
    """Formula y valores actuales de una salida; None si no existe."""
    root = ET.fromstring(rules_xml)
    action = _entry_action(root, direction)
    params = action.findall(f"Param[@key='{EXIT_KEYS[exit_name]}']")
    if len(params) != 1:
        return None
    formula = params[0].find('Formula')
    if formula is None:
        return {'formula': None, 'value': (params[0].text or '').strip()}
    values = {p.get('key'): (p.text or '').strip() for p in formula.findall('Param')}
    return {'formula': formula.get('key'), **{k.strip('#'): v for k, v in values.items()}}


def apply_change(rules_xml: bytes, change: dict) -> tuple[bytes, dict]:
    """Aplica un cambio {direction, exit, value?, atr_period?} y devuelve (xml, registro)."""
    direction, exit_name = change['direction'], change['exit']
    if direction not in ENTRY_RULES or exit_name not in EXIT_KEYS:
        raise ValueError(f'Cambio no soportado: {change}')
    root = ET.fromstring(rules_xml)
    action = _entry_action(root, direction)
    params = action.findall(f"Param[@key='{EXIT_KEYS[exit_name]}']")
    if len(params) != 1:
        raise ValueError(f'La salida {exit_name} no existe exactamente una vez en la entrada {direction}')
    param = params[0]
    before = read_exit(rules_xml, direction, exit_name)
    if exit_name == 'exit_after_bars':
        if param.find('Formula') is not None or 'value' not in change:
            raise ValueError('exit_after_bars requiere un valor entero directo')
        value = int(change['value'])
        if value < 0:
            raise ValueError('exit_after_bars no admite valores negativos')
        param.text = str(value)
    else:
        formula = param.find('Formula')
        if formula is None:
            raise ValueError(f'La salida {exit_name} no usa fórmula; no se soporta')
        kind = formula.get('key')
        if kind not in FORMULA_VALUE_KEYS:
            raise ValueError(f'Fórmula no soportada para mutación: {kind}')
        applied = False
        for key, field in (('#Value#', 'value'), ('#AtrPeriod#', 'atr_period')):
            if field not in change:
                continue
            if key not in FORMULA_VALUE_KEYS[kind]:
                raise ValueError(f'{kind} no tiene {key}')
            targets = formula.findall(f"Param[@key='{key}']")
            if len(targets) != 1:
                raise ValueError(f'{key} no aparece exactamente una vez en {kind}')
            new = Decimal(str(change[field]))
            if not new.is_finite() or new <= 0:
                raise ValueError('Los valores de salida deben ser positivos y finitos')
            if key == '#AtrPeriod#' and new != new.to_integral_value():
                raise ValueError('El periodo ATR debe ser entero')
            targets[0].text = str(int(new)) if key == '#AtrPeriod#' else str(new.normalize()) if new != new.to_integral_value() else str(int(new)) + '.0'
            applied = True
        if not applied:
            raise ValueError('El cambio no especifica value ni atr_period')
    after_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    record = {**change, 'before': before, 'after': read_exit(after_xml, direction, exit_name)}
    if record['before'] == record['after']:
        raise ValueError(f'El cambio no altera nada: {change}')
    return after_xml, record


def build_variant(rules_xml: bytes, changes: list[dict]) -> dict:
    """Aplica varios cambios coherentes y verifica que no hay efectos colaterales."""
    if not 1 <= len(changes) <= 6:
        raise ValueError('Una variante admite entre uno y seis cambios explícitos')
    seen = set()
    current, records = rules_xml, []
    for change in changes:
        key = (change['direction'], change['exit'])
        if key in seen:
            raise ValueError(f'Cambio duplicado sobre {key}')
        seen.add(key)
        current, record = apply_change(current, change)
        records.append(record)
    comparison = compare_rules(rules_xml, current)
    if comparison['classification'] != 'RULES_CHANGED':
        raise ValueError('La variante no cambia el comportamiento: ' + comparison['classification'])
    touched = [c for c in comparison['changed_params'] if c.get('param') != 'structure']
    expected = sum(len([k for k in ('value', 'atr_period') if k in c]) for c in changes)
    if len(touched) != expected:
        raise ValueError(f'Cambios detectados ({len(touched)}) distintos de los previstos ({expected}): {touched}')
    return {'rules': current, 'changes': records, 'comparison': comparison,
            'semantic_rules_sha256': semantic_rules_sha256(current)}


def scaled(value, factor, decimals=1):
    """Valor escalado con redondeo explícito; útil para hipótesis relativas."""
    result = (Decimal(str(value)) * Decimal(str(factor))).quantize(Decimal(1).scaleb(-decimals))
    if result <= 0:
        raise ValueError('El escalado produce un valor no positivo')
    return str(result)


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    import zipfile
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--changes', required=True, help='JSON con la lista de cambios')
    args = parser.parse_args()
    with zipfile.ZipFile(args.source) as archive:
        rules = archive.read('strategy_Portfolio.xml')
    result = build_variant(rules, json.loads(args.changes))
    print(json.dumps({k: v for k, v in result.items() if k != 'rules'}, indent=2, ensure_ascii=False))
