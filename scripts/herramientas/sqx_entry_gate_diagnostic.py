"""Three native controls from one real SQX strategy; never a funding verdict."""
import copy
import csv
from datetime import date
import json
from pathlib import Path
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

import sqx_native_improvement as engine


def main():
    parent, template, output = map(Path, sys.argv[1:4])
    project = sys.argv[4]
    engine.native_evidence(parent)
    engine.native_evidence(template)
    base_manifest = json.loads(parent.read_text())
    base = next(e for e in base_manifest['entries'] if e['name'].endswith('_BASE'))
    source = parent.parent / 'input' / base['file']
    assert engine.sha(source.read_bytes()) == base['sha256']
    with zipfile.ZipFile(source) as archive:
        original = {n: archive.read(n) for n in archive.namelist()}
    with zipfile.ZipFile(template.parent / 'project.cfx') as archive:
        config_files = {n: archive.read(n) for n in archive.namelist()}
    config = ET.fromstring(config_files['config.xml'])
    config.set('name', project)
    config_files['config.xml'] = engine.xml(config)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'input').mkdir()
    manifest = copy.deepcopy(base_manifest)
    manifest.update(project=project, entries=[], state='DIAGNOSTIC_NOT_FUNDING_EVIDENCE',
                    hypothesis='Same BASE: unchanged, broad date gate, five-day gate',
                    source_input_sha256=base['sha256'])
    bounds = [('CONTROL', None), ('BROAD', (date(1900, 1, 1), date(2100, 12, 31))),
              ('FIVE_DAYS', (date(2026, 5, 4), date(2026, 5, 8)))]
    if len(sys.argv) > 5 and sys.argv[5] == 'isolate-bounds':
        bounds = [('CONTROL', None), ('LOWER', (date(2026, 5, 4), date(2100, 12, 31))),
                  ('UPPER', (date(1900, 1, 1), date(2026, 5, 8)))]
        manifest['hypothesis'] = 'Same BASE: unchanged, lower date bound, upper date bound'
    if len(sys.argv) > 5 and sys.argv[5] == 'date-semantics':
        bounds = [('CONTROL', None), ('MONTH_MINUS_ONE', (date(2026, 4, 4), date(2026, 4, 8))),
                  ('BAR_DATE', (date(2026, 5, 4), date(2026, 5, 8)))]
        manifest['hypothesis'] = 'Same BASE: unchanged, previous-month bound, explicit bar date'
    for label, dates in bounds:
        payload = dict(original)
        name = base['name'] + '_' + label
        settings = ET.fromstring(payload['settings.xml'])
        settings.set('ResultName', name)
        payload['settings.xml'] = engine.xml(settings)
        rules = ET.fromstring(payload['strategy_Portfolio.xml'])
        if dates:
            rules = engine.gate_entry_dates(rules, *dates, date_source='CurrentDate')
            if label == 'BAR_DATE':
                for item in rules.findall('.//Item[@key="CurrentDate"]'):
                    item.set('key', 'BarDate')
                    ET.SubElement(item, 'Param', key='#Chart#', type='data', controlType='dataVar').text = '0'
                    ET.SubElement(item, 'Param', key='#Shift#', type='int', controlType='jspinnerVar').text = '0'
            payload['strategy_Portfolio.xml'] = engine.xml(rules)
        entry = {'name': name, 'file': name + '.sqx', 'arm': label,
                 'gate_dates': [d.isoformat() for d in dates] if dates else None,
                 'rules_sha256': engine.sha(engine.canonical(rules).encode())}
        with zipfile.ZipFile(output / 'input' / entry['file'], 'w', zipfile.ZIP_DEFLATED) as archive:
            for n, data in payload.items():
                archive.writestr(n, data)
        entry['sha256'] = engine.sha((output / 'input' / entry['file']).read_bytes())
        manifest['entries'].append(entry)
    with zipfile.ZipFile(output / 'project.cfx', 'w', zipfile.ZIP_DEFLATED) as archive:
        for n, data in config_files.items():
            archive.writestr(n, data)
    manifest['config_sha256'] = engine.sha((output / 'project.cfx').read_bytes())
    engine.atomic_report(output / 'manifest.json', manifest)
    names = ','.join(e['name'] for e in manifest['entries'])
    (output / 'import.cli').write_text(f'-databank action=load project={project} name=Input folder={output}/input strategies="{names}"\n')
    (output / 'collect.cli').write_text(
        f'-databank action=export project={project} name=RetestResults file={output}/retest.csv\n'
        f'-databank action=save project={project} name=RetestResults folder={output}/retested\n')
    cmd = f'-project action=loadconfig name={project} file={output}/project.cfx'
    with urllib.request.urlopen('http://127.0.0.1:5050/call?cmd=' + cmd.replace(' ', '%20'), timeout=30) as response:
        (output / 'load_response.txt').write_text(response.read().decode())
    time.sleep(2)
    evidence = engine.run_native(output / 'manifest.json', evidence_only=True)
    results = []
    for entry in manifest['entries']:
        orders_file = output / (entry['name'] + '_orders.csv')
        rows = list(csv.DictReader(orders_file.open()))
        results.append({'arm': entry['arm'], 'order_rows': len(rows),
                        'orders_sha256': engine.sha(orders_file.read_bytes())})
    report = {'state': 'DIAGNOSTIC_COMPLETE', 'probada': False,
              'funding_verdict': 'NO_EVALUABLE', 'results': results, 'evidence': evidence}
    engine.atomic_report(output / 'diagnostic_report.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
