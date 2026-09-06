"""One bounded native Improver job. Keeps entries, exports at most two variants.

Run on the SQX VPS. Search/OOS metrics are development evidence, never funding
certification. A separate native retest compares exported rules with the control.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_variants(rows, limit=2):
    if limit not in (1, 2):
        raise ValueError('Export limit must be one or two')
    ranked = []
    for row in rows:
        if not re.fullmatch(r'[A-Za-z0-9 ._()-]{1,120}', row.get('Strategy Name', '')):
            continue
        try:
            values = {(metric, part): float(row[f'{metric} ({part})'])
                      for part in ('IS', 'OOS')
                      for metric in ('# of trades', 'Profit factor', 'Ret/DD Ratio', 'Net profit')}
            if not all(math.isfinite(v) for v in values.values()):
                continue
            if values['# of trades', 'IS'] < 100 or values['# of trades', 'OOS'] < 30:
                continue
            if any(values['Profit factor', p] < 1.2 or values['Ret/DD Ratio', p] < 1
                   or values['Net profit', p] <= 0 for p in ('IS', 'OOS')):
                continue
            ranked.append((min(values['Ret/DD Ratio', p] for p in ('IS', 'OOS')),
                           min(values['Profit factor', p] for p in ('IS', 'OOS')), row))
        except (KeyError, ValueError):
            continue
    ranked.sort(key=lambda x: (-x[0], -x[1], x[2]['Strategy Name']))
    picked, seen = [], set()
    for _, _, row in ranked:
        key = tuple(row[k] for k in sorted(row)
                    if k.startswith(('# of trades', 'Net profit', 'Drawdown', 'Profit factor')))
        if key not in seen:
            seen.add(key)
            picked.append(row)
        if len(picked) == limit:
            break
    return picked


def run(source, template, output, project, builder, seconds=180):
    if not re.fullmatch(r'UR_IMPROVE_SEARCH_[A-Z0-9_]+', project):
        raise ValueError('Dedicated search project required')
    if not re.fullmatch(r'/opt/SQX-headless/import/[A-Za-z0-9_/-]+', str(output)) or '..' in str(output):
        raise ValueError('Unsafe job directory')
    if not 30 <= seconds <= 600:
        raise ValueError('Deadline must be 30..600 seconds')
    output.mkdir(parents=True, exist_ok=False)
    # Load an immutable local copy, so future selective-stage changes cannot
    # alter the input between configuration and native databank import.
    original_source = source
    (output / 'source').mkdir()
    source = output / 'source' / original_source.name
    source.write_bytes(original_source.read_bytes())
    with zipfile.ZipFile(source) as z:
        name = ET.fromstring(z.read('settings.xml')).get('ResultName')
    if not re.fullmatch(r'Strategy [0-9.]+(?:\([0-9]+\))?', name or ''):
        raise ValueError('Unexpected source name')
    state = dict(project=project, source=str(source), source_sha256=digest(source),
                 state='PREPARING', funding_verdict='NO_EVALUABLE', exported=[], max_exports=2)
    def save():
        tmp = output / 'state.tmp'
        tmp.write_text(json.dumps(state, indent=2), encoding='utf-8')
        tmp.replace(output / 'state.json')
    def call(cmd):
        with urllib.request.urlopen('http://127.0.0.1:5050/call?cmd=' + cmd.replace(' ', '%20'), timeout=30) as r:
            response = r.read().decode()
        with (output / 'native_calls.log').open('a', encoding='utf-8') as f:
            f.write(cmd + '\n' + response + '\n')
        return response
    def filecall(filename, commands):
        p = output / filename
        p.write_text(commands + '\n', encoding='utf-8')
        return call('-run file=' + str(p))
    def count():
        raw = call(f'-databank action=count project={project} name=Results')
        match = re.search(r'Records:\s*(\d+)', raw)
        if not match:
            raise RuntimeError('Unrecognized bank count: ' + raw)
        return int(match[1])
    save()
    subprocess.run(['python3', str(builder), '--source', str(template), '--target', str(output/'project.cfx'),
                    '--manifest', str(output/'project_manifest.json'), '--project', project,
                    '--candidate', name, '--candidate-file', str(source)], check=True, stdout=subprocess.DEVNULL)
    listing = call('-project action=list')
    if project in listing:
        raise RuntimeError('Project already exists; reconcile, do not rerun')
    loaded = call(f'-project action=loadconfig name={project} file={output}/project.cfx')
    if f"Project loaded '{project}'" not in loaded:
        raise RuntimeError('Native project import not confirmed: ' + loaded)
    filecall('import.cli', f'-databank action=load project={project} name="Strategies to improve" folder={source.parent} strategies="{name}"')
    deadline = time.monotonic() + 40
    while True:
        response = filecall('count_input.cli', f'-databank action=count project={project} name="Strategies to improve"')
        if re.search(r'Records:\s*1\b', response):
            break
        if time.monotonic() >= deadline:
            raise RuntimeError('One input strategy not confirmed')
        time.sleep(2)
    state.update(state='START_REQUESTED', started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    save()
    try:
        response = call(f'-project action=start name={project}')
        if any(s in response.lower() for s in ('cannot start', 'no se puede iniciar', 'unresolved', 'could not start')):
            raise RuntimeError('Native start refused: ' + response)
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            state.update(state='SEARCHING', bank_count=count())
            save()
            project_logs = list((Path('/opt/SQX-headless/user/projects')/project/'log').glob('global_log_*.log'))
            progress = '\n'.join(p.read_text(errors='replace') for p in project_logs)
            if any(token in progress for token in ('TAREA TERMINADA', 'TASK FINISHED', 'Task finished')):
                break
            if state['bank_count'] >= 12:
                break
            time.sleep(5)
    finally:
        state['stop_response'] = call(f'-project action=stop name={project}')
        state['state'] = 'STOP_REQUESTED'
        save()
    # A completed project log is needed in addition to a returned stop request.
    time.sleep(3)
    logs = list((Path('/opt/SQX-headless/user/projects')/project/'log').glob('global_log_*.log'))
    log = '\n'.join(p.read_text(errors='replace') for p in logs)
    (output/'native_search.log').write_text(log, encoding='utf-8')
    if not any(token in log for token in ('TAREA TERMINADA', 'TASK FINISHED', 'Task finished')):
        state['state'] = 'NEEDS_STOP_RECONCILIATION'
        save()
        raise RuntimeError('No native task completion evidence; export blocked')
    filecall('metrics.cli', f'-databank action=export project={project} name=Results file={output}/metrics.csv')
    deadline = time.monotonic() + 30
    while not (output/'metrics.csv').exists() and time.monotonic() < deadline:
        time.sleep(1)
    rows = list(csv.DictReader((output/'metrics.csv').read_text(encoding='utf-8-sig').splitlines(), delimiter=';'))
    picked = select_variants(rows)
    if picked:
        names = ','.join(r['Strategy Name'] for r in picked)
        filecall('export.cli', f'-databank action=save project={project} name=Results folder={output}/selected strategies="{names}"')
        expected = {r['Strategy Name']+'.sqx' for r in picked}
        deadline = time.monotonic() + 30
        while {p.name for p in (output/'selected').glob('*.sqx')} != expected and time.monotonic() < deadline:
            time.sleep(1)
        if {p.name for p in (output/'selected').glob('*.sqx')} != expected:
            raise RuntimeError('Native export differs from exact selection')
        for r in picked:
            p = output/'selected'/(r['Strategy Name']+'.sqx')
            with zipfile.ZipFile(p) as z:
                if z.testzip() or ET.fromstring(z.read('settings.xml')).get('ResultName') != r['Strategy Name']:
                    raise RuntimeError('Invalid exported strategy')
            state['exported'].append(dict(path=str(p), sha256=digest(p), metrics=r))
    state.update(state='VARIANTS_REQUIRE_CONTROLLED_RETEST' if picked else 'NO_VARIANTS_PASS_DEVELOPMENT_FILTER',
                 bank_count=count(), metrics_sha256=digest(output/'metrics.csv'))
    save()
    return state


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'template', 'output', 'builder'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--project', required=True)
    p.add_argument('--seconds', type=int, default=180)
    args = p.parse_args()
    print(json.dumps(run(**vars(args)), indent=2))
