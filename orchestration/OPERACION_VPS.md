# OPERACIÓN DEL VPS — SSOT de recursos

> **LEER ANTES DE LANZAR NADA.** Este documento manda sobre cualquier otra costumbre del
> proyecto. Estabilizar la máquina es la PRIMERA tarea de cada sesión, no algo que se gestione
> sobre la marcha.

## La máquina

| | |
|:--|:--|
| Núcleos | 4 — **menos el 4-9 % que se lleva el hipervisor de Oracle** (`st` en `top`) |
| RAM | ~23 GB |
| Swap | 4 GB |
| Además sirve | API FastAPI (`:8000`), web Next.js (`:3000`), StrategyQuantX headless (`:5050`) |

La capacidad real es menor que la nominal, y el margen se reparte con tres servicios que Emilio
usa. Un colapso no ralentiza un cálculo: tira la API y la web.

## Por qué se colapsó tres veces

El problema nunca fue un proceso concreto. Fue que **cada proceso decidía por su cuenta cuándo
arrancar**. Diagnóstico medido el 2026-09-01:

1. **Thrashing de cgroup — la causa más grave.** `ultrarentable-discovery.service` declaraba
   `MemoryHigh=1.5G` con un working set real de 1,6 GB. `MemoryHigh` es un límite **blando**: al
   superarlo el kernel frena el proceso para forzar reclamo. Como vivía permanentemente por
   encima, entró en bucle. `memory.events` registró **713.626 frenazos**, el proceso clavado en
   estado D con `wchan = mem_cgroup_handle_over_high` y 947 MB suyos en swap. Ésa era la presión
   de I/O del 13-15 %, no la CPU.
   **Lección general: un límite blando por debajo del uso estable de un proceso no lo limita — lo
   convierte en un generador permanente de presión de disco.**
2. **Swap agotada al 100 %**: 4,0 GB de 4,0 GB, 40 KiB libres.
3. **`nice` no salva.** El 56,6 % del tiempo de CPU ya era `nice` y la máquina seguía saturada. La
   cortesía reparte la CPU; no reduce la demanda.
4. **Las sesiones de Claude cuentan como carga pesada.** El segundo mayor consumidor medido era
   "otra sesión de Claude Code al 122 %" ejecutando `pytest` y un script de verificación. Diez
   subagentes lanzando tests en paralelo saturan igual que una campaña de minería.

## El mecanismo: turno único, no buena voluntad

`services/ops/gobernanza_recursos.py` es la **puerta de admisión única** para todo trabajo pesado.

```python
from services.ops.gobernanza_recursos import trabajo_pesado

with trabajo_pesado("campana-fondeo-5m"):
    ...   # minería, backfill, build de la web, consolidación, pytest largo
```

Qué garantiza:

- **Un solo trabajo pesado a la vez en toda la máquina.** Candado `flock`, así que si el proceso
  muere el kernel lo libera solo: no hay candados huérfanos que limpiar a mano, que es como
  acaban fallando estos mecanismos.
- **Admisión previa.** Rechaza arrancar si la swap libre baja de 256 MB, si la memoria disponible
  baja de 1,5 GB o si la carga supera 1,5 por núcleo. Falla cerrado y dice el motivo concreto:
  esperar cinco minutos no cuesta nada, tumbar la máquina cuesta la sesión entera.
- **Prioridad rebajada** (`nice 19` + `ionice -c 3`) automáticamente, sin depender de que quien
  llama se acuerde.
- **Turno visible**: `~/.local/state/ultrarentable/trabajo_pesado.json` dice quién lo tiene y desde
  cuándo, para que un humano pueda ver por qué algo está esperando.

Desde la línea de comandos:

```bash
python -m services.ops.gobernanza_recursos estado
python -m services.ops.gobernanza_recursos ejecutar --nombre backfill -- <comando>
```

**Qué cuenta como trabajo pesado**: campañas de minería, backfills, consolidación de datasets,
`npm run build`, `git push` de cientos de MB, Chrome headless, y los `pytest` o scripts de
verificación de los subagentes.

**Excepción documentada**: el backfill de Dukascopy es I/O-bound (~3 % de CPU) y puede convivir con
otro trabajo, pero sigue pasando por la puerta para que quede registrado.

## Reglas que siguen vigentes

1. **Primero estabilizar, luego producir.** Inventario al empezar: `ps aux --sort=-%cpu | head`,
   `free -h`, y los `memory.events` de los cgroups del proyecto.
2. **La web se sirve en build de producción** (`npm run build && npm run start`), nunca `next dev`.
3. **Cuidado con lo que resucita solo.** `ultrarentable-discovery.service` y `sqx.service` quedan
   `enabled` y systemd los relanza; el cron `improve_cycle.sh` (minuto :40) revive el bucle de SQX
   cada hora. Parar el proceso no basta si no se cortan las tres vías.
4. **Si la máquina ya está saturada por procesos ajenos, no se añade trabajo encima**: se reporta
   el bloqueo y se espera.

## Comandos que sólo puede ejecutar Emilio (requieren sudo)

### A. Cortar de raíz lo que satura hoy

```bash
# 1. El servicio en thrashing. Bajo el mandato FONDEO-only no aporta nada: lleva sin evaluar
#    una sola estrategia de FONDEO desde el 2026-08-30 (bug de enrutamiento, ya corregido) y
#    sostiene los 713.626 frenazos de memoria.
sudo systemctl stop ultrarentable-discovery.service
sudo systemctl disable ultrarentable-discovery.service

# 2. SQX: consume la mitad de la máquina produciendo cero mientras su configuración apunte a un
#    único símbolo con OOS del 0,3 %. Se PARA pero NO se deshabilita: hace falta después.
sudo systemctl stop sqx.service

# 3. Los bucles que resucitan solos
pkill -f run_continuous_pipeline
pkill -f discovery_validation_pipeline
crontab -e     # comentar la línea de improve_cycle.sh (minuto :40)
```

### B. Instalar los límites correctos (para cuando se reactiven)

```bash
cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable"

sudo mkdir -p /etc/systemd/system/ultrarentable-discovery.service.d
sudo cp orchestration/ops/systemd/ultrarentable-discovery.service.d-override.conf \
        /etc/systemd/system/ultrarentable-discovery.service.d/override.conf

sudo mkdir -p /etc/systemd/system/sqx.service.d
sudo cp orchestration/ops/systemd/sqx.service.d-override.conf \
        /etc/systemd/system/sqx.service.d/override.conf

sudo systemctl daemon-reload
```

### C. Comprobar que el thrashing paró

```bash
cat /sys/fs/cgroup/system.slice/ultrarentable-discovery.service/memory.events
# 'high' debe dejar de crecer. Si sigue subiendo miles de veces por minuto, el límite continúa
# por debajo del working set real y hay que subirlo más, no bajarlo.
free -h    # la swap debe empezar a liberarse
```
