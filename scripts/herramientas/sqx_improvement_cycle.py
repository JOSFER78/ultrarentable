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

SCHEMA = 'ultrarentable.improvement_cycle.v1'
CLASSES = (
    'NO_CHANGE_RULES', 'NO_EFFECT_IN_SAMPLE', 'REJECTED_WORSE', 'HISTORICAL_FIT_ONLY',
    'DEV_FAVORABLE_RELEVANT', 'DEV_FAVORABLE_NOT_RELEVANT', 'INCONCLUSIVE',
)

# Criterios por defecto, registrados antes de recalcular. Son una política
# explícita y revisable, no umbrales universales. Se copian a criterios.json.
DEFAULT_CRITERIA = {
    'schema': 'ultrarentable.improvement_criteria.v1',
    'development_samples': ['IS', 'OOS'],
    'note': 'OOS es la muestra de desarrollo (se consulta para decidir). No existe prueba final reservada en el conjunto de datos actual; ver contract.period.',
    'technical': {
        'rules_must_change_semantically': True,
        'orders_must_differ_in_at_least_one_sample': True,
        'min_changed_days_for_conclusion': 5,
    },
    'not_worse_tolerance': {
        'net_profit_relative': 0.02, 'profit_factor_absolute': 0.03, 'ret_dd_relative': 0.05,
        'note': 'Diferencias dentro de la tolerancia se consideran equivalentes, no mejoras ni empeoramientos.',
    },
    'evidence': {
        'bootstrap_resamples': 4000, 'seed': 20260906,
        'strong': 'IC 90 % de la suma de deltas diarios OOS por encima de cero',
        'moderate': 'IC 80 % por encima de cero',
        'weak': 'media positiva sin IC por encima de cero',
    },
    'fondeo': {
        'primary_scenario': 'PROV_50K_OBJ6_TRAIL4', 'horizon_days': 5,
        'relevant_target_rate_gain_pp': 5.0, 'max_breach_rate_increase_pp': 1.0,
        'note': 'Relevante si sube ≥5 puntos la tasa de objetivo a 5 días en IS y OOS sin subir la ruptura más de 1 punto. Escenario provisional, no una empresa.',
    },
    'ultra': {
        'exploratory': True,
        'min_expectancy_r_change': -0.02, 'relevant_tail_share_gain_pp': 5.0, 'relevant_mfe2r_gain_pp': 5.0,
        'note': 'Ultra en construcción: se mide convexidad (beneficio de operaciones ≥3R y frecuencia de MFE ≥2R). Exploratorio.',
    },
}

HYPOTHESIS_LIBRARY = {
    'H_PT_NEAR': {
        'title': 'Acercar el objetivo de beneficio',
        'problem': 'El objetivo casi nunca se alcanza y se devuelve gran parte del recorrido favorable.',
        'change': 'Multiplicador ATR del objetivo × 0.6 en ambas direcciones.',
        'expected': 'Más salidas por objetivo, menor devolución, mayor tasa de acierto; riesgo de recortar las operaciones grandes.',
        'destination_expectation': {'fondeo': 'sube la tasa de objetivo a 5 días', 'ultra': 'probablemente reduce la convexidad'},
        'requires': ['PT_RARELY_HIT'],
        'supporting': ['HIGH_GIVEBACK_FROM_MFE', 'LOSERS_AFTER_FAVOURABLE_EXCURSION'],
    },
    'H_TS_TIGHT': {
        'title': 'Activar antes y ceñir el stop dinámico',
        'problem': 'Las operaciones ganadoras devuelven una parte grande de su máximo recorrido favorable.',
        'change': 'Nivel de activación del trailing × 0.5 y distancia del trailing × 0.5 en ambas direcciones.',
        'expected': 'Menor devolución desde el MFE conservando las operaciones largas cuando la tendencia continúa.',
        'destination_expectation': {'fondeo': 'menos días perdedores tras un recorrido favorable', 'ultra': 'conserva cola derecha con menor devolución'},
        'requires': [],
        'requires_any': ['HIGH_GIVEBACK_FROM_MFE', 'LOSERS_AFTER_FAVOURABLE_EXCURSION'],
    },
    'H_SL_TIGHT': {
        'title': 'Reducir el stop inicial',
        'problem': 'Una parte alta de las salidas es por stop y concentra las pérdidas.',
        'change': 'Stop inicial × 0.7 en ambas direcciones.',
        'expected': 'Pérdidas medias menores; riesgo de más stops tocados por ruido.',
        'destination_expectation': {'fondeo': 'menor ruptura de límites', 'ultra': 'mayor R por operación si la entrada es precisa'},
        'requires': ['SL_HIT_SHARE_HIGH'],
    },
}


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


def hypothesis_changes(hid: str, rules: bytes) -> list[dict]:
    changes = []
    for direction in ('long', 'short'):
        if hid == 'H_PT_NEAR':
            current = mutations.read_exit(rules, direction, 'profit_target')
            if not current or 'Value' not in current:
                raise ValueError(f'Sin objetivo con valor en {direction}')
            changes.append({'direction': direction, 'exit': 'profit_target', 'value': mutations.scaled(current['Value'], 0.6, 2)})
        elif hid == 'H_TS_TIGHT':
            for exit_name in ('trailing_activation', 'trailing_stop'):
                current = mutations.read_exit(rules, direction, exit_name)
                if not current or 'Value' not in current or current['formula'] is None or current['formula'].endswith('.None'):
                    raise ValueError(f'Sin {exit_name} configurado en {direction}')
                changes.append({'direction': direction, 'exit': exit_name, 'value': mutations.scaled(current['Value'], 0.5, 2)})
        elif hid == 'H_SL_TIGHT':
            current = mutations.read_exit(rules, direction, 'stop_loss')
            if not current or 'Value' not in current:
                raise ValueError(f'Sin stop con valor en {direction}')
            changes.append({'direction': direction, 'exit': 'stop_loss', 'value': mutations.scaled(current['Value'], 0.7, 1)})
        else:
            raise ValueError('Hipótesis desconocida')
    return changes


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


# ------------------------------------------------------------------- paso 6

def variant_label(manifest: dict, name: str) -> str:
    prefix = manifest['source_name'] + '_'
    return name[len(prefix):] if name.startswith(prefix) else name


def metrics_rows(retest_csv: Path) -> dict:
    rows = list(csv.DictReader(retest_csv.read_text(encoding='utf-8-sig').splitlines(), delimiter=';'))
    out = {}
    for row in rows:
        out[row['Strategy Name']] = {part: {
            'net': float(row[f'Net profit ({part})']), 'profit_factor': float(row[f'Profit factor ({part})']),
            'ret_dd': float(row[f'Ret/DD Ratio ({part})']), 'trades': int(float(row[f'# of trades ({part})'])),
            'drawdown': float(row[f'Drawdown ({part})']), 'win_loss': float(row[f'Win/Loss ratio ({part})'])}
            for part in ('IS', 'OOS')}
    return out


def paired_days(base: dict, variant: dict, resamples: int, seed: int) -> dict:
    days = sorted(set(base) | set(variant))
    deltas = [variant.get(d, 0.0) - base.get(d, 0.0) for d in days]
    changed = [x for x in deltas if abs(x) > 1e-9]
    total = sum(deltas)
    rng = random.Random(seed)
    sums = []
    n = len(deltas)
    if n:
        for _ in range(resamples):
            sums.append(sum(deltas[rng.randrange(n)] for _ in range(n)))
        sums.sort()
    def quantile(q):
        if not sums:
            return None
        return round(sums[min(len(sums) - 1, max(0, int(q * len(sums))))], 2)
    positives = sum(1 for x in changed if x > 0)
    # Prueba de signos bilateral sobre los días con cambio.
    m = len(changed)
    p_value = None
    if m:
        k = min(positives, m - positives)
        p_value = min(1.0, 2 * sum(math.comb(m, i) for i in range(k + 1)) / 2 ** m)
    strength = 'NONE'
    if total > 0:
        strength = 'WEAK'
        if quantile(0.10) is not None and quantile(0.10) > 0 and m >= 5:
            strength = 'MODERATE'
        if quantile(0.05) is not None and quantile(0.05) > 0 and m >= 10:
            strength = 'STRONG'
    return {'days_with_activity': n, 'days_changed': m, 'positive_changed_days': positives,
            'sum_delta': round(total, 2), 'mean_delta_changed_days': round(statistics.mean(changed), 2) if changed else None,
            'bootstrap_sum_ci80': [quantile(0.10), quantile(0.90)], 'bootstrap_sum_ci90': [quantile(0.05), quantile(0.95)],
            'sign_test_p_value': round(p_value, 4) if p_value is not None else None, 'evidence_strength': strength}


def compare_orders(base_csv: Path, variant_csv: Path) -> dict:
    def keyed(path):
        return {(t['open_utc'].isoformat(), t['sample']): t for t in diagnosis_module.load_orders(path)}
    a, b = keyed(base_csv), keyed(variant_csv)
    shared = set(a) & set(b)
    changed = sum(1 for k in shared if abs(a[k]['pl'] - b[k]['pl']) > 1e-9 or a[k]['close_utc'] != b[k]['close_utc'])
    return {'orders_identical': engine.sha(base_csv.read_bytes()) == engine.sha(variant_csv.read_bytes()),
            'base_trades': len(a), 'variant_trades': len(b), 'shared_entries': len(shared),
            'shared_with_different_outcome': changed, 'only_in_base': len(set(a) - shared), 'only_in_variant': len(set(b) - shared)}


def better(v, b, tol_rel, tol_abs=0.0):
    tol = max(tol_abs, abs(b) * tol_rel)
    return 'BETTER' if v > b + tol else 'WORSE' if v < b - tol else 'EQUIVALENT'


def rate(diag: dict, sample: str, scenario: str, horizon: int, key: str):
    try:
        return diag['samples'][sample]['exam_screen_provisional'][scenario]['horizons'][str(horizon)][key]
    except KeyError:
        return None


def classify(variant_name: str, base_metrics: dict, var_metrics: dict, base_diag: dict, var_diag: dict,
             orders_cmp: dict, paired: dict, criteria: dict, rules_class: str) -> dict:
    tol = criteria['not_worse_tolerance']
    verdicts = {}
    for part in ('IS', 'OOS'):
        b, v = base_metrics[part], var_metrics[part]
        verdicts[part] = {
            'net': better(v['net'], b['net'], tol['net_profit_relative']),
            'profit_factor': better(v['profit_factor'], b['profit_factor'], 0, tol['profit_factor_absolute']),
            'ret_dd': better(v['ret_dd'], b['ret_dd'], tol['ret_dd_relative']),
            'delta': {k: round(v[k] - b[k], 4) for k in ('net', 'profit_factor', 'ret_dd', 'trades', 'drawdown')},
        }
    def overall(part):
        values = [verdicts[part][k] for k in ('net', 'profit_factor', 'ret_dd')]
        if 'WORSE' in values and 'BETTER' in values:
            return 'MIXED'
        if 'WORSE' in values:
            return 'WORSE'
        if 'BETTER' in values:
            return 'BETTER'
        return 'EQUIVALENT'
    is_v, oos_v = overall('IS'), overall('OOS')
    # Destinos
    f = criteria['fondeo']
    fondeo = {}
    for part in ('IS', 'OOS'):
        bt, vt = rate(base_diag, part, f['primary_scenario'], f['horizon_days'], 'target_rate'), rate(var_diag, part, f['primary_scenario'], f['horizon_days'], 'target_rate')
        bb, vb = rate(base_diag, part, f['primary_scenario'], f['horizon_days'], 'breach_rate'), rate(var_diag, part, f['primary_scenario'], f['horizon_days'], 'breach_rate')
        if None in (bt, vt, bb, vb):
            fondeo[part] = {'available': False}
            continue
        fondeo[part] = {'available': True, 'target_rate_base': bt, 'target_rate_variant': vt, 'delta_target_pp': round((vt - bt) * 100, 2),
                        'breach_rate_base': bb, 'breach_rate_variant': vb, 'delta_breach_pp': round((vb - bb) * 100, 2)}
    fondeo_relevant = all(p.get('available') and p['delta_target_pp'] >= f['relevant_target_rate_gain_pp']
                          and p['delta_breach_pp'] <= f['max_breach_rate_increase_pp'] for p in fondeo.values())
    fondeo_worse = any(p.get('available') and (p['delta_target_pp'] < -2.0 or p['delta_breach_pp'] > f['max_breach_rate_increase_pp']) for p in fondeo.values())
    u = criteria['ultra']
    ultra = {}
    for part in ('IS', 'OOS'):
        br, vr = base_diag['samples'][part]['r_multiples'], var_diag['samples'][part]['r_multiples']
        if not (br.get('available') and vr.get('available')):
            ultra[part] = {'available': False}
            continue
        ultra[part] = {'available': True,
                       'delta_expectancy_r': round(vr['expectancy_r'] - br['expectancy_r'], 4),
                       'delta_tail_share_pp': round(((vr['share_of_profit_from_trades_ge_3r'] or 0) - (br['share_of_profit_from_trades_ge_3r'] or 0)) * 100, 2),
                       'delta_mfe2r_pp': round((vr['fraction_mfe_ge_2r'] - br['fraction_mfe_ge_2r']) * 100, 2),
                       'skewness_base': br['skewness_r'], 'skewness_variant': vr['skewness_r']}
    ultra_relevant = all(p.get('available') and p['delta_expectancy_r'] >= u['min_expectancy_r_change']
                         and (p['delta_tail_share_pp'] >= u['relevant_tail_share_gain_pp'] or p['delta_mfe2r_pp'] >= u['relevant_mfe2r_gain_pp'])
                         for p in ultra.values())
    # Clase
    if rules_class != 'RULES_CHANGED':
        klass, reason = 'NO_CHANGE_RULES', 'Las reglas no cambian de comportamiento; no se debió recalcular.'
    elif orders_cmp['orders_identical'] or (orders_cmp['shared_with_different_outcome'] == 0 and not orders_cmp['only_in_base'] and not orders_cmp['only_in_variant']):
        klass, reason = 'NO_EFFECT_IN_SAMPLE', 'El cambio es real pero no altera ninguna operación en los datos disponibles.'
    elif paired['days_changed'] < criteria['technical']['min_changed_days_for_conclusion']:
        klass, reason = 'INCONCLUSIVE', f"Solo {paired['days_changed']} días cambian: muestra insuficiente para concluir."
    elif is_v in ('BETTER', 'EQUIVALENT') and oos_v == 'WORSE':
        klass, reason = 'HISTORICAL_FIT_ONLY', 'Mejora o iguala en construcción pero empeora en desarrollo.'
    elif oos_v == 'WORSE' or (is_v == 'WORSE' and oos_v != 'BETTER'):
        klass, reason = 'REJECTED_WORSE', 'Empeora las métricas de desarrollo.'
    elif is_v == 'BETTER' and oos_v == 'BETTER' or (oos_v == 'BETTER' and is_v == 'EQUIVALENT') or (is_v == 'BETTER' and oos_v == 'EQUIVALENT'):
        oos_strength = paired.get('OOS', paired).get('evidence_strength', paired.get('evidence_strength'))
        if (fondeo_relevant or ultra_relevant) and oos_strength in ('MODERATE', 'STRONG'):
            klass, reason = 'DEV_FAVORABLE_RELEVANT', 'Mejora en ambas muestras, relevante para un destino y con evidencia OOS por encima del ruido.'
        elif fondeo_relevant or ultra_relevant:
            klass, reason = 'INCONCLUSIVE', f'Relevante para un destino pero la evidencia OOS emparejada es {oos_strength}: el intervalo incluye el cero o hay pocos días con cambio.'
        elif fondeo_worse:
            klass, reason = 'INCONCLUSIVE', 'Mejora métricas generales pero empeora el cribado de examen.'
        else:
            klass, reason = 'DEV_FAVORABLE_NOT_RELEVANT', 'Mejora estadística sin relevancia práctica para el destino.'
    else:
        klass, reason = 'INCONCLUSIVE', f'Resultado mixto (IS {is_v}, OOS {oos_v}).'
    next_action = {
        'NO_CHANGE_RULES': 'Descartar; corregir el generador de variantes.',
        'NO_EFFECT_IN_SAMPLE': 'Conservar como no evaluable en esta muestra; probar solo si otra muestra lo activa.',
        'REJECTED_WORSE': 'Registrar el rechazo y no repetir la hipótesis con estos datos.',
        'HISTORICAL_FIT_ONLY': 'Descartar: sobreajuste probable. No optimizar sobre el OOS.',
        'DEV_FAVORABLE_RELEVANT': 'Candidata a validación independiente con datos no consultados; no promover aún.',
        'DEV_FAVORABLE_NOT_RELEVANT': 'Conservar la información; no consumir más presupuesto salvo combinación con otra hipótesis.',
        'INCONCLUSIVE': 'No concluir; una nueva muestra o más operaciones podrían decidir. No ajustar sobre OOS.',
    }[klass]
    return {'name': variant_name, 'class': klass, 'reason': reason, 'next_action': next_action,
            'development': {'IS': is_v, 'OOS': oos_v, 'detail': verdicts},
            'paired_daily': paired, 'orders': orders_cmp,
            'destinations': {'fondeo': {'relevant': fondeo_relevant, 'worse': fondeo_worse, 'by_sample': fondeo, 'mode': 'PROVISIONAL_SCENARIOS'},
                             'ultra': {'relevant': ultra_relevant, 'by_sample': ultra, 'mode': 'EXPLORATORY'}},
            'validated': False, 'funding_verdict': 'NO_EVALUABLE'}


def step_evaluate(cycle: Path, contract: dict, criteria: dict) -> dict:
    experiment = cycle / 'experiment'
    manifest = read_json(experiment / 'manifest.json')
    engine.native_evidence(experiment / 'manifest.json')
    registered = manifest.get('criteria_sha256')
    if registered and registered != engine.sha((cycle / 'criteria.json').read_bytes()):
        raise ValueError('criteria.json cambió después de preparar el experimento; no se evalúa con criterios alterados')
    metrics = metrics_rows(experiment / 'retest.csv')
    base_name = manifest['entries'][0]['name']
    base_csv = experiment / f'{base_name}_orders.csv'
    base_diag = diagnosis_module.diagnose(base_csv, contract)
    write_json(cycle / 'diagnosis_base_fresh.json', base_diag)
    base_rules = rules_of(experiment / 'input' / manifest['entries'][0]['file'])
    paired_conf = criteria['evidence']
    variants = []
    for index, entry in enumerate(manifest['entries'][1:], 1):
        csv_path = experiment / f"{entry['name']}_orders.csv"
        var_diag = diagnosis_module.diagnose(csv_path, contract, reference_orders=base_csv)
        label = variant_label(manifest, entry['name'])
        write_json(cycle / f"diagnosis_{label}.json", var_diag)
        rules_class = contract_module.compare_rules(base_rules, rules_of(experiment / 'input' / entry['file']))['classification']
        paired = {}
        for part in ('IS', 'OOS'):
            paired[part] = paired_days(base_diag['samples'][part]['daily_pl'], var_diag['samples'][part]['daily_pl'],
                                       paired_conf['bootstrap_resamples'], paired_conf['seed'] + index)
        summary_paired = {**paired['OOS'], 'IS': paired['IS'], 'OOS': paired['OOS']}
        result = classify(entry['name'], metrics[base_name], metrics[entry['name']], base_diag, var_diag,
                          compare_orders(base_csv, csv_path), summary_paired, criteria, rules_class)
        result['hypothesis'] = next((v for v in manifest.get('variants', []) if entry['name'].endswith('_' + v['label'])), None)
        result['metrics'] = metrics[entry['name']]
        variants.append(result)
    evaluation = {
        'schema': 'ultrarentable.improvement_evaluation.v1', 'generated_utc': now(),
        'project': manifest['project'], 'base': {'name': base_name, 'metrics': metrics[base_name],
                                                  'orders_sha256': engine.sha(base_csv.read_bytes())},
        'criteria_sha256': engine.sha((cycle / 'criteria.json').read_bytes()),
        'variants': variants,
        'accepted_for_validation': [v['name'] for v in variants if v['class'] == 'DEV_FAVORABLE_RELEVANT'],
        'limitations': [
            'El OOS es de desarrollo: se ha consultado para clasificar; no es una prueba final reservada.',
            'El cribado de examen usa escenarios provisionales; no acredita compatibilidad con ninguna empresa.',
            'Ultra es exploratorio: sus criterios están en construcción.',
        ],
    }
    write_json(cycle / 'evaluation.json', evaluation)
    return evaluation


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
