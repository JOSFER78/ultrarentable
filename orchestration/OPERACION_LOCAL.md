# OPERACIÓN LOCAL — SSOT de recursos y topología PC + VPS (2026-09-01)

> Complementa (no sustituye) a `OPERACION_VPS.md`: aquel sigue mandando sobre la máquina del
> VPS; este manda sobre el PC y sobre el reparto de trabajo entre ambos.

## 1. La nueva topología

```
        ┌──────────────── PC (local, 32 GB RAM, IP residencial) ────────────────┐
        │ ORQUESTADOR Opus 5 (tmux/WSL2)      SQX StrategyQuant X (Windows GUI) │
        │ Minería cola_mineria/mine.py         Backfill Dukascopy (nohup)       │
        │ BD de trabajo local (SQLite)         Build de la web (next build)     │
        │ Repo git = fuente de código          [futuro] NinjaTrader 8 ejecución │
        └───────────────┬───────────────────────────────────────────────────────┘
                        │  git (código/manifiestos/informes) · rsync/R2 (datasets)
                        │  ssh (operar el VPS) · espejo de lectura (RTDB/export)
        ┌───────────────┴───────────────── VPS (4 cores ARM, 23 GB) ────────────┐
        │ API FastAPI :8000 · Web servida     HERMES VIGÍA (monitor de trades)  │
        │ BD histórica (solo consolidación)   [APAGADO: sqcli, discovery]       │
        └────────────────────────────────────────────────────────────────────────┘
```

**Principio**: el PC calcula y decide; el VPS sirve y vigila. Nada pesado corre en el VPS salvo
orden expresa, y siempre por `services/ops/gobernanza_recursos.py`.

## 2. Reparto de cargas (definitivo)

| Carga | Dónde | Motivo |
| :--- | :--- | :--- |
| Orquestación (Opus + subagentes) | PC | Es donde vive el proyecto ahora |
| Backfill Dukascopy / Binance | PC | I/O-bound; el VPS tardaba días con la CPU ahogada |
| Campañas de minería (backtests) | PC | CPU-bound; `concurrencia = núcleos − 2`, sin steal |
| StrategyQuant X | PC (GUI Windows) | Iterar la config del Builder exige interfaz; libera 8-10 GB del VPS. OJO licencia: puede pedir desactivar el seat del VPS (paso de Emilio) |
| Build de producción de la web | PC | `next build` era "trabajo pesado" prohibido en el VPS |
| Servir API + web | VPS | Es servicio, no cálculo |
| Vigía de trades (Hermes) | VPS | 24/7, cerca de la ejecución; ver `HERMES_VPS_VIGIA.md` |
| Ejecución prop (NT8/Tradovate) | PC (futuro, F08+) | NT8 es Windows-only; IP residencial obligatoria según `docs/conexiones_automatizar/` |
| `git push` a GitHub | PC | El 408 del VPS era su CPU saturada |

## 3. El PC: reglas de la máquina

1. **Entorno de trabajo: WSL2 (Ubuntu)** sobre la copia del repo. Los scripts usan `flock`,
   `nice`, `nohup` y rutas Unix: en Windows nativo no funcionan. La ruta Windows
   `...\UltrarentablePC\ultrarentable` es la misma carpeta que ve WSL vía `/mnt/c/...`.
2. **I/O**: `/mnt/c` (DrvFs) es lento para lecturas masivas. Regla práctica: si una celda tarda
   >2× lo esperado, mover `data/normalized/` a disco ext4 de WSL (`~/ultrarentable_data/`) y
   dejar symlink. Se decide midiendo, no por adelantado.
3. **Presupuesto de recursos**: reservar SIEMPRE 2 núcleos y ~8 GB para el uso normal del PC.
   Minería `--concurrencia (nproc-2)`; si Emilio está usando el PC activamente, la mitad.
   Un solo trabajo de cada clase a la vez (1 backfill + 1 campaña + 1 build máximo).
4. **Persistencia de sesión**: el orquestador vive en `tmux` (`tmux new -s orq` → `claude`).
   Cerrar la ventana no mata nada; `tmux attach -t orq` retoma. Los nohup sobreviven incluso
   al reinicio de la sesión de Claude.
5. **Energía**: suspensión de Windows desactivada mientras haya campañas (el orquestador lo
   recuerda en cada arranque de campaña; ajustarlo es un clic de Emilio si está activado).

## 4. Setup inicial del PC (lo ejecuta el orquestador, una vez)

| # | Paso | Verificación |
| :--- | :--- | :--- |
| 1 | WSL2 Ubuntu operativo (`wsl --version`) | shell responde |
| 2 | `python3.11+`, `uv` (o venv+pip) instalados | `python3 --version` |
| 3 | `.venv` del repo desde `uv.lock`/`pyproject.toml` | `python -c "import services"` OK |
| 4 | `scripts/verificacion_f02.py` — **identidad del motor EN EL PC** | Las 15 celdas IDÉNTICAS a los JSON de `orchestration/results/verificacion_f02_5.17.*.json`. **Sin esto, ninguna campaña local vale**: sería otro motor |
| 5 | BD de trabajo local creada (ver §5) | `cola_mineria.py estado` responde |
| 6 | ssh al VPS con clave (`ssh ubuntu@<vps>`) | `ssh ... 'echo ok'` — la clave la genera el orquestador; añadirla al VPS puede requerir la contraseña UNA vez (ventana Emilio) |
| 7 | Node 18+ para `apps/web` | `npm --version` |

## 5. Datos y base de datos: quién es la fuente de verdad

- **Los datasets pesados NO están en esta copia** (solo manifiestos: `data/normalized/` = 1,1 MB
  de JSON de manifiesto; los datos se sacaron del índice git el 2026-08-31). Recuperación, en
  este orden: (1) `rsync` desde el VPS de lo ya descargado (ES completo 1m/5m/15m, NQ parcial,
  ~algún GB — minutos con buena línea); (2) lo que falte, descarga directa en el PC con
  `services/data_ingestion/dukascopy_feed.py` (símbolo a símbolo, `--concurrency 3`).
  Cada dataset se verifica contra su manifiesto SHA-256 al llegar; si el hash no cuadra ⇒
  re-descarga, jamás "se acepta".
- **BD de trabajo del laboratorio = la del PC** mientras el descubrimiento viva aquí
  (`STATE_DB_PATH` local, misma ruta relativa `~/.local/state/ultrarentable/` dentro de WSL).
  La BD del VPS queda como histórico y como fuente de la web hasta que exista el espejo.
- **Consolidación**: candidatas y evidencia (`data/evidence/<sid>/`) viajan del PC al VPS por
  git (evidencia y manifiestos) y merge-upsert idempotente (BD), con `engine_version` y hashes.
  Nunca al revés: el VPS ya no genera candidatas.
- **La web consume espejo de solo lectura**: export periódico de la BD local → VPS/Firebase
  (RTDB ya tiene `services/sync/firebase_sync_manager.py`; Firestore es alternativa válida).
  La web JAMÁS lee una BD que se esté escribiendo desde otra máquina.
- **Datasets → R2 (opcional, recomendado)**: bucket `ultrarentable-lake` con los consolidados
  Parquet/JSON+zstd y manifiestos; PC y VPS tiran de ahí (egress 0 €). Mientras no exista,
  rsync directo PC↔VPS.

## 6. El VPS: qué queda y cómo se toca

1. **Se toca solo por ssh desde el orquestador.** Cambios de código llegan por `git pull`
   (nunca editar a mano en el VPS).
2. **Ventana sudo única** (con Emilio delante para teclear la contraseña, 10 min):
   - Sección A de `OPERACION_VPS.md`: stop+disable `ultrarentable-discovery`, stop `sqx`,
     `pkill` de mineros huérfanos, comentar cron `improve_cycle.sh`.
   - Optimización del informe externo §8 (versión corregida): backup de `/tmp` del proyecto
     ANTES de limpiar, zRAM DESPUÉS de liberar la máquina, sin `overcommit_memory=1`, purga
     X11 con `apt purge x11vnc xvfb` (sin `x11-common`), slices integrados con los overrides
     ya preparados en `ops/systemd/`, journald limitado.
   - Instalar la unit del vigía Hermes (V0 read-only, ver `HERMES_VPS_VIGIA.md`).
3. **Servicios que quedan activos**: `ultrarentable-api.service`, la web en build de
   producción, y el vigía. Nada más arranca en boot.
4. **SQX en el VPS queda apagado** (deshabilitado, no desinstalado) hasta que Emilio confirme
   la licencia en el PC.

## 7. Sincronización: el bus completo

| Qué | Vía | Cadencia |
| :--- | :--- | :--- |
| Código, docs, manifiestos, informes, evidencia | git (commits temáticos del orquestador) | por lote auditado |
| Datasets consolidados | rsync o R2 | al producirse |
| Candidatas/certificadas → web | export espejo (RTDB/Firestore o JSON estático) | tras cada censo |
| Estado del vigía → orquestador | fichero JSON en el VPS leído por ssh + alertas | continuo |
| GitHub `origin/main` | push desde el PC | árbol coherente; `origin/tmp-sync` no se borra hasta verificar |
