"""Mutaciones verificadas sobre las reglas de una estrategia SQX.

Cada variante es una lista de cambios explícitos: salidas por dirección,
parámetros numéricos por ruta del catálogo, o filtros de entrada (ventana de
horas, exclusión de días de la semana, desactivar una dirección) que se añaden
como bloques de condición nativos de SQX (`SQ.Blocks.BarAndTime`) a la regla de
entrada. Tras aplicar los cambios se comprueba que las reglas resultantes
difieren del original exactamente en lo previsto y en nada más (los filtros solo
pueden tocar el bloque `If` de su regla), y que el cambio no es solo de
metadatos. No ejecuta backtests.

Los filtros se expresan en el XML de la estrategia y no en las opciones de
trading de `lastSettings.xml`, porque el proyecto de recálculo aplica las mismas
opciones a control y variantes: solo lo que está en las reglas varía por variante.

Solo biblioteca estándar.
"""
from __future__ import annotations

import copy
import json
import xml.etree.ElementTree as ET
from decimal import Decimal

from sqx_strategy_contract import canonical, compare_rules, semantic_rules_sha256

ENTRY_RULES = {'long': 'Long entry', 'short': 'Short entry'}
EXIT_KEYS = {
    'profit_target': '#ProfitTarget.ProfitTarget#',
    'stop_loss': '#StopLoss.StopLoss#',
    'trailing_stop': '#TrailingStop.TrailingStop#',
    'trailing_activation': '#TrailingStop.TrailingActivation#',
    'move_sl_to_be': '#MoveSL2BE.MoveSL2BE#',
    'exit_after_bars': '#ExitAfterBars.ExitAfterBars#',
}
FILTER_KINDS = ('hour_range', 'exclude_weekdays', 'disable_direction')
WEEKDAY_NAMES = ('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
WEEKDAY_ALIASES = {
    'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4, 'friday': 5, 'saturday': 6,
    'sun': 0, 'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6,
    'domingo': 0, 'lunes': 1, 'martes': 2, 'miercoles': 3, 'miércoles': 3, 'jueves': 4, 'viernes': 5, 'sabado': 6, 'sábado': 6,
}
# Bloques nativos de SQX (internal/extend/Snippets/SQ/Blocks/BarAndTime y Other) usados por los filtros.
FILTER_BLOCK_KEYS = ('BarHourIsBigger', 'BarHourIsSmaller', 'BarDayOfWeekIsNot', 'Boolean')
# Desfase de barra del filtro. Comprobado con recálculo real en la VPS (2026-09-06,
# UR_IMPROVE_MECANISMO_FILTROS_02): con Shift 0 el bloque lee la barra que acaba de cerrar y
# genera la señal (hora de apertura H); la orden stop queda activa desde la barra siguiente, así
# que en H1 el primer relleno cae en la hora H+1 (filtro "hora = 10" → rellenos a las 11).
FILTER_SHIFT = 0
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
                      '#Level#', '#Value#', '#AtrPeriod#', '#ExitAfterBars.ExitAfterBars#', '#Hour#')


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
    is_int = node.get('type') == 'int' or node.get('key') in ('#Period#', '#Shift#', '#BarsValid#', '#AtrPeriod#', '#ExitAfterBars.ExitAfterBars#', '#Hour#')
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


# ------------------------------------------------------------------ filtros

def _entry_rule(root: ET.Element, direction: str) -> ET.Element:
    rule_name = ENTRY_RULES[direction]
    rules = root.findall(f"Strategy/Rules/Events/Event[@key='OnBarUpdate']/Rule[@name='{rule_name}']")
    if len(rules) != 1:
        raise ValueError(f'Se esperaba exactamente una regla "{rule_name}"; hay {len(rules)}')
    return rules[0]


def _rule_scope(root: ET.Element, rule: ET.Element) -> str:
    """Prefijo de ruta semántica del bloque If de la regla (como lo etiqueta compare_rules)."""
    siblings = root.findall("Strategy/Rules/Events/Event[@key='OnBarUpdate']/Rule")
    index = siblings.index(rule)
    return 'Strategy/Rules/Events/Event[OnBarUpdate]/Rule' + (f'#{index}' if index else '') + '/If'


def _param(key: str, name: str, type_: str, control: str, value, **extra) -> ET.Element:
    node = ET.Element('Param', {'key': key, 'name': name, 'type': type_, 'controlType': control, **extra})
    node.text = str(value)
    return node


def _condition_item(key: str, name: str, display: str, params: list, main: str = 'BarAndTime',
                    category: str = 'simpleRules', **extra) -> ET.Element:
    # Forma tomada de una plantilla nativa de SQX (user/settings/StrategyTemplates/highest_breakout_template_daily_filter.sqx).
    item = ET.Element('Item', {'customSnippet': 'false', 'key': key, 'name': name, 'display': display, 'returnType': 'boolean',
                               'mI': main, 'categoryType': category, 'openingBrackets': '0', 'closingBrackets': '0', **extra})
    for node in params:
        item.append(node)
    return item


def _bar_and_time_item(key: str, name: str, display: str, value_param: ET.Element) -> ET.Element:
    return _condition_item(key, name, display, [
        _param('#Chart#', 'Chart', 'data', 'dataVar', 0, defaultValue='0'),
        value_param,
        _param('#Shift#', 'Shift', 'int', 'jspinnerVar', FILTER_SHIFT, defaultValue='1', minValue='0', maxValue='1000',
               paramType='shift', step='1', builderStep='1'),
    ])


def hour_bigger_item(hour: int) -> ET.Element:
    return _bar_and_time_item('BarHourIsBigger', 'Bar Hour Is Bigger', 'Bar[#Shift#] hour > #Hour#',
                              _param('#Hour#', 'Hour', 'int', 'jspinnerVar', hour, defaultValue='0', minValue='0', maxValue='23',
                                     step='1', builderStep='1'))


def hour_smaller_item(hour: int) -> ET.Element:
    return _bar_and_time_item('BarHourIsSmaller', 'Bar Hour Is Smaller', 'Bar[#Shift#] hour < #Hour#',
                              _param('#Hour#', 'Hour', 'int', 'jspinnerVar', hour, defaultValue='0', minValue='0', maxValue='23',
                                     step='1', builderStep='1'))


def weekday_not_item(day: int) -> ET.Element:
    values = ','.join(f'{name}={index}' for index, name in enumerate(WEEKDAY_NAMES))
    return _bar_and_time_item('BarDayOfWeekIsNot', 'Bar Day Of Week Is Not', 'Bar[#Shift#] day of week != #Day#',
                              _param('#Day#', 'Day', 'int', 'combo', day, defaultValue='0', values=values, builderStep='1'))


def boolean_false_item() -> ET.Element:
    return _condition_item('Boolean', '(BOOL) Boolean', '#Value#',
                           [_param('#Value#', 'Value', 'boolean', 'checkbox', 'false', defaultValue='false')],
                           main='Other', category='other', notFirstValue='true', ignoreInBuilder='true')


def _plain_block(node: ET.Element) -> bool:
    # Etiqueta "Block" sin índice de clave en param_paths (los atributos name se eliminan en la copia semántica).
    return node.tag == 'Block' and not node.get('key') and not node.get('variable')


def _append_condition(rule: ET.Element, item: ET.Element) -> tuple[str, bool]:
    """Añade `item` como condición AND al If de la regla y devuelve (sufijo de ruta semántica del
    bloque nuevo, envuelto). Si el If no era un AND raíz, se envuelve la condición existente en un
    AND nuevo sin alterarla (se comprueba por forma canónica) y se declara `envuelto`."""
    if_node = rule.find('If')
    if if_node is None:
        raise ValueError(f'La regla "{rule.get("name")}" no tiene bloque If')
    children = list(if_node)
    block = ET.Element('Block')
    block.append(item)
    wrapped = False
    if len(children) == 1 and children[0].get('key') == 'AND':
        root_and = children[0]
    else:
        before = [canonical(child) for child in children]
        root_and = ET.Element('Item', {'key': 'AND'})
        for child in children:
            if_node.remove(child)
            inner = ET.Element('Block')
            inner.append(child)
            root_and.append(inner)
        if_node.append(root_and)
        after = [canonical(inner[0]) for inner in root_and]
        if before != after:
            raise ValueError('Al envolver la condición existente en un AND cambió su forma; se aborta el filtro')
        wrapped = True
    index = sum(1 for c in root_and if _plain_block(c))
    root_and.append(block)
    return 'Item[AND]/Block' + (f'#{index}' if index else ''), wrapped


def conjunction_items(if_node: ET.Element):
    """Condiciones que forman la conjunción del If: AND raíz y AND anidados. No entra en Not, OR ni comparaciones."""
    def walk(item):
        if item.get('key') == 'AND':
            for block in item.findall('Block'):
                for child in block.findall('Item'):
                    yield from walk(child)
        else:
            yield item
    if if_node is not None:
        for child in if_node.findall('Item'):
            yield from walk(child)


def entry_filters(rule: ET.Element) -> list[dict]:
    """Filtros de entrada activos en la conjunción del If de una regla (bloques de hora, día y Boolean false)."""
    found = []
    for item in conjunction_items(rule.find('If')):
        key = item.get('key')
        if key not in FILTER_BLOCK_KEYS:
            continue
        params = {p.get('key').strip('#'): (p.text or '').strip() for p in item.findall('Param') if p.get('key') != '#Chart#'}
        if key == 'Boolean' and params.get('Value') != 'false':
            continue  # un Boolean true en la conjunción no filtra nada
        entry = {'block': key, **params}
        if key == 'BarDayOfWeekIsNot' and params.get('Day', '').isdigit():
            entry['day_name'] = WEEKDAY_NAMES[int(params['Day'])]
        found.append(entry)
    return found


def disabled_directions(rules_xml: bytes) -> set:
    root = ET.fromstring(rules_xml)
    out = set()
    for direction in ENTRY_RULES:
        try:
            rule = _entry_rule(root, direction)
        except ValueError:
            continue
        if any(f['block'] == 'Boolean' for f in entry_filters(rule)):
            out.add(direction)
    return out


def normalize_weekday(value) -> int:
    if isinstance(value, bool):
        raise ValueError(f'Día de la semana no válido: {value!r}')
    if isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit()):
        day = int(value)
    else:
        day = WEEKDAY_ALIASES.get(str(value).strip().lower())
        if day is None:
            raise ValueError(f'Día de la semana no reconocido: {value!r}')
    if not 0 <= day <= 6:
        raise ValueError(f'Día de la semana fuera de 0-6: {value!r}')
    return day


def _int_hour(value, field: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError(f'{field} debe ser un entero de 0 a 24')
    try:
        hour = int(str(value).strip())
    except ValueError:
        raise ValueError(f'{field} debe ser un entero de 0 a 24, no {value!r}')
    if not 0 <= hour <= 24:
        raise ValueError(f'{field} fuera de 0-24: {hour}')
    return hour


def apply_filter(rules_xml: bytes, change: dict) -> tuple[bytes, dict]:
    """Aplica un filtro de entrada {filter, direction, from/to | days} y devuelve (xml, registro).

    hour_range: la señal solo se toma si la hora de la barra (zona horaria de los datos,
    desfase FILTER_SHIFT) cumple from <= hora < to. exclude_weekdays: la señal no se toma en
    esos días (0 = domingo … 6 = sábado). disable_direction: la regla de entrada nunca se
    cumple (equivale a operar solo la otra dirección).
    """
    kind = change.get('filter')
    if kind not in FILTER_KINDS:
        raise ValueError(f'Filtro no soportado: {kind!r} (admitidos: {", ".join(FILTER_KINDS)})')
    direction = change.get('direction', 'both')
    if direction not in ('long', 'short', 'both'):
        raise ValueError(f'Dirección no válida para un filtro: {direction!r}')
    directions = ('long', 'short') if direction == 'both' else (direction,)
    root = ET.fromstring(rules_xml)
    record = {'filter': kind, 'direction': direction, 'before': None, 'effective_fields': 0, 'blocks_added': [],
              'scope_prefixes': [], 'added_paths': [], 'wrapped_prefixes': []}
    if kind == 'hour_range':
        start, end = _int_hour(change.get('from'), 'from'), _int_hour(change.get('to'), 'to')
        if start >= end:
            raise ValueError(f'hour_range exige from < to (recibido {start}-{end})')
        if start == 0 and end == 24:
            raise ValueError('hour_range 0-24 no filtra nada')
        record.update({'from': start, 'to': end})
        items = ([hour_bigger_item(start - 1)] if start > 0 else []) + ([hour_smaller_item(end)] if end < 24 else [])
    elif kind == 'exclude_weekdays':
        raw = change.get('days')
        if not isinstance(raw, (list, tuple)) or not raw:
            raise ValueError('exclude_weekdays exige una lista days no vacía')
        days = sorted({normalize_weekday(d) for d in raw})
        if len(days) > 3:
            raise ValueError('exclude_weekdays admite como máximo tres días')
        if len([d for d in days if 1 <= d <= 5]) > 2:
            raise ValueError('exclude_weekdays admite como máximo dos días laborables (quedarían menos de tres sesiones por semana)')
        record['days'] = [WEEKDAY_NAMES[d] for d in days]
        items = [weekday_not_item(d) for d in days]
    else:
        if direction == 'both':
            raise ValueError('disable_direction exige direction long o short, no both')
        items = [boolean_false_item()]
    for target in directions:
        rule = _entry_rule(root, target)
        _entry_action(root, target)  # la regla debe seguir siendo una entrada única
        existing = entry_filters(rule)
        for item in items:
            key = item.get('key')
            new_params = {p.get('key').strip('#'): (p.text or '').strip() for p in item.findall('Param') if p.get('key') != '#Chart#'}
            if any(e['block'] == key and all(e.get(k) == v for k, v in new_params.items()) for e in existing):
                raise ValueError(f'La regla "{rule.get("name")}" ya contiene el filtro {key} {new_params}')
            if kind == 'hour_range' and any(e['block'] == key for e in existing):
                raise ValueError(f'La regla "{rule.get("name")}" ya tiene un filtro {key}: cámbialo por param_path (#Hour#) en vez de apilar otro')
            if kind == 'disable_direction' and any(e['block'] == 'Boolean' for e in existing):
                raise ValueError(f'La dirección {target} ya está desactivada')
            suffix, wrapped = _append_condition(rule, copy.deepcopy(item))
            scope = _rule_scope(root, rule)
            record['added_paths'].append(scope + '/' + suffix)
            if wrapped:
                record['wrapped_prefixes'].append(scope)
            record['blocks_added'].append({'direction': target, 'block': key, **new_params})
        record['scope_prefixes'].append(_rule_scope(root, rule))
    after_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    record['after'] = {target: entry_filters(_entry_rule(root, target)) for target in directions}
    return after_xml, record


def describe_filter(change: dict) -> str:
    kind = change.get('filter')
    direction = change.get('direction', 'both')
    if kind == 'hour_range':
        return f"{direction}: señal solo si {change.get('from')} <= hora de barra < {change.get('to')} (zona de los datos)"
    if kind == 'exclude_weekdays':
        return f"{direction}: sin señal los días {', '.join(map(str, change.get('days') or []))}"
    return f'{direction}: dirección desactivada'


CHANGE_GROUPS = {
    'filter': {'filter', 'direction', 'from', 'to', 'days'},
    'param_path': {'param_path', 'value'},
    'exit': {'direction', 'exit', 'value', 'atr_period'},
}


def change_group(change: dict) -> str:
    if not isinstance(change, dict):
        raise ValueError(f'Cambio no válido: {change!r}')
    group = 'filter' if 'filter' in change else 'param_path' if 'param_path' in change else 'exit'
    extra = set(change) - CHANGE_GROUPS[group]
    if extra:
        raise ValueError(f'Cambio con claves mezcladas {sorted(extra)}: un cambio es una salida, un param_path o un filtro, no varios a la vez')
    return group


def change_directions(change: dict) -> set:
    """Direcciones a las que apunta un cambio (para detectar cambios sobre direcciones desactivadas)."""
    group = change_group(change)
    if group == 'param_path':
        path = change['param_path']
        return {d for d, name in ENTRY_RULES.items() if f'Rule[{name}]' in path}
    direction = change.get('direction', 'both' if group == 'filter' else None)
    return {'long', 'short'} if direction == 'both' else {direction} if direction in ENTRY_RULES else set()


def apply_change(rules_xml: bytes, change: dict) -> tuple[bytes, dict]:
    """Aplica un cambio {direction, exit, value?, atr_period?}, {param_path, value} o {filter, ...} y devuelve (xml, registro)."""
    group = change_group(change)
    if group == 'filter':
        return apply_filter(rules_xml, change)
    if group == 'param_path':
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


def change_key(change: dict):
    if 'filter' in change:
        return ('filter', change['filter'], change.get('direction', 'both'))
    if 'param_path' in change:
        return change['param_path']
    return (change['direction'], change['exit'])


def build_variant(rules_xml: bytes, changes: list[dict]) -> dict:
    """Aplica varios cambios coherentes y verifica que no hay efectos colaterales.

    Cambios de salida y de parámetro: el número de parámetros que cambian fuera de
    cualquier filtro debe ser exactamente el previsto. Filtros: todo cambio dentro del
    If de su regla se les atribuye; cada filtro debe haber añadido condiciones en su
    regla sin alterar las existentes, y ningún cambio puede quedar sin atribuir.
    """
    if not 1 <= len(changes) <= 6:
        raise ValueError('Una variante admite entre uno y seis cambios explícitos')
    seen = set()
    for change in changes:
        key = change_key(change)
        if key in seen:
            raise ValueError(f'Cambio duplicado sobre {key}')
        seen.add(key)
    filter_directions = set()
    for change in changes:
        if 'filter' in change:
            for direction in (('long', 'short') if change.get('direction', 'both') == 'both' else (change.get('direction'),)):
                if (change['filter'], direction) in filter_directions:
                    raise ValueError(f'Filtro {change["filter"]} repetido para {direction}')
                filter_directions.add((change['filter'], direction))
    current, records = rules_xml, []
    for change in changes:
        current, record = apply_change(current, change)
        records.append(record)
    comparison = compare_rules(rules_xml, current)
    if comparison['classification'] != 'RULES_CHANGED':
        raise ValueError('La variante no cambia el comportamiento: ' + comparison['classification'])
    touched = [c for c in comparison['changed_params'] if c.get('param') != 'structure']
    added_paths = [p for r in records for p in r.get('added_paths', [])]
    wrapped = [p for r in records for p in r.get('wrapped_prefixes', [])]

    def attributed_to_filters(c):
        # Solo cuentan como filtro las adiciones bajo el bloque exacto que añadió, y, si hubo que envolver la
        # condición existente en un AND, el traslado de esa condición (retirada de su ruta antigua y alta en el
        # primer bloque del AND nuevo, con forma canónica comprobada al envolver).
        if c.get('change') == 'added' and any(c['param'].startswith(p + '/') for p in added_paths):
            return True
        for prefix in wrapped:
            if c.get('change') == 'removed' and c['param'].startswith(prefix + '/'):
                return True
            if c.get('change') == 'added' and c['param'].startswith(prefix + '/Item[AND]/Block/'):
                return True
        return False
    in_scope = [c for c in touched if attributed_to_filters(c)]
    free = [c for c in touched if not attributed_to_filters(c)]
    expected = sum(r.get('effective_fields', 1) for r in records if 'filter' not in r)
    if len(free) != expected:
        raise ValueError(f'Cambios detectados fuera de filtros ({len(free)}) distintos de los previstos ({expected}): {free}')
    for record in records:
        for path in record.get('added_paths', []):
            if not any(c['param'].startswith(path + '/') and c.get('change') == 'added' for c in in_scope):
                raise ValueError(f'El filtro {record["filter"]} no añadió ninguna condición en {path}')
    # Combinaciones sin sentido que gastarían un recálculo.
    disabled = disabled_directions(current)
    if disabled >= set(ENTRY_RULES):
        raise ValueError('La variante desactiva las dos direcciones: la estrategia no operaría nunca')
    for change in changes:
        if change.get('filter') == 'disable_direction':
            continue
        hit = change_directions(change) & disabled
        if hit:
            raise ValueError(f'El cambio {change} apunta a una dirección desactivada ({", ".join(sorted(hit))})')
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
