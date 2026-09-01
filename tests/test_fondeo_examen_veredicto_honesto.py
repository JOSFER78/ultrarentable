"""tests/test_fondeo_examen_veredicto_honesto.py — W4.1 (AG-C): el examen de fondeo debe
DECIDIR con la verificación honesta barra a barra, nunca con el bootstrap optimista solo.

Antes del fix, `scripts/fondeo_examen.py::main()` calculaba
`reejecutar_examen_barra_a_barra()` (verificación real sobre equity FLOTANTE, F02.3) pero la
variable `cumple_sellado` -- y por tanto el veredicto "CUMPLE" impreso y persistido en el
ranking -- se derivaba EXCLUSIVAMENTE del Monte Carlo por bootstrap (`evaluar_negocio` /
`evaluar_rendimiento_mensual`), que remuestrea PnL YA CERRADO por operación y es ciego a la
excursión adversa intra-operación. Con 0 candidatas FONDEO reconstruibles hoy el bug era
inerte, pero en cuanto exista una candidata con blueprint reconstruible cuya reproducción
honesta reviente la cuenta (`prop_firm_busted=True`), el bootstrap podía seguir siendo
optimista y el script imprimir/persistir "CUMPLE" sobre una cuenta reventada.

Este test prueba la función pura `determinar_veredicto_sellado()` (extraída exactamente de
esa decisión) con un caso `prop_firm_busted=True` construido explícitamente -- un test de la
función, no un dato de mercado inventado -- y demuestra que el resultado JAMÁS es "CUMPLE",
sea cual sea el veredicto del bootstrap. También cubre el fail-closed: sin verificación
disponible (verif_flotante=None, p.ej. sin blueprint reconstruible o --sin-verificacion-flotante)
el veredicto es SIEMPRE "NO_EVALUABLE", nunca "CUMPLE" por defecto ni una caída silenciosa al
bootstrap.
"""
from __future__ import annotations

import itertools

from scripts.fondeo_examen import determinar_veredicto_sellado


def test_cuenta_reventada_verificada_jamas_es_cumple_aunque_el_bootstrap_diga_que_si():
    """Caso central de aceptación W4.1: verif_flotante con prop_firm_busted=True. Se prueban
    AMBOS valores de cumple_bootstrap (True y False) -- el veredicto honesto debe ganar
    siempre, jamás "CUMPLE"."""
    verif_flotante_reventada = {
        "verificado_equity_flotante": True,
        "engine_version_reejecucion": "5.17.0",
        "prop_firm_busted": True,
        "prop_firm_violations": ["TRAILING_DD_INTRADAY"],
        "trades_oos_reales": 214,
        "profit_factor_oos_real": 1.31,
        "net_profit_oos_usd_real": 4200.0,
    }
    for cumple_bootstrap in (True, False):
        veredicto = determinar_veredicto_sellado(cumple_bootstrap, verif_flotante_reventada)
        assert veredicto != "CUMPLE", (
            f"cumple_bootstrap={cumple_bootstrap}: una cuenta VERIFICADA como reventada "
            f"(prop_firm_busted=True) nunca puede producir el veredicto CUMPLE, pero se "
            f"obtuvo {veredicto!r}."
        )
        assert veredicto == "NO_CUMPLE"


def test_barrido_exhaustivo_nunca_cumple_con_cuenta_reventada():
    """Barrido de todas las combinaciones de violaciones/métricas junto a
    prop_firm_busted=True: en NINGUNA combinación el veredicto es CUMPLE. Encapsula la
    propiedad de aceptación como invariante, no solo como un caso puntual."""
    violaciones_posibles = ([], ["TRAILING_DD_INTRADAY"], ["PERDIDA_DIARIA", "TRAILING_DD_INTRADAY"])
    pf_posibles = (0.4, 1.0, 1.8, 3.0)
    for cumple_bootstrap, violaciones, pf in itertools.product((True, False), violaciones_posibles, pf_posibles):
        verif = {
            "verificado_equity_flotante": True,
            "engine_version_reejecucion": "5.17.0",
            "prop_firm_busted": True,
            "prop_firm_violations": violaciones,
            "trades_oos_reales": 250,
            "profit_factor_oos_real": pf,
            "net_profit_oos_usd_real": -500.0,
        }
        veredicto = determinar_veredicto_sellado(cumple_bootstrap, verif)
        assert veredicto == "NO_CUMPLE", (
            f"cumple_bootstrap={cumple_bootstrap} violaciones={violaciones} pf={pf}: "
            f"se esperaba NO_CUMPLE (cuenta reventada verificada), se obtuvo {veredicto!r}"
        )


def test_sin_verificacion_es_siempre_no_evaluable_fail_closed():
    """FAIL-CLOSED: sin verif_flotante (None) -- p.ej. sin blueprint reconstruible, dataset
    con SHA-256 distinto al certificado, o --sin-verificacion-flotante -- el veredicto es
    SIEMPRE NO_EVALUABLE, nunca CUMPLE por defecto ni una caída silenciosa al bootstrap
    (aunque el bootstrap diga que sí cumple)."""
    assert determinar_veredicto_sellado(True, None) == "NO_EVALUABLE"
    assert determinar_veredicto_sellado(False, None) == "NO_EVALUABLE"


def test_cuenta_no_reventada_verificada_respeta_el_resultado_economico_del_bootstrap():
    """Con verificación disponible Y la cuenta SIN reventar en la reproducción real, el
    veredicto sigue al resultado económico del bootstrap (mensual mediano / P(romper) sobre
    el horizonte) -- ni más optimista ni más pesimista que eso."""
    verif_ok = {
        "verificado_equity_flotante": True,
        "engine_version_reejecucion": "5.17.0",
        "prop_firm_busted": False,
        "prop_firm_violations": [],
        "trades_oos_reales": 240,
        "profit_factor_oos_real": 1.6,
        "net_profit_oos_usd_real": 8000.0,
    }
    assert determinar_veredicto_sellado(True, verif_ok) == "CUMPLE"
    assert determinar_veredicto_sellado(False, verif_ok) == "NO_CUMPLE"


def test_veredicto_es_siempre_uno_de_los_tres_valores_documentados():
    """No hay un cuarto estado posible ni un booleano ambiguo: la función es total sobre las
    combinaciones válidas de entrada."""
    valores_validos = {"CUMPLE", "NO_CUMPLE", "NO_EVALUABLE"}
    for cumple_bootstrap in (True, False):
        for verif in (None,
                      {"prop_firm_busted": True},
                      {"prop_firm_busted": False}):
            assert determinar_veredicto_sellado(cumple_bootstrap, verif) in valores_validos
