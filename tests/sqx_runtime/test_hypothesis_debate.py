"""Pruebas del debate de agentes con respuestas grabadas (sin red) sobre la evidencia real EW."""
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
FINAL_ZIP = EVIDENCE / 'ew_improvement_final_20260906.zip'
SL_DIR = 'ew_native_sl_retest_20260906/'

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


contract_module = module('sqx_strategy_contract', 'sqx_strategy_contract.py')
diagnosis_module = module('sqx_trade_diagnosis', 'sqx_trade_diagnosis.py')
mutations = module('sqx_variant_mutations', 'sqx_variant_mutations.py')
engine = module('sqx_native_improvement', 'sqx_native_improvement.py')
cycle = module('sqx_improvement_cycle', 'sqx_improvement_cycle.py')
debate = module('sqx_hypothesis_debate', 'sqx_hypothesis_debate.py')


def extract_sl_experiment(directory: Path) -> Path:
    with zipfile.ZipFile(FINAL_ZIP) as archive:
        for info in archive.infolist():
            if info.filename.startswith(SL_DIR) and not info.is_dir():
                target = directory / info.filename[len(SL_DIR):]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info))
    return directory


def make_cycle(directory: Path) -> Path:
    experiment = extract_sl_experiment(directory / 'evidence')
    root = directory / 'cycle'
    root.mkdir()
    contract = cycle.step_contract(root, experiment / 'input' / 'Strategy 1.1.27_BASE.sqx')
    cycle.step_diagnose(root, contract, experiment / 'Strategy 1.1.27_BASE_orders.csv', 'FRESH_RETEST')
    cycle.write_json(root / 'criteria.json', {**cycle.DEFAULT_CRITERIA, 'registered_utc': cycle.now()})
    cycle.write_json(root / 'explored.json', {'variants': {}, 'experiments': []})
    return root


def proposal(pid, changes, **extra):
    base = {'id': pid, 'title': f'Propuesta {pid}', 'problem': 'PT_RARELY_HIT en IS y OOS', 'evidence_codes': ['PT_RARELY_HIT'],
            'mechanism': 'Objetivo más cercano', 'change': 'PT × 0,75', 'changes': changes, 'expected': 'Más cierres por objetivo',
            'destination_expectation': {'fondeo': 'sube objetivo 5d', 'ultra': 'reduce cola'}, 'acceptance': 'DEV_FAVORABLE_RELEVANT',
            'risks': 'recorta ganadoras', 'confidence': 'media'}
    base.update(extra)
    return base


class MutableCatalogue(unittest.TestCase):
    def test_catalogue_and_generic_change_on_real_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = extract_sl_experiment(Path(directory))
            rules = contract_module.read_archive(experiment / 'input' / 'Strategy 1.1.27_BASE.sqx')['strategy_Portfolio.xml']
        catalogue = mutations.mutable_parameters(rules)
        keys = {(c['key'], c['current']) for c in catalogue}
        self.assertIn(('BarsValid', '4'), keys)
        self.assertIn(('Period', '188'), keys)
        bars = next(c for c in catalogue if c['key'] == 'BarsValid' and c['current'] == '4')
        variant = mutations.build_variant(rules, [{'param_path': bars['path'], 'value': '8'}])
        self.assertEqual(variant['changes'][0]['after'], '8')
        self.assertEqual(len(variant['comparison']['changed_params']), 1)
        with self.assertRaisesRegex(ValueError, 'entero'):
            mutations.build_variant(rules, [{'param_path': bars['path'], 'value': '8.5'}])
        with self.assertRaisesRegex(ValueError, 'no mutable'):
            mutations.build_variant(rules, [{'param_path': 'StrategyFile/inexistente', 'value': '1'}])


class OmnirouteProviderContract(unittest.TestCase):
    """El proveedor del sistema pide un modelo virtual por tarea y cae al alias por defecto si no existe."""

    def test_task_alias_then_default_alias_on_unknown_model(self):
        provider = debate.OmnirouteProvider(url='https://omniroute.example/pro/omniroute/api', default_model='auto/best-reasoning', insecure=True)
        calls = []

        def fake_post(payload):
            calls.append(payload['model'])
            if payload['model'].startswith('ultrarentable-'):
                # Respuesta real del omnirouter cuando el alias no existe (2026-09-06).
                raise provider.request.HTTPError(provider.url, 401, 'unauthorized', {}, io.BytesIO(b'{"error":{"message":"No active credentials for provider: ultrarentable-mejora-proponente."}}'))
            return {'body': {'model': 'gemini-3-flash', 'choices': [{'message': {'content': '{"analysis": "x", "proposals": [], "capability_gaps": []}'}}],
                             'usage': {'prompt_tokens': 10, 'completion_tokens': 5}}, 'decision': 'strategy=auto; provider=antigravity'}
        provider._post = fake_post
        result = provider.complete('proponente_salidas_riesgo', 'sistema', 'usuario', debate.PROPOSER_SCHEMA)
        self.assertEqual(calls, ['ultrarentable-mejora-proponente', 'auto/best-reasoning'])
        self.assertEqual(result['data']['proposals'], [])
        self.assertIn('(fallback)', result['model'])
        self.assertIn('HTTP 401', result['fallback_reason'])
        self.assertEqual(result['routing_decision'], 'strategy=auto; provider=antigravity')

    def test_invalid_json_is_retried_then_rejected(self):
        provider = debate.OmnirouteProvider(url='https://omniroute.example/pro/omniroute/api', default_model='auto/best-reasoning', insecure=True)
        provider._post = lambda payload: {'body': {'choices': [{'message': {'content': 'no soy json'}}]}, 'decision': None}
        with self.assertRaisesRegex(RuntimeError, 'no devolvió JSON'):
            provider.complete('critico', 'sistema', 'usuario', debate.CRITIC_SCHEMA)


class HypothesisDebate(unittest.TestCase):
    def test_replay_debate_validates_selects_and_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_cycle(Path(directory))
            good = proposal('PT_MAS_CERCA', [{'direction': 'long', 'exit': 'profit_target', 'value': '1.5'},
                                             {'direction': 'short', 'exit': 'profit_target', 'value': '1.8'}])
            noop = proposal('NULO', [{'direction': 'long', 'exit': 'stop_loss', 'value': '90'}])
            unsupported = proposal('IMPOSIBLE', [{'param_path': 'StrategyFile/nada', 'value': '3'}])
            refuted = proposal('SL_CENIDO', [{'direction': 'long', 'exit': 'stop_loss', 'value': '60'}])
            responses = {
                'proponente_salidas_riesgo': {'analysis': 'lente salidas', 'proposals': [good, noop], 'capability_gaps': ['filtro de lunes']},
                'proponente_estructura_frecuencia': {'analysis': 'lente estructura', 'proposals': [unsupported, refuted], 'capability_gaps': []},
                'critico': {'verdicts': [
                    {'id': 'PT_MAS_CERCA_sal1', 'verdict': 'ACEPTAR', 'reasons': ['apoyo en ambas muestras'], 'overfitting_risk': 'medio', 'revised_acceptance': 'igual'},
                    {'id': 'NULO_sal2', 'verdict': 'REFUTAR', 'reasons': ['no aplicable'], 'overfitting_risk': 'bajo', 'revised_acceptance': ''},
                    {'id': 'IMPOSIBLE_est1', 'verdict': 'REFUTAR', 'reasons': ['no aplicable'], 'overfitting_risk': 'bajo', 'revised_acceptance': ''},
                    {'id': 'SL_CENIDO_est2', 'verdict': 'REFUTAR', 'reasons': ['SL_HIT_SHARE_HIGH solo en OOS'], 'overfitting_risk': 'alto', 'revised_acceptance': ''},
                ], 'general_objections': ['muestra OOS pequeña']},
                'arbitro': {'selected_ids': ['PT_MAS_CERCA_sal1', 'SL_CENIDO_est2', 'NULO_sal2'], 'rationale': 'una sola aplicable y no refutada',
                            'dissent': ['el proponente 2 discrepa del crítico sobre el stop'], 'next_round_if_all_fail': 'probar lado de entrada'},
            }
            summary = debate.run_debate(root, debate.ReplayProvider(responses), max_variants=2)
            hypotheses = cycle.read_json(root / 'debate' / 'hypotheses.json')
            self.assertEqual([h['id'] for h in hypotheses['hypotheses']], ['PT_MAS_CERCA_sal1'])
            self.assertEqual(summary['search_budget'], {'proposed': 4, 'applicable': 2, 'refuted_by_critic': 3, 'selected': 1, 'previously_tested': 0})
            by_id = {p['id']: p for p in summary['proposals']}
            self.assertFalse(by_id['NULO_sal2']['applicable'])
            self.assertIn('no altera nada', by_id['NULO_sal2']['validation_error'])
            self.assertFalse(by_id['IMPOSIBLE_est1']['applicable'])
            self.assertTrue(by_id['SL_CENIDO_est2']['applicable'])
            self.assertFalse(by_id['SL_CENIDO_est2']['selected'])
            self.assertEqual(summary['dissent'], ['el proponente 2 discrepa del crítico sobre el stop'])
            self.assertEqual(summary['capability_gaps'], ['filtro de lunes'])
            for role in ('proponente_salidas_riesgo', 'proponente_estructura_frecuencia', 'critico', 'arbitro'):
                self.assertTrue((root / 'debate' / f'{role}.json').exists())
            intervenciones = cycle.read_json(root / 'debate' / 'intervenciones.json')
            self.assertEqual(len(intervenciones['intervenciones']), 4)
            # Las hipótesis del debate entran en el ciclo como fuente AGENT_DEBATE y se construyen de verdad.
            contract = cycle.read_json(root / 'contract.json')
            diagnosis = cycle.read_json(root / 'diagnosis_base.json')
            plan = cycle.step_plan(root, contract, diagnosis, {}, hypotheses_path=root / 'debate' / 'hypotheses.json')
            self.assertEqual(plan['hypothesis_source'], 'AGENT_DEBATE')
            self.assertEqual([h['status'] for h in plan['hypotheses']], ['PLANNED'])
            self.assertEqual(plan['hypotheses'][0]['changes'][0]['after']['Value'], '1.5')

    def test_explored_variant_is_not_selected_again(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_cycle(Path(directory))
            experiment = Path(directory) / 'evidence'
            rules = contract_module.read_archive(experiment / 'input' / 'Strategy 1.1.27_BASE.sqx')['strategy_Portfolio.xml']
            same = mutations.build_variant(rules, [{'direction': 'long', 'exit': 'stop_loss', 'value': '81'}])
            cycle.write_json(root / 'explored.json', {'variants': {same['semantic_rules_sha256']: {'hypothesis': 'EXIT90', 'class': 'HISTORICAL_FIT_ONLY'}}, 'experiments': []})
            again = proposal('SL81', [{'direction': 'long', 'exit': 'stop_loss', 'value': '81'}])
            responses = {
                'proponente_salidas_riesgo': {'analysis': '', 'proposals': [again], 'capability_gaps': []},
                'proponente_estructura_frecuencia': {'analysis': '', 'proposals': [], 'capability_gaps': []},
                'critico': {'verdicts': [{'id': 'SL81_sal1', 'verdict': 'ACEPTAR', 'reasons': [], 'overfitting_risk': 'bajo', 'revised_acceptance': ''}], 'general_objections': []},
                'arbitro': {'selected_ids': ['SL81_sal1'], 'rationale': '', 'dissent': [], 'next_round_if_all_fail': ''},
            }
            summary = debate.run_debate(root, debate.ReplayProvider(responses))
            self.assertEqual(summary['search_budget']['selected'], 0)
            self.assertIn('ya explorada', summary['proposals'][0]['validation_error'])
            self.assertEqual(summary['search_budget']['previously_tested'], 1)


if __name__ == '__main__':
    unittest.main()
