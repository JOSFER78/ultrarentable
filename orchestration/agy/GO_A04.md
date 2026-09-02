# GO_A04 — W1.6: checksum de CONTENIDO en market_ingestor

## Identidad
- ID: A04 · Ola: A · Rama/worktree: JOSFER78/agy-A04 (Orca; la rama real lleva el prefijo del usuario) · Timebox: 45 min
- Variable de entorno obligatoria: AGY_AGENT=A04

## OBJETIVO (una frase verificable)
`MarketDataAuditor.audit` firma `checksum_sha256` = SHA-256 de los BYTES del fichero normalizado que `persist_normalized_dataset` escribe (el mismo criterio que `services/api/app/api/routes.py:168` y `DatasetRepository._verificar_custodia`), con una función reutilizable `verificar_dataset_contra_manifiesto`, y un test demuestra que dos series con mismo conteo y rango y un solo precio distinto dan hashes distintos.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- services/data/market_ingestor.py (existe)
- tests/test_market_ingestor_checksum_contenido.py (nuevo)
- orchestration/results/agy/A04.md (nuevo; el directorio `orchestration/results/agy/` NO existe en este worktree: crearlo)
- orchestration/agy/DONE_A04.md (nuevo; el directorio `orchestration/agy/` NO existe en este worktree: crearlo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- services/data/market_ingestor.py — líneas 106-110 (hash de METADATOS `venue:symbol:interval:n:start:end` y `dataset_id`), 150-170 (serialización `raw_list` y `json.dump` del fichero), 172-191 (manifiesto con `checksumSha256`).
- services/api/app/api/routes.py — líneas 51-56 (`_canonical_json` = `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`, `_sha256_bytes`), 146-170 (`_validate_dataset_artifacts`: `sha256(bytes del fichero) == checksum`, línea 168) y 431-438 (el fichero se escribe con LOS MISMOS bytes que se hashean). ESTE es el criterio canónico; no inventar otro.
- services/data/dataset_repository.py — líneas 107-113 (`_sha256_file`, por bloques) y 136-158 (`_verificar_custodia`: compara `checksum_sha256` del manifiesto con el sha256 del fichero y falla cerrado). Solo lectura.
- contracts/backtest.py — líneas 19-26 (`BarData`: `timestamp_utc_ms` int; open/high/low/close/volume float; `frozen=True`, usar `model_copy(update=...)`).
- tests/test_data_pipeline.py — los 7 tests `test_market_data_*` deben seguir pasando SIN tocarlos.
- data/normalized/ — en este worktree SOLO hay `*_manifest.json` (`.gitignore` líneas 179-180 excluyen los `.json` de velas). Claves de checksum en manifiestos reales: `checksumSha256` (BingX/ingestor) y `checksum_sha256` (Binance/Dukascopy); conteos: `recordCount` / `record_count` / `bar_count`. Un fichero de velas es una lista (Binance/BingX) o un dict con clave `bars` (Dukascopy).

## PASOS (numerados, cortos, en orden; qué comprobar antes de cambiar nada)
1. Punto de partida, sin cambiar nada: `git status --porcelain` (vacío) · `git ls-files data/normalized | grep -v _manifest.json` (solo `.gitkeep` ⇒ NO DATA de velas en el worktree; anotarlo en A04.md) · ejecutar el 2.º comando de ACEPTACIÓN (esperado hoy: `7 passed, 3 deselected`).
2. En `services/data/market_ingestor.py`, añadir a nivel de módulo (entre los imports y `class IngestionAuditReport`), exactamente esta API:
   ```python
   CLAVES_CHECKSUM_MANIFIESTO = ("checksumSha256", "checksum_sha256")
   CLAVES_CONTEO_MANIFIESTO = ("recordCount", "record_count", "bar_count")

   def serializar_velas_canonico(bars: List[BarData]) -> bytes:
       """Bytes EXACTOS del fichero normalizado. Mismo criterio que routes.py::_canonical_json."""
       raw_list = [{"timestamp": b.timestamp_utc_ms, "open": b.open, "high": b.high,
                    "low": b.low, "close": b.close, "volume": b.volume} for b in bars]
       return json.dumps(raw_list, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

   def checksum_contenido_sha256(bars: List[BarData]) -> str:
       return hashlib.sha256(serializar_velas_canonico(bars)).hexdigest()

   def sha256_fichero(path: Path) -> str:  # sha256 de los bytes, leídos por bloques de 1 MiB

   class VerificacionCustodia(BaseModel):
       dataset_path: str; manifest_path: str; hash_fichero: str
       hash_manifiesto: Optional[str] = None      # None => el manifiesto no declara checksum (NO DATA)
       conteo_fichero: Optional[int] = None; conteo_manifiesto: Optional[int] = None
       coincide: bool; motivo: str

   def verificar_dataset_contra_manifiesto(dataset_path: Path, manifest_path: Optional[Path] = None) -> VerificacionCustodia:
   ```
   Reglas de `verificar_dataset_contra_manifiesto`: `manifest_path` por defecto = `dataset_path.with_name(dataset_path.stem + "_manifest.json")`; si falta el dataset o el manifiesto ⇒ `raise FileNotFoundError(...)` (nunca `coincide=True` por defecto); `hash_fichero = sha256_fichero(dataset_path)`; `hash_manifiesto` = valor de la primera clave presente de `CLAVES_CHECKSUM_MANIFIESTO`; `conteo_fichero` = `len(obj)` si el JSON es lista, `len(obj["bars"])` si es dict con `bars`, si no `None`; `conteo_manifiesto` = primera clave presente de `CLAVES_CONTEO_MANIFIESTO`; `coincide = (hash_fichero == hash_manifiesto) and (conteos iguales cuando ambos se conocen)`; `motivo` ∈ {`"OK"`, `"HASH_MISMATCH"`, `"RECORD_COUNT_MISMATCH"`, `"NO DATA: el manifiesto no declara checksum"`}.
3. En `MarketDataAuditor.audit` (líneas 106-108) sustituir las dos líneas del payload de metadatos por `sha_hash = checksum_contenido_sha256(unique_bars)`. Dejar `dataset_id` (línea 110) con `sha_hash[:10]`. NO tocar la detección de orden/duplicados/gaps/calendario (líneas 62-104) ni `is_valid`.
4. En `persist_normalized_dataset`: sustituir `raw_list` (líneas 150-161) y el `json.dump` del fichero (líneas 169-170) por `contenido = serializar_velas_canonico(clean_bars)` y `data_path.write_bytes(contenido)` (así los bytes del fichero son EXACTAMENTE los hasheados; nada de `json.dump` en modo texto). En `manifest_data` añadir UNA sola clave, `"checksumScope": "normalized-file-bytes"`; mantener `"checksumSha256": report.checksum_sha256` y todas las demás claves tal cual.
5. Crear `tests/test_market_ingestor_checksum_contenido.py`. Fixture común: `t0 = 1771718400000`; serie A = `[BarData(timestamp_utc_ms=t0 + i*3600000, open=100+i, high=105+i, low=95+i, close=102+i, volume=50) for i in range(3)]`; serie B = A con `A[1].model_copy(update={"close": 104.0})` (mismo conteo, mismo rango, un precio distinto); `venue="BINGX", symbol="ETH-USDT", interval="1h"`. Cinco tests:
   - `test_mismo_conteo_y_rango_precio_distinto_hash_distinto`: `MarketDataAuditor.audit` de A y de B ⇒ `checksum_sha256` distintos, `dataset_id` distintos, ambos de 64 hex; ninguno igual al hash de metadatos antiguo `sha256(b"BINGX:ETH-USDT:1h:3:1771718400000:1771725600000")` = `5771d5de5bcd6a13c0edabb8f6298caed6fc4fe2d17be1feca7a701523b60763`.
   - `test_checksum_es_sha256_de_los_bytes_del_fichero`: `MarketDataIngestor(data_root=tmp_path).persist_normalized_dataset(A, ...)` ⇒ `hashlib.sha256(data_file.read_bytes()).hexdigest() == report.checksum_sha256 == manifest["checksumSha256"] == "2a5c29e758a06521eafd0f0dcb6277703ac31904f82de127cc303ae52d156de1"`; `manifest["checksumScope"] == "normalized-file-bytes"`; `verificar_dataset_contra_manifiesto(data_file)` ⇒ `coincide is True`, `motivo == "OK"`, `conteo_fichero == conteo_manifiesto == 3`.
   - `test_verificacion_rechaza_fichero_alterado`: tras persistir A, reescribir `data_file` con `serializar_velas_canonico(B)` ⇒ `coincide is False`, `motivo == "HASH_MISMATCH"`, `hash_fichero == "20c8c4c48f4c3432fcb443ed7937d73a8cf225438764393087d4b22fcb1b9a3c"`.
   - `test_verificacion_falla_cerrado_sin_manifiesto`: `manifest_file.unlink()` (es un tmp) ⇒ `pytest.raises(FileNotFoundError)`.
   - `test_datasets_canonicos_del_worktree_verifican`: `raiz = Path(__file__).resolve().parents[1] / "data" / "normalized"`; candidatos = `sorted(p for p in raiz.glob("ds_*.json") if not p.name.endswith("_manifest.json"))`; si está vacío ⇒ `pytest.skip("NO DATA: en este worktree data/normalized solo contiene manifiestos")`; si no, para cada candidato cuyo manifiesto exista, `verificar_dataset_contra_manifiesto(p)` y `assert` con la lista `nombre: motivo` de los que no coinciden.
6. Ejecutar la ACEPTACIÓN completa y pegar la salida cruda en `orchestration/results/agy/A04.md`. Si el 2.º comando deja de dar `7 passed`, arreglar el ingestor, NUNCA el test antiguo.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta él mismo desde la raíz del worktree)
```bash
export AGY_AGENT=A04 PYTHONPATH=.
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_market_ingestor_checksum_contenido.py -q -p no:cacheprovider -rs
# esperado: 4 passed, 1 skipped  (el skip lleva "NO DATA: ..." porque no hay .json de velas en el worktree)
"$PY" -m pytest tests/test_data_pipeline.py -q -p no:cacheprovider -k market_data
# esperado: 7 passed, 3 deselected  (los 3 deselected necesitan velas reales en disco: NO DATA aquí, preexistente)
"$PY" -c "from contracts.backtest import BarData; from services.data.market_ingestor import checksum_contenido_sha256 as c; t=1771718400000; print(c([BarData(timestamp_utc_ms=t+i*3600000, open=100+i, high=105+i, low=95+i, close=102+i, volume=50) for i in range(3)]))"
# esperado: 2a5c29e758a06521eafd0f0dcb6277703ac31904f82de127cc303ae52d156de1
grep -n 'venue}:{symbol}:{interval}' services/data/market_ingestor.py
# esperado: sin salida (el payload de metadatos ha desaparecido)
grep -c "def serializar_velas_canonico\|def checksum_contenido_sha256\|def verificar_dataset_contra_manifiesto" services/data/market_ingestor.py
# esperado: 3
git diff --name-only   # ⊆ TERRITORIO (más GO_A04.md si el ORQ añadió CORRECCION_n)
# esperado: services/data/market_ingestor.py ; y en `git status --porcelain` solo ?? tests/test_market_ingestor_checksum_contenido.py, ?? orchestration/results/agy/, ?? orchestration/agy/
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor (services/validation/engine/ o services/engine_version.py)? NO. `services/data/` no es el motor; no se toca nada de `services/validation/` ni `services/engine_version.py`. Los `dataset_id` de datasets NUEVOS cambian de sufijo (ahora prefijo del hash de contenido): esperado y alineado con `routes.py:433`.
- ¿Ejecuta algo pesado? NO. Solo pytest de dos ficheros (~2 s). Prohibido `pytest` completo, cualquier descarga (`data_downloader`), backfill o script de ingesta.
- Serialización: usar EXACTAMENTE `sort_keys=True, separators=(",", ":"), ensure_ascii=False` y escribir con `write_bytes`. No cambiar los nombres de campo (`timestamp`, `open`, ...): `DatasetRepository.load_bars` los acepta (dataset_repository.py:190). No copiar el formato lista-de-listas de `data/market_ingestor.py` (copia divergente en la raíz del repo, sin importadores): no se toca.
- Hallazgos que se REPORTAN en A04.md y NO se tocan (fuera de territorio): (a) `services/data/data_downloader.py:193-214 y 361-380` escribe el JSON con su propia serialización (`b.model_dump()`) y un manifiesto `checksum_sha256=audit_report.checksum_sha256` ⇒ su manifiesto seguirá sin coincidir con los bytes de SU fichero (tampoco coincidía antes); necesita adoptar `serializar_velas_canonico` en un GO aparte. (b) Manifiestos ya sellados con hash de metadatos no se re-sellan aquí (no hay velas en el worktree). (c) Si el ORQ ejecuta el test de canónicos en el checkout principal, cualquier fallo es un manifiesto con sello de metadatos: se lista, no se "arregla".

## PROHIBIDO (lista negra, sin excepciones)
git add/commit/push/reset/checkout/merge/stash · rm (se aparca en cuarentena/ con MANIFEST SHA-256) · datos sintéticos, mocks, random/seed, valores por defecto ante falta de dato (se escribe NO DATA) · relajar umbrales · escribir fuera del TERRITORIO · tocar services/engine_version.py salvo que este GO lo ordene · procesos largos sin admisión · inventar una salida que no se ejecutó · declarar subagentes que tu CLI no tiene · modificar tests/test_data_pipeline.py, services/data/data_downloader.py, services/data/dataset_repository.py o services/api/app/api/routes.py.

## SALIDA
1. Working tree con los cambios (SIN commit).
2. orchestration/results/agy/A04.md: comandos ejecutados y salida CRUDA pegada literal; lo que no se pudo (incluido "NO DATA: sin .json de velas en data/normalized del worktree"); hallazgos fuera de alcance (data_downloader, data/market_ingestor.py, manifiestos con sello de metadatos); veredicto propio.
3. orchestration/agy/DONE_A04.md (plantilla: orchestration/agy/PLANTILLA_DONE.md; si no existe en el worktree, secciones: Resultado, Ficheros tocados, Comandos de aceptación y salida, Pendiente/NO DATA, Veredicto).
4. Cierre: orca orchestration send --type worker_done --subject "A04 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
