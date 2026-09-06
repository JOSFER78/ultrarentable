"""Consume selective SQX exports, one bounded development experiment per run.

Recipes support MYM/MNQ: bounded fixed targets or native exit improvement.
It never changes the generator or certifies funding. An uncertain execution
blocks further work until reconciled; rejected recipes are not repeated.
"""
import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import shutil
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

import sqx_native_improvement as engine
import sqx_selective_stage as selector
import sqx_native_exit_search as native_search

RECIPE = 'fixed_pt_first_exit_inward_10pct_integer_m1_v1'
NATIVE_RECIPE = 'native_exit_search_preserved_entries_no_percent_pt_integer_m1_v2'
TERMINAL = {'COMPLETED_NOT_FUNDING_CERTIFIED', 'NO_COMPARABLE_NATIVE_VARIANTS'}

# Deployment-specific quarantine, established by data_provenance_audit.json
# (2026-09-06). These aliases were populated by importar_celdas.sh from CFD
# histories. Renaming an instrument does not turn those bars into futures.
# Revisit only after an audited dataset migration; this is not a global claim
# about these futures symbols, nor does absence here certify another dataset.
PROXY_DATA_QUARANTINE = {'MNQ': 'USATECHIDXUSD', 'MYM': 'USA30IDXUSD'}


def admit_automatic_candidates(candidates):
    """Avoid spending native improvement jobs on known unsuitable data."""
    eligible, excluded = [], []
    for candidate in candidates:
        proxy = PROXY_DATA_QUARANTINE.get(candidate['symbol'])
        if proxy:
            excluded.append({'identity': candidate['identity'],
                             'name': candidate['name'],
                             'source_sha256': candidate['source_sha256'],
                             'symbol': candidate['symbol'], 'proxy_source': proxy,
                             'reason': 'KNOWN_CFD_HISTORY_UNDER_FUTURES_ALIAS'})
        else:
            eligible.append(candidate)
    return eligible, excluded


def initial_percent_target_issue(last, rules):
    """Quarantine the pending-entry/initial-percent-PT route reproduced in SQX.

    Do not disable initial protection as a workaround: that delays SL/PT until
    the next bar. Other engines and formula types are not inferred to be faulty.
    """
    setups = last.findall('Data/Setups/Setup')
    if not any(s.get('engine', '').lower() in ('tradestation', 'multicharts') for s in setups):
        return None
    option = last.find('Options/BuildTradingOptions/Params/Param[@key="UseInitialSLPT"]')
    if option is None or (option.text or '').strip().lower() != 'true':
        return None
    for action in rules.findall('.//Rule/Then/Item'):
        if action.get('key') not in ('EnterAtStop', 'EnterAtLimit'):
            continue
        if action.find('.//Param[@exitMethodType="PT"]/Formula[@key="SQ.Formulas.SLPT.PctValue"]') is not None:
            return 'INITIAL_PERCENT_PT_PENDING_ENTRY: native initial-target calculation requires separate correction and retest'
    return None


def read_candidates(manifest_path, recipe=RECIPE, issues=None):
    """Validate the completed manifest, metric selection and exact native bytes."""
    if recipe not in (RECIPE, NATIVE_RECIPE):
        raise ValueError('Unknown improvement recipe')
    folder = manifest_path.resolve().parent
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['state'] in ('STAGING', 'SIN_CANDIDATAS'):
        return []
    if manifest['state'] != 'PRESELECCION_NO_VALIDADA' or manifest.get('probada') is not False:
        raise ValueError('Unsupported selection state')
    if not re.fullmatch(r'FONDEO_[A-Z0-9]+_[A-Z0-9]+', manifest['project']):
        raise ValueError('Unsupported source project')
    entries = manifest['files']
    if not 1 <= len(entries) <= 5 or len({e['name'] for e in entries}) != len(entries):
        raise ValueError('Expected at most five unique selected strategies')
    metrics = Path(manifest['metrics_path']).resolve()
    if metrics.parent != folder.parent or engine.sha(metrics.read_bytes()) != manifest['metrics_sha256']:
        raise ValueError('Selection metrics provenance mismatch')
    import csv
    rows = list(csv.DictReader(metrics.read_text(encoding='utf-8-sig').splitlines(), delimiter=';'))
    _, picked = selector.select(rows)
    chosen = {row['Strategy Name']: row for row in picked}
    if {e['name'] for e in entries} != set(chosen):
        raise ValueError('Manifest differs from the bounded metric selection')
    result = []
    for entry in entries:
        if entry['metrics'] != chosen[entry['name']]:
            raise ValueError('Selected metrics were changed')
        source = Path(entry['path']).resolve()
        if source.parent != folder or source.name != entry['name'] + '.sqx':
            raise ValueError('Selected archive outside the verified export')
        payload = source.read_bytes()
        if engine.sha(payload) != entry['sha256'] or len(payload) != entry['bytes']:
            raise ValueError('Selected native bytes were changed')
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            if archive.testzip() is not None:
                raise ValueError('Damaged native archive')
            settings = ET.fromstring(archive.read('settings.xml'))
            last = ET.fromstring(archive.read('lastSettings.xml'))
            rules = ET.fromstring(archive.read('strategy_Portfolio.xml'))
            if not archive.read('orders.bin'):
                raise ValueError('Missing native orders')
        strategy = engine.unique(rules, 'Strategy')
        if settings.get('ResultName') != entry['name'] or engine.sha(ET.tostring(strategy)) != entry['rules_sha256']:
            raise ValueError('Native identity or rules provenance mismatch')
        chart = engine.unique(last, 'Data/Setups/Setup/Chart')
        symbol = chart.get('symbol')
        if entry['metrics'].get('Symbol (IS)') != symbol:
            raise ValueError('Native instrument differs from selection')
        if symbol not in ('MYM', 'MNQ') or entry.get('duplicate_rules'):
            continue
        engine.native_session_profile(last)
        issue = initial_percent_target_issue(last, rules)
        if issue:
            if issues is not None:
                issues.append({'manifest': str(manifest_path), 'strategy': entry['name'],
                               'source_sha256': entry['sha256'], 'error': issue})
            continue
        exits = rules.findall('.//Param[@exitMethodType="PT"]')
        if not exits:
            continue
        if recipe == RECIPE and any(e.find('Formula') is None or
                            e.find('Formula').get('key') != 'SQ.Formulas.SLPT.FixedValue' for e in exits):
            continue  # Percent target behavior needs a separate reviewed recipe.
        if recipe == NATIVE_RECIPE:
            actions = rules.findall('.//Rule/Then/Item[@key="EnterAtStop"]')
            if len(actions) != 2:
                continue  # Only the entry shape covered by the transplant verifier.
        selected = exits[0]
        value = None
        if recipe == RECIPE:
            value = engine.unique(selected, 'Formula/Param[@key="#Value#"]').text
            engine.bounded_exit_values(value, '1')
        # Include native data, costs and sizing settings: a new market sample is
        # a new experiment, while renamed copies of the same rules are not.
        identity = engine.sha(json.dumps({'recipe': recipe, 'rules': engine.canonical(strategy),
                                         'settings': engine.canonical(last)}, sort_keys=True).encode())
        result.append({'identity': identity, 'source': str(source), 'name': entry['name'],
                       'source_sha256': entry['sha256'], 'selection_manifest': str(manifest_path),
                       'selection_manifest_sha256': engine.sha(manifest_path.read_bytes()),
                       'gid': selected.get('gid'), 'expected': value, 'symbol': symbol,
                       'rank': min(selector.number(entry['metrics'], 'Ret/DD Ratio (' + p + ')')
                                   for p in ('IS', 'OOS'))})
    return result


def discover(selection_root, registry, recipe=RECIPE):
    candidates, issues = {}, []
    for path in sorted(selection_root.glob('*/selected/manifest.json'), reverse=True):
        try:
            for candidate in read_candidates(path, recipe, issues):
                if not (registry / (candidate['identity'] + '.json')).exists():
                    candidates.setdefault(candidate['identity'], candidate)
        except (ValueError, KeyError, ArithmeticError, OSError, zipfile.BadZipFile, ET.ParseError) as error:
            issues.append({'manifest': str(path), 'error': str(error)})
    return sorted(candidates.values(), key=lambda c: (-c['rank'], c['identity'])), issues


def native_call(command):
    with urllib.request.urlopen('http://127.0.0.1:5050/call?cmd=' + command.replace(' ', '%20'), timeout=30) as response:
        return response.read().decode('utf-8')


def archive_and_release(manifest_path, assessment):
    """Release only this completed project after preserving its native evidence."""
    folder = manifest_path.parent
    manifest = json.loads(manifest_path.read_text())
    project = manifest['project']
    if not re.fullmatch(r'UR_IMPROVE_AUTO_[A-F0-9]{20}', project):
        raise ValueError('Automatic cleanup requires an owned project')
    if assessment['state'] != 'ASSESSED_NOT_FUNDING_CERTIFIED':
        raise ValueError('Cannot release an unassessed project')
    engine.native_evidence(manifest_path)
    if json.loads((folder / 'assessment.json').read_text()) != assessment:
        raise ValueError('Assessment changed before archive')
    hashes = {str(p.relative_to(folder)): engine.sha(p.read_bytes())
              for p in folder.rglob('*') if p.is_file()}
    engine.atomic_report(folder / 'archive_verified.json', {'files': hashes,
                         'state': 'NATIVE_EVIDENCE_PRESERVED_BEFORE_PROJECT_RELEASE'})
    for name, digest in hashes.items():
        if engine.sha((folder / name).read_bytes()) != digest:
            raise ValueError('Archive changed before release')
    response = native_call(f'-project action=remove name={project}')
    (folder / 'release_response.txt').write_text(response)
    projects = native_call('-project action=list')
    (folder / 'projects_after_release.txt').write_text(projects)
    if 'Lista de proyectos disponibles' not in projects or 'FONDEO_' not in projects or project in projects:
        raise RuntimeError('Completed project release not confirmed')


def release_search(folder, search):
    """Archive only a completed owned search, then release its in-memory bank."""
    if not re.fullmatch(r'UR_IMPROVE_SEARCH_AUTO_[A-F0-9]{20}', search['project']):
        raise ValueError('Not an owned automatic search')
    if search['state'] not in ('VARIANTS_REQUIRE_CONTROLLED_RETEST', 'NO_VARIANTS_PASS_DEVELOPMENT_FILTER'):
        raise ValueError('Cannot release an unfinished search')
    if json.loads((folder / 'state.json').read_text()) != search:
        raise ValueError('Search state changed before release')
    for entry in search['exported']:
        path = Path(entry['path']).resolve()
        if path.parent != (folder / 'selected').resolve() or engine.sha(path.read_bytes()) != entry['sha256']:
            raise ValueError('Search export provenance mismatch')
    hashes = {str(p.relative_to(folder)): engine.sha(p.read_bytes()) for p in folder.rglob('*') if p.is_file()}
    engine.atomic_report(folder / 'archive_verified.json', {'files': hashes, 'state': 'SEARCH_EVIDENCE_PRESERVED'})
    for name, digest in hashes.items():
        if engine.sha((folder / name).read_bytes()) != digest:
            raise ValueError('Search archive changed before release')
    response = native_call('-project action=remove name=' + search['project'])
    (folder / 'release_response.txt').write_text(response)
    projects = native_call('-project action=list')
    (folder / 'projects_after_release.txt').write_text(projects)
    if 'Lista de proyectos disponibles' not in projects or 'FONDEO_' not in projects or search['project'] in projects:
        raise RuntimeError('Search project release not confirmed')


def run_once(selection_root, registry, template, dry_run=False, search_template=None):
    recipe = NATIVE_RECIPE if search_template is not None else RECIPE
    registry.mkdir(parents=True, exist_ok=True)
    pending = [str(p) for p in registry.glob('*.json') if p.name != 'latest.json'
               and json.loads(p.read_text()).get('state') not in TERMINAL]
    if pending or Path('/opt/SQX-headless/import/reviewed_improvement_jobs/active.json').exists():
        return {'state': 'BLOCKED_PENDING_RECONCILIATION', 'pending': pending}
    candidates, issues = discover(selection_root, registry, recipe)
    candidates, excluded = admit_automatic_candidates(candidates)
    if dry_run:
        return {'state': 'INSPECTED_NOT_EXECUTED', 'eligible': candidates,
                'excluded_data': excluded, 'invalid_manifests': issues}
    if not candidates:
        return {'state': ('WAITING_FOR_NON_PROXY_DATA' if excluded else
                          'WAITING_FOR_SUPPORTED_SELECTED_STRATEGY'),
                'excluded_data': excluded, 'invalid_manifests': issues,
                'probada_para_fondeo': False}
    if shutil.disk_usage(registry).free < 5 * 1024**3:
        return {'state': 'WAITING_FOR_DISK_CAPACITY'}
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    if int(memory['MemAvailable'].split()[0]) < 8 * 1024**2:
        return {'state': 'WAITING_FOR_MEMORY_CAPACITY'}
    candidate = candidates[0]
    identity = candidate['identity']
    root = Path('/opt/SQX-headless/import/auto_improvement_' + identity[:20])
    record = registry / (identity + '.json')
    state = {'state': 'PREPARING', 'recipe': recipe, 'candidate': candidate,
             'selection_issues': issues,
             'excluded_data': excluded,
             'utc': datetime.now(timezone.utc).isoformat(), 'experiment': str(root),
             'probada_para_fondeo': False}
    engine.atomic_report(record, state)
    try:
        # Revalidate immediately before preparing immutable native input.
        fresh = read_candidates(Path(candidate['selection_manifest']), recipe)
        if candidate not in fresh:
            raise ValueError('Selection changed after scheduling')
        options = dict(gid=candidate['gid'], expected=candidate['expected'], step='1')
        working_source = Path(candidate['source'])
        if search_template is not None:
            search_root = Path('/opt/SQX-headless/import/auto_exit_search_' + identity[:20])
            state.update(state='NATIVE_SEARCH_PENDING', search=str(search_root))
            engine.atomic_report(record, state)
            search = native_search.run(Path(candidate['source']), search_template, search_root,
                         'UR_IMPROVE_SEARCH_AUTO_' + identity[:20].upper(),
                         Path(__file__).with_name('create_sqx_improvement_project.py'))
            working_source = Path(search['source'])
            if (working_source.resolve().parent != (search_root / 'source').resolve() or
                    engine.sha(working_source.read_bytes()) != candidate['source_sha256']):
                raise ValueError('Frozen search source differs from scheduled selection')
            release_search(search_root, search)
            variants = [Path(e['path']) for e in search['exported']]
            problem = 'Expected one or two qualifying variants' if len(variants) not in (1, 2) else None
            if problem is None:
                try:
                    with zipfile.ZipFile(working_source) as source_zip:
                        original = source_zip.read('strategy_Portfolio.xml')
                        effective_settings = ET.fromstring(source_zip.read('lastSettings.xml'))
                    recipes = []
                    for path in variants:
                        with zipfile.ZipFile(path) as variant_zip:
                            recipes.append(engine.transplant_native_exits(original, variant_zip.read('strategy_Portfolio.xml')))
                        issue = initial_percent_target_issue(effective_settings, ET.fromstring(recipes[-1]))
                        if issue:
                            raise ValueError(issue)
                    if len({engine.sha(recipe) for recipe in recipes}) != len(recipes):
                        problem = 'Native recipes are identical'
                except ValueError as error:
                    problem = str(error)
            if problem is not None:
                state.update(state='NO_COMPARABLE_NATIVE_VARIANTS', reason=problem,
                             next_stage_candidates=[], completed_utc=datetime.now(timezone.utc).isoformat())
                engine.atomic_report(record, state)
                return state
            options = dict(native_variants=variants)
        engine.prepare(working_source, template, root, str(root),
                       'UR_IMPROVE_AUTO_' + identity[:20].upper(),
                       integer_contracts=True, precision=2, **options)
        state['state'] = 'NATIVE_EXECUTION_PENDING'
        engine.atomic_report(record, state)
        assessment = engine.run_reviewed(root / 'manifest.json')
        archive_and_release(root / 'manifest.json', assessment)
        state.update(state='COMPLETED_NOT_FUNDING_CERTIFIED', assessment=str(root / 'assessment.json'),
                     assessment_sha256=engine.sha((root / 'assessment.json').read_bytes()),
                     decisions=assessment['decisions'], next_stage_candidates=assessment['next_stage_candidates'],
                     completed_utc=datetime.now(timezone.utc).isoformat())
        engine.atomic_report(record, state)
        return state
    except BaseException as error:
        state.update(state='NEEDS_RECONCILIATION', error=f'{type(error).__name__}: {error}')
        engine.atomic_report(record, state)
        engine.atomic_report(registry / 'latest.json', state)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection-root', type=Path, default=Path('/opt/SQX-headless/import/fondeo/preseleccion'))
    parser.add_argument('--registry', type=Path, default=Path('/opt/SQX-headless/import/automatic_improvement_jobs'))
    parser.add_argument('--template', type=Path, required=True)
    parser.add_argument('--search-template', type=Path, help='Enable bounded native exit improvement')
    parser.add_argument('--inspect', action='store_true')
    args = parser.parse_args()
    if not str(args.registry.resolve()).startswith('/opt/SQX-headless/import/'):
        parser.error('Automatic native execution is VPS-only')
    import fcntl
    args.registry.mkdir(parents=True, exist_ok=True)
    with (args.registry / 'stage.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = run_once(args.selection_root, args.registry, args.template, args.inspect, args.search_template)
        if not args.inspect:
            engine.atomic_report(args.registry / 'latest.json', result)
        print(json.dumps(result, indent=2))
