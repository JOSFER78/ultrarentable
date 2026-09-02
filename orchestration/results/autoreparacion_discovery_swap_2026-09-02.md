# Autorreparación: discovery pipeline atascado por fuga de memoria (2026-09-02 13:50 UTC)

## Síntoma detectado (por el orquestador-auditor, no por el monitor)
- `fase_05_discovery.log` no registraba NINGÚN veredicto desde el **2026-09-01 09:07 UTC**
  (28h de silencio) pese a que `ultrarentable-discovery.service` constaba "active (running)".
- El diff que despertó el cron vigilante era solo ruido: líneas de lock
  `[DISCOVERY] Otra instancia ya esta en ejecucion` escritas cada 5 min por el
  arranque duplicado de otro job.

## Diagnóstico REAL (verificado con comandos propios, cero supuestos)
1. Proceso PID 1368614 en **estado D** con stack kernel atascado en
   `mem_cgroup_handle_over_high` → estrangulación de memoria del cgroup.
2. Memoria del servicio: RSS 1.5G (en el límite `MemoryHigh`) + **2.6G de swap**
   (working set ≈ 4.1G para un servicio con techo de 2G).
3. **Swap del sistema al 100% (4G/4G)** — el thrash también degradaba al resto del VPS.
4. CPU total del servicio en 29h de wall-clock: solo 2h30m (≈8,6%) → no estaba
   computando, estaba paginando.
5. El ciclo #1 del 09-01 08:01 procesó 4 veredictos (AVAX 15M/1H/1M/4H, 8-54 min
   cada uno) y luego se congeló en el 5º dataset. Patrón compatible con fuga de
   memoria acumulativa por dataset, no con un dataset anómalo.

## Causa raíz
El cgroup limitaba RAM (`MemoryHigh=1.5G`, `MemoryMax=2G`) pero **no limitaba swap**
(`MemorySwapMax` sin definir = infinito). Resultado: al hincharse el proceso, en vez de
morir por OOM y renacer limpio (`Restart=always`), quedaba agonizando en swap durante
horas sin producir veredictos. Violación del principio de degradación honesta
(morir rápido > agonizar lento).

## Corrección aplicada (autorreparación, mandato de auto-recuperación 2026-08-29)
Drop-in `/etc/systemd/system/ultrarentable-discovery.service.d/90-autorepair-swap.conf`:
- `MemorySwapMax=1G` → si vuelve a hincharse, el kernel lo mata (fail-fast) y
  `Restart=always` lo levanta limpio en segundos.
- `RuntimeMaxSec=12h` → reciclaje preventivo cada 12h para contener la fuga de base
  (el pipeline es idempotente: cada dataset se valida con 256 trials propios).

Reinicio: `systemctl daemon-reload && systemctl restart ultrarentable-discovery.service`.

## Resultado verificado tras la reparación
- Nuevo PID 555795 activo, estado R normal, RSS ~525M y CPU sostenida (1201 ticks/30s ≈ 40% core).
- Swap del sistema liberado: de 4,0G/4,0G (100%) a **1,5G/4,0G**.
- Ciclo #1 re-arrancado: **556 datasets detectados** (antes 213 — el backfill Binance
  profundo ya está siendo minado).
- Nota systemd: el propio arranque del nuevo proceso y el stop del viejo quedaron
  registrados en el journal ("Consumed 2h30min CPU, 1.6G memory peak, 2.5G swap peak").

## Pendiente (trabajo de fondo, sin intervención del usuario)
- Vigilar que el nuevo ciclo emite veredictos con cadencia normal (~2-8 min/dataset);
  el primer veredicto del ciclo puede tardar hasta ~54 min (caso AVAX_15M).
- Si vuelve a hincharse, ahora morirá solo y renacerá; si la fuga de base persiste,
  el candidato a auditar es la liberación de resultados por dataset en
  `services/discovery/discovery_validation_pipeline.py`.
