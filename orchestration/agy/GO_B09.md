# GO_B09 — W4.8 + W4.9(a): catálogo de prop firms v2 con `SourceRef` (D6) y endpoint fail-closed; el motor NO se toca

## Identidad
- ID: B09 · Ola: B · Rama/worktree: JOSFER78/agy-B09 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B09, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
Existe `services/fondeo/catalogo_firmas_v2.py` con `SourceRef(confidence: Literal["fetch","ws_official","unverified"], url: str | None, captured_at: str | None, note: str)` y `FirmaV2` cuyos parámetros de riesgo (trailing DD tipo/valor, pérdida diaria, consistencia, mínimo de días, micros permitidos, hora de cierre obligatoria, precio examen, activación, payout) son `None` + `SourceRef(unverified)` salvo que `results/I4_prop_firms_hallazgos.md` aporte cita con fecha y URL; test que impone D6 (valor ≠ None ⇒ confidence ∈ {fetch, ws_official} y url no vacía; nunca `url=""`); y `POST /api/v1/providers/sync` deja de repintar `verified_at` (responde 501 con motivo o re-verifica de verdad; W4.8).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- services/fondeo/ (nuevo: `__init__.py`, `catalogo_firmas_v2.py`)
- services/api/app/api/providers_router.py (SOLO el handler de `POST /api/v1/providers/sync`, líneas ~189-215, y un endpoint nuevo `GET /api/v1/prop-firms/v2` que sirve el catálogo v2 con sus SourceRef)
- tests/test_catalogo_firmas_v2.py (nuevo)
- orchestration/results/agy/B09.md (nuevo) · orchestration/agy/DONE_B09.md (nuevo)
- SOLO LECTURA: services/exploitation_engines/prop_firm_engine.py (`PROP_FIRM_CATALOG` del MOTOR: tocarlo es regla #26 → W4.9(b), tarea aparte del ORQ), services/validation/engine/**.

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/results/I4_prop_firms_hallazgos.md (catálogo re-verificado contra ToS con `[FETCH]`/`NO VERIFICABLE` por dato: ES la fuente; copia la cita y la fecha).
- orchestration/results/M3_plan_catalogo_firmas.md (plan v2 con SourceRef; §1.3 el endpoint que finge frescura).
- orchestration/state/current_phase.md decisiones D6 y D7; PLAN_LOCAL_FONDEO.md W4.8/W4.9/W5.8.
- services/api/app/api/providers_router.py líneas 180-220.
- services/exploitation_engines/prop_firm_engine.py (para conocer los NOMBRES de campo que espera el motor; no los cambias).

## PASOS (numerados, cortos, en orden)
1. Comprobar `git status --porcelain` vacío. Lee I4 entero y tabula qué dato de qué firma tiene cita verificable (Topstep, Apex, MFFU, TradeDay y las demás del expediente).
2. `catalogo_firmas_v2.py`: dataclasses frozen; `CATALOGO_V2: tuple[FirmaV2, ...]` construido a mano desde I4 con un `SourceRef` por campo; función `verificar_catalogo() -> list[str]` que devuelve las violaciones de D6 (vacía si está bien).
3. Endpoint `GET /api/v1/prop-firms/v2` (JSON con firmas y SourceRef por campo). `POST /api/v1/providers/sync`: sustituye el repintado de `verified_at` por `HTTPException(501, detail="sin re-verificación real implementada; ver M3 §1.3")`; nunca escribir fechas de hoy sin consultar una fuente.
4. Tests (reales, sin mocks: `TestClient` de FastAPI sobre la app real): (a) `verificar_catalogo() == []`; (b) para cada firma y campo, valor ≠ None ⇒ confidence válida y url no vacía; (c) `GET /api/v1/prop-firms/v2` 200 y cada campo trae `source`; (d) `POST /api/v1/providers/sync` ⇒ 501 y `verified_at` en BD/JSON no cambia (lee antes y después).
5. Informe con la tabla firma × campo × confidence; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_catalogo_firmas_v2.py -q -p no:cacheprovider            # esperado: >= 4 passed
"$PY" -c "from services.fondeo.catalogo_firmas_v2 import CATALOGO_V2, verificar_catalogo; print(len(CATALOGO_V2), verificar_catalogo())"   # esperado: >= 4 []
grep -n "verified_at" services/api/app/api/providers_router.py | head -5           # esperado: ninguna asignación a 'hoy' en el handler de sync
git diff --name-only -- services/exploitation_engines services/validation/engine services/engine_version.py   # esperado: vacío
git diff --name-only   # ⊆ TERRITORIO; esperado: services/api/app/api/providers_router.py
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO: `PROP_FIRM_CATALOG` del motor se queda como está (W4.9(b) = decisión escrita del ORQ + bump; no aquí).
- ¿Ejecuta algo pesado? NO. Nada de fetch a internet: los datos vienen de I4, que ya los verificó; un dato sin cita en I4 queda `None + unverified`.
- D7: nada comercial (cupones/afiliados) en el catálogo v2.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · escribir fuera del TERRITORIO · tocar el catálogo del motor · datos sin fuente · `url=""` · mocks · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B09.md. 3. orchestration/agy/DONE_B09.md.
4. Cierre: orca orchestration send --type worker_done --subject "B09 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
