"""Pruebas del servicio autónomo: cola, presupuesto, reconciliación y estados (sin SQX ni red)."""
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'scripts' / 'herramientas'
EVIDENCE = ROOT / 'orchestration/results/codex/SQX_NATIVE_IMPROVEMENT_20260905'
SEARCH_ZIP = EVIDENCE / 'ew_native_search_evidence_20260906.zip'

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


for name in ('sqx_strategy_contract', 'sqx_trade_diagnosis', 'sqx_variant_mutations', 'sqx_native_improvement',
             'sqx_variant_evaluation', 'sqx_fixed_hypotheses_scaffold', 'sqx_improvement_cycle', 'sqx_hypothesis_debate'):
    module(name, name + '.py')
service = module('sqx_improvement_service', 'sqx_improvement_service.py')
mutations = sys.modules['sqx_variant_mutations']
evaluation = sys.modules['sqx_variant_evaluation']
cycle = sys.modules['sqx_improvement_cycle']


def variant_archive(source_bytes: bytes, changes: list) -> bytes:
    """Un .sqx con las reglas mutadas (simula la variante recalculada que SQX deja en retested/)."""
    with zipfile.ZipFile(io.BytesIO(source_bytes)) as archive:
        payload = {n: archive.read(n) for n in archive.namelist()}
    payload['strategy_Portfolio.xml'] = mutations.build_variant(payload['strategy_Portfolio.xml'], changes)['rules']
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in payload.items():
            archive.writestr(name, data)
    return buffer.getvalue()


def real_source_bytes():
    with zipfile.ZipFile(SEARCH_ZIP) as archive:
        return archive.read('ew_native_builder_20260906/selected/Strategy 1.1.27.sqx')


def evaluated(classes, accepted=()):
    def runner(base, entry, template, registry, provider, remote_root):
        cycle_dir = base / 'strategies' / entry['slug'] / f"ciclo_{len(entry['experiments']) + 1:02d}"
        cycle_dir.mkdir(parents=True, exist_ok=True)
        (cycle_dir / 'entrega.json').write_text(json.dumps({'fake': True}), encoding='utf-8')
        return {'outcome': 'EVALUATED', 'cycle': str(cycle_dir), 'project': 'UR_IMPROVE_TEST', 'classes': classes,
                'accepted_for_validation': list(accepted), 'cost': None, 'entrega': str(cycle_dir / 'entrega.json')}
    return runner


class ServiceQueue(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.base = Path(self.directory.name) / 'mejora'
        (self.base / 'inbox').mkdir(parents=True)
        (self.base / 'inbox' / 'Strategy 1.1.27.sqx').write_bytes(real_source_bytes())
        (self.base / 'inbox' / 'Strategy 1.1.27.json').write_text(json.dumps({'origin': 'prueba', 'destino': 'fondeo'}), encoding='utf-8')
        (self.base / 'inbox' / 'roto.sqx').write_bytes(b'no es un zip')
        self.template = Path(self.directory.name) / 'template.cfx'
        self.registry = Path(self.directory.name) / 'registry'

    def tearDown(self):
        self.directory.cleanup()

    def run_service(self, runner, budget=None):
        return service.run_once(self.base, self.template, self.registry, service.debate.ReplayProvider({}),
                                str(self.base / 'strategies'), budget, experiment_runner=runner)

    def test_ingest_moves_sources_and_rejects_corrupt_input(self):
        status = self.run_service(evaluated({'v': 'INCONCLUSIVE'}))
        queue = service.Queue(self.base).data['strategies']
        self.assertEqual(sorted(e['state'] for e in queue.values()), ['IN_PROGRESS', 'REJECTED_INPUT'])
        good = next(e for e in queue.values() if e['state'] == 'IN_PROGRESS')
        self.assertEqual(good['name'], 'Strategy 1.1.27')
        self.assertEqual(good['symbol'], '@EW')
        self.assertEqual(good['origin'], {'origin': 'prueba', 'destino': 'fondeo'})
        self.assertTrue(Path(good['source']).exists())
        self.assertFalse((self.base / 'inbox' / 'Strategy 1.1.27.sqx').exists())
        self.assertEqual(status['state'], 'EXPERIMENT_DONE')
        self.assertEqual(len(good['experiments']), 1)
        self.assertTrue((self.base / 'status.json').exists())

    def test_budget_exhausts_after_max_experiments_without_progress(self):
        for _ in range(3):
            self.run_service(evaluated({'v': 'INCONCLUSIVE'}), {'max_experiments': 3})
        good = next(e for e in service.Queue(self.base).data['strategies'].values() if e['name'] == 'Strategy 1.1.27')
        self.assertEqual(good['state'], 'EXHAUSTED')
        self.assertEqual(len(good['experiments']), 3)
        idle = self.run_service(evaluated({'v': 'INCONCLUSIVE'}), {'max_experiments': 3})
        self.assertEqual(idle['state'], 'IDLE')

    def test_relevant_variant_becomes_candidate_and_goes_to_outbox(self):
        self.run_service(evaluated({'v': 'DEV_FAVORABLE_RELEVANT'}, accepted=['v']))
        good = next(e for e in service.Queue(self.base).data['strategies'].values() if e['name'] == 'Strategy 1.1.27')
        self.assertEqual(good['state'], 'CANDIDATE_FOR_VALIDATION')
        self.assertEqual(len(list((self.base / 'outbox').glob('*_entrega.json'))), 1)

    def test_repeated_technical_failure_stops_with_diagnosis(self):
        def failing(*args):
            raise RuntimeError('omniroute caído')
        first = self.run_service(failing, {'max_failed_attempts': 2})
        self.assertEqual(first['state'], 'EXPERIMENT_FAILED')
        self.assertEqual(first['strategy_state'], 'IN_PROGRESS')
        second = self.run_service(failing, {'max_failed_attempts': 2})
        self.assertEqual(second['strategy_state'], 'NEEDS_ATTENTION')
        good = next(e for e in service.Queue(self.base).data['strategies'].values() if e['name'] == 'Strategy 1.1.27')
        self.assertIn('omniroute caído', good['reason'])
        self.assertEqual(self.run_service(failing, {'max_failed_attempts': 2})['state'], 'IDLE')

    def test_empty_debates_exhaust_the_strategy(self):
        def empty(base, entry, *args):
            return {'outcome': 'NO_HYPOTHESES', 'cycle': 'x', 'debate': {'selected': 0}}
        self.run_service(empty, {'max_empty_debates': 2})
        self.run_service(empty, {'max_empty_debates': 2})
        good = next(e for e in service.Queue(self.base).data['strategies'].values() if e['name'] == 'Strategy 1.1.27')
        self.assertEqual(good['state'], 'EXHAUSTED')
        self.assertIn('no encuentran hipótesis', good['reason'])

    def test_duplicate_input_is_recorded_not_requeued(self):
        self.run_service(evaluated({'v': 'INCONCLUSIVE'}))
        (self.base / 'inbox' / 'Strategy 1.1.27 (copia).sqx').write_bytes(real_source_bytes())
        self.run_service(evaluated({'v': 'INCONCLUSIVE'}))
        queue = service.Queue(self.base).data['strategies']
        good = next(e for e in queue.values() if e['name'] == 'Strategy 1.1.27')
        self.assertEqual(len([e for e in queue.values() if e['state'] != 'REJECTED_INPUT']), 1)
        self.assertEqual(len(good['duplicates']), 1)


class ServiceV2(unittest.TestCase):
    """Objetivo de Emilio (2026-09-06): todas las estrategias extraídas, mejoradas todo lo posible."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.base = root / 'mejora'
        self.base.mkdir()
        self.template = root / 'template.cfx'
        self.registry = root / 'registry'
        self.registry.mkdir()
        self.source_bytes = real_source_bytes()
        # Dos rondas de preselección del generador y una entrega de fase 5, como en la VPS.
        self.round_a = root / 'fondeo' / 'preseleccion' / 'FONDEO_MNQ_H1_r6_20260906T000000Z'
        self.round_b = root / 'fondeo' / 'preseleccion' / 'FONDEO_MNQ_H1_r7_20260906T010000Z'
        self.fase5 = root / 'fondeo' / 'entrega_fase5' / 'strategies'
        for folder in (self.round_a / 'selected', self.round_b / 'selected', self.fase5):
            folder.mkdir(parents=True)
        (self.round_a / 'selected' / 'Strategy 1.1.27.sqx').write_bytes(self.source_bytes)
        (self.round_a / 'selection_output.txt').write_text(json.dumps({'files': [{'name': 'Strategy 1.1.27', 'metrics': {'Net profit (OOS)': '7706.0', 'Fitness (IS)': '0.55'}}]}), encoding='utf-8')
        self.other = variant_archive(self.source_bytes, [{'filter': 'exclude_weekdays', 'direction': 'both', 'days': ['Monday']}])
        (self.round_b / 'selected' / 'Strategy 1.1.27.sqx').write_bytes(self.other)  # mismo nombre, reglas distintas
        (self.round_b / 'selected' / 'Strategy 1.1.27 (copia).sqx').write_bytes(self.source_bytes)  # ya vista: no entra
        self.fase5_variant = variant_archive(self.source_bytes, [{'filter': 'disable_direction', 'direction': 'short'}])
        (self.fase5 / 'Strategy 9.9.9.sqx').write_bytes(self.fase5_variant)
        self.sources = [{'pattern': str(self.fase5 / '*.sqx'), 'origin': 'entrega_fase5', 'priority': 0},
                        {'pattern': str(root / 'fondeo' / 'preseleccion' / '*' / 'selected' / '*.sqx'), 'origin': 'preseleccion_generador', 'priority': 1}]

    def tearDown(self):
        self.directory.cleanup()

    def run_service(self, runner, budget=None, **kwargs):
        return service.run_once(self.base, self.template, self.registry, service.debate.ReplayProvider({}),
                                str(self.base / 'strategies'), budget, experiment_runner=runner, intake=self.sources, **kwargs)

    def queue(self):
        return service.Queue(self.base).data['strategies']

    def test_intake_copies_new_files_once_with_provenance_and_priority(self):
        status = self.run_service(evaluated({'v': 'INCONCLUSIVE'}), max_experiments_per_run=0)
        self.assertEqual(status['intaken'], 3)
        for folder in (self.round_a / 'selected', self.round_b / 'selected', self.fase5):
            self.assertTrue(list(folder.glob('*.sqx')), 'los archivos de origen se conservan')
        entries = self.queue()
        self.assertEqual(len(entries), 3)
        by_origin = {e['origin']['origin']: e for e in entries.values()}
        self.assertEqual(by_origin['entrega_fase5']['priority'], 0)
        first = next(e for e in entries.values() if e['origin'].get('round_dir', '').startswith('FONDEO_MNQ_H1_r6'))
        self.assertEqual(first['origin']['cell'], 'FONDEO_MNQ_H1')
        self.assertEqual(first['origin']['selection_metrics'], {'Net profit (OOS)': '7706.0'})
        self.assertEqual(first['lineage'], {'depth': 0, 'parent': None, 'root': first['slug']})
        again = self.run_service(evaluated({'v': 'INCONCLUSIVE'}), max_experiments_per_run=0)
        self.assertEqual(again['intaken'], 0)
        self.assertEqual(len(self.queue()), 3)

    def test_run_spreads_experiments_over_strategies_by_priority_and_attention(self):
        status = self.run_service(evaluated({'v': 'INCONCLUSIVE'}), max_experiments_per_run=2)
        self.assertEqual([r['state'] for r in status['runs']], ['EXPERIMENT_DONE'] * 2)
        worked = [r['strategy'] for r in status['runs']]
        self.assertEqual(len(set(worked)), 2)
        self.assertEqual(self.queue()[worked[0]]['origin']['origin'], 'entrega_fase5', 'la entrega de fase 5 (prioridad 0) va primero')
        second = self.run_service(evaluated({'v': 'INCONCLUSIVE'}), max_experiments_per_run=1)
        self.assertNotIn(second['runs'][0]['strategy'], worked, 'la estrategia nunca atendida va antes que las ya atendidas')
        self.assertEqual(second['queue']['by_state'], {'IN_PROGRESS': 3})

    def test_time_budget_stops_after_the_current_experiment(self):
        def slow(base, entry, *args):
            import time
            time.sleep(0.05)
            return evaluated({'v': 'INCONCLUSIVE'})(base, entry, *args)
        status = self.run_service(slow, max_experiments_per_run=5, time_budget_seconds=0.01)
        self.assertEqual(len(status['runs']), 1)
        self.assertIn('Presupuesto de tiempo', status['reason'])

    def test_budget_counts_experiments_without_progress_and_resets_on_progress(self):
        budget = {'max_experiments_without_progress': 2, 'max_experiments': 6}
        self.run_service(evaluated({'v': 'INCONCLUSIVE'}), budget, max_experiments_per_run=3)
        self.run_service(evaluated({'v': 'DEV_FAVORABLE_NOT_RELEVANT'}), budget, max_experiments_per_run=3)
        self.assertTrue(all(e['without_progress'] == 0 for e in self.queue().values()))
        self.run_service(evaluated({'v': 'REJECTED_WORSE'}), budget, max_experiments_per_run=3)
        self.run_service(evaluated({'v': 'INCONCLUSIVE'}), budget, max_experiments_per_run=3)
        states = {e['state'] for e in self.queue().values()}
        self.assertEqual(states, {'EXHAUSTED'})
        self.assertTrue(all('sin progreso' in e['reason'] for e in self.queue().values()))
        self.assertTrue(all(len(e['experiments']) == 4 for e in self.queue().values()), 'el tope duro no interfiere')

    def accepting_runner(self, changes, evidence='MODERATE'):
        """Runner que deja una variante recalculada real (reglas mutadas) y sus órdenes, como hace SQX."""
        def runner(base, entry, template, registry, provider, remote_root):
            cycle_dir = base / 'strategies' / entry['slug'] / f"ciclo_{len(entry['experiments']) + 1:02d}"
            (cycle_dir / 'experiment' / 'retested').mkdir(parents=True, exist_ok=True)
            name = f"{entry['name']}_VAR"
            source = Path(entry['source']).read_bytes()
            (cycle_dir / 'experiment' / 'retested' / f'{name}.sqx').write_bytes(variant_archive(source, changes))
            (cycle_dir / 'experiment' / f'{name}_orders.csv').write_text('ticket,type\n1,1\n', encoding='utf-8')
            (cycle_dir / 'entrega.json').write_text(json.dumps({'fake': True}), encoding='utf-8')
            registry.mkdir(exist_ok=True)
            cycle.write_json(registry / f"{entry['semantic_rules_sha256']}.json",
                             {'variants': {'abc': {'label': 'VAR', 'class': 'DEV_FAVORABLE_RELEVANT', 'changes': changes}}, 'experiments': []})
            return {'outcome': 'EVALUATED', 'cycle': str(cycle_dir), 'project': f"UR_IMPROVE_{entry['slug'].upper()}",
                    'classes': {name: 'DEV_FAVORABLE_RELEVANT'}, 'accepted_for_validation': [name],
                    'oos_evidence': {name: evidence}, 'cost': None, 'entrega': str(cycle_dir / 'entrega.json')}
        return runner

    def test_accepted_variant_continues_as_a_child_with_stricter_evidence(self):
        self.sources = [self.sources[0]]  # solo la entrega de fase 5 para seguir un único linaje
        depth_cap = {'max_lineage_depth': 2}  # el presupuesto se fija al crear cada entrada y las hijas lo heredan
        first = self.run_service(self.accepting_runner([{'direction': 'long', 'exit': 'profit_target', 'value': '2.5'}]), depth_cap, max_experiments_per_run=1)
        run = first['runs'][0]
        parent = self.queue()[run['strategy']]
        self.assertEqual(parent['state'], 'IMPROVED_CONTINUED')
        self.assertIsNotNone(run['child'])
        child = self.queue()[run['child']]
        self.assertEqual(child['lineage'], {'depth': 1, 'parent': parent['slug'], 'root': parent['slug']})
        self.assertEqual(child['state'], 'QUEUED')
        self.assertLess(child['priority'], parent['priority'])
        self.assertEqual(child['budget']['required_oos_evidence'], 'MODERATE')
        self.assertNotEqual(child['semantic_rules_sha256'], parent['semantic_rules_sha256'])
        self.assertEqual(len(list((self.base / 'outbox').glob('*_entrega.json'))), 1)
        folder = self.base / 'strategies' / child['slug']
        orders, provenance = service.base_orders_for(folder, child)
        self.assertEqual(orders.name, 'orders_fresh.csv')
        self.assertTrue(provenance.startswith('FRESH_RETEST_UR_IMPROVE_'))
        explored = service.explored_for(child, self.registry, service.Queue(self.base))
        self.assertEqual([v['inherited_from'] for v in explored['variants'].values()], [parent['slug']])
        # Segunda generación: exige evidencia STRONG; tercera: tope del linaje → candidata sin hija.
        # La extraída de fase 5 tiene los cortos desactivados: la segunda generación cambia el lado largo.
        second = self.run_service(self.accepting_runner([{'direction': 'long', 'exit': 'trailing_stop', 'value': '60'}]), depth_cap, max_experiments_per_run=1)
        grandchild = self.queue()[second['runs'][0]['child']]
        self.assertEqual((grandchild['lineage']['depth'], grandchild['budget']['required_oos_evidence']), (2, 'STRONG'))
        third = self.run_service(self.accepting_runner([{'filter': 'hour_range', 'direction': 'long', 'from': 9, 'to': 14}]),
                                 depth_cap, max_experiments_per_run=1)
        self.assertEqual(third['runs'][0]['strategy'], grandchild['slug'])
        self.assertEqual(self.queue()[grandchild['slug']]['state'], 'CANDIDATE_FOR_VALIDATION')
        self.assertIn('Profundidad máxima', self.queue()[grandchild['slug']]['reason'])
        self.assertIsNone(third['runs'][0]['child'])

    def test_identical_recalculated_variant_does_not_spawn_a_lineage(self):
        self.sources = [self.sources[0]]
        def same_rules(base, entry, template, registry, provider, remote_root):
            cycle_dir = base / 'strategies' / entry['slug'] / 'ciclo_01'
            (cycle_dir / 'experiment' / 'retested').mkdir(parents=True, exist_ok=True)
            name = f"{entry['name']}_VAR"
            (cycle_dir / 'experiment' / 'retested' / f'{name}.sqx').write_bytes(Path(entry['source']).read_bytes())
            (cycle_dir / 'experiment' / f'{name}_orders.csv').write_text('ticket\n', encoding='utf-8')
            (cycle_dir / 'entrega.json').write_text('{}', encoding='utf-8')
            return {'outcome': 'EVALUATED', 'cycle': str(cycle_dir), 'project': 'P', 'classes': {name: 'DEV_FAVORABLE_RELEVANT'},
                    'accepted_for_validation': [name], 'oos_evidence': {name: 'STRONG'}, 'cost': None, 'entrega': str(cycle_dir / 'entrega.json')}
        status = self.run_service(same_rules, max_experiments_per_run=1)
        self.assertIsNone(status['runs'][0]['child'])
        self.assertEqual(status['runs'][0]['strategy_state'], 'CANDIDATE_FOR_VALIDATION')
        self.assertEqual(len(self.queue()), 1)


class EvidenceByDepth(unittest.TestCase):
    def test_strong_evidence_required_rejects_moderate(self):
        metrics = lambda net, pf, rd: {'net': net, 'profit_factor': pf, 'ret_dd': rd, 'trades': 100, 'drawdown': 1000.0}
        base = {'IS': metrics(10000, 1.5, 2.0), 'OOS': metrics(3000, 1.3, 1.2)}
        better = {'IS': metrics(12000, 1.7, 2.5), 'OOS': metrics(3600, 1.45, 1.5)}
        def screen(target, breach):
            return {'PROV_50K_OBJ6_TRAIL4': {'horizons': {'5': {'target_rate': target, 'breach_rate': breach}}}}
        base_diag = {'samples': {p: {'exam_screen_provisional': screen(0.05, 0.05), 'r_multiples': {'available': False}} for p in ('IS', 'OOS')}}
        var_diag = {'samples': {p: {'exam_screen_provisional': screen(0.12, 0.05), 'r_multiples': {'available': False}} for p in ('IS', 'OOS')}}
        orders = {'orders_identical': False, 'shared_with_different_outcome': 10, 'only_in_base': 0, 'only_in_variant': 0}
        moderate = {'days_changed': 20, 'evidence_strength': 'MODERATE', 'IS': {}, 'OOS': {'evidence_strength': 'MODERATE'}}
        default = evaluation.classify('v', base, better, base_diag, var_diag, orders, moderate, evaluation.DEFAULT_CRITERIA, 'RULES_CHANGED')
        self.assertEqual(default['class'], 'DEV_FAVORABLE_RELEVANT')
        strict = {**evaluation.DEFAULT_CRITERIA, 'required_oos_evidence': 'STRONG'}
        result = evaluation.classify('v', base, better, base_diag, var_diag, orders, moderate, strict, 'RULES_CHANGED')
        self.assertEqual(result['class'], 'INCONCLUSIVE')
        self.assertIn('exigida: STRONG', result['reason'])
        strong = {**moderate, 'OOS': {'evidence_strength': 'STRONG'}}
        self.assertEqual(evaluation.classify('v', base, better, base_diag, var_diag, orders, strong, strict, 'RULES_CHANGED')['class'],
                         'DEV_FAVORABLE_RELEVANT')


if __name__ == '__main__':
    unittest.main()
