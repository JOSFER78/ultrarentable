"""Pruebas del vocabulario de filtros de entrada (hora, día, dirección) sobre las reglas reales EW.

Comprobación de mecanismo en SQX (VPS, 2026-09-06, UR_IMPROVE_MECANISMO_FILTROS_01): la
ventana 8-13 y la desactivación de cortos recalcularon sin error y cambiaron la muestra como
se esperaba; aquí solo se prueba la construcción y la verificación del XML, sin SQX ni red.
"""
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'scripts' / 'herramientas'
EVIDENCE = ROOT / 'orchestration/results/codex/SQX_NATIVE_IMPROVEMENT_20260905'
SEARCH_ZIP = EVIDENCE / 'ew_native_search_evidence_20260906.zip'
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
evaluation = module('sqx_variant_evaluation', 'sqx_variant_evaluation.py')
module('sqx_fixed_hypotheses_scaffold', 'sqx_fixed_hypotheses_scaffold.py')
cycle = module('sqx_improvement_cycle', 'sqx_improvement_cycle.py')
debate = module('sqx_hypothesis_debate', 'sqx_hypothesis_debate.py')


def real_rules() -> bytes:
    with zipfile.ZipFile(SEARCH_ZIP) as archive:
        source = archive.read('ew_native_builder_20260906/selected/Strategy 1.1.27.sqx')
    with zipfile.ZipFile(io.BytesIO(source)) as inner:
        return inner.read('strategy_Portfolio.xml')


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


def filter_items(rules_xml: bytes, direction: str) -> list[dict]:
    root = ET.fromstring(rules_xml)
    return mutations.entry_filters(mutations._entry_rule(root, direction))


class EntryFilters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = real_rules()

    def test_hour_range_adds_exactly_two_conditions_per_direction(self):
        built = mutations.build_variant(self.rules, [{'filter': 'hour_range', 'direction': 'both', 'from': 8, 'to': 13}])
        for direction in ('long', 'short'):
            items = filter_items(built['rules'], direction)
            self.assertEqual([(i['block'], i['Hour'], i['Shift']) for i in items],
                             [('BarHourIsBigger', '7', str(mutations.FILTER_SHIFT)), ('BarHourIsSmaller', '13', str(mutations.FILTER_SHIFT))])
        self.assertEqual(filter_items(self.rules, 'long'), [])
        # Solo se añaden parámetros; nada existente cambia y las salidas siguen iguales.
        changed = built['comparison']['changed_params']
        self.assertEqual({c.get('change') for c in changed}, {'added'})
        self.assertEqual(len(changed), 12)
        for direction in ('long', 'short'):
            for name in mutations.EXIT_KEYS:
                self.assertEqual(mutations.read_exit(built['rules'], direction, name), mutations.read_exit(self.rules, direction, name))
        record = built['changes'][0]
        self.assertEqual((record['from'], record['to'], record['effective_fields']), (8, 13, 0))
        self.assertEqual(len(record['scope_prefixes']), 2)

    def test_open_ended_windows_add_a_single_condition(self):
        built = mutations.build_variant(self.rules, [{'filter': 'hour_range', 'direction': 'long', 'from': 0, 'to': 15}])
        self.assertEqual([i['block'] for i in filter_items(built['rules'], 'long')], ['BarHourIsSmaller'])
        built = mutations.build_variant(self.rules, [{'filter': 'hour_range', 'direction': 'short', 'from': 9, 'to': 24}])
        self.assertEqual([(i['block'], i['Hour']) for i in filter_items(built['rules'], 'short')], [('BarHourIsBigger', '8')])
        self.assertEqual(filter_items(built['rules'], 'long'), [])

    def test_disable_direction_only_touches_that_rule(self):
        built = mutations.build_variant(self.rules, [{'filter': 'disable_direction', 'direction': 'short'}])
        self.assertEqual(filter_items(built['rules'], 'short'), [{'block': 'Boolean', 'Value': 'false'}])
        self.assertEqual(filter_items(built['rules'], 'long'), [])
        self.assertEqual(len(built['comparison']['changed_params']), 1)
        self.assertTrue(built['comparison']['changed_params'][0]['param'].startswith('Strategy/Rules/Events/Event[OnBarUpdate]/Rule#2/If/'))

    def test_exclude_weekdays_accepts_names_in_both_languages_and_orders_them(self):
        built = mutations.build_variant(self.rules, [{'filter': 'exclude_weekdays', 'direction': 'long', 'days': ['viernes', 'Mon']}])
        items = filter_items(built['rules'], 'long')
        self.assertEqual([(i['block'], i['Day'], i['day_name']) for i in items],
                         [('BarDayOfWeekIsNot', '1', 'Monday'), ('BarDayOfWeekIsNot', '5', 'Friday')])
        self.assertEqual(built['changes'][0]['days'], ['Monday', 'Friday'])

    def test_filters_combine_with_exit_and_parameter_changes(self):
        catalogue = {c['key']: c for c in mutations.mutable_parameters(self.rules) if c['context'].startswith('Long entry')}
        built = mutations.build_variant(self.rules, [
            {'filter': 'hour_range', 'direction': 'long', 'from': 9, 'to': 14},
            {'direction': 'long', 'exit': 'profit_target', 'value': '2.5'},
            {'param_path': catalogue['BarsValid']['path'], 'value': '2'},
        ])
        free = [c for c in built['comparison']['changed_params'] if c.get('change') != 'added']
        self.assertEqual(len(free), 2)
        self.assertEqual(mutations.read_exit(built['rules'], 'long', 'profit_target')['Value'], '2.5')
        self.assertEqual(len(filter_items(built['rules'], 'long')), 2)

    def test_same_filter_twice_yields_same_semantic_hash(self):
        changes = [{'filter': 'exclude_weekdays', 'direction': 'both', 'days': ['Monday']}]
        a, b = mutations.build_variant(self.rules, changes), mutations.build_variant(self.rules, changes)
        self.assertEqual(a['semantic_rules_sha256'], b['semantic_rules_sha256'])
        self.assertNotEqual(a['semantic_rules_sha256'], contract_module.semantic_rules_sha256(self.rules))

    def test_invalid_filters_are_rejected_before_any_retest(self):
        cases = {
            'from >= to': [{'filter': 'hour_range', 'from': 13, 'to': 8}],
            '0-24 no filtra': [{'filter': 'hour_range', 'from': 0, 'to': 24}],
            'hora fuera de rango': [{'filter': 'hour_range', 'from': 8, 'to': 25}],
            'más de tres días': [{'filter': 'exclude_weekdays', 'days': ['Mon', 'Tue', 'Wed', 'Thu']}],
            'día desconocido': [{'filter': 'exclude_weekdays', 'days': ['Funday']}],
            'both para desactivar': [{'filter': 'disable_direction', 'direction': 'both'}],
            'filtro repetido': [{'filter': 'hour_range', 'from': 8, 'to': 13}, {'filter': 'hour_range', 'direction': 'long', 'from': 9, 'to': 12}],
            'tipo desconocido': [{'filter': 'session_only'}],
            'dirección inválida': [{'filter': 'hour_range', 'direction': 'sideways', 'from': 8, 'to': 13}],
        }
        for label, changes in cases.items():
            with self.assertRaises(ValueError, msg=label):
                mutations.build_variant(self.rules, changes)

    def test_existing_filter_is_visible_and_retunable_not_stackable(self):
        built = mutations.build_variant(self.rules, [{'filter': 'hour_range', 'direction': 'long', 'from': 8, 'to': 13}])
        described = contract_module.describe_rules(built['rules'])
        long_entry = next(e for e in described['entries'] if e['direction'] == 'long')
        self.assertEqual([f['meaning'] for f in long_entry['entry_filters']], ['hora de barra > 7', 'hora de barra < 13'])
        hours = [c for c in mutations.mutable_parameters(built['rules']) if c['key'] == 'Hour']
        self.assertEqual([c['current'] for c in hours], ['7', '13'])
        retuned = mutations.build_variant(built['rules'], [{'param_path': hours[1]['path'], 'value': '12'}])
        self.assertEqual([f['Hour'] for f in filter_items(retuned['rules'], 'long')], ['7', '12'])
        with self.assertRaises(ValueError):
            mutations.build_variant(built['rules'], [{'filter': 'hour_range', 'direction': 'long', 'from': 9, 'to': 12}])
        with self.assertRaises(ValueError):
            mutations.build_variant(built['rules'], [{'param_path': hours[1]['path'], 'value': '30'}])

    def test_engine_prepare_accepts_filter_variants(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = extract_sl_experiment(Path(directory) / 'evidence')
            source = experiment / 'input' / 'Strategy 1.1.27_BASE.sqx'
            rules = cycle.rules_of(source)
            variants = {'HOURS': mutations.build_variant(rules, [{'filter': 'hour_range', 'from': 8, 'to': 13}])['rules'],
                        'LONGONLY': mutations.build_variant(rules, [{'filter': 'disable_direction', 'direction': 'short'}])['rules']}
            manifest = engine.prepare(source, experiment / 'project.cfx', Path(directory) / 'out',
                                      '/opt/SQX-headless/import/prueba_filtros', 'UR_IMPROVE_PRUEBA_FILTROS', custom_variants=variants)
            self.assertEqual([e['name'].split('_')[-1] for e in manifest['entries']], ['BASE', 'HOURS', 'LONGONLY'])
            for entry in manifest['entries'][1:]:
                with zipfile.ZipFile(Path(directory) / 'out' / 'input' / entry['file']) as archive:
                    self.assertEqual(contract_module.compare_rules(rules, archive.read('strategy_Portfolio.xml'))['classification'], 'RULES_CHANGED')


class DebateVocabulary(unittest.TestCase):
    def test_dossier_offers_filters_and_hides_oos_segment_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            root = make_cycle(Path(directory))
            contract = cycle.read_json(root / 'contract.json')
            diagnosis = cycle.read_json(root / 'diagnosis_base.json')
            rules = cycle.rules_of(Path(contract['provenance']['archive_path']))
            dossier = debate.build_dossier(contract, diagnosis, rules, {'variants': {}}, {**cycle.DEFAULT_CRITERIA, 'max_variants': 2})
            vocabulary = dossier['mutation_vocabulary']
            self.assertIn('hour_range', vocabulary['filters']['description'])
            self.assertEqual(vocabulary['filters']['current'], {'long': [], 'short': []})
            self.assertNotIn('filtros de horario o día de la semana', vocabulary['not_supported_yet'])
            self.assertIn('by_entry_hour_local', dossier['diagnosis']['samples']['IS'])
            for table in debate.SEGMENT_TABLES:
                self.assertNotIn(table, dossier['diagnosis']['samples']['OOS'])
            self.assertIn('segment_tables_hidden', dossier['diagnosis']['samples']['OOS'])
            for finding in dossier['diagnosis']['findings']:
                if finding['sample'] == 'OOS' and finding['code'] in debate.SEGMENT_FINDING_CODES:
                    self.assertTrue(finding.get('segment_hidden'))
                    self.assertNotIn('net', finding['evidence'])

    def test_filter_proposals_validate_and_flow_into_plan_and_registry_keys(self):
        rules = real_rules()
        proposals = [
            {'id': 'P1', 'changes': [{'filter': 'hour_range', 'direction': 'both', 'from': 8, 'to': 13}]},
            {'id': 'P2', 'changes': [{'filter': 'exclude_weekdays', 'direction': 'long', 'days': ['Monday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']}]},
            {'id': 'P3', 'changes': [{'filter': 'disable_direction', 'direction': 'short'}, {'direction': 'long', 'exit': 'stop_loss', 'value': '80'}]},
        ]
        validated = debate.validate_proposals(proposals, rules)
        self.assertEqual([v['validation']['applicable'] for v in validated], [True, False, True])
        self.assertIn('máximo tres días', validated[1]['validation']['error'])
        self.assertEqual(len(validated[2]['validation']['verified_changes']), 2)
        for key in ('filter', 'from', 'to', 'days'):
            self.assertIn(key, cycle.CHANGE_KEYS)
            self.assertIn(key, debate.CHANGE_SCHEMA['properties'])
        self.assertIn('both', debate.CHANGE_SCHEMA['properties']['direction']['enum'])


if __name__ == '__main__':
    unittest.main()
