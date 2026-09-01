# OPERACIÓN DE LA VPS — modelo de uso de recursos (SSOT)

> **Este documento se lee ANTES de lanzar nada.** La VPS se ha colapsado varias veces por
> acumular procesos pesados. Estabilizar la máquina es la PRIMERA tarea de cada sesión, no algo
> que se gestione sobre la marcha.

## La máquina

**4 cores · ~23 GB RAM · 4 GB swap.** No es una máquina de cómputo dedicada: además del trabajo
de investigación, sirve la API, la web, SQX y el IDE remoto. Con 4 cores, **un solo proceso
pesado ya consume el 25 % de la capacidad**; tres la dejan inutilizable.

Regla de oro: **load average por encima de ~4,0 sostenido = la máquina está en problemas.**

## Qué corre permanentemente (no tocar)

| Proceso | Coste típico | Para qué |
| :--- | :--- | :--- |
| `ultrarentable-api.service` (uvicorn :8000) | ~0,2 % CPU | API FastAPI; la web depende de ella |
| Antigravity IDE server + Claude Code | 5-10 % CPU | entorno de trabajo remoto |
| Web Next.js :3000 (**build de producción**) | bajo en reposo | NUNCA `next dev`: compila bajo demanda y satura |

## Qué corre bajo demanda (uno a la vez, siempre con `nice -n 19` + `ionice -c 3`)

Sólo **UNO** de estos puede estar activo simultáneamente:

| Trabajo | Coste | Notas |
| :--- | :--- | :--- |
| Campaña de minería (`cola_mineria.py trabajar`) | 1 core por celda concurrente | `--concurrencia 1` con la máquina cargada; 2 como máximo |
| Backfill Dukascopy (`run_dukascopy_backfill`) | ~3 % CPU (I/O-bound) | Excepción: es tan barato que puede convivir con otro trabajo |
| Build de SQX (`sqx.service`) | **1 core entero, ~4,5 GB RAM** | El más caro de todos |
| `git push` de cientos de MB | 1 core (`pack-objects`) | Nunca durante una campaña |
| Build de la web (`npm run build`) | 1-2 cores | Puntual |
| Chrome/Brave headless (auditorías) | 1 core + RAM | Puntual |

**El backfill de Dukascopy es la única excepción**: al ser I/O-bound consume ~3 % de CPU y puede
convivir con un trabajo pesado. Todo lo demás va estrictamente de uno en uno.

## Lo que resucita solo (la causa de los colapsos)

Este es el punto que más veces ha roto la estabilidad:

| Qué | Cómo vuelve | Cómo se corta de verdad |
| :--- | :--- | :--- |
| `sqx.service` | `enabled` → systemd lo relanza al reiniciar | `sudo systemctl stop sqx.service` |
| `ultrarentable-discovery.service` | `enabled` → ídem, y mina sin gobernanza | `stop` **y** `disable` |
| Bucle de SQX (`improve_cycle.sh`) | **cron cada 20-30 min** (`/etc/crontab`, minuto :40) | comentar la línea con `crontab -e` |

**Parar el proceso no basta si el cron o systemd lo reviven.** Hay que cortar las tres vías.

## Estado a 2026-09-01 08:20 y por qué importa

- `sqcli` (sqx.service): **114 % CPU, 4,2 GB RAM** — y su proyecto lleva horas con
  **0 % de aceptación** sobre `AUDUSD_H1`, un símbolo irrelevante para el proyecto.
  Es el mayor consumidor de la máquina y no produce nada.
- `discovery_validation_pipeline.py` (ultrarentable-discovery.service): **39,8 % CPU**, resucitado.
- Backfill Dukascopy: 3,2 % CPU — correcto, es el camino crítico de FONDEO.

## Procedimiento de arranque de sesión (obligatorio)

```bash
# 1. Fotografía
uptime; free -h
ps -eo pid,ni,%cpu,%mem,etime,cmd --sort=-%cpu --no-headers | head -12
systemctl is-active sqx.service ultrarentable-discovery.service ultrarentable-api.service

# 2. Si load > 4 o RAM libre < 3 GB: estabilizar ANTES de trabajar.
#    Lo que necesita sudo se le pasa a Emilio en UNA lista agrupada, no goteando.

# 3. Sólo entonces, lanzar UN trabajo pesado:
nohup nice -n 19 ionice -c 3 <comando> </dev/null >> <log> 2>&1 &
```

## Comandos de estabilización (requieren sudo — los ejecuta Emilio)

```bash
sudo systemctl stop sqx.service ultrarentable-discovery.service
sudo systemctl disable ultrarentable-discovery.service   # mina sin gobernanza; que no vuelva
pkill -f run_continuous_pipeline
pkill -f discovery_validation_pipeline
crontab -e     # comentar la linea de improve_cycle.sh (minuto :40)
```

`sqx.service` sólo se **para**, no se deshabilita: hace falta más adelante, con un proyecto bien
configurado (hoy apunta al símbolo equivocado por orden alfabético de los 97 Setups cargados).

## Reglas que no se negocian

1. **Estabilizar primero, producir después.**
2. Un solo proceso pesado a la vez, con `nice -n 19` / `ionice -c 3`.
3. Si la máquina ya está saturada por procesos que el orquestador no controla, **no se añade
   trabajo encima**: se reporta el bloqueo y se espera.
4. La web siempre en build de producción.
5. Antes de lanzar: mirar `ps` y `free`. Después de lanzar: comprobar que el `nice` se aplicó
   de verdad (`ps -o ni`), porque `nohup ... &` desde un wrapper puede perderlo.
