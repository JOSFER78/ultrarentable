"""Controlled offline migration; backup first, change only PTPercent in 30 projects.

Run on the VPS only after the runner has parked and SQX is fully stopped.
Does not start/stop services, touch databanks, or load duplicate projects.
"""
import datetime as dt
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

BASE = Path('/opt/SQX-headless/import/fondeo')
EVIDENCE = BASE / 'pt_migration_20260906'


def revised(raw):
    source = zipfile.ZipFile(io.BytesIO(raw))
    names = source.namelist()
    if len(names) != len(set(names)) or names.count('Build-Task1.xml') != 1:
        raise ValueError('Ambiguous task archive')
    task = source.read('Build-Task1.xml')
    pattern = rb'<PTPercent>(true|false)</PTPercent>'
    matches = re.findall(pattern, task)
    if len(matches) != 1:
        raise ValueError('Expected exactly one PTPercent setting')
    updated = re.sub(pattern, b'<PTPercent>false</PTPercent>', task)
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w') as target:
        target.comment = source.comment
        for member in source.infolist():
            target.writestr(copy.copy(member), updated if member.filename == 'Build-Task1.xml'
                            else source.read(member.filename))
    output = result.getvalue()
    with zipfile.ZipFile(io.BytesIO(output)) as check:
        assert check.namelist() == names
        assert check.testzip() is None
        for name in names:
            assert check.read(name) == (updated if name == 'Build-Task1.xml' else source.read(name))
    return output, matches[0].decode()


def atomic(path, data):
    temporary = path.with_name(path.name + '.pt-migration.tmp')
    if temporary.exists():
        raise RuntimeError(f'Unresolved temporary file: {temporary}')
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    shutil.copystat(path, temporary)
    os.replace(temporary, path)


def main():
    for unit in ['sqx-headless', 'm1-runner', 'sqx-improvement', 'ultrarentable-supervisor']:
        status = subprocess.run(['systemctl', 'is-active', unit], capture_output=True, text=True).stdout.strip()
        assert status == 'inactive', (unit, status)
    state = json.loads((BASE / 'estado.json').read_text())
    assert state.get('celda_en_curso') is None and not state.get('cierre_pendiente')
    assert (BASE / 'pause_after_current_cell.request').is_file()
    manifest_path = BASE / 'manifiesto.json'
    manifest = json.loads(manifest_path.read_text())
    entries = manifest['proyectos']
    names = [entry['proyecto'] for entry in entries]
    assert len(names) == 30 and len(set(names)) == 30
    backup = EVIDENCE / 'backup'
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(manifest_path, backup / 'manifiesto.json')
    work, rows = [], []
    for entry in entries:
        name = entry['proyecto']
        assert re.fullmatch(r'FONDEO_(MES|MNQ|MYM|MGC|MCL|M6E)_(M1|M5|M15|H1|H4)', name)
        for kind, path in [('loaded', Path('/opt/SQX-headless/user/projects') / name / 'project.cfx'),
                           ('fallback', BASE / (name + '.cfx'))]:
            raw = path.read_bytes()
            output, old = revised(raw)
            saved = backup / (name + '_' + kind + '.cfx')
            shutil.copy2(path, saved)
            assert saved.read_bytes() == raw
            work.append((path, raw, output))
            row = dict(project=name, kind=kind, path=str(path), before=old, after='false',
                       sha256_before=hashlib.sha256(raw).hexdigest(),
                       sha256_after=hashlib.sha256(output).hexdigest())
            rows.append(row)
            if kind == 'fallback':
                entry['sha256'] = row['sha256_after']
    # All archives and backups are verified before the first mutation.
    try:
        for path, raw, output in work:
            assert path.read_bytes() == raw
            atomic(path, output)
        manifest['search_recipe'] = 'preserved_initial_protection_no_percent_pt_v2'
        manifest['loaded_config_migration'] = str(EVIDENCE)
        atomic(manifest_path, (json.dumps(manifest, indent=2) + '\n').encode())
        for path, _, output in work:
            assert path.read_bytes() == output
    except BaseException:
        for path, raw, _ in work:
            atomic(path, raw)
        atomic(manifest_path, (backup / 'manifiesto.json').read_bytes())
        raise
    report = dict(utc=dt.datetime.now(dt.UTC).isoformat(), status='APPLIED_OFFLINE',
                  only_changed_member='Build-Task1.xml', only_changed_setting='PTPercent',
                  databanks_untouched=True, files=rows)
    (EVIDENCE / 'migration.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], projects=len(names), archives=len(rows))))


if __name__ == '__main__':
    main()
