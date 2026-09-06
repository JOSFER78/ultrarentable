"""Bounded native SQX exit experiments. No live trading or certification.

prepare creates an immutable control-and-variants experiment and a Retest project.
Load the dedicated project with load.cli, then use run on the VPS. SQX's
asynchronous import is checked before starting. Funding remains unverified.
"""
from __future__ import annotations

import argparse
import copy
import csv
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import hashlib
import io
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile
import time
import urllib.request
import subprocess
from datetime import datetime, timezone, timedelta, time as daytime
from zoneinfo import ZoneInfo


def sha(data):
    return hashlib.sha256(data).hexdigest()


def xml(data):
    return ET.tostring(data, encoding="utf-8", xml_declaration=True)


def canonical(node):
    return ET.canonicalize(ET.tostring(node, encoding="unicode"), strip_text=True)


def unique(root, xpath):
    nodes = root.findall(xpath)
    if len(nodes) != 1:
        raise ValueError(f"Expected exactly one {xpath}; found {len(nodes)}")
    return nodes[0]


def mutate_exit(strategy, gid, expected, value):
    """Change exactly one fixed-value exit; reject entry or formula mutations."""
    root = ET.fromstring(strategy)
    before = canonical(root)
    exit_node = unique(root, f".//Param[@gid='{gid}']")
    if exit_node.get("exitMethodType") not in ("PT", "SL"):
        raise ValueError("Only PT or SL exits may be changed")
    formula = unique(exit_node, "Formula[@key='SQ.Formulas.SLPT.FixedValue']")
    param = unique(formula, "Param[@key='#Value#']")
    old = param.text
    if Decimal(old) != Decimal(expected):
        raise ValueError("Original exit differs from the reviewed plan")
    if not Decimal(expected) * Decimal("0.9") <= Decimal(value) <= Decimal(expected) * Decimal("1.1"):
        raise ValueError("Experiment limited to +/-10%")
    param.text = str(value)
    changed = xml(root)
    param.text = old
    if canonical(root) != before:
        raise ValueError("Unexpected change outside selected parameter")
    return changed


def bounded_exit_values(expected, step):
    center, unit = Decimal(expected), Decimal(step)
    if not all(v.is_finite() and v > 0 for v in (center, unit)) or center % unit:
        raise ValueError('Exit must be a positive multiple of its reviewed unit step')
    low = (center * Decimal('0.9') / unit).to_integral_value(rounding=ROUND_CEILING) * unit
    high = (center * Decimal('1.1') / unit).to_integral_value(rounding=ROUND_FLOOR) * unit
    if not low < center < high:
        raise ValueError('Unit step cannot produce two distinct variants within +/-10%')
    return dict(BASE=str(center), EXIT90=str(low), EXIT110=str(high))


def replace_reviewed_percent_pt(strategy, gid, percent, points):
    """Explicit new hypothesis, NOT an equivalent conversion of percent to points."""
    root = ET.fromstring(strategy)
    node = unique(root, f".//Param[@gid='{gid}']")
    if node.get('exitMethodType') != 'PT':
        raise ValueError('Percent replacement requires a PT exit')
    formula = unique(node, "Formula[@key='SQ.Formulas.SLPT.PctValue']")
    param = unique(formula, "Param[@key='#Value#']")
    values = [Decimal(v) for v in (param.text, percent, points)]
    if not all(v.is_finite() and v > 0 for v in values) or values[0] != values[1]:
        raise ValueError('Percent PT differs from reviewed positive hypothesis')
    formula.set('key', 'SQ.Formulas.SLPT.FixedValue')
    param.text = str(points)
    return xml(root)


UTC_SESSION_PARAMS = {
    'LimitTimeRange': 'true', 'SignalTimeRangeFrom': '0',
    'SignalTimeRangeTo': '68400', 'ExitAtEndOfRange': 'true',
    'OrderTypeToExit': '0', 'DontTradeOnWeekends': 'true',
    'FridayCloseTime': '68400', 'SundayOpenTime': '82800',
    'ExitOnFriday': 'true', 'FridayExitTime': '68400',
}


def verify_utc_session(last):
    chart = unique(last, 'Data/Setups/Setup/Chart')
    symbol = unique(last, f"Resources/Symbols/Symbol[@name='{chart.get('symbol')}']")
    if symbol.get('timezone') not in ('UTC', 'Etc/UTC'):
        raise ValueError('Conservative session requires verified UTC market data')


def source_resources(last):
    """Resolve declared charts, excluding obsolete template symbol references."""
    resources = copy.deepcopy(unique(last, 'Resources'))
    symbols = unique(resources, 'Symbols')
    used = {chart.get('symbol') for chart in unique(last, 'Data').iter('Chart')}
    if not used or None in used or '' in used:
        raise ValueError('Cannot resolve candidate chart symbols')
    if not used <= {symbol.get('name') for symbol in symbols}:
        raise ValueError('Candidate chart lacks resource provenance')
    for symbol in list(symbols):
        if symbol.get('name') not in used:
            symbols.remove(symbol)
    return resources


def exit_signature(node):
    """Ignore known editor/generator metadata, never formulas or parameter values.

    SQX's Improver can export an unchanged exit under new generator IDs and
    editor hints. Unknown attributes remain significant (fail conservatively).
    """
    node = copy.deepcopy(node)
    metadata = ('generated', 'randomId', 'gid', 'randomValue', 'name', 'help',
                'builderMinValue', 'builderMaxValue', 'builderStep',
                'recommendedMinValue', 'recommendedMaxValue')
    for item in node.iter():
        for key in metadata:
            item.attrib.pop(key, None)
        if item.get('identification') == '':
            item.attrib.pop('identification')
    return canonical(node)


def transplant_native_exits(original, candidate):
    """Transfer only native exit parameters; retain the original entry program.

    SQX rewrites metadata and empty exit signals when exporting Improver results.
    We do not transplant those rewrites or claim full-strategy equivalence.
    """
    base, variant = ET.fromstring(original), ET.fromstring(candidate)
    for section in ('Variables', 'Datas', 'CustomBlocks'):
        if canonical(unique(base, 'Strategy/' + section)) != canonical(unique(variant, 'Strategy/' + section)):
            raise ValueError('Native variant changed ' + section)
    def entry_signature(rule):
        rule = copy.deepcopy(rule)
        for node in rule.iter():
            node.attrib.pop('generated', None)
            node.attrib.pop('ruleIndex', None)
            for child in list(node):
                if child.tag == 'Param' and child.get('exitMethod') == 'true':
                    node.remove(child)
        action = unique(rule, 'Then/Item')
        if action.get('key') != 'EnterAtStop':
            raise ValueError('Unsupported native entry action')
        identification = unique(action, "Param[@key='#Identification#']")
        identification.attrib.pop('ownRandomKey', None)
        identification.text = 'PRESERVED_ORIGINAL_ACTION_ID'
        return canonical(rule)
    # Signal definitions used by entries must be unchanged. Empty exit signals
    # may be serialized as false, but the original representation is retained.
    rules_path = "Strategy/Rules/Events/Event[@key='OnBarUpdate']/Rule"
    a, b = (unique(tree, rules_path + "[@name='Trading signals']") for tree in (base, variant))
    empty_signals = {n.get('variable') for n in a.findall('signals/signal')
                     if not len(n) and not (n.text or '').strip()}
    def signal_signature(rule):
        rule = copy.deepcopy(rule)
        rule.attrib.pop('ruleIndex', None)
        for node in rule.iter():
            node.attrib.pop('generated', None)
        for tag in ('Then', 'Else'):
            node = rule.find(tag)
            if node is not None and not len(node) and not (node.text or '').strip():
                rule.remove(node)
        # Only an exact literal false is equivalent to the known empty value.
        for parent in rule.findall('signals/signal'):
            if parent.get('variable') not in empty_signals:
                continue
            for child in list(parent):
                if child.tag == 'Item' and child.get('key') == 'Boolean' and len(child) == 1:
                    value = child[0]
                    if value.tag == 'Param' and value.get('key') == '#Value#' and (value.text or '').strip() == 'false':
                        parent.remove(child)
        return canonical(rule)
    if signal_signature(a) != signal_signature(b):
        raise ValueError('Native variant changed entry signals')
    changed = 0
    for direction in ('Long', 'Short'):
        xpath = rules_path + f"[@name='{direction} entry']"
        original_rule, candidate_rule = unique(base, xpath), unique(variant, xpath)
        if entry_signature(original_rule) != entry_signature(candidate_rule):
            raise ValueError('Native variant changed entry rules')
        action, native_action = unique(original_rule, 'Then/Item'), unique(candidate_rule, 'Then/Item')
        old = action.findall("Param[@exitMethod='true']")
        new = native_action.findall("Param[@exitMethod='true']")
        old_keys, new_keys = [p.get('key') for p in old], [p.get('key') for p in new]
        if len(old_keys) != 7 or len(set(old_keys)) != 7 or sorted(old_keys) != sorted(new_keys):
            raise ValueError('Unsupported native exit parameter set')
        for before in old:
            after = next(p for p in new if p.get('key') == before.get('key'))
            if exit_signature(before) == exit_signature(after):
                continue
            changed += 1
            index = list(action).index(before)
            action.remove(before)
            action.insert(index, copy.deepcopy(after))
    if not changed:
        raise ValueError('Native variant contains no exit changes')
    return xml(base)


def prepare(source, template, output, remote_dir, project, gid=None, expected=None, step=None, integer_contracts=False, precision=2, percent_pt_original=None, conservative_utc_session=False, session_end_utc=19, native_variants=None, funding_profile=None):
    if not re.fullmatch(r"UR_IMPROVE_[A-Z0-9_]+", project):
        raise ValueError("Dedicated improvement project name required")
    if not re.fullmatch(r"/opt/SQX-headless/import/[A-Za-z0-9_/-]+", remote_dir) or '..' in remote_dir:
        raise ValueError("Unsafe remote directory")
    if type(session_end_utc) is not int or not 1 <= session_end_utc <= 19:
        raise ValueError('Session end must be an integer UTC hour from 1 through 19')
    if session_end_utc != 19 and not conservative_utc_session:
        raise ValueError('Explicit session end requires the session experiment flag')
    session_params = dict(UTC_SESSION_PARAMS)
    for key in ('SignalTimeRangeTo', 'FridayCloseTime', 'FridayExitTime'):
        session_params[key] = str(session_end_utc * 3600)
    with zipfile.ZipFile(source) as archive:
        original = {n: archive.read(n) for n in archive.namelist()}
    settings = ET.fromstring(original["settings.xml"])
    last = ET.fromstring(original["lastSettings.xml"])
    product_check = funding_product_profile(last, funding_profile) if funding_profile else None
    if product_check and not product_check['symbol_listed']:
        raise ValueError(f"Funding product not listed: {product_check['instrument']} in {funding_profile}")
    base_name = settings.attrib["ResultName"]
    strategy_name = "strategy_Portfolio.xml"
    native_rules, native_sources = {}, []
    if native_variants is not None:
        if len(native_variants) not in (1, 2) or any(v is not None for v in (gid, expected, step, percent_pt_original)):
            raise ValueError('Native comparison requires one or two variants and no fixed mutation')
        for index, path in enumerate(native_variants, 1):
            data = Path(path).read_bytes()
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                native_rules[f'NATIVE{index}'] = transplant_native_exits(original[strategy_name], archive.read(strategy_name))
            native_sources.append({'file': Path(path).name, 'sha256': sha(data)})
        if len({sha(v) for v in native_rules.values()}) != len(native_variants):
            raise ValueError('Duplicate native exit recipes')
        exit_values = dict(BASE=None, **{name: None for name in native_rules})
    else:
        exit_values = bounded_exit_values(expected, step)
    # Validate the reviewed mutation before creating anything.
    mutation_source = original[strategy_name]
    if percent_pt_original is not None:
        mutation_source = replace_reviewed_percent_pt(mutation_source, gid, percent_pt_original, expected)
    if not native_variants:
        mutate_exit(mutation_source, gid, expected, expected)
    with zipfile.ZipFile(template) as archive:
        task = ET.fromstring(archive.read("Retest-Task1.xml"))
        config = ET.fromstring(archive.read("config.xml"))
    resources = source_resources(last)
    for tag in ("Options", "RiskMoneyManagement", "ATMs", "Data", "Resources"):
        replacement = copy.deepcopy(resources if tag == 'Resources' else unique(last, tag))
        old = unique(task, tag)
        task.remove(old)
        if tag in ("Options", "RiskMoneyManagement"):
            replacement.set("customSettings", "true")
        task.append(replacement)
    old_resources = config.find('Resources')
    if old_resources is not None:
        config.remove(old_resources)
    config.append(copy.deepcopy(resources))
    if precision not in (1, 2):
        raise ValueError('Supported precision: 1 selected timeframe, 2 one-minute simulation')
    unique(task, 'Data/Setups/Setup').set('testPrecision', str(precision))
    if conservative_utc_session:
        verify_utc_session(task)
        # SQX task XML stores Time editor values in seconds after midnight.
        # This is a conservative experiment, not a complete exchange calendar.
        for key, value in session_params.items():
            unique(task, f"Options/BuildTradingOptions/Params/Param[@key='{key}']").text = value
    if integer_contracts:
        mm = unique(task, "RiskMoneyManagement/MoneyManagement/Method[@use='true']")
        if mm.get('type') != 'RiskFixedBalancePct':
            raise ValueError('Integer sizing requires the reviewed RiskFixedBalancePct method')
        unique(mm, "Params/Param[@key='Decimals']").text = '0'
    for condition in task.findall("Rankings/Conditions/Condition"):
        condition.set("use", "false")
    unique(task, "Rankings/MaxStrategies").text = str(len(exit_values))
    for check in task.findall("CrossChecks/*"):
        if "use" in check.attrib:
            check.set("use", "false")
    config.set("name", project)
    for bank in config.findall("Databanks/Databank"):
        bank.set("syncType", "Auto-sync never")
    output.mkdir(parents=True, exist_ok=False)
    (output / "input").mkdir()
    manifest = {
        "schema": 1, "project": project, "source_name": base_name,
        "source_sha256": sha(source.read_bytes()), "source_rules_sha256": sha(original[strategy_name]),
        "state": "PREPARED_NOT_RECALCULATED", "funding_verdict": "NO_EVALUABLE",
        "selection_data_is_development": True,
        "hypothesis": "A modest change to the selected fixed exit may improve return/drawdown without changing entries.",
        "max_variants": 2, "gid": gid, "exit_unit_step": step, "entries": [],
        "integer_contracts_requested": integer_contracts,
        "precision_requested": precision,
        "limitations": ["Input archives contain inherited historical results; only fresh RetestResults count.",
                        "Development OOS is not a final holdout.",
                        "No intraday equity path, exam session checks, or integer-contract proof yet."],
    }
    if product_check is not None:
        manifest['funding_product_check'] = product_check
    if percent_pt_original is not None:
        manifest['hypothesis'] = 'Keep original percent PT control; test two fixed-distance PT alternatives with unchanged initial stop protection. This changes the strategy and is not an equivalent conversion.'
        manifest['percent_pt_replacement'] = {'original_percent': percent_pt_original, 'fixed_center_points': expected}
    if conservative_utc_session:
        manifest['session_experiment'] = {
            'params': session_params, 'timezone': 'Etc/UTC',
            'scope': 'All retests including BASE use the changed session; BASE is not the unrestricted original.',
            'limitations': f'Conservative UTC 00:00-{session_end_utc:02d}:00; native TS exits depend on bar close. Check actual orders, holidays and early closes separately.',
        }
    if native_variants:
        manifest.update(native_exit_sources=native_sources,
                        hypothesis='Transfer up to two native exit recipes to the unchanged original entry program and compare under identical fresh retest conditions. Native historical results are not reused.')
    for label in exit_values:
        value = exit_values[label]
        name = f"{base_name}_{label}"
        payload = dict(original)
        renamed = ET.fromstring(original["settings.xml"])
        renamed.set("ResultName", name)
        payload["settings.xml"] = xml(renamed)
        if label != "BASE":
            payload[strategy_name] = native_rules[label] if native_variants else mutate_exit(mutation_source, gid, expected, value)
        path = output / "input" / f"{name}.sqx"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for key, data in payload.items():
                archive.writestr(key, data)
        manifest["entries"].append({"name": name, "file": str(path.name), "exit_value": percent_pt_original if label == 'BASE' and percent_pt_original is not None else value,
                                    "exit_unit": 'native_recipe' if native_variants else ('percent' if label == 'BASE' and percent_pt_original is not None else 'fixed'),
                                    "sha256": sha(path.read_bytes()),
                                    "rules_sha256": sha(payload[strategy_name])})
    config_path = output / "project.cfx"
    with zipfile.ZipFile(config_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("config.xml", xml(config))
        archive.writestr("Retest-Task1.xml", xml(task))
    manifest["config_sha256"] = sha(config_path.read_bytes())
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "load.cli").write_text(f"-project action=loadconfig name={project} file={remote_dir}/project.cfx\n", encoding="utf-8")
    strategy_names = ','.join(e['name'] for e in manifest['entries'])
    (output / "import.cli").write_text(
        f'-databank action=load project={project} name=Input folder={remote_dir}/input strategies="{strategy_names}"\n',
        encoding="utf-8")
    (output / "collect.cli").write_text(
        f"-databank action=export project={project} name=RetestResults file={remote_dir}/retest.csv\n"
        f"-databank action=save project={project} name=RetestResults folder={remote_dir}/retested\n",
        encoding="utf-8")
    return manifest


def gate_entry_dates(rules, start, end, date_encoding='NATIVE_GET_DATE', date_source='BarDate'):
    """Add native SQX date predicates to both entries; preserve all other rules."""
    result = copy.deepcopy(rules)
    entries = [r for r in result.findall('.//Rule')
               if r.get('name') in ('Long entry', 'Short entry')]
    if len(entries) != 2:
        raise ValueError('Requires exactly the reviewed long and short entry rules')
    actions = result.findall('.//Item[@key="EnterAtStop"]')
    if len(actions) != 2 or any(len(r.findall('.//Item[@key="EnterAtStop"]')) != 1 for r in entries):
        raise ValueError('Unsupported entry actions')
    for rule in entries:
        condition = unique(rule, 'If')
        if len(condition) != 1 or condition[0].tag != 'Item':
            raise ValueError('Unsupported entry condition')
        original = condition[0]
        condition.remove(original)
        wrapper = ET.SubElement(condition, 'Item', key='AND')
        # Evaluate the original expression first, including during warmup.
        ET.SubElement(wrapper, 'Block').append(original)
        for operator, date in (('IsGreaterOrEqual', start), ('IsLowerOrEqual', end)):
            comparison = ET.SubElement(ET.SubElement(wrapper, 'Block'), 'Item',
                                       key=operator, returnType='boolean')
            left = ET.SubElement(comparison, 'Block', key='#Left#')
            if date_source not in ('BarDate', 'CurrentDate'):
                raise ValueError('Unsupported date source')
            clock = ET.SubElement(left, 'Item', key=date_source, returnType='number')
            if date_source == 'BarDate':
                ET.SubElement(clock, 'Param', key='#Chart#', type='data', controlType='dataVar').text = '0'
                ET.SubElement(clock, 'Param', key='#Shift#', type='int', controlType='jspinnerVar').text = '0'
            right = ET.SubElement(comparison, 'Block', key='#Right#')
            if date_encoding == 'LEGACY_YYYYMMDD':
                # Reconstruct old evidence only; new runs must use SQX's date encoding.
                number = ET.SubElement(right, 'Item', key='Number', returnType='number')
                ET.SubElement(number, 'Param', key='#Number#', type='double').text = date.strftime('%Y%m%d')
            elif date_encoding == 'NATIVE_GET_DATE':
                native_date = ET.SubElement(right, 'Item', key='GetDate', returnType='number')
                for key, value in (('Day', date.day), ('Month', date.month), ('Year', date.year)):
                    ET.SubElement(native_date, 'Param', key=f'#{key}#', type='int').text = str(value)
            else:
                raise ValueError('Unsupported native date encoding')
    return result


def verify_entry_gate(root, entry, spec):
    """Rebuild the exact wrapper from preserved parent rules, not a trusted label."""
    parent = root / 'parent_input' / entry['file']
    if sha(parent.read_bytes()) != entry['parent_input_sha256']:
        raise ValueError('Parent input for date gate changed')
    with zipfile.ZipFile(parent) as archive:
        original = ET.fromstring(archive.read('strategy_Portfolio.xml'))
    expected = gate_entry_dates(original, *(datetime.strptime(spec[k], '%Y-%m-%d').date()
                                          for k in ('start', 'end')),
                                date_encoding=spec.get('date_encoding', 'LEGACY_YYYYMMDD'),
                                date_source=spec.get('date_source', 'CurrentDate'))
    with zipfile.ZipFile(root / 'input' / entry['file']) as archive:
        actual = ET.fromstring(archive.read('strategy_Portfolio.xml'))
    if canonical(expected) != canonical(actual):
        raise ValueError('Date gate changed original strategy beyond the declared wrapper')


def prepare_fresh_attempt(parent_manifest, output, remote_dir, project, start, end, warmup_start=None):
    """Retest the same three rules from a fresh balance; no window optimization."""
    native_evidence(parent_manifest)
    if not re.fullmatch(r'UR_IMPROVE_[A-Z0-9_]+', project):
        raise ValueError('Invalid dedicated project')
    if not re.fullmatch(r'/opt/SQX-headless/import/[A-Za-z0-9_/-]+', remote_dir) or '..' in remote_dir:
        raise ValueError('Invalid remote directory')
    first, last = (datetime.strptime(v, '%Y-%m-%d').date() for v in (start, end))
    if first.weekday() != 0 or last != first + timedelta(days=4):
        raise ValueError('This bounded diagnostic requires one Monday-Friday window')
    parent = json.loads(parent_manifest.read_text(encoding='utf-8'))
    if parent.get('fresh_attempt') or len(parent['entries']) != 3:
        raise ValueError('Requires a verified three-strategy development comparison')
    with zipfile.ZipFile(parent_manifest.parent / 'project.cfx') as archive:
        payload = {n: archive.read(n) for n in archive.namelist()}
    task = ET.fromstring(payload['Retest-Task1.xml'])
    setup = unique(task, 'Data/Setups/Setup')
    old_start, old_end = (datetime.strptime(setup.get(k), '%Y.%m.%d').date()
                          for k in ('dateFrom', 'dateTo'))
    if not old_start <= first <= last <= old_end:
        raise ValueError('Diagnostic window lies outside the original data range')
    history_start = datetime.strptime(warmup_start, '%Y-%m-%d').date() if warmup_start else first
    if warmup_start and not old_start <= history_start < first:
        raise ValueError('Warmup must precede entries and remain inside original data')
    oos = unique(task, 'Data/OutOfSample/Range')
    for node in (setup, oos):
        node.set('dateFrom', first.strftime('%Y.%m.%d'))
        node.set('dateTo', last.strftime('%Y.%m.%d'))
    setup.set('dateFrom', history_start.strftime('%Y.%m.%d'))
    unique(task, 'RiskMoneyManagement/MoneyManagement/InitialCapital').text = '50000'
    payload['Retest-Task1.xml'] = xml(task)
    config = ET.fromstring(payload['config.xml'])
    config.set('name', project)
    payload['config.xml'] = xml(config)
    manifest = copy.deepcopy(parent)
    manifest.update(project=project, state='PREPARED_FRESH_ACCOUNT_NOT_RECALCULATED',
                    fresh_attempt={'start': start, 'end': end, 'initial_capital': '50000',
                                   'parent_manifest_sha256': sha(parent_manifest.read_bytes()),
                                   'parent_project': parent['project'],
                                   'selection': 'Known development window; diagnostic, not held-out evidence',
                                   'strategy_rules_changed': False})
    if warmup_start:
        manifest['fresh_attempt'].update(warmup_start=warmup_start, strategy_rules_changed=True,
                                        entry_gate='NATIVE_BAR_DATE_INCLUSIVE', date_source='BarDate',
                                        date_encoding='NATIVE_GET_DATE')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'input').mkdir()
    if warmup_start:
        (output / 'parent_input').mkdir()
    for entry in manifest['entries']:
        data = (parent_manifest.parent / 'input' / entry['file']).read_bytes()
        if sha(data) != entry['sha256']:
            raise ValueError('Parent input changed')
        if warmup_start:
            (output / 'parent_input' / entry['file']).write_bytes(data)
            entry['parent_input_sha256'] = sha(data)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                contents = {n: archive.read(n) for n in archive.namelist()}
            gated = gate_entry_dates(ET.fromstring(contents['strategy_Portfolio.xml']), first, last)
            contents['strategy_Portfolio.xml'] = xml(gated)
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
                for name, content in contents.items():
                    archive.writestr(name, content)
            data = buffer.getvalue()
            entry.update(sha256=sha(data), rules_sha256=sha(canonical(gated).encode('utf-8')))
        (output / 'input' / entry['file']).write_bytes(data)
    with zipfile.ZipFile(output / 'project.cfx', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in payload.items():
            archive.writestr(name, data)
    manifest['config_sha256'] = sha((output / 'project.cfx').read_bytes())
    atomic_report(output / 'manifest.json', manifest)
    (output / 'load.cli').write_text(f'-project action=loadconfig name={project} file={remote_dir}/project.cfx\n', encoding='utf-8')
    names = ','.join(e['name'] for e in manifest['entries'])
    (output / 'import.cli').write_text(f'-databank action=load project={project} name=Input folder={remote_dir}/input strategies="{names}"\n', encoding='utf-8')
    (output / 'collect.cli').write_text(
        f'-databank action=export project={project} name=RetestResults file={remote_dir}/retest.csv\n'
        f'-databank action=save project={project} name=RetestResults folder={remote_dir}/retested\n', encoding='utf-8')
    return manifest


def native_evidence(manifest_path):
    """Reject cached inputs, incomplete runs and changed strategy rules."""
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if sha((root / 'project.cfx').read_bytes()) != manifest['config_sha256']:
        raise ValueError('Project configuration changed after preparation')
    with zipfile.ZipFile(root / 'project.cfx') as config_archive:
        task = ET.fromstring(config_archive.read('Retest-Task1.xml'))
    expected_risk = unique(task, 'RiskMoneyManagement')
    if expected_risk.get('customSettings') != 'true':
        raise ValueError('Experiment must explicitly override historical money management')
    start = json.loads((root / 'verified_start.json').read_text(encoding='utf-8'))
    counts = [re.findall(r'\bRecords:\s*(\d+)\b', start[key]) for key in ('input', 'output_before')]
    expected_count = len(manifest['entries'])
    if expected_count not in (2, 3) or counts != [[str(expected_count)], ['0']]:
        raise ValueError('Missing evidence of all planned inputs and empty output before start')
    if manifest['project'] not in start['start']:
        raise ValueError('Start evidence belongs to a different project')
    log = (root / 'native_retest.log').read_text(encoding='utf-8')
    required = (manifest['project'], 'RetestResults (0)', f'RetestResults ({expected_count})',
                'TAREA TERMINADA', f'Éxito: {expected_count}, Fallido: 0')
    if not all(token in log for token in required):
        raise ValueError('Native completion of all planned retests is not proven')
    artifacts = []
    for entry in manifest['entries']:
        if manifest.get('fresh_attempt', {}).get('warmup_start'):
            verify_entry_gate(root, entry, manifest['fresh_attempt'])
        src = root / 'input' / entry['file']
        dst = root / 'retested' / entry['file']
        if sha(src.read_bytes()) != entry['sha256']:
            raise ValueError('Prepared input changed')
        if src.read_bytes() == dst.read_bytes():
            raise ValueError('Cached input copied as native retest output')
        with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
            if canonical(ET.fromstring(a.read('strategy_Portfolio.xml'))) != canonical(ET.fromstring(b.read('strategy_Portfolio.xml'))):
                raise ValueError('Retested strategy rules differ from planned input')
            result_settings = ET.fromstring(b.read('settings.xml'))
            last = ET.fromstring(b.read('lastSettings.xml'))
            if canonical(unique(last, 'RiskMoneyManagement')) != canonical(expected_risk):
                raise ValueError('Native money management differs from prepared experiment')
            if canonical(unique(last, 'Data')) != canonical(unique(task, 'Data')):
                raise ValueError('Native data settings differ from prepared experiment')
            if 'session_experiment' in manifest:
                verify_utc_session(last)
                for key, value in manifest['session_experiment']['params'].items():
                    if unique(last, f"Options/BuildTradingOptions/Params/Param[@key='{key}']").text != value:
                        raise ValueError('Native session differs from prepared experiment: ' + key)
            if result_settings.get('ResultName') != entry['name']:
                raise ValueError('Native result name mismatch')
            if 'precision_requested' in manifest:
                for key in ('BacktestPrecision', 'Precision'):
                    if unique(result_settings, './/' + key).text != str(manifest['precision_requested']):
                        raise ValueError('Native execution precision differs from prepared experiment')
        artifacts.append({'name': entry['name'], 'sha256': sha(dst.read_bytes())})
    return {'start_sha256': sha((root / 'verified_start.json').read_bytes()),
            'log_sha256': sha((root / 'native_retest.log').read_bytes()), 'artifacts': artifacts}


def fresh_memory_alert(log_dir, offsets):
    """Read only new native log bytes; old memory failures cannot reject a new run."""
    for log in sorted(log_dir.glob('log_*.log')):
        offset = offsets.get(str(log), 0)
        size = log.stat().st_size
        if size < offset:  # Rotation/truncation in place.
            offset = 0
        with log.open('rb') as stream:
            stream.seek(offset)
            content = stream.read().decode('utf-8', errors='replace')
        for line in content.splitlines():
            if 'Memory usage limit reached' in line:
                return {'file': str(log), 'line': line}
    return None


def reviewed_identity(manifest_path):
    """Identify native work by actual rules and retest settings, not project names."""
    root = manifest_path.resolve().parent
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if len(manifest['entries']) not in (2, 3) or manifest['max_variants'] != 2:
        raise ValueError('Reviewed experiments require one control and one or two variants')
    config = (root / 'project.cfx').read_bytes()
    if sha(config) != manifest['config_sha256']:
        raise ValueError('Prepared project was changed')
    rules = []
    for entry in manifest['entries']:
        filename = entry['file']
        if Path(filename).name != filename or not filename.endswith('.sqx'):
            raise ValueError('Input must be a named local SQX archive')
        payload = (root / 'input' / filename).read_bytes()
        if sha(payload) != entry['sha256']:
            raise ValueError('Prepared input changed')
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            strategy = archive.read('strategy_Portfolio.xml')
        if sha(strategy) != entry['rules_sha256']:
            raise ValueError('Prepared rules changed')
        rules.append(canonical(ET.fromstring(strategy)))
    with zipfile.ZipFile(io.BytesIO(config)) as archive:
        task = canonical(ET.fromstring(archive.read('Retest-Task1.xml')))
    return sha(json.dumps({'rules': rules, 'task': task}, sort_keys=True).encode())


def claim_reviewed_experiment(registry, identity, manifest_path):
    """Exclusive durable claim. A crash leaves an explicit reconciliation block."""
    registry.mkdir(parents=True, exist_ok=True)
    record = registry / (identity + '.json')
    if record.exists():
        raise ValueError('Experiment already recorded; inspect its result instead of rerunning')
    active = registry / 'active.json'
    claim = {'state': 'CLAIMED_NOT_STARTED', 'identity': identity,
             'manifest': str(manifest_path.resolve()),
             'utc': datetime.now(timezone.utc).isoformat()}
    # Exclusive creation protects against another caller, including another hypothesis.
    with active.open('x', encoding='utf-8') as stream:
        json.dump(claim, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    # A previous caller may have completed between the first check and our claim.
    if record.exists():
        os.replace(active, registry / (identity + '_denied_' + str(time.time_ns()) + '.json'))
        raise ValueError('Experiment already recorded; concurrent duplicate denied')
    atomic_report(record, claim)
    return record, active, claim


def run_reviewed(manifest_path):
    """Load, retest and assess one reviewed recipe, with no blind retries."""
    root = manifest_path.resolve().parent
    if not str(root).startswith('/opt/SQX-headless/import/'):
        raise ValueError('Reviewed native execution is VPS-only')
    identity = reviewed_identity(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('fresh_attempt'):
        raise ValueError('Reviewed execution currently accepts development comparisons only')
    project = manifest['project']
    if not re.fullmatch(r'UR_IMPROVE_[A-Z0-9_]+', project):
        raise ValueError('Dedicated improvement project required')
    if not re.fullmatch(r'/opt/SQX-headless/import/[A-Za-z0-9_/-]+', str(root)):
        raise ValueError('Unsafe experiment path')
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    if int(memory['MemAvailable'].split()[0]) < 8 * 1024 * 1024:
        raise RuntimeError('Less than 8 GiB available; leave capacity for continuous generation')
    registry = Path('/opt/SQX-headless/import/reviewed_improvement_jobs')
    record, active, claim = claim_reviewed_experiment(registry, identity, manifest_path)
    try:
        claim['state'] = 'NATIVE_WORK_MAY_BE_RUNNING'
        atomic_report(record, claim)
        # Persist uncertainty BEFORE any native mutation. Never reload an existing project.
        with urllib.request.urlopen('http://127.0.0.1:5050/call?cmd=-project%20action=list', timeout=30) as response:
            projects = response.read().decode('utf-8')
        (root / 'projects_before.txt').write_text(projects, encoding='utf-8')
        if project in projects:
            raise ValueError('Dedicated project already exists; reconcile before any load')
        command = f'-project action=loadconfig name={project} file={root}/project.cfx'
        with urllib.request.urlopen('http://127.0.0.1:5050/call?cmd=' + command.replace(' ', '%20'), timeout=30) as response:
            loaded = response.read().decode('utf-8')
        (root / 'load_response.txt').write_text(loaded, encoding='utf-8')
        if f"Project loaded '{project}'" not in loaded:
            raise RuntimeError('Project load not confirmed; do not retry automatically')
        result = run_native(manifest_path)
        assessment_path = root / 'assessment.json'
        if json.loads(assessment_path.read_text(encoding='utf-8')) != result:
            raise ValueError('Persisted assessment differs from returned result')
        claim.update(state='COMPLETED_NOT_FUNDING_CERTIFIED',
                     completed_utc=datetime.now(timezone.utc).isoformat(),
                     assessment=str(assessment_path), assessment_sha256=sha(assessment_path.read_bytes()))
        atomic_report(record, claim)
        os.replace(active, registry / (identity + '_closed_claim.json'))
        return result
    except BaseException as exc:
        claim.update(state='NEEDS_RECONCILIATION', error=f'{type(exc).__name__}: {exc}')
        atomic_report(record, claim)
        # Keep active.json: even another recipe must not overlap an uncertain native run.
        raise


def check_start_response(response, root, project):
    """Persist explicit native refusals before waiting for nonexistent work."""
    normalized = response.casefold()
    if any(marker in normalized for marker in (
        'unresolved resources', 'no se puede iniciar', 'cannot start',
        'could not start', 'unable to start',
    )):
        diagnostic = {'state': 'START_REFUSED', 'project': project,
                      'utc': datetime.now(timezone.utc).isoformat(),
                      'native_response': response, 'retest_started': False}
        (root / 'start_failure.json').write_text(json.dumps(diagnostic, indent=2), encoding='utf-8')
        raise RuntimeError('SQX refused to start the dedicated retest; see start_failure.json')


def run_native(manifest_path, *, evidence_only=False):
    """Run on the VPS after loading the dedicated project with load.cli."""
    root = manifest_path.resolve().parent
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    project = manifest['project']
    if not re.fullmatch(r'UR_IMPROVE_[A-Z0-9_]+', project) or not str(root).startswith('/opt/SQX-headless/import/'):
        raise ValueError('Only dedicated improvement projects on the VPS are allowed')
    if sha((root / 'project.cfx').read_bytes()) != manifest['config_sha256']:
        raise ValueError('Prepared project was changed')
    def call(cmd):
        with urllib.request.urlopen('http://127.0.0.1:5050/call?cmd=' + cmd.replace(' ', '%20'), timeout=30) as response:
            return response.read().decode('utf-8')
    def count(bank, expected):
        result = call(f'-databank action=count project={project} name={bank}')
        match = re.search(r'Records:\s*(\d+)', result)
        if not match or int(match[1]) != expected:
            raise ValueError(f'{bank}: expected {expected} records; got {result}')
        return result
    count('Input', 0)
    count('RetestResults', 0)
    for entry in manifest['entries']:
        if sha((root / 'input' / entry['file']).read_bytes()) != entry['sha256']:
            raise ValueError('Prepared input changed')
    native_logs = Path('/opt/SQX-headless/user/log/StrategyQuant')
    offsets = {str(log): log.stat().st_size for log in native_logs.glob('log_*.log')}
    (root / 'import_response.txt').write_text(call(f'-run file={root}/import.cli'), encoding='utf-8')
    # SQX acknowledges loading before the databank is populated.
    deadline = time.time() + 45
    while True:
        try:
            count('Input', len(manifest['entries']))
            break
        except ValueError:
            alert = fresh_memory_alert(native_logs, offsets)
            if alert:
                diagnostic = {'state': 'IMPORT_INCOMPLETE_WITH_NATIVE_MEMORY_ALERT',
                              'project': project, 'utc': datetime.now(timezone.utc).isoformat(),
                              'native_alert': alert, 'retest_started': False}
                (root / 'import_failure.json').write_text(json.dumps(diagnostic, indent=2), encoding='utf-8')
                raise RuntimeError('Import incomplete: SQX reports memory limit; retest was not started')
            if time.time() >= deadline:
                raise
            time.sleep(1)
    evidence = {'utc': datetime.now(timezone.utc).isoformat(), 'input': count('Input', len(manifest['entries'])),
                'output_before': count('RetestResults', 0)}
    started = time.time()
    evidence['start'] = call(f'-project action=start name={project}')
    (root / 'verified_start.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    check_start_response(evidence['start'], root, project)
    logs = Path('/opt/SQX-headless/user/projects') / project / 'log'
    while time.time() - started < 120:
        for log in logs.glob('global_log_*.log'):
            if log.stat().st_mtime < started:
                continue
            content = log.read_text(encoding='utf-8')
            if 'TAREA TERMINADA' in content:
                (root / 'native_retest.log').write_text(content, encoding='utf-8')
                count('RetestResults', len(manifest['entries']))
                (root / 'collect_response.txt').write_text(call(f'-run file={root}/collect.cli'), encoding='utf-8')
                deadline = time.time() + 45
                expected = [root / 'retest.csv'] + [root / 'retested' / e['file'] for e in manifest['entries']]
                while not all(f.is_file() and f.stat().st_size > 0 for f in expected):
                    if time.time() >= deadline:
                        raise TimeoutError('Native results were not saved completely')
                    time.sleep(1)
                export_orders(manifest_path)
                if evidence_only:
                    return native_evidence(manifest_path)
                evaluator = assess_fresh_attempt if manifest.get('fresh_attempt') else assess
                return evaluator(manifest_path, root / 'retest.csv')
        time.sleep(2)
    raise TimeoutError('Retest did not complete within 120 seconds; inspect dedicated project before retrying')


def export_orders(manifest_path):
    """Read only the fresh comparison archives, using SQX's own binary order reader."""
    native_evidence(manifest_path)
    root = manifest_path.resolve().parent
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    java = Path('/opt/SQX-headless/j64/bin/java')
    reader = Path(__file__).with_name('ExportNativeOrders.java')
    exports = []
    for entry in manifest['entries']:
        output = root / (entry['name'] + '_orders.csv')
        subprocess.run([str(java), '--class-path', '/opt/SQX-headless/internal/libs/*',
                        str(reader), str(root / 'retested' / entry['file']), str(output)],
                       check=True, capture_output=True, text=True, timeout=30)
        exports.append({'name': entry['name'], 'native_sha256': sha((root / 'retested' / entry['file']).read_bytes()),
                        'orders_sha256': sha(output.read_bytes())})
    provenance = {'reader_sha256': sha(reader.read_bytes()), 'exports': exports}
    (root / 'orders_export.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    return provenance


def native_exit_diagnostic(rows):
    """Inspect recorded native PT fills; do not infer how SQX computed the target."""
    required = ('close_type', 'take_profit', 'open_price', 'is_long', 'is_short')
    if not rows or not all(all(key in row for key in required) for row in rows):
        return {'state': 'NATIVE_EXIT_FIELDS_UNAVAILABLE'}
    counts, invalid_pt = {}, 0
    for row in rows:
        close_type = str(int(row['close_type']))
        counts[close_type] = counts.get(close_type, 0) + 1
        if (row['is_long'], row['is_short']) not in (('true', 'false'), ('false', 'true')):
            raise ValueError('Ambiguous native order direction')
        target, opened = Decimal(row['take_profit']), Decimal(row['open_price'])
        if not target.is_finite() or not opened.is_finite():
            raise ValueError('Invalid native exit price')
        # OrderCloseTypes.PT == 3 in the installed SQX library.
        if close_type == '3' and ((row['is_long'] == 'true' and target <= opened)
                                  or (row['is_short'] == 'true' and target >= opened)):
            invalid_pt += 1
    return {'state': 'NATIVE_EXIT_FIELDS_INSPECTED', 'close_types': counts,
            'pt_fills_with_nonpositive_target_distance': invalid_pt}


def partition_native_orders(rows):
    """Separate explicitly canceled pending orders without discarding their evidence.

    SQX can retain MAE on canceled pending records; it is not an executed trade.
    Only records with both flags and no realized economic effect are excluded.
    Counts and P/L of executed orders must still reconcile with native metrics.
    """
    executed, canceled = [], []
    for row in rows:
        flags = tuple(row[k] for k in ('is_balance', 'is_canceled', 'is_pending'))
        if row['sample'] not in ('11', '21'):
            raise ValueError('Unsupported sample or non-executed native order')
        if flags == ('false', 'false', 'false'):
            executed.append(row)
        elif flags == ('false', 'true', 'true'):
            effects = [Decimal(row[k]) for k in ('pl', 'commission_swap', 'slippage_money')]
            if any(not value.is_finite() or value != 0 for value in effects):
                raise ValueError('Canceled pending order has economic effects')
            canceled.append(row)
        else:
            raise ValueError('Unsupported sample or non-executed native order')
    return executed, canceled


def diagnose_orders(manifest_path, metrics_path):
    """Reconcile native closed orders; never infer intraday exam survival from them."""
    native_evidence(manifest_path)
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    exports = json.loads((root / 'orders_export.json').read_text(encoding='utf-8'))['exports']
    if len(exports) != len(manifest['entries']) or {e['name'] for e in exports} != {e['name'] for e in manifest['entries']}:
        raise ValueError('Incomplete native orders provenance')
    provenance = {e['name']: e for e in exports}
    metrics = {r['Strategy Name']: r for r in csv.DictReader(
        metrics_path.read_text(encoding='utf-8-sig').splitlines(), delimiter=';')}
    reports = []
    for entry in manifest['entries']:
        path = root / (entry['name'] + '_orders.csv')
        proof = provenance[entry['name']]
        if (sha(path.read_bytes()) != proof['orders_sha256'] or
                sha((root / 'retested' / entry['file']).read_bytes()) != proof['native_sha256']):
            raise ValueError('Native order export changed after extraction')
        rows = list(csv.DictReader(path.read_text(encoding='utf-8').splitlines()))
        if not rows and not manifest.get('fresh_attempt'):
            raise ValueError('No native orders')
        rows, canceled = partition_native_orders(rows)
        amounts = [(Decimal(r['size']), Decimal(r['pl'])) for r in rows]
        if any(not size.is_finite() or size <= 0 or not pl.is_finite() for size, pl in amounts):
            raise ValueError('Invalid native size or P/L')
        if any(r['commission_applied'] != 'true' for r in rows):
            raise ValueError('Native commissions are not applied')
        with zipfile.ZipFile(root / 'retested' / entry['file']) as archive:
            last = ET.fromstring(archive.read('lastSettings.xml'))
        mm = unique(last, "RiskMoneyManagement/MoneyManagement/Method[@use='true']")
        if mm.get('type') == 'RiskFixedBalancePct':
            max_lots = Decimal(unique(mm, "Params/Param[@key='MaxLots']").text)
            if not max_lots.is_finite() or max_lots <= 0:
                raise ValueError('Invalid native maximum position size')
            if any(size > max_lots for size, _ in amounts):
                raise ValueError('Native position exceeds prepared maximum contracts')
        fractional = sum(size != size.to_integral_value() for size, _ in amounts)
        execution_review = []
        directional = {}
        if rows and all(k in rows[0] for k in ('is_long', 'is_short')):
            if any((r['is_long'], r['is_short']) not in (('true', 'false'), ('false', 'true')) for r in rows):
                raise ValueError('Ambiguous native order direction')
            for side in ('long', 'short'):
                selected = [r for r in rows if r['is_' + side] == 'true']
                immediate = sum(int(r['close_time']) == int(r['open_time']) for r in selected)
                directional[side] = {
                    'trades': len(selected), 'zero_duration': immediate,
                    'net_profit': str(sum((Decimal(r['pl']) for r in selected), Decimal(0))),
                    'winners': sum(Decimal(r['pl']) > 0 for r in selected),
                    'native_exits': native_exit_diagnostic(selected),
                }
                invalid_pt = directional[side]['native_exits'].get(
                    'pt_fills_with_nonpositive_target_distance', 0)
                if invalid_pt:
                    execution_review.append(
                        f'{invalid_pt} {side} PT fills have zero or adverse target distance; '
                        'target calculation requires review.')
                if selected and immediate == len(selected):
                    execution_review.append(f'All {side} orders close immediately; cause not established.')
        elif rows:
            execution_review.append('Direction fields unavailable in this historical export.')
        samples = {}
        for code, part in (('11', 'IS'), ('21', 'OOS')):
            selected = [r for r in rows if r['sample'] == code]
            total = sum((Decimal(r['pl']) for r in selected), Decimal(0))
            if (Decimal(len(selected)) != Decimal(metrics[entry['name']][f'# of trades ({part})'])
                    or abs(total - Decimal(metrics[entry['name']][f'Net profit ({part})'])) > Decimal('.05')):
                raise ValueError('Native orders do not reconcile with retest metrics')
            samples[part] = {'trades': len(selected), 'net_profit': str(total)}
        reports.append({'name': entry['name'], 'orders_sha256': sha(path.read_bytes()),
                        'canceled_pending_count': len(canceled),
                        'canceled_pending_records': canceled,
                        'fractional_orders': fractional, 'integer_contracts': fractional == 0,
                        'sizes': sorted({str(size) for size, _ in amounts}), 'samples': samples,
                        'directional': directional, 'execution_review': execution_review,
                        'funding_verdict': 'NO_EVALUABLE',
                        'blockers': (['Fractional futures quantities'] if fractional else []) + [
                            'No independent intraday equity replay: trailing loss survival is unknown.',
                            'No complete versioned exam profile with calendar and session checks.',
                            'Data provenance and execution precision not independently validated.',
                            'Development OOS reused for comparison; final holdout still required.']})
    result = {'schema': 1, 'state': 'NATIVE_ORDERS_RECONCILED_NOT_FUNDING_VALIDATION',
              'target_days': [1, 5], 'probada_para_fondeo': False, 'strategies': reports}
    (root / 'orders_diagnostic.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


TOPSTEP_PRODUCT_PROFILE = {
    'id': 'topstep_permitted_products_2026-09-06',
    'source': 'https://help.topstep.com/en/articles/8284206-when-and-what-products-can-i-trade',
    'source_updated': '2026-07-13', 'checked_on': '2026-09-06',
    'symbols': ('ES MES NQ MNQ RTY M2K NKD MBT MET 6A 6B 6C 6E 6J 6S E7 M6E M6A '
                '6M 6N M6B HE LE CL QM NG QG MCL RB HO PL MNG ZC ZW ZS ZM ZL YM MYM '
                'ZT ZF ZN TN ZB UB GC SI HG MGC SIL MHG').split(),
}


def funding_product_profile(settings, profile='topstep'):
    """A dated symbol-list gate only; an alias cannot establish futures provenance."""
    if profile != 'topstep':
        raise ValueError('Unsupported funding product profile')
    instrument = unique(settings, './/Data/Setups/Setup/Chart').get('symbol')
    if not instrument:
        raise ValueError('Missing native instrument')
    listed = instrument in TOPSTEP_PRODUCT_PROFILE['symbols']
    return {'state': ('PRODUCT_LISTED_IDENTITY_UNVERIFIED' if listed else 'BLOCKED_PRODUCT_NOT_LISTED'),
            'instrument': instrument, 'symbol_listed': listed,
            'profile': copy.deepcopy(TOPSTEP_PRODUCT_PROFILE),
            'probada_para_fondeo': False, 'next_stage_candidates': [],
            'limitations': [
                'Exact symbol comparison only; no alias, CFD or continuous-contract conversion.',
                'A listed symbol does not prove the dataset is the actual futures instrument.',
                'Dated product snapshot; current exam rules, product restrictions and calendar require verification.',
                'No conclusion about performance, sizing, execution or passing an exam.']}


def funding_product_check(source, output, profile='topstep'):
    """Persist a product decision for one real SQX source, revoking stale results on error."""
    report = {'state': 'BLOCKED_INVALID_OR_UNSUPPORTED_EVIDENCE',
              'probada_para_fondeo': False, 'next_stage_candidates': []}
    if Path(source).resolve() == Path(output).resolve():
        raise ValueError('Product report must not overwrite its source')
    try:
        data = Path(source).read_bytes()
        report['source_sha256'] = sha(data)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            raw = archive.read('lastSettings.xml')
        report.update(funding_product_profile(ET.fromstring(raw), profile))
        report.update(settings_sha256=sha(raw), checked_at=datetime.now(timezone.utc).isoformat(),
                      engine_sha256=sha(Path(__file__).read_bytes()))
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        atomic_report(Path(output), report)
        raise
    atomic_report(Path(output), report)
    return report


TOPSTEP_SESSION_PROFILE = {
    'id': 'topstep_mym_regular_session_2026-09-05',
    'scope': 'Example profile: MYM regular sessions only, not a complete exam profile',
    'source': 'https://help.topstep.com/en/articles/8284206-when-and-what-products-can-i-trade',
    'source_updated': '2026-07-13', 'checked_on': '2026-09-05',
    'timezone': 'America/Chicago', 'instrument': 'MYM',
    'flat_by': '15:10', 'reopen': '17:00',
    'weekend': 'Friday 15:10 through Sunday 17:00',
}


def native_session_profile(settings):
    """Bind the verified regular-session rule to a supported native instrument."""
    instrument = unique(settings, './/Data/Setups/Setup/Chart').get('symbol')
    product = funding_product_profile(settings)
    if not product['symbol_listed']:
        raise ValueError(f'Funding product not listed: {instrument} in topstep; session profile only supports MYM and MNQ')
    if instrument not in ('MYM', 'MNQ'):
        raise ValueError('This explicit session profile only supports MYM and MNQ')
    resource = unique(settings, f".//Resources/Symbols/Symbol[@name='{instrument}']")
    if resource.get('timezone') not in ('UTC', 'Etc/UTC'):
        raise ValueError('Native order timezone must be verified UTC')
    return {**TOPSTEP_SESSION_PROFILE,
            'id': f'topstep_{instrument.lower()}_regular_session_2026-09-06',
            'scope': f'Example profile: {instrument} regular sessions only, not a complete exam profile',
            'checked_on': '2026-09-06', 'instrument': instrument}


def session_violations(opened, closed):
    """Check regular CT closures, including DST. No holiday/calendar approval."""
    if opened.tzinfo is None or closed.tzinfo is None or closed < opened:
        raise ValueError('Invalid or timezone-naive native order interval')
    zone = ZoneInfo(TOPSTEP_SESSION_PROFILE['timezone'])
    opened, closed = opened.astimezone(zone), closed.astimezone(zone)
    if closed - opened > timedelta(days=3660):
        raise ValueError('Unsupported order duration')
    reasons = set()
    day = opened.date()
    while day <= closed.date():
        # Represent every day's forbidden interval, including full Saturday.
        weekday = day.weekday()
        start_time = daytime(15, 10) if weekday < 5 else daytime(0)
        end_time = daytime(17) if weekday < 4 or weekday == 6 else daytime(0)
        start = datetime.combine(day, start_time, zone)
        end_day = day + timedelta(days=1) if weekday in (4, 5) else day
        end = datetime.combine(end_day, end_time, zone)
        if start <= opened < end:
            reasons.add('OPENED_DURING_REGULAR_CLOSURE')
        # A position closed exactly at the deadline is not held beyond it.
        if opened < end and closed > start and closed > opened:
            reasons.add('POSITION_HELD_DURING_REGULAR_CLOSURE')
        day += timedelta(days=1)
    return sorted(reasons)


def funding_session_screen(manifest_path, metrics_path):
    """Reject incompatible recorded sessions; never infer an exam pass from P&L."""
    diagnostic = diagnose_orders(manifest_path, metrics_path)
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    reports = []
    profile = None
    for entry in manifest['entries']:
        with zipfile.ZipFile(root / 'retested' / entry['file']) as archive:
            settings = ET.fromstring(archive.read('lastSettings.xml'))
        entry_profile = native_session_profile(settings)
        if profile is not None and entry_profile != profile:
            raise ValueError('Cannot compare different native session profiles')
        profile = entry_profile
        path = root / (entry['name'] + '_orders.csv')
        orders, _ = partition_native_orders(csv.DictReader(path.read_text(encoding='utf-8-sig').splitlines()))
        counts = {'IS': 0, 'OOS': 0}
        examples = []
        for row in orders:
            opened = datetime.fromtimestamp(int(row['open_time']) / 1000, timezone.utc)
            closed = datetime.fromtimestamp(int(row['close_time']) / 1000, timezone.utc)
            reasons = session_violations(opened, closed)
            if reasons:
                counts[{'11': 'IS', '21': 'OOS'}[row['sample']]] += 1
                if len(examples) < 3:
                    examples.append({'ticket': row['ticket'], 'sample': row['sample'],
                                     'open_utc': opened.isoformat(), 'close_utc': closed.isoformat(),
                                     'reasons': reasons})
        reports.append({'name': entry['name'], 'orders_sha256': sha(path.read_bytes()),
                        'orders': len(orders), 'incompatible_orders': counts,
                        'session_verdict': ('INCOMPATIBLE_RECORDED_SESSIONS' if sum(counts.values())
                                            else 'NO_REGULAR_SESSION_VIOLATION_FOUND'),
                        'examples': examples, 'funding_verdict': 'NO_EVALUABLE'})
    result = {'schema': 1, 'state': 'SESSION_SCREEN_ONLY_NOT_EXAM_VALIDATION',
              'profile': profile,
              'profile_sha256': sha(json.dumps(profile, sort_keys=True).encode()),
              'native_orders_state': diagnostic['state'], 'strategies': reports,
              'probada_para_fondeo': False, 'funding_verdict': 'NO_EVALUABLE',
              'limitations': ['Current regular rules applied retrospectively, not historical rule certification.',
                              'Holiday and exceptional early-close calendar not verified.',
                              'No independent intraday equity replay or complete exam evaluation.',
                              'Adding daily flatten changes the strategy and requires a fresh native retest.']}
    (root / 'funding_session_screen.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def compare(manifest_path, metrics_path):
    evidence = native_evidence(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(metrics_path.read_text(encoding="utf-8-sig").splitlines(), delimiter=";"))
    names = {entry["name"] for entry in manifest["entries"]}
    actual = [row["Strategy Name"] for row in rows]
    if len(rows) != len(manifest['entries']) or set(actual) != names:
        raise ValueError("Exactly baseline plus all planned native retest results required")
    diagnostic = diagnose_orders(manifest_path, metrics_path)
    order_reports = {r['name']: r for r in diagnostic['strategies']}
    base_orders = order_reports[manifest['entries'][0]['name']]
    index = {row["Strategy Name"]: row for row in rows}
    baseline = index[manifest["entries"][0]["name"]]
    metrics = ("Net profit", "Profit factor", "Ret/DD Ratio", "# of trades")
    def values(row):
        result = {f"{m} ({part})": Decimal(row[f"{m} ({part})"])
                  for m in metrics for part in ("IS", "OOS")}
        if not all(v.is_finite() for v in result.values()):
            raise ValueError("Non-finite native metrics")
        return result
    base = values(baseline)
    decisions = []
    for entry in manifest["entries"][1:]:
        val = values(index[entry["name"]])
        reasons = []
        for label, report in (('Baseline', base_orders), ('Variant', order_reports[entry['name']])):
            if not report['integer_contracts']:
                reasons.append(f'{label} has fractional futures quantities')
            if report['execution_review']:
                reasons.append(f'{label} requires execution review before promotion')
        for part, minimum in (("IS", 100), ("OOS", 30)):
            for label, candidate in (('Baseline', base), ('Variant', val)):
                if candidate[f"# of trades ({part})"] < minimum:
                    reasons.append(f"{label}: Insufficient {part} trades")
                if (candidate[f"Net profit ({part})"] <= 0 or
                        candidate[f"Profit factor ({part})"] <= 1 or
                        candidate[f"Ret/DD Ratio ({part})"] <= 0):
                    reasons.append(f"{label}: Non-positive development edge {part}")
            for metric in ("Net profit", "Profit factor", "Ret/DD Ratio"):
                if val[f"{metric} ({part})"] < base[f"{metric} ({part})"]:
                    reasons.append(f"Worse {metric} {part}")
        improvement = min(val[f"Ret/DD Ratio ({p})"] for p in ("IS", "OOS"))
        if improvement < min(base[f"Ret/DD Ratio ({p})"] for p in ("IS", "OOS")) * Decimal("1.05"):
            reasons.append("Less than 5% improvement in weakest development Ret/DD")
        decisions.append({"name": entry["name"], "decision": "REJECT" if reasons else "RESEARCH_PROMOTION_ONLY",
                          "reasons": reasons, "metrics": {k: str(v) for k, v in val.items()}})
    return {"schema": 1, "state": "NATIVE_COMPARISON_NOT_FUNDING_CERTIFICATION",
            "project": manifest["project"], "metrics_sha256": sha(metrics_path.read_bytes()),
            "native_evidence": evidence,
            "orders_diagnostic": diagnostic,
            "baseline": {k: str(v) for k, v in base.items()}, "decisions": decisions,
            "funding_verdict": "NO_EVALUABLE", "probada_para_fondeo": False}


def atomic_report(path, result):
    temporary = path.with_suffix('.json.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


FUNDING_WINDOW_PROFILE = {
    'id': 'topstep_50k_optional_dll_off_screen_2026-09-06',
    'checked_on': '2026-09-06', 'nominal': '50000', 'target': '3000',
    'eod_trailing_loss': '2000', 'best_day_fraction': '0.5',
    'minimum_trading_days': 2, 'max_micro_contracts': 50,
    'sources': [
        'https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit',
        'https://help.topstep.com/en/articles/8284208-consistency-at-topstep',
        'https://help.topstep.com/en/articles/8284197-trading-combine-parameters',
        'https://help.topstep.com/en/articles/8284206-when-and-what-products-can-i-trade',
    ],
    'scope': 'Historical diagnostic for one example exam; holidays and exact intraday replay still missing.',
}


def native_window_outcome(days, profile=FUNDING_WINDOW_PROFILE):
    """Screen serial, same-session native trades; never certify their equity path.

    Each day contains verified order dictionaries. Arithmetic boundary tests of
    this function are not strategy evidence. MAE cost treatment is deliberately
    conservative until the native excursion definition is independently checked.
    """
    capital = Decimal(profile['nominal'])
    balance = peak = capital
    loss = Decimal(profile['eod_trailing_loss'])
    floor = capital - loss
    best_day = Decimal(0)
    trade_days = trades = 0
    excursion_risk = False
    for number, orders in enumerate(days, 1):
        start_balance = balance
        trade_days += bool(orders)
        for order in orders:
            trades += 1
            if order.get('unsupported'):
                return {'outcome': 'UNSUPPORTED_NATIVE_WINDOW', 'day': number}
            pl, mae, fees, slippage, size = (Decimal(order[k]) for k in
                                             ('pl', 'mae', 'fees', 'slippage', 'size'))
            if (not all(v.is_finite() for v in (pl, mae, fees, slippage, size))
                    or min(mae, fees, slippage) < 0 or size <= 0):
                raise ValueError('Invalid native excursion, cost or size')
            if size != size.to_integral_value() or size > profile['max_micro_contracts']:
                return {'outcome': 'INCOMPATIBLE_CONTRACT_SIZE', 'day': number}
            # Costs may already contribute to MAE; this only flags possible risk.
            excursion_risk |= balance - mae - fees - slippage <= floor
            balance += pl
            if balance <= floor:
                return {'outcome': 'LOSS_LIMIT_AT_CLOSE', 'day': number,
                        'profit': str(balance - capital)}
        best_day = max(best_day, balance - start_balance)
        peak = max(peak, balance)
        floor = max(floor, min(capital, peak - loss))
        profit = balance - capital
        target = max(Decimal(profile['target']), best_day / Decimal(profile['best_day_fraction']))
        if profit >= target and trade_days >= profile['minimum_trading_days']:
            return {'outcome': ('TARGET_WITH_POSSIBLE_INTRATRADE_BREACH' if excursion_risk
                                else 'TARGET_REACHED_IN_NATIVE_SCREEN'),
                    'day': number, 'profit': str(profit), 'required_target': str(target),
                    'trading_days': trade_days}
    return {'outcome': ('NO_TRADES' if not trades else 'POSSIBLE_INTRATRADE_BREACH'
                       if excursion_risk else 'NO_TARGET_WITHIN_HORIZON'),
            'profit': str(balance - capital), 'trading_days': trade_days}


def native_trading_day(opened):
    """Assign even closed-hours orders to a weekday so they cannot disappear."""
    local = opened.astimezone(ZoneInfo('America/Chicago'))
    day = local.date() + timedelta(days=int(local.hour >= 17))
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def funding_windows(manifest_path, metrics_path):
    """Enumerate every complete weekday window, including inactivity.

    Sizes and entries are frozen from a continuous native history. In particular
    RiskFixedBalancePct depends on accumulated account balance: this screen is
    NOT a fresh-account simulation, a holdout test or an exam pass probability.
    """
    root = manifest_path.parent
    path = root / 'funding_windows.json'
    report = {'schema': 1, 'state': 'WINDOW_SCREEN_IN_PROGRESS',
              'probada_para_fondeo': False, 'funding_verdict': 'NO_EVALUABLE',
              'strategies': []}
    atomic_report(path, report)
    try:
        diagnostic = diagnose_orders(manifest_path, metrics_path)
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        proofs = {s['name']: s for s in diagnostic['strategies']}
        zone = ZoneInfo('America/Chicago')
        strategies = []
        for entry in manifest['entries']:
            with zipfile.ZipFile(root / 'retested' / entry['file']) as archive:
                settings_bytes = archive.read('lastSettings.xml')
            settings = ET.fromstring(settings_bytes)
            native_session_profile(settings)
            setup = unique(settings, 'Data/Setups/Setup')
            oos = unique(settings, 'Data/OutOfSample/Range')
            parse = lambda value: datetime.strptime(value, '%Y.%m.%d').replace(tzinfo=timezone.utc)
            start, finish = parse(setup.get('dateFrom')), parse(setup.get('dateTo')) + timedelta(days=1)
            split = parse(oos.get('dateFrom'))
            if not start < split < finish or parse(oos.get('dateTo')) + timedelta(days=1) != finish:
                raise ValueError('Only one final development OOS partition is supported')
            mm = unique(settings, "RiskMoneyManagement/MoneyManagement/Method[@use='true']")
            sizing = mm.get('type')
            rows, _ = partition_native_orders(csv.DictReader((root / (entry['name'] + '_orders.csv')).read_text(encoding='utf-8').splitlines()))
            parsed = []
            for row in rows:
                opened = datetime.fromtimestamp(int(row['open_time']) / 1000, timezone.utc)
                closed = datetime.fromtimestamp(int(row['close_time']) / 1000, timezone.utc)
                if closed < opened or opened < start or closed >= finish:
                    raise ValueError('Order interval outside declared data')
                parsed.append((opened, closed, row))
            parsed.sort(key=lambda item: (item[0], item[1], item[2]['ticket']))
            samples = {}
            for label, code, lower, upper in [('IS', '11', start, split), ('DEVELOPMENT_OOS', '21', split, finish)]:
                calendar = []
                day = lower.astimezone(zone).date()
                while day <= upper.astimezone(zone).date():
                    opening = datetime.combine(day - timedelta(days=1), daytime(17), zone)
                    closing = datetime.combine(day, daytime(15, 10), zone)
                    if day.weekday() < 5 and opening >= lower and closing < upper:
                        selected = [(a, b, r) for a, b, r in parsed
                                    if (a <= closing and b >= opening) or native_trading_day(a) == day]
                        orders, previous_close = [], None
                        for a, b, row in selected:
                            unsupported = (row['sample'] != code or a == b or a < opening or b > closing
                                           or bool(session_violations(a, b))
                                           or (previous_close is not None and a <= previous_close))
                            previous_close = max(previous_close or b, b)
                            orders.append({'pl': row['pl'], 'mae': row['mae'],
                                           'fees': str(abs(Decimal(row['commission_swap']))),
                                           'slippage': str(abs(Decimal(row['slippage_money']))),
                                           'size': row['size'], 'unsupported': unsupported})
                        calendar.append((day.isoformat(), orders))
                    day += timedelta(days=1)
                horizons = {}
                for horizon in range(1, 6):
                    counts, examples = {}, []
                    for index in range(max(0, len(calendar) - horizon + 1)):
                        window = calendar[index:index + horizon]
                        result = native_window_outcome([orders for _, orders in window])
                        outcome = result['outcome']
                        counts[outcome] = counts.get(outcome, 0) + 1
                        if outcome.startswith('TARGET_') and len(examples) < 3:
                            examples.append({'start': window[0][0], 'end': window[-1][0], **result})
                    horizons[str(horizon)] = {'all_windows': sum(counts.values()),
                                             'outcomes': counts, 'target_examples': examples}
                samples[label] = {'complete_weekday_sessions': len(calendar),
                                  'sessions_with_orders': sum(bool(o) for _, o in calendar),
                                  'horizons': horizons}
            strategies.append({'name': entry['name'], 'sizing_method': sizing,
                               'fresh_account_sizing': 'NOT_RETESTED',
                               'balance_dependent_sizing': sizing != 'FixedSize',
                               'orders_sha256': proofs[entry['name']]['orders_sha256'],
                               'settings_sha256': sha(settings_bytes), 'samples': samples})
        report.update(state='NATIVE_WINDOWS_SCREENED_NOT_EXAM_VALIDATION',
                      project=manifest['project'], strategies=strategies,
                      profile=FUNDING_WINDOW_PROFILE,
                      profile_sha256=sha(json.dumps(FUNDING_WINDOW_PROFILE, sort_keys=True).encode()),
                      manifest_sha256=sha(manifest_path.read_bytes()),
                      metrics_sha256=sha(metrics_path.read_bytes()),
                      engine_sha256=sha(Path(__file__).read_bytes()),
                      limitations=[
                          'Frozen native entries and sizes; fresh-account risk sizing and entry state require new retests.',
                          'Overlapping rolling windows are dependent observations, not estimated success probabilities.',
                          'Weekdays include holidays; exceptional closures and data completeness are not verified.',
                          'MAE cost inclusion unverified; conservative excursion flags are not exact intraday equity.',
                          'Current example rules applied retrospectively; development OOS is not an untouched holdout.',
                          'Zero-duration, overlapping and cross-session orders are unsupported where encountered.',
                          'No screen outcome authorizes promotion as a funding-proven strategy.',
                      ])
    except Exception as error:
        report.update(state='BLOCKED_INVALID_OR_UNSUPPORTED_EVIDENCE', strategies=[],
                      error=f'{type(error).__name__}: {error}')
        atomic_report(path, report)
        raise
    atomic_report(path, report)
    return report


def assess(manifest_path, metrics_path):
    """One post-retest decision; development improvement cannot bypass sessions.

    A fresh assessment first revokes any old readiness. Failed evidence and
    unsupported profiles remain blocked, with a durable reason for the caller.
    This does not claim to run an independent backtester or certify an exam.
    """
    root = manifest_path.parent
    report_path = root / 'assessment.json'
    report = {
        'schema': 1, 'state': 'ASSESSMENT_IN_PROGRESS',
        'utc': datetime.now(timezone.utc).isoformat(),
        'probada_para_fondeo': False, 'funding_verdict': 'NO_EVALUABLE',
        'target_days': [1, 5], 'next_stage_candidates': [], 'decisions': [],
    }
    atomic_report(report_path, report)
    try:
        comparison = compare(manifest_path, metrics_path)
        atomic_report(root / 'comparison.json', comparison)
        if not comparison['decisions'] or any(
                entry['decision'] not in ('REJECT', 'RESEARCH_PROMOTION_ONLY')
                for entry in comparison['decisions']):
            raise ValueError('Missing or unrecognized development verdict')
        eligible = any(entry['decision'] == 'RESEARCH_PROMOTION_ONLY'
                       for entry in comparison['decisions'])
        sessions = {}
        if eligible:
            screen = funding_session_screen(manifest_path, metrics_path)
            funding_windows(manifest_path, metrics_path)
            sessions = {entry['name']: entry for entry in screen['strategies']}
        decisions = []
        candidates = []
        for entry in comparison['decisions']:
            session = sessions.get(entry['name'])
            reasons = list(entry['reasons'])
            if entry['decision'] not in ('REJECT', 'RESEARCH_PROMOTION_ONLY'):
                raise ValueError('Unrecognized development verdict')
            if entry['decision'] == 'REJECT':
                decision = 'DROP_VARIANT'
                next_action = 'Preserve the failure; do not spend final validation data on this variant.'
            elif session['session_verdict'] == 'INCOMPATIBLE_RECORDED_SESSIONS':
                decision = 'NEEDS_SESSION_REPAIR'
                reasons.append('Recorded positions violate the selected exam regular sessions')
                next_action = 'Change execution/session rules and run a fresh bounded native comparison; do not trim past trades.'
            elif session['session_verdict'] == 'NO_REGULAR_SESSION_VIOLATION_FOUND':
                decision = 'READY_FOR_INDEPENDENT_VALIDATION'
                candidates.append(entry['name'])
                next_action = 'First verify source and contract identity of the market data; then validate exact rules on untouched data with intraday equity, complete calendar and a dated exam profile.'
            else:
                raise ValueError('Unrecognized session verdict')
            decisions.append({
                'name': entry['name'], 'decision': decision,
                'development_decision': entry['decision'], 'reasons': reasons,
                'incompatible_orders': session['incompatible_orders'] if session else None,
                'orders_sha256': session['orders_sha256'] if session else None,
                'session_gate': 'EVALUATED' if session else 'SKIPPED_DEVELOPMENT_REJECTED',
                'next_action': next_action,
                'probada_para_fondeo': False, 'funding_verdict': 'NO_EVALUABLE',
            })
        report.update({
            'state': 'ASSESSED_NOT_FUNDING_CERTIFIED', 'project': comparison['project'],
            'manifest_sha256': sha(manifest_path.read_bytes()),
            'metrics_sha256': comparison['metrics_sha256'],
            'comparison_sha256': sha((root / 'comparison.json').read_bytes()),
            'session_screen_sha256': sha((root / 'funding_session_screen.json').read_bytes()) if eligible else None,
            'funding_windows_sha256': sha((root / 'funding_windows.json').read_bytes()) if eligible else None,
            'funding_screen_state': 'SCREENED_NOT_CERTIFIED' if eligible else 'SKIPPED_DEVELOPMENT_REJECTED',
            'engine_sha256': sha(Path(__file__).read_bytes()),
            'decisions': decisions, 'next_stage_candidates': candidates,
            'missing_exam_evidence': [
                'Verified market-data provenance bound to the tested dataset: provider, actual traded instrument, timezone, file hashes and futures contract/roll policy. A proxy imported under a futures symbol does not establish futures performance.',
                'Dated complete rules for the chosen firm and exam, including allowed minimum trading days.',
                'Native-equivalent independent intraday equity, costs and contract sizing.',
                'Verified holidays and exceptional early closes.',
                'Untouched final data and rolling 1-5-day outcomes including failed attempts.',
            ],
        })
    except Exception as error:
        report.update(state='BLOCKED_INVALID_OR_UNSUPPORTED_EVIDENCE',
                      error=f'{type(error).__name__}: {error}')
        atomic_report(report_path, report)
        raise
    atomic_report(report_path, report)
    return report


def assess_fresh_attempt(manifest_path, metrics_path):
    """Screen one native fresh-account retest without promoting a strategy."""
    root = manifest_path.parent
    path = root / 'fresh_attempt_assessment.json'
    report = {'state': 'CHECKING_NATIVE_EVIDENCE', 'strategies': [],
              'probada_para_fondeo': False, 'funding_verdict': 'NO_EVALUABLE',
              'next_stage_candidates': []}
    atomic_report(path, report)
    try:
        diagnostic = diagnose_orders(manifest_path, metrics_path)
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        spec = manifest['fresh_attempt']
        start = datetime.strptime(spec['start'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end = datetime.strptime(spec['end'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        if start.weekday() != 0 or end - start != timedelta(days=4):
            raise ValueError('Unsupported fresh-account window')
        if Decimal(spec['initial_capital']) != Decimal(FUNDING_WINDOW_PROFILE['nominal']):
            raise ValueError('Initial capital differs from the diagnostic exam profile')
        proofs = {s['name']: s for s in diagnostic['strategies']}
        strategies = []
        for entry in manifest['entries']:
            with zipfile.ZipFile(root / 'retested' / entry['file']) as archive:
                settings = ET.fromstring(archive.read('lastSettings.xml'))
                rules = ET.fromstring(archive.read('strategy_Portfolio.xml'))
            native_session_profile(settings)
            capital = unique(settings, 'RiskMoneyManagement/MoneyManagement/InitialCapital').text
            if Decimal(capital) != Decimal(spec['initial_capital']):
                raise ValueError('Native initial capital differs from planned reset')
            for xpath in ('Data/Setups/Setup', 'Data/OutOfSample/Range'):
                node = unique(settings, xpath)
                expected_start = spec.get('warmup_start', spec['start']) if xpath.endswith('Setup') else spec['start']
                if (node.get('dateFrom') != expected_start.replace('-', '.') or
                        node.get('dateTo') != end.strftime('%Y.%m.%d')):
                    raise ValueError('Native dates differ from the fresh-account window')
            rows, _ = partition_native_orders(csv.DictReader((root / (entry['name'] + '_orders.csv')).read_text(encoding='utf-8').splitlines()))
            rows.sort(key=lambda r: (int(r['open_time']), int(r['close_time']), r['ticket']))
            days = [[] for _ in range(5)]
            previous_close = None
            for row in rows:
                opened = datetime.fromtimestamp(int(row['open_time']) / 1000, timezone.utc)
                closed = datetime.fromtimestamp(int(row['close_time']) / 1000, timezone.utc)
                if opened < start or closed >= end + timedelta(days=1) or closed < opened:
                    raise ValueError('Native orders escape the fresh-account data range')
                day = native_trading_day(opened)
                index = (day - start.date()).days
                if not 0 <= index < 5:
                    raise ValueError('Native order belongs to a session outside the diagnostic')
                unsupported = (row['sample'] != '21' or opened == closed or
                               bool(session_violations(opened, closed)) or
                               native_trading_day(closed) != day or
                               (previous_close is not None and opened <= previous_close))
                previous_close = max(previous_close or closed, closed)
                days[index].append({'pl': row['pl'], 'mae': row['mae'], 'size': row['size'],
                                    'fees': str(abs(Decimal(row['commission_swap']))),
                                    'slippage': str(abs(Decimal(row['slippage_money']))),
                                    'unsupported': unsupported})
            # This is a lower bound from explicit extrema periods, not a complete
            # warmup calculator (recursive indicators can require more history).
            periods = [int(p.text) for item in rules.iter('Item')
                       if item.get('key') in ('Highest', 'Lowest')
                       for p in item.findall('Param')
                       if p.get('key') == '#Period#' and (p.text or '').isdigit()]
            timeframe = unique(settings, 'Data/Setups/Setup/Chart').get('timeframe', '')
            minutes = (int(timeframe[1:]) * (60 if timeframe.startswith('H') else 1)
                       if timeframe[:1] in ('H', 'M') and timeframe[1:].isdigit() else None)
            upper_bound = int((end - start + timedelta(days=1)).total_seconds() / 60 / minutes) if minutes else None
            initialization = {
                'state': 'PRIOR_INDICATOR_HISTORY_NOT_VERIFIED',
                'observed_extrema_period_lower_bound': max(periods, default=0),
                'timeframe': timeframe, 'window_bars_upper_bound': upper_bound,
                'window_alone_too_short': upper_bound is not None and max(periods, default=0) > upper_bound,
                'interpretation': 'No inference about strategy quality or fresh-account viability without verified warmup.'}
            if spec.get('warmup_start'):
                initialization.update(
                    state='NATIVE_HISTORY_CONFIGURED_INITIALIZATION_NOT_VERIFIED',
                    history_start=spec['warmup_start'],
                    orders_before_exam=0,
                    entry_gate_runtime=('OBSERVED_IN_WINDOW_ORDERS' if rows else 'UNVERIFIED_NO_ORDERS'),
                    interpretation=('Native orders occur inside the requested window with prior history configured; full indicator convergence remains unverified.' if rows else
                                    'Native settings request prior history; neither configuration nor zero orders proves indicator initialization or entry-gate behavior.'))
            strategies.append({'name': entry['name'], 'initial_capital': capital,
                               'initialization': initialization,
                               'fresh_account_sizing': 'NATIVE_RETEST_FROM_INITIAL_CAPITAL',
                               'orders_sha256': proofs[entry['name']]['orders_sha256'],
                               'trades': len(rows), 'sizes': proofs[entry['name']]['sizes'],
                               'net_profit': str(sum((Decimal(r['pl']) for r in rows), Decimal(0))),
                               'daily_net_profit': [str(sum((Decimal(r['pl']) for r in day), Decimal(0))) for day in days],
                               'screen': native_window_outcome(days)})
        observed_execution = bool(spec.get('warmup_start')) and all(s['trades'] for s in strategies) and bool(strategies)
        report.update(state=('NATIVE_WINDOW_EXECUTED_FUNDING_UNVERIFIED' if observed_execution else
                             'BLOCKED_UNVERIFIED_FRESH_ACCOUNT_EXECUTION'
                             if spec.get('warmup_start') and not any(s['trades'] for s in strategies)
                             else 'BLOCKED_UNVERIFIED_INDICATOR_INITIALIZATION'),
                      project=manifest['project'], window=spec, strategies=strategies,
                      profile=FUNDING_WINDOW_PROFILE,
                      manifest_sha256=sha(manifest_path.read_bytes()),
                      metrics_sha256=sha(metrics_path.read_bytes()),
                      engine_sha256=sha(Path(__file__).read_bytes()),
                      limitations=[
                          ('Native execution is observed, but a selected development week cannot establish funding suitability.' if observed_execution else
                           'An empty native retest does not distinguish no strategy signals from an invalid entry gate or incomplete indicator initialization.'),
                          'Known development window selected for diagnosis; not held-out evidence or a success probability.',
                          'Monday UTC entry gate omits the preceding Sunday evening; indicator convergence requires separate validation.',
                          'Exact intraday equity, data provenance, exceptional closures and complete exam rules remain unverified.',
                          'MAE cost inclusion is unknown; excursion flags are conservative screening only.',
                          'All variants retain their prior development rejection; this diagnostic cannot promote them.'])
    except Exception as error:
        report.update(state='BLOCKED_INVALID_OR_UNSUPPORTED_EVIDENCE', error=f'{type(error).__name__}: {error}')
        atomic_report(path, report)
        raise
    atomic_report(path, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    for arg in ("source", "template", "output"):
        prep.add_argument("--" + arg, type=Path, required=True)
    for arg in ("remote-dir", "project"):
        prep.add_argument("--" + arg, required=True)
    for arg in ('gid', 'expected', 'step'):
        prep.add_argument('--' + arg)
    prep.add_argument('--native-variants', nargs='+', type=Path, help='One or two distinct native variants; validated before preparing files')
    prep.add_argument('--funding-profile', choices=('topstep',), help='Reject unlisted products before preparing this exam-specific experiment; not certification')
    prep.add_argument('--integer-contracts', action='store_true')
    prep.add_argument('--precision', type=int, choices=(1, 2), default=2)
    prep.add_argument('--percent-pt-original', help='Explicitly reviewed percent PT to replace only in variants; control remains original')
    prep.add_argument('--conservative-utc-session', action='store_true', help='Test all comparison strategies in conservative UTC 00:00-19:00 hours; requires actual-order verification')
    prep.add_argument('--session-end-utc', type=int, default=19, help='Explicit end hour (1-19) for the session experiment; verify native bar-close behavior')
    run = sub.add_parser('run')
    run.add_argument('--manifest', type=Path, required=True)
    reviewed = sub.add_parser('run-reviewed', help='Load and execute one prepared recipe once; persist uncertain failures')
    reviewed.add_argument('--manifest', type=Path, required=True)
    fresh = sub.add_parser('prepare-fresh-attempt', help='Repeat one development week with initial capital; no promotion')
    fresh.add_argument('--parent-manifest', type=Path, required=True)
    fresh.add_argument('--output', type=Path, required=True)
    fresh.add_argument('--warmup-start', help='Load earlier native history and gate entries to the diagnostic week')
    for arg in ('remote-dir', 'project', 'start', 'end'):
        fresh.add_argument('--' + arg, required=True)
    fresh_assessment = sub.add_parser('assess-fresh-attempt')
    fresh_assessment.add_argument('--manifest', type=Path, required=True)
    fresh_assessment.add_argument('--metrics', type=Path, required=True)
    comp = sub.add_parser("compare")
    comp.add_argument("--manifest", type=Path, required=True)
    comp.add_argument("--metrics", type=Path, required=True)
    orders = sub.add_parser('orders')
    orders.add_argument('--manifest', type=Path, required=True)
    diag = sub.add_parser('diagnose')
    diag.add_argument('--manifest', type=Path, required=True)
    diag.add_argument('--metrics', type=Path, required=True)
    screen = sub.add_parser('funding-screen', help='Explicit example: MYM/MNQ Topstep regular sessions only')
    screen.add_argument('--manifest', type=Path, required=True)
    screen.add_argument('--metrics', type=Path, required=True)
    assessment = sub.add_parser('assess', help='Combine verified development results and session gate; no exam certification')
    assessment.add_argument('--manifest', type=Path, required=True)
    assessment.add_argument('--metrics', type=Path, required=True)
    windows = sub.add_parser('funding-windows', help='Historical 1-5-day screen with frozen native sizes; not exam certification')
    windows.add_argument('--manifest', type=Path, required=True)
    windows.add_argument('--metrics', type=Path, required=True)
    product = sub.add_parser('funding-product', help='Dated product-list check of one native SQX file; not certification')
    product.add_argument('--source', type=Path, required=True)
    product.add_argument('--output', type=Path, required=True)
    product.add_argument('--profile', choices=('topstep',), default='topstep')
    args = vars(parser.parse_args())
    action = args.pop("action")
    if action == 'prepare':
        result = prepare(**args)
    elif action == 'funding-product':
        result = funding_product_check(**args)
    elif action == 'prepare-fresh-attempt':
        result = prepare_fresh_attempt(**args)
    elif action == 'assess-fresh-attempt':
        result = assess_fresh_attempt(args['manifest'], args['metrics'])
    elif action == 'run':
        result = run_native(args['manifest'])
    elif action == 'run-reviewed':
        result = run_reviewed(args['manifest'])
    elif action == 'orders':
        result = export_orders(args['manifest'])
    elif action == 'diagnose':
        result = diagnose_orders(args['manifest'], args['metrics'])
    elif action == 'funding-screen':
        result = funding_session_screen(args['manifest'], args['metrics'])
    elif action == 'assess':
        result = assess(args['manifest'], args['metrics'])
    elif action == 'funding-windows':
        result = funding_windows(args['manifest'], args['metrics'])
    else:
        result = compare(args['manifest'], args['metrics'])
    print(json.dumps(result, indent=2))
