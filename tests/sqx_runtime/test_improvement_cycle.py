"""Pruebas del ciclo de mejora sobre la evidencia real EW (2026-09-06).

Usan los paquetes de evidencia conservados en el repositorio: el experimento de
stops ±10 % (control + dos variantes recalculadas en SQX) y la variante del
Improver nativo que solo cambiaba metadatos.
"""
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'scripts' / 'herramientas'
EVIDENCE = ROOT / 'orchestration/results/codex/SQX_NATIVE_IMPROVEMENT_20260905'
FINAL_ZIP = EVIDENCE / 'ew_improvement_final_20260906.zip'
SEARCH_ZIP = EVIDENCE / 'ew_native_search_evidence_20260906.zip'
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


def extract_sl_experiment(directory: Path) -> Path:
    with zipfile.ZipFile(FINAL_ZIP) as archive:
        for info in archive.infolist():
            if info.filename.startswith(SL_DIR) and not info.is_dir():
                target = directory / info.filename[len(SL_DIR):]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info))
    return directory


def search_member(name: str) -> bytes:
    with zipfile.ZipFile(SEARCH_ZIP) as archive:
        return archive.read(name)


class StrategyContract(unittest.TestCase):
    def test_real_ew_contract_is_complete_and_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = extract_sl_experiment(Path(directory))
            contract = contract_module.extract_contract(experiment / 'input' / 'Strategy 1.1.27_BASE.sqx')
        self.assertEqual(contract['state'], 'CONTRACT_COMPLETE')
        self.assertEqual(contract['market']['symbol'], '@EW')
        self.assertEqual(contract['market']['timeframe'], 'H1')
        self.assertEqual(contract['market']['resolved_timezone'], 'America/Chicago')
        self.assertEqual(contract['period']['oos_ranges'], [{'from': '2025.01.01', 'to': '2025.12.31'}])
        self.assertEqual(contract['costs']['commission_params'], {'Commission': '5.0'})
        self.assertEqual(contract['sizing']['method'], 'FixedSize')
        self.assertEqual(len(contract['rules']['entries']), 2)
        self.assertEqual({e['direction'] for e in contract['rules']['entries']}, {'long', 'short'})
        self.assertTrue(contract['destination_hints']['fondeo']['eligible_for_provisional_exam_screen'])
        self.assertEqual(contract['provenance']['data_provenance_state'], 'DECLARED_NOT_INDEPENDENTLY_VERIFIED')

    def test_missing_settings_is_reported_not_guessed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'broken.sqx'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('strategy_Portfolio.xml', '<StrategyFile><Strategy/></StrategyFile>')
            contract = contract_module.extract_contract(path)
        self.assertEqual(contract['state'], 'CONTRACT_INCOMPLETE')
        self.assertIn('archive:settings.xml', contract['essentials_missing'])

    def test_real_improver_metadata_only_variant_is_classified_as_no_change(self):
        original = search_member('ew_native_builder_20260906/selected/Strategy 1.1.27.sqx')
        improved = search_member('ew_native_improve_20260906_v2/selected/Strategy 1.1.27 - Improved 1.1.15.sqx')
        rules = []
        for payload in (original, improved):
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                rules.append(archive.read('strategy_Portfolio.xml'))
        self.assertNotEqual(rules[0], rules[1])
        result = contract_module.compare_rules(*rules)
        self.assertEqual(result['classification'], 'METADATA_ONLY_NO_BEHAVIOUR_CHANGE')
        self.assertEqual(result['changed_params'], [])

    def test_real_exit90_variant_changes_exactly_the_long_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = extract_sl_experiment(Path(directory))
            base = contract_module.read_archive(experiment / 'input' / 'Strategy 1.1.27_BASE.sqx')['strategy_Portfolio.xml']
            exit90 = contract_module.read_archive(experiment / 'input' / 'Strategy 1.1.27_EXIT90.sqx')['strategy_Portfolio.xml']
        result = contract_module.compare_rules(base, exit90)
        self.assertEqual(result['classification'], 'RULES_CHANGED')
        self.assertEqual(len(result['changed_params']), 1)
        self.assertIn('#StopLoss.StopLoss#', result['changed_params'][0]['param'])
        self.assertEqual((result['changed_params'][0]['before'], result['changed_params'][0]['after']), ('90.0', '81'))


class VariantMutations(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        experiment = extract_sl_experiment(Path(self.directory.name))
        self.rules = contract_module.read_archive(experiment / 'input' / 'Strategy 1.1.27_BASE.sqx')['strategy_Portfolio.xml']

    def tearDown(self):
        self.directory.cleanup()

    def test_profit_target_multiplier_change_is_verified(self):
        variant = mutations.build_variant(self.rules, [
            {'direction': 'long', 'exit': 'profit_target', 'value': '1.2'},
            {'direction': 'short', 'exit': 'profit_target', 'value': '1.44'}])
        self.assertEqual(len(variant['comparison']['changed_params']), 2)
        self.assertEqual(variant['changes'][0]['after']['Value'], '1.2')
        self.assertEqual(variant['changes'][0]['after']['AtrPeriod'], '20')
        self.assertNotEqual(variant['semantic_rules_sha256'], contract_module.semantic_rules_sha256(self.rules))

    def test_no_op_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no altera nada'):
            mutations.build_variant(self.rules, [{'direction': 'long', 'exit': 'stop_loss', 'value': '90'}])

    def test_duplicate_and_negative_changes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicado'):
            mutations.build_variant(self.rules, [{'direction': 'long', 'exit': 'stop_loss', 'value': '80'},
                                                 {'direction': 'long', 'exit': 'stop_loss', 'value': '70'}])
        with self.assertRaisesRegex(ValueError, 'positivos'):
            mutations.build_variant(self.rules, [{'direction': 'long', 'exit': 'stop_loss', 'value': '-5'}])

    def test_engine_prepare_accepts_custom_variants_and_keeps_control_intact(self):
        experiment = Path(self.directory.name)
        variant = mutations.build_variant(self.rules, [{'direction': 'long', 'exit': 'stop_loss', 'value': '63'}])
        output = experiment / 'prepared'
        manifest = engine.prepare(experiment / 'input' / 'Strategy 1.1.27_BASE.sqx', experiment / 'project.cfx', output,
                                  '/opt/SQX-headless/import/test_cycle/experiment', 'UR_IMPROVE_TEST_CYCLE',
                                  custom_variants={'VSL': variant['rules']}, hypothesis='prueba')
        self.assertEqual([e['name'] for e in manifest['entries']], ['Strategy 1.1.27_BASE_BASE', 'Strategy 1.1.27_BASE_VSL'])
        self.assertEqual(manifest['recipe'], 'custom_reviewed_mutation')
        base_rules = contract_module.read_archive(output / 'input' / 'Strategy 1.1.27_BASE_BASE.sqx')['strategy_Portfolio.xml']
        self.assertEqual(base_rules, self.rules)
        prepared = contract_module.read_archive(output / 'input' / 'Strategy 1.1.27_BASE_VSL.sqx')['strategy_Portfolio.xml']
        self.assertEqual(prepared, variant['rules'])
        with self.assertRaisesRegex(ValueError, 'distinct'):
            engine.prepare(experiment / 'input' / 'Strategy 1.1.27_BASE.sqx', experiment / 'project.cfx', experiment / 'again',
                           '/opt/SQX-headless/import/test_cycle/experiment', 'UR_IMPROVE_TEST_CYCLE',
                           custom_variants={'SAME': self.rules})


class TradeDiagnosis(unittest.TestCase):
    def test_real_base_orders_profile_and_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = extract_sl_experiment(Path(directory))
            contract = contract_module.extract_contract(experiment / 'input' / 'Strategy 1.1.27_BASE.sqx')
            diagnosis = diagnosis_module.diagnose(experiment / 'Strategy 1.1.27_BASE_orders.csv', contract)
        self.assertEqual(diagnosis['point_value']['point_value'], 100.0)
        self.assertTrue(diagnosis['point_value']['matches_reference_table'])
        is_sample, oos = diagnosis['samples']['IS'], diagnosis['samples']['OOS']
        self.assertEqual((is_sample['summary']['trades'], oos['summary']['trades']), (173, 56))
        self.assertEqual((is_sample['summary']['net'], oos['summary']['net']), (40503.0, 7706.0))
        self.assertEqual(is_sample['exit_efficiency']['close_types']['EOD_TIME']['trades'], 101)
        # Las marcas nativas ya son hora de bolsa: las entradas caen en la sesión regular (08–15 h Chicago).
        self.assertEqual(diagnosis['timestamp_interpretation'], 'EXCHANGE_LOCAL_AS_WRITTEN')
        hours = set(is_sample['time']['by_entry_hour_local'])
        self.assertTrue(hours <= {f'{h:02d}' for h in range(8, 16)}, hours)
        # La devolución se mide sobre ganadoras: distinta de la media que mezcla perdedoras.
        self.assertLess(is_sample['exit_efficiency']['mean_giveback_winners'], is_sample['exit_efficiency']['mean_giveback_all_with_mfe'])
        codes = {(f['code'], f['sample']) for f in diagnosis['findings']}
        self.assertIn(('TIME_EXIT_DOMINATED', 'IS'), codes)
        self.assertIn(('PT_RARELY_HIT', 'OOS'), codes)
        self.assertIn(('LOW_EXAM_TARGET_RATE_5D', 'OOS'), codes)
        self.assertIn(('LOW_FREQUENCY_FOR_SHORT_EXAM', 'IS'), codes)
        screen = oos['exam_screen_provisional']['PROV_50K_OBJ6_TRAIL4']['horizons']['5']
        self.assertEqual(screen['windows'], 257)
        self.assertLess(screen['target_rate'], 0.10)
        # Todas las operaciones IS entran en el calendario diario (ningún día perdido en silencio).
        self.assertEqual(round(sum(is_sample['daily_pl'].values()), 2), is_sample['summary']['net'])

    def test_non_final_oos_range_keeps_every_trade_in_a_calendar(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = extract_sl_experiment(Path(directory))
            contract = contract_module.extract_contract(experiment / 'input' / 'Strategy 1.1.27_BASE.sqx')
            calendars = diagnosis_module.sample_calendars({**contract, 'period': {**contract['period'], 'oos_ranges': [{'from': '2023.01.01', 'to': '2023.12.31'}]}})
            self.assertTrue(all(d.year != 2023 for d in calendars['IS']))
            self.assertTrue(all(d.year == 2023 for d in calendars['OOS']))
            self.assertEqual(len(calendars['IS']) + len(calendars['OOS']), len(diagnosis_module.weekdays_between(calendars['IS'][0], calendars['IS'][-1])))

    def test_variant_r_multiples_use_control_risk(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = extract_sl_experiment(Path(directory))
            contract = contract_module.extract_contract(experiment / 'input' / 'Strategy 1.1.27_BASE.sqx')
            base = experiment / 'Strategy 1.1.27_BASE_orders.csv'
            own = diagnosis_module.diagnose(experiment / 'Strategy 1.1.27_EXIT90_orders.csv', contract)
            referenced = diagnosis_module.diagnose(experiment / 'Strategy 1.1.27_EXIT90_orders.csv', contract, reference_orders=base)
        self.assertEqual(referenced['samples']['IS']['r_multiples']['risk_source'], 'CONTROL_REFERENCE')
        # Con el stop más ceñido, medir con su propio riesgo infla los múltiplos; con el del control no.
        self.assertGreater(own['samples']['IS']['r_multiples']['fraction_mfe_ge_2r'], referenced['samples']['IS']['r_multiples']['fraction_mfe_ge_2r'])

    def test_window_outcome_rules(self):
        scenario = {'target': 3000.0, 'max_loss': 2000.0, 'max_loss_mode': 'trailing_eod', 'daily_loss_limit': 1000.0, 'min_trading_days': 1}
        day = lambda pl, worst=0.0: {'pl': pl, 'worst_intraday_estimate': worst, 'trades': 1, 'costs': 0.0}
        self.assertEqual(diagnosis_module.window_outcome([day(1500.0), day(1600.0)], scenario)['outcome'], 'TARGET')
        self.assertEqual(diagnosis_module.window_outcome([day(-1000.0)], scenario)['outcome'], 'DAILY_LOSS_BREACH')
        self.assertEqual(diagnosis_module.window_outcome([day(-900.0), day(-900.0), day(-300.0)], scenario)['outcome'], 'MAX_LOSS_BREACH_AT_CLOSE')
        # Suelo arrastrado hasta el saldo inicial: tras +2500 el suelo sube a 0; caer a -200 rompe
        # aunque ningún día supere el límite diario.
        trailed = diagnosis_module.window_outcome([day(2500.0), day(-900.0), day(-900.0), day(-900.0)], scenario)
        self.assertEqual((trailed['outcome'], trailed['day']), ('MAX_LOSS_BREACH_AT_CLOSE', 4))
        # Sin suelo arrastrado la misma secuencia no rompe (queda en -200 sobre un suelo de -2000).
        static = {**scenario, 'max_loss_mode': 'static'}
        self.assertEqual(diagnosis_module.window_outcome([day(2500.0), day(-900.0), day(-900.0), day(-900.0)], static)['outcome'], 'NO_TARGET_NO_BREACH')
        # El límite diario se comprueba antes que el suelo.
        self.assertEqual(diagnosis_module.window_outcome([day(2500.0), day(-2100.0)], scenario)['outcome'], 'DAILY_LOSS_BREACH')
        # Un día que cierra por encima del límite diario pero cuya peor excursión lo cruzó no es un objetivo limpio.
        self.assertEqual(diagnosis_module.window_outcome([day(-900.0, worst=-1500.0), day(3900.0)], scenario)['outcome'], 'TARGET_WITH_POSSIBLE_INTRADAY_BREACH')
        screen = diagnosis_module.exam_screen({date(2026, 1, 5): day(-900.0, worst=-1500.0), date(2026, 1, 6): day(3900.0)}, [scenario | {'id': 'T'}])
        self.assertEqual(screen['T']['horizons']['2']['target_rate'], 0.0)
        self.assertEqual(screen['T']['horizons']['2']['breach_rate'], 1.0)
        self.assertEqual(diagnosis_module.window_outcome([day(500.0, worst=-2500.0)], scenario)['outcome'], 'POSSIBLE_INTRADAY_BREACH')
        self.assertEqual(diagnosis_module.window_outcome([{'pl': 0.0, 'worst_intraday_estimate': 0.0, 'trades': 0, 'costs': 0.0}], scenario)['outcome'], 'NO_TRADES')


class ImprovementCycleEvaluation(unittest.TestCase):
    def test_previous_real_stop_experiment_is_reclassified_honestly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extract_sl_experiment(root / 'experiment')
            contract = cycle.step_contract(root, root / 'experiment' / 'input' / 'Strategy 1.1.27_BASE.sqx')
            cycle.write_json(root / 'criteria.json', {**cycle.DEFAULT_CRITERIA, 'registered_utc': cycle.now()})
            cycle.write_json(root / 'plan.json', {'destinations': {}, 'hypotheses': [], 'planned_labels': []})
            evaluation = cycle.step_evaluate(root, contract, json.loads((root / 'criteria.json').read_text(encoding='utf-8')))
            package = cycle.step_package(root)
            registry = cycle.update_registry(root / 'registry', root, contract, evaluation)
        classes = {v['name']: v['class'] for v in evaluation['variants']}
        self.assertEqual(classes['Strategy 1.1.27_EXIT90'], 'HISTORICAL_FIT_ONLY')
        self.assertEqual(classes['Strategy 1.1.27_EXIT110'], 'INCONCLUSIVE')
        self.assertEqual(evaluation['accepted_for_validation'], [])
        exit90 = next(v for v in evaluation['variants'] if v['name'].endswith('EXIT90'))
        self.assertEqual(exit90['orders']['shared_with_different_outcome'], 50)
        self.assertEqual(exit90['paired_daily']['OOS']['sum_delta'], -1087.0)
        self.assertFalse(exit90['destinations']['fondeo']['relevant'])
        self.assertFalse(package['levels']['useful_progress'])
        self.assertTrue(package['levels']['mechanism_works'])
        self.assertFalse(package['validated'])
        self.assertEqual(len(registry['variants']), 2)

    def test_classification_rules(self):
        criteria = cycle.DEFAULT_CRITERIA
        metrics = lambda net, pf, rd: {'net': net, 'profit_factor': pf, 'ret_dd': rd, 'trades': 100, 'drawdown': 1000.0}
        base = {'IS': metrics(10000, 1.5, 2.0), 'OOS': metrics(3000, 1.3, 1.2)}
        diag = lambda: {'samples': {p: {'exam_screen_provisional': {}, 'r_multiples': {'available': False}} for p in ('IS', 'OOS')}}
        paired = {'days_changed': 20, 'evidence_strength': 'WEAK', 'IS': {}, 'OOS': {'evidence_strength': 'WEAK'}}
        orders = {'orders_identical': False, 'shared_with_different_outcome': 10, 'only_in_base': 0, 'only_in_variant': 0}
        better = {'IS': metrics(12000, 1.7, 2.5), 'OOS': metrics(3600, 1.45, 1.5)}
        self.assertEqual(cycle.classify('v', base, better, diag(), diag(), orders, paired, criteria, 'RULES_CHANGED')['class'],
                         'DEV_FAVORABLE_NOT_RELEVANT')
        # Relevante para un destino pero con evidencia OOS débil → inconcluso; con evidencia moderada → favorable.
        def screen(target, breach):
            return {'PROV_50K_OBJ6_TRAIL4': {'horizons': {'5': {'target_rate': target, 'breach_rate': breach}}}}
        base_diag = {'samples': {p: {'exam_screen_provisional': screen(0.05, 0.05), 'r_multiples': {'available': False}} for p in ('IS', 'OOS')}}
        var_diag = {'samples': {p: {'exam_screen_provisional': screen(0.12, 0.05), 'r_multiples': {'available': False}} for p in ('IS', 'OOS')}}
        self.assertEqual(cycle.classify('v', base, better, base_diag, var_diag, orders, paired, criteria, 'RULES_CHANGED')['class'],
                         'INCONCLUSIVE')
        strong = {**paired, 'OOS': {'evidence_strength': 'MODERATE'}}
        self.assertEqual(cycle.classify('v', base, better, base_diag, var_diag, orders, strong, criteria, 'RULES_CHANGED')['class'],
                         'DEV_FAVORABLE_RELEVANT')
        fit = {'IS': metrics(12000, 1.7, 2.5), 'OOS': metrics(2000, 1.1, 0.8)}
        self.assertEqual(cycle.classify('v', base, fit, diag(), diag(), orders, paired, criteria, 'RULES_CHANGED')['class'],
                         'HISTORICAL_FIT_ONLY')
        worse = {'IS': metrics(8000, 1.3, 1.5), 'OOS': metrics(2000, 1.1, 0.8)}
        self.assertEqual(cycle.classify('v', base, worse, diag(), diag(), orders, paired, criteria, 'RULES_CHANGED')['class'],
                         'REJECTED_WORSE')
        self.assertEqual(cycle.classify('v', base, better, diag(), diag(), orders, paired, criteria, 'METADATA_ONLY_NO_BEHAVIOUR_CHANGE')['class'],
                         'NO_CHANGE_RULES')
        same_orders = {**orders, 'orders_identical': True}
        self.assertEqual(cycle.classify('v', base, base, diag(), diag(), same_orders, paired, criteria, 'RULES_CHANGED')['class'],
                         'NO_EFFECT_IN_SAMPLE')
        few = {**paired, 'days_changed': 2}
        self.assertEqual(cycle.classify('v', base, better, diag(), diag(), orders, few, criteria, 'RULES_CHANGED')['class'],
                         'INCONCLUSIVE')


if __name__ == '__main__':
    unittest.main()
