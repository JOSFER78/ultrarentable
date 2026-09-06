"""Diagnóstico determinista de una estrategia a partir de sus órdenes nativas.

Entrada: el CSV de órdenes exportado por ExportNativeOrders.java (SQX) y el
contrato de la estrategia. Salida: perfil por muestra (IS / OOS de desarrollo),
concentración, eficiencia de salidas, horarios, costes, frecuencia, múltiplos R,
cribado provisional de ventanas de examen y una lista de hallazgos que pueden
convertirse en hipótesis. No certifica nada: describe lo que hay en las órdenes.

Marcas de tiempo: cuando el recurso de datos declara zona "Exchange", SQX
escribe las horas de bolsa como si fueran UTC (los cierres por hora caen a las
15:00 exactas todo el año); se interpretan como hora local de la bolsa sin
conversión. Con datos declarados en UTC se convierten a la zona de la bolsa.

Solo biblioteca estándar.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = 'ultrarentable.trade_diagnosis.v2'

# com.strategyquant.tradinglib.OrderCloseTypes de la instalación 144.2953
# (javap -constants, 2026-09-06).
CLOSE_TYPES = {
    1: 'Manual', 2: 'SL', 3: 'PT', 4: 'EndTest', 5: 'EOD', 6: 'Expired', 7: 'Reversed',
    8: 'Deleted', 9: 'Replaced', 11: 'OCA', 12: 'Commission', 13: 'EOD_TIME', 14: 'EOF',
    16: 'EOF_TIME', 17: 'EOR', 18: 'NETTING_CONTROL_ORDER', 19: 'ExitAfterXBars',
    20: 'MoveSL2BE', 21: 'TrailingStop', 22: 'ExitSignal', 55: 'EOD_NEXT_OPEN', 60: 'Delisted',
}
SAMPLES = {'11': 'IS', '21': 'OOS'}
TIME_EXIT_TYPES = ('EOD', 'EOD_TIME', 'EOF', 'EOF_TIME', 'EOR', 'EndTest', 'EOD_NEXT_OPEN')

# Escenarios PROVISIONALES de examen. No corresponden a ninguna empresa concreta:
# sirven para medir con qué frecuencia se alcanza un objetivo antes de romper una
# regla, con reglas explícitas y fechadas. Sustituir por la modalidad real cuando
# se evalúe una empresa. `trailing_stops_at_breakeven`: el suelo arrastrado deja
# de subir al alcanzar el saldo inicial (regla habitual de las evaluadoras).
PROVISIONAL_EXAM_SCENARIOS = [
    {'id': 'PROV_50K_OBJ6_TRAIL4', 'nominal': 50000.0, 'target': 3000.0,
     'max_loss': 2000.0, 'max_loss_mode': 'trailing_eod', 'trailing_stops_at_breakeven': True,
     'daily_loss_limit': None, 'min_trading_days': 1,
     'note': 'Objetivo 6 %, pérdida máxima 4 % arrastrada al cierre de cada día hasta el saldo inicial. Provisional.'},
    {'id': 'PROV_50K_OBJ8_TRAIL5_DLL2', 'nominal': 50000.0, 'target': 4000.0,
     'max_loss': 2500.0, 'max_loss_mode': 'trailing_eod', 'trailing_stops_at_breakeven': True,
     'daily_loss_limit': 1000.0, 'min_trading_days': 1,
     'note': 'Objetivo 8 %, pérdida máxima 5 % arrastrada y límite diario 2 %. Provisional.'},
]
HORIZONS = (1, 2, 3, 4, 5)


def native_datetime(ms: int, zone: ZoneInfo, declared_timezone: str | None) -> datetime:
    """Marca de tiempo nativa como hora de la bolsa (ver docstring del módulo)."""
    naive = datetime.fromtimestamp(int(ms) / 1000, timezone.utc).replace(tzinfo=None)
    if declared_timezone == 'Exchange':
        return naive.replace(tzinfo=zone)
    return naive.replace(tzinfo=timezone.utc).astimezone(zone)


def load_orders(path: Path, zone: ZoneInfo | None = None, declared_timezone: str | None = None) -> list[dict]:
    """Órdenes ejecutadas normalizadas; excluye pendientes canceladas y saldos."""
    zone = zone or timezone.utc
    rows = list(csv.DictReader(Path(path).read_text(encoding='utf-8-sig').splitlines()))
    trades = []
    for row in rows:
        flags = (row['is_balance'], row['is_canceled'], row['is_pending'])
        if flags != ('false', 'false', 'false'):
            continue
        if row['sample'] not in SAMPLES:
            raise ValueError(f"Muestra nativa no soportada: {row['sample']}")
        pl = float(row['pl'])
        commission = float(row['commission_swap'])
        slippage = float(row['slippage_money'])
        trades.append({
            'ticket': row['ticket'], 'sample': SAMPLES[row['sample']],
            'open_ms': int(row['open_time']), 'close_ms': int(row['close_time']),
            'open_utc': native_datetime(row['open_time'], zone, declared_timezone),
            'close_utc': native_datetime(row['close_time'], zone, declared_timezone),
            'size': float(row['size']), 'pl': pl,
            'gross': pl - commission + slippage,
            'costs': abs(commission) + abs(slippage),
            'mae': float(row['mae']), 'mfe': float(row['mfe']),
            'open_price': float(row['open_price']), 'close_price': float(row['close_price']),
            'long': row['is_long'] == 'true',
            'bars': int(row['bars_in_trade']),
            'close_type': CLOSE_TYPES.get(int(row['close_type']), f"code_{row['close_type']}"),
            'stop_loss': float(row['stop_loss']), 'take_profit': float(row['take_profit']),
            'balance_after': float(row['balance']),
        })
    trades.sort(key=lambda t: (t['open_ms'], t['close_ms'], int(t['ticket'])))
    return trades


def infer_point_value(trades: list[dict]) -> dict:
    """Valor del punto deducido de las órdenes: bruto / (Δprecio × tamaño)."""
    estimates = []
    for t in trades:
        delta = (t['close_price'] - t['open_price']) * (1 if t['long'] else -1) * t['size']
        if abs(delta) > 1e-9 and t['size'] > 0:
            estimates.append(t['gross'] / delta)
    if not estimates:
        return {'point_value': None, 'observations': 0}
    median = statistics.median(estimates)
    spread = max(abs(e - median) for e in estimates)
    return {'point_value': round(median, 6), 'observations': len(estimates),
            'max_abs_deviation': round(spread, 6), 'consistent': spread <= max(0.01, abs(median) * 0.01)}


def _round(x, digits=4):
    return None if x is None else round(x, digits)


def summary(trades: list[dict]) -> dict:
    if not trades:
        return {'trades': 0}
    pls = [t['pl'] for t in trades]
    wins = [p for p in pls if p > 0]
    losses = [p for p in pls if p < 0]
    gross_win, gross_loss = sum(wins), -sum(losses)
    equity, peak, max_dd = 0.0, 0.0, 0.0
    for p in pls:
        equity += p
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    net = sum(pls)
    return {
        'trades': len(trades), 'net': _round(net, 2), 'gross': _round(sum(t['gross'] for t in trades), 2),
        'costs': _round(sum(t['costs'] for t in trades), 2),
        'profit_factor': _round(gross_win / gross_loss, 3) if gross_loss > 0 else None,
        'win_rate': _round(len(wins) / len(trades), 4),
        'avg_win': _round(statistics.mean(wins), 2) if wins else None,
        'avg_loss': _round(statistics.mean(losses), 2) if losses else None,
        'payoff': _round(statistics.mean(wins) / -statistics.mean(losses), 3) if wins and losses else None,
        'expectancy': _round(net / len(trades), 2),
        'max_drawdown_closed': _round(max_dd, 2),
        'return_over_drawdown': _round(net / max_dd, 3) if max_dd > 0 else None,
        'largest_win': _round(max(pls), 2), 'largest_loss': _round(min(pls), 2),
        'pl_std': _round(statistics.pstdev(pls), 2) if len(pls) > 1 else None,
        'long_trades': sum(t['long'] for t in trades),
        'short_trades': sum(not t['long'] for t in trades),
        'sizes': sorted({t['size'] for t in trades}),
    }


def by_group(trades, key) -> dict:
    groups = defaultdict(list)
    for t in trades:
        groups[key(t)].append(t)
    result = {}
    for name in sorted(groups, key=str):
        s = summary(groups[name])
        result[str(name)] = {'trades': s['trades'], 'net': s['net'], 'win_rate': s['win_rate'],
                             'profit_factor': s['profit_factor']}
    return result


def concentration(trades) -> dict:
    if not trades:
        return {}
    pls = sorted((t['pl'] for t in trades), reverse=True)
    net = sum(pls)
    winners = [p for p in pls if p > 0]
    top_k = max(1, math.ceil(len(pls) * 0.05))
    gross_win = sum(winners) or 1.0
    return {
        'top_5pct_count': top_k,
        'top_5pct_share_of_gross_profit': _round(sum(pls[:top_k]) / gross_win, 4) if winners else None,
        'net_without_top_3_winners': _round(net - sum(pls[:3]), 2),
        'net_without_worst_3_losers': _round(net - sum(pls[-3:]), 2),
        'net_without_top_3_and_worst_3': _round(net - sum(pls[:3]) - sum(pls[-3:]), 2),
    }


def exit_efficiency(trades) -> dict:
    """Devolución medida sobre ganadoras; las perdedoras se tratan aparte (múltiplos R)."""
    if not trades:
        return {}
    by_type = by_group(trades, lambda t: t['close_type'])
    winners = [t for t in trades if t['pl'] > 0 and t['mfe'] > 0]
    giveback_winners = [t['mfe'] - t['gross'] for t in winners]
    with_mfe = [t for t in trades if t['mfe'] > 0]
    return {
        'close_types': by_type,
        'mean_mfe': _round(statistics.mean(t['mfe'] for t in trades), 2),
        'mean_mae': _round(statistics.mean(t['mae'] for t in trades), 2),
        'mean_giveback_winners': _round(statistics.mean(giveback_winners), 2) if giveback_winners else None,
        'mean_giveback_all_with_mfe': _round(statistics.mean(t['mfe'] - t['gross'] for t in with_mfe), 2) if with_mfe else None,
        'winners_closed_below_half_mfe': sum(1 for t in winners if t['gross'] < t['mfe'] / 2),
        'trades_with_mfe_over_2x_final_loss': sum(1 for t in trades if t['pl'] < 0 and t['mfe'] >= 2 * abs(t['pl'])),
        'mean_bars_in_trade': _round(statistics.mean(t['bars'] for t in trades), 2),
        'zero_duration_trades': sum(1 for t in trades if t['open_ms'] == t['close_ms']),
    }


def initial_risk(trade: dict, point_value: float):
    if trade['stop_loss'] <= 0 or not point_value:
        return None
    risk = abs(trade['open_price'] - trade['stop_loss']) * point_value * trade['size']
    return risk if risk > 0 else None


def risk_map(trades: list[dict], point_value: float) -> dict:
    """Riesgo inicial por entrada (clave: muestra y apertura), para comparar variantes con el riesgo del control."""
    return {(t['sample'], t['open_ms']): risk for t in trades if (risk := initial_risk(t, point_value)) is not None}


def r_multiples(trades, point_value, risk_reference: dict | None = None) -> dict:
    """Múltiplos R respecto al riesgo inicial (distancia al stop × valor del punto).

    Con `risk_reference` (riesgos del control por entrada) una variante se mide con
    el riesgo del control: cambiar el stop no puede inflar la convexidad aparente.
    Las entradas sin correspondencia usan la mediana del riesgo del control.
    """
    if not trades or not point_value:
        return {'available': False}
    rs, mfe_rs, losers_after_1r = [], [], 0
    fallback = statistics.median(risk_reference.values()) if risk_reference else None
    matched = 0
    for t in trades:
        if risk_reference is not None:
            risk = risk_reference.get((t['sample'], t['open_ms']))
            matched += risk is not None
            risk = risk if risk is not None else fallback
        else:
            risk = initial_risk(t, point_value)
        if not risk:
            continue
        rs.append(t['gross'] / risk)
        mfe_rs.append(t['mfe'] / risk)
        if t['pl'] < 0 and t['mfe'] / risk >= 1:
            losers_after_1r += 1
    if len(rs) < 5:
        return {'available': False, 'reason': 'Menos de cinco operaciones con riesgo inicial'}
    mean = statistics.mean(rs)
    std = statistics.pstdev(rs)
    skew = (sum((r - mean) ** 3 for r in rs) / len(rs)) / (std ** 3) if std > 0 else None
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r < 0]
    profit_from_big = sum(r for r in rs if r >= 3)
    total_profit = sum(wins)
    losers = sum(1 for t in trades if t['pl'] < 0)
    return {
        'available': True, 'trades_with_initial_risk': len(rs),
        'risk_source': 'CONTROL_REFERENCE' if risk_reference is not None else 'OWN_INITIAL_STOP',
        'matched_to_reference': matched if risk_reference is not None else None,
        'expectancy_r': _round(mean, 4), 'std_r': _round(std, 4), 'skewness_r': _round(skew, 4) if skew is not None else None,
        'payoff_ratio_r': _round(statistics.mean(wins) / -statistics.mean(losses), 3) if wins and losses else None,
        'share_of_profit_from_trades_ge_3r': _round(profit_from_big / total_profit, 4) if total_profit > 0 else None,
        'fraction_mfe_ge_1r': _round(sum(m >= 1 for m in mfe_rs) / len(mfe_rs), 4),
        'fraction_mfe_ge_2r': _round(sum(m >= 2 for m in mfe_rs) / len(mfe_rs), 4),
        'fraction_mfe_ge_3r': _round(sum(m >= 3 for m in mfe_rs) / len(mfe_rs), 4),
        'losers_after_mfe_ge_1r': losers_after_1r,
        'share_of_losers_after_mfe_ge_1r': _round(losers_after_1r / losers, 4) if losers else None,
        'max_r': _round(max(rs), 3), 'min_r': _round(min(rs), 3),
    }


def trading_day(opened: datetime, zone: ZoneInfo) -> date:
    """Día de negociación con cambio a las 17:00 hora de la bolsa (sesión Globex)."""
    local = opened.astimezone(zone)
    day = local.date() + timedelta(days=int(local.hour >= 17))
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def time_profile(trades, zone: ZoneInfo) -> dict:
    return {
        'by_entry_hour_local': by_group(trades, lambda t: f"{t['open_utc'].astimezone(zone).hour:02d}"),
        'by_weekday': by_group(trades, lambda t: t['open_utc'].astimezone(zone).strftime('%u-%a')),
        'by_year': by_group(trades, lambda t: t['open_utc'].astimezone(zone).strftime('%Y')),
        'by_quarter': by_group(trades, lambda t: t['open_utc'].astimezone(zone).strftime('%Y-Q') + str((t['open_utc'].astimezone(zone).month - 1) // 3 + 1)),
        'by_direction': by_group(trades, lambda t: 'long' if t['long'] else 'short'),
        'holding_bars': {'mean': _round(statistics.mean(t['bars'] for t in trades), 2) if trades else None,
                         'max': max((t['bars'] for t in trades), default=None)},
    }


def weekdays_between(start: date, end: date) -> list[date]:
    day, days = start, []
    while day <= end:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


def parse_native_date(value: str) -> date:
    return datetime.strptime(value.replace('-', '.'), '%Y.%m.%d').date()


def sample_calendars(contract: dict) -> dict:
    """Días hábiles de cada muestra: OOS = unión de los rangos declarados; IS = el resto del periodo."""
    zone_name = (contract.get('market') or {}).get('resolved_timezone') or 'UTC'
    zone = ZoneInfo(zone_name)

    def to_trading_session_end(d: date) -> date:
        # Los contratos con cotizaciones de domingo por la tarde pertenecen a la sesión de negociación del lunes siguiente
        return trading_day(datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc), zone)

    start = parse_native_date(contract['period']['date_from'])
    end = to_trading_session_end(parse_native_date(contract['period']['date_to']))
    oos_days = set()
    for rng in contract['period'].get('oos_ranges', []):
        rng_start = parse_native_date(rng['from'])
        rng_end = to_trading_session_end(parse_native_date(rng['to']))
        oos_days.update(weekdays_between(rng_start, rng_end))
    all_days = weekdays_between(start, end)
    return {'IS': [d for d in all_days if d not in oos_days], 'OOS': sorted(d for d in oos_days if start <= d <= end)}


def daily_results(trades, zone: ZoneInfo, calendar: list[date]) -> dict:
    """P&L y peor excursión por día de negociación, incluidos días sin operar."""
    days = {d: {'pl': 0.0, 'worst_intraday_estimate': 0.0, 'trades': 0, 'costs': 0.0} for d in calendar}
    for t in trades:
        day = trading_day(t['open_utc'], zone)
        if day not in days:
            # Tolerancia de sesión: si el día de negociación cae dentro o en extremos adyacentes del calendario
            if calendar and (calendar[0] - timedelta(days=3) <= day <= calendar[-1] + timedelta(days=3)):
                days[day] = {'pl': 0.0, 'worst_intraday_estimate': 0.0, 'trades': 0, 'costs': 0.0}
            else:
                raise ValueError(f"Orden {t['ticket']} ({day}) fuera del calendario de su muestra {t['sample']}")
        entry = days[day]
        # Estimación conservadora del peor punto intradía: saldo previo del día
        # menos la máxima excursión adversa de cada operación, en orden de apertura.
        entry['worst_intraday_estimate'] = min(entry['worst_intraday_estimate'], entry['pl'] - t['mae'] - t['costs'])
        entry['pl'] += t['pl']
        entry['costs'] += t['costs']
        entry['trades'] += 1
    return days


def window_outcome(day_entries: list[dict], scenario: dict) -> dict:
    """Resultado de una ventana de examen provisional que empieza con cuenta nueva."""
    balance, peak = 0.0, 0.0
    floor = -scenario['max_loss']
    trading_days = 0
    intraday_breach_possible = False
    dll = scenario.get('daily_loss_limit')
    for number, day in enumerate(day_entries, 1):
        if day['trades']:
            trading_days += 1
        if dll and day['pl'] <= -dll:
            return {'outcome': 'DAILY_LOSS_BREACH', 'day': number, 'profit': round(balance + day['pl'], 2)}
        if dll and day['worst_intraday_estimate'] <= -dll:
            intraday_breach_possible = True
        if balance + day['worst_intraday_estimate'] <= floor:
            intraday_breach_possible = True
        balance += day['pl']
        if balance <= floor:
            return {'outcome': 'MAX_LOSS_BREACH_AT_CLOSE', 'day': number, 'profit': round(balance, 2)}
        if balance >= scenario['target'] and trading_days >= scenario.get('min_trading_days', 1):
            return {'outcome': ('TARGET_WITH_POSSIBLE_INTRADAY_BREACH' if intraday_breach_possible else 'TARGET'),
                    'day': number, 'profit': round(balance, 2), 'trading_days': trading_days}
        peak = max(peak, balance)
        if scenario.get('max_loss_mode') == 'trailing_eod':
            trailed = peak - scenario['max_loss']
            if scenario.get('trailing_stops_at_breakeven', True):
                trailed = min(0.0, trailed)
            floor = max(floor, trailed)
    if intraday_breach_possible:
        return {'outcome': 'POSSIBLE_INTRADAY_BREACH', 'profit': round(balance, 2), 'trading_days': trading_days}
    return {'outcome': 'NO_TRADES' if not trading_days else 'NO_TARGET_NO_BREACH',
            'profit': round(balance, 2), 'trading_days': trading_days}


def exam_screen(days: dict, scenarios=PROVISIONAL_EXAM_SCENARIOS) -> dict:
    """Frecuencia con la que una ventana de 1–5 días alcanza el objetivo antes de romper una regla.

    `target_rate` cuenta solo objetivos limpios; una ventana que alcanza el objetivo
    con posible ruptura intradía cuenta como ruptura. Las ventanas solapadas (una por
    día de inicio) no son observaciones independientes; `disjoint_windows` es el
    tamaño muestral efectivo de referencia.
    """
    calendar = [days[d] for d in sorted(days)]
    result = {}
    for scenario in scenarios:
        horizons = {}
        for horizon in HORIZONS:
            counts = defaultdict(int)
            outcomes = []
            for index in range(max(0, len(calendar) - horizon + 1)):
                outcome = window_outcome(calendar[index:index + horizon], scenario)['outcome']
                counts[outcome] += 1
                outcomes.append(outcome)
            total = len(outcomes)
            disjoint = outcomes[::horizon]
            breach = (counts['MAX_LOSS_BREACH_AT_CLOSE'] + counts['DAILY_LOSS_BREACH'] +
                      counts['POSSIBLE_INTRADAY_BREACH'] + counts['TARGET_WITH_POSSIBLE_INTRADAY_BREACH'])
            horizons[str(horizon)] = {
                'windows': total, 'disjoint_windows': len(disjoint),
                'outcomes': dict(sorted(counts.items())),
                'target_rate': _round(counts['TARGET'] / total, 4) if total else None,
                'target_rate_including_possible_breach': _round((counts['TARGET'] + counts['TARGET_WITH_POSSIBLE_INTRADAY_BREACH']) / total, 4) if total else None,
                'breach_rate': _round(breach / total, 4) if total else None,
                'disjoint_target_rate': _round(sum(o == 'TARGET' for o in disjoint) / len(disjoint), 4) if disjoint else None,
            }
        result[scenario['id']] = {'scenario': scenario, 'horizons': horizons}
    return result


def frequency(trades, days: dict) -> dict:
    if not days:
        return {}
    ordered = sorted(days)
    active = [d for d in ordered if days[d]['trades']]
    gaps = []
    last = None
    for d in ordered:
        if days[d]['trades']:
            if last is not None:
                gaps.append((d - last).days)
            last = d
    weeks = max(1.0, len(ordered) / 5.0)
    return {
        'weekdays_in_sample': len(ordered), 'days_with_trades': len(active),
        'share_of_days_with_trades': _round(len(active) / len(ordered), 4),
        'trades_per_week': _round(len(trades) / weeks, 3),
        'longest_gap_days': max(gaps, default=None),
        'median_gap_days': statistics.median(gaps) if gaps else None,
    }


def findings(profile: dict) -> list[dict]:
    """Hallazgos heurísticos que pueden convertirse en hipótesis; no son veredictos."""
    out = []
    for sample in ('IS', 'OOS'):
        p = profile['samples'].get(sample)
        if not p or p['summary'].get('trades', 0) == 0:
            out.append({'code': 'NO_TRADES', 'sample': sample, 'severity': 'blocking'})
            continue
        s, ex, con, fr, rm = p['summary'], p['exit_efficiency'], p['concentration'], p['frequency'], p['r_multiples']
        n = s['trades']
        if n < 30:
            out.append({'code': 'FEW_TRADES', 'sample': sample, 'severity': 'high',
                        'evidence': {'trades': n}, 'note': 'Muestra escasa para sostener conclusiones.'})
        types = ex['close_types']
        time_exits = sum(v['trades'] for k, v in types.items() if k in TIME_EXIT_TYPES)
        if n and time_exits / n >= 0.5:
            out.append({'code': 'TIME_EXIT_DOMINATED', 'sample': sample, 'severity': 'medium',
                        'evidence': {'share': round(time_exits / n, 3), 'close_types': {k: v['trades'] for k, v in types.items()}},
                        'note': 'La mayoría de las salidas las decide el reloj, no el objetivo ni el stop.'})
        pt = types.get('PT', {}).get('trades', 0)
        if n and pt / n <= 0.15:
            out.append({'code': 'PT_RARELY_HIT', 'sample': sample, 'severity': 'medium',
                        'evidence': {'pt_share': round(pt / n, 3)}, 'note': 'El objetivo de beneficio casi nunca se alcanza: puede estar demasiado lejos.'})
        sl = types.get('SL', {}).get('trades', 0)
        if n and sl / n >= 0.35:
            out.append({'code': 'SL_HIT_SHARE_HIGH', 'sample': sample, 'severity': 'medium',
                        'evidence': {'sl_share': round(sl / n, 3), 'sl_net': types['SL']['net']}})
        if ex.get('mean_giveback_winners') is not None and s.get('avg_win') and ex['mean_giveback_winners'] >= 0.5 * s['avg_win']:
            out.append({'code': 'HIGH_GIVEBACK_FROM_MFE', 'sample': sample, 'severity': 'medium',
                        'evidence': {'mean_giveback_winners': ex['mean_giveback_winners'], 'avg_win': s['avg_win']},
                        'note': 'Las ganadoras devuelven al mercado la mitad o más de su recorrido favorable.'})
        if rm.get('available') and rm.get('losers_after_mfe_ge_1r', 0) >= 5 and (rm.get('share_of_losers_after_mfe_ge_1r') or 0) >= 0.2:
            out.append({'code': 'LOSERS_AFTER_FAVOURABLE_EXCURSION', 'sample': sample, 'severity': 'medium',
                        'evidence': {'losers_after_mfe_ge_1r': rm['losers_after_mfe_ge_1r'], 'share_of_losers': rm['share_of_losers_after_mfe_ge_1r']},
                        'note': 'Una de cada cinco perdedoras o más llegó a estar 1R a favor antes de perder.'})
        if s['net'] and s['costs'] and s['gross'] and s['gross'] > 0 and s['costs'] / s['gross'] >= 0.3:
            out.append({'code': 'COST_SHARE_HIGH', 'sample': sample, 'severity': 'medium',
                        'evidence': {'costs': s['costs'], 'gross': s['gross']}})
        if con.get('net_without_top_3_winners') is not None and s['net'] > 0 and con['net_without_top_3_winners'] <= 0:
            out.append({'code': 'PROFIT_DEPENDS_ON_FEW_TRADES', 'sample': sample, 'severity': 'high',
                        'evidence': {'net': s['net'], 'net_without_top_3_winners': con['net_without_top_3_winners']}})
        for group_name, groups in (('by_entry_hour_local', p['time']['by_entry_hour_local']),
                                   ('by_weekday', p['time']['by_weekday']),
                                   ('by_direction', p['time']['by_direction'])):
            for key, g in groups.items():
                if g['trades'] >= max(10, 0.15 * n) and g['net'] < 0 and s['net'] > 0 and abs(g['net']) >= 0.25 * s['net']:
                    out.append({'code': 'LOSS_CONCENTRATED_SEGMENT', 'sample': sample, 'severity': 'medium',
                                'evidence': {'dimension': group_name, 'segment': key, 'trades': g['trades'], 'net': g['net']},
                                'note': 'Un segmento identificable pierde de forma consistente.'})
        if fr.get('share_of_days_with_trades') is not None and fr['share_of_days_with_trades'] < 0.35:
            out.append({'code': 'LOW_FREQUENCY_FOR_SHORT_EXAM', 'sample': sample, 'severity': 'high',
                        'evidence': {'trades_per_week': fr['trades_per_week'], 'share_of_days_with_trades': fr['share_of_days_with_trades'],
                                     'longest_gap_days': fr['longest_gap_days']},
                        'note': 'Opera menos de uno de cada tres días: en una ventana de 1–5 días suele no haber oportunidad.'})
        for scenario_id, scenario in p.get('exam_screen_provisional', {}).items():
            h5 = scenario['horizons'].get('5', {})
            if h5.get('target_rate') is not None and h5['target_rate'] < 0.10:
                out.append({'code': 'LOW_EXAM_TARGET_RATE_5D', 'sample': sample, 'severity': 'high',
                            'evidence': {'scenario': scenario_id, 'target_rate_5d': h5['target_rate'],
                                         'breach_rate_5d': h5['breach_rate'], 'windows': h5['windows'],
                                         'disjoint_windows': h5['disjoint_windows']},
                            'note': 'Con el tamaño actual, menos del 10 % de las ventanas de cinco días alcanza el objetivo provisional.'})
    return out


def exposure_study(days: dict, contracts=(1, 2, 3, 4), scenarios=PROVISIONAL_EXAM_SCENARIOS) -> dict:
    """Efecto del número de contratos sobre objetivo y ruptura, sin recálculo.

    Válido cuando todas las órdenes tienen tamaño 1 y los costes son por
    contrato: el P&L diario escala linealmente. Mide exposición, NO calidad de
    la estrategia: subir contratos sube a la vez la frecuencia de objetivo y la
    de ruptura, y ambas se presentan juntas.
    """
    result = {}
    for k in contracts:
        scaled_days = {d: {'pl': v['pl'] * k, 'worst_intraday_estimate': v['worst_intraday_estimate'] * k,
                           'trades': v['trades'], 'costs': v['costs'] * k} for d, v in days.items()}
        screen = exam_screen(scaled_days, scenarios)
        result[str(k)] = {sid: {h: {'target_rate': v['target_rate'], 'breach_rate': v['breach_rate'], 'windows': v['windows']}
                                for h, v in s['horizons'].items()} for sid, s in screen.items()}
    return {'contracts': list(contracts), 'by_contracts': result,
            'note': 'Escalado lineal de P&L y excursión; es exposición, no mejora de la estrategia.'}


def diagnose(orders_path: Path, contract: dict, scenarios=PROVISIONAL_EXAM_SCENARIOS,
             reference_orders: Path | None = None) -> dict:
    """Perfil completo. `reference_orders`: órdenes del control para medir los múltiplos R con su riesgo."""
    zone_name = contract['market'].get('resolved_timezone') or 'UTC'
    declared = contract['market'].get('declared_timezone')
    zone = ZoneInfo(zone_name)
    trades = load_orders(orders_path, zone, declared)
    point = infer_point_value(trades)
    reference = (contract['market'].get('reference_contract') or {}).get('point_value')
    if point['point_value'] is not None and reference is not None:
        point['matches_reference_table'] = abs(point['point_value'] - reference) <= 0.01 * reference
    risk_reference = None
    if reference_orders is not None:
        risk_reference = risk_map(load_orders(reference_orders, zone, declared), point['point_value'])
    calendars = sample_calendars(contract)
    samples = {}
    for label in ('IS', 'OOS'):
        selected = [t for t in trades if t['sample'] == label]
        calendar = calendars[label]
        days = daily_results(selected, zone, calendar)
        samples[label] = {
            'range': {'from': calendar[0].isoformat() if calendar else None, 'to': calendar[-1].isoformat() if calendar else None,
                      'weekdays': len(calendar)},
            'summary': summary(selected),
            'concentration': concentration(selected),
            'exit_efficiency': exit_efficiency(selected),
            'r_multiples': r_multiples(selected, point['point_value'], risk_reference),
            'time': time_profile(selected, zone),
            'frequency': frequency(selected, days),
            'exam_screen_provisional': exam_screen(days, scenarios),
            'daily_pl': {d.isoformat(): round(v['pl'], 2) for d, v in days.items() if v['trades']},
        }
    profile = {
        'schema': SCHEMA, 'generated_utc': datetime.now(timezone.utc).isoformat(),
        'orders_path': str(orders_path), 'timezone': zone_name, 'declared_timezone': declared,
        'timestamp_interpretation': 'EXCHANGE_LOCAL_AS_WRITTEN' if declared == 'Exchange' else 'UTC_CONVERTED_TO_EXCHANGE',
        'point_value': point, 'trades_total': len(trades), 'samples': samples,
        'limitations': [
            'Órdenes cerradas con MAE/MFE por operación; no hay trayectoria intradía completa.',
            'El cribado de examen usa escenarios provisionales explícitos, no reglas de una empresa.',
            'Las ventanas solapadas dependen entre sí; ver disjoint_windows como tamaño efectivo.',
            'La muestra OOS es de desarrollo si se consulta para decidir; no es una prueba final reservada.',
        ],
    }
    profile['findings'] = findings(profile)
    return profile


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--orders', type=Path, required=True)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--reference-orders', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding='utf-8'))
    result = diagnose(args.orders, contract, reference_orders=args.reference_orders)
    text = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text)
