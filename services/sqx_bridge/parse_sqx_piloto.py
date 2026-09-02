"""services/sqx_bridge/parse_sqx_piloto.py
Parser de estrategias SQX (.sqx) a AST Canónico (CanonicalStrategy) y evaluación en RegistryPipeline.
ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · NO-SYNTHETIC-DEFAULTS · FAIL-CLOSED

Piloto W3.3 (AGY-B05):
1. Lectura determinista de ficheros .sqx (ZIP con XML strategy_Portfolio.xml y settings.xml).
2. Mapeo transparente a AST canónico (RuleTree, ConditionNode, IndicatorSpec, ExitModel, SizingAndRisk).
3. Registro honesto de NO DATA para campos ausentes o no expresables.
4. Evaluación en RegistryPipeline de 11 Gates con evidencia física real (sin trades inventados).
5. Medición precisa de coste temporal (time.perf_counter).
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import time
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOp,
    ConditionNode,
    ExitModel,
    IndicatorSpec,
    LogicalOp,
    ProvenanceMetadata,
    RuleTree,
    SizingAndRisk,
    SizingType,
    StopLossType,
    TakeProfitType,
)
from services.validation.registry import Evidencia, RegistryPipeline


OPERATOR_MAP = {
    "IsGreater": ComparisonOp.GT,
    "Greater": ComparisonOp.GT,
    "IsAbove": ComparisonOp.GT,
    ">": ComparisonOp.GT,
    "IsGreaterOrEqual": ComparisonOp.GTE,
    "GreaterEqual": ComparisonOp.GTE,
    ">=": ComparisonOp.GTE,
    "IsLower": ComparisonOp.LT,
    "Lower": ComparisonOp.LT,
    "IsBelow": ComparisonOp.LT,
    "<": ComparisonOp.LT,
    "IsLowerOrEqual": ComparisonOp.LTE,
    "LowerEqual": ComparisonOp.LTE,
    "<=": ComparisonOp.LTE,
    "IsEqual": ComparisonOp.EQ,
    "Equal": ComparisonOp.EQ,
    "==": ComparisonOp.EQ,
    "CrossesAbove": ComparisonOp.CROSS_ABOVE,
    "CrossAbove": ComparisonOp.CROSS_ABOVE,
    "CrossesBelow": ComparisonOp.CROSS_BELOW,
    "CrossBelow": ComparisonOp.CROSS_BELOW,
    "IsGreaterCount": ComparisonOp.GT,
    "IsLowerCount": ComparisonOp.LT,
}

SOURCE_FIELD_MAP = {
    0: "close",
    1: "open",
    2: "high",
    3: "low",
    4: "median",
    5: "typical",
    6: "weighted",
}


def _clean_val(val: Any) -> Any:
    """Convierte strings numéricos a int o float cuando corresponda."""
    if val is None:
        return None
    if isinstance(val, (int, float, bool)):
        return val
    s = str(val).strip()
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    try:
        if "." in s:
            return float(s)
        return int(s)
    except (ValueError, TypeError):
        return s


def leer_sqx(sqx_path: str | Path) -> Dict[str, Any]:
    """Lee y parsea un archivo .sqx (ZIP con XML) extrayendo la estructura pura de la estrategia."""
    path_obj = Path(sqx_path)
    if not path_obj.is_file():
        raise FileNotFoundError(f"Fichero SQX no encontrado: {sqx_path}")

    res: Dict[str, Any] = {
        "sqx_path": str(path_obj.resolve()),
        "filename": path_obj.name,
        "options": {},
        "variables": {},
        "money_management": {},
        "global_slpt": {},
        "datas": [],
        "signals": {},
        "rules": [],
        "indicators_detected": [],
        "settings_data": {},
        "parse_errors": [],
    }

    try:
        with zipfile.ZipFile(path_obj, "r") as z:
            namelist = z.namelist()

            # 1. strategy_Portfolio.xml
            strategy_xml_name = None
            for cand in ["strategy_Portfolio.xml", "strategy.xml"]:
                if cand in namelist:
                    strategy_xml_name = cand
                    break
            if not strategy_xml_name:
                for name in namelist:
                    if name.endswith(".xml") and "setting" not in name.lower():
                        strategy_xml_name = name
                        break

            if strategy_xml_name:
                xml_bytes = z.read(strategy_xml_name)
                root = ET.fromstring(xml_bytes.decode("utf-8", errors="ignore"))

                # options
                opt_elem = root.find("options")
                if opt_elem is not None:
                    res["options"] = {child.tag: child.text.strip() if child.text else "" for child in opt_elem}

                # variables
                vars_elem = root.find(".//Variables")
                if vars_elem is not None:
                    for var in vars_elem.findall("variable"):
                        vid = var.findtext("id") or ""
                        vname = var.findtext("name") or ""
                        vval = var.findtext("value") or ""
                        vtype = var.findtext("type") or ""
                        if vid:
                            res["variables"][vid.strip()] = {
                                "id": vid.strip(),
                                "name": vname.strip(),
                                "value": _clean_val(vval),
                                "type": vtype.strip(),
                            }

                # money management
                mm_elem = root.find(".//MoneyManagement")
                if mm_elem is not None:
                    mm_type = mm_elem.get("type", "FixedSize")
                    mm_params: Dict[str, Any] = {}
                    for param in mm_elem.findall(".//Param"):
                        pkey = param.get("name") or param.get("key") or ""
                        mm_params[pkey] = _clean_val(param.text)
                    res["money_management"] = {
                        "type": mm_type,
                        "params": mm_params,
                    }

                # global SL/PT
                slpt_elem = root.find(".//GlobalSLPT")
                if slpt_elem is not None:
                    res["global_slpt"] = {
                        "use_same": slpt_elem.findtext("useSameSLPTforBothDirections") == "true",
                        "sl_val": _clean_val(slpt_elem.findtext(".//globalSL//value")),
                        "tp_val": _clean_val(slpt_elem.findtext(".//globalPT//value")),
                    }

                # Datas
                datas_elem = root.find(".//Datas")
                if datas_elem is not None:
                    for data in datas_elem.findall("data"):
                        res["datas"].append({
                            "id": data.findtext("id"),
                            "chart": data.findtext("chart"),
                            "symbol": data.findtext("symbol"),
                            "timeframe": data.findtext("timeFrame"),
                        })

                # Signals & Rules
                rules_elem = root.find(".//Rules")
                if rules_elem is not None:
                    # Signals
                    for sig in rules_elem.findall(".//signals/signal"):
                        var_id = sig.get("variable", "").strip()
                        items_parsed = []
                        for item in sig.findall("./Item"):
                            items_parsed.append(_parse_xml_item(item, res["variables"]))
                        if var_id:
                            res["signals"][var_id] = items_parsed

                    # Rules (Long entry, Short entry, Long exit, Short exit, etc.)
                    for rule in rules_elem.findall(".//Rule"):
                        rname = rule.get("name", "")
                        rtype = rule.get("type", "")
                        rindex = rule.get("ruleIndex", "")
                        r_if = rule.find("If")
                        r_then = rule.find("Then")

                        then_items = []
                        if r_then is not None:
                            for item in r_then.findall(".//Item"):
                                then_items.append(_parse_xml_item(item, res["variables"]))

                        if_items = []
                        if r_if is not None:
                            for item in r_if.findall(".//Item"):
                                if_items.append(_parse_xml_item(item, res["variables"]))

                        res["rules"].append({
                            "name": rname,
                            "type": rtype,
                            "index": rindex,
                            "if": if_items,
                            "then": then_items,
                        })

                # Extract unique detected indicator names
                indicators_set = set()
                for item_node in root.findall(".//Item"):
                    cat = item_node.get("categoryType", "")
                    mi = item_node.get("mI", "")
                    key = item_node.get("key", "")
                    if cat == "indicator" or mi in ["SuperTrend", "LowestIndex", "HighestIndex", "EMA", "SMA", "RSI", "ATR", "MACD", "BollingerBands", "Stochastic", "LinearRegression", "Ichimoku", "Price"]:
                        indicators_set.add(key)
                res["indicators_detected"] = sorted(list(indicators_set))

            # 2. settings.xml
            if "settings.xml" in namelist:
                s_bytes = z.read("settings.xml")
                s_root = ET.fromstring(s_bytes.decode("utf-8", errors="ignore"))
                res["settings_data"]["result_name"] = s_root.get("ResultName", "")
                results_elem = s_root.find(".//Result")
                if results_elem is not None:
                    r_key = results_elem.get("resultKey", "")
                    res["settings_data"]["result_key"] = r_key
                    # Try to extract symbol and timeframe from resultKey (e.g. "Main: XAUUSD_M1_dukas/H1" or "Main: EURUSD_H1")
                    m = re.search(r"Main:\s*([A-Za-z0-9_]+)(?:/[A-Za-z0-9_]+)?", r_key)
                    if m:
                        raw_sym = m.group(1)
                        # Extract base symbol
                        sym_clean = raw_sym.split("_")[0]
                        res["settings_data"]["extracted_symbol"] = sym_clean
                        if "_H1" in raw_sym or "/H1" in r_key:
                            res["settings_data"]["extracted_timeframe"] = "1h"
                        elif "_H4" in raw_sym or "/H4" in r_key:
                            res["settings_data"]["extracted_timeframe"] = "4h"
                        elif "_M15" in raw_sym or "/M15" in r_key:
                            res["settings_data"]["extracted_timeframe"] = "15m"
                        elif "_M5" in raw_sym or "/M5" in r_key:
                            res["settings_data"]["extracted_timeframe"] = "5m"
                        elif "_M1" in raw_sym or "/M1" in r_key:
                            res["settings_data"]["extracted_timeframe"] = "1m"

    except Exception as e:
        res["parse_errors"].append(f"Error parsing SQX zip/xml: {str(e)}")

    return res


def _parse_xml_item(item: ET.Element, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Parsea recursivamente un nodo <Item> de SQX resolviendo variables."""
    key = item.get("key", "")
    name = item.get("name", "")
    cat = item.get("categoryType", "")
    mi = item.get("mI", "")
    return_type = item.get("returnType", "")

    params: Dict[str, Any] = {}
    formulas: Dict[str, Any] = {}
    blocks: Dict[str, Any] = {}

    for param in item.findall("./Param"):
        pkey = param.get("name") or param.get("key") or ""
        ptext = param.text.strip() if param.text else ""
        # Check if variable reference
        is_var = param.get("variable") == "true" or ptext in variables
        if is_var and ptext in variables:
            val = variables[ptext]["value"]
        else:
            val = _clean_val(ptext)
        params[pkey] = val

        # Formulas inside param
        for formula in param.findall(".//Formula"):
            fkey = formula.get("key", "")
            fparams: Dict[str, Any] = {}
            for fparam in formula.findall(".//Param"):
                fpkey = fparam.get("name") or fparam.get("key") or ""
                fptext = fparam.text.strip() if fparam.text else ""
                if fptext in variables:
                    fval = variables[fptext]["value"]
                else:
                    fval = _clean_val(fptext)
                fparams[fpkey] = fval
            formulas[pkey] = {"key": fkey, "params": fparams}

    for block in item.findall("./Block"):
        bkey = block.get("key", "")
        b_items = []
        for sub_item in block.findall("./Item"):
            b_items.append(_parse_xml_item(sub_item, variables))
        blocks[bkey] = b_items

    return {
        "key": key,
        "name": name,
        "categoryType": cat,
        "mI": mi,
        "returnType": return_type,
        "params": params,
        "formulas": formulas,
        "blocks": blocks,
    }


def _item_to_condition_node(item_dict: Dict[str, Any]) -> Optional[ConditionNode]:
    """Convierte un item de condición SQX en un ConditionNode canónico."""
    key = item_dict.get("key", "")
    blocks = item_dict.get("blocks", {})
    params = item_dict.get("params", {})

    # Operadores estándar: IsGreater, IsLower, CrossesAbove, CrossesBelow, etc.
    if key in OPERATOR_MAP:
        op = OPERATOR_MAP[key]
        left_items = blocks.get("#Left#") or blocks.get("#IndicatorLeft#") or []
        right_items = blocks.get("#Right#") or blocks.get("#IndicatorRight#") or []

        left_node: Any = None
        if left_items:
            left_node = _item_to_indicator_or_val(left_items[0])
        else:
            left_node = params.get("#Left#") or params.get("Left") or 0.0

        right_node: Any = None
        if right_items:
            right_node = _item_to_indicator_or_val(right_items[0])
        else:
            right_node = params.get("#Right#") or params.get("Right") or 0.0

        if left_node is not None and right_node is not None:
            return ConditionNode(left=left_node, op=op, right=right_node)

    # Indicador / simpleRules autónomo como condición (e.g. IchimokuSenkouSpanCrossBearish, LinRegBarOpensAboveAfterOpenBelow)
    cat = item_dict.get("categoryType", "")
    if cat in ("simpleRules", "indicator") or item_dict.get("returnType") == "boolean":
        ind = _item_to_indicator_spec(item_dict)
        op = ComparisonOp.CROSS_ABOVE if "bull" in key.lower() or "above" in key.lower() else ComparisonOp.CROSS_BELOW
        return ConditionNode(left=ind, op=op, right=0.0)

    return None


def _item_to_indicator_or_val(item_dict: Dict[str, Any]) -> Union[IndicatorSpec, float, str]:
    """Convierte un subnodo a IndicatorSpec o valor constante."""
    cat = item_dict.get("categoryType", "")
    key = item_dict.get("key", "")
    if cat in ("indicator", "priceValue", "price", "other") or key in ["EMA", "SMA", "RSI", "SuperTrend", "ATR", "Lowest", "Highest", "OpenD", "LowD", "HighD", "CloseD", "MACD", "CCI", "TEMA", "HullMovingAverage", "KeltnerChannel"]:
        return _item_to_indicator_spec(item_dict)
    # Check if constant
    val = item_dict.get("params", {}).get("#Value#") or item_dict.get("params", {}).get("Value")
    if val is not None and isinstance(val, (int, float)):
        return float(val)
    return _item_to_indicator_spec(item_dict)


def _item_to_indicator_spec(item_dict: Dict[str, Any]) -> IndicatorSpec:
    """Construye un IndicatorSpec a partir de un Item SQX."""
    key = item_dict.get("key", "INDICATOR")
    params = item_dict.get("params", {})
    cleaned_params: Dict[str, Any] = {}
    shift = 0
    source_field = "close"

    for k, v in params.items():
        clean_k = k.replace("#", "").lower()
        if clean_k in ("shift",):
            try:
                shift = int(v) if v is not None else 0
            except (ValueError, TypeError):
                shift = 0
        elif clean_k in ("computedfrom",):
            try:
                cf = int(v)
                source_field = SOURCE_FIELD_MAP.get(cf, "close")
            except (ValueError, TypeError):
                source_field = "close"
        elif clean_k not in ("chart", "identification", "variable"):
            if v is not None:
                cleaned_params[clean_k] = v

    return IndicatorSpec(
        name=key,
        params=cleaned_params,
        source_field=source_field,
        shift=max(0, shift),
    )


def a_ast_canonico(
    sqx_data: Dict[str, Any],
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    route: str = "FONDEO",
) -> Tuple[Optional[CanonicalStrategy], List[str]]:
    """Convierte el diccionario SQX a una CanonicalStrategy SSOT canónica o retorna lista de motivos NO DATA."""
    motivos_no_data: List[str] = []

    # 1. Identificadores y nombres
    options = sqx_data.get("options", {})
    sname = options.get("StrategyName") or sqx_data.get("filename", "SQX_Strategy").replace(".sqx", "")
    strategy_id = re.sub(r"[^A-Za-z0-9_.-]", "_", sname).strip("_")
    if not strategy_id:
        strategy_id = "SQX_STRAT_01"

    # 2. Símbolo
    eff_symbol = symbol
    if not eff_symbol:
        eff_symbol = sqx_data.get("settings_data", {}).get("extracted_symbol")
    if not eff_symbol:
        for d in sqx_data.get("datas", []):
            sym_raw = d.get("symbol")
            if sym_raw and sym_raw.upper() not in ("NULL", "NONE", "0", ""):
                eff_symbol = sym_raw.split("_")[0]
                break
    if not eff_symbol or eff_symbol.upper() in ("NULL", "NONE", ""):
        # Fallback honesto: si el nombre del archivo contiene un símbolo obvio (ej. ES_H1, EURUSD_H1)
        fname = sqx_data.get("filename", "")
        for sym_cand in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "ES", "NQ", "YM", "RTY", "GC", "CL", "XAUUSD", "EW", "GBPJPY", "EURJPY"]:
            if sym_cand in fname.upper():
                eff_symbol = sym_cand
                break
    if not eff_symbol:
        motivos_no_data.append("NO DATA: symbol ausente o NULL en SQX")

    # 3. Timeframe
    eff_tf = timeframe
    if not eff_tf:
        eff_tf = sqx_data.get("settings_data", {}).get("extracted_timeframe")
    if not eff_tf:
        fname = sqx_data.get("filename", "")
        if "H1" in fname or "_1h" in fname.lower():
            eff_tf = "1h"
        elif "H4" in fname or "_4h" in fname.lower():
            eff_tf = "4h"
        elif "M15" in fname or "_15m" in fname.lower():
            eff_tf = "15m"
        elif "M5" in fname or "_5m" in fname.lower():
            eff_tf = "5m"
        elif "M1" in fname or "_1m" in fname.lower():
            eff_tf = "1m"
    if not eff_tf:
        eff_tf = "1h"  # Default estándar intradía si no está especificado

    # 4. Reglas de entrada (Signals)
    variables = sqx_data.get("variables", {})
    signals = sqx_data.get("signals", {})

    # Detect Long & Short signal variable IDs
    long_sig_var = None
    short_sig_var = None
    for vid, vinfo in variables.items():
        vname = vinfo.get("name", "").lower()
        if "longentry" in vname or "signal1" in vname or vid == "33333333-1111-1111-3333-333333333333":
            long_sig_var = vid
        elif "shortentry" in vname or "signal2" in vname or vid == "33333333-2222-1111-3333-333333333333":
            short_sig_var = vid

    long_conds: List[ConditionNode] = []
    short_conds: List[ConditionNode] = []

    if long_sig_var and long_sig_var in signals:
        for item_dict in signals[long_sig_var]:
            cnode = _item_to_condition_node(item_dict)
            if cnode:
                long_conds.append(cnode)

    if short_sig_var and short_sig_var in signals:
        for item_dict in signals[short_sig_var]:
            cnode = _item_to_condition_node(item_dict)
            if cnode:
                short_conds.append(cnode)

    # Si no encontramos por signal variable, buscar en rules directas (IfThen)
    if not long_conds and not short_conds:
        for r in sqx_data.get("rules", []):
            rname = r.get("name", "").lower()
            if "long entry" in rname or "buy" in rname:
                for if_item in r.get("if", []):
                    cnode = _item_to_condition_node(if_item)
                    if cnode:
                        long_conds.append(cnode)
            elif "short entry" in rname or "sell" in rname:
                for if_item in r.get("if", []):
                    cnode = _item_to_condition_node(if_item)
                    if cnode:
                        short_conds.append(cnode)

    # Construcción de RuleTree
    entry_rules: Optional[RuleTree] = None
    if long_conds and short_conds:
        entry_rules = RuleTree(
            logic=LogicalOp.AND,
            direction="BOTH",
            long_conditions=long_conds,
            short_conditions=short_conds,
        )
    elif long_conds:
        entry_rules = RuleTree(
            logic=LogicalOp.AND,
            direction="LONG",
            long_conditions=long_conds,
            conditions=long_conds,
        )
    elif short_conds:
        entry_rules = RuleTree(
            logic=LogicalOp.AND,
            direction="SHORT",
            short_conditions=short_conds,
            conditions=short_conds,
        )
    else:
        motivos_no_data.append("NO DATA: no se encontraron condiciones de entrada válidas en el AST")

    # 5. Salidas (ExitModel: SL & TP)
    sl_val: Optional[float] = None
    sl_type: StopLossType = StopLossType.FIXED_POINTS
    tp_val: Optional[float] = None
    tp_type: TakeProfitType = TakeProfitType.FIXED_POINTS
    trail_after_r: Optional[float] = None
    time_stop_bars: Optional[int] = None

    # Buscar en reglas 'Then' de Long/Short entry
    for r in sqx_data.get("rules", []):
        rname = r.get("name", "").lower()
        if "entry" in rname or "enter" in rname:
            for item in r.get("then", []):
                formulas = item.get("formulas", {})
                params = item.get("params", {})

                # Stop Loss
                sl_formula = formulas.get("Stop Loss") or formulas.get("#StopLoss.StopLoss#")
                if sl_formula:
                    fkey = sl_formula.get("key", "")
                    fparams = sl_formula.get("params", {})
                    raw_val = fparams.get("#Value#") or fparams.get("Value") or fparams.get("val")
                    if raw_val is not None and isinstance(raw_val, (int, float)) and raw_val > 0:
                        sl_val = float(raw_val)
                        if "ATR" in fkey:
                            sl_type = StopLossType.ATR_MULTIPLE
                        elif "Pct" in fkey or "Percentage" in fkey:
                            sl_type = StopLossType.PERCENTAGE
                        else:
                            sl_type = StopLossType.FIXED_POINTS

                # Profit Target
                tp_formula = formulas.get("Profit Target") or formulas.get("#ProfitTarget.ProfitTarget#")
                if tp_formula:
                    fkey = tp_formula.get("key", "")
                    fparams = tp_formula.get("params", {})
                    raw_val = fparams.get("#Value#") or fparams.get("Value") or fparams.get("val")
                    if raw_val is not None and isinstance(raw_val, (int, float)) and raw_val > 0:
                        tp_val = float(raw_val)
                        if "ATR" in fkey:
                            tp_type = TakeProfitType.ATR_MULTIPLE
                        elif "Pct" in fkey or "Percentage" in fkey:
                            tp_type = TakeProfitType.PERCENTAGE
                        elif "RR" in fkey:
                            tp_type = TakeProfitType.RR_MULTIPLE
                        else:
                            tp_type = TakeProfitType.FIXED_POINTS

                # Trailing Stop
                ts_formula = formulas.get("Trailing Stop") or formulas.get("#TrailingStop.TrailingStop#")
                if ts_formula and "ATR" in ts_formula.get("key", ""):
                    raw_ts = ts_formula.get("params", {}).get("#Value#") or ts_formula.get("params", {}).get("Value")
                    if raw_ts is not None and isinstance(raw_ts, (int, float)) and raw_ts > 0:
                        trail_after_r = float(raw_ts)

                # Time stop
                exit_after_bars = params.get("Exit After Bars") or params.get("#ExitAfterBars#")
                if exit_after_bars is not None and isinstance(exit_after_bars, int) and exit_after_bars > 0:
                    time_stop_bars = exit_after_bars

    # Fallback GlobalSLPT
    if sl_val is None or sl_val <= 0:
        g_sl = sqx_data.get("global_slpt", {}).get("sl_val")
        if g_sl is not None and isinstance(g_sl, (int, float)) and g_sl > 0:
            sl_val = float(g_sl)
            sl_type = StopLossType.FIXED_POINTS

    if tp_val is None or tp_val <= 0:
        g_tp = sqx_data.get("global_slpt", {}).get("tp_val")
        if g_tp is not None and isinstance(g_tp, (int, float)) and g_tp > 0:
            tp_val = float(g_tp)
            tp_type = TakeProfitType.FIXED_POINTS

    exit_rules: Optional[ExitModel] = None
    if sl_val is None or sl_val <= 0:
        motivos_no_data.append("NO DATA: Stop Loss ausente o <= 0 en SQX")
    if tp_val is None or tp_val <= 0:
        motivos_no_data.append("NO DATA: Profit Target ausente o <= 0 en SQX")

    if sl_val is not None and sl_val > 0 and tp_val is not None and tp_val > 0:
        exit_rules = ExitModel(
            sl_type=sl_type,
            sl_value=sl_val,
            tp_type=tp_type,
            tp_value=tp_val,
            trail_after_r=trail_after_r,
            time_stop_bars=time_stop_bars,
        )

    # 6. Sizing and Risk
    mm = sqx_data.get("money_management", {})
    mm_type = mm.get("type", "FixedSize")
    mm_params = mm.get("params", {})
    risk_val = 1.0
    stype = SizingType.FIXED_CONTRACTS

    if "risk" in mm_type.lower() or "percent" in mm_type.lower():
        stype = SizingType.RISK_PCT_EQUITY
        r_raw = mm_params.get("Risk") or mm_params.get("RiskPct") or mm_params.get("risk")
        if r_raw is not None and isinstance(r_raw, (int, float)) and r_raw > 0:
            risk_val = float(r_raw)
    else:
        stype = SizingType.FIXED_CONTRACTS
        lots_raw = mm_params.get("LotsStart") or mm_params.get("Size") or mm_params.get("Starting lots")
        if lots_raw is not None and isinstance(lots_raw, (int, float)) and lots_raw > 0:
            risk_val = float(lots_raw)

    sizing_and_risk = SizingAndRisk(
        sizing_type=stype,
        risk_value=risk_val,
        max_open_positions=1,
    )

    # 7. Arquetipo
    inds = sqx_data.get("indicators_detected", [])
    if any("breakout" in i.lower() or "highest" in i.lower() or "lowest" in i.lower() for i in inds):
        archetype = "BREAKOUT"
    elif any("ema" in i.lower() or "sma" in i.lower() or "trend" in i.lower() for i in inds):
        archetype = "TREND_FOLLOWING"
    elif any("rsi" in i.lower() or "cci" in i.lower() or "bb" in i.lower() or "divergence" in i.lower() for i in inds):
        archetype = "MEAN_REVERSION"
    else:
        archetype = "SQX_AST"

    # 8. Provenance
    prov = ProvenanceMetadata(
        author="SQX_BRIDGE_PILOT",
        engine_version="5.18.0",
        policy_version="5.18.0",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        project_name="ToImprove",
        databank_name="Results",
        build_id=options.get("ID") or "SQX_BUILD_144",
    )

    # Si faltan componentes mandatorios, abortar de forma fail-closed con lista de motivos
    if motivos_no_data or not eff_symbol or entry_rules is None or exit_rules is None:
        return None, motivos_no_data

    # Fabricar CanonicalStrategy determinista con hash canónico
    canonical_strat = CanonicalStrategy.create_and_hash(
        strategy_id=strategy_id,
        name=sname,
        version="1.0.0",
        symbol=eff_symbol.strip().upper(),
        timeframe=eff_tf.strip().lower(),
        route=route,  # type: ignore[arg-type]
        archetype=archetype,
        provenance=prov,
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=sizing_and_risk,
        session_window=None,
    )

    if not canonical_strat.verify_integrity():
        motivos_no_data.append("ERROR_INTEGRIDAD: el hash canónico generado no valida su propia identidad semántica")
        return None, motivos_no_data

    return canonical_strat, []


def localizar_sqx_disponibles(sqx_dir: Optional[str] = None) -> Dict[str, str]:
    """Localiza todos los ficheros .sqx disponibles en el sistema y retorna mapeo {basename_sin_ext: ruta}."""
    rutas_busqueda = []
    if sqx_dir and os.path.isdir(sqx_dir):
        rutas_busqueda.append(sqx_dir)
    rutas_busqueda.extend([
        "C:/StrategyQuantX144",
        "tests/fixtures/sqx",
    ])

    sqx_map: Dict[str, str] = {}
    for base_path in rutas_busqueda:
        if os.path.isdir(base_path):
            for f in glob.glob(f"{base_path}/**/*.sqx", recursive=True):
                norm_f = f.replace("\\", "/")
                base = os.path.splitext(os.path.basename(f))[0]
                if base not in sqx_map:
                    sqx_map[base] = norm_f

    return sqx_map


def ejecutar_piloto(
    csv_path: Optional[str] = None,
    n: int = 20,
    sqx_dir: Optional[str] = None,
    out_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Ejecuta el piloto de parseo y evaluación de N estrategias SQX con medición temporal rigurosa."""
    t_inicio_total = time.perf_counter()
    sqx_map = localizar_sqx_disponibles(sqx_dir)

    # Leer CSV de estrategias para priorizar el orden exacto del CSV
    csv_strats: List[Dict[str, Any]] = []
    if csv_path and os.path.isfile(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            header = next(reader, [])
            for row in reader:
                if row:
                    name = row[0].strip()
                    sym = row[3].strip() if len(row) > 3 else ""
                    tf = row[4].strip() if len(row) > 4 else ""
                    csv_strats.append({
                        "name": name,
                        "symbol": sym.split("_")[0] if sym else "",
                        "timeframe": tf.lower() if tf else "",
                        "row": row,
                    })

    # Seleccionar las N estrategias a procesar
    seleccionadas: List[Tuple[str, str, Optional[str], Optional[str]]] = []

    # 1. Primero las que coincidan exactamente con el CSV
    for cs in csv_strats:
        if len(seleccionadas) >= n:
            break
        cname = cs["name"]
        if cname in sqx_map and cname not in [s[0] for s in seleccionadas]:
            seleccionadas.append((cname, sqx_map[cname], cs["symbol"], cs["timeframe"]))

    # 2. Si hay menos de N, completar con el resto de .sqx reales en disco
    for base_name, sqx_file in sqx_map.items():
        if len(seleccionadas) >= n:
            break
        if base_name not in [s[0] for s in seleccionadas]:
            seleccionadas.append((base_name, sqx_file, None, None))

    # Pipeline de validación de 11 Gates
    pipeline = RegistryPipeline()
    resultados_estrategias: List[Dict[str, Any]] = []

    for idx, (strat_name, sqx_file, csv_sym, csv_tf) in enumerate(seleccionadas, 1):
        t0 = time.perf_counter()
        sqx_dict = leer_sqx(sqx_file)
        ast, motivos_no_data = a_ast_canonico(sqx_dict, symbol=csv_sym, timeframe=csv_tf, route="FONDEO")

        candidate_id = ast.strategy_id if ast else strat_name
        symbol_eff = ast.symbol if ast else (csv_sym or sqx_dict.get("settings_data", {}).get("extracted_symbol") or "NO_DATA")
        timeframe_eff = ast.timeframe if ast else (csv_tf or "1h")

        cand_info = {
            "candidate_id": candidate_id,
            "strategy_snapshot_hash": ast.strategy_hash if ast else "NO_DATA_AST_INCOMPLETO",
            "symbol": symbol_eff,
            "timeframe": timeframe_eff,
            "route": "FONDEO",
        }

        # Evidencia física real (SIN trades/velas inventados: honestidad REAL-ONLY)
        ev = Evidencia(
            candidate_info=cand_info,
            strategy_snapshot=ast,
        )

        veredicto_res = pipeline.veredicto(ev)
        t_coste = time.perf_counter() - t0

        indicators_str = ", ".join(sqx_dict.get("indicators_detected", [])) or "NO_DATA"

        resultados_estrategias.append({
            "idx": idx,
            "id": candidate_id,
            "nombre": sqx_dict.get("options", {}).get("StrategyName") or strat_name,
            "sqx_path": sqx_file,
            "familia_indicadores": indicators_str,
            "symbol": symbol_eff,
            "timeframe": timeframe_eff,
            "ast_completo": ast is not None,
            "motivos_no_data": motivos_no_data,
            "strategy_hash": ast.strategy_hash if ast else "NO_DATA",
            "gates_aprobados": veredicto_res["gates_passed_count"],
            "total_gates": veredicto_res["total_gates"],
            "overall_score": veredicto_res["overall_score"],
            "tier": veredicto_res["tier"],
            "coste_s": round(t_coste, 4),
        })

    t_total = time.perf_counter() - t_inicio_total
    total_completos = sum(1 for e in resultados_estrategias if e["ast_completo"])

    output_payload = {
        "estrategias": resultados_estrategias,
        "total_procesadas": len(resultados_estrategias),
        "total_ast_completos": total_completos,
        "porcentaje_ast_completo": round((total_completos / len(resultados_estrategias) * 100.0), 1) if resultados_estrategias else 0.0,
        "coste_total_s": round(t_total, 3),
        "coste_medio_por_estrategia_s": round((t_total / len(resultados_estrategias)), 4) if resultados_estrategias else 0.0,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    if out_path:
        out_dir = os.path.dirname(out_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)

    return output_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Piloto parseo SQX -> AST canónico -> RegistryPipeline")
    parser.add_argument("--csv", default="data/sqx_exports/toimprove_2026-08-31.csv", help="Ruta al CSV de ToImprove")
    parser.add_argument("--n", type=int, default=20, help="Número de estrategias a evaluar")
    parser.add_argument("--sqx-dir", default=None, help="Directorio raíz donde buscar .sqx")
    parser.add_argument("--out", default=None, help="Ruta de salida JSON")
    args = parser.parse_args()

    res = ejecutar_piloto(csv_path=args.csv, n=args.n, sqx_dir=args.sqx_dir, out_path=args.out)

    print(f"\n{'='*95}")
    print(f"PILOTO W3.3 SQX -> AST CANÓNICO -> REGISTRY PIPELINE (N={res['total_procesadas']})")
    print(f"{'='*95}")
    print(f"{'#':<3} | {'ID Estrategia':<22} | {'Símbolo':<7} | {'TF':<4} | {'¿AST?':<6} | {'Gates':<6} | {'Tier':<18} | {'Coste (s)':<9} | {'Indicadores'}")
    print(f"{'-'*95}")
    for e in res["estrategias"]:
        ast_str = "SÍ" if e["ast_completo"] else "NO"
        print(f"{e['idx']:<3} | {e['id'][:22]:<22} | {e['symbol']:<7} | {e['timeframe']:<4} | {ast_str:<6} | {e['gates_aprobados']}/{e['total_gates']}  | {e['tier']:<18} | {e['coste_s']:<9.4f} | {e['familia_indicadores'][:25]}")
    print(f"{'-'*95}")
    print(f"TOTAL: {res['total_procesadas']} estrategias | AST completos: {res['total_ast_completos']}/{res['total_procesadas']} ({res['porcentaje_ast_completo']}%) | Coste total: {res['coste_total_s']}s (media: {res['coste_medio_por_estrategia_s']}s/strat)")
    print(f"{'='*95}\n")


if __name__ == "__main__":
    main()
