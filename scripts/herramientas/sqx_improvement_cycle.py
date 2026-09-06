"""Ciclo de mejora de una estrategia: contrato → diagnóstico → hipótesis → variantes
→ recálculo nativo en SQX → comparación emparejada → clasificación → entrega.

Cada paso deja un archivo JSON en el directorio del ciclo y puede repetirse sin
rehacer lo ya hecho. El recálculo solo se ejecuta en la VPS (usa el motor
sqx_native_improvement ya desplegado). Nada de lo que produce este módulo
acredita rentabilidad futura ni aprobación de un examen.

Destinos: Fondeo (cribado provisional de examen en 1–5 días) y Ultra
(exploratorio: convexidad de los múltiplos R). Los criterios se registran ANTES
de recalcular (criterios.json) y no se cambian después de ver los resultados.

Solo biblioteca estándar.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import statistics
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sqx_native_improvement as engine  # noqa: E402
import sqx_strategy_contract as contract_module  # noqa: E402
import sqx_trade_diagnosis as diagnosis_module  # noqa: E402
import sqx_variant_mutations as mutations  # noqa: E402
import sqx_variant_evaluation as evaluation_module  # noqa: E402
import sqx_fixed_hypotheses_scaffold as scaffold  # noqa: E402
from sqx_variant_evaluation import (  # noqa: E402,F401  (re-exportado: política de evaluación en su propio módulo)
    CLASSES, DEFAULT_CRITERIA, better, classify, compare_orders, metrics_rows, paired_days, rate,
    step_evaluate, variant_label,
)
from sqx_fixed_hypotheses_scaffold import HYPOTHESIS_LIBRARY, hypothesis_changes  # noqa: E402,F401


SCHEMA = 'ultrarentable.improvement_cycle.v1'
def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data):
    engine.atomic_report(path, data)


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def rules_of(archive: Path) -> bytes:
    with zipfile.ZipFile(archive) as z:
        return z.read('strategy_Portfolio.xml')


# ---------------------------------------------------------------- pasos 1-2

def step_contract(cycle: Path, source: Path, origin: dict | None = None) -> dict:
    contract = contract_module.extract_contract(source, origin)
    write_json(cycle / 'contract.json', contract)
    return contract


def export_inherited_orders(source: Path, output: Path) -> dict:
    """Órdenes heredadas del archivo (backtest del generador). Solo VPS (java)."""
    java = Path('/opt/SQX-headless/j64/bin/java')
    reader = Path(engine.__file__).with_name('ExportNativeOrders.java')
    if not java.exists():
        raise RuntimeError('La exportación de órdenes heredadas requiere el runtime Java de SQX (VPS)')
    subprocess.run([str(java), '--class-path', '/opt/SQX-headless/internal/libs/*', str(reader),
                    str(source), str(output)], check=True, capture_output=True, text=True, timeout=60)
    return {'orders_csv': str(output), 'orders_sha256': engine.sha(output.read_bytes()),
            'provenance': 'INHERITED_FROM_SOURCE_ARCHIVE_NOT_FRESH_RETEST'}


def step_diagnose(cycle: Path, contract: dict, orders: Path, provenance: str) -> dict:
    diagnosis = diagnosis_module.diagnose(orders, contract)
    diagnosis['orders_provenance'] = provenance
    diagnosis['orders_sha256'] = engine.sha(Path(orders).read_bytes())
    sizes = set()
    for sample in diagnosis['samples'].values():
        sizes.update(sample['summary'].get('sizes', []) or [])
    if contract['sizing'].get('method') == 'FixedSize' and contract['sizing']['params'].get('Size') == '1':
        from zoneinfo import ZoneInfo
        zone = ZoneInfo(diagnosis['timezone'])
        trades = diagnosis_module.load_orders(orders, zone, contract['market'].get('declared_timezone'))
        calendars = diagnosis_module.sample_calendars(contract)
        exposure = {}
        for label in ('IS', 'OOS'):
            selected = [t for t in trades if t['sample'] == label]
            days = diagnosis_module.daily_results(selected, zone, calendars[label])
            exposure[label] = diagnosis_module.exposure_study(days)
        diagnosis['exposure_study_fondeo'] = exposure
    write_json(cycle / 'diagnosis_base.json', diagnosis)
    return diagnosis


# ------------------------------------------------------------------- paso 3

def consistent_findings(diagnosis: dict) -> dict:
    """Códigos de hallazgo presentes en IS y en OOS (evita hipótesis de una sola muestra)."""
    by_sample = {}
    for f in diagnosis['findings']:
        by_sample.setdefault(f['code'], set()).add(f['sample'])
    return {code: sorted(samples) for code, samples in by_sample.items()}


def external_hypotheses(path: Path) -> dict:
    """Hipótesis propuestas por agentes (debate por estrategia), no por la biblioteca fija.

    Formato: lista de objetos {id, title, problem, change, expected, changes:[{direction, exit,
    value|atr_period}], destination_expectation?, evidence?}. El programa solo valida que el
    cambio es aplicable y exacto; la decisión de qué probar es de los agentes.
    """
    items = read_json(path)
    if isinstance(items, dict):
        items = items.get('hypotheses', [])
    library = {}
    for item in items:
        hid = str(item['id'])
        if not hid or 'changes' not in item or not item['changes']:
            raise ValueError(f'Hipótesis externa sin cambios concretos: {item}')
        library[hid] = {**item, 'requires': [], 'source': 'AGENT_DEBATE'}
    return library


def step_plan(cycle: Path, contract: dict, diagnosis: dict, explored: dict, criteria=None, max_variants=2,
              hypotheses_path: Path | None = None) -> dict:
    """Hipótesis con criterios pre-registrados.

    Con `hypotheses_path` las hipótesis vienen del debate de agentes (fuente prevista por
    Emilio, 2026-09-06); la biblioteca fija queda solo como andamio de pruebas del mecanismo.
    """
    criteria = criteria or DEFAULT_CRITERIA
    rules = rules_of(Path(contract['provenance']['archive_path']))
    present = consistent_findings(diagnosis)
    hints = contract['destination_hints']
    destinations = {
        'fondeo': {'evaluate': hints['fondeo']['eligible_for_provisional_exam_screen'],
                   'mode': 'PROVISIONAL_SCENARIOS', 'reason': hints['fondeo']['note']},
        'ultra': {'evaluate': hints['ultra']['timeframe_in_canonical_set'], 'mode': 'EXPLORATORY', 'reason': hints['ultra']['note']},
    }
    library = external_hypotheses(hypotheses_path) if hypotheses_path else HYPOTHESIS_LIBRARY
    candidates = []
    for hid, spec in library.items():
        codes = list(spec['requires']) + list(spec.get('requires_any', [])) + list(spec.get('supporting', []))
        support = {code: present.get(code, []) for code in codes}
        both = all(len(present.get(code, [])) == 2 for code in spec['requires'])
        if spec.get('requires_any'):
            both = both and any(len(present.get(code, [])) == 2 for code in spec['requires_any'])
        if not both:
            candidates.append({'id': hid, 'status': 'NOT_SUPPORTED_IN_BOTH_SAMPLES', 'support': support})
            continue
        try:
            changes = spec['changes'] if spec.get('source') == 'AGENT_DEBATE' else hypothesis_changes(hid, rules)
            variant = mutations.build_variant(rules, changes)
        except ValueError as error:
            candidates.append({'id': hid, 'status': 'NOT_APPLICABLE', 'support': support, 'reason': str(error)})
            continue
        semantic = variant['semantic_rules_sha256']
        if semantic in explored.get('variants', {}):
            candidates.append({'id': hid, 'status': 'EXPLORED_BEFORE', 'support': support,
                               'previous': explored['variants'][semantic]})
            continue
        candidates.append({'id': hid, 'status': 'PLANNED', 'support': support, **spec,
                           'changes': variant['changes'], 'semantic_rules_sha256': semantic})
    planned = [c for c in candidates if c['status'] == 'PLANNED'][:max_variants]
    for index, c in enumerate(planned, 1):
        label = re.sub(r'[^A-Z0-9_]', '', c['id'].upper().replace('H_', 'V'))[:30] or f'V{index}'
        c['label'] = label if re.fullmatch(r'[A-Z][A-Z0-9_]{1,30}', label) else f'V{index}'
    plan = {
        'schema': 'ultrarentable.improvement_plan.v1', 'generated_utc': now(),
        'hypothesis_source': 'AGENT_DEBATE' if hypotheses_path else 'FIXED_LIBRARY_SCAFFOLD',
        'strategy': contract['identity']['name'], 'semantic_rules_sha256': contract['identity']['semantic_rules_sha256'],
        'destinations': destinations, 'findings_by_sample': present,
        'hypotheses': candidates, 'planned_labels': [c['label'] for c in planned],
        'unsupported_hypothesis_types': [
            'Filtros de horario o día (requieren añadir bloques de condición; no implementado en esta versión).',
            'Cambios de entrada (BarsValid, periodos de indicador): cambian la muestra de operaciones y exigen otra política de comparación.',
        ],
        'budget': {'max_variants_per_experiment': 2, 'max_experiments_this_phase': 2},
    }
    write_json(cycle / 'plan.json', plan)
    # Los criterios se registran una sola vez: repetir el paso no los reescribe.
    if not (cycle / 'criteria.json').exists():
        write_json(cycle / 'criteria.json', {**criteria, 'registered_utc': now(), 'plan_sha256': engine.sha((cycle / 'plan.json').read_bytes())})
    return plan


# ------------------------------------------------------------------- paso 4

def step_prepare(cycle: Path, contract: dict, plan: dict, template: Path, remote_dir: str, project: str,
                 candidates: list[dict] | None = None) -> dict:
    """Construye control + variantes y el proyecto de recálculo (motor existente).

    candidates: archivos .sqx externos (p. ej. exportados por el Improver nativo)
    que se clasifican antes de gastar un recálculo: los que solo cambian
    metadatos se rechazan aquí y no entran en el experimento.
    """
    experiment = cycle / 'experiment'
    if (experiment / 'manifest.json').exists():
        return read_json(experiment / 'manifest.json')  # Repetir el paso no rehace ni altera el experimento.
    source = Path(contract['provenance']['archive_path'])
    rules = rules_of(source)
    variants, records = {}, []
    for hypothesis in plan['hypotheses']:
        if hypothesis['status'] != 'PLANNED':
            continue
        built = mutations.build_variant(rules, [{k: c[k] for k in ('direction', 'exit', 'value', 'atr_period', 'param_path') if k in c}
                                                for c in hypothesis['changes']])
        variants[hypothesis['label']] = built['rules']
        records.append({'label': hypothesis['label'], 'hypothesis': hypothesis['id'], 'changes': built['changes'],
                        'semantic_rules_sha256': built['semantic_rules_sha256'], 'source': 'reviewed_mutation'})
    screened = []
    for candidate in candidates or []:
        comparison = contract_module.compare_rules(rules, rules_of(Path(candidate['path'])))
        entry = {'path': candidate['path'], 'label': candidate.get('label'), 'classification': comparison['classification'],
                 'changed_params': comparison['changed_params']}
        if comparison['classification'] == 'RULES_CHANGED' and candidate.get('label') and len(variants) < 2:
            variants[candidate['label']] = rules_of(Path(candidate['path']))
            records.append({'label': candidate['label'], 'hypothesis': candidate.get('hypothesis', 'EXTERNAL_CANDIDATE'),
                            'changes': comparison['changed_params'], 'semantic_rules_sha256': comparison['semantic_sha256_after'],
                            'source': 'external_candidate'})
            entry['decision'] = 'ADMITTED_TO_RETEST'
        else:
            entry['decision'] = 'REJECTED_BEFORE_RETEST' if comparison['classification'] != 'RULES_CHANGED' else 'NOT_ADMITTED_BUDGET'
        screened.append(entry)
    if not variants:
        raise ValueError('No hay variantes que recalcular')
    hypothesis_text = '; '.join(f"{r['label']}: {HYPOTHESIS_LIBRARY.get(r['hypothesis'], {}).get('change', r['hypothesis'])}" for r in records)
    manifest = engine.prepare(source, template, experiment, remote_dir, project, integer_contracts=False,
                              precision=int(contract['period'].get('test_precision') or 2),
                              custom_variants=variants, hypothesis=hypothesis_text)
    manifest['variants'] = records
    manifest['screened_candidates'] = screened
    manifest['cycle_schema'] = SCHEMA
    manifest['criteria_sha256'] = engine.sha((cycle / 'criteria.json').read_bytes())
    write_json(experiment / 'manifest.json', manifest)
    return manifest


# ------------------------------------------------------------------- paso 5

def step_run(cycle: Path) -> dict:
    """Recálculo nativo en la VPS mediante el motor existente; mide el coste."""
    manifest_path = cycle / 'experiment' / 'manifest.json'
    started = time.monotonic()
    assessment = engine.run_reviewed(manifest_path)
    elapsed = time.monotonic() - started
    log = (cycle / 'experiment' / 'native_retest.log').read_text(encoding='utf-8', errors='replace')
    import re
    native = re.search(r'TAREA TERMINADA .* en (?:(\d+) min\. )?(\d+) s\.', log)
    native_seconds = (int(native[1] or 0) * 60 + int(native[2])) if native else None
    cost = {'wall_seconds_total': round(elapsed, 1), 'native_task_seconds': native_seconds,
            'strategies_retested': len(manifest_path and read_json(manifest_path)['entries']),
            'measured_utc': now()}
    write_json(cycle / 'experiment' / 'cost.json', cost)
    return assessment


# ------------------------------------------------------------------- paso 7

def step_package(cycle: Path) -> dict:
    files = {str(p.relative_to(cycle)): engine.sha(p.read_bytes()) for p in sorted(cycle.rglob('*')) if p.is_file() and p.name != 'entrega.json'}
    contract, plan, evaluation = read_json(cycle / 'contract.json'), read_json(cycle / 'plan.json'), read_json(cycle / 'evaluation.json')
    cost = read_json(cycle / 'experiment' / 'cost.json') if (cycle / 'experiment' / 'cost.json').exists() else None
    diagnosis = read_json(cycle / 'diagnosis_base_fresh.json')
    classes = {v['name']: v['class'] for v in evaluation['variants']}
    package = {
        'schema': 'ultrarentable.improvement_delivery.v1', 'generated_utc': now(),
        'strategy': {'name': contract['identity']['name'], 'symbol': contract['market']['symbol'],
                     'timeframe': contract['market']['timeframe'], 'semantic_rules_sha256': contract['identity']['semantic_rules_sha256'],
                     'contract_state': contract['state'], 'data_provenance_state': contract['provenance']['data_provenance_state']},
        'destinations': plan['destinations'],
        'reference': evaluation['base'],
        'findings': [f for f in diagnosis['findings']],
        'hypotheses_tested': [h for h in plan['hypotheses'] if h['status'] == 'PLANNED'],
        'hypotheses_not_tested': [{k: h[k] for k in ('id', 'status') if k in h} | ({'reason': h['reason']} if 'reason' in h else {}) for h in plan['hypotheses'] if h['status'] != 'PLANNED'],
        'screened_candidates': read_json(cycle / 'experiment' / 'manifest.json').get('screened_candidates', []),
        'variants': [{'name': v['name'], 'class': v['class'], 'reason': v['reason'], 'next_action': v['next_action'],
                      'development': {'IS': v['development']['IS'], 'OOS': v['development']['OOS']},
                      'oos_evidence': v['paired_daily']['evidence_strength'], 'destinations': {
                          'fondeo': {'relevant': v['destinations']['fondeo']['relevant'], 'by_sample': v['destinations']['fondeo']['by_sample']},
                          'ultra': {'relevant': v['destinations']['ultra']['relevant'], 'by_sample': v['destinations']['ultra']['by_sample']}},
                      'metrics': v['metrics']} for v in evaluation['variants']],
        'accepted_for_validation': evaluation['accepted_for_validation'],
        'consumed_evidence': {'period': {'from': contract['period']['date_from'], 'to': contract['period']['date_to']},
                              'development_oos_ranges': contract['period']['oos_ranges'],
                              'samples': {k: diagnosis['samples'][k]['range'] for k in ('IS', 'OOS')},
                              'reserved_final_sample': None,
                              'note': 'No hay muestra final reservada en los datos actuales; cualquier validación independiente exige datos no consultados.'},
        'cost': cost, 'evidence_files': files, 'validated': False,
        'levels': {'mechanism_works': all(c != 'NO_CHANGE_RULES' for c in classes.values()),
                   'useful_progress': bool(evaluation['accepted_for_validation']),
                   'candidate_for_validation': bool(evaluation['accepted_for_validation']),
                   'validated_result': False},
    }
    write_json(cycle / 'entrega.json', package)
    return package


def update_registry(registry: Path, cycle: Path, contract: dict, evaluation: dict):
    """Registro por estrategia: hipótesis y variantes ya exploradas (evita repetir)."""
    registry.mkdir(parents=True, exist_ok=True)
    key = contract['identity']['semantic_rules_sha256']
    path = registry / f'{key}.json'
    record = read_json(path) if path.exists() else {'strategy': contract['identity']['name'], 'variants': {}, 'experiments': []}
    manifest = read_json(cycle / 'experiment' / 'manifest.json')
    variants = manifest.get('variants') or [
        # Experimentos anteriores al ciclo: identidad por reglas semánticas del archivo preparado.
        {'label': variant_label(manifest, entry['name']), 'hypothesis': manifest.get('hypothesis', 'LEGACY'),
         'semantic_rules_sha256': contract_module.semantic_rules_sha256(rules_of(cycle / 'experiment' / 'input' / entry['file']))}
        for entry in manifest['entries'][1:]]
    for variant in variants:
        result = next((v for v in evaluation['variants'] if v['name'].endswith('_' + variant['label'])), None)
        # Los agentes necesitan saber QUÉ se cambió y qué pasó, no solo la etiqueta.
        record['variants'][variant['semantic_rules_sha256']] = {
            'hypothesis': variant['hypothesis'], 'label': variant['label'], 'class': result['class'] if result else None,
            'changes': [{k: c.get(k) for k in ('direction', 'exit', 'param_path', 'value', 'before', 'after') if c.get(k) is not None}
                        for c in variant.get('changes', [])],
            'development': result['development'] if result else None,
            'oos_evidence': result['paired_daily'].get('evidence_strength') if result else None,
            'cycle': str(cycle), 'utc': now()}
    entry = {'project': manifest['project'], 'cycle': str(cycle), 'utc': now(),
             'hypothesis_source': manifest.get('recipe'), 'classes': {v['name']: v['class'] for v in evaluation['variants']}}
    # Re-evaluar un ciclo no es un experimento nuevo: se sustituye la entrada del mismo proyecto.
    record['experiments'] = [e for e in record['experiments'] if e.get('project') != entry['project']] + [entry]
    write_json(path, record)
    return record


# --------------------------------------------------------------------- CLI

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    dg = sub.add_parser('dossier', help='contrato, diagnóstico, criterios y variantes exploradas: la entrada del debate de agentes (sin SQX)')
    dg.add_argument('--source', type=Path, required=True)
    dg.add_argument('--orders', type=Path, required=True)
    dg.add_argument('--orders-provenance', default='FRESH_RETEST')
    dg.add_argument('--cycle', type=Path, required=True)
    dg.add_argument('--registry', type=Path)
    p = sub.add_parser('prepare-local', help='contrato, diagnóstico, plan, criterios y variantes (sin SQX)')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--orders', type=Path, required=True, help='CSV de órdenes de la base (fresco o heredado)')
    p.add_argument('--orders-provenance', default='FRESH_RETEST')
    p.add_argument('--template', type=Path, required=True)
    p.add_argument('--cycle', type=Path, required=True)
    p.add_argument('--remote-dir', required=True)
    p.add_argument('--project', required=True)
    p.add_argument('--registry', type=Path)
    p.add_argument('--hypotheses', type=Path, help='JSON con hipótesis propuestas por el debate de agentes (sustituye a la biblioteca fija)')
    p.add_argument('--candidate', action='append', default=[], help='label=ruta.sqx de un candidato externo a cribar')
    r = sub.add_parser('run', help='recálculo nativo (solo VPS)')
    r.add_argument('--cycle', type=Path, required=True)
    e = sub.add_parser('evaluate', help='comparación emparejada, clasificación y entrega')
    e.add_argument('--cycle', type=Path, required=True)
    e.add_argument('--registry', type=Path)
    args = parser.parse_args()
    if args.action == 'dossier':
        cycle = args.cycle
        cycle.mkdir(parents=True, exist_ok=True)
        contract = step_contract(cycle, args.source)
        if contract['state'] != 'CONTRACT_COMPLETE':
            raise SystemExit('Contrato incompleto: ' + ', '.join(contract['essentials_missing']))
        step_diagnose(cycle, contract, args.orders, args.orders_provenance)
        if not (cycle / 'criteria.json').exists():
            write_json(cycle / 'criteria.json', {**DEFAULT_CRITERIA, 'registered_utc': now()})
        key = contract['identity']['semantic_rules_sha256']
        explored = read_json(args.registry / f'{key}.json') if args.registry and (args.registry / f'{key}.json').exists() else {'variants': {}, 'experiments': []}
        write_json(cycle / 'explored.json', explored)
        print(json.dumps({'cycle': str(cycle), 'strategy': contract['identity']['name'], 'findings': len(read_json(cycle / 'diagnosis_base.json')['findings']),
                          'explored_variants': len(explored['variants']), 'next': 'sqx_hypothesis_debate.py --cycle <cycle> --provider anthropic|claude-cli'}, indent=2, ensure_ascii=False))
    elif args.action == 'prepare-local':
        cycle = args.cycle
        cycle.mkdir(parents=True, exist_ok=True)
        contract = step_contract(cycle, args.source)
        if contract['state'] != 'CONTRACT_COMPLETE':
            print(json.dumps(contract, indent=2, ensure_ascii=False))
            raise SystemExit('Contrato incompleto: ' + ', '.join(contract['essentials_missing']))
        diagnosis = step_diagnose(cycle, contract, args.orders, args.orders_provenance)
        explored = {}
        if args.registry and (args.registry / f"{contract['identity']['semantic_rules_sha256']}.json").exists():
            explored = read_json(args.registry / f"{contract['identity']['semantic_rules_sha256']}.json")
        plan = step_plan(cycle, contract, diagnosis, explored, hypotheses_path=args.hypotheses)
        candidates = []
        for item in args.candidate:
            label, path = item.split('=', 1)
            candidates.append({'label': label, 'path': path})
        manifest = step_prepare(cycle, contract, plan, args.template, args.remote_dir, args.project, candidates)
        print(json.dumps({'cycle': str(cycle), 'planned': plan['planned_labels'], 'entries': [e['name'] for e in manifest['entries']],
                          'screened_candidates': manifest['screened_candidates']}, indent=2, ensure_ascii=False))
    elif args.action == 'run':
        print(json.dumps(step_run(args.cycle), indent=2, ensure_ascii=False))
    else:
        cycle = args.cycle
        contract, criteria = read_json(cycle / 'contract.json'), read_json(cycle / 'criteria.json')
        evaluation = step_evaluate(cycle, contract, criteria)
        if args.registry:
            update_registry(args.registry, cycle, contract, evaluation)
        package = step_package(cycle)
        print(json.dumps({'variants': package['variants'], 'accepted_for_validation': package['accepted_for_validation'],
                          'levels': package['levels'], 'cost': package['cost']}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
