# INFORME DE TRASPASO — Ultrarentable (2026-08-31 ~20:00 UTC)

Para el agente que retome el trabajo. Contexto automático: lee `CLAUDE.md` (raíz del repo),
`orchestration/state/current_phase.md` y `orchestration/state/plan_maestro.md` + `plan/bloques/`.
Repo: `/home/ubuntu/workspace/pro/trading/01 Ultrarentable` · remoto
`https://github.com/JOSFER78/ultrarentable.git` · rama `main`.

## Estado en una línea

Motor de backtest honesto **5.14.0** terminado y verificado; **0 estrategias certificadas**
(cifra honesta tras sanear 728 falsas); la siguiente oportunidad real es la re-campaña con los
4 arquetipos nuevos; el push a GitHub está a medias por cortes de red (los datos pesados YA
están subidos); la máquina está saturada por procesos que solo Emilio puede parar.

## TAREA 1 — URGENTE: liberar la máquina (necesita a Emilio, requiere sudo)

El VPS (4 cores) está saturado: `sqx.service` (~90 % CPU) y un minero huérfano sin gobernanza
(`run_continuous_pipeline`, llegó a 9 GB RAM) + `ultrarentable-discovery.service` (resucita al
reiniciar porque está `enabled`). Comandos:

```
sudo systemctl stop ultrarentable-discovery.service sqx.service
sudo systemctl disable ultrarentable-discovery.service
pkill -f run_continuous_pipeline
```

Sin esto, todo lo demás (push, campañas, web) irá lento o fallará.

## TAREA 2 — Terminar el push a GitHub (estado exacto)

- Local `main` = `8f4fbe11bc38d670819e58ac231a2b6d08d4d776` (todo el trabajo commiteado, árbol limpio).
- `origin/main` = `e485fdabba6f...` (viejo, 2 commits de Antigravity ya reconciliados en local
  con `merge -s ours`; el push es fast-forward-con-merge, NO requiere force).
- **`origin/tmp-sync` = `f1213603...` contiene YA los 36 blobs grandes (~1,3 GB subidos)** en
  lotes. NO BORRAR esa rama hasta que `origin/main == local main`.
- Falta el pack final: ~390 objetos (~260 MB comprimidos). TODOS los intentos (6+) mueren
  igual: la subida llega al 100 % y el servidor corta con HTTP 408 / "remote end hung up".
  No hay proxy configurado (verificado); parece límite de tiempo de GitHub/red del VPS con la
  CPU saturada (a 2,6 MiB/s el POST dura ~100 s). Lotes de ≤50 MB entran SIEMPRE a la primera.
- Herramienta reanudable: `scripts/ops/push_troceado.sh` (sube blobs >8 MB en lotes a
  tmp-sync, reanuda desde `origin/tmp-sync`, hace push final y SOLO limpia tras verificar
  `ls-remote`). Nota: por razón no cerrada, el pack final de main incluye ~260 MB pese a
  tmp-sync (posible no-exclusión de blobs en send-pack); diagnosticar antes de reintentar.
- Opciones en orden: (1) reintentar `git push origin main` con la máquina LIBERADA (tarea 1);
  (2) configurar clave SSH del VPS en la cuenta GitHub de Emilio y pushear por SSH (aguanta
  streams lentos; OJO: `ssh git@github.com` hoy resuelve a una IP Tailscale 100.106.212.23 —
  investigar esa redirección); (3) reducir LOTE_MAX del script y trocear también el resto.
- Rama local `tmp-sync` puede existir; es solo transporte. Los mensajes de commit de main ya
  están limpios (los "wer"/"werwe" fueron reescritos preservando contenido).

## TAREA 3 — Gate 9 antes de la re-campaña

`services/api/app/validation/gates/gate_09_novelty_antifit.py` NO conoce las dimensiones
`archetype_params` de las 4 familias nuevas de la 5.14.0 (reversion_atr, squeeze_breakout,
session_momentum, streak_edge): el conteo de grados de libertad y la perturbación de
vecindario usan solo las dimensiones antiguas (ema_fast/ema_slow/sl/tp). Corregirlo ANTES de
certificar nada de la re-campaña o el gate mentirá. Spec de las familias:
`orchestration/reviews/diseno_arquetipos_5_14.md`.

## TAREA 4 — Re-campaña `arquetipos` (el objetivo real)

Con la máquina liberada y el gate 9 corregido:

```
.venv/bin/python scripts/cola_mineria.py encolar --solo-cripto --tfs 15m,4h --ver   # revisar
.venv/bin/python scripts/cola_mineria.py encolar --solo-cripto --tfs 15m,4h
.venv/bin/python scripts/cola_mineria.py trabajar --concurrencia 2 --max-candidates 2000 --profile arquetipos
```

(comprobar flags exactos con `--help`; el perfil `arquetipos` mina SOLO las 4 familias nuevas).
Después: censo criterio 1.1 (`scripts/censo_f01.py`). El criterio está SELLADO: no se relaja.
Si hay supervivientes → F04 (mejora) → F05 (envolvente ULTRA) → F06 (meta-router).
FONDEO sigue bloqueado hasta que el backfill Dukascopy tenga datos verificados (hoy solo
USA500IDXUSD parcial).

## Riesgos y avisos

1. La BD canónica vive FUERA del repo (`services/api/app/config.py::STATE_DB_PATH`).
2. Zero-mocks / REAL-ONLY: nada sintético, nunca. Cuarentena en vez de borrar (manifiesto SHA-256).
3. Regla #26: cualquier cambio que altere operaciones del motor → bump de versión
   (`services/engine_version.py`) + verificación `scripts/verificacion_f02.py --comparar`.
4. Push a main autorizado por Emilio (commits temáticos, trailer de Claude). Responder en español.
5. La web va en :3000 con build de producción (`apps/web`: `npm run build && npm run start -- -p 3000`);
   su contenido (badge v5.4.0, etc.) está desactualizado — actualizarla es F09, no urgente.
   El login Firebase tiene watchdog de 6 s; la causa raíz (claves .env.local mezclando
   proyectos goalskid/pecemi en `apps/web/lib/firebase.ts`) sigue abierta.
6. Procesos pesados: `nice -n 19` + `ionice -c 3`, de uno en uno (regla sellada tras el
   colapso de hoy).

## Evidencia de lo cerrado hoy (por si hay dudas)

- Identidad motor 5.13.0→5.14.0: `orchestration/results/verificacion_f02_diff_5.13.0_vs_5.14.0.md` (15/15 idénticas).
- Smoke 4 familias: `orchestration/results/smoke_arquetipos_5_14_0.md` (todas generan trades).
- Censo honesto: `orchestration/results/censo_f01.md` (0 de 728).
- CSV SQX: `data/sqx_exports/toimprove_2026-08-31.csv` (2.035 estrategias, carril SQX pendiente).
