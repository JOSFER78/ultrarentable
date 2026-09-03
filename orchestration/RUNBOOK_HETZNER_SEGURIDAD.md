# RUNBOOK — cerrar el servidor Hetzner (88.99.210.167)

> Estado medido el 2026-09-03 02:45 UTC: escritorio remoto **público y sin contraseña**, VNC sin
> contraseña alcanzable por IPv6, websockify en `0.0.0.0:6080`, sin cortafuegos y sin fail2ban.
> Detalle y comandos de medición en `ARQUITECTURA_RECURSOS.md` §4. Ejecuta los bloques **en orden**:
> el primero abre el puerto 22 antes de activar nada, así que no puede dejarte fuera.

Entrar: `ssh sqx-hetzner`

## Bloque 1 — Cortafuegos

Cierra el 6080 directo, el VNC por IPv6 y, de paso, el futuro 5050 de StrategyQuant (que no tiene
autenticación y jamás debe estar en internet). Deja SSH y la web.

```bash
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
ufw --force enable
ufw status verbose
```

Para deshacerlo: `ufw disable`.

## Bloque 2 — Contraseña en el escritorio remoto

El 443 sigue abierto a internet y hoy entra cualquiera con la URL.

```bash
apt-get update -qq && apt-get install -y apache2-utils
htpasswd -c /etc/nginx/.htpasswd emilio     # pide la contraseña dos veces
cp /etc/nginx/sites-available/default /root/nginx-default.bak
sed -i 's|^\(    location /novnc/ {\)|\1\n        auth_basic "Ultrarentable";\n        auth_basic_user_file /etc/nginx/.htpasswd;|' /etc/nginx/sites-available/default
sed -i 's|^\(    location = /novnc/websockify {\)|\1\n        auth_basic "Ultrarentable";\n        auth_basic_user_file /etc/nginx/.htpasswd;|' /etc/nginx/sites-available/default
nginx -t && systemctl reload nginx
```

Para deshacerlo: `cp /root/nginx-default.bak /etc/nginx/sites-available/default && systemctl reload nginx`.

## Bloque 3 — Comprobación

```bash
curl -s -o /dev/null -w 'novnc: %{http_code}\n' https://88-99-210-167.sslip.io/novnc/vnc.html   # debe ser 401
ufw status verbose | head -12
ss -ltn | grep -E ':(5900|6080)'    # siguen escuchando en local: correcto, ya no desde fuera
```

Tras esto el enlace de noVNC pide usuario y contraseña.

## Bloque 4 — Opcional, recomendable

```bash
apt-get install -y fail2ban && systemctl enable --now fail2ban && fail2ban-client status sshd
```

## Nota sobre StrategyQuant

Cuando SQX corra aquí, su puerto 5050 queda **solo accesible desde la propia máquina**. Oracle lo
alcanzará por un túnel SSH (`ARQUITECTURA_RECURSOS.md` §3), no por internet. Si alguna vez hay que
abrirlo, la respuesta correcta es el túnel o una red privada, nunca `ufw allow 5050`.
