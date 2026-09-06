"""Pruebas del servicio autónomo: cola, presupuesto, reconciliación y estados (sin SQX ni red)."""
import importlib.util
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


if __name__ == '__main__':
    unittest.main()
