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


# Parámetros numéricos que un agente puede proponer cambiar por ruta estructural.
# Claves de SQX que expresan comportamiento (periodos, desviaciones, desfases,
# validez de la orden). Todo lo demás queda fuera del catálogo.
GENERIC_PARAM_KEYS = ('#Period#', '#Deviation#', '#Shift#', '#BarsValid#', '#Multiplier#',
                      '#Level#', '#Value#', '#AtrPeriod#', '#ExitAfterBars.ExitAfterBars#')


def _raw_paths(root: ET.Element) -> dict:
    """Ruta estructural → nodo, sobre el XML tal cual (sin quitar metadatos)."""
    result = {}

    def walk(node, path):
        counters = {}
        for child in node:
            label = child.tag
            for attr in ('key', 'name', 'variable'):
                if child.get(attr):
                    label += f"[{child.get(attr)}]"
                    break
            index = counters.get(label, 0)
            counters[label] = index + 1
            child_path = f"{path}/{label}" + (f"#{index}" if index else '')
            result[child_path] = child
            walk(child, child_path)
    walk(root, 'StrategyFile')
    return result


def _is_number(text: str) -> bool:
    try:
        Decimal(text)
        return True
    except Exception:
        return False


def mutable_parameters(rules_xml: bytes) -> list[dict]:
    """Catálogo de parámetros numéricos con contexto legible, para que los agentes
    propongan cambios concretos sin conocer el XML de SQX."""
    root = ET.fromstring(rules_xml)
    catalogue = []
    for path, node in _raw_paths(root).items():
        if node.tag != 'Param' or node.get('key') not in GENERIC_PARAM_KEYS:
            continue
        if len(node) or not _is_number((node.text or '').strip()):
            continue
        context = []
        parent_path = path
        for segment in path.split('/')[1:-1]:
            if segment.startswith(('Rule[', 'Item[', 'Formula[')):
                context.append(segment.split('[', 1)[1].rstrip('#0123456789').rstrip(']'))
        catalogue.append({'path': path, 'key': node.get('key').strip('#'), 'current': (node.text or '').strip(),
                          'type': node.get('type') or ('int' if node.get('key') in ('#Period#', '#Shift#', '#BarsValid#', '#AtrPeriod#') else 'double'),
                          'context': ' > '.join(context[-4:]), 'min': node.get('minValue'), 'max': node.get('maxValue')})
    return catalogue


def apply_path_change(rules_xml: bytes, path: str, value) -> tuple[bytes, dict]:
    """Cambia un parámetro numérico identificado por su ruta del catálogo."""
    root = ET.fromstring(rules_xml)
    node = _raw_paths(root).get(path)
    if node is None or node.tag != 'Param' or node.get('key') not in GENERIC_PARAM_KEYS or len(node):
        raise ValueError(f'Ruta no mutable: {path}')
    before = (node.text or '').strip()
    new = Decimal(str(value))
    if not new.is_finite():
        raise ValueError('Valor no finito')
    is_int = node.get('type') == 'int' or node.get('key') in ('#Period#', '#Shift#', '#BarsValid#', '#AtrPeriod#', '#ExitAfterBars.ExitAfterBars#')
    if is_int and new != new.to_integral_value():
        raise ValueError(f'{path} exige un entero')
    if new < 0 or (is_int and new == 0 and node.get('key') in ('#Period#', '#AtrPeriod#')):
        raise ValueError(f'{path}: valor fuera de rango')
    for bound, op in (('minValue', lambda a, b: a < b), ('maxValue', lambda a, b: a > b)):
        limit = node.get(bound)
        if limit and _is_number(limit) and op(new, Decimal(limit)):
            raise ValueError(f'{path}: {value} fuera del límite {bound}={limit} declarado por SQX')
    node.text = str(int(new)) if is_int else str(new.normalize()) if new != new.to_integral_value() else str(int(new)) + '.0'
    after_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    if before == (node.text or '').strip() or Decimal(before) == new:
        raise ValueError(f'El cambio no altera nada: {path}={value}')
    return after_xml, {'param_path': path, 'value': str(value), 'before': before, 'after': node.text, 'effective_fields': 1}


def apply_change(rules_xml: bytes, change: dict) -> tuple[bytes, dict]:
    """Aplica un cambio {direction, exit, value?, atr_period?} o {param_path, value} y devuelve (xml, registro)."""
    if 'param_path' in change:
        return apply_path_change(rules_xml, change['param_path'], change['value'])
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
            # Repetir el valor vigente (p. ej. el periodo ATR que no cambia) no es un cambio:
            # se ignora y solo cuentan los campos que realmente varían.
            if Decimal((targets[0].text or '0').strip() or '0') == new:
                continue
            targets[0].text = str(int(new)) if key == '#AtrPeriod#' else str(new.normalize()) if new != new.to_integral_value() else str(int(new)) + '.0'
            applied = True
        if not applied:
            raise ValueError(f'El cambio no altera nada: {change}')
    after_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    record = {**change, 'before': before, 'after': read_exit(after_xml, direction, exit_name)}
    if record['before'] == record['after']:
        raise ValueError(f'El cambio no altera nada: {change}')
    record['effective_fields'] = sum(1 for k in ('formula', 'Value', 'AtrPeriod', 'value') if (record['before'] or {}).get(k) != (record['after'] or {}).get(k))
    return after_xml, record


def build_variant(rules_xml: bytes, changes: list[dict]) -> dict:
    """Aplica varios cambios coherentes y verifica que no hay efectos colaterales."""
    if not 1 <= len(changes) <= 6:
        raise ValueError('Una variante admite entre uno y seis cambios explícitos')
    seen = set()
    current, records = rules_xml, []
    for change in changes:
        key = change['param_path'] if 'param_path' in change else (change['direction'], change['exit'])
        if key in seen:
            raise ValueError(f'Cambio duplicado sobre {key}')
        seen.add(key)
        current, record = apply_change(current, change)
        records.append(record)
    comparison = compare_rules(rules_xml, current)
    if comparison['classification'] != 'RULES_CHANGED':
        raise ValueError('La variante no cambia el comportamiento: ' + comparison['classification'])
    touched = [c for c in comparison['changed_params'] if c.get('param') != 'structure']
    expected = sum(r.get('effective_fields', 1) for r in records)
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
