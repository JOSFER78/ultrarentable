"""Servicio autónomo del motor de mejora: recorre todas las estrategias extraídas de SQX y las exprime.

Corre en la VPS bajo un temporizador de systemd (sqx-mejora-agentes.timer) y no
necesita conversación con ninguna IA ni con el PC. Encadena los programas
independientes del motor con ficheros como contrato entre ellos:

  fuentes (preselección del generador, entregas de fase 5) → inbox/*.sqx (copia + procedencia)
               → contrato (sqx_strategy_contract)
               → órdenes base (del último recálculo, del linaje, o heredadas del archivo)
               → diagnóstico (sqx_trade_diagnosis)
               → debate de agentes por el omnirouter (sqx_hypothesis_debate)
               → variantes verificadas (sqx_variant_mutations) y proyecto (sqx_native_improvement.prepare)
               → recálculo nativo en SQX (sqx_native_improvement.run_reviewed)
               → evaluación y clase (sqx_variant_evaluation)
               → entrega y registro (sqx_improvement_cycle)

Objetivo fijado por Emilio (2026-09-06): mejorar todo lo posible las estrategias
ya extraídas. Por eso el servicio (1) admite solo las fuentes configuradas y no
repite archivos ya vistos, (2) reparte cada ejecución entre varias estrategias
(la menos atendida primero) dentro de un presupuesto de tiempo, (3) mide el
presupuesto en experimentos SIN progreso, no en experimentos totales, y (4)
continúa desde una variante aceptada: la variante recalculada pasa a ser una
estrategia hija (linaje) con exigencia de evidencia creciente con la profundidad,
porque iterar sobre el mismo OOS de desarrollo aumenta el riesgo de descubrimiento
falso. Nada de esto acredita rentabilidad: toda candidata exige validación con
datos no consultados.

Estado persistente en `queue.json` (una entrada por estrategia, identificada por
el hash semántico de sus reglas). Un fallo técnico repetido deja la estrategia en
NEEDS_ATTENTION con diagnóstico; nunca reintenta indefinidamente.

Solo biblioteca estándar.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sqx_hypothesis_debate as debate  # noqa: E402
import sqx_improvement_cycle as cycle  # noqa: E402
import sqx_native_improvement as engine  # noqa: E402
import sqx_strategy_contract as contract_module  # noqa: E402

SCHEMA = 'ultrarentable.improvement_service.v2'
ACTIVE_STATES = ('QUEUED', 'IN_PROGRESS')
TERMINAL_STATES = ('CANDIDATE_FOR_VALIDATION', 'IMPROVED_CONTINUED', 'EXHAUSTED', 'NEEDS_ATTENTION', 'REJECTED_INPUT')
PROGRESS_CLASSES = ('DEV_FAVORABLE_RELEVANT', 'DEV_FAVORABLE_NOT_RELEVANT')
DEFAULT_BUDGET = {
    'max_experiments_without_progress': 3,  # experimentos evaluados seguidos sin ninguna clase DEV_FAVORABLE_*
    'max_experiments': 6,                   # tope duro por estrategia (por nodo del linaje)
    'max_failed_attempts': 2,
    'max_empty_debates': 2,
    'max_variants': 2,
    'max_lineage_depth': 3,                 # profundidad máxima de hijas encadenadas desde la extraída
}
# Evidencia OOS emparejada exigida para aceptar una variante según la profundidad del linaje.
EVIDENCE_BY_DEPTH = {0: 'MODERATE', 1: 'MODERATE'}
DEFAULT_INTAKE = (
    {'pattern': '/opt/SQX-headless/import/fondeo/entrega_fase5/strategies/*.sqx', 'origin': 'entrega_fase5', 'priority': 0},
    {'pattern': '/opt/SQX-headless/import/fondeo/preseleccion/*/selected/*.sqx', 'origin': 'preseleccion_generador', 'priority': 1},
)


def now():
    return datetime.now(timezone.utc).isoformat()


def slugify(name: str, semantic: str) -> str:
    base = re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_')[:40] or 'estrategia'
    return f'{base}_{semantic[:8]}'


def required_evidence(depth: int) -> str:
    return EVIDENCE_BY_DEPTH.get(depth, 'STRONG')


class Queue:
    def __init__(self, base: Path):
        self.base = base
        self.path = base / 'queue.json'
        self.data = cycle.read_json(self.path) if self.path.exists() else {'schema': SCHEMA, 'strategies': {}}
        self.data.setdefault('intake_seen', {})

    def save(self):
        self.data['updated_utc'] = now()
        cycle.write_json(self.path, self.data)

    def entry(self, slug: str) -> dict:
        return self.data['strategies'][slug]


# ------------------------------------------------------------------ ingesta

def intake_sources(base: Path, queue: Queue, sources) -> list[dict]:
    """Copia al inbox los .sqx nuevos de las fuentes configuradas, con su procedencia en un .json.

    No mueve ni altera los archivos de origen (son artefactos de otros procesos). Un archivo
    ya visto (mismo SHA-256) no vuelve a entrar aunque cambie de sitio.
    """
    inbox = base / 'inbox'
    inbox.mkdir(parents=True, exist_ok=True)
    copied = []
    for source in sources:
        for path in sorted(glob.glob(source['pattern'])):
            file = Path(path)
            digest = engine.sha(file.read_bytes())
            if digest in queue.data['intake_seen']:
                continue
            round_dir = file.parent.parent if file.parent.name == 'selected' else file.parent
            origin = {'origin': source['origin'], 'path': str(file), 'sha256': digest, 'priority': source.get('priority', 1),
                      'cell': round_dir.name.rsplit('_r', 1)[0] if '_r' in round_dir.name else None, 'round_dir': round_dir.name,
                      'intake_utc': now()}
            selection = round_dir / 'selection_output.txt'
            if selection.exists():
                try:
                    for item in json.loads(selection.read_text(encoding='utf-8', errors='replace')).get('files', []):
                        if item.get('sha256') == digest or item.get('name') == file.stem:
                            origin['selection_metrics'] = {k: v for k, v in (item.get('metrics') or {}).items()
                                                           if k in ('Net profit (IS)', 'Net profit (OOS)', 'Profit factor (IS)', 'Profit factor (OOS)',
                                                                    '# of trades (IS)', '# of trades (OOS)', 'Ret/DD Ratio (IS)', 'Ret/DD Ratio (OOS)')}
                            break
                except (ValueError, OSError):
                    pass
            target = inbox / file.name
            if target.exists():  # mismo nombre desde otra ronda: se distingue por hash
                target = inbox / f'{file.stem}_{digest[:8]}.sqx'
            shutil.copy2(file, target)
            cycle.write_json(target.with_suffix('.json'), origin)
            queue.data['intake_seen'][digest] = {'file': target.name, 'source': source['origin'], 'utc': now()}
            copied.append(origin)
    if copied:
        queue.save()
    return copied


def ingest_inbox(base: Path, queue: Queue, budget: dict) -> list[dict]:
    """Cada .sqx nuevo del inbox entra en la cola con su contrato; el original se conserva."""
    admitted = []
    inbox = base / 'inbox'
    inbox.mkdir(parents=True, exist_ok=True)
    for source in sorted(inbox.glob('*.sqx')):
        try:
            contract = contract_module.extract_contract(source)
        except Exception as error:  # archivo corrupto: se aparta con motivo
            slug = slugify(source.stem, engine.sha(source.read_bytes()))
            folder = base / 'strategies' / slug
            folder.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), folder / source.name)
            queue.data['strategies'][slug] = {'slug': slug, 'name': source.stem, 'state': 'REJECTED_INPUT',
                                              'reason': f'{type(error).__name__}: {error}', 'updated_utc': now()}
            admitted.append(queue.entry(slug))
            continue
        semantic = contract['identity']['semantic_rules_sha256']
        slug = slugify(contract['identity']['name'], semantic)
        folder = base / 'strategies' / slug
        (folder / 'source').mkdir(parents=True, exist_ok=True)
        sidecar = source.with_suffix('.json')
        origin = cycle.read_json(sidecar) if sidecar.exists() else {}
        target = folder / 'source' / source.name
        shutil.move(str(source), target)
        if sidecar.exists():
            shutil.move(str(sidecar), folder / 'source' / sidecar.name)
        contract = contract_module.extract_contract(target, origin)
        cycle.write_json(folder / 'contract.json', contract)
        if slug in queue.data['strategies'] and queue.entry(slug)['state'] not in ('REJECTED_INPUT',):
            queue.entry(slug).setdefault('duplicates', []).append({'file': source.name, 'utc': now()})
            admitted.append(queue.entry(slug))
            continue
        state = 'QUEUED' if contract['state'] == 'CONTRACT_COMPLETE' else 'REJECTED_INPUT'
        queue.data['strategies'][slug] = {
            'slug': slug, 'name': contract['identity']['name'], 'symbol': contract['market'].get('symbol'),
            'timeframe': contract['market'].get('timeframe'), 'semantic_rules_sha256': semantic,
            'data_is_known_cfd_proxy': bool(contract['market'].get('known_proxy_alias')),
            'source': str(target), 'source_sha256': contract['identity']['archive_sha256'], 'origin': origin,
            'priority': origin.get('priority', 1), 'lineage': {'depth': 0, 'parent': None, 'root': slug},
            'state': state, 'reason': None if state == 'QUEUED' else 'Contrato incompleto: ' + ', '.join(contract['essentials_missing']),
            'budget': {**budget, 'required_oos_evidence': required_evidence(0)},
            'experiments': [], 'without_progress': 0, 'failed_attempts': 0, 'empty_debates': 0,
            'last_error': None, 'created_utc': now(), 'updated_utc': now(),
        }
        admitted.append(queue.entry(slug))
    queue.save()
    return admitted


def pick_next(queue: Queue, exclude=()) -> dict | None:
    """Reparto en anchura: la estrategia activa con menos experimentos primero (todas avanzan antes de que
    ninguna repita), la prioridad desempata (entregas de fase 5 y linajes antes) y después la menos atendida."""
    candidates = [e for e in queue.data['strategies'].values() if e['state'] in ACTIVE_STATES and e['slug'] not in exclude]
    candidates.sort(key=lambda e: (len(e.get('experiments', [])), e.get('priority', 1), e.get('updated_utc', ''), e.get('created_utc', '')))
    return candidates[0] if candidates else None


# -------------------------------------------------------------- experimento

def base_orders_for(folder: Path, entry: dict) -> tuple[Path, str]:
    """Órdenes del control: las del último recálculo; si no, las frescas heredadas del linaje; si no, las del archivo."""
    for previous in sorted(folder.glob('ciclo_*'), reverse=True):
        manifest = previous / 'experiment' / 'manifest.json'
        if manifest.exists():
            base_name = cycle.read_json(manifest)['entries'][0]['name']
            orders = previous / 'experiment' / f'{base_name}_orders.csv'
            if orders.exists():
                return orders, f'FRESH_RETEST_{cycle.read_json(manifest)["project"]}'
    fresh = folder / 'orders_fresh.csv'
    if fresh.exists():
        note = folder / 'orders_fresh.json'
        provenance = cycle.read_json(note).get('provenance') if note.exists() else 'FRESH_RETEST_LINEAGE'
        return fresh, provenance
    inherited = folder / 'orders_inherited.csv'
    if not inherited.exists():
        cycle.export_inherited_orders(Path(entry['source']), inherited)
    return inherited, 'INHERITED_FROM_SOURCE_ARCHIVE_NOT_FRESH_RETEST'


def explored_for(entry: dict, registry: Path, queue: Queue | None = None) -> dict:
    """Variantes ya probadas: las de esta estrategia y, en un linaje, las de sus antecesoras (marcadas)."""
    key = entry['semantic_rules_sha256']
    explored = cycle.read_json(registry / f'{key}.json') if (registry / f'{key}.json').exists() else {'variants': {}, 'experiments': []}
    explored = {'variants': dict(explored.get('variants', {})), 'experiments': list(explored.get('experiments', []))}
    parent = (entry.get('lineage') or {}).get('parent')
    depth = 0
    while parent and queue is not None and parent in queue.data['strategies'] and depth < 10:
        ancestor = queue.entry(parent)
        akey = ancestor.get('semantic_rules_sha256')
        if akey and (registry / f'{akey}.json').exists():
            for sha, variant in cycle.read_json(registry / f'{akey}.json').get('variants', {}).items():
                explored['variants'].setdefault(f'ancestor:{sha}', {**variant, 'inherited_from': parent})
        parent = (ancestor.get('lineage') or {}).get('parent')
        depth += 1
    return explored


def run_experiment(base: Path, entry: dict, template: Path, registry: Path, provider, remote_root: str, queue: Queue | None = None) -> dict:
    """Un experimento completo; cada paso deja ficheros y es idempotente."""
    folder = base / 'strategies' / entry['slug']
    number = len(entry['experiments']) + 1
    cycle_dir = folder / f'ciclo_{number:02d}'
    cycle_dir.mkdir(parents=True, exist_ok=True)
    source = Path(entry['source'])
    contract = cycle.step_contract(cycle_dir, source, entry.get('origin'))
    if contract['state'] != 'CONTRACT_COMPLETE':
        raise ValueError('Contrato incompleto: ' + ', '.join(contract['essentials_missing']))
    orders, provenance = base_orders_for(folder, entry)
    if not (cycle_dir / 'diagnosis_base.json').exists():
        cycle.step_diagnose(cycle_dir, contract, orders, provenance)
    if not (cycle_dir / 'criteria.json').exists():
        cycle.write_json(cycle_dir / 'criteria.json', {**cycle.DEFAULT_CRITERIA, 'registered_utc': now(),
                                                       'required_oos_evidence': entry['budget'].get('required_oos_evidence', 'MODERATE'),
                                                       'lineage': entry.get('lineage')})
    explored = explored_for(entry, registry, queue)
    cycle.write_json(cycle_dir / 'explored.json', explored)
    hypotheses = cycle_dir / 'debate' / 'hypotheses.json'
    if not hypotheses.exists():
        summary = debate.run_debate(cycle_dir, provider, entry['budget']['max_variants'])
        if summary['search_budget']['selected'] == 0:
            return {'outcome': 'NO_HYPOTHESES', 'cycle': str(cycle_dir), 'debate': summary['search_budget'],
                    'next_round': summary.get('next_round_if_all_fail'), 'capability_gaps': summary.get('capability_gaps', [])}
    diagnosis = cycle.read_json(cycle_dir / 'diagnosis_base.json')
    plan = cycle.step_plan(cycle_dir, contract, diagnosis, explored, max_variants=entry['budget']['max_variants'],
                           hypotheses_path=hypotheses)
    if not plan['planned_labels']:
        return {'outcome': 'NO_APPLICABLE_HYPOTHESES', 'cycle': str(cycle_dir),
                'hypotheses': [{k: h.get(k) for k in ('id', 'status', 'reason')} for h in plan['hypotheses']]}
    project = re.sub(r'[^A-Z0-9_]', '', f"UR_IMPROVE_{entry['slug'].upper()}_{number:02d}")[:60]
    remote_dir = f'{remote_root}/{entry["slug"]}/ciclo_{number:02d}/experiment'
    cycle.step_prepare(cycle_dir, contract, plan, template, remote_dir, project)
    if str(cycle_dir.resolve()).replace('\\', '/') != remote_dir.rsplit('/experiment', 1)[0]:
        # El motor de recálculo exige que el experimento viva exactamente en la ruta declarada.
        raise RuntimeError(f'El ciclo debe vivir en {remote_dir.rsplit("/experiment", 1)[0]}; está en {cycle_dir}')
    if not (cycle_dir / 'experiment' / 'assessment.json').exists():
        cycle.step_run(cycle_dir)
    criteria = cycle.read_json(cycle_dir / 'criteria.json')
    evaluation = cycle.step_evaluate(cycle_dir, contract, criteria)
    cycle.update_registry(registry, cycle_dir, contract, evaluation)
    package = cycle.step_package(cycle_dir)
    return {'outcome': 'EVALUATED', 'cycle': str(cycle_dir), 'project': project,
            'classes': {v['name']: v['class'] for v in evaluation['variants']},
            'accepted_for_validation': evaluation['accepted_for_validation'],
            'oos_evidence': {v['name']: v['paired_daily'].get('evidence_strength') for v in evaluation['variants']},
            'cost': package.get('cost'), 'entrega': str(cycle_dir / 'entrega.json')}


# ---------------------------------------------------------------- decisión

def spawn_child(base: Path, queue: Queue, entry: dict, result: dict, variant_name: str) -> dict | None:
    """La variante aceptada pasa a ser una estrategia hija con sus órdenes frescas y evidencia más exigente."""
    cycle_dir = Path(result['cycle'])
    retested = cycle_dir / 'experiment' / 'retested' / f'{variant_name}.sqx'
    orders = cycle_dir / 'experiment' / f'{variant_name}_orders.csv'
    if not retested.exists() or not orders.exists():
        return None
    try:
        contract = contract_module.extract_contract(retested)
    except Exception:
        return None
    semantic = contract['identity']['semantic_rules_sha256']
    slug = slugify(contract['identity']['name'], semantic)
    if semantic == entry.get('semantic_rules_sha256') or slug == entry['slug']:
        return None  # la variante recalculada no difiere de su base: no hay linaje que continuar
    if slug in queue.data['strategies']:
        return queue.entry(slug)
    depth = (entry.get('lineage') or {}).get('depth', 0) + 1
    folder = base / 'strategies' / slug
    (folder / 'source').mkdir(parents=True, exist_ok=True)
    target = folder / 'source' / retested.name
    shutil.copy2(retested, target)
    shutil.copy2(orders, folder / 'orders_fresh.csv')
    cycle.write_json(folder / 'orders_fresh.json', {'provenance': f"FRESH_RETEST_{result.get('project')}", 'variant': variant_name,
                                                    'parent_cycle': str(cycle_dir), 'sha256': engine.sha(orders.read_bytes())})
    origin = {**(entry.get('origin') or {}), 'origin': 'lineage', 'parent': entry['slug'], 'parent_cycle': str(cycle_dir),
              'variant': variant_name, 'class': result['classes'].get(variant_name),
              'oos_evidence': (result.get('oos_evidence') or {}).get(variant_name), 'priority': entry.get('priority', 1)}
    contract = contract_module.extract_contract(target, origin)
    cycle.write_json(folder / 'contract.json', contract)
    child = {
        'slug': slug, 'name': contract['identity']['name'], 'symbol': contract['market'].get('symbol'),
        'timeframe': contract['market'].get('timeframe'), 'semantic_rules_sha256': semantic,
        'data_is_known_cfd_proxy': bool(contract['market'].get('known_proxy_alias')),
        'source': str(target), 'source_sha256': contract['identity']['archive_sha256'], 'origin': origin,
        'priority': entry.get('priority', 1) - 0.5,  # la línea que progresa se atiende antes
        'lineage': {'depth': depth, 'parent': entry['slug'], 'root': (entry.get('lineage') or {}).get('root', entry['slug'])},
        'state': 'QUEUED', 'reason': None,
        'budget': {**entry['budget'], 'required_oos_evidence': required_evidence(depth)},
        'experiments': [], 'without_progress': 0, 'failed_attempts': 0, 'empty_debates': 0,
        'last_error': None, 'created_utc': now(), 'updated_utc': now(),
    }
    queue.data['strategies'][slug] = child
    return child


def apply_outcome(base: Path, queue: Queue, entry: dict, result: dict):
    budget = entry['budget']
    entry['experiments'].append({**result, 'utc': now()})
    entry['failed_attempts'] = 0
    entry['last_error'] = None
    if result['outcome'] in ('NO_HYPOTHESES', 'NO_APPLICABLE_HYPOTHESES'):
        entry['empty_debates'] += 1
        if entry['empty_debates'] >= budget['max_empty_debates']:
            entry['state'], entry['reason'] = 'EXHAUSTED', 'Los agentes no encuentran hipótesis aplicables nuevas: la estrategia deja de consumir recursos.'
        else:
            entry['state'] = 'IN_PROGRESS'
        return
    entry['empty_debates'] = 0
    classes = result.get('classes') or {}
    accepted = list(result.get('accepted_for_validation') or [])
    if accepted:
        # Entrega de la candidata y continuación del linaje desde la mejor variante aceptada.
        outbox = base / 'outbox'
        outbox.mkdir(exist_ok=True)
        if result.get('entrega') and Path(result['entrega']).exists():
            shutil.copy(result['entrega'], outbox / f"{entry['slug']}_{Path(result['cycle']).name}_entrega.json")
        entry['without_progress'] = 0
        depth = (entry.get('lineage') or {}).get('depth', 0)
        strength = {'STRONG': 2, 'MODERATE': 1}
        best = max(accepted, key=lambda n: strength.get((result.get('oos_evidence') or {}).get(n), 0))
        child = spawn_child(base, queue, entry, result, best) if depth + 1 <= budget['max_lineage_depth'] else None
        if child is not None:
            entry['state'], entry['reason'] = 'IMPROVED_CONTINUED', f"Variante {best} aceptada; el linaje continúa en {child['slug']} (profundidad {child['lineage']['depth']})."
            entry['child'] = child['slug']
        else:
            entry['state'], entry['reason'] = 'CANDIDATE_FOR_VALIDATION', ('Variante con progreso útil en desarrollo; requiere validación independiente con datos no consultados.'
                                                                           + ('' if depth + 1 <= budget['max_lineage_depth'] else f' Profundidad máxima del linaje ({budget["max_lineage_depth"]}) alcanzada.'))
        return
    if any(c in PROGRESS_CLASSES for c in classes.values()):
        entry['without_progress'] = 0  # mejora estadística sin relevancia: se sigue buscando, sin crear hija
    else:
        entry['without_progress'] = entry.get('without_progress', 0) + 1
    evaluated = [e for e in entry['experiments'] if e['outcome'] == 'EVALUATED']
    if entry['without_progress'] >= budget['max_experiments_without_progress']:
        entry['state'], entry['reason'] = 'EXHAUSTED', f"{entry['without_progress']} experimentos seguidos sin progreso útil: la estrategia deja de consumir recursos."
    elif len(evaluated) >= budget['max_experiments']:
        entry['state'], entry['reason'] = 'EXHAUSTED', f"{len(evaluated)} experimentos evaluados: tope duro por estrategia."
    else:
        entry['state'] = 'IN_PROGRESS'


def apply_failure(entry: dict, error: BaseException, budget: dict):
    entry['failed_attempts'] += 1
    entry['last_error'] = {'type': type(error).__name__, 'message': str(error)[:800], 'utc': now(),
                           'traceback': traceback.format_exc()[-1500:]}
    if entry['failed_attempts'] >= budget['max_failed_attempts']:
        entry['state'], entry['reason'] = 'NEEDS_ATTENTION', f"Fallo técnico repetido ({entry['failed_attempts']}): {type(error).__name__}: {str(error)[:200]}"
    else:
        entry['state'] = 'IN_PROGRESS'


# -------------------------------------------------------------------- ciclo

def preflight(base: Path) -> str | None:
    """Motivos para no gastar recursos en esta ejecución (no son fallos de la estrategia)."""
    claim = Path('/opt/SQX-headless/import/reviewed_improvement_jobs/active.json')
    if claim.exists():
        return 'BLOCKED_BY_ACTIVE_CLAIM: otro recálculo revisado está en curso o pendiente de reconciliación'
    meminfo = Path('/proc/meminfo')
    if meminfo.exists():
        memory = dict(line.split(':', 1) for line in meminfo.read_text().splitlines())
        if int(memory['MemAvailable'].split()[0]) < 8 * 1024 * 1024:
            return 'WAITING_FOR_MEMORY_CAPACITY'
    if shutil.disk_usage(base).free < 5 * 1024 ** 3:
        return 'WAITING_FOR_DISK_CAPACITY'
    return None


def run_once(base: Path, template: Path, registry: Path, provider, remote_root: str, budget: dict = None,
             experiment_runner=None, max_experiments_per_run: int = 1, time_budget_seconds: float | None = None,
             intake=None) -> dict:
    budget = {**DEFAULT_BUDGET, **(budget or {})}
    base.mkdir(parents=True, exist_ok=True)
    queue = Queue(base)
    intaken = intake_sources(base, queue, intake or ())
    admitted = ingest_inbox(base, queue, budget)
    status = {'schema': SCHEMA, 'utc': now(), 'intaken': len(intaken), 'admitted': [a['slug'] for a in admitted],
              'provider': getattr(provider, 'name', None), 'runs': []}
    started = time.monotonic()
    runner = experiment_runner or run_experiment
    worked = []
    while len(status['runs']) < max_experiments_per_run:
        reason = preflight(base)
        if reason:
            status.update(state='SKIPPED' if not status['runs'] else 'STOPPED', reason=reason)
            break
        entry = pick_next(queue, exclude=worked)
        if entry is None:
            status.update(state='IDLE' if not status['runs'] else 'DONE', reason='Sin estrategias con presupuesto en la cola')
            break
        entry['state'] = 'IN_PROGRESS'
        entry['updated_utc'] = now()
        queue.save()
        run = {'strategy': entry['slug'], 'started_utc': now()}
        try:
            result = runner(base, entry, template, registry, provider, remote_root)
            apply_outcome(base, queue, entry, result)
            run.update(state='EXPERIMENT_DONE', result=result, strategy_state=entry['state'], child=entry.get('child'))
        except BaseException as error:
            apply_failure(entry, error, budget)
            run.update(state='EXPERIMENT_FAILED', error=entry['last_error'], strategy_state=entry['state'])
        entry['updated_utc'] = now()
        queue.save()
        worked.append(entry['slug'])
        status['runs'].append(run)
        if time_budget_seconds is not None and time.monotonic() - started >= time_budget_seconds:
            status.update(state='DONE', reason='Presupuesto de tiempo de la ejecución agotado')
            break
    if 'state' not in status:
        status.update(state='DONE', reason=f"{len(status['runs'])} experimentos en esta ejecución")
    # Compatibilidad con el formato v1 (una ejecución = un experimento) para lectores existentes.
    if status['runs']:
        last = status['runs'][-1]
        status.update({k: last[k] for k in ('strategy', 'result', 'error', 'strategy_state') if k in last})
        if len(status['runs']) == 1:
            status['state'] = last['state']
    status['seconds'] = round(time.monotonic() - started, 1)
    status['queue'] = queue_summary(queue)
    cycle.write_json(base / 'status.json', status)
    return status


def queue_summary(queue: Queue) -> dict:
    counts = {}
    for entry in queue.data['strategies'].values():
        counts[entry['state']] = counts.get(entry['state'], 0) + 1
    return {'strategies': len(queue.data['strategies']), 'by_state': counts,
            'lineage_children': sum(1 for e in queue.data['strategies'].values() if (e.get('lineage') or {}).get('depth', 0) > 0),
            'intake_seen': len(queue.data.get('intake_seen', {}))}


def inspect(base: Path) -> dict:
    queue = Queue(base)
    return {'schema': SCHEMA, 'utc': now(), 'summary': queue_summary(queue),
            'strategies': [{k: e.get(k) for k in ('slug', 'name', 'symbol', 'timeframe', 'state', 'reason', 'priority', 'without_progress',
                                                   'failed_attempts', 'empty_debates', 'data_is_known_cfd_proxy')}
                           | {'lineage': e.get('lineage'), 'experiments': [(x['outcome'], x.get('classes')) for x in e.get('experiments', [])]}
                           for e in queue.data['strategies'].values()],
            'last_status': cycle.read_json(base / 'status.json') if (base / 'status.json').exists() else None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path('/opt/SQX-headless/import/mejora'))
    parser.add_argument('--template', type=Path, help='project.cfx de un retest verificado (obligatorio con --once)')
    parser.add_argument('--registry', type=Path, default=Path('/opt/SQX-headless/import/improvement_registry'))
    parser.add_argument('--provider', choices=('omniroute', 'anthropic', 'claude-cli'), default='omniroute')
    parser.add_argument('--model')
    parser.add_argument('--max-experiments', type=int, default=DEFAULT_BUDGET['max_experiments'], help='tope duro de experimentos evaluados por estrategia')
    parser.add_argument('--max-without-progress', type=int, default=DEFAULT_BUDGET['max_experiments_without_progress'])
    parser.add_argument('--max-lineage-depth', type=int, default=DEFAULT_BUDGET['max_lineage_depth'])
    parser.add_argument('--max-experiments-per-run', type=int, default=1, help='experimentos por ejecución (estrategias distintas)')
    parser.add_argument('--time-budget-minutes', type=float, help='no empezar otro experimento pasado este tiempo')
    parser.add_argument('--intake', action='append', default=[], metavar='ORIGEN=PRIORIDAD=GLOB',
                        help="fuente de estrategias extraídas, p. ej. 'preseleccion_generador=1=/opt/SQX-headless/import/fondeo/preseleccion/*/selected/*.sqx'; por defecto las dos fuentes del generador de fondeo")
    parser.add_argument('--no-intake', action='store_true', help='no leer fuentes; solo el inbox')
    parser.add_argument('--once', action='store_true', help='una ejecución del servicio (varios experimentos si se pide)')
    parser.add_argument('--inspect', action='store_true')
    args = parser.parse_args()
    if args.inspect or not args.once:
        print(json.dumps(inspect(args.base), indent=2, ensure_ascii=False))
        raise SystemExit(0)
    if not str(args.base.resolve()).startswith('/opt/SQX-headless/import/'):
        parser.error('El recálculo nativo solo se ejecuta en la VPS bajo /opt/SQX-headless/import/')
    if not args.template:
        parser.error('--template es obligatorio con --once')
    sources = []
    for item in args.intake:
        origin, priority, pattern = item.split('=', 2)
        sources.append({'origin': origin, 'priority': float(priority), 'pattern': pattern})
    if not sources and not args.no_intake:
        sources = list(DEFAULT_INTAKE)
    import fcntl
    args.base.mkdir(parents=True, exist_ok=True)
    with (args.base / 'service.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({'state': 'SKIPPED', 'reason': 'Otra ejecución del servicio está en curso'}))
            raise SystemExit(0)
        result = run_once(args.base, args.template, args.registry, debate.make_provider(args.provider, args.model),
                          str(args.base / 'strategies'),
                          {'max_experiments': args.max_experiments, 'max_experiments_without_progress': args.max_without_progress,
                           'max_lineage_depth': args.max_lineage_depth},
                          max_experiments_per_run=args.max_experiments_per_run,
                          time_budget_seconds=args.time_budget_minutes * 60 if args.time_budget_minutes else None,
                          intake=sources)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
