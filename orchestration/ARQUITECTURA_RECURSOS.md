# ARQUITECTURA DE RECURSOS — quién corre qué y en qué máquina (2026-09-03)

> Escrito al incorporar el servidor dedicado de Hetzner. Todo lo de aquí está **medido**, no
> supuesto; cada cifra lleva el comando con el que se obtuvo. Sustituye a la parte de reparto de
> máquinas de `OPERACION_VPS.md`, que sigue valiendo para la operación del VPS de Oracle.

---

## 1. Las tres máquinas, medidas

| | **Hetzner** (nuevo) | **Oracle** (VPS) | **PC de Emilio** |
| :--- | :--- | :--- | :--- |
| Nombre / acceso | `sqx-ultrarentable`, `ssh sqx-hetzner` (88.99.210.167) | `ssh oracle-vps` (143.47.35.167) | local |
| CPU | Intel i7-6700, 4 núcleos / **8 hilos**, 3,4-4,0 GHz | Ampere **ARM aarch64**, 4 núcleos | 8 núcleos |
| RAM | **62 GB** + 15 GB swap | 23 GB + 4 GB swap | 24 GB |
| Disco | 212 GB RAID 1, **196 GB libres** | 193 GB, **15 GB libres (93 % lleno)** | — |
| Carga al medir | 1,2 de 8 (vacía) | 2-13 de 4 (saturada por herramientas de Emilio) | 39-54 % |
| Arquitectura | x86-64 | **aarch64** | x86-64 |

`lscpu`, `free -g`, `df -h`, `uptime`, `uname -m` el 2026-09-03 02:33-02:45 UTC.

**Consecuencia inmediata y no negociable:** los binarios de SQX de Oracle (`sqcli`,
`StrategyQuantX`, y el JRE embebido `j64`) son **ELF aarch64** (`file` lo confirma). **No se pueden
copiar** al Hetzner. Hay que instalar allí el build **Linux x86-64** de StrategyQuant X 144 desde
la cuenta de Emilio. Lo que sí se copia son **datos**: `user/` (351 MB) y `sqx_imports_m1` (2,5 GB).

## 2. Reparto propuesto (por qué cada cosa va donde va)

| Trabajo | Máquina | Motivo medido |
| :--- | :--- | :--- |
| **StrategyQuant X (sqcli)** — minería genética M1 | **Hetzner** | Hoy en Oracle está estrangulado a `CPUQuota=120%` (1,2 núcleos) y `-Xmx4g` por `sqx.service`, compartiendo 4 núcleos con Hermes, la API, la web y el backfill. En Hetzner puede usar 8 hilos y `-Xmx48g` sin competir con nada: es entre 6 y 10 veces más caudal de estrategias crudas. |
| **Campañas de descubrimiento** (`scripts/mine.py`) | **Hetzner** (fase 2) | Son el segundo consumidor de CPU. 420 configuraciones tardaron ~45 min en Oracle. Con paralelismo por proceso en 8 hilos bajan a minutos (contrato `GO_B24.md`). |
| **Hermes y sus herramientas** (gateway, dashboard, Brave, CleanLinux, puente Antigravity, MCP) | **Oracle** | Es su casa; consume 18 GB de disco y decenas de procesos. Moverlo no aporta nada al trading y rompería lo que ya funciona. |
| **API FastAPI + base canónica + web** | **Oracle** | La base canónica (`~/.local/state/ultrarentable/ultrarentable.sqlite3`) es **maestro único**: no se replica ni se parte. La API es ligera (36 ms de respuesta); lo que la hacía sufrir era la competencia por CPU, que se va con SQX. |
| **Backfill de Dukascopy** | **Oracle** | Es I/O, ~3 % de CPU. Donde están los datos. |
| **Orquestación, desarrollo, build de la web** | **PC** | Donde trabaja Emilio. |

**Lo que NO se hace:** partir la base canónica entre máquinas. Una sola base, en Oracle; el Hetzner
produce estrategias crudas y resultados de campaña, y los entrega a Oracle.

## 3. Cómo se conectan (sin abrir nada a internet)

`sqcli` **no tiene autenticación**: quien alcance su puerto 5050 controla StrategyQuant. Por eso
nunca se publica. El código del proyecto habla con `http://localhost:5050` por defecto
(`services/sqx_bridge/sqx_client.py`, `sqx_router.py`), así que la forma de que **nada cambie en el
código** es un túnel SSH desde Oracle:

```
# En Oracle: el 5050 local sale al 5050 del Hetzner por SSH, con reconexión automática
autossh -M 0 -N -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
        -L 127.0.0.1:5050:127.0.0.1:5050 sqx-hetzner
```

Así `SQX_API_URL` sigue siendo `http://localhost:5050` en Oracle y la API, la web y el puente
funcionan igual. Alternativa si algún día hacen falta más servicios cruzados: red privada
(Tailscale) entre las tres máquinas; el PC de Emilio ya está en una (`100.106.212.23`).

## 4. Seguridad del Hetzner (estado al recibirlo, 2026-09-03 02:45 UTC)

Medido, no supuesto:

- **Sin cortafuegos**: `ufw` inactivo, `iptables -S INPUT` con política `ACCEPT`.
- **Escritorio remoto público sin contraseña**: `https://88-99-210-167.sslip.io/novnc/vnc.html`
  responde **200** sin autenticación y `autoconnect=true`; nginx no tiene `auth_basic` en ninguna
  de las dos `location` que hacen `proxy_pass` a `127.0.0.1:6080`.
- **VNC sin contraseña alcanzable por IPv6**: `x11vnc` corre con `-nopw` y, pese a `-noipv6`,
  escucha en `[::]:5900`; la máquina tiene IPv6 pública `2a01:4f8:10a:3b9a::2/64`.
- **websockify** en `0.0.0.0:6080` (se salta nginx).
- Sin `fail2ban`. SSH con `PermitRootLogin without-password` (solo clave: correcto).

Cierre (en este orden; el primer bloque no puede dejar a nadie fuera porque abre el 22 antes de
activar nada), en `orchestration/RUNBOOK_HETZNER_SEGURIDAD.md`.

## 5. Fases del traslado

| Fase | Qué | Quién | Estado |
| :--- | :--- | :--- | :--- |
| 0 | Asegurar el Hetzner (§4) | Emilio | instrucciones entregadas 03-09 02:50 |
| 1 | Instalar StrategyQuant X **x86-64** en el Hetzner y activar la licencia (la GUI por noVNC sirve para la activación) | Emilio | en curso |
| 2 | Copiar datos de Oracle: `StrategyQuantX144/user/` (351 MB) y `sqx_imports_m1/` (2,5 GB) | orquestador | pendiente de fase 1 |
| 3 | Túnel `autossh` Oracle→Hetzner en el 5050 y unidad systemd | orquestador | pendiente de fase 2 |
| 4 | Parar `sqx.service` en Oracle, desactivarlo y liberar sus 1,5 GB + el cron `improve_cycle.sh` que lo revive | orquestador, con visto bueno de Emilio | pendiente |
| 5 | Campañas paralelas (`GO_B24.md`) y gobernanza consciente de la máquina | orquestador + agente | pendiente |

**Cuidado en la fase 4**: `sqx.service` está `enabled` (systemd lo relanza) y el cron de Emilio
(`improve_cycle.sh`, minuto :40) revive el ciclo de SQX. Parar el proceso no basta: hay que
desactivar el servicio y comentar el cron, o el Oracle volverá a levantar un SQX que ya no manda.

## 6. Qué gana el proyecto con esto (la razón de todo)

Hoy hay **0 estrategias válidas para FONDEO**. El cuello no es la idea, es el caudal: cada campaña
de 420 configuraciones tarda 45 minutos y muere entera en la primera criba. Con el Hetzner:

- SQX pasa de 1,2 núcleos y 4 GB a 8 hilos y hasta 48 GB: muchas más estrategias crudas por hora.
- Las campañas del motor propio se paralelizan: se pueden probar familias y mercados nuevos el
  mismo día en vez de uno por noche.
- Oracle se queda con la API, la web y Hermes, y deja de colapsar.

Nada de esto relaja el criterio 1.1 ni la doctrina REAL-ONLY: más potencia significa **más
hipótesis probadas y descartadas honestamente por hora**, no un listón más bajo.
