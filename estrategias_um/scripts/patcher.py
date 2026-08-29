#!/usr/bin/env python3
"""MC-fix: desactiva SOLO el metodo RandomizeHistoryData dentro de MonteCarloRetest use=true
(patron de fabrica tpl_build.xml: metodos de aleatorizacion use=false). No toca nada mas.
Uso: python3 patcher.py <ruta_project.cfx> [--apply]
Sin --apply: dry-run (extrae y comprueba en /tmp, NO escribe el project.cfx real)."""
import sys, zipfile, shutil, re, os, subprocess

SRC = sys.argv[1]
APPLY = "--apply" in sys.argv
BACKUP_DIR = "/home/ubuntu/ORDENAR"
WORK = "/tmp/um_mcpatch/work"

def main():
    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)
    with zipfile.ZipFile(SRC) as z:
        z.extractall(WORK)
        names = z.namelist()
    total = 0
    for root, _, files in os.walk(WORK):
        for fn in files:
            if not fn.endswith(".xml"):
                continue
            p = os.path.join(root, fn)
            with open(p, encoding="utf-8") as f:
                txt = f.read()
            cambios = 0
            out = txt
            for m in re.finditer(r'<MonteCarloRetest[^>]*use="true"[^>]*>.*?</MonteCarloRetest>', out, re.S):
                block = m.group(0)
                if 'type="RandomizeHistoryData"' not in block:
                    continue
                nb, n = re.subn(
                    r'(<Method\s+use=")true("\s+type="RandomizeHistoryData")',
                    r'\1false\2',
                    block,
                )
                if n:
                    out = out.replace(block, nb)
                    cambios += n
            if cambios:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(out)
                print(f"patched {os.path.relpath(p, WORK)}: {cambios} x RandomizeHistoryData use=true->false")
                total += cambios
    if not total:
        print("SIN CAMBIOS: no hay RandomizeHistoryData use=true activo dentro de MonteCarloRetest")
        return 2
    if not APPLY:
        print(f"DRY-RUN OK ({total} cambios detectados) - NO se escribe el project.cfx real")
        return 0
    ts = subprocess.run(["date", "+%Y%m%d_%H%M%S"], capture_output=True, text=True).stdout.strip()
    os.makedirs(BACKUP_DIR, exist_ok=True)
    bkp = f"{BACKUP_DIR}/backup_Ultra_Matrix_pre_mcfix_{ts}.cfx"
    shutil.copy2(SRC, bkp)
    print(f"backup: {bkp}")
    tmp_out = SRC + ".new"
    if os.path.exists(tmp_out):
        os.remove(tmp_out)
    with zipfile.ZipFile(tmp_out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(WORK):
            for fn in files:
                p = os.path.join(root, fn)
                z.write(p, os.path.relpath(p, WORK))
    os.replace(tmp_out, SRC)
    with zipfile.ZipFile(SRC) as z:
        bad = z.testzip()
        assert bad is None, f"zip corrupto: {bad}"
        _ = z.namelist()
    print(f"APLICADO y ZIP valido: {SRC} ({len(names)} entradas originales)")
    return 0

sys.exit(main())
