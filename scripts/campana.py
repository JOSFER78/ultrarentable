#!/usr/bin/env python3
"""Campana de descubrimiento masiva sobre todas las celdas con datos reales.

Recorre (activo x temporalidad), ejecuta mine.py y acumula la telemetria del embudo
para saber DONDE muere cada celda. Real-only: si una celda no tiene dataset, se registra
como SIN DATOS y se sigue; nunca se inventa nada.
"""
import importlib.util, json, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("mine", ROOT / "scripts" / "mine.py")
mine = importlib.util.module_from_spec(spec); spec.loader.exec_module(mine)

PERFIL = "amplio"   # 675 configuraciones ULTRA / 225 FONDEO por celda

CRIPTO = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "AVAXUSDT", "BNBUSDT", "LINKUSDT", "DOGEUSDT", "SUIUSDT"]
# TRADFI: 13 activos con dataset 4h real verificado en disco (ls data/normalized/*4h*).
# ULTRA los opera TODOS como perpetuo BingX (point_value=1, decision #25).
# FONDEO solo los que tienen micro verificado: SI queda fuera (FONDEO_NO_MICRO en mine.py).
TRADFI = ["ES", "NQ", "YM", "RTY", "GC", "CL", "SI", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
TRADFI_FONDEO = [s for s in TRADFI if s != "SI"]
# 5m y 15m quedan fuera del primer barrido: el coste por operacion se come el edge (PF medio 0,39 y 0,70).
# 4h primero: unica temporalidad donde el edge sobrevive al coste por operacion
# (PF medio medido: 0,39 a 5m | 0,70 a 15m | 0,92 a 1h | viable a 4h).
# SOLO 4h en esta campana: a 1h el coste por operacion deja el PF medio en 0,92 y
# ninguna celda certifica, mientras cada celda cuesta 3x mas (15.300 barras vs 5.100).
# Se retomara 1h cuando el motor de fricción realista permita evaluarlo bien.
TFS = ["4h"]

def main():
    salida = ROOT / "orchestration" / "results" / "campana_02_amplia.jsonl"
    salida.parent.mkdir(parents=True, exist_ok=True)

    # REANUDABILIDAD: si el proceso se cayo, no se empieza de cero. Se leen las celdas ya
    # completadas y se saltan. Sin esto, cada caida perdia horas de CPU.
    hechas = set()
    if salida.exists():
        for linea in salida.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(linea)
                if r.get("estado") in ("OK", "SIN DATOS"):
                    hechas.add((r["track"], r["symbol"], r["tf"]))
            except (json.JSONDecodeError, KeyError):
                continue
    if hechas:
        print(f"Reanudando: {len(hechas)} celdas ya completadas se omiten", flush=True)
    total_cert = 0
    inicio = time.time()
    with salida.open("a", encoding="utf-8") as fh:
        # FONDEO primero: 125 configuraciones por celda frente a 525 de ULTRA, o sea 4x mas rapido,
        # y desbloquea antes el meta-FONDEO. ULTRA continua despues.
        # Orden por rendimiento demostrado: ULTRA sobre cripto es donde el motor corregido
        # certifica (27 en BTCUSDT 4h). Luego FONDEO y por ultimo ULTRA sobre futuros.
        # ULTRA sobre TODO el universo (mandato del usuario: no solo cripto). FONDEO solo micros.
        for track, universo in (("ultra", CRIPTO + TRADFI), ("fondeo", TRADFI_FONDEO)):
            for sym in universo:
                for tf in TFS:
                    if (track, sym, tf) in hechas:
                        continue
                    t0 = time.time()
                    reg = {"ts": datetime.now(timezone.utc).isoformat(), "track": track, "symbol": sym, "tf": tf}
                    try:
                        r = mine.run_mining_pipeline(track=track, symbol=sym, timeframe=tf,
                                                     profile=PERFIL, max_candidates=2000, dry_run=False)
                        tel = r.get("telemetria", [])
                        gates = [x.get("gates_passed", 0) for x in tel if x.get("etapa") == "GATES"]
                        reg.update({
                            "estado": "OK",
                            "certificadas": r.get("certified_count", 0),
                            "embudo": r.get("embudo", {}),
                            "mejor_gates": max(gates) if gates else 0,
                            "mejor_pf": max([float(x.get("pf", 0)) for x in tel], default=0.0),
                            "segundos": round(time.time() - t0, 1),
                        })
                        total_cert += r.get("certified_count", 0)
                    except FileNotFoundError:
                        reg.update({"estado": "SIN DATOS"})
                    except Exception as e:
                        reg.update({"estado": "ERROR", "error": f"{type(e).__name__}: {str(e)[:160]}"})
                    fh.write(json.dumps(reg, ensure_ascii=False) + "\n"); fh.flush()
                    print(f"{track:>6} {sym:>9} {tf:>4} -> {reg.get('estado')} "
                          f"cert={reg.get('certificadas', 0)} mejor_gates={reg.get('mejor_gates', '-')} "
                          f"({reg.get('segundos', 0)}s)", flush=True)
    print(f"\nCAMPANA TERMINADA: {total_cert} certificadas 11/11 en {round((time.time()-inicio)/60,1)} min")
    print(f"Telemetria completa: {salida}")

if __name__ == "__main__":
    main()
