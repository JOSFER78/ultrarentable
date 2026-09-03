---
id: F10
titulo: "Operaciones e infraestructura — tareas para agentes (AGY)"
estado: EN_CURSO
depende_de: []
desbloquea: []
verificacion_global: "Cada tarea la verifica el orquestador re-ejecutando los comandos de ACEPTACIÓN. Un parte de entrega sin salida cruda pegada no se acepta."
actualizado: "2026-09-03"
---

# FASE 10 — OPERACIONES E INFRAESTRUCTURA · TABLERO DE TAREAS PARA AGY

> **Esta página es el tablero.** Aquí el orquestador (sesión Claude Code) deja tareas concretas
> para los agentes de Emilio (Antigravity/AGY), y aquí mismo el agente deja su parte de entrega
> cuando termina. Emilio lo ve en `/plan` sin abrir una terminal.
>
> **Reglas para el agente, sin excepciones:** ejecuta SOLO la tarea que se te asigna; no toques
> nada fuera de su ámbito; si un comando falla, para y cuéntalo con la salida cruda; nunca
> inventes una salida que no ejecutaste; nunca uses `rm`; no relajes ni "simplifiques" un paso
> porque parezca innecesario.

## Protocolo entre el orquestador y AGY (leedlo los dos)

El orquestador (sesión Claude Code, en el PC) y AGY (los agentes de Antigravity, que trabajan por su
cuenta y en otra ventana) **no se ven entre sí**. Este fichero es el único canal, y funciona así:

| | Orquestador (Claude Code) | AGY (Antigravity) |
| :--- | :--- | :--- |
| Qué hace | Investiga, mide, escribe las tareas de aquí y **verifica** re-ejecutando la ACEPTACIÓN | **Ejecuta** la tarea asignada y escribe su parte de entrega en este fichero |
| Dónde escribe | `orchestration/`, `services/`, `scripts/` | lo que diga el ámbito de su tarea, y este fichero |
| Cómo avisa | deja la tarea escrita aquí y avisa a Emilio | marca `HECHO` en la tabla y añade el parte al final (ver abajo) |
| Qué no hace | ejecutar la tarea de AGY por su cuenta | dar por buena una tarea sin pegar la salida cruda |

Regla que evita que os piséis: **una tarea tiene un solo dueño**. Si AGY ve algo roto fuera de su
tarea, no lo arregla: lo escribe como `HALLAZGO` en su parte y sigue. Si el orquestador necesita algo
de AGY, no lo hace él: abre una tarea nueva aquí con su ACEPTACIÓN.

## Tareas

| ID | Tarea | Máquina | Prioridad | Estado |
| :--- | :--- | :--- | :--- | :--- |
| A01 | Cerrar el servidor Hetzner: cortafuegos y contraseña en el escritorio remoto | Hetzner (`ssh sqx-hetzner`) | **URGENTE** | PENDIENTE |
| A02 | Instalar fail2ban en el Hetzner | Hetzner | media | PENDIENTE |
| A03 | Inventario post-instalación de StrategyQuant X en el Hetzner | Hetzner | media | PENDIENTE (espera a que Emilio instale SQX) |

---

## A01 — Cerrar el servidor Hetzner (URGENTE)

### Por qué
El servidor `88.99.210.167` está recién entregado y **abierto a internet**. Medido por el
orquestador el 2026-09-03 a las 02:45 UTC:

- `ufw status` → `inactive`; `iptables -S INPUT` → política `ACCEPT`. **No hay cortafuegos.**
- `curl https://88-99-210-167.sslip.io/novnc/vnc.html` → **200 sin pedir contraseña**, y la URL
  lleva `autoconnect=true`. Cualquiera con el enlace entra a un escritorio gráfico **como root**.
- `nginx` hace `proxy_pass` a `127.0.0.1:6080` en dos `location` y **ninguna** tiene `auth_basic`.
- `x11vnc` corre con `-nopw` (sin contraseña) y escucha en `[::]:5900`; la máquina tiene IPv6
  pública `2a01:4f8:10a:3b9a::2/64`. Segunda puerta abierta, independiente de la web.
- `websockify` escucha en `0.0.0.0:6080`, es decir, se puede saltar nginx.
- `fail2ban` no está instalado.

En esa máquina va a vivir StrategyQuant X con la licencia de Emilio y, después, las campañas del
proyecto. Además, `sqcli` (el StrategyQuant headless) **no tiene autenticación**: quien alcance su
puerto 5050 controla la minería. Por eso el cortafuegos es lo primero, antes que nada más.

### Cómo (ejecutar EN ORDEN; el bloque 1 abre el puerto 22 antes de activar nada, así que no puede dejar a nadie fuera)

Entrar: `ssh sqx-hetzner`

**Bloque 1 — cortafuegos**

```bash
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
ufw --force enable
ufw status verbose
```

Deshacer si algo va mal: `ufw disable`.

**Bloque 2 — contraseña en el escritorio remoto**

La contraseña la elige Emilio; el agente debe **pedírsela** y no inventarla ni dejar una por
defecto. Si el agente no puede pedirla, deja A01 a medias con el bloque 1 hecho y lo dice.

```bash
apt-get update -qq && apt-get install -y apache2-utils
htpasswd -c /etc/nginx/.htpasswd emilio     # pide la contraseña dos veces
cp /etc/nginx/sites-available/default /root/nginx-default.bak
sed -i 's|^\(    location /novnc/ {\)|\1\n        auth_basic "Ultrarentable";\n        auth_basic_user_file /etc/nginx/.htpasswd;|' /etc/nginx/sites-available/default
sed -i 's|^\(    location = /novnc/websockify {\)|\1\n        auth_basic "Ultrarentable";\n        auth_basic_user_file /etc/nginx/.htpasswd;|' /etc/nginx/sites-available/default
nginx -t && systemctl reload nginx
```

Deshacer: `cp /root/nginx-default.bak /etc/nginx/sites-available/default && systemctl reload nginx`.

### ACEPTACIÓN (el orquestador re-ejecuta esto; pega la salida CRUDA en el parte)

```bash
curl -s -o /dev/null -w 'novnc: %{http_code}\n' https://88-99-210-167.sslip.io/novnc/vnc.html   # esperado: 401
ufw status verbose | head -12                        # esperado: Status: active, y 22/80/443 permitidos
ss -ltn | grep -E ':(5900|6080)'                     # siguen escuchando en local: correcto
grep -c auth_basic /etc/nginx/sites-available/default # esperado: 4
nginx -t                                             # esperado: syntax is ok / test is successful
ssh -o ConnectTimeout=10 sqx-hetzner 'echo SSH_SIGUE_VIVO'   # desde el PC, para probar que no te has cerrado la puerta
```

### PROHIBIDO en A01
Abrir el puerto 5050 (`ufw allow 5050`) ni ningún otro; tocar `sshd_config`; cambiar la clave SSH;
parar `novnc-display.service`; reiniciar el servidor; instalar nada que no esté en los bloques.

---

## A02 — fail2ban en el Hetzner

```bash
apt-get install -y fail2ban && systemctl enable --now fail2ban
fail2ban-client status sshd
```

ACEPTACIÓN: `systemctl is-active fail2ban` → `active`, y `fail2ban-client status sshd` responde sin error.
Hacer **después** de A01, no antes.

---

## A03 — Inventario de StrategyQuant X en el Hetzner (cuando Emilio lo haya instalado)

Solo lectura, no cambia nada. Sirve para que el orquestador prepare la copia de datos desde Oracle.

```bash
ls -la /opt/strategyquant 2>/dev/null || find / -maxdepth 4 -iname "*trategy*uant*" -not -path "/proc/*" 2>/dev/null
file /opt/strategyquant/sqcli 2>/dev/null           # esperado: ELF 64-bit x86-64 (NO aarch64)
ls /opt/strategyquant/user/ 2>/dev/null
ss -ltnp | grep 5050 || echo "sqcli no está escuchando todavía"
systemctl list-units --type=service | grep -i -E "sqx|strategy" || echo "sin servicio systemd de SQX"
java -version 2>&1 | head -2
free -g | sed -n 2p
```

ACEPTACIÓN: pegar la salida cruda de los siete comandos. Si `file` dice `aarch64`, avisar: sería el
build equivocado (el de Oracle es ARM y esta máquina es Intel x86-64).

---

## CÓMO AVISAR AL ORQUESTADOR CUANDO TERMINES (obligatorio)

El orquestador **no ve tu terminal**. La única forma de que se entere es esta, y es sencilla:

1. **Cambia el estado en la tabla de arriba**: la celda `Estado` de tu tarea pasa de `PENDIENTE` a
   `HECHO` (si algo quedó a medias: `PARCIAL`). Escribe `HECHO` en mayúsculas: la página del plan
   cuenta las tareas terminadas buscando esa palabra, así que ese solo cambio ya mueve la barra de
   progreso que ve Emilio.
2. **Añade tu parte de entrega al final de este mismo fichero**
   (`orchestration/state/plan/bloques/F10_operaciones_infra.md`), con este formato exacto:

```
## PARTE DE ENTREGA — A01 — 2026-09-03 HH:MM UTC — agente: <tu nombre>

**Resultado en una frase:** <qué es verdad ahora que antes no lo era>

**Comandos ejecutados y salida CRUDA** (pegada tal cual, sin resumir ni recortar):
<pega aquí cada comando y lo que devolvió>

**Lo que no pude hacer y por qué:** <o "nada">
**Hallazgos fuera de mi tarea (no los toqué):** <o "ninguno">
```

3. **Actualiza la fecha** del frontmatter de arriba: `actualizado: "2026-09-03"`.
4. **Guarda el fichero.** No hace falta que hagas `git commit`: con guardarlo basta, el orquestador
   está vigilando este fichero y se entera solo. Si además quieres commitear, usa
   `ORQ_COMMIT=1 git commit -- orchestration/state/plan/bloques/F10_operaciones_infra.md` y nada más
   en el mismo commit.

El orquestador verificará re-ejecutando los comandos de ACEPTACIÓN por su cuenta y marcará la tarea
como `VERIFICADO` (o la devolverá con una lista concreta de correcciones). Un parte sin salida cruda
pegada se devuelve sin leer: en este proyecto una afirmación sin su comando no existe.
