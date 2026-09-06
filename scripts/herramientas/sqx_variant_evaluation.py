"""Evaluación y clasificación de variantes: la política del motor de mejora.

Módulo independiente: recibe un experimento recalculado (manifest, retest.csv,
órdenes por estrategia) y el contrato, y devuelve `evaluation.json` con la
comparación emparejada por día, la relevancia por destino y una clase por
variante. Los criterios se registran antes de recalcular (criteria.json) y este
módulo se niega a evaluar con criterios alterados. Cambiar la política de
aceptación es cambiar ESTE fichero; no toca el recálculo ni el debate.

Solo biblioteca estándar.
"""
from __future__ import annotations

import csv
import json
import math
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sqx_native_improvement as engine  # noqa: E402
import sqx_strategy_contract as contract_module  # noqa: E402
import sqx_trade_diagnosis as diagnosis_module  # noqa: E402


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data):
    engine.atomic_report(path, data)


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def rules_of(archive: Path) -> bytes:
    import zipfile
    with zipfile.ZipFile(archive) as z:
        return z.read('strategy_Portfolio.xml')


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
    elif (is_v == 'WORSE' and (paired.get('IS') or {}).get('bootstrap_sum_ci90')
          and (paired['IS']['bootstrap_sum_ci90'][1] or 0) < -abs(base_metrics['IS']['net']) * tol['net_profit_relative']):
        # Destruir la construcción con todo el intervalo más allá de la tolerancia es concluyente
        # aunque el OOS cambie poco. Un empeoramiento IS pequeño (intervalo que roza el cero) no basta.
        klass, reason = 'REJECTED_WORSE', f"Empeora la construcción con evidencia: IC 90 % de la suma de deltas IS {paired['IS']['bootstrap_sum_ci90']} íntegramente más allá de la tolerancia."
    elif paired['days_changed'] < criteria['technical']['min_changed_days_for_conclusion']:
        klass, reason = 'INCONCLUSIVE', f"Solo {paired['days_changed']} días de desarrollo (OOS) cambian: muestra insuficiente para concluir."
    elif is_v in ('BETTER', 'EQUIVALENT') and oos_v == 'WORSE':
        klass, reason = 'HISTORICAL_FIT_ONLY', 'Mejora o iguala en construcción pero empeora en desarrollo.'
    elif oos_v == 'WORSE' or (is_v == 'WORSE' and oos_v != 'BETTER'):
        klass, reason = 'REJECTED_WORSE', 'Empeora las métricas de desarrollo.'
    elif is_v == 'BETTER' and oos_v == 'BETTER' or (oos_v == 'BETTER' and is_v == 'EQUIVALENT') or (is_v == 'BETTER' and oos_v == 'EQUIVALENT'):
        oos_strength = paired.get('OOS', paired).get('evidence_strength', paired.get('evidence_strength'))
        # La evidencia OOS exigida crece con la profundidad del linaje (criteria.required_oos_evidence):
        # iterar sobre el mismo OOS de desarrollo aumenta el riesgo de descubrimiento falso.
        acceptable = ('STRONG',) if criteria.get('required_oos_evidence') == 'STRONG' else ('MODERATE', 'STRONG')
        if (fondeo_relevant or ultra_relevant) and oos_strength in acceptable:
            klass, reason = 'DEV_FAVORABLE_RELEVANT', 'Mejora en ambas muestras, relevante para un destino y con evidencia OOS por encima del ruido.'
        elif fondeo_relevant or ultra_relevant:
            klass, reason = 'INCONCLUSIVE', f'Relevante para un destino pero la evidencia OOS emparejada es {oos_strength} (exigida: {acceptable[0]}): el intervalo incluye el cero o hay pocos días con cambio.'
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


