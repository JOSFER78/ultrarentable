"""Keep a verified VPS recovery copy before releasing a stopped Results bank.

This is storage maintenance, not a handoff or strategy validation. The caller
must own and stop the project. Nothing is deleted from the filesystem.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def durable(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    if os.name == 'posix':
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def records(text):
    if isinstance(text, (int, float)):
        return int(text)
    if isinstance(text, dict):
        if 'count' in text and isinstance(text['count'], (int, float)):
            return int(text['count'])
    if isinstance(text, str):
        text_clean = text.strip()
        if text_clean.startswith('{') and text_clean.endswith('}'):
            try:
                data = json.loads(text_clean)
                if 'count' in data and isinstance(data['count'], (int, float)):
                    return int(data['count'])
            except Exception:
                pass
        matches = re.findall(r'^Records:\s*(\d+)\s*$', text, re.M)
        if len(matches) == 1:
            return int(matches[0])
    raise ValueError('Native bank count is unknown')


def metric_names(path):
    rows = list(csv.DictReader(io.StringIO(Path(path).read_text(encoding='utf-8-sig')), delimiter=';'))
    names = [row['Strategy Name'] for row in rows]
    if len(names) != len(set(names)) or any(not re.fullmatch(r'Strategy [0-9.]+(?: ?\(\d+\))?', n) for n in names):
        raise ValueError('Ambiguous native strategy identities')
    return set(names)


def verify_archive(folder, names, previous=None):
    files = sorted(Path(folder).glob('*.sqx'))
    if {f.stem for f in files} != names:
        raise ValueError('Recovery copy does not contain the exact bank inventory')
    entries = []
    for path in files:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError('Corrupt recovery file: ' + path.name)
            settings = ET.fromstring(archive.read('settings.xml'))
            if settings.attrib.get('ResultName') != path.stem:
                raise ValueError('Recovery identity mismatch: ' + path.name)
            ET.fromstring(archive.read('strategy_Portfolio.xml'))
            ET.fromstring(archive.read('lastSettings.xml'))
            if not archive.read('orders.bin'):
                raise ValueError('Missing native orders: ' + path.name)
        entries.append({'file': path.name, 'size': path.stat().st_size, 'sha256': digest(path)})
    if previous is not None and entries != previous:
        raise ValueError('Recovery copy changed after verification')
    return entries


def retain(base_url, project, selection_path, expected_count, request=None, reserve_bytes=10 * 1024**3):
    """Idempotent archive/clear transaction; only a verified shortlist permits it.

    Failed/ambiguous writes are not replayed automatically. Recovery reads the
    durable transaction and native inventory before deciding the next action.
    """
    if not re.fullmatch(r'FONDEO_[A-Z0-9]+_[A-Z0-9]+', project):
        raise ValueError('Unexpected project')
    selection_path = Path(selection_path)
    selection = json.loads(selection_path.read_text())
    if (selection['project'] != project or selection['probada'] is not False
            or selection['state'] not in ('PRESELECCION_NO_VALIDADA', 'SIN_CANDIDATAS')
            or len(selection['files']) > 5):
        raise ValueError('Unverified selective handoff')
    for entry in selection['files']:
        if digest(entry['path']) != entry['sha256']:
            raise ValueError('Selected strategy changed')
    metrics = Path(selection['metrics_path'])
    if digest(metrics) != selection['metrics_sha256']:
        raise ValueError('Metrics changed')
    names = metric_names(metrics)
    if len(names) != expected_count or selection['rows'] != expected_count:
        raise ValueError('Bank and selection inventories differ')

    root = selection_path.parent.parent / 'recovery_bank'
    root.mkdir(exist_ok=True)
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(root)) and request is None:
        raise ValueError('Unsafe native output path')
    transaction = root / 'transaction.json'
    identity = {'project': project, 'count': expected_count, 'selection_sha256': digest(selection_path)}
    state = json.loads(transaction.read_text()) if transaction.exists() else dict(identity, state='NEW')
    if state.get('state') not in {'NEW', 'SAVE_REQUESTED', 'VERIFIED', 'CLEAR_REQUESTED', 'RELEASED'}:
        raise ValueError('Unknown retention transaction state')
    if any(state.get(key) != val for key, val in identity.items()):
        raise ValueError('Transaction belongs to a different bank')

    def call(command):
        if request is not None:
            return request(command)
        with urllib.request.urlopen(base_url + '/call?cmd=' + command.replace(' ', '%20'), timeout=180) as response:
            return response.read().decode('utf-8')

    def count():
        if request is None:
            host = urllib.parse.urlsplit(base_url).hostname or '127.0.0.1'
            url_native = f'http://{host}:8080/project/databankCount?' + urllib.parse.urlencode({
                'projectName': project,
                'databankName': 'Results',
            })
            try:
                with urllib.request.urlopen(url_native, timeout=30) as resp:
                    payload = json.loads(resp.read().decode('utf-8'))
                    if 'count' in payload and isinstance(payload['count'], (int, float)):
                        return int(payload['count'])
            except Exception:
                pass
        return records(call(f'-databank action=count project={project} name=Results'))

    if state['state'] == 'RELEASED':
        return {'retencion_estado': 'RELEASED', 'retencion_manifest': str(transaction), 'retencion_count': expected_count}
    native_count = count()
    if state['state'] in ('VERIFIED', 'CLEAR_REQUESTED'):
        verify_archive(root, names, state['files'])
        if native_count == 0 and state['state'] == 'CLEAR_REQUESTED':
            state.update(state='RELEASED', released_at=dt.datetime.now(dt.UTC).isoformat())
            durable(transaction, state)
            return {'retencion_estado': 'RELEASED', 'retencion_manifest': str(transaction), 'retencion_count': expected_count}
    if native_count != expected_count:
        raise ValueError('Native bank changed; no release permitted')
    if state['state'] == 'NEW':
        # Conservative bound based on actual shortlist sizes, plus a 10 GiB reserve.
        largest = max((Path(entry['path']).stat().st_size for entry in selection['files']), default=1024**2)
        if shutil.disk_usage(root).free < reserve_bytes + expected_count * max(largest * 4, 1024**2):
            raise RuntimeError('Insufficient disk reserve for recovery copy')
        command_file = root / 'save.commands'
        command_file.write_text(f'-databank action=save project={project} name=Results folder={root}\n', encoding='utf-8')
        state['state'] = 'SAVE_REQUESTED'
        durable(transaction, state)
        response = call('-run file=' + str(command_file))
        (root / 'save_response.txt').write_text(response, encoding='utf-8')
    if state['state'] == 'SAVE_REQUESTED':
        state['files'] = verify_archive(root, names)
        # Sync native files before recording authorization to clear memory.
        for item in state['files']:
            with (root / item['file']).open('r+b') as stream:
                os.fsync(stream.fileno())
        state.update(state='VERIFIED', verified_at=dt.datetime.now(dt.UTC).isoformat())
        durable(transaction, state)
    if count() != expected_count:
        raise ValueError('Bank changed during archive; no release permitted')
    # Detect a replaced bank with the same count, not just count changes.
    current = root / 'before_clear.csv'
    command_file = root / 'check.commands'
    command_file.write_text(f'-databank action=export project={project} name=Results file={current}\n', encoding='utf-8')
    call('-run file=' + str(command_file))
    if digest(current) != selection['metrics_sha256']:
        raise ValueError('Bank metrics changed during archive; no release permitted')
    state['state'] = 'CLEAR_REQUESTED'
    durable(transaction, state)
    response = call(f'-databank action=clear project={project} name=Results')
    (root / 'clear_response.txt').write_text(response, encoding='utf-8')
    if count() != 0:
        raise RuntimeError('Native release not confirmed')
    state.update(state='RELEASED', released_at=dt.datetime.now(dt.UTC).isoformat())
    durable(transaction, state)
    return {'retencion_estado': 'RELEASED', 'retencion_manifest': str(transaction), 'retencion_count': expected_count}
