"""Contrato de entrada del motor de mejora: qué debe declarar una estrategia SQX.

Un nombre y unas estadísticas no bastan. Este módulo extrae de un archivo .sqx
todo lo necesario para reproducir la estrategia (instrumento, temporalidad,
datos, periodo, entradas, salidas, tamaño, costes, configuración y procedencia)
y señala lo que falta. No ejecuta nada ni certifica rentabilidad.

Solo biblioteca estándar: debe funcionar en la VPS con /usr/bin/python3.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 'ultrarentable.strategy_contract.v1'

# Hechos de procedencia conocidos en este despliegue (auditoría 2026-09-06):
# estos alias se importaron desde históricos CFD; renombrar un símbolo no lo
# convierte en el futuro real. No es una afirmación global sobre esos futuros.
KNOWN_PROXY_ALIASES = {
    'MNQ': 'USATECHIDXUSD', 'MYM': 'USA30IDXUSD', 'MES': 'USA500IDXUSD',
    'MGC': 'XAUUSD', 'MCL': 'LIGHTCMDUSD',
}

# Tabla de referencia de contratos (especificaciones públicas del CME); el valor
# del punto se contrasta con las órdenes nativas cuando existen. Fuente: fichas
# de producto del CME Group; fecha de consulta 2026-09-06.
CME_REFERENCE = {
    '@EW': {'exchange': 'CME', 'description': 'E-mini S&P MidCap 400 (EMD)',
            'point_value': 100.0, 'tick_size': 0.1, 'timezone': 'America/Chicago'},
    '@ES': {'exchange': 'CME', 'description': 'E-mini S&P 500', 'point_value': 50.0,
            'tick_size': 0.25, 'timezone': 'America/Chicago'},
    'MES': {'exchange': 'CME', 'description': 'Micro E-mini S&P 500', 'point_value': 5.0,
            'tick_size': 0.25, 'timezone': 'America/Chicago'},
    'MNQ': {'exchange': 'CME', 'description': 'Micro E-mini Nasdaq-100', 'point_value': 2.0,
            'tick_size': 0.25, 'timezone': 'America/Chicago'},
    'MYM': {'exchange': 'CBOT', 'description': 'Micro E-mini Dow', 'point_value': 0.5,
            'tick_size': 1.0, 'timezone': 'America/Chicago'},
    '@E6': {'exchange': 'CME', 'description': 'Euro FX', 'point_value': 125000.0,
            'tick_size': 0.00005, 'timezone': 'America/Chicago'},
}

EXIT_PARAM_KEYS = (
    '#ExitAfterBars.ExitAfterBars#', '#MoveSL2BE.MoveSL2BE#', '#MoveSL2BE.SL2BEAddPips#',
    '#ProfitTarget.ProfitTarget#', '#StopLoss.StopLoss#', '#TrailingStop.TrailingStop#',
    '#TrailingStop.TrailingActivation#',
)

# Atributos que SQX reescribe sin cambiar el comportamiento (editor/generador).
METADATA_ATTRIBUTES = (
    'generated', 'randomId', 'gid', 'randomValue', 'name', 'help', 'display',
    'builderMinValue', 'builderMaxValue', 'builderStep', 'recommendedMinValue',
    'recommendedMaxValue', 'ruleIndex', 'retries', 'ownRandomKey', 'customSnippet',
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(node: ET.Element) -> str:
    return ET.canonicalize(ET.tostring(node, encoding='unicode'), strip_text=True)


def read_archive(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('Archivo SQX dañado')
        return {name: archive.read(name) for name in archive.namelist()}


def semantic_strategy(rules_xml: bytes) -> ET.Element:
    """Copia del nodo Strategy sin metadatos de editor ni representaciones vacías.

    Dos archivos con la misma copia semántica describen las mismas reglas. Un
    atributo desconocido se conserva (fallo conservador: se considera cambio).
    """
    root = ET.fromstring(rules_xml)
    strategy = copy.deepcopy(root.find('Strategy'))
    if strategy is None:
        raise ValueError('El archivo no contiene un nodo Strategy')
    for attr in ('engine', 'name'):
        strategy.attrib.pop(attr, None)
    if strategy.get('negateRules') == 'false':
        strategy.attrib.pop('negateRules')
    for tag in ('Note', 'Description'):
        for node in strategy.findall(tag):
            strategy.remove(node)
    for node in strategy.iter():
        for key in METADATA_ATTRIBUTES:
            node.attrib.pop(key, None)
        if node.get('identification') == '':
            node.attrib.pop('identification')
    # <signal/> vacío y <signal><Item Boolean>false</Item></signal> son la misma
    # señal ausente; <Then/> y <Else/> vacíos no aportan reglas.
    for rule in strategy.iter('Rule'):
        for tag in ('Then', 'Else'):
            for child in rule.findall(tag):
                if not len(child) and not (child.text or '').strip():
                    rule.remove(child)
    for signal in strategy.iter('signal'):
        for child in list(signal):
            if child.tag == 'Item' and child.get('key') == 'Boolean' and len(child) == 1:
                value = child[0]
                if value.get('key') == '#Value#' and (value.text or '').strip() == 'false':
                    signal.remove(child)
    # El texto de #Identification# es una etiqueta de orden que SQX renombra al
    # exportar; conserva la distinción entre acciones, no el nombre concreto.
    names = {}
    for param in strategy.iter('Param'):
        if param.get('key') == '#Identification#':
            label = (param.text or '').strip()
            param.text = names.setdefault(label, f'ID#{len(names) + 1}')
    return strategy


def param_paths(strategy: ET.Element) -> dict:
    """Ruta estructural → forma canónica de cada Param (evita colisiones de claves)."""
    result = {}

    def walk(node, path):
        counters = {}
        for child in node:
            label = child.tag
            for attr in ('name', 'key', 'variable'):
                if child.get(attr):
                    label += f"[{child.get(attr)}]"
                    break
            index = counters.get(label, 0)
            counters[label] = index + 1
            child_path = f"{path}/{label}" + (f"#{index}" if index else '')
            if child.tag == 'Param':
                result[child_path] = child
            walk(child, child_path)
    walk(strategy, 'Strategy')
    return result


def semantic_rules_sha256(rules_xml: bytes) -> str:
    return sha(canonical(semantic_strategy(rules_xml)).encode('utf-8'))


def _formula(param: ET.Element) -> dict:
    formula = param.find('Formula')
    if formula is None:
        return {'kind': 'value', 'value': (param.text or '').strip()}
    values = {p.get('key').strip('#'): (p.text or '').strip() for p in formula.findall('Param')}
    return {'kind': formula.get('key'), **values}


# Bloques de condición que el motor de mejora añade como filtros de entrada (ver sqx_variant_mutations).
FILTER_BLOCK_KEYS = ('BarHourIsBigger', 'BarHourIsSmaller', 'BarDayOfWeekIsNot', 'Boolean')
WEEKDAY_NAMES = ('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')


def entry_filters(rule: ET.Element) -> list:
    """Filtros de hora/día/dirección presentes en el If de una regla de entrada (legibles para el dosier)."""
    found = []
    if_node = rule.find('If')
    for item in ([] if if_node is None else if_node.iter('Item')):
        key = item.get('key')
        if key not in FILTER_BLOCK_KEYS:
            continue
        params = {p.get('key').strip('#'): (p.text or '').strip() for p in item.findall('Param') if p.get('key') != '#Chart#'}
        entry = {'block': key, **params}
        if key == 'BarHourIsBigger':
            entry['meaning'] = f"hora de barra > {params.get('Hour')}"
        elif key == 'BarHourIsSmaller':
            entry['meaning'] = f"hora de barra < {params.get('Hour')}"
        elif key == 'BarDayOfWeekIsNot' and params.get('Day', '').isdigit():
            entry['meaning'] = f"no opera el {WEEKDAY_NAMES[int(params['Day'])]}"
        elif key == 'Boolean' and params.get('Value') == 'false':
            entry['meaning'] = 'dirección desactivada'
        found.append(entry)
    return found


def describe_rules(rules_xml: bytes) -> dict:
    root = ET.fromstring(rules_xml)
    strategy = root.find('Strategy')
    rules = strategy.findall("Rules/Events/Event[@key='OnBarUpdate']/Rule")
    summary = {'signals': [], 'entries': [], 'exit_rules': [], 'rule_names': [r.get('name') for r in rules]}

    def describe_item(item):
        params = {p.get('key').strip('#'): (p.text or '').strip()
                  for p in item.findall('Param') if p.get('key') != '#Chart#'}
        children = [describe_item(c) for c in item.findall('Item')] + \
                   [describe_item(i) for b in item.findall('Block') for i in b.findall('Item')]
        node = {'key': item.get('key')}
        if params:
            node['params'] = params
        if children:
            node['children'] = children
        return node

    for rule in rules:
        if rule.get('type') == 'Signal':
            for index, signal in enumerate(rule.findall('signals/signal')):
                items = [describe_item(i) for i in signal.findall('Item')]
                summary['signals'].append({'slot': index, 'variable': signal.get('variable'),
                                           'items': items, 'empty': not items})
        elif rule.get('type') == 'IfThen':
            action = rule.find('Then/Item')
            if action is None:
                continue
            key = action.get('key') or ''
            if key.startswith('Enter'):
                params = {p.get('key'): p for p in action.findall('Param')}
                direction = (params.get('#Direction#').text or '').strip() if '#Direction#' in params else ''
                exits = {}
                for exit_key in EXIT_PARAM_KEYS:
                    param = params.get(exit_key)
                    if param is not None:
                        exits[exit_key.strip('#')] = {'gid': param.get('gid'), **_formula(param)}
                summary['entries'].append({
                    'rule': rule.get('name'), 'action': key,
                    'direction': 'long' if direction == '1' else 'short' if direction == '-1' else direction,
                    'price': _formula(params['#Price#']) if '#Price#' in params else None,
                    'bars_valid': (params['#BarsValid#'].text or '').strip() if '#BarsValid#' in params else None,
                    'size': _formula(params['#Size#']) if '#Size#' in params else None,
                    'exits': exits,
                    'entry_filters': entry_filters(rule),
                })
            elif key in ('ClosePosition', 'CloseOrder', 'ExitPosition'):
                summary['exit_rules'].append({'rule': rule.get('name'), 'action': key})
    return summary


def _text(node, path, default=None):
    found = node.find(path) if node is not None else None
    return (found.text or '').strip() if found is not None and found.text else default


def _epoch_ms(value):
    try:
        return datetime.fromtimestamp(int(value) / 1000, timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        return None


def extract_contract(path: Path, origin: dict | None = None) -> dict:
    """Ficha reproducible de una estrategia SQX y lista de carencias esenciales."""
    path = Path(path)
    archive = read_archive(path)
    payload = path.read_bytes()
    missing, warnings = [], []
    for required in ('settings.xml', 'lastSettings.xml', 'strategy_Portfolio.xml'):
        if required not in archive:
            missing.append(f'archive:{required}')
    if missing:
        return {'schema': SCHEMA, 'state': 'CONTRACT_INCOMPLETE', 'archive_sha256': sha(payload),
                'essentials_missing': missing}
    settings = ET.fromstring(archive['settings.xml'])
    last = ET.fromstring(archive['lastSettings.xml'])
    rules_xml = archive['strategy_Portfolio.xml']
    rules_root = ET.fromstring(rules_xml)

    setup = last.find('Data/Setups/Setup')
    chart = setup.find('Chart') if setup is not None else None
    symbol = chart.get('symbol') if chart is not None else None
    timeframe = chart.get('timeframe') if chart is not None else None
    resource = last.find(f"Resources/Symbols/Symbol[@name='{symbol}']") if symbol else None
    reference = CME_REFERENCE.get(symbol or '')
    tz = resource.get('timezone') if resource is not None else None
    resolved_tz = tz
    if tz == 'Exchange':
        resolved_tz = reference['timezone'] if reference else None
        if resolved_tz is None:
            warnings.append('Zona horaria "Exchange" sin tabla de referencia para el instrumento')

    commission = setup.find("Commissions/Method[@use='true']") if setup is not None else None
    swap = setup.find('Swap') if setup is not None else None
    mm = last.find("RiskMoneyManagement/MoneyManagement/Method[@use='true']")
    options = {p.get('key'): (p.text or '').strip()
               for p in last.findall('Options/BuildTradingOptions/Params/Param')}

    contract = {
        'schema': SCHEMA,
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'identity': {
            'name': settings.get('ResultName'),
            'archive_sha256': sha(payload), 'archive_bytes': len(payload),
            'rules_sha256': sha(rules_xml), 'semantic_rules_sha256': semantic_rules_sha256(rules_xml),
            'sqx_file_version': rules_root.get('Version'), 'sqx_app_version': rules_root.get('AppVersion'),
            'strategy_engine': rules_root.find('Strategy').get('engine'),
            'setup_engine': setup.get('engine') if setup is not None else None,
        },
        'market': {
            'symbol': symbol, 'timeframe': timeframe,
            'instrument_name': resource.get('uSymbolName') if resource is not None else None,
            'data_source_id': resource.get('source') if resource is not None else None,
            'bar_type': resource.get('barType') if resource is not None else None,
            'declared_timezone': tz, 'resolved_timezone': resolved_tz,
            'data_precision': resource.get('precision') if resource is not None else None,
            'resource_date_from': _epoch_ms(resource.get('dateFrom')) if resource is not None else None,
            'resource_date_to': _epoch_ms(resource.get('dateTo')) if resource is not None else None,
            'reference_contract': reference,
            'known_proxy_alias': KNOWN_PROXY_ALIASES.get(symbol or ''),
        },
        'period': {
            'date_from': setup.get('dateFrom') if setup is not None else None,
            'date_to': setup.get('dateTo') if setup is not None else None,
            'oos_ranges': [{'from': r.get('dateFrom'), 'to': r.get('dateTo')}
                           for r in last.findall('Data/OutOfSample/Range')],
            'test_precision': setup.get('testPrecision') if setup is not None else None,
            'session': setup.get('session') if setup is not None else None,
        },
        'costs': {
            'commission_method': commission.get('type') if commission is not None else None,
            'commission_params': {p.get('key'): (p.text or '').strip()
                                  for p in commission.findall('Params/Param')} if commission is not None else {},
            'slippage': setup.get('slippage') if setup is not None else None,
            'spread': chart.get('spread') if chart is not None else None,
            'swap_used': swap.get('use') if swap is not None else None,
        },
        'sizing': {
            'method': mm.get('type') if mm is not None else None,
            'params': {p.get('key'): (p.text or '').strip() for p in mm.findall('Params/Param')} if mm is not None else {},
            'initial_capital': _text(last, 'RiskMoneyManagement/MoneyManagement/InitialCapital'),
            'risk_management_max_drawdown': (last.find('RiskMoneyManagement/RiskManagement').get('maxDrawdown')
                                             if last.find('RiskMoneyManagement/RiskManagement') is not None else None),
        },
        'options': {k: options.get(k) for k in (
            'ExitAtEndOfDay', 'EODExitTime', 'ExitOnFriday', 'FridayExitTime', 'DontTradeOnWeekends',
            'LimitTimeRange', 'SignalTimeRangeFrom', 'SignalTimeRangeTo', 'ExitAtEndOfRange',
            'UseInitialSLPT', 'Session', 'MarketOpenSession')},
        'rules': describe_rules(rules_xml),
        'provenance': {
            'archive_path': str(path), 'origin': origin or {},
            'inherited_results_present': any(n.endswith('orders.bin') for n in archive),
            'inherited_results_policy': 'Los resultados heredados del archivo sirven para diagnosticar; la referencia comparable es siempre un recálculo fresco.',
            'data_provenance_state': ('KNOWN_CFD_PROXY_UNDER_FUTURES_ALIAS' if symbol in KNOWN_PROXY_ALIASES
                                      else 'DECLARED_NOT_INDEPENDENTLY_VERIFIED'),
        },
    }
    # Carencias esenciales para reproducir la estrategia.
    checks = [
        ('market.symbol', symbol), ('market.timeframe', timeframe),
        ('period.date_from', contract['period']['date_from']), ('period.date_to', contract['period']['date_to']),
        ('costs.commission', contract['costs']['commission_method']),
        ('costs.slippage', contract['costs']['slippage']),
        ('sizing.method', contract['sizing']['method']),
        ('sizing.initial_capital', contract['sizing']['initial_capital']),
        ('market.timezone', resolved_tz),
    ]
    missing.extend(name for name, value in checks if value in (None, ''))
    if not contract['rules']['entries']:
        missing.append('rules.entries')
    if not any(e['exits'] for e in contract['rules']['entries']):
        missing.append('rules.exits')
    if not contract['period']['oos_ranges']:
        warnings.append('Sin partición fuera de muestra declarada: no hay datos de desarrollo separados')
    contract['essentials_missing'] = missing
    contract['warnings'] = warnings
    contract['state'] = 'CONTRACT_COMPLETE' if not missing else 'CONTRACT_INCOMPLETE'
    contract['destination_hints'] = destination_hints(contract)
    return contract


def destination_hints(contract: dict) -> dict:
    """Pistas de destino; no son veredictos ni admisión a ningún examen."""
    symbol = contract['market'].get('symbol') or ''
    timeframe = (contract['market'].get('timeframe') or '').upper()
    options = contract.get('options', {})
    flat_eod = options.get('ExitAtEndOfDay') == 'true'
    futures = symbol.startswith('@') or bool(contract['market'].get('reference_contract'))
    proxy = contract['market'].get('known_proxy_alias')
    return {
        'fondeo': {
            'instrument_is_futures_contract': futures,
            'data_is_known_cfd_proxy': bool(proxy),
            'flat_at_end_of_day': flat_eod,
            'eligible_for_provisional_exam_screen': futures and not proxy,
            'note': 'Elegible para un cribado provisional de examen; la admisión real depende de las reglas fechadas de cada modalidad.',
        },
        'ultra': {
            'timeframe_in_canonical_set': timeframe in ('M1', 'M5', 'M15', 'H1', 'H4'),
            'intraday_only': flat_eod,
            'note': 'Criterios Ultra en construcción; cualquier evaluación es exploratoria.',
        },
    }


def compare_rules(original_xml: bytes, candidate_xml: bytes) -> dict:
    """Clasifica un cambio de reglas: sin cambio, solo metadatos o cambio real."""
    same_bytes = original_xml == candidate_xml
    a, b = semantic_strategy(original_xml), semantic_strategy(candidate_xml)
    same_semantics = canonical(a) == canonical(b)
    changed = []
    if not same_semantics:
        left, right = param_paths(a), param_paths(b)
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                changed.append({'param': key, 'change': 'added' if key not in left else 'removed'})
            elif canonical(left[key]) != canonical(right[key]):
                # Solo hojas: un Param contenedor cambia porque cambia su hijo.
                if any(k.startswith(key + '/') for k in left):
                    continue
                changed.append({'param': key, 'before': (left[key].text or '').strip(),
                                'after': (right[key].text or '').strip()})
        if not changed:
            changed.append({'param': 'structure', 'change': 'Diferencia estructural fuera de parámetros'})
    return {
        'classification': ('IDENTICAL_BYTES' if same_bytes else
                           'METADATA_ONLY_NO_BEHAVIOUR_CHANGE' if same_semantics else 'RULES_CHANGED'),
        'semantic_sha256_before': sha(canonical(a).encode()),
        'semantic_sha256_after': sha(canonical(b).encode()),
        'changed_params': changed,
    }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--compare', type=Path, help='Segundo .sqx: clasifica el cambio de reglas')
    args = parser.parse_args()
    if args.compare:
        result = compare_rules(read_archive(args.source)['strategy_Portfolio.xml'],
                               read_archive(args.compare)['strategy_Portfolio.xml'])
    else:
        result = extract_contract(args.source)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text)
