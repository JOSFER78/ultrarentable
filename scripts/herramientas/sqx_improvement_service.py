"""Servicio autónomo del motor de mejora: una estrategia, un experimento por ejecución.

Corre en la VPS bajo un temporizador de systemd (sqx-mejora-agentes.timer) y no
necesita conversación con ninguna IA ni con el PC. Encadena los programas
independientes del motor con ficheros como contrato entre ellos:

  inbox/*.sqx  → contrato (sqx_strategy_contract)
               → órdenes base (heredadas del archivo o del último recálculo)
               → diagnóstico (sqx_trade_diagnosis)
               → debate de agentes por el omnirouter (sqx_hypothesis_debate)
               → variantes verificadas (sqx_variant_mutations) y proyecto (sqx_native_improvement.prepare)
               → recálculo nativo en SQX (sqx_native_improvement.run_reviewed)
               → evaluación y clase (sqx_variant_evaluation)
               → entrega y registro (sqx_improvement_cycle)

Estado persistente en `queue.json` (una entrada por estrategia, identificada por
el hash semántico de sus reglas): presupuesto de experimentos, intentos fallidos,
último error y decisión. Un fallo técnico repetido deja la estrategia en
NEEDS_ATTENTION con diagnóstico; nunca reintenta indefinidamente. Una estrategia
que agota su presupuesto sin progreso útil queda EXHAUSTED; una con una variante
DEV_FAVORABLE_RELEVANT pasa a CANDIDATE_FOR_VALIDATION y su entrega se copia a
`outbox/` para el siguiente proceso. Nada de esto acredita rentabilidad.

Solo biblioteca estándar.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sqx_hypothesis_debate as debate  # noqa: E402
import sqx_improvement_cycle as cycle  # noqa: E402
import sqx_native_improvement as engine  # noqa: E402
import sqx_strategy_contract as contract_module  # noqa: E402

SCHEMA = 'ultrarentable.improvement_service.v1'
ACTIVE_STATES = ('QUEUED', 'IN_PROGRESS')
TERMINAL_STATES = ('CANDIDATE_FOR_VALIDATION', 'EXHAUSTED', 'NEEDS_ATTENTION', 'REJECTED_INPUT')
DEFAULT_BUDGET = {'max_experiments': 3, 'max_failed_attempts': 2, 'max_empty_debates': 2, 'max_variants': 2}


def now():
    return datetime.now(timezone.utc).isoformat()


def slugify(name: str, semantic: str) -> str:
    base = re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_')[:40] or 'estrategia'
    return f'{base}_{semantic[:8]}'


class Queue:
    def __init__(self, base: Path):
        self.base = base
        self.path = base / 'queue.json'
        self.data = cycle.read_json(self.path) if self.path.exists() else {'schema': SCHEMA, 'strategies': {}}

    def save(self):
        self.data['updated_utc'] = now()
        cycle.write_json(self.path, self.data)

    def entry(self, slug: str) -> dict:
        return self.data['strategies'][slug]


# ------------------------------------------------------------------ ingesta

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
            'source': str(target), 'source_sha256': contract['identity']['archive_sha256'], 'origin': origin,
            'state': state, 'reason': None if state == 'QUEUED' else 'Contrato incompleto: ' + ', '.join(contract['essentials_missing']),
            'budget': dict(budget), 'experiments': [], 'failed_attempts': 0, 'empty_debates': 0,
            'last_error': None, 'created_utc': now(), 'updated_utc': now(),
        }
        admitted.append(queue.entry(slug))
    queue.save()
    return admitted


def pick_next(queue: Queue) -> dict | None:
    candidates = [e for e in queue.data['strategies'].values() if e['state'] in ACTIVE_STATES]
    candidates.sort(key=lambda e: (e['state'] != 'IN_PROGRESS', e.get('created_utc', '')))
    return candidates[0] if candidates else None


# -------------------------------------------------------------- experimento

def base_orders_for(folder: Path, entry: dict) -> tuple[Path, str]:
    """Órdenes del control: las del último recálculo si existe; si no, las heredadas del archivo."""
    for previous in sorted(folder.glob('ciclo_*'), reverse=True):
        manifest = previous / 'experiment' / 'manifest.json'
        if manifest.exists():
            base_name = cycle.read_json(manifest)['entries'][0]['name']
            orders = previous / 'experiment' / f'{base_name}_orders.csv'
            if orders.exists():
                return orders, f'FRESH_RETEST_{cycle.read_json(manifest)["project"]}'
    inherited = folder / 'orders_inherited.csv'
    if not inherited.exists():
        cycle.export_inherited_orders(Path(entry['source']), inherited)
    return inherited, 'INHERITED_FROM_SOURCE_ARCHIVE_NOT_FRESH_RETEST'


def run_experiment(base: Path, entry: dict, template: Path, registry: Path, provider, remote_root: str) -> dict:
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
        cycle.write_json(cycle_dir / 'criteria.json', {**cycle.DEFAULT_CRITERIA, 'registered_utc': now()})
    key = contract['identity']['semantic_rules_sha256']
    explored = cycle.read_json(registry / f'{key}.json') if (registry / f'{key}.json').exists() else {'variants': {}, 'experiments': []}
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
            'cost': package.get('cost'), 'entrega': str(cycle_dir / 'entrega.json')}


# ---------------------------------------------------------------- decisión

def apply_outcome(base: Path, entry: dict, result: dict):
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
    if result['accepted_for_validation']:
        entry['state'], entry['reason'] = 'CANDIDATE_FOR_VALIDATION', 'Variante con progreso útil en desarrollo; requiere validación independiente con datos no consultados.'
        outbox = base / 'outbox'
        outbox.mkdir(exist_ok=True)
        shutil.copy(result['entrega'], outbox / f"{entry['slug']}_{Path(result['cycle']).name}_entrega.json")
        return
    evaluated = [e for e in entry['experiments'] if e['outcome'] == 'EVALUATED']
    if len(evaluated) >= budget['max_experiments']:
        entry['state'], entry['reason'] = 'EXHAUSTED', f"{len(evaluated)} experimentos sin progreso útil: presupuesto agotado."
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
             experiment_runner=None) -> dict:
    budget = {**DEFAULT_BUDGET, **(budget or {})}
    base.mkdir(parents=True, exist_ok=True)
    queue = Queue(base)
    admitted = ingest_inbox(base, queue, budget)
    status = {'schema': SCHEMA, 'utc': now(), 'admitted': [a['slug'] for a in admitted], 'provider': getattr(provider, 'name', None)}
    reason = preflight(base)
    if reason:
        status.update(state='SKIPPED', reason=reason)
        cycle.write_json(base / 'status.json', status)
        return status
    entry = pick_next(queue)
    if entry is None:
        status.update(state='IDLE', reason='Sin estrategias con presupuesto en la cola')
        cycle.write_json(base / 'status.json', status)
        return status
    entry['state'] = 'IN_PROGRESS'
    entry['updated_utc'] = now()
    queue.save()
    runner = experiment_runner or run_experiment
    try:
        result = runner(base, entry, template, registry, provider, remote_root)
        apply_outcome(base, entry, result)
        status.update(state='EXPERIMENT_DONE', strategy=entry['slug'], result=result, strategy_state=entry['state'])
    except BaseException as error:
        apply_failure(entry, error, budget)
        status.update(state='EXPERIMENT_FAILED', strategy=entry['slug'], error=entry['last_error'], strategy_state=entry['state'])
    entry['updated_utc'] = now()
    queue.save()
    cycle.write_json(base / 'status.json', status)
    return status


def inspect(base: Path) -> dict:
    queue = Queue(base)
    return {'schema': SCHEMA, 'utc': now(),
            'strategies': [{k: e.get(k) for k in ('slug', 'name', 'symbol', 'state', 'reason', 'failed_attempts', 'empty_debates')}
                           | {'experiments': [(x['outcome'], x.get('classes')) for x in e.get('experiments', [])]}
                           for e in queue.data['strategies'].values()],
            'last_status': cycle.read_json(base / 'status.json') if (base / 'status.json').exists() else None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path('/opt/SQX-headless/import/mejora'))
    parser.add_argument('--template', type=Path, help='project.cfx de un retest verificado (obligatorio con --once)')
    parser.add_argument('--registry', type=Path, default=Path('/opt/SQX-headless/import/improvement_registry'))
    parser.add_argument('--provider', choices=('omniroute', 'anthropic', 'claude-cli'), default='omniroute')
    parser.add_argument('--model')
    parser.add_argument('--max-experiments', type=int, default=DEFAULT_BUDGET['max_experiments'])
    parser.add_argument('--once', action='store_true', help='una estrategia, un experimento')
    parser.add_argument('--inspect', action='store_true')
    args = parser.parse_args()
    if args.inspect or not args.once:
        print(json.dumps(inspect(args.base), indent=2, ensure_ascii=False))
        raise SystemExit(0)
    if not str(args.base.resolve()).startswith('/opt/SQX-headless/import/'):
        parser.error('El recálculo nativo solo se ejecuta en la VPS bajo /opt/SQX-headless/import/')
    if not args.template:
        parser.error('--template es obligatorio con --once')
    import fcntl
    args.base.mkdir(parents=True, exist_ok=True)
    with (args.base / 'service.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({'state': 'SKIPPED', 'reason': 'Otra ejecución del servicio está en curso'}))
            raise SystemExit(0)
        result = run_once(args.base, args.template, args.registry, debate.make_provider(args.provider, args.model),
                          str(args.base / 'strategies'), {'max_experiments': args.max_experiments})
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
