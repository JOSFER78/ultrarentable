"""Stage at most five native SQX candidates; never certify or bulk-export.

Run on the SQX VPS, against a completed, quiescent Results bank. The CSV
contains metrics only. OOS used here is development data, not a final holdout.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def number(row, key):
    value = float(row[key])
    if not math.isfinite(value):
        raise ValueError(key)
    return value


def select(rows):
    eligible = []
    for row in rows:
        try:
            if not re.fullmatch(r"Strategy [0-9.]+(?:\([0-9]+\))?", row['Strategy Name']):
                continue
            if any(number(row, '# of trades (' + part + ')') < minimum
                   for part, minimum in [('IS', 100), ('OOS', 30)]):
                continue
            if any(number(row, metric + ' (' + part + ')') < minimum
                   for part in ['IS', 'OOS']
                   for metric, minimum in [('Profit factor', 1.2), ('Ret/DD Ratio', 1.0)]):
                continue
            if any(number(row, 'Net profit (' + part + ')') <= 0 for part in ['IS', 'OOS']):
                continue
            eligible.append(row)
        except (ValueError, KeyError):
            continue
    eligible.sort(key=lambda row: (
        -min(number(row, 'Ret/DD Ratio (' + p + ')') for p in ['IS', 'OOS']),
        -min(number(row, 'Profit factor (' + p + ')') for p in ['IS', 'OOS']),
        row['Strategy Name']))
    picked, seen = [], set()
    for row in eligible:
        # Suppress identical reported performance. This is not correlation testing.
        fingerprint = tuple(row[k] for k in sorted(row)
                            if k.startswith(('# of trades', 'Net profit', 'Drawdown', 'Profit factor')))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        picked.append(row)
        if len(picked) == 5:
            break
    return eligible, picked


def stage(project, metrics, output, endpoint):
    if not re.fullmatch(r'FONDEO_[A-Z0-9]+_[A-Z0-9]+', project):
        raise ValueError('Unexpected project name')
    output = output.resolve()
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(output)):
        raise ValueError('Output path must be safe for native CLI')
    output.mkdir(parents=True, exist_ok=False)
    raw = metrics.read_bytes()
    rows = list(csv.DictReader(raw.decode('utf-8-sig').splitlines(), delimiter=';'))
    eligible, picked = select(rows)
    manifest = dict(schema=1, project=project, created=dt.datetime.now(dt.UTC).isoformat(),
                    metrics_path=str(metrics), metrics_sha256=sha(raw), rows=len(rows),
                    eligible=len(eligible), state='STAGING', probada=False,
                    policy={'max_files': 5, 'min_trades_IS': 100, 'min_trades_OOS': 30,
                            'min_profit_factor_both': 1.2, 'min_ret_dd_both': 1.0,
                            'net_profit_both': '>0', 'rank': 'minimum IS/OOS RetDD; then minimum PF'},
                    limitations=['Preliminary ranking only; no robustness certification',
                                 'OOS used for selection is no longer a final holdout',
                                 'Reported metrics deduplication is not correlation analysis',
                                 'Data provenance, executable sizing and replay remain to verify'],
                    files=[])
    mp = output / 'manifest.json'
    mp.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    if picked:
        names = ','.join(row['Strategy Name'] for row in picked)
        command = output / 'save.commands'
        command.write_text(f'-databank action=save project={project} name=Results folder={output} strategies="{names}"\n', encoding='utf-8')
        # Direct /call tokenization loses spaces in strategy names. Native -run
        # parses command-file quoting correctly on SQX 144.2953.
        url = endpoint + '?cmd=' + ('-run file=' + str(command)).replace(' ', '%20')
        with urllib.request.urlopen(url, timeout=120) as response:
            (output / 'cli_response.txt').write_bytes(response.read())
        expected = {row['Strategy Name'] + '.sqx' for row in picked}
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if {p.name for p in output.glob('*.sqx')} == expected:
                break
            time.sleep(1)
        if {p.name for p in output.glob('*.sqx')} != expected:
            raise RuntimeError('Native export did not produce exactly the selected names')
        rules_seen = set()
        for row in picked:
            p = output / (row['Strategy Name'] + '.sqx')
            with zipfile.ZipFile(p) as archive:
                if archive.testzip() is not None:
                    raise ValueError('Damaged SQX')
                settings = ET.fromstring(archive.read('settings.xml'))
                if settings.attrib.get('ResultName') != row['Strategy Name']:
                    raise ValueError('Export identity mismatch')
                strategy = ET.fromstring(archive.read('strategy_Portfolio.xml')).find('Strategy')
                if strategy is None or len(strategy) == 0:
                    raise ValueError('Missing strategy rules')
                ET.fromstring(archive.read('lastSettings.xml'))
                orders = archive.read('orders.bin')
                if not orders:
                    raise ValueError('Missing saved orders')
                rules_hash = sha(ET.tostring(strategy))
                duplicate = rules_hash in rules_seen
                rules_seen.add(rules_hash)
                manifest['files'].append(dict(name=row['Strategy Name'], path=str(p),
                    sha256=sha(p.read_bytes()), bytes=p.stat().st_size, rules_sha256=rules_hash,
                    duplicate_rules=duplicate, orders_bytes=len(orders), metrics=row))
    manifest['state'] = 'PRESELECCION_NO_VALIDADA' if picked else 'SIN_CANDIDATAS'
    mp.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--metrics', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--endpoint', default='http://127.0.0.1:5051/call')
    args = parser.parse_args()
    result = stage(args.project, args.metrics, args.output, args.endpoint)
    print(json.dumps({k: result[k] for k in ['state', 'rows', 'eligible', 'files']}, indent=2))
